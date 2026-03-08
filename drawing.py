# -*- coding: utf-8 -*-
"""
Created on Sun Nov 26 13:45:06 2023

@author: Trabajador
"""

import matplotlib.pyplot as plt
# import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import auxiliar as aux


# =============================================================================
def pintaSolucion(nameScenario, sol_x_dict, sol_y_dict, security_distance):
        
    # Read data
    # -------------------------------------
    continuous_scenario, grids = aux.readScenario(nameScenario)
    # -------------------------------------
    
    # Colours
    # -------------------------------------------------------------------------
    number_colours = len([tree 
                         for list_tree in continuous_scenario["arboles"].values() 
                         for tree in list_tree])

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
    
    colours = dicc_colours[number_colours]
    
    # print('xxxxxxxxxxxxxxxxxxx')
    # print(type(sol_x_dict))
    # print(sol_x_dict)
    # print('xxxxxxxxxxxxxxxxxxx')
    
    dicc_branch_colours = dict(zip(sol_x_dict.keys(), colours))
    # -------------------------------------------------------------------------
    
    # initialization
    # -------------------------------------------------------------------------
    fig = plt.figure()
    ax  = fig.add_subplot(111, projection = '3d')
    # -------------------------------------------------------------------------
    
    # Set common labels
    # -------------------------------------------------------------------------
    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    ax.set_zlabel('Z-axis')
    # -------------------------------------------------------------------------
 
    # # Edges grids
    # # -------------------------------------------------------------------------
    # for grid in grids:
    #     for i in grid.edges:
    #         xs = [grid.edges[i]["coor"][0][0], grid.edges[i]["coor"][1][0]]
    #         ys = [grid.edges[i]["coor"][0][1], grid.edges[i]["coor"][1][1]]
    #         zs = [grid.edges[i]["coor"][0][2], grid.edges[i]["coor"][1][2]]
    #         ax.plot(xs, ys, zs, color = "grey", alpha = 0.1)   
    # # -------------------------------------------------------------------------

    # Edges colector
    # -------------------------------------------------------------------------
    for colector_points in continuous_scenario["colectores"].values():
        aristas_colector = list(zip(colector_points[:-1], colector_points[1:]))
        for i in aristas_colector:
            xs = [i[0][0], i[1][0]]
            ys = [i[0][1], i[1][1]]
            zs = [i[0][2], i[1][2]]
            ax.plot(xs, ys, zs, color = "black")    
    # -------------------------------------------------------------------------
    
    # Edges branches
    # -------------------------------------------------------------------------
    for key, edges in sol_x_dict.items():
        colour = dicc_branch_colours[key]
        for i in edges:
            xs = [i[0][0], i[1][0]]
            ys = [i[0][1], i[1][1]]
            zs = [i[0][2], i[1][2]]
            ax.plot(xs, ys, zs, color = colour)
    # -------------------------------------------------------------------------
    
    
    # lista = [(0, 0, 1), (0, 0, 3), (0, 0, 6), (0, 0, 8), (0, 0, 9),
    #           (0, 1, 2), (0, 1, 7), (0, 1, 9),
    #           (1, 0, 1), (1, 0, 2), (1, 0, 4), (1, 0, 5), (1, 0, 7), (1, 0, 9),
    #           (1, 1, 2), (1, 1, 6), (1, 1, 8), (1, 1, 9)]
    
    # Points branches
    # -------------------------------------------------------------------------
    for key, point in sol_y_dict.items():
        colour = dicc_branch_colours[(key[0], key[1])]
        ax.scatter(point[0], point[1], point[2], color = colour, marker = "o")
        ax.text(point[0], point[1], point[2], key[2])
    # -------------------------------------------------------------------------
    
    # Get spaces from graph
    # -------------------------------------------------------------------------
    dicc_space = {}
    for number_colector, Ts in continuous_scenario["arboles"].items():
        for number_branch, T in enumerate(Ts):
            for i in T.nodes:
                if 'space' in T.nodes[i]:
                    dicc_info = {}
                    center_valve = T.nodes[i]['center'][0]
                    margin_valve = T.nodes[i]["epsilon"][0]
                    coor0 = [center_valve[0] - margin_valve[0],
                              center_valve[1] - margin_valve[1],
                              center_valve[2] - margin_valve[2]]
                    coor1 = [center_valve[0] + margin_valve[0],
                              center_valve[1] + margin_valve[1],
                              center_valve[2] + margin_valve[2]]
                    dicc_info["space"] = [coor0, coor1]
                    dicc_info["center"] = T.nodes[i]['center'][0]
                    dicc_space[(number_colector, number_branch, i)] = dicc_info
    # -------------------------------------------------------------------------
    
    # valveSpace are the coordinates of two vertices of the prism that forms
    # the space. The vertex with the minimum coordinates and the vertex with
    # the maximum coordinates
    # Plotting Valve Space
    # -------------------------------------------------------------------------
    for key, value in dicc_space.items():
        
        # Determine colour
        # --
        colour = dicc_branch_colours[(key[0], key[1])]
        # --
        
        # Plot number inside space
        # --
        nodo = key[2]
        center = value["center"]
        # ax.scatter(center[0], center[1], center[2], color = 'black', marker = "o")
        ax.text(center[0], center[1], center[2], nodo, color = 'black', size = 'xx-large')
        # --

        # print(key, value)
        coorVerticesValve = value["space"]
        # Vertices of prism   
        V0 = (coorVerticesValve[0][0],
              coorVerticesValve[0][1],
              coorVerticesValve[0][2])
        V1 = (coorVerticesValve[1][0],
              coorVerticesValve[0][1],
              coorVerticesValve[0][2])
        V2 = (coorVerticesValve[0][0],
              coorVerticesValve[1][1],
              coorVerticesValve[0][2])
        V3 = (coorVerticesValve[1][0],
              coorVerticesValve[1][1],
              coorVerticesValve[0][2])
        V4 = (coorVerticesValve[0][0],
              coorVerticesValve[0][1],
              coorVerticesValve[1][2])
        V5 = (coorVerticesValve[1][0],
              coorVerticesValve[0][1],
              coorVerticesValve[1][2])
        V6 = (coorVerticesValve[0][0],
              coorVerticesValve[1][1],
              coorVerticesValve[1][2])
        V7 = (coorVerticesValve[1][0],
              coorVerticesValve[1][1],
              coorVerticesValve[1][2])
    
        # Vertices by X, Y, Z coordinate
        VX = [V0[0], V1[0], V2[0], V3[0], V4[0], V5[0], V6[0], V7[0]]
        VY = [V0[1], V1[1], V2[1], V3[1], V4[1], V5[1], V6[1], V7[1]]
        VZ = [V0[2], V1[2], V2[2], V3[2], V4[2], V5[2], V6[2], V7[2]]
    
        # Points
        p = []
        for i in range(len(VX)):
            helpy = [VX[i], VY[i], VZ[i]]
            # ax.scatter(VX[i], VY[i], VZ[i], color = 'black', marker = "o")
            # ax.text(VX[i], VY[i], VZ[i], idx)
            p.append(helpy)
            
        # faces of prism
        caras = [[p[0],p[2],p[3],p[1]],
                  [p[1],p[5],p[7],p[3]],
                  [p[4],p[6],p[7],p[5]],
                  [p[2],p[3],p[7],p[6]],
                  [p[6],p[2],p[0],p[4]],
                  [p[0],p[4],p[5],p[1]]]
        
        # plot the prism
        collection = Poly3DCollection(caras, facecolors=colour, linewidths=0.1, edgecolors='b', alpha=.2)
        ax.add_collection3d(collection)
    # -------------------------------------------------------------------------

    # Maximize the window
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    # Plot everything
    plt.show()
    # -------------------------------------------------------------------------

    plt.savefig("./output/" + nameScenario + "distance" + str(security_distance) + "/" + 'dibujo_sol.png', dpi=300, bbox_inches='tight')
