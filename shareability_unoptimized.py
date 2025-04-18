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

# changed data generation function 
def generate_realistic_data():
    file_path = os.path.join(os.path.dirname(__file__), "lodes_2021-01-04.csv")
    df = pd.read_csv(file_path)

    # Select ~15 cluster centers (mimicking urban/suburban hubs)
    num_clusters = 15
    cluster_centers = df.sample(n=num_clusters)[["origin_loc_lat", "origin_loc_lon"]].values

    rows = []

    for center_lat, center_lon in cluster_centers:
        for _ in range(20):  # 20 trips per cluster

            # Assign total_jobs (trip intensity)
            total_jobs = np.random.randint(1, 101)

            # Pick origin near the cluster center (small dispersion)
            origin_radius_km = np.random.uniform(0.1, 1.5)
            origin_lat_shift = np.random.uniform(-1, 1) * origin_radius_km / 111  # ~111 km per degree lat
            origin_lon_shift = np.random.uniform(-1, 1) * origin_radius_km / (111 * np.cos(np.radians(center_lat)))
            origin_lat = center_lat + origin_lat_shift
            origin_lon = center_lon + origin_lon_shift

            # Assign a realistic destination distance
            rand_val = np.random.rand()
            if rand_val < 0.6:
                trip_distance_km = np.random.uniform(1, 3)
            elif rand_val < 0.9:
                trip_distance_km = np.random.uniform(3, 8)
            else:
                trip_distance_km = np.random.uniform(8, 20)

            # Perturb destination
            angle = np.random.uniform(0, 2 * np.pi)
            dest_lat = origin_lat + (trip_distance_km / 111) * np.sin(angle)
            dest_lon = origin_lon + (trip_distance_km / (111 * np.cos(np.radians(origin_lat)))) * np.cos(angle)

            rows.append({
                "total_jobs": total_jobs,
                "origin_loc_lat": origin_lat,
                "origin_loc_lon": origin_lon,
                "dest_loc_lat": dest_lat,
                "dest_loc_lon": dest_lon,
                "origin_geom": f"POINT ({origin_lon} {origin_lat})",
                "dest_geom": f"POINT ({dest_lon} {dest_lat})",
            })

    synthetic_df = pd.DataFrame(rows)
    synthetic_df.to_csv('new_synthetic_data_realistic.csv', index=False)

# precompute the dictionary of the origins and destinations
def pre_computations(no_of_trips, data_reduced):
  origins = dict()
  dest = dict() 
  distance = dict()
  for trip in range(no_of_trips): 
    o = (data_reduced.loc[trip, 'origin_loc_lat'], data_reduced.loc[trip, 'origin_loc_lon'])
    d = (data_reduced.loc[trip, 'dest_loc_lat'], data_reduced.loc[trip, 'dest_loc_lon'])
    origins[trip] = Point(o)
    dest[trip] = Point(d)
    distance[trip] = data_reduced.loc[trip, 'distance_kilometers']
  return origins, dest, distance

# convex hull helper function 
def convex_hull_extend(clique, origins, dest, no_of_trips):
  # origins and dest are calculated before hand 
  extension = False
  points = []
  # BUG - points is never acucumulated with the clique trips
  for trip in clique: 
    points.append(origins[trip])
    points.append(dest[trip])

  # base case 
  if len(points) == 0: 
    return clique # this is because we do not have any points so clique must be len 0
  
  # create the convex hull 
  convex_hull = MultiPoint(points).convex_hull 
  # create the set that will have all the points that have to be grouped together 
  extend_set = set(clique)
  # checks for all the possible trips that could be encapsulated 
  for trip in range(no_of_trips):
    if trip not in clique: 
      # this means that the trip is encapsualted by the hull 
      if convex_hull.contains(origins[trip]) and convex_hull.contains(dest[trip]):
        extend_set.add(trip)
        print("trip extended!")
        # later we can set a bool to basically add it to a special "extended" array
        extension = True
  return tuple(sorted(extend_set))

def reduce(df, major_length):
  return df[df['distance_kilometers'] <= major_length]

# Determines if a set of trips can be feasibly shared by checking the total travel distance.
# can be optimized further
def can_serve_req(requests, max_diameter, data_reduced):
    if len(requests) < 2:
        return False

    trip_data = [data_reduced.loc[req] for req in requests]

    # Compute unshared distance
    unshared_dist = sum(trip['distance_kilometers'] for trip in trip_data)

    # Extract origin and destination points
    locations = [(trip['origin_loc_lat'], trip['origin_loc_lon']) for trip in trip_data] + \
                [(trip['dest_loc_lat'], trip['dest_loc_lon']) for trip in trip_data]

    # Limit the number of permutations for efficiency (factorial growth is problematic)
    if len(locations) > 40320:  # 8! = 40320 is a practical cutoff for right now
        print("Too many permutations; aborting for efficiency.")
        return False

    # Try all permutations to find the shortest shared path
    for combo in permutations(locations):
        dist = sum(geodesic(combo[i], combo[i + 1]).km for i in range(len(combo) - 1))
        # return the first instance that satisfies both constraints
        # counts it out in the first go so probably there are a lot more 
        # it needs to be actually worth it to share the trips
        if dist < unshared_dist and dist <= max_diameter:
            return True
    return False

