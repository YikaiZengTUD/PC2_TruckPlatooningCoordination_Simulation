# -*- coding: utf-8 -*-
"""
Created on Tue Nov 7 17:54:08 2023

Initialization: Functions --Fourth Edition-functions

@author: tingbai
"""

#-------------------------------------------------
#find the edge-set for each vehicle

def edges_between_OD(OD_jun_dict):#OD_jun_dict includes the orgin and destination
    #input:ordered junctions of each OD
    edge_vehicle={}
    for k in range(len(OD_jun_dict.keys())):
        edges=[]
        for i in range(len(OD_jun_dict[k])):#len(OD_jun_dict[k]>=2)
            edges.append((OD_jun_dict[k][i],OD_jun_dict[k][i+1]))
            if i==(len(OD_jun_dict[k])-2):
                break
        edge_vehicle[k]=edges
    
    return edge_vehicle

#-------------------------------------------------
#find common edges for different OD, and determine the information of every hub

def hub_inf(edge_vehicle):
    edge_list=[]
    for i in edge_vehicle.keys():#all the vehicles
        for j in range(len(edge_vehicle[i])):
            edge_list.append(edge_vehicle[i][j])
    edge_uni=set(edge_list)
   # put all the edges in a set, removing the repeating edges

    edge_index={}#for all the edges
    common_edge_index={}
    for i in range(len(edge_uni)):
        index=[]
        for j in edge_vehicle.keys():
            if list(edge_uni)[i] in edge_vehicle[j]:
                index.append(j)
        edge_index[list(edge_uni)[i]]=index
        if len(edge_index[list(edge_uni)[i]])!=1:
            common_edge_index[list(edge_uni)[i]]=index
    return common_edge_index# common_edge_index is a dictionary, the key is the common edge, the indexes are the number of vehicles passing this common edge
