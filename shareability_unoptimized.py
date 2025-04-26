import pandas as pd  
from geopy.distance import geodesic
from itertools import permutations
import itertools
from shapely.wkt import loads
from shapely.geometry import LineString, Point, MultiPoint
import numpy as np
import os
import gurobipy as gp
from gurobipy import GRB
from gurobipy import Model, GRB, quicksum
from scipy.spatial import Delaunay
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
import networkx as nx
from rtree import index  # For efficient spatial adjacency search
import geopandas as gpd
from shapely.geometry import Point
import math
from copy import deepcopy

def generate_delaunary_graph(num_nodes, width, one_way_prob = 0.2, edge_ratio = 0.8):

    """
    Generate a random directed graph with a road-like structure using Delaunay triangulation.
    Parameters
    ----------
    num_nodes : int
        Number of intersections (nodes).
    width : float
        Width of the unit square.
    one_way_prob : float
        Probability that a road is one-way.
    edge_ratio : float
        Probability of keeping additional edges from Delaunay triangulation.
    Returns
    -------
    H : networkx.DiGraph
        Directed graph representing the road-like structure
    """


    # Generate random node positions in a unit square
    points = np.random.rand(num_nodes, 2) * width

    # Compute Delaunay triangulation (planar by definition)
    tri = Delaunay(points)
    H = nx.DiGraph()  # Directed graph

    # Add nodes with positions
    for i, (x, y) in enumerate(points):
        H.add_node(i, pos=(x, y))

    # Add edges from Delaunay triangulation (planar)
    for simplex in tri.simplices:
        for i in range(3):
            u, v = int(simplex[i]), int(simplex[(i + 1) % 3])  # Convert to Python int
            dist = np.linalg.norm(points[u] - points[v])

            # Randomly assign one-way or two-way road
            if np.random.rand() < one_way_prob:  # One-way road
                H.add_edge(u, v, weight=dist)
            else:  # Two-way road
                H.add_edge(u, v, weight=dist)
                H.add_edge(v, u, weight=dist)  # Add reverse edge for two-way road

    # Sparsify, but keep some extra edges to make it denser
    edges = list(H.edges())
    np.random.shuffle(edges)
    for u, v in edges:
        if np.random.rand() > edge_ratio:  # Randomly remove edges with some probability
            weight = H[u][v]['weight']  # Save the weight before removing the edge
            H.remove_edge(u, v)
            if not nx.is_strongly_connected(H):  # Ensure the graph remains weakly connected
                H.add_edge(u, v, weight=weight)  # Restore the edge with its weight

    return H

def compute_shortest_path_distances(H, power = 2):

    """
    Compute shortest path distances raised to the power.
    Parameters:
    -----------
    H : networkx.DiGraph
        Directed graph.
    power : int
        Power to raise the shortest path distances.

    Returns:
    --------
    cost_dict : dict
        Dictionary of shortest path distances raised to the power
    """


    if H is not None:

        shortest_distances = dict(nx.all_pairs_dijkstra_path_length(H, weight='weight'))
        cost_dict = {key: {inner_key: value**power for inner_key, value in inner_dict.items()}
                     for key, inner_dict in shortest_distances.items()}

    return cost_dict

