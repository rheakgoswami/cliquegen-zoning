from utils import generate_delaunary_graph, compute_shortest_path_distances, generate_od_demand_mixed, generate_dataframe, clique_generator
from utils import visualize_demand_pattern, visualize_optimal_zones
import numpy as np
import gurobipy as gp
from gurobipy import GRB
from gurobipy import Model, GRB, quicksum


def main(): 

  #! [Hins] Parameters
  NUM_ZONES = 4
  MAX_DIAMETER = 1.5
  CONNECTIVITY = 1
    
  # Random seed
  seed = 42
  np.random.seed(seed)

  # Generate the graph
  G = generate_delaunary_graph(50, 10, one_way_prob=0, edge_ratio=0.8)

  # Compute shortest path distances
  # [Hins] Use the original distance but not the square one
  distances = compute_shortest_path_distances(G, power = 1)

  # Generate demand with a mixed distribution (clusters + uniform)
  centers = [(1.8, 6.3), (2.8, 2), (9.5, 3.8)]
  radius = [1, 1, 1]
  demand, _ = generate_od_demand_mixed(G, centers, radius, cluster_factor=10)
  visualize_demand_pattern(G, demand, filename="demand_pattern.png")

  #![Hins] No max_dist
  data = generate_dataframe(G, demand, distances, MAX_DIAMETER)
  print(data)
  # print(max_dist)

  #![Hins] Why set is as a different parameter? Shouldn't it be MAX_DIAMETER?
  #![Hins] Also, you can filter out those long trips when creating them, no need to loop over them again
  # major_length = 4
  # data_reduced = reduce(data, major_length)
  # data_reduced.reset_index(drop=True, inplace=True)
  # print(data_reduced)

  # can change the connectivity constraint and your max diameter
  #![Hins] Use data not data_reduced (it was reduced inside while being created)
  lst, cardinality = clique_generator(data, distances, MAX_DIAMETER, CONNECTIVITY)
  
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

  # optimization based on the lst
  benefit = {}
  for clique in lst:
    total = 0
    for trip in clique:
      total += data.loc[trip, 'demand']
    benefit[clique] = total

  # print(benefit)

  # i do not know if these params will work but will debug later
  params = {
  "WLSACCESSID": '3d967c9e-4aa5-4f43-a846-07dfc27bf8ed',
  "WLSSECRET": 'd352f07c-2cc8-4cd9-9e9a-a2099278483f',
  "LICENSEID": 2654733,
  }
  env = gp.Env(params=params)
  model = gp.Model(env=env)
  # create decision variables - we make one to indicate if the clique is chosen or not
  y = {}
  # stores whether or not it is a 1 or 0 basically (selected or not)
  for clique in lst:
    y[clique] = model.addVar(vtype = GRB.BINARY, obj = benefit[clique], name=f"y_{clique}")
  # objective function
  model.setObjective(gp.quicksum(benefit[clique] * y[clique] for clique in lst), GRB.MAXIMIZE)
  # constraints
  # ensuring that the cliques selected do not overlap
  #! [Hins] Use all nodes in G is fine. You don't need to create the nodes again
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
  model.addConstr(
      gp.quicksum(y[clique] for clique in lst) <= NUM_ZONES
  )

  model.optimize()

  if model.status == GRB.OPTIMAL:
    selected_zones = [clique for clique in lst if y[clique].X > 0.5]
    print("Selected candidate zones:", selected_zones)
    print("Optimal total benefit:", model.objVal)
  
  #post_processing of zones with nodes instead
  l = []
  for zones in selected_zones:
    z = set()
    for trip in zones:
      z.add(data.loc[trip, 'origin_node'])
      z.add(data.loc[trip, 'dest_node'])
    l.append(list(z))

  visualize_optimal_zones(G, l)

if __name__ == "__main__":
    main()