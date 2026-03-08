# -*- coding: utf-8 -*-
"""
Created on Sun Nov 26 13:45:06 2023

@author: Trabajador
"""

import math
import numpy as np
import scenario_generator as generator 
import pickle
import os

# =============================================================================
def isBetween(a, b, c):
    """
    Check if point `c` lies on the line segment between points `a` and `b`.
    
    Parameters:
    a, b, c: array-like, representing the coordinates of the points [x, y] (or [x, y, z] for 3D).
    
    Returns:
    bool: True if `c` is between `a` and `b` on the line segment; otherwise, False.
    """
    # Vector from a to b and from a to c
    ab = np.subtract(b, a)
    ac = np.subtract(c, a)

    # Calculate the cross product to check if ab and ac are collinear
    cross_product = np.cross(ab, ac)

    # For floating-point comparisons, use a small tolerance to account for numerical errors
    if np.linalg.norm(cross_product) > 1e-6:
        return False  # Points are not collinear

    # Dot product check to confirm `c` is in the same direction as `b` from `a`
    dot_product = np.dot(ab, ac)
    if dot_product < 0:
        return False  # `c` is behind `a`

    # Length squared of the segment ab (avoids using sqrt for efficiency)
    ab_length_squared = np.dot(ab, ab)
    if dot_product > ab_length_squared:
        return False  # `c` is beyond `b`

    # if np.all(a == c) or np.all(b == c):
    #     return True

    # All checks passed, `c` is on the segment between `a` and `b`
    return True
# =============================================================================

# =============================================================================
def traverseTreeGraph(start_node, visited_nodes, graph):
    """
    Perform a depth-first traversal of the graph, starting from `start_node`.
    
    Parameters:
    start_node : The node from which traversal begins.
    visited_nodes : List to store nodes as they are visited.
    graph : Graph object containing nodes and adjacency lists (assumes `graph.adj` holds adjacency info).
    
    Returns:
    List of visited nodes in the order they were discovered.
    """
    # Base case: Stop recursion if all nodes have been visited
    if len(visited_nodes) == len(graph.nodes):
        return visited_nodes

    # Explore each neighboring node of the current start_node
    for neighbor in graph.adj[start_node].keys():
        # Only visit the node if it hasn't been visited already
        if neighbor not in set(visited_nodes):
            visited_nodes.append(neighbor)  # Mark the node as visited
            traverseTreeGraph(neighbor, visited_nodes, graph)  # Recursively visit its neighbors

    # Return the full list of visited nodes after all reachable nodes are explored
    return visited_nodes
# =============================================================================

# =============================================================================
def calculateDistanceBetweenNodes(node1, node2, nodes_dict):
    """
    Computes the Euclidean distance between two nodes using their coordinates stored in a dictionary.

    Parameters:
    node1 : int
        Identifier for the first node.
    node2 : int
        Identifier for the second node.
    nodes_dict : dict
        Dictionary containing nodes with coordinates as `{'X': x, 'Y': y, 'Z': z}`.

    Returns:
    float
        The Euclidean distance between the two nodes.
    """
    
    # Extract the 3D coordinates for both nodes as NumPy arrays
    coord1 = np.array([nodes_dict[node1]["X"], nodes_dict[node1]["Y"], nodes_dict[node1]["Z"]])
    coord2 = np.array([nodes_dict[node2]["X"], nodes_dict[node2]["Y"], nodes_dict[node2]["Z"]])
    
    # Calculate and return the Euclidean distance
    return np.linalg.norm(coord1 - coord2)
# =============================================================================

# =============================================================================
def ordenaSolucion(solucion, fuente):
    """
    Sorts the solution edges in a sequential order starting from a specified source node.

    Parameters:
    solucion : list of tuples
        List of edges represented as tuples (edge_id, start_node, end_node).
    fuente : int
        The starting node (source) for ordering the solution.

    Returns:
    list
        A list of edges in sequential order starting from the specified source.
    """
    
    # Initialize the ordered solution list
    sol_ordenada = []

    # Continue until all edges are sorted
    while solucion:
        for idx, (edge_id, start_node, end_node) in enumerate(solucion):
            # Check if the current edge starts from the specified source node
            if fuente == start_node:
                # Add edge to ordered solution
                sol_ordenada.append((edge_id, start_node, end_node))
                # Update source to the current edge's destination
                fuente = end_node
                # Remove the processed edge from the solution
                del solucion[idx]
                break

    return sol_ordenada
# =============================================================================