def generate_od_demand_mixed(H, cluster_centers, cluster_radius, is_cluster=True, is_uniform=True, cluster_factor=1):

    """
    Generates origin-destination demand within multiple overlapping clusters and assigns random demand outside the clusters.

    Parameters:
    - H: NetworkX graph with 'pos' node attributes
    - cluster_centers: List of cluster centers in [(x1, y1), (x2, y2), ...]
    - cluster_radius: List of radii for each cluster
    - outside_demand: Boolean indicating whether to generate uniform demand outside clusters

    Returns:
    - demand: Dictionary containing intra-cluster and external demand.
    - cluster_map: Dictionary mapping each node to its assigned clusters.
    """

    nodes = list(H.nodes())
    pos = {n: np.array(H.nodes[n]['pos']) for n in nodes}
    demand = defaultdict(lambda: defaultdict(int))

    if is_cluster:
        cluster_map = defaultdict(list)

        # Assign nodes to multiple clusters
        for n in nodes:
            for c, r in zip(cluster_centers, cluster_radius):
                if np.linalg.norm(pos[n] - np.array(c)) <= r:
                    cluster_map[n].append(tuple(c))

        # Create intra-cluster demand for each cluster separately
        clusters = {tuple(center): [] for center in cluster_centers}
        for n, centers in cluster_map.items():
            for center in centers:
                clusters[center].append(n)

        for cluster_nodes in clusters.values():
            for i in cluster_nodes:
                for j in cluster_nodes:
                    if i != j:
                        demand[i][j] += cluster_factor * np.random.rand()  # Accumulate demand for nodes in multiple clusters

    # Assign uniform demand outside clusters
    if is_uniform:
        for i in nodes:
            for j in nodes:
                if i != j:
                    demand[i][j] += np.random.rand()  # Lower magnitude than intra-cluster demand

    return demand, cluster_map

def visualize_demand_pattern(H, demand, filename="demand_pattern.png"):
    """
    Visualize the demand pattern on a graph.

    Parameters:
    - H: NetworkX graph with 'pos' node attributes
    - demand: Dictionary containing demand between nodes
    - filename: Output filename for the plot
    """
    pos = nx.get_node_attributes(H, 'pos')
    nodes = list(H.nodes())

    total_demand = {n: 0 for n in nodes}
    for i in demand:
        for j in demand[i]:
            total_demand[i] += demand[i][j]  # Outgoing demand
            total_demand[j] += demand[i][j]  # Incoming demand

    max_demand = max(total_demand.values(), default=1)
    node_colors = [total_demand[n] / max_demand for n in nodes]

    x_vals = [pos[n][0] for n in nodes]
    y_vals = [pos[n][1] for n in nodes]

    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(x_vals, y_vals, c=node_colors, cmap='viridis', s=50, alpha=0.7)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Demand Level')
    ax.set_title("Demand Heatmap")

    plt.savefig(filename)
    plt.close()

def generate_dataframe(H, demand, cost_dist, max_diameter):

    pos = nx.get_node_attributes(H, 'pos')
    # edges = list(H.edges())
    nodes = list(H.nodes())
    data = []
    #![Hins] we don't need this
    # max_dist = 0
    
    #![Hins] Remove everything related to info. This is redundant
    # info = {}

    #![Hins] This is problematic. We should consider any pairs of nodes, not only those connected with an edge. The graph is artificial to mimic the road netowrk.
    # for o, d in edges:
    for o, d in permutations(nodes, 2):
        if cost_dist[o][d] > max_diameter:
            continue
        entry = {'origin_node': o, 'dest_node': d, 'origin': (pos[o][0], pos[o][1]), 'dest': (pos[d][0], pos[d][1]), 'dist': cost_dist[o][d],
                'demand': demand[o][d]}
        # info[(pos[o][0], pos[o][1])] = o
        # info[(pos[d][0], pos[d][1])] = d
        # if cost_dist[o][d] > max_dist:
        #   max_dist = cost_dist[o][d]
        data.append(entry)

    df = pd.DataFrame(data)
    return df

# precompute the dictionary of the origins and destinations
def pre_computations(no_of_trips, data):
    origins = dict()
    dest = dict()
    # benefit = dict()
    for trip in range(no_of_trips):
        o = (data.loc[trip, 'origin'])
        d = (data.loc[trip, 'dest'])
        origins[trip] = Point(o)
        dest[trip] = Point(d)
    return origins, dest