# the implementation seems to be okay - feasibility is not determined correctly
def generate_shared_trips_more(no_of_trips, max_cardinality, max_diameter, data_reduced):
    # pre-computations and set up 
    origins, dest, dist = pre_computations(no_of_trips, data_reduced)
    shared_map = {}
    final_results = []
    cardinality = 2

    # we know that at a minimum that we will always have at least 2 trips
    shared_map[2] = []
    # combinations already makes it so that order does not matter
    # forming the base foundation of the cliques of size 2
    for clique in itertools.combinations(range(no_of_trips), 2):
      if can_serve_req(clique, max_diameter, data_reduced):
        # if we can serve these two trips 
        # what can be added with convex hull 
        extended_clique = convex_hull_extend(clique, origins, dest, no_of_trips)
        # well we need to add it to the correct length lowkey LOL which may not always be shared_map[2]
        # well technically actually we do not
        # since we are "encapsulating" cliques that are actually of size 2 but becom bigger
        shared_map[2].append(extended_clique)
    final_results.extend(shared_map[2])
    print("cardinality 2 complete")

    # build candidates for cardinality > 2
    while cardinality != max_cardinality:
      cardinality += 1
      shared_map[cardinality] = []

      # prepare prev candidates for efficient look up
      prev_list = shared_map[cardinality-1]
      # possible new candidates that we need to check basically
      # we could 
      new_candidate = []

      # generating a dictionary of common prefixes to group the elements 
      groups = dict()
      for p in prev_list: 
         # exclude the last element and put the prefix in 
         groups.setdefault(p[:-1], set()).add(p[-1])  # to make sure that everything is unique
      # form the new candidates
      for prefix, last in groups.items(): 
         # this means that we just tack both of them on 
         # if there is only one we can't create a new size
        if len(last) == 2: 
          new_candidate.append(prefix + tuple(sorted(last)))
        if len(last) > 2:
          # forming the new pairs
          for pair in itertools.combinations(last, 2): 
            new_candidate.append(prefix + pair)
      
      # now that we have a whole new candidate that we can use we can then check if they are valid 
      for clique in new_candidate:
        # i think a part of the optimization problem is just the sheer number of combinations we have to test
        # removed the number of combinations because we actually do not need to worry about that since serve_req handles that 
        if can_serve_req(clique, max_diameter, data_reduced):
          # we do the same extension that we did above 
          extended_clique = convex_hull_extend(clique, origins, dest, no_of_trips)
          shared_map[cardinality].append(clique)
      final_results.extend(shared_map[cardinality])
      print(cardinality, "cardinality done")
    return final_results