# =============================================================================
def dist3DSegmentToSegment(S1, S2):
    """
    Calculates the minimum distance between two segments in 3D space.

    Parameters:
    S1 : tuple
        Two endpoints defining the first segment ((x1, y1, z1), (x2, y2, z2)).
    S2 : tuple
        Two endpoints defining the second segment ((x3, y3, z3), (x4, y4, z4)).

    Returns:
    float
        The minimum distance between the two segments S1 and S2.
        
    Reference:
    http://geomalgorithms.com/a07-_distance.html#dist3D_Segment_to_Segment()
    """

    # Helper Functions
    # -------------------------------------------------------------------------
    def dotProduct(v, w):
        """Calculates the dot product of vectors v and w."""
        return v[0] * w[0] + v[1] * w[1] + v[2] * w[2]

    def scaleVector(v, scalar):
        """Scales vector v by a given scalar."""
        return (v[0] * scalar, v[1] * scalar, v[2] * scalar)

    def vector(P1, P2):
        """Creates a vector from points P1 to P2."""
        return (P2[0] - P1[0], P2[1] - P1[1], P2[2] - P1[2])

    def addVectors(v, w):
        """Adds vectors v and w."""
        return (v[0] + w[0], v[1] + w[1], v[2] + w[2])

    def subtractVectors(v, w):
        """Subtracts vector w from vector v."""
        return (v[0] - w[0], v[1] - w[1], v[2] - w[2])

    def vectorLength(v):
        """Calculates the Euclidean length of vector v."""
        return math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    # -------------------------------------------------------------------------

    # Segment vectors
    u = vector(S1[0], S1[1])  # Vector along segment S1
    v = vector(S2[0], S2[1])  # Vector along segment S2
    w = vector(S2[0], S1[0])  # Vector between the start points of S1 and S2

    # Dot products needed for distance calculation
    a = dotProduct(u, u)
    b = dotProduct(u, v)
    c = dotProduct(v, v)
    d = dotProduct(u, w)
    e = dotProduct(v, w)

    D = a * c - b * b  # Denominator to determine parallelism of segments
    # sD and tD are initially set to D
    sD = D
    tD = D


    # If segments are almost parallel (D close to zero)
    if D < 0.001:
        sN = 0.0  # Force using point S1[0] as starting point
        sD = 1.0  # Prevent division by zero
        tN = e
        tD = c
    else:
        sN = b * e - c * d
        tN = a * e - b * d

        # Ensure sc remains within [0, 1] bounds
        if sN < 0.0:
            sN = 0.0
            tN = e
            tD = c
        elif sN > sD:
            sN = sD
            tN = e + b
            tD = c

    # Ensure tc remains within [0, 1] bounds
    if tN < 0.0:
        tN = 0.0
        if -d < 0.0:
            sN = 0.0
        elif -d > a:
            sN = sD
        else:
            sN = -d
            sD = a
    elif tN > tD:
        tN = tD
        if -d + b < 0.0:
            sN = 0.0
        elif -d + b > a:
            sN = sD
        else:
            sN = -d + b
            sD = a

    # Compute the sc and tc parameters for the closest points on segments
    sc = 0.0 if abs(sN) < 0.001 else sN / sD
    tc = 0.0 if abs(tN) < 0.001 else tN / tD

    # Calculate the vector between the closest points on each segment
    closest_point_diff = addVectors(w, subtractVectors(scaleVector(u, sc), scaleVector(v, tc)))

    # Calculate and return the distance
    return vectorLength(closest_point_diff)
# =============================================================================