# =============================================================================

















# =============================================================================
def pintaSolucion2(nameScenario, sol_x_dict, sol_y_dict):
        
    # Read data
    # -------------------------------------
    continuous_scenario, grids = aux.readScenario(nameScenario)
    # -------------------------------------
    
    # Colours
    # -------------------------------------------------------------------------
    number_colours = len([tree 
                         for list_tree in continuous_scenario["arboles"].values() 
                         for tree in list_tree])

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
    
    colours = dicc_colours[number_colours]
    dicc_branch_colours = dict(zip(sol_x_dict.keys(), colours))
    # -------------------------------------------------------------------------
    
    # initialization
    # -------------------------------------------------------------------------
    fig = plt.figure()
    ax  = fig.add_subplot(111, projection = '3d')
    # -------------------------------------------------------------------------
    
    # Set common labels
    # -------------------------------------------------------------------------
    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    ax.set_zlabel('Z-axis')
    # -------------------------------------------------------------------------
 
    # # Edges grids
    # # -------------------------------------------------------------------------
    # for grid in grids:
    #     for i in grid.edges:
    #         xs = [grid.edges[i]["coor"][0][0], grid.edges[i]["coor"][1][0]]
    #         ys = [grid.edges[i]["coor"][0][1], grid.edges[i]["coor"][1][1]]
    #         zs = [grid.edges[i]["coor"][0][2], grid.edges[i]["coor"][1][2]]
    #         ax.plot(xs, ys, zs, color = "grey", alpha = 0.1)   
    # # -------------------------------------------------------------------------

    # # Edges colector
    # # -------------------------------------------------------------------------
    # for colector_points in continuous_scenario["colectores"].values():
    #     aristas_colector = list(zip(colector_points[:-1], colector_points[1:]))
    #     for i in aristas_colector:
    #         xs = [i[0][0], i[1][0]]
    #         ys = [i[0][1], i[1][1]]
    #         zs = [i[0][2], i[1][2]]
    #         ax.plot(xs, ys, zs, color = "black")    
    # # -------------------------------------------------------------------------
    
    # Edges branches
    # -------------------------------------------------------------------------
    for key, edges in sol_x_dict.items():
        colour = dicc_branch_colours[key]
        for i in edges:
            xs = [i[0][0], i[1][0]]
            ys = [i[0][1], i[1][1]]
            zs = [i[0][2], i[1][2]]
            ax.plot(xs, ys, zs, color = colour)
    # -------------------------------------------------------------------------
    
    
    # lista = [(0, 0, 1), (0, 0, 3), (0, 0, 6), (0, 0, 8), (0, 0, 9),
    #           (0, 1, 2), (0, 1, 7), (0, 1, 9),
    #           (1, 0, 1), (1, 0, 2), (1, 0, 4), (1, 0, 5), (1, 0, 7), (1, 0, 9),
    #           (1, 1, 2), (1, 1, 6), (1, 1, 8), (1, 1, 9)]
    
    # # Points branches
    # # -------------------------------------------------------------------------
    # for key, point in sol_y_dict.items():
    #     colour = dicc_branch_colours[(key[0], key[1])]
    #     ax.scatter(point[0], point[1], point[2], color = colour, marker = "o")
    #     ax.text(point[0], point[1], point[2], key[2])
    # # -------------------------------------------------------------------------
    
    # Get spaces from graph
    # -------------------------------------------------------------------------
    dicc_space = {}
    for number_colector, Ts in continuous_scenario["arboles"].items():
        for number_branch, T in enumerate(Ts):
            for i in T.nodes:
                if 'space' in T.nodes[i]:
                    dicc_info = {}
                    center_valve = T.nodes[i]['center'][0]
                    margin_valve = T.nodes[i]["epsilon"][0]
                    coor0 = [center_valve[0] - margin_valve[0],
                              center_valve[1] - margin_valve[1],
                              center_valve[2] - margin_valve[2]]
                    coor1 = [center_valve[0] + margin_valve[0],
                              center_valve[1] + margin_valve[1],
                              center_valve[2] + margin_valve[2]]
                    dicc_info["space"] = [coor0, coor1]
                    dicc_info["center"] = T.nodes[i]['center'][0]
                    dicc_space[(number_colector, number_branch, i)] = dicc_info
    # -------------------------------------------------------------------------
    
    # # valveSpace are the coordinates of two vertices of the prism that forms
    # # the space. The vertex with the minimum coordinates and the vertex with
    # # the maximum coordinates
    # # Plotting Valve Space
    # # -------------------------------------------------------------------------
    # for key, value in dicc_space.items():
        
    #     # Determine colour
    #     # --
    #     colour = dicc_branch_colours[(key[0], key[1])]
    #     # --
        
    #     # Plot number inside space
    #     # --
    #     nodo = key[2]
    #     center = value["center"]
    #     # ax.scatter(center[0], center[1], center[2], color = 'black', marker = "o")
    #     ax.text(center[0], center[1], center[2], nodo, color = 'black', size = 'xx-large')
    #     # --

    #     # print(key, value)
    #     coorVerticesValve = value["space"]
    #     # Vertices of prism   
    #     V0 = (coorVerticesValve[0][0],
    #           coorVerticesValve[0][1],
    #           coorVerticesValve[0][2])
    #     V1 = (coorVerticesValve[1][0],
    #           coorVerticesValve[0][1],
    #           coorVerticesValve[0][2])
    #     V2 = (coorVerticesValve[0][0],
    #           coorVerticesValve[1][1],
    #           coorVerticesValve[0][2])
    #     V3 = (coorVerticesValve[1][0],
    #           coorVerticesValve[1][1],
    #           coorVerticesValve[0][2])
    #     V4 = (coorVerticesValve[0][0],
    #           coorVerticesValve[0][1],
    #           coorVerticesValve[1][2])
    #     V5 = (coorVerticesValve[1][0],
    #           coorVerticesValve[0][1],
    #           coorVerticesValve[1][2])
    #     V6 = (coorVerticesValve[0][0],
    #           coorVerticesValve[1][1],
    #           coorVerticesValve[1][2])
    #     V7 = (coorVerticesValve[1][0],
    #           coorVerticesValve[1][1],
    #           coorVerticesValve[1][2])
    
    #     # Vertices by X, Y, Z coordinate
    #     VX = [V0[0], V1[0], V2[0], V3[0], V4[0], V5[0], V6[0], V7[0]]
    #     VY = [V0[1], V1[1], V2[1], V3[1], V4[1], V5[1], V6[1], V7[1]]
    #     VZ = [V0[2], V1[2], V2[2], V3[2], V4[2], V5[2], V6[2], V7[2]]
    
    #     # Points
    #     p = []
    #     for i in range(len(VX)):
    #         helpy = [VX[i], VY[i], VZ[i]]
    #         # ax.scatter(VX[i], VY[i], VZ[i], color = 'black', marker = "o")
    #         # ax.text(VX[i], VY[i], VZ[i], idx)
    #         p.append(helpy)
            
    #     # faces of prism
    #     caras = [[p[0],p[2],p[3],p[1]],
    #               [p[1],p[5],p[7],p[3]],
    #               [p[4],p[6],p[7],p[5]],
    #               [p[2],p[3],p[7],p[6]],
    #               [p[6],p[2],p[0],p[4]],
    #               [p[0],p[4],p[5],p[1]]]
        
    #     # plot the prism
    #     collection = Poly3DCollection(caras, facecolors=colour, linewidths=0.1, edgecolors='b', alpha=.2)
    #     ax.add_collection3d(collection)
    # # -------------------------------------------------------------------------

    # Maximize the window
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    # Plot everything
    plt.show()
    # -------------------------------------------------------------------------

    # plt.savefig("./output/" + nameScenario + "/" + 'dibujo_sol.png', dpi=300, bbox_inches='tight')
# =============================================================================



