# convex hull helper function
def convex_hull_extend(clique, origins, dest, data, visited_cliques):
  
    is_extended = False
  
    # Number of trips (i.e., requests)
    no_of_trips = len(data)

    # origins and dest are calculated before hand
    #![Hins] Do you do this for speed-up? Is Point() slow?
    points = []
    for trip in clique:
        points.append(origins[trip])
        points.append(dest[trip])

    #![Hins] I don't understand why you need this base case?
    # base case
    # if len(points) == 0:
    #   return clique # this is because we do not have any points so clique must be len 0

    # create the convex hull
    convex_hull = MultiPoint(points).convex_hull
    # create the set that will have all the points that have to be grouped together
    extend_set = deepcopy(clique)
    # checks for all the possible trips that could be encapsulated
    for trip in set(range(no_of_trips)) - clique:
        #![Hins] Check if the clique is already visited
        clique_key = tuple(sorted(clique | {trip}))
        if visited_cliques[clique_key] == 1:
            continue
        # this means that the trip is encapsualted by the hull
        if convex_hull.contains(origins[trip]) and convex_hull.contains(dest[trip]):
            extend_set.add(trip)
    if extend_set != clique:
        is_extended = True
    return is_extended, extend_set

  #![Hins] Everything below is redundant
  # # we should only return the extend_set if that is also "serveable"
  # extended = tuple(sorted(extend_set))
  # if clique == extended:
  #   return clique
  # if can_serve_quasi_req(extended, max_diameter, data, distances, connectivity_threshold):
  #   return extended
  # return clique

#![Hins] We don't need this
# pre-processing step to remove the "major" lines
# def reduce(df, major_length):
#   return df[df['dist'] <= major_length]

# Determines if a set of trips can be feasibly shared by checking the total travel distance.
# can be optimized further
#![Hins] Probably we only need the simplified version of this function: we only need to check two requests at a time 
def can_serve_req(requests, max_diameter, data, cost_dist):
    if len(requests) < 2:
        raise ValueError("At least two requests are required.")

    trip_data = [data.loc[req] for req in requests]

    # can serve requests needs to be done in a way that we find the maximum distance between any two points in the trip
    # Extract origin and destination points
    nodes = [trip['origin_node'] for trip in trip_data] + \
                            [trip['dest_node'] for trip in trip_data]
    # we need to try two combinations of all pairs of locations and return the max
    maximum = 0
    for n1, n2 in itertools.combinations(nodes, 2):
        #![Hins] Need to check both directions in case the cost matrix is not symmetric (e.g., in the road network)
        dist = max(cost_dist[n1][n2], cost_dist[n2][n1])
        # return the first instance that satisfies both constraints
        # counts it out in the first go so probably there are a lot more
        # it needs to be actually worth it to share the trips
        if maximum < dist:
            maximum = dist
    return maximum <= max_diameter

def can_serve_quasi_req(requests, pairwise_map, connectivity_threshold):
    
    n = len(requests)
    
    if n == 1:
        raise ValueError("At least two requests are required.")
    if n == 2:
        # return can_serve_req(requests, max_diameter, data, cost_dist)
        return pairwise_map[tuple(sorted(requests))]
    
    #![Hins] We know the # of total pairs and can stop early
    valid_edges = 0
    invalid_edges = 0
    total_pairs = len(requests) * (len(requests) - 1) // 2

    # Evaluate every unique pair in the candidate.
    for pair in itertools.combinations(requests, 2):
        # if can_serve_req((r1, r2), max_diameter, data, cost_dist):
        if pairwise_map[tuple(sorted(pair))]:
            valid_edges += 1
        else:
            invalid_edges += 1			
        
      #![Hins] Early termination
        if valid_edges >= math.ceil(total_pairs * connectivity_threshold):
            return True
        if invalid_edges > total_pairs - math.ceil(total_pairs * connectivity_threshold):
            return False
    # The required number of valid edges is the connectivity threshold times the total possible pairs.
    # required_edges = math.ceil(connectivity_threshold * total_pairs)

    return False


