from utils import generate_delaunary_graph, compute_shortest_path_distances, generate_od_demand_mixed, generate_dataframe, clique_generator_on_map
from utils import visualize_demand_pattern, visualize_optimal_zones, solve_ILP, visualize_graph, baseline_A, calculate_total_demand_served
import numpy as np
import gurobipy as gp
from gurobipy import GRB
import os
import cProfile
import pstats

def main(): 

  #! [Hins] Parameters
  NUM_ZONES = 4
  MAX_DIAMETER = 3
  CONNECTIVITY = 1
  ALGO = "clique_generation" # "clique_generation" or "baseline_A"
  NUM_NODE = 200
  seed = 42
  np.random.seed(seed)
  
  #![Hins] Create an output folder
  if not os.path.exists("output"):
    os.makedirs("output")

  # Generate the graph
  G = generate_delaunary_graph(NUM_NODE, 10, one_way_prob=0, edge_ratio=0.8)
  
  #![Hins] Debugging
  # visualize_graph(G)

  # Compute shortest path distances
  # [Hins] Use the original distance but not the square one
  distances = compute_shortest_path_distances(G, power = 1)

  # Generate demand with a mixed distribution (clusters + uniform)
  centers = [(1.8, 6.3), (2.8, 2), (9.5, 3.8)]
  radius = [1, 1, 1]
  demand, _ = generate_od_demand_mixed(G, centers, radius, cluster_factor=10)
  visualize_demand_pattern(G, demand, filename="output/demand_pattern.png")

  #![Hins] No max_dist
  #![Hins] We don't need this
  # data = generate_dataframe(G, demand, distances, MAX_DIAMETER)
  # print(data)
  # print(max_dist)

  #![Hins] Why set is as a different parameter? Shouldn't it be MAX_DIAMETER?
  #![Hins] Also, you can filter out those long trips when creating them, no need to loop over them again
  # major_length = 4
  # data_reduced = reduce(data, major_length)
  # data_reduced.reset_index(drop=True, inplace=True)
  # print(data_reduced)

  # can change the connectivity constraint and your max diameter
  #![Hins] Use data not data_reduced (it was reduced inside while being created)
  # lst, cardinality = clique_generator(data, distances, MAX_DIAMETER, CONNECTIVITY)
  
  if ALGO == "clique_generation":
    lst, cardinality = clique_generator_on_map(G, MAX_DIAMETER, distances, CONNECTIVITY)
    
    print(len(lst))
    print("Highest Cardinality", cardinality)

    # need to fix there is a better way to do this 
    # d = {2: [], 3: [], 4: [], 5:[], 6:[], 7:[], 8:[], 9:[], 10:[], 11:[], 12:[], 13:[], 14: [], 15:[], 16:[], 17:[]}
    # sum = 0
    # for i in lst:
    #   d[len(i)].append(i)
    #   sum += 1
    # for i in d.keys():
    #   print("Cardinality-" + str(i) + ": " + str(len(d[i])))
    # saved_lst = lst
    # print(sum)
    
    #![Hins] Use an updated ILP solver
    # l = solve_ILP_Rhea(lst, data, NUM_ZONES)
    selected_zones = solve_ILP(G, lst, demand, NUM_ZONES)
    print("Selected zones:", selected_zones)
    print("Total demand served:", calculate_total_demand_served(selected_zones, demand))
    visualize_optimal_zones(G, selected_zones, filename="output/optimal_zones.png")
  
  elif ALGO == "baseline_A":
    selected_zones = baseline_A(G, demand, MAX_DIAMETER, distances, NUM_ZONES)
    print("Selected zones:", selected_zones)
    print("Total demand served:", calculate_total_demand_served(selected_zones, demand))
    visualize_optimal_zones(G, selected_zones, filename="output/zones_by_heuristic.png")
    
  else:
    raise ValueError("Invalid algorithm selected. Choose 'clique_generation' or 'baseline_A'.")
  

if __name__ == "__main__":

  #![Hins] Everything here is for profiling
  # profiler = cProfile.Profile()
  # profiler.enable()
  # try:
  main()
  # except MemoryError:
  #   print("Program terminated due to OOM error.")
  # finally:
  #   profiler.disable()
  #   stats = pstats.Stats(profiler)
  #   stats.strip_dirs()
  #   stats.sort_stats("cumulative")

  #   # Save profiling results to a file
  #   with open("profile.out", "w") as f:
  #       stats.stream = f  # Redirect output to the file
  #       stats.print_stats()

  #   # Print profiling results to stdout (captured in nohup log)
  #   print("Profiling results:")
  #   stats.stream = None  # Reset output to stdout
  #   stats.print_stats(20)  # Print the top 20 functions
