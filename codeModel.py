# -*- coding: utf-8 -*-
"""
Created on Sun Nov 26 13:45:05 2023

@author: Trabajador
"""
import gurobipy as gb
import auxiliar as aux
import math
# from collections import Counter
# import pickle
import os
import ast
import shutil
import time

lazy_count = 0


# ============================================================================= 
def modelSchematic(nameScenario, security_distance, gap, timelimit):
    
    # Read data
    # -------------------------------------
    continuous_scenario, grids = aux.readScenario(nameScenario)
    # -------------------------------------
    
    # Parameters
    # -------------------------------------------------------------------------
    dict_distances = {}
    for grid in grids:
        for arc in grid.edges:
            distance = math.dist(grid.nodes[arc[0]]['coor'], grid.nodes[arc[1]]['coor'])
            key = (grid.edges[arc]['colector'], grid.edges[arc]['branch'], arc[0], arc[1])
            dict_distances[key] = distance
    
    colector_numbers = []
    for i in continuous_scenario["colectores"]:
        colector_numbers.append(i)
    
    branch_number_dict = {}
    for colector, trees in continuous_scenario["arboles"].items():
        branch_number_dict[colector] = range(len(trees))

    dict_trees = {}
    for colector, trees in continuous_scenario["arboles"].items():
        for branch, tree in enumerate(trees):
            dict_trees[(colector, branch)] = tree
    
    dict_grids = {}
    for grid in grids:
        dict_grids[(grid.nodes[0]['colector'], grid.nodes[0]['branch'])] = grid
        
    colector_edges_dict = {}
    for colector_number, colector_points in continuous_scenario["colectores"].items():
        colector_edges_dict[colector_number] = list(zip(colector_points[:-1], colector_points[1:]))
    # -------------------------------------------------------------------------
        
    # initialize the model
    m = gb.Model('model')
    
    # Variables
    # -------------------------------------------------------------------------
    # Variable f
    # ---------
    variables_dicc_f = []
    for grid in grids:
        for arc in grid.edges:
            for arc_tree in grid.edges[arc]['padreHijo']:
                var = {}
                var["c"] = grid.edges[arc]['colector']
                var["b"] = grid.edges[arc]['branch']
                var["s"] = arc_tree[0]
                var["t"] = arc_tree[1]
                var["i"] = arc[0]
                var["j"] = arc[1]
                variables_dicc_f.append(var)
    
    variables_f = []
    for i in variables_dicc_f:
        variables_f.append(tuple(i.values()))

    f = m.addVars(variables_f, vtype = gb.GRB.BINARY, name = "f")
    # ---------
    # Variable y
    # ---------
    variables_dicc_y = []
    for grid in grids:
        for i in grid.nodes():
            if grid.nodes[i]['node'] != "none":
                var = {}
                var["c"] = grid.nodes[i]['colector']
                var["b"] = grid.nodes[i]['branch']
                var["s"] = grid.nodes[i]['node']
                var["i"] = i
                variables_dicc_y.append(var)
    
    # print(variables_dicc_y)
    variables_y = []
    for i in variables_dicc_y:
        variables_y.append(tuple(i.values()))

    y = m.addVars(variables_y, vtype = gb.GRB.BINARY, name = "y")
    # ---------
    # Variable x
    # ---------
    variables_dicc_x = []
    for grid in grids:
        for arc in grid.edges:
            var = {}
            var["c"] = grid.edges[arc]['colector']
            var["b"] = grid.edges[arc]['branch']
            var["i"] = arc[0]
            var["j"] = arc[1]
            variables_dicc_x.append(var)
        
    variables_x = []
    for i in variables_dicc_x:
        variables_x.append(tuple(i.values()))
      
    x = m.addVars(variables_x, vtype = gb.GRB.BINARY, name = "x")
    # -------------------------------------------------------------------------

    # Objective function
    # -------------------------------------------------------------------------
    obj= gb.quicksum(dict_distances[x_var]*x[x_var[0], x_var[1], x_var[2], x_var[3]] 
            for x_var in variables_x)
    m.setObjective(obj, gb.GRB.MINIMIZE)
    # -------------------------------------------------------------------------
    
    # Constraints
    # -------------------------------------------------------------------------
    # print(dict_trees)
    # for colector_number in colector_numbers:
    #     for branch_number in branch_number_dict[colector_number]:
    #         for node_in_tree in dict_trees[(colector_number, branch_number)].nodes:
    #             print(node_in_tree)

    
    
    # Location node ------------
    m.addConstrs((y.sum(colector_number, branch_number, node_in_tree, '*') == 1
                  for colector_number in colector_numbers
                  for branch_number in branch_number_dict[colector_number]
                  for node_in_tree in dict_trees[(colector_number, branch_number)].nodes
                  ), "location valve")
    # --------------------------
    m.addConstrs(
        (f.sum(colector_number, branch_number, edge_in_tree[0], edge_in_tree[1], node_in_grid, '*')
         - f.sum(colector_number, branch_number, edge_in_tree[0], edge_in_tree[1], '*', node_in_grid) 
         == y[colector_number, branch_number, edge_in_tree[0], node_in_grid]
         for colector_number in colector_numbers
         for branch_number in branch_number_dict[colector_number]
         for edge_in_tree in dict_trees[(colector_number, branch_number)].edges
         for node_in_grid in dict_grids[(colector_number, branch_number)].nodes
         if dict_grids[(colector_number, branch_number)].nodes[node_in_grid]["node"] == edge_in_tree[0]
         ), "conservation flow in source y")
    # --------------------------
    m.addConstrs(
        (f.sum(colector_number, branch_number, edge_in_tree[0], edge_in_tree[1], node_in_grid, '*')
         - f.sum(colector_number, branch_number, edge_in_tree[0], edge_in_tree[1], '*', node_in_grid) 
         == -y[colector_number, branch_number, edge_in_tree[1], node_in_grid]
         for colector_number in colector_numbers
         for branch_number in branch_number_dict[colector_number]
         for edge_in_tree in dict_trees[(colector_number, branch_number)].edges
         for node_in_grid in dict_grids[(colector_number, branch_number)].nodes
         if dict_grids[(colector_number, branch_number)].nodes[node_in_grid]["node"] == edge_in_tree[1]
         ), "conservation flow in sink y")
    # --------------------------
    m.addConstrs(
        (f.sum(colector_number, branch_number, edge_in_tree[0], edge_in_tree[1], node_in_grid, '*') 
          - f.sum(colector_number, branch_number, edge_in_tree[0], edge_in_tree[1], '*', node_in_grid) 
          == 0 
          for colector_number in colector_numbers
          for branch_number in branch_number_dict[colector_number]
          for edge_in_tree in dict_trees[(colector_number, branch_number)].edges
          for node_in_grid in dict_grids[(colector_number, branch_number)].nodes
           if (dict_grids[(colector_number, branch_number)].nodes[node_in_grid]["node"] != edge_in_tree[0] 
              and dict_grids[(colector_number, branch_number)].nodes[node_in_grid]["node"] != edge_in_tree[1])
          ), "regular conservation flow")
    # -------------------------------
    m.addConstrs(
        (x[colector_number, branch_number, arc_in_grid[0], arc_in_grid[1]] 
          >= f[colector_number, branch_number, edge_in_tree[0], edge_in_tree[1], arc_in_grid[0], arc_in_grid[1]]
          for colector_number in colector_numbers
          for branch_number in branch_number_dict[colector_number]
          for arc_in_grid in dict_grids[(colector_number, branch_number)].edges
          for edge_in_tree in dict_grids[(colector_number, branch_number)].edges[arc_in_grid]['padreHijo']
          ), "x")
    # -------------------------------
    m.addConstrs(
        (x.sum(colector_number, branch_number, node_in_grid, '*')
          == y[colector_number, branch_number, 0, node_in_grid]
          for colector_number in colector_numbers
          for branch_number in branch_number_dict[colector_number]
          for node_in_grid in dict_grids[(colector_number, branch_number)].nodes
          if dict_grids[(colector_number, branch_number)].nodes[node_in_grid]["node"] == 0
          ), 
        "one edge from the root")
    # -------------------------------
    m.addConstrs(
        (x.sum(colector_number, branch_number, '*', node_in_grid)
         == y[colector_number, branch_number, dict_grids[(colector_number, branch_number)].nodes[node_in_grid]["node"], node_in_grid]
        for colector_number in colector_numbers
        for branch_number in branch_number_dict[colector_number]
        for node_in_grid in dict_grids[(colector_number, branch_number)].nodes
        if ("typ" in dict_grids[(colector_number, branch_number)].nodes[node_in_grid] 
            and dict_grids[(colector_number, branch_number)].nodes[node_in_grid]["typ"] == 'leaf')
        ), "one edge to the leaf")
    # -------------------------------
    m.addConstrs(
        (x.sum(colector_number, branch_number, node_in_grid, '*') 
         <= 1 - y[colector_number, branch_number, dict_grids[(colector_number, branch_number)].nodes[node_in_grid]["node"], node_in_grid]
         for colector_number in colector_numbers
         for branch_number in branch_number_dict[colector_number]
         for node_in_grid in dict_grids[(colector_number, branch_number)].nodes
         if ("typ" in dict_grids[(colector_number, branch_number)].nodes[node_in_grid] 
             and dict_grids[(colector_number, branch_number)].nodes[node_in_grid]["typ"] == 'leaf')
         ), "no edge from the leaf")
    # -------------------------------
    m.addConstrs(
        (f[colector_number, branch_number, edge_in_tree[0], edge_in_tree[1], arc_in_grid[0], arc_in_grid[1]] 
          + f[colector_number, branch_number, edge_in_tree[0], edge_in_tree[1], arc_in_grid[1], arc_in_grid[0]]
          <= 1
          for colector_number in colector_numbers
          for branch_number in branch_number_dict[colector_number]
          for arc_in_grid in dict_grids[(colector_number, branch_number)].edges
          for edge_in_tree in dict_grids[(colector_number, branch_number)].edges[arc_in_grid]['padreHijo']
          ), "one direction")
     # -------------------------------------------------------------------------

    # Gurobi parameters
    m.Params.MIPGap = gap
    m.Params.TimeLimit = timelimit
    m.Params.LazyConstraints = 1
    m.Params.LogToConsole = 0
    
    # Variables for the lazy constraints
    #-------------------------------------------------------------------------
    m._x = x
    m._dict_grids = dict_grids
    m._security_distance = security_distance
    m._colector_edges_dict = colector_edges_dict
    #-------------------------------------------------------------------------

    # solve
    restricciones_iniciales = m.NumConstrs
    start_time = time.time()
    m.optimize(functionLazy)
    end_time = time.time()
    
    # print(m.status)

    if m.SolCount == 0:
        # dictValues = "no solution"
        print("runtime: " + str(m.runtime))
        # Compute an Irreducible Inconsistent Subsystem (IIS)
        # IIS is infeasible. If any of the constraints or bounds of the IIS is
        # removed, the subsystem becomes feasible
        # m.computeIIS()
        # m.write("infeasible.ilp")
        # dictValues = "no solution"
        
        return [], []
        
    if m.status != 3:
        print(f"Restricciones iniciales: {restricciones_iniciales}")
        print(f"Restricciones lazy añadidas: {lazy_count}")
        print(f"Número de variables: {m.NumVars}")
        print(f"Número de restricciones: {m.NumConstrs}")
        print(f"Valor de la función objetivo: {m.ObjVal}")
        print(f"Tiempo de resolución: {end_time - start_time:.4f} segundos")

        solutionX = [
            ast.literal_eval(v.VarName[1:])
            for v in m.getVars() if "x" in v.VarName and v.X > 0.5
        ]
        
        
        sol_x_dict = {(i[0], i[1]): [] for i in solutionX}        
        
        for i in solutionX:
            grid = dict_grids[(i[0], i[1])]
            coor_1 = grid.nodes[i[2]]["coor"]
            coor_2 = grid.nodes[i[3]]["coor"]
            sol_x_dict[(i[0], i[1])].append((coor_1, coor_2))

        solutionY = [
            ast.literal_eval(v.VarName[1:])
            for v in m.getVars() if "y" in v.VarName and v.X > 0.5
        ]
        
        sol_y_dict = {}        

        for i in solutionY:
            grid = dict_grids[(i[0], i[1])]
            coor = grid.nodes[i[3]]["coor"]
            sol_y_dict[(i[0], i[1], i[2])] = coor
            
            
        path_folder = "./output/" + nameScenario + "distance" + str(security_distance)
        if os.path.exists(path_folder):
            # Deletes the folder and all its contents
            shutil.rmtree(path_folder)  
        os.makedirs(path_folder)
        
        dicc_output = {}
        f_valores = dict([(tuple(ast.literal_eval(v.VarName[1:])),v.X) 
                    for v in m.getVars() if "f" in v.VarName])
        dicc_output['f'] = f_valores
        x_valores = dict([(tuple(ast.literal_eval(v.VarName[1:])),v.X) 
                    for v in m.getVars() if "x" in v.VarName])
        dicc_output['x'] = x_valores
        y_valores = dict([(tuple(ast.literal_eval(v.VarName[1:])),v.X) 
                    for v in m.getVars() if "y" in v.VarName])
        dicc_output['y'] = y_valores
        dicc_output['runtime'] = m.runtime
        obj = m.getObjective()
        dicc_output['objective'] = obj.getValue()
        dicc_output['GAP'] = m.MIPGap
        dicc_output['variables'] = m.NumVars
        dicc_output['constraints'] = m.NumConstrs
        dicc_output["security_distance"] = security_distance
        
        # Create txt with scenario characteristics
        with open(path_folder + "/info.txt", "w") as file:
            for key, value in dicc_output.items():
                file.write(f"{key}: {value}\n")

        return sol_x_dict, sol_y_dict