#![Hins] Rewriting the clique generation function
def clique_generator(data, distances, max_diameter, connectivity_threshold):  
    
    # Initialization
    no_of_trips = len(data)
    shared_map = defaultdict(list)
    shared_map[1] = [{trip} for trip in range(no_of_trips)]
    visited_cliques = defaultdict(int)
    card = 2
    # The maximum cardinality seen so far (updated dynamically)
    max_card = 2
    
    # Pre-computation for efficiency
    origins, dest = pre_computations(no_of_trips, data)
    pairwise_map = defaultdict(int)
    for pair in itertools.combinations(range(no_of_trips), 2):
        pair = tuple(sorted(pair))
        pairwise_map[pair] = can_serve_req(pair, max_diameter, data, distances)  

    # Start with cardinality 2
    while True:
        
        # Termination condition
        if card > max_card:
            break

        prev_list = shared_map[card - 1]
        for clique in prev_list:
            for trip in set(range(no_of_trips)) - clique:
                # Check if the new clique is visited already
                clique_key = tuple(sorted(clique | {trip}))
                if visited_cliques[clique_key] == 1:
                    continue
                # Check if the new clique is valid
                if can_serve_quasi_req(clique | {trip}, pairwise_map, connectivity_threshold):
                    
                    # Further checking the convex hull extension
                    is_extended, extended_clique = convex_hull_extend(clique | {trip}, origins, dest, data, visited_cliques)
                    if is_extended:
                        new_card = len(extended_clique)
                        shared_map[new_card].append(extended_clique)
                        clique_key = tuple(sorted(extended_clique))
                        visited_cliques[clique_key] = 1
                        max_card = max(max_card, new_card)
                    else:
                        shared_map[card].append(clique | {trip})
                        clique_key = tuple(sorted(clique | {trip}))
                        visited_cliques[clique_key] = 1
                        max_card = max(max_card, card)
                else:
                    # We also mark the invalid cliques as visited to avoid rechecking
                    clique_key = tuple(sorted(clique | {trip}))
                    visited_cliques[clique_key] = 1
        
        print(f"Cardinality {card} has {len(shared_map[card])} cliques")
        print(f"Cardinality {card} complete")
        
        # Increase the cardinality
        card += 1
      
    # Extract the final list of cliques
    clique_list = []
    for cliques in shared_map.values():
        clique_list.extend(cliques)

    return clique_list, max_card
  


# # the implementation seems to be okay - feasibility is not determined correctly
# # we want to modify generate_shared_trips to basically find the highest cardinality of cliques it can form within a diameter and not be limited by an arg
# # a brute force way to do it is like we keep on increasing cardinality until we have a shared_map[cardinality] has length 0
# def generate_shared_trips_more(no_of_trips, max_diameter, data, distances, connectivity_threshold):
#     # pre-computations and set up
#     not_empty = False # this is to basically do the brute force way because you can't create the next step if there is nothing to share
#     origins, dest = pre_computations(no_of_trips, data)
#     shared_map = {}
#     final_results = []
#     cardinality = 2

#     # we know that at a minimum that we will always have at least 2 trips
#     shared_map[2] = []
#     # combinations already makes it so that order does not matter
#     # forming the base foundation of the cliques of size 2
#     for clique in itertools.combinations(range(no_of_trips), 2):
#       # we can stick to can_serve request in this case bc we are assuming that the connectivity constraint will always be greater than 50%
#       if can_serve_req(clique, max_diameter, data, distances):
#         # if we can serve these two trips
#         # what can be added with convex hull
#         extended_clique = sorted(convex_hull_extend(clique, origins, dest, data))
#         shared_map[2].append(tuple(extended_clique))
#     if len(shared_map[2]) > 0:
#       not_empty = True
#       final_results.extend(shared_map[2])
#     print("cardinality 2 complete")