# =============================================================================
def giveMeExtremeNodesColectors(colectors):
    """
    Generates and returns a dictionary of extreme nodes for each collector's path, 
    based on the specified number of collectors.

    Parameters:
    colectors : int
        Number of collectors (1 or 2) to generate the graph and find extreme nodes.

    Returns:
    dict
        A dictionary where each key corresponds to a collector index (0 or 1) and 
        each value is a list of coordinates representing the extreme nodes for 
        that collector's path.
    """

    # Grid dimensions and node separation distances
    dimensionX, dimensionY, dimensionZ = 40, 20, 20
    separationX, separationY, separationZ = 10, 10, 10
    
    # Generate nodes for the 3D grid
    nodes = generator.nodesWithCoordinates(dimensionX, dimensionY, dimensionZ, separationX, separationY, separationZ)
    
    # Define graph, origins, and endpoints based on the number of collectors
    # -------------------------------------------------------------------------
    if colectors == 2:
        # Origin and endpoint coordinates for two collectors
        coorOr0, coorOr1 = [50, 0, 180], [50, 0, 20]
        coorEn0, coorEn1 = [50, 190, 20], [50, 190, 180]
        
        # Generate graph and obtain path solutions for two collectors
        G = generator.generateGraphForElbows2Colec(nodes, dimensionX, dimensionY, dimensionZ, coorOr0, coorOr1, coorEn0, coorEn1)
        edgesSolution = generator.trazaCaminos(G, False)
        
    elif colectors == 1:
        # Generate graph and obtain path solution for a single collector
        G = generator.generateGraphForElbows(nodes, dimensionX, dimensionY, dimensionZ)
        edgesSolution = generator.tracePathsSinglePath(G, False)
    # -------------------------------------------------------------------------

    # Map collector paths to collector indices
    pathsEdgesDict = dict(zip([0, 1], edgesSolution))

    # Find the extreme nodes for each collector
    # -------------------------------------------------------------------------
    extremeNodesColector = {}
    
    for colector, edges in pathsEdgesDict.items():
        listExtremeNodes = []
        
        for i in edges:
            if i == edges[0]:  # First edge of the path
                listExtremeNodes.append(i[1])
            elif i == edges[-1]:  # Last edge of the path
                listExtremeNodes.append(i[2])
            elif calculateDistanceBetweenNodes(i[1], i[2], nodes) == 0:  # Node pair at zero distance
                listExtremeNodes.append(i[1])

        # Remove duplicate entries
        listExtremeNodes = [entry for idx, entry in enumerate(listExtremeNodes) 
                            if entry not in listExtremeNodes[:idx]]
        
        # Map the extreme nodes list to the collector
        extremeNodesColector[colector] = listExtremeNodes
    # -------------------------------------------------------------------------

    # Map extreme nodes to their coordinates
    # ------------------------------------------------------------------------- 
    extremeNodesColectorCoor = {
        idx: [G.nodes[i]['coor'] for i in value] for idx, value in extremeNodesColector.items()
    }
    # -------------------------------------------------------------------------
    
    return extremeNodesColectorCoor
# =============================================================================


# Given two points. Create several intermediate points and joint the two
# initials points with thought the created ones.
# =============================================================================
def nodesBetweenSourceAndDestination(point1, point2):
    if (point1[0] != point2[0]
        and point1[1] != point2[1]
        and point1[2] != point2[2]):
        aux0 = [point2[0], point1[1], point1[2]]
        aux1 = [point2[0], point2[1], point1[2]]
        chain = [point1, aux0, aux1, point2]
    elif (point1[0] != point2[0]
          and point1[1] != point2[1] 
          and point1[2] == point2[2]):
        aux0 = [point2[0], point1[1], point1[2]]
        chain = [point1, aux0, point2]
    elif (point1[0] != point2[0] 
          and point1[1] == point2[1]
          and point1[2] != point2[2]):
        aux0 = [point2[0], point1[1], point1[2]]
        chain = [point1, aux0, point2]
    elif (point1[0] == point2[0]
          and point1[1] != point2[1] 
          and point1[2] != point2[2]):
        aux0 = [point1[0], point2[1], point1[2]]
        chain = [point1, aux0, point2]
    else:
        chain = [point1, point2]
    return chain
# =============================================================================


# ============================================================================= 
def readScenario(nameScenario):
    basic_path = "./scenarios/" + nameScenario + "/"
    continuous_scenario = pickle.load(open(basic_path + "continuous_scenario.pickle", 'rb'))
    # print(continuous_scenario)
    listFiles = listFilesInDirectory(basic_path + "grids")
    # print(listFiles)
    grids = []
    for i in listFiles:
        grid = pickle.load(open(basic_path + "grids/" + i, 'rb'))
        grids.append(grid)
    return continuous_scenario, grids
# ============================================================================= 



# ============================================================================= 
def listFilesInDirectory(directory_path):
    try:
        # Check if the provided path is a valid directory
        if not os.path.isdir(directory_path):
            print(f"Error: {directory_path} is not a valid directory.")
            return []

        # Get the list of all files and directories
        entries = os.listdir(directory_path)

        # Filter out only files
        # files = [entry for entry in entries if os.path.isfile(os.path.join(directory_path, entry))]
        files = [entry for entry in entries]

        return files

    except Exception as e:
        print(f"An error occurred: {e}")
        return []
# ============================================================================= 