# ============================================================================= 
    
  
# ============================================================================= 
def functionLazy(model, where):
    
    global lazy_count
        
    if where == gb.GRB.Callback.MIPNODE:
        nodecnt = model.cbGet(gb.GRB.Callback.MIPNODE_NODCNT)

        if nodecnt==0:
            model._lproot=model.cbGet(gb.GRB.Callback.MIPNODE_OBJBND)
            model._timelp=model.cbGet(gb.GRB.Callback.RUNTIME)

    if where == gb.GRB.Callback.MIPSOL:
        nodecnt = model.cbGet(gb.GRB.Callback.MIPSOL_NODCNT)
        if nodecnt==0:# and status!=2:

            model._lproot=model.cbGet(gb.GRB.Callback.MIPSOL_OBJ)
            model._timelp=model.cbGet(gb.GRB.Callback.RUNTIME)   
        
        # Cargar cosas
        # ---------------------------------------------------------------------
        vals_x = model.cbGetSolution(model._x)
        dict_grids = model._dict_grids
        security_distance = model._security_distance
        colector_edges_dict = model._colector_edges_dict
        # ---------------------------------------------------------------------

        # Arcs that are solution
        selected = gb.tuplelist(a for a in vals_x if vals_x[a] > 0.5)

        # print('---')
        # print(list(selected))




        # Introduce constraints if necesary
        # Distance between arcs solution
        for idx_1, entry_1 in enumerate(selected):
            helpy = idx_1 + 1
            list_variables = [entry_1]
            for idx_2 in range(helpy, len(selected)):
                entry_2 = selected[idx_2]
                if entry_1[0] != entry_2[0] or entry_1[1] != entry_2[1]:
                    arc1_1 = dict_grids[(entry_1[0], entry_1[1])].nodes[entry_1[2]]["coor"]
                    arc1_2 = dict_grids[(entry_1[0], entry_1[1])].nodes[entry_1[3]]["coor"]
                    arc1 = (arc1_1, arc1_2)
                    arc2_1 = dict_grids[(entry_2[0], entry_2[1])].nodes[entry_2[2]]["coor"]
                    arc2_2 = dict_grids[(entry_2[0], entry_2[1])].nodes[entry_2[3]]["coor"]
                    arc2 = (arc2_1, arc2_2)
                    distance = aux.dist3DSegmentToSegment(arc1, arc2)
                    if distance <= security_distance:
                        list_variables.append(entry_2)
            if len(list_variables) > 1:
                model.cbLazy(gb.quicksum(model._x[i] for i in list_variables) <= 1)
                lazy_count += 1  # Incrementar contador
        #
        # Distance between arc solution and colectors
        list_null_variables = []
        # print(colector_edges_dict)
        for colector_number, colector_edges in colector_edges_dict.items():
            for var_sol in selected:
                if colector_number != var_sol[0]:
                    for arc_colector in colector_edges:
                        arc_sol_1 = dict_grids[(var_sol[0], var_sol[1])].nodes[var_sol[2]]["coor"]
                        arc_sol_2 = dict_grids[(var_sol[0], var_sol[1])].nodes[var_sol[3]]["coor"]
                        arc_sol = (arc_sol_1, arc_sol_2)
                        distance_col = aux.dist3DSegmentToSegment(arc_colector, arc_sol)
                        if distance_col <= security_distance:
                            list_null_variables.append(var_sol)
        if len(list_null_variables) > 0:
            model.cbLazy(gb.quicksum(model._x[i] for i in list_null_variables) == 0)
            lazy_count += 1  # Incrementar contador
            # print('XXXXXXXXXXXXXXXXXXXXXXX')
# ============================================================================= 


                