def main(): 
    filepath = os.path.join(os.path.dirname(__file__), "new_synthetic_data_realistic_short.csv")
    df = pd.read_csv(filepath)

    # Displaying the first few rows of the DataFrame
    len_trips = 300
    data = df.head(len_trips)
    data['origin_geom'] = data['origin_geom'].apply(loads)
    data['dest_geom'] = data['dest_geom'].apply(loads)
    data['line'] = data.apply(lambda x: LineString([x['origin_geom'], x['dest_geom']]),axis=1)
    data['distance_kilometers'] = data.apply(lambda x: geodesic((x['origin_geom'].y, x['origin_geom'].x),
                        (x['dest_geom'].y, x['dest_geom'].x)).meters/1000, axis=1)
    print(data)

    # pre-processing (not as relevant)
    major_length = 5
    data_reduced = reduce(data, major_length)
    data_reduced.reset_index(drop=True, inplace=True)
    print(data_reduced)

    lst = generate_shared_trips_more(len(data_reduced), 3, 7, data_reduced)
    print(lst)
    print(len(lst))

    counter_2 = 0
    counter_3 = 0
    counter_4 = 0
    counter_5 = 0
    for i in lst:
        if len(i) == 2: 
            counter_2 += 1
        if len(i) == 3:
            counter_3 += 1
        if len(i) == 4:
            counter_4 += 1
        if len(i) == 5: 
            counter_5 += 1
    print("Counter 2:", counter_2)
    print("Counter 3:", counter_3)
    print("Counter 4:", counter_4)
    print("Counter 5:", counter_5)
    print(counter_2 + counter_3 + counter_4 + counter_5)

    # optimization based on the lst
    # for max cardinality 3 and max diameter = 7 w/ convex hull changes
    lst = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 8), (0, 9), (0, 12), (0, 13), (1, 3), (1, 4), (1, 8), (1, 10), (1, 12), (2, 4), (3, 4), (3, 8), (3, 11), (3, 12), (4, 7), (4, 11), (6, 13), (6, 199), (7, 11), (10, 12), (11, 12), (15, 22), (15, 23), (15, 24), (15, 25), (15, 26), (15, 28), (16, 23), (16, 25), (16, 27), (16, 29), (17, 25), (18, 19), (20, 22), (20, 24), (20, 26), (20, 28), (20, 29), (21, 23), (22, 24), (22, 26), (22, 28), (22, 29), (23, 24), (23, 25), (23, 26), (23, 29), (24, 25), (24, 26), (24, 29), (25, 26), (25, 29), (26, 28), (26, 29), (30, 33), (30, 41), (30, 104), (30, 117), (30, 143), (31, 35), (31, 39), (31, 106), (31, 109), (32, 39), (32, 40), (32, 41), (32, 42), (32, 43), (32, 105), (32, 106), (32, 108), (32, 109), (32, 110), (32, 111), (32, 112), (32, 113), (32, 114), (32, 117), (32, 118), (32, 134), (32, 137), (32, 139), (32, 141), (32, 143), (32, 145), (33, 38), (33, 39), (33, 40), (33, 41), (33, 42), (33, 104), (33, 105), (33, 110), (33, 114), (33, 117), (33, 118), (33, 143), (34, 38), (34, 42), (34, 110), (34, 116), (35, 106), (36, 39), (36, 40), (36, 43), (36, 109), (36, 110), (38, 39), (38, 40), (38, 41), (38, 42), (38, 104), (38, 105), (38, 110), (38, 116), (39, 41), (39, 43), (39, 105), (39, 109), (39, 110), (39, 114), (39, 118), (39, 143), (40, 41), (40, 42), (40, 43), (40, 104), (40, 105), (40, 109), (40, 110), (40, 115), (40, 145), (41, 104), (41, 105), (41, 107), (41, 108), (41, 110), (41, 111), (41, 114), (41, 117), (41, 118), (41, 143), (42, 104), (42, 107), (42, 108), (42, 110), (42, 111), (42, 114), (42, 118), (42, 138), (42, 143), (43, 104), (43, 106), (43, 108), (43, 109), (43, 110), (43, 112), (43, 113), (43, 115), (43, 141), (43, 143), (43, 145), (44, 45), (44, 51), (44, 52), (44, 53), (44, 54), (44, 55), (44, 56), (44, 57), (44, 58), (44, 59), (45, 48), (45, 55), (45, 58), (46, 49), (46, 50), (46, 56), (46, 57), (47, 49), (47, 50), (47, 54), (47, 56), (47, 57), (47, 59), (48, 59), (49, 50), (49, 56), (49, 57), (49, 58), (49, 59), (50, 54), (50, 56), (50, 59), (51, 52), (52, 54), (52, 57), (52, 58), (52, 59), (53, 55), (54, 59), (55, 58), (55, 59), (56, 57), (57, 58), (57, 59), (60, 63), (60, 64), (60, 68), (60, 74), (61, 66), (61, 72), (61, 74), (62, 64), (62, 65), (62, 67), (62, 68), (63, 66), (63, 68), (63, 71), (63, 74), (64, 65), (64, 67), (64, 68), (64, 70), (64, 74), (65, 67), (66, 69), (66, 72), (66, 74), (67, 68), (68, 70), (68, 72), (69, 71), (69, 74), (70, 72), (70, 73), (70, 74), (72, 74), (75, 83), (76, 79), (77, 80), (77, 89), (78, 79), (79, 84), (79, 87), (79, 89), (80, 84), (80, 89), (81, 82), (81, 85), (82, 84), (82, 85), (84, 85), (84, 87), (84, 89), (85, 87), (85, 89), (87, 89), (90, 91), (90, 92), (90, 93), (90, 94), (90, 95), (90, 96), (90, 100), (90, 101), (90, 102), (91, 96), (91, 99), (92, 93), (92, 94), (92, 95), (92, 98), (93, 94), (93, 95), (93, 98), (94, 95), (94, 96), (94, 98), (94, 100), (95, 96), (95, 98), (95, 99), (95, 100), (96, 99), (96, 101), (96, 102), (99, 101), (99, 102), (104, 105), (104, 107), (104, 108), (104, 111), (104, 112), (104, 113), (104, 114), (104, 117), (104, 138), (104, 141), (104, 143), (105, 110), (105, 114), (105, 116), (105, 118), (105, 143), (106, 109), (106, 112), (106, 141), (106, 145), (107, 118), (107, 138), (107, 143), (108, 111), (108, 113), (108, 114), (108, 115), (108, 117), (108, 118), (108, 141), (108, 143), (108, 145), (109, 110), (110, 114), (110, 116), (110, 143), (111, 114), (111, 118), (111, 141), (112, 113), (112, 141), (112, 145), (113, 115), (113, 139), (113, 141), (113, 143), (113, 145), (114, 118), (114, 143), (117, 118), (117, 133), (117, 135), (117, 136), (117, 138), (117, 143), (117, 144), (118, 138), (118, 143), (120, 122), (121, 125), (121, 127), (121, 128), (122, 128), (122, 129), (122, 130), (123, 129), (124, 125), (125, 127), (125, 128), (126, 127), (126, 128), (126, 129), (127, 128), (128, 129), (128, 130), (132, 135), (132, 136), (132, 144), (133, 134), (133, 135), (133, 136), (133, 137), (133, 138), (133, 140), (133, 143), (133, 144), (134, 143), (134, 145), (135, 136), (135, 138), (135, 144), (136, 139), (136, 144), (137, 139), (137, 140), (137, 141), (137, 143), (137, 145), (138, 143), (139, 141), (139, 143), (139, 145), (141, 145), (146, 150), (146, 152), (146, 153), (146, 156), (146, 159), (147, 148), (147, 151), (147, 152), (147, 154), (147, 155), (147, 156), (147, 157), (147, 159), (147, 160), (148, 154), (148, 156), (148, 157), (148, 159), (149, 155), (149, 159), (150, 152), (150, 153), (150, 154), (150, 156), (151, 160), (152, 153), (152, 159), (152, 160), (153, 156), (153, 159), (154, 156), (154, 159), (155, 160), (156, 158), (156, 159), (158, 159), (161, 162), (161, 167), (161, 168), (161, 173), (162, 168), (162, 170), (164, 169), (165, 169), (165, 173), (167, 168), (167, 172), (168, 170), (168, 173), (169, 173), (171, 172), (174, 178), (174, 181), (174, 182), (174, 185), (174, 187), (174, 188), (175, 178), (175, 180), (177, 178), (177, 181), (177, 182), (177, 184), (178, 179), (178, 180), (178, 181), (178, 182), (178, 184), (178, 185), (178, 186), (178, 188), (179, 186), (181, 182), (181, 184), (181, 185), (181, 186), (181, 187), (181, 188), (182, 184), (182, 185), (182, 186), (184, 186), (185, 187), (185, 188), (187, 188), (189, 196), (190, 191), (190, 193), (190, 197), (190, 200), (191, 193), (191, 197), (192, 194), (192, 196), (192, 199), (192, 200), (193, 197), (193, 200), (194, 196), (194, 199), (195, 196), (195, 198), (196, 200), (198, 200), (202, 206), (202, 207), (202, 209), (202, 210), (202, 212), (202, 213), (202, 214), (202, 215), (202, 216), (203, 206), (204, 216), (205, 217), (206, 208), (206, 210), (206, 211), (206, 212), (206, 213), (206, 214), (206, 215), (206, 216), (206, 217), (207, 212), (207, 213), (207, 214), (208, 209), (208, 210), (208, 211), (208, 215), (209, 210), (209, 215), (209, 216), (209, 217), (210, 214), (210, 215), (210, 216), (210, 217), (211, 215), (211, 216), (212, 216), (213, 214), (213, 216), (214, 217), (215, 216), (215, 217)]
    # create benefit - from above
    benefit = {}
    for i in lst: 
        total = 0
        for trip in i:
            total += b[trip]
        benefit[i] = total

    model = gp.Model("ZoneSelection")
    # create decision variables - we make one to indicate if the clique is chosen or not 
    y = {}
    # stores whether or not it is a 1 or 0 basically (selected or not)
    for clique in lst: 
        y[clique] = model.addVar(vtype = GRB.BINARY, obj = benefit[clique], name=f"y_{clique}")
    # objective function
    model.setObjective(gp.quicksum(benefit[clique] * y[clique] for clique in lst), GRB.MAXIMIZE)
    # constraints 

    # ensuring that the cliques selected do not overlap 
    nodes = set()
    for clique in lst: 
        for n in clique: 
            nodes.add(n)
    # create the constraint that one node can only be selected at one time (non-overlapping)
    for n in nodes: 
    # we only need to add the constraint if it is acc in the clique
        model.addConstr(
            gp.quicksum(y[clique] for clique in lst if n in clique) <= 1
        )

    # adding the constraint that we need to select less than m 
    # let's set m to 10
    model.addConstr(
        gp.quicksum(y[clique] for clique in lst) <= 10
    )

    model.optimize()

    if model.status == GRB.OPTIMAL: 
        selected_zones = [clique for clique in lst if y[clique].X > 0.5]
    print("Selected candidate zones:", selected_zones)
    print("Optimal total benefit:", model.objVal)

if __name__ == "__main__":
    main()