#     # build candidates for cardinality > 2
#     while not_empty:
#       cardinality += 1
#       shared_map[cardinality] = []

#       # prepare prev candidates for efficient look up
#       prev_list = shared_map[cardinality-1]

#       # generating a dictionary of common prefixes to group the elements
#       groups = dict()
#       for p in prev_list:
#          # exclude the last element and put the prefix in
#          groups.setdefault(tuple(p[:-1]), set()).add(p[-1])  # to make sure that everything is unique
#       # form the new candidates
#       for prefix, last in groups.items():
#         base_length = len(prefix)
#         if len(last) == 2:
#           candidate = prefix + tuple(sorted(last))
#           if can_serve_quasi_req(candidate, max_diameter, data, distances, connectivity_threshold):
#             extended_clique = convex_hull_extend(candidate, origins, dest, data)
#             shared_map[cardinality].append(tuple(extended_clique))
#         if len(last) > 2:
#           # forming the new pairs
#           for pair in itertools.combinations(last, 2):
#             candidate = prefix + tuple(sorted(pair))
#             if can_serve_quasi_req(candidate, max_diameter, data, distances, connectivity_threshold):
#               extended_clique = convex_hull_extend(candidate, origins, dest, data)
#               shared_map[cardinality].append(tuple(extended_clique))

#       # # now that we have a whole new candidate that we can use we can then check if they are valid
#       # for clique in new_candidate:
#       #   # quasi clique generation takes place here
#       #   if can_serve_req(clique, max_diameter, data_reduced, info, distances):
#       #     # we do the same extension that we did above
#       #     extended_clique = convex_hull_extend(clique, origins, dest, data)
#       #     shared_map[cardinality].append(extended_clique)
#       if len(shared_map[cardinality]) > 0:
#         not_empty = True
#         final_results.extend(shared_map[cardinality])
#         print("definitely moving onto cardinality", cardinality + 1)
#       else:
#         not_empty = False # this means that we no longer can extend
#       print(cardinality, "cardinality done")
#     return final_results, cardinality-1

def visualize_optimal_zones(H, zones, filename="zones_plot.png"):

    """
    Visualize the selected zones on a graph.

    Parameters:
    - H: NetworkX graph with 'pos' node attributes
    - zones: List of selected zones, where each zone is a list of node indices
    - filename: Output filename for the plot
    """


    # Graph node positions
    pos = nx.get_node_attributes(H, 'pos')

    # Generate a dynamic list of colors
    cmap = plt.get_cmap("tab10")
    zone_colors = [cmap(i) for i in range(len(zones))]

    # Identify all nodes that are not part of any zone using H.nodes()
    all_zone_nodes = set(node for zone in zones for node in zone)
    non_zone_nodes = set(H.nodes()) - all_zone_nodes

    fig, ax = plt.subplots(figsize=(8, 6))

    # Plot the nodes not part of any zone in gray (from H.nodes())
    non_zone_x_vals = [pos[node][0] for node in non_zone_nodes]
    non_zone_y_vals = [pos[node][1] for node in non_zone_nodes]
    ax.scatter(non_zone_x_vals, non_zone_y_vals, color='gray', s=50, label="Non-Zone Nodes", edgecolor='black', alpha=0.5)

    # Plot each zone with a different color
    for i, zone in enumerate(zones):
        zone_nodes = [node for node in zone if node in pos]
        if zone_nodes:  # Only plot if there are nodes in the current zone
            x_vals_zone = [pos[node][0] for node in zone_nodes]
            y_vals_zone = [pos[node][1] for node in zone_nodes]
            ax.scatter(x_vals_zone, y_vals_zone, color=zone_colors[i], s=100, label=f"Zone {i+1}", edgecolor='black', alpha=0.7)

    # Title and legend
    ax.set_title("Selected Zones Visualization")
    ax.legend()

    # Save the plot instead of showing it
    plt.savefig(filename)
    plt.close()
