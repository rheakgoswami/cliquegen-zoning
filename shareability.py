import pandas as pd  
from geopy.distance import geodesic
from itertools import permutations
import itertools
from shapely.wkt import loads
from shapely.geometry import LineString, Point

def reduce(df, major_length):
  return df[df['distance_kilometers'] <= major_length]

# Determines if a set of trips can be feasibly shared by checking the total travel distance.
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
    min_dist = unshared_dist
    for combo in permutations(locations):
        dist = sum(geodesic(combo[i], combo[i + 1]).km for i in range(len(combo) - 1))
        # return the first instance that satisfies both constraints
        if dist < min_dist and min_dist <= max_diameter:
            return True
    return False

# the implementation seems to be okay - feasibility is not determined correctly
def generate_shared_trips_more(no_of_trips, max_cardinality, max_diameter, data_reduced):
    shared_map = {}
    final_results = []
    cardinality = 2
    not_found = 0
    found = 0
    feasible_num = 0

    # we know that at a minimum that we will always have at least 2 trips
    shared_map[2] = []
    for requests in itertools.combinations(range(no_of_trips), 2):
      if can_serve_req(requests, max_diameter):
        shared_map[2].append(requests)
    final_results.extend(shared_map[2])

    # build candidates for cardinality > 2
    while cardinality <= max_cardinality:
      next_card = cardinality + 1
      shared_map[next_card] = []

      # prepare prev candidates for efficient look up
      tried = set()
      prev_list = shared_map[cardinality]
      l_prev = len(prev_list)
      prev_shared = set(prev_list)

      # combine pairs of previous candidates to form next valid candidates
      for i in range(l_prev):
        for j in range(i+1, l_prev):
          t1 = prev_list[i]
          t2 = prev_list[j]
          # common - they should have one element difference
          # check that at the beginning they have the same ordering of trips
          if t1[:-1] == t2[:-1]:
            new_candidate = t1 + (t2[-1],)
            if new_candidate in tried:
              continue
            tried.add(new_candidate)

            # now check that every sub combination of the new candidate exists
            # at prev level
            candidate_valid = True
            for sub in itertools.combinations(new_candidate, cardinality):
              # sub is already a sorted tuple because new_candidate is sorted.
              if sub not in prev_shared:
                candidate_valid = False
                not_found += 1
                break
            if candidate_valid:
              found += 1
              if can_serve_req(new_candidate, max_diameter, data_reduced):
                feasible_num += 1
                shared_map[next_card].append(new_candidate)

      final_results.extend(shared_map[next_card])
      cardinality += 1

    print("# Feasible: ", feasible_num)
    print("# Found: ", found)
    print("# Not Found: ", not_found)
    return final_results

def main(): 
    df = pd.read_csv('new_synthetic_data.csv')

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

