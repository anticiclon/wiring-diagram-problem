# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 16:51:58 2024

@author: Trabajador
"""

import networkx as nx
import auxiliar as aux
import random as rd
import gurobipy as gb
import drawing
import math
import shutil
import copy
from networkx.drawing.nx_pydot import graphviz_layout
import pickle
import os
import matplotlib.pyplot as plt



# =============================================================================
def generateBasicTree(nodes_in_tree):
    """
    Generates a directed tree with `nodes_in_tree` nodes. The nodes are properly enumerated, 
    and the tree structure is randomized but follows a consistent direction for each edge.
    
    Parameters:
    nodes_in_tree : int
        The number of nodes in the generated tree.

    Returns:
    new_tree : DiGraph
        A directed tree graph with `nodes_in_tree` nodes, created from a randomly generated tree structure.
    """ 
    # Step 1: Generate a random undirected tree with `nodes_in_tree` nodes
    tree = nx.random_tree(nodes_in_tree)
    
    # Step 2: Traverse the tree to establish a consistent node order
    # Starting from node 0, generate a list of nodes in traversal order
    start_node = 0
    visited_nodes = aux.traverseTreeGraph(start_node, [start_node], tree)

    # Step 3: Create a mapping between traversal order and actual nodes in the tree
    node_mapping = dict(zip(visited_nodes, list(tree.nodes)))

    # Step 4: Initialize a new directed graph to store the directed tree
    new_tree = nx.DiGraph()
    
    # Step 5: Add nodes to the directed graph with mapped node identifiers
    for original_node in tree.nodes:
        new_tree.add_node(node_mapping[original_node])  # Adding nodes with new enumerated IDs
    
    # Step 6: Add directed edges to the new tree, ensuring consistent direction
    for edge in tree.edges:
        node_u, node_v = node_mapping[edge[0]], node_mapping[edge[1]]
        # Direct the edge from the smaller node to the larger node for consistency
        if node_u < node_v:
            new_tree.add_edge(node_u, node_v)
        else:
            new_tree.add_edge(node_v, node_u)
    
    return new_tree
# =============================================================================


# =============================================================================
def generateTree(n, b, s, x_min, y_min, z_min, x_max, y_max, z_max, x_min_root, x_max_root):
    """
    Creates a directed tree with `n` nodes. Each node is assigned spatial attributes based on its type:
    root, valve, or leaf. Spatial parameters define 3D bounds within which nodes are placed.

    Parameters:
    n : int
        The number of nodes in the tree.
    b : int
        Number of spatial attribute "boxes" associated with each valve node.
    s : int
        Half the length of a spatial box's edge, determining its size.
    x_min, y_min, z_min, x_max, y_max, z_max : int
        Bounds for the 3D spatial coordinates of non-root nodes.
    x_min_root, x_max_root : int
        Bounds for the x-coordinate of root nodes.

    Returns:
    T : DiGraph
        A directed tree graph with `n` nodes, each having attributes (type, center, epsilon, space, position).
    """
    # Step 1: Generate the tree structure
    T = generateBasicTree(n)

    # Step 2: Initialize dictionary to store node attributes
    node_attributes = {}

    # Step 3: Assign attributes for each node based on its type (root, valve, or leaf)
    for node in T.nodes:
        # Determine the type of node based on its position in the tree
        children = list(nx.descendants(T, node))  # List of all descendants of the node

        # Initialize empty attribute dictionaries for each category
        spaces = {}
        centers = {}
        epsilons = {}

        if node == 0:
            # Root node attributes
            node_attribute = {"type": "root"}
        
        elif children:
            # Valve node with `b` spatial attribute boxes
            for box_index in range(b):
                # Generate random position for the valve's bounding box within given limits
                position = (rd.randint(x_min, x_max - s),
                            rd.randint(y_min, y_max - s),
                            rd.randint(z_min, z_max - s))
                
                # Define the spatial box as a bounding box in 3D space
                space = ((position[0], position[1], position[2]),
                         (position[0] + 2 * s, position[1] + 2 * s, position[2] + 2 * s))
                spaces[box_index] = space

                # Calculate center and epsilon for each spatial box
                center = (position[0] + s, position[1] + s, position[2] + s)
                centers[box_index] = center
                epsilon = (s, s, s)  # Epsilon represents the half-size of the bounding box
                epsilons[box_index] = epsilon

            # Set valve node attributes
            node_attribute = {
                "type": "valve",
                "center": centers,
                "epsilon": epsilons,
                "space": spaces
            }
        
        else:
            # Leaf node attributes with a position only
            position = (rd.randint(x_min_root, x_max_root),
                        rd.randint(y_min, y_max),
                        rd.randint(z_min, z_max))
            node_attribute = {"type": "leaf", "position": position}

        # Add node attributes to the dictionary
        node_attributes[node] = node_attribute

    # Step 4: Set attributes for each node in the tree
    nx.set_node_attributes(T, node_attributes)
    
    return T
# =============================================================================

# =============================================================================
def tracePathsSinglePath(G, draw_solution=False):
    """
    Optimizes a network flow to trace paths between source and destination nodes in a directed graph `G`.
    
    Parameters:
    G : Graph
        A NetworkX directed graph with source and destination attributes for nodes.
    draw_solution : bool, optional
        If True, draws the traced paths using an external `drawing` module.
        
    Returns:
    solution : list
        List of solutions, each representing an ordered path for a source-destination pair.
    """
    
    # Load nodes and edges
    nodes = G.nodes()
    edges = G.edges()

    # Create optimization model
    model = gb.Model('network_flow')

    # Identify sources and destinations
    sources = [G.nodes[i]['source'] for i in G.nodes if 'source' in G.nodes[i]]
    source_nodes = {}
    dest_nodes = {}

    # Map sources and destinations based on node attributes
    for src in sources:
        source_nodes[src] = [i for i in G.nodes 
                              if 'source' in G.nodes[i] and G.nodes[i]['source'] == src][0]
        dest_nodes[src] = [i for i in G.nodes 
                            if 'destination' in G.nodes[i] and G.nodes[i]['destination'] == src][0]

    # Create binary variables for each edge and source
    x = model.addVars(sources, edges, vtype=gb.GRB.BINARY, name="x")

    # Objective: Minimize the weighted path sum
    objective = gb.quicksum(G[i][j]['weight'] * x[src, i, j] for i, j in edges for src in sources)
    model.setObjective(objective, gb.GRB.MINIMIZE)

    # Constraints
    # -------------------------------------------------------------------------
    # No more than one edge can enter the same node for each source
    model.addConstrs((x.sum('*', '*', j) <= 1 for j in nodes), "Single_Incoming_Edge")

    # Flow conservation: at each node, inflow equals outflow (except for sources and sinks)
    model.addConstrs((x.sum(src, i, '*') - x.sum(src, '*', i) == 0
                      for i in nodes for src in sources if i != source_nodes[src] and i != dest_nodes[src]),
                      "Flow_Conservation")

    # From each source, only one outgoing edge
    model.addConstrs((x.sum(src, src_node, '*') == 1 for src, src_node in source_nodes.items()),
                      "Single_Source_Outflow")
    model.addConstrs((x.sum(src, other_src, '*') == 0
                      for other_src in source_nodes.values() for src in sources if other_src != source_nodes[src]),
                      "No_Other_Source_Outflow")

    # Into each sink, only one incoming edge
    model.addConstrs((x.sum(src, '*', dest) == 1 for src, dest in dest_nodes.items()),
                      "Single_Sink_Inflow")
    model.addConstrs((x.sum(src, '*', other_dest) == 0
                      for other_dest in dest_nodes.values() for src in sources if other_dest != dest_nodes[src]),
                      "No_Other_Sink_Inflow")

    # No inflow to the source
    model.addConstrs((x.sum('*', '*', src_node) == 0 for src_node in source_nodes.values()), "No_Source_Inflow")

    # No outflow from the sink
    model.addConstrs((x.sum('*', dest, '*') == 0 for dest in dest_nodes.values()), "No_Sink_Outflow")
    # -------------------------------------------------------------------------

    # Lazy constraints and model parameters
    model.Params.LazyConstraints = 1
    model.Params.TimeLimit = 24 * 60 * 60  # 24-hour limit
    model.Params.OutputFlag = 0

    # Prepare variables for lazy constraints if needed
    model._x = x
    model._K = sources
    model._G = G

    # Optimize with optional heuristic function `superHeu`
    model.optimize(superHeu)

    # Process solution
    if model.status != 3:  # 3 means infeasible
        solution_edges = [(eval(v.VarName[1:])[0], eval(v.VarName[1:])[1], eval(v.VarName[1:])[2])
                          for v in model.getVars() if "x" in v.VarName and v.X > 0.5]

        # Optionally draw the solution
        if draw_solution:
            drawing.dibujaTrazaCaminos(solution_edges, G)

        # Organize solution for each source
        solution_paths = []
        for src in sources:
            path_edges = [edge for edge in solution_edges if edge[0] == src]
            ordered_path = aux.ordenaSolucion(path_edges, source_nodes[src])  # Order edges for coherent path
            solution_paths.append(ordered_path)

        return solution_paths
# =============================================================================

# =============================================================================
def generateGraphForElbows(nodes, prop_x, prop_y, prop_z):
    """
    Generates a directed graph with edges and weights, setting a specified origin and destination node.
    
    Parameters:
    nodes : dict
        Dictionary of nodes with their 3D coordinates as `{'X': x, 'Y': y, 'Z': z}`.
    prop_x : float
        X-axis proportion for generating edges.
    prop_y : float
        Y-axis proportion for generating edges.
    prop_z : float
        Z-axis proportion for generating edges.
    
    Returns:
    G : DiGraph
        A NetworkX directed graph with node positions and weighted edges, as well as designated source and destination nodes.
    """

    # Step 1: Generate edges based on given proportions
    start_nodes, end_nodes = generateEdges(prop_x, prop_y, prop_z)
    
    # Step 2: Generate weights for the edges
    weights = generateWeights(start_nodes, end_nodes, nodes)
    
    # Step 3: Initialize the directed graph and add nodes with coordinates
    G = nx.DiGraph()
    for node, coord in nodes.items():
        G.add_node(node, coor=(coord['X'], coord['Y'], coord['Z']))
    
    # Step 4: Add directed edges between nodes with associated weights
    for idx in range(len(start_nodes)):
        G.add_edge(start_nodes[idx], end_nodes[idx], weight=weights[idx])
        G.add_edge(end_nodes[idx], start_nodes[idx], weight=weights[idx])

    # Step 5: Set origin node based on fixed coordinates
    origin_coords = [50, 0, rd.randrange(20) * 10]  # Random Z-coordinate within range
    origin_node = [
        node for node, coord in nodes.items()
        if coord['X'] == origin_coords[0] and coord['Y'] == origin_coords[1] and coord['Z'] == origin_coords[2]
    ][0]  # Select the node matching the origin coordinates

    # Step 6: Set end node based on fixed coordinates
    end_coords = [50, 180, rd.randrange(20) * 10]  # Random Z-coordinate within range
    end_node = [
        node for node, coord in nodes.items()
        if coord['X'] == end_coords[0] and coord['Y'] == end_coords[1] and coord['Z'] == end_coords[2]
    ][0]  # Select the node matching the end coordinates

    # Step 7: Mark the origin and destination nodes in the graph
    G.nodes[origin_node]["source"] = 0
    G.nodes[end_node]["destination"] = 0

    return G
# =============================================================================

# =============================================================================
def generateWeights(start_nodes, end_nodes, nodes_dict):
    """
    Generates weights for edges between start and end nodes based on the distance between them.
    If the distance is zero, assigns a higher weight; otherwise, assigns a random weight in a lower range.
    
    Parameters:
    start_nodes : list
        List of start node identifiers for each edge.
    end_nodes : list
        List of end node identifiers for each edge.
    nodes_dict : dict
        Dictionary containing node coordinates as `{'X': x, 'Y': y, 'Z': z}`.

    Returns:
    list
        List of weights corresponding to each edge.
    """
    
    # Step 1: Compile list of edges as (start, end) tuples
    edges = [(start_nodes[i], end_nodes[i]) for i in range(len(start_nodes))]
    
    # Step 2: Calculate weights based on distance between each pair of nodes
    weights = []
    for node1, node2 in edges:
        # Calculate the Euclidean distance between the nodes
        distance = aux.calculateDistanceBetweenNodes(node1, node2, nodes_dict)
        
        # Assign weight based on the distance
        if distance == 0:
            weight = rd.randint(20, 30)  # Higher weight for zero-distance edges
        else:
            weight = rd.randint(1, 9)    # Lower weight range for non-zero distances
        weights.append(weight)
    
    return weights
# =============================================================================


# =============================================================================
def generateEdges(nx, ny, nz):
    """
    Generates the edges for a graph structured in three dimensions with elbows.
    
    Parameters:
    nx : int
        Number of nodes along the x-axis.
    ny : int
        Number of nodes along the y-axis.
    nz : int
        Number of nodes along the z-axis.

    Returns:
    tuple
        A tuple containing two lists: start_nodes and end_nodes of the edges.
    """
    
    # Step 1: Create a cross list based on the z dimension
    cross_list = [i * 3 * nx * ny for i in range(nz)]

    # Step 2: Generate vertical connections
    vertical_lists = []
    for offset in cross_list:
        vertical_list = [j * 3 * nx + offset for j in range(ny)]
        vertical_lists.append(vertical_list)

    # Step 3: Generate horizontal connections
    horizontal_lists = []
    for lista in vertical_lists:
        horizontal_list2 = []
        for i in lista:
            horizontal_list1 = [j * 3 + i for j in range(nx)]
            horizontal_list2.append(horizontal_list1)
        horizontal_lists.append(horizontal_list2)

    # Step 4: Initialize list for edges
    lista_aristas = []

    # Step 5: Generate virtual edges between symbolic nodes
    for listaza in horizontal_lists:
        for lista in listaza:
            for a in lista:
                # Create edges between a, a+1, and a+2
                lista_aristas.append([a, a + 1])  # Edge from a to a + 1
                lista_aristas.append([a, a + 2])  # Edge from a to a + 2
                lista_aristas.append([a + 1, a + 2])  # Edge from a + 1 to a + 2

    # Step 6: Create horizontal edges within each horizontal list
            for a in lista[:-1]:
                lista_aristas.append([a, a + 3]) # Connect a to the next layer in the x direction

    # Step 7: Create vertical edges
        for lista in listaza[:-1]:
            for a in lista:
                b = a + 1
                lista_aristas.append([b, 3 * nx + b]) # Connect node b to its vertical counterpart
    

    # Step 8: Create transverse edges between different z levels
    for listaza in horizontal_lists[:-1]:
        for lista in listaza:
            for a in lista:
                c = a + 2
                lista_aristas.append([c, 3 * nx * ny + c])  # Connect to the next z layer

    # Step 9: Separate start and end nodes for each edge
    start_nodes, end_nodes = zip(*lista_aristas)  # Unzip edges into two lists

    return list(start_nodes), list(end_nodes)  # Return as lists for compatibility
# =============================================================================

# =============================================================================
def superHeu(model, where):
    """
    Custom heuristic callback for optimizing edge constraints in a model.

    Parameters:
    model : gurobipy.Model
        The optimization model instance.
    where : int
        The callback context provided by Gurobi (e.g., MIPSOL).
    """

    # Execute only if in the solution callback context
    if where == gb.GRB.Callback.MIPSOL:
        # Retrieve current solution values and model parameters
        # ---------------------------------------------------------------------
        vals_x = model.cbGetSolution(model._x)   # Get edge values from the solution
        services = model._K                      # List of services
        graph = model._G                         # NetworkX graph with nodes
        radius_threshold = 6                     # Maximum allowed distance for real edges
        virtual_dist_threshold = 10              # Maximum allowed distance for virtual edges
        # ---------------------------------------------------------------------

        # Filter edges that are part of the solution
        selected_edges = gb.tuplelist(edge for edge in vals_x if vals_x[edge] > 0.5)

        # Group solution edges by service for easier processing
        solution_groups = []
        for service in services:
            service_edges = [edge for edge in selected_edges if edge[0] == service]
            solution_groups.append(service_edges)

        # Separate edges into real and virtual groups by service
        real_edges_groups = []
        virtual_edges_groups = []
        for edges in solution_groups:
            real_edges = []
            virtual_edges = []
            for edge in edges:
                # Check if edge length is zero to classify as virtual or real
                if math.dist(graph.nodes[edge[1]]['coor'], graph.nodes[edge[2]]['coor']) == 0:
                    virtual_edges.append(edge)
                else:
                    real_edges.append(edge)
            real_edges_groups.append(real_edges)
            virtual_edges_groups.append(virtual_edges)

        # Add lazy constraints to enforce distance thresholds for real edges
        # ---------------------------------------------------------------------
        for i, real_edges_group1 in enumerate(real_edges_groups):
            for j in range(i + 1, len(real_edges_groups)):
                real_edges_group2 = real_edges_groups[j]
                for edge1 in real_edges_group1:
                    coord1_start = graph.nodes[edge1[1]]['coor']
                    coord1_end = graph.nodes[edge1[2]]['coor']
                    for edge2 in real_edges_group2:
                        coord2_start = graph.nodes[edge2[1]]['coor']
                        coord2_end = graph.nodes[edge2[2]]['coor']
                        edge_distance = aux.dist3DSegmentToSegment([coord1_start, coord1_end], [coord2_start, coord2_end])

                        # If edges are too close, add a constraint to prevent both being selected
                        if edge_distance <= 2 * radius_threshold:
                            model.cbLazy(model._x[edge1] + model._x[edge2] <= 1)
        # ---------------------------------------------------------------------

        # Add lazy constraints for virtual edges to enforce minimum spacing
        # ---------------------------------------------------------------------
        for virtual_edges in virtual_edges_groups:
            if len(virtual_edges) > 1:
                for idx, edge1 in enumerate(virtual_edges):
                    coord1 = graph.nodes[edge1[1]]['coor']
                    for edge2 in virtual_edges[idx + 1:]:
                        coord2 = graph.nodes[edge2[1]]['coor']
                        elbow_distance = math.dist(coord1, coord2)

                        # If virtual edges are too close, constrain simultaneous selection
                        if elbow_distance <= virtual_dist_threshold:
                            model.cbLazy(model._x[edge1] + model._x[edge2] <= 3)
                            
        # for i in [0, 1]:
        #     solVir = virtuales[i]
            
        #     aristaRealOrigin = sol[i][0]
        #     aristaRealOriginCoor = G.nodes[aristaRealOrigin[1]]['coor']
        #     if aristaRealOrigin not in solVir:
        #         for a in solVir:
        #             aristaVirtualOrigin = a
        #             aristaVirtualOriginCoor = G.nodes[aristaVirtualOrigin[1]]['coor']
        #             dis_codos = math.dist(aristaRealOriginCoor, aristaVirtualOriginCoor)
        #             if dis_codos <= distcodos:
        #                 model.cbLazy(model._x[aristaRealOrigin] + model._x[aristaVirtualOrigin] <= 1)

        #     aristaRealEnd = sol[i][-1]
        #     aristaRealEndCoor = G.nodes[aristaRealEnd[2]]['coor']
        #     if aristaRealEnd not in solVir:
        #         for a in solVir:
        #             aristaVirtualEnd = a
        #             aristaVirtualEndCoor = G.nodes[aristaVirtualEnd[1]]['coor']
        #             dis_codos = math.dist(aristaRealEndCoor, aristaVirtualEndCoor)
        #             if dis_codos <= distcodos:
        #                 model.cbLazy(model._x[aristaRealEnd] + model._x[aristaVirtualEnd] <= 1)
        # ---------------------------------------------------------------------
# =============================================================================
  

                
# =============================================================================
def trazaCaminos(G, draw_solution):
    """
    Trace optimal paths in the graph G for multiple services using Gurobi.
    
    Parameters:
    G : NetworkX graph
        The graph on which paths are to be traced.
    draw_solution : bool
        Flag to indicate if the solution should be visualized.

    Returns:
    list : Ordered solution paths for each service, if optimal paths are found.
    """

    # Load nodes and edges
    nodes = G.nodes()
    edges = G.edges()

    # Initialize optimization model
    model = gb.Model('netflow')

    # Retrieve services with defined sources
    services = [G.nodes[node]['source'] for node in G.nodes() if 'source' in G.nodes[node]]

    # Map each service to its respective source (S) and destination (T) nodes
    sources = {k: next(node for node in G.nodes() if G.nodes[node].get('source') == k) for k in services}
    destinations = {k: next(node for node in G.nodes() if G.nodes[node].get('destination') == k) for k in services}

    # Define binary decision variables for edge usage per service
    x = model.addVars(services, edges, vtype=gb.GRB.BINARY, name="x")

    # Define objective function: minimize total edge weights across all services
    objective = gb.quicksum(G[i][j]['weight'] * x[k, i, j] for i, j in edges for k in services)
    model.setObjective(objective, gb.GRB.MINIMIZE)

    # Add Constraints
    # -------------------------------------------------------------------------
    # Only one edge can enter each node
    model.addConstrs((x.sum('*', '*', j) <= 1 for j in nodes), "SingleEdgeEntry")

    # Flow conservation: except for source or destination, inflow equals outflow
    model.addConstrs((x.sum(k, i, '*') - x.sum(k, '*', i) == 0
                      for i in nodes for k in services if i != sources[k] and i != destinations[k]), "FlowConservation")

    # Source node constraint: only one edge exits each source
    model.addConstrs((x.sum(k, sources[k], '*') == 1 for k in services), "SourceSingleExit")
    model.addConstrs((x.sum(k, s, '*') == 0
                      for s in sources.values() for k in services if s != sources[k]), "SourceNoExit")

    # Destination node constraint: only one edge enters each destination
    model.addConstrs((x.sum(k, '*', destinations[k]) == 1 for k in services), "DestinationSingleEntry")
    model.addConstrs((x.sum(k, '*', t) == 0
                      for t in destinations.values() for k in services if t != destinations[k]), "DestinationNoEntry")

    # No edges enter the source and no edges exit the destination
    model.addConstrs((x.sum('*', '*', s) == 0 for s in sources.values()), "SourceNoEntry")
    model.addConstrs((x.sum('*', t, '*') == 0 for t in destinations.values()), "DestinationNoExit")
    # -------------------------------------------------------------------------

    # Model parameters
    model.Params.LazyConstraints = 1
    model.Params.TimeLimit = 24 * 60 * 60   # 24-hour time limit
    model.Params.OutputFlag = 0              # Suppress output

    # Set model attributes for lazy constraints
    model._x = x
    model._K = services
    model._G = G

    # Optimize using custom lazy constraints
    model.optimize(superHeu)

    # Solution Processing
    # -------------------------------------------------------------------------
    # If an optimal solution is found, retrieve and order the solution paths
    if model.status != gb.GRB.INFEASIBLE:
        solution_edges = [(int(var.VarName.split(",")[0][2:]), int(var.VarName.split(",")[1]), int(var.VarName.split(",")[2][:-1]))
                          for var in model.getVars() if "x" in var.VarName and var.X > 0.5]

        # Draw solution if requested
        if draw_solution:
            drawing.dibujaTrazaCaminos(solution_edges, G)

        # Separate edges by service and order them based on path flow
        service_0_edges = [edge for edge in solution_edges if edge[0] == 0]
        service_1_edges = [edge for edge in solution_edges if edge[0] == 1]

        # Order edges to create complete paths for each service
        ordered_service_0 = aux.ordenaSolucion(service_0_edges, sources[0])
        ordered_service_1 = aux.ordenaSolucion(service_1_edges, sources[1])

        return [ordered_service_0, ordered_service_1]
# =============================================================================



# =============================================================================
# Create a dictionary that associates a numeric label to each x, y, z 
# coordinate in order.
def nodesWithCoordinates(nx, ny, nz, dx, dy, dz):
    """
    Generates a dictionary where each entry represents a node in a 3D grid.
    Each node is assigned a unique label and its corresponding x, y, and z coordinates.

    Parameters:
    nx, ny, nz : int
        Number of grid divisions along the x, y, and z axes, respectively.
    dx, dy, dz : float
        Spacing between nodes along the x, y, and z axes, respectively.

    Returns:
    dict
        A dictionary where each key is a unique node label and each value is a dictionary
        with 'X', 'Y', 'Z' coordinates for that node.
    """
    
    nodes = {}      # Dictionary to store nodes and their coordinates
    counter = 0     # Unique label for each node
    
    # Iterate over the 3D grid defined by nx, ny, and nz
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                # Calculate the coordinates based on grid spacing
                coordinate = {
                    "X": i * dx,
                    "Y": j * dy,
                    "Z": k * dz
                }
                
                # Assign the same coordinate to three consecutive node labels
                # and increment counter accordingly.
                for _ in range(3):
                    nodes[counter] = coordinate
                    counter += 1
                    
    return nodes
# =============================================================================

# =============================================================================
def generateGraphForElbows2Colec(nodes, propx, propy, propz, coorOr0, coorOr1, coorEn0, coorEn1):
    """
    Generates a directed graph for a dual-collector system with specified nodes, edge properties,
    and source/destination coordinates.

    Parameters:
    nodes : dict
        Dictionary of node identifiers and their coordinates {'X': x_val, 'Y': y_val, 'Z': z_val}.
    propx, propy, propz : lists
        Edge properties along x, y, and z axes (used by `generateEdges` function).
    coorOr0, coorOr1 : tuples
        Coordinates (X, Y, Z) for the origins of collectors 0 and 1.
    coorEn0, coorEn1 : tuples
        Coordinates (X, Y, Z) for the ends of collectors 0 and 1.

    Returns:
    nx.DiGraph
        A directed graph `G` with nodes, bidirectional edges, and source/destination labels.
    """
    
    # Generate edges and weights for the graph
    start_nodes, end_nodes = generateEdges(propx, propy, propz)     # Generate start and end nodes for edges
    weights = generateWeights(start_nodes, end_nodes, nodes)         # Calculate weights for edges based on nodes

    # Create the directed graph
    G = nx.DiGraph()

    # Add nodes with 3D coordinates to the graph
    for node_id, coor in nodes.items():
        G.add_node(node_id, coor=(coor['X'], coor['Y'], coor['Z']))

    # Add edges with weights to create bidirectional edges
    for idx, start_node in enumerate(start_nodes):
        end_node = end_nodes[idx]
        weight = weights[idx]
        G.add_edge(start_node, end_node, weight=weight)
        G.add_edge(end_node, start_node, weight=weight)  # Add reverse edge for bidirectionality

    # Identify and label the origins of the collectors based on coordinates
    origin0 = [node for node, coor in nodes.items()
              if coor['X'] == coorOr0[0] and
              coor['Y'] == coorOr0[1] and coor['Z'] == coorOr0[2]][0]
    origin1 = [node for node, coor in nodes.items()
              if coor['X'] == coorOr1[0] and
              coor['Y'] == coorOr1[1] and coor['Z'] == coorOr1[2]][0]


    # Identify and label the endpoints of the collectors based on coordinates
    end0 = [node for node, coor in nodes.items()
            if coor['X'] == coorEn0[0] and
              coor['Y'] == coorEn0[1] and coor['Z'] == coorEn0[2]][0]
    end1 = [node for node, coor in nodes.items()
            if coor['X'] == coorEn1[0] and 
            coor['Y'] == coorEn1[1] and coor['Z'] == coorEn1[2]][0]

    # Add source and destination labels to the graph nodes for collectors
    G.nodes[origin0]["source"] = 0
    G.nodes[origin1]["source"] = 1
    G.nodes[end0]["destination"] = 0
    G.nodes[end1]["destination"] = 1

    return G
# =============================================================================


# =============================================================================
def dameVariosMalladosCuadrados(number_colector, number_branch, colector, T):
    """
    Generate multiple square grids from the input graph and collector data.
    
    This function processes the nodes of a graph to extract information 
    about various types of nodes (root, valve, leaf) and creates a 
    list of grids (edges and nodes) based on their coordinates. 
    The grids are then combined into a directed graph.
    
    Parameters:
    number_colector (int): Identifier for the collector.
    number_branch (int): Identifier for the branch.
    colector (list): List of collector coordinates.
    T (networkx.Graph): Input graph containing nodes and edges.
    
    Returns:
    networkx.DiGraph: A directed graph formed from the generated grids.
    """
    
    # ESTA FUNCION FUNCIONA CORRECTAMENTE
    # =========================================================================
    def giveMeFatherAndChildren(graph, node):
        """
        Retrieves the father node and its children from a directed graph.
        
        Parameters:
        graph (networkx.DiGraph): The directed graph to analyze.
        node (any): The node for which to find the father and children.
        
        Returns:
        tuple: A tuple containing:
            - A list with the father node followed by its children.
            - A list of edges represented as tuples (father, child).
            
        If the node has no children, both returned lists will be empty.
        """

        # Get the successors (children) of the specified node
        children = list(graph.successors(node))
        
        if not children:
            # If there are no children, return empty lists
            return [], []
        
        # Return the father node and its children, along with the edges
        return [node] + children, [(node, child) for child in children]
    # =========================================================================
    
    # =========================================================================
    def gridHanan(points):
        """
        Generate the Hanan grid from a list of points in 3D space.
        
        Parameters:
        points (list of tuples): List of points, where each point is a tuple (x, y, z).
        
        Returns:
        tuple: A tuple containing:
            - A list of edges in the Hanan grid.
            - A list of unique points in the Hanan grid.
        """
        
        # Edges in Hannan Grid
        # ---------------------------------------------------------------------
        # Initialize lists to store unique x, y, z coordinates
        xs, ys, zs = [], [], []

        # Extract and collect unique x, y, z coordinates from the input points
        for point in points:
            xs.append(point[0])
            ys.append(point[1])
            zs.append(point[2])
            
        # Sort and remove duplicates from coordinates
        xs = sorted(set(xs))
        ys = sorted(set(ys))
        zs = sorted(set(zs))
        
        # Create edges for the Hanan grid along x, y, and z axes
        edges_x = zip(xs[:-1], xs[1:])
        edges_y = zip(ys[:-1], ys[1:])
        edges_z = zip(zs[:-1], zs[1:])
        
        # Initialize a list to store edges in the Hanan grid
        hanan_grid_edges = []
        
        # Create edges along the x-axis
        for edge_x in edges_x:
            for y in ys:
                for z in zs:
                    edge = ((edge_x[0], y, z), (edge_x[1], y, z))
                    hanan_grid_edges.append(edge)
    
        # Create edges along the y-axis
        for edge_y in edges_y:
            for x in xs:
                for z in zs:
                    edge = ((x, edge_y[0], z), (x, edge_y[1], z))
                    hanan_grid_edges.append(edge)
    
        # Create edges along the z-axis
        for edge_z in edges_z:
            for x in xs:
                for y in ys:
                    edge = ((x, y, edge_z[0]), (x, y, edge_z[1]))
                    hanan_grid_edges.append(edge)
                    
        # # Remove duplicates
        # hananGridEdges = [entry for idx, entry in enumerate(hananGridEdges)
        #                   if entry not in hananGridEdges[:idx]]
        
        # Remove duplicate edges
        hanan_grid_edges = list(set(hanan_grid_edges))
        # ---------------------------------------------------------------------
        
        # Points in Hannan Grid
        # ---------------------------------------------------------------------
        # Extract unique points from edges
        hanan_grid_points = set()
        for edge in hanan_grid_edges:
            hanan_grid_points.update(edge)  # Add both endpoints of the edge
        
        # Convert set back to list
        hanan_grid_points = list(hanan_grid_points)
        # ---------------------------------------------------------------------
        
        return hanan_grid_edges, hanan_grid_points
    # =========================================================================

    # =========================================================================
    def damePuntosEnEspacios(G, nodos_padre_e_hijos, hanan_grid_points, colector):
        """
        Auxiliary function to retrieve points in specified spaces for nodes in a graph.
        
        This function analyzes nodes of type "valve", "root", and "leaf" within the graph
        to determine which points from the Hanan grid fall within defined spatial constraints.
        
        Parameters:
        G (networkx.Graph): The graph containing nodes and their properties.
        nodos_padre_e_hijos (list): A list of nodes to evaluate.
        hanan_grid_points (list): A list of points from the Hanan grid.
        colector (list): A list representing two collectors.
        
        Returns:
        dict: A dictionary where keys are node IDs and values are lists of points that fit the criteria.
        """
        # Prepare segments for root nodes based on collector input
        cole0 = colector[:-1]  # All but the last collector
        cole1 = colector[1:]   # All but the first collector
        tramos = list(zip(cole0, cole1))  # Create pairs of segments

        # Dictionary to store coordinates associated with each node
        dict_coor = {}
        
        # Iterate through each node to determine valid points
        for node in nodos_padre_e_hijos:
            lista = []  # List to collect valid points for the current node

            # Check if the current node is of type 'valve'
            if G.nodes[node]["type"] == "valve":
                dict_spacios = G.nodes[node]["space"]  # Get the defined spaces for this valve
                for point in hanan_grid_points:
                    # Check if the point is within any defined space
                    for space in dict_spacios.values():
                        if (space[0][0] <= point[0] <= space[1][0] and
                            space[0][1] <= point[1] <= space[1][1] and
                            space[0][2] <= point[2] <= space[1][2]):
                            lista.append(point)  # Add point to the list if it's valid
                            break  # No need to check other spaces once a point is added

            # Check if the current node is of type 'root'
            elif G.nodes[node]["type"] == "root":
                for point in hanan_grid_points:
                    # Check if the point lies between segments defined in tramos
                    for tramo in tramos:
                        if aux.isBetween(tramo[0], tramo[1], point):
                            lista.append(point)
                            break  # No need to check other segments once a point is added
    
            # Check if the current node is of type 'leaf'
            elif G.nodes[node]["type"] == "leaf":
                # Directly compare the point to the position of the leaf
                if G.nodes[node]["position"] in set(hanan_grid_points):
                    lista.append(G.nodes[node]["position"])
    
            # Store the list of valid points in the dictionary for the current node
            dict_coor[node] = lista
                    
        return dict_coor
    # =========================================================================

    # =========================================================================
    def joinDictionaries(list_dict_coor):
        """
        Joins multiple dictionaries into a single dictionary by taking the intersection 
        of lists associated with the same keys.
        
        Parameters:
        list_dict_coor (list): A list of dictionaries to be merged.
        
        Returns:
        dict: A dictionary where each key corresponds to the intersection of lists 
              from the input dictionaries.
        """
        
        # Collect all unique keys from the provided dictionaries
        unique_keys = set()  # Use a set for uniqueness
        for mini_dict in list_dict_coor:
            unique_keys.update(mini_dict.keys())  # Add keys from each dictionary
        
        # Sort the keys to maintain order
        sorted_keys = sorted(unique_keys)
        
        # Initialize the resulting dictionary
        dict_sol = {}
        
        # For each key, find the intersection of its associated lists across all dictionaries
        for key in sorted_keys:
            lists_to_intersect = []
            
            for mini_dict in list_dict_coor:
                # If the key exists in the current dictionary, append its value (list)
                if key in mini_dict:
                    lists_to_intersect.append(mini_dict[key])
            
            # Compute the intersection of all lists found for the current key
            if lists_to_intersect:  # Ensure there are lists to intersect
                # Use set intersection to find common elements
                intersected_list = list(set.intersection(*map(set, lists_to_intersect)))
                dict_sol[key] = intersected_list  # Assign the result to the key in the result dictionary
            else:
                dict_sol[key] = []  # If no lists found, assign an empty list to the key
        
        return dict_sol
    # =========================================================================

    # =========================================================================
    def formarGrafo(G, list_dict_mallado, list_dict_coor, number_colector, number_branch):
        """
        Constructs a directed graph from the provided data structures.
        
        This function populates the graph `G` with nodes and edges defined in the
        lists of dictionaries representing the grid and coordinates. It sets various 
        attributes for nodes and edges, including collector and branch information.
        
        Parameters:
        G (networkx.Graph): The original graph (not modified in this function).
        list_dict_mallado (list): A list of dictionaries containing node and edge information.
        list_dict_coor (list): A list of dictionaries mapping node types to coordinates.
        number_colector (int): An identifier for the collector.
        number_branch (int): An identifier for the branch.
        
        Returns:
        networkx.DiGraph: The newly constructed directed graph.
        """
        
        # Collect unique coordinates from the list of grid dictionaries
        unique_coords = set()  # Use a set for uniqueness
        for grid in list_dict_mallado:
            unique_coords.update(grid["nodes"])  # Add nodes to the set
        
        # Convert the set back to a sorted list
        sorted_coords = sorted(unique_coords)
        
        # Create dictionaries to map coordinates to numerical indices and vice versa
        dict_coord_num = {coord: idx for idx, coord in enumerate(sorted_coords)}
        dict_num_coord = {idx: coord for idx, coord in enumerate(sorted_coords)}
        
        # Initialize a directed graph
        new_graph = nx.DiGraph()
        
        # Add edges to the graph from the grid dictionaries
        for grid in list_dict_mallado:
            for edge in grid["edges"]:
                node_from = dict_coord_num[edge[0]]
                node_to = dict_coord_num[edge[1]]
                                
                # Add edges in both directions
                new_graph.add_edge(node_from, node_to, 
                                    coor = edge, 
                                    padreHijo = grid['listaPadreHijos'],
                                    colector = number_colector,
                                    branch = number_branch)
                new_graph.add_edge(node_to, node_from, 
                                    coor = edge, 
                                    padreHijo = grid['listaPadreHijos'],
                                    colector = number_colector,
                                    branch = number_branch)
        
        # Add nodes to the graph with their attributes
        for coord_dict in list_dict_coor:
            for key, coordinates in coord_dict.items():
                for coord in coordinates:
                    new_graph.add_node(dict_coord_num[coord], 
                                        coor=coord, 
                                        node=key, 
                                        typ=G.nodes[key]["type"],
                                        colector=number_colector,
                                        branch=number_branch)
        
        # Set default attributes for any nodes that are missing coordinates
        for node in new_graph.nodes:
            if "coor" not in new_graph.nodes[node]:
                new_graph.nodes[node].update({
                    'coor': dict_num_coord[node],
                    'node': "none",
                    'colector': number_colector,
                    'branch': number_branch
                })
        
        return new_graph
    # =========================================================================
    
    list_dict_coor = []  # To store coordinate dictionaries for each grid
    list_dict_mallado = []  # To store grid information (edges and nodes)

    # Iterate over each node in the graph T
    for i in T.nodes:
        nodos_padre_e_hijos, lista_padre_hijos = giveMeFatherAndChildren(T, i)
        
        if nodos_padre_e_hijos:# Proceed only if there are parent and child nodes
            puntos = []  # List to accumulate points
            # Process each parent/child node
            for j in nodos_padre_e_hijos:
                node_type = T.nodes[j]["type"]

                if node_type == "root":
                    # For root nodes, append all collector coordinates
                    puntos.extend(colector)
                elif node_type == "valve":
                    # For valve nodes, generate corner points based on their center and epsilon offsets
                    for key, center in T.nodes[j]["center"].items():
                        epsilon = T.nodes[j]["epsilon"][key]
                        # Generate eight corner points for the valve
                        puntos.extend([
                            (center[0] - epsilon[0], center[1] - epsilon[1], center[2] - epsilon[2]),
                            (center[0] + epsilon[0], center[1] - epsilon[1], center[2] - epsilon[2]),
                            (center[0] - epsilon[0], center[1] + epsilon[1], center[2] - epsilon[2]),
                            (center[0] - epsilon[0], center[1] - epsilon[1], center[2] + epsilon[2]),
                            (center[0] + epsilon[0], center[1] + epsilon[1], center[2] - epsilon[2]),
                            (center[0] + epsilon[0], center[1] - epsilon[1], center[2] + epsilon[2]),
                            (center[0] - epsilon[0], center[1] + epsilon[1], center[2] + epsilon[2]),
                            (center[0] + epsilon[0], center[1] + epsilon[1], center[2] + epsilon[2]),
                        ])

                elif node_type == "leaf":
                    # For leaf nodes, add their position directly
                    puntos.append(T.nodes[j]["position"])

            # Create the Hanan grid based on the collected points
            hanan_grid_edges, hanan_grid_points = gridHanan(puntos)
            
            
            # Create a dictionary for the current grid
            dict_mallado = {
                "edges": hanan_grid_edges,
                "nodes": hanan_grid_points,
                "listaPadreHijos": lista_padre_hijos
            }

            list_dict_mallado.append(dict_mallado)  # Append the grid to the list

            # Get coordinate points for the grid
            dict_coor = damePuntosEnEspacios(T, nodos_padre_e_hijos, hanan_grid_points, colector)

            list_dict_coor.append(dict_coor)
        
    grid = formarGrafo(T, list_dict_mallado, list_dict_coor, number_colector, number_branch)
        
    return grid
# =============================================================================


# =============================================================================
def createContinuousScenario(
    numero_colectores, ramales_por_colector, numero_nodos, caja_por_valvula,
    lado_caja, xMin, yMin, zMin, xMax, yMax, zMax, xMinRoot, xMaxRoot):
    """
    Creates a continuous scenario simulation with collectors and branches (trees)
    in a 3D space with specified constraints.

    Parameters:
    ----------
    numero_colectores : int
        Number of main collectors to generate.
    ramales_por_colector : int
        Number of branches per collector.
    numero_nodos : int
        Number of nodes per branch.
    caja_por_valvula : float
        Proportion of box allocation per valve.
    lado_caja : float
        Side length of the box that defines the branching area.
    xMin, yMin, zMin, xMax, yMax, zMax : float
        Minimum and maximum x, y, and z boundaries for the 3D space.
    xMinRoot, xMaxRoot : float
        Minimum and maximum x boundaries for root nodes of the branches.

    Returns:
    -------
    dict
        A dictionary containing:
            "colectores": Coordinates of extreme nodes for each collector.
            "arboles": Dictionary of branches for each collector.
    """
    
    # Initialize solution dictionary
    solucion = {}
    
    # Get the extreme node coordinates for each collector
    extremeNodesColectorCoor = aux.giveMeExtremeNodesColectors(numero_colectores)
    solucion["colectores"] = extremeNodesColectorCoor

    # Dictionary to hold branch structures for each collector
    arbolesDict = {}
    
    # Generate trees for each collector
    for colector in range(numero_colectores):
        arboles = []
        
        # Generate individual branches (trees) for the current collector
        for i in range(ramales_por_colector):
            T = generateTree(
                numero_nodos, caja_por_valvula, lado_caja,
                xMin, yMin, zMin, xMax, yMax, zMax, xMinRoot, xMaxRoot
            )
            arboles.append(T)
        
        # Store the generated branches for the current collector
        arbolesDict[colector] = arboles
    
    # Add the tree structures to the solution dictionary
    solucion["arboles"] = arbolesDict
    
    return solucion
# =============================================================================




def createScenario(dicc_input):
    
    # Get parameters
    numero_colectores = dicc_input["numero_colectores"]
    ramales_por_colector = dicc_input["ramales_por_colector"]
    numero_nodos = dicc_input["numero_nodos"]
    caja_por_valvula = dicc_input["caja_por_valvula"]
    lado_caja = dicc_input["lado_caja"]
    xMin = dicc_input["xMin"]
    yMin = dicc_input["yMin"]
    zMin = dicc_input["zMin"]
    xMax = dicc_input["xMax"]
    yMax = dicc_input["yMax"]
    zMax = dicc_input["zMax"]
    xMinRoot = dicc_input["xMinRoot"]
    xMaxRoot = dicc_input["xMaxRoot"]
    version = dicc_input["version"]
    
    # Name scenario
    name_scenario = "col" + str(numero_colectores) + "ram" + str(ramales_por_colector) + "nod" + str(numero_nodos) + "caj" + str(caja_por_valvula) + "lad" + str(lado_caja) + "ver" + str(version)
    
    # Create folders
    path_folder = "./scenarios/" + name_scenario
    # If folder already exits, erase it
    if os.path.exists(path_folder):
        shutil.rmtree(path_folder)  # Deletes the folder and all its contents
    os.makedirs(path_folder)
    os.makedirs(path_folder + "/grids")
    
    # Create txt with scenario characteristics
    with open(path_folder + "/info.txt", "w") as file:
        for key, value in dicc_input.items():
            file.write(f"{key}: {value}\n")
            
    # Create continuous scenario
    continuous = createContinuousScenario(numero_colectores, ramales_por_colector, numero_nodos, caja_por_valvula, lado_caja, xMin, yMin, zMin, xMax, yMax, zMax, xMinRoot, xMaxRoot)
    pickle.dump(continuous, open(path_folder + "/continuous_scenario"+ ".pickle", "wb"))  
    
    
# ----------------------------------------------------------------------------- 
    dicc_colours = {
                1: ['royalblue'],
                2: ['red', 'blue'],
                3: ['red', 'blue', 'green'],
                4: ['red', 'blue', 'green', 'orange'],
                5: ['red', 'blue', 'green', 'orange', 'purple'],
                6: ['red', 'blue', 'green', 'orange', 'purple', 'brown'],
                7: ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink'],
                8: ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan'],
                9: ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'yellow'],
                10: ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'yellow', 'black'],
                12: ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'yellow', 'black', 'gray', 'lime'],
                14: ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'yellow', 'black', 'gray', 'lime', 'gold', 'teal'],
                16: ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'yellow', 'black', 'gray', 'lime', 'gold', 'teal', 'navy', 'violet'],
                18: ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'yellow', 'black', 'gray', 'lime', 'gold', 'teal', 'navy', 'violet', 'magenta', 'olive'],
                20: ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'yellow', 'black', 'gray', 'lime', 'gold', 'teal', 'navy', 'violet', 'magenta', 'olive', 'turquoise', 'coral']
                }
# ----------------------------------------------------------------------------- 
    
    number_rows = len(continuous["arboles"].keys())
    number_columns = len(continuous["arboles"][0])
    fig, axes = plt.subplots(number_rows, number_columns, figsize=(20, 9))  # 1 row, 2 columns

    for key, value in continuous["arboles"].items():
        for idx, i in enumerate(value):
            
            colours = dicc_colours[len(value)]
            
            i_m = copy.deepcopy(i)
            for j in i_m.nodes:
                if i_m.nodes[j]['type'] != 'root' and i_m.nodes[j]['type'] != 'leaf':
                    del i_m.nodes[j]['center']
                    del i_m.nodes[j]['space']
                    del i_m.nodes[j]['epsilon']
            pos = graphviz_layout(i_m, prog="dot")
            print(i)
            print(pos)
            print(idx)
            print(colours)
            print(colours[idx])
            print('-----------')
            if number_rows == 1 and number_columns == 1: 
                nx.draw(i, pos, with_labels=True, node_color=colours[idx], alpha=0.5)
                axes.set_title("c" + str(key) + "_b" + str(idx))
            elif number_rows == 1:
                nx.draw(i, pos, ax=axes[idx], with_labels=True, node_color=colours[idx], alpha=0.5)
                axes[idx].set_title("c" + str(key) + "_b" + str(idx))
            elif number_columns == 1:
                nx.draw(i, pos, ax=axes[key], with_labels=True, node_color=colours[idx], alpha=0.5)
                axes[key].set_title("c" + str(key) + "_b" + str(idx))
            else:
                nx.draw(i, pos, ax=axes[key, idx], with_labels=True, node_color=colours[idx], alpha=0.5)
                axes[key, idx].set_title("c" + str(key) + "_b" + str(idx))

    # Adjust layout to use all available space
    plt.tight_layout()
    
    # Save the figure as a high-resolution PNG
    plt.savefig(path_folder + "/branches.png", dpi=300, bbox_inches="tight")
    
    # Explicitly close the figure to prevent it from showing
    plt.close(fig)
    # # Show the figure
    # plt.show()
    
    
    # Create grids
    for number_colector, colector_nodes in continuous["colectores"].items():
        for colector_branch, branches in continuous["arboles"].items():
            if number_colector == colector_branch:
                for number_branch, branch in enumerate(branches):
                    grid = dameVariosMalladosCuadrados(number_colector, number_branch, colector_nodes, branch)
                    grid_name = "c" + str(number_colector) + "_b" + str(number_branch)
                    pickle.dump(grid, open(path_folder + "/grids/" +  grid_name + ".pickle", "wb"))

    
    
    


def main():


    # 2 combinaciones ( 2 colestores, 3 ramales, 15 nodos, lado 5)
    # 4 combinaciones (2 colestores, 3 ramales, 15 nodos, lado 10)
    # 5 combinaciones ( 2 colestores, 5 ramales, 15 nodos, lado 5)
    # 5 combinaciones ( 2 colestores, 5 ramales, 15 nodos, lado 10) 

    number_colectors = [2]
    number_branches = [3]
    number_nodes = [5]
    # number_nodes = [15, 20]
    # valve_space = []
    valve_space = [10]
    versions = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    versions = range(240)
    for c in number_colectors:
        for b in number_branches:
            for n in number_nodes:
                for s in valve_space:
                    for v in versions:
                        dicc_input = {
                            "numero_colectores" : c,
                            "ramales_por_colector" : b,
                            "xMin" : 70,
                            "yMin" : 0,
                            "zMin" : 0,
                            "xMax" : 345,
                            "yMax" : 200,
                            "zMax" : 200,
                            "numero_nodos" : n,
                            "caja_por_valvula" : 1,
                            "lado_caja" : s,
                            "xMinRoot" : 360,
                            "xMaxRoot" : 400,
                            "version" : v
                            }
                        createScenario(dicc_input)






if __name__ == "__main__":
    main()




