import pandas as pd  
from geopy.distance import geodesic
from itertools import permutations
import itertools
from shapely.wkt import loads
from shapely.geometry import LineString, Point
import numpy as np
import os

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
    shared_map = {}
    final_results = []
    cardinality = 2

    # we know that at a minimum that we will always have at least 2 trips
    shared_map[2] = []
    # combinations already makes it so that order does not matter
    # forming the base foundation of the cliques of size 2
    for requests in itertools.combinations(range(no_of_trips), 2):
      if can_serve_req(requests, max_diameter, data_reduced):
        shared_map[2].append(requests)
    final_results.extend(shared_map[2])
    print("cardinality 2 complete")

    # build candidates for cardinality > 2
    while cardinality != max_cardinality:
      cardinality += 1
      shared_map[cardinality] = []

      # prepare prev candidates for efficient look up
      prev_list = shared_map[cardinality-1]
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
      for candidate in new_candidate: 
         # now we try all the different orders to see what works in terms of serving the request
         for order in itertools.combinations(candidate, cardinality): 
            # i think a part of the optimization problem is just the sheer number of combinations we have to test
            if can_serve_req(order, max_diameter, data_reduced):
              shared_map[cardinality].append(order)
            
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

    lst = generate_shared_trips_more(len(data_reduced), 3, 5, data_reduced)
    print(lst)
    print(len(lst))

    counter_3 = 0
    counter_4 = 0
    for i in lst:
        if len(i) == 3:
            counter_3 += 1
        if len(i) == 4: 
            counter_4 += 1
    print("Counter 3:", counter_3)
    print("Counter 4:", counter_4)

if __name__ == "__main__":
    main()

