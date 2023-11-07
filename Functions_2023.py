# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 17:56:24 2023

Functions

@author: tingbai
"""

#-------------------------------------------------------------------------------
'''(1) — Compute P_i(k) offline'''

def Potential_partner_set(OD_jun_dict, common_edge):
    #OD_jun_dict: {vi:[oi,hub1,hub2,...,di] ordered hubs of each truck
    #common_edge: {common edge:[vehilce-list]}
    
    #1. initialize P_i
    v_jun_p={}
    for i in OD_jun_dict.keys():
        v_p={}
        for h in range(len(OD_jun_dict[i])):
            v_p[OD_jun_dict[i][h]]=[]#P_i=emptyset 
        v_jun_p[i]=v_p
            
    #2. obtain P_i for each vehicle at every hub
    for edge in common_edge.keys():
        edge_start=edge[0]
        v_list=common_edge[edge]
        for v in v_list:
            v_jun_p[v][edge_start]=v_list
            
    return v_jun_p

#-------------------------------------------------------------------------------
'''(2-1) —— Vary the departure time of different trucks leaving from the origin'''
import random

def Ini_td_variation(OD_jun_dict, t_str_v):
    t_str_v_varied={}
    
    Td_add={} # the time to be added to the time sequence for every truck
    for i in t_str_v.keys():
        Td_add[i]=random.randint(0,36)*100 # seconds, 08:00-09:00
    
    # Add td0_add to the original time sequence
    for i in t_str_v.keys():
        t_sequence=[]
        t_to_add=Td_add[i]
        for n in range(len(OD_jun_dict[i])-1):
            t_s_ori=t_str_v[i][n]
            t_s_new=[]
            for t in t_s_ori:
                t_new=(parse(t)+timedelta(seconds=t_to_add)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
                t_s_new.append(t_new)
            t_sequence.append(t_s_new)
        t_str_v_varied[i]=t_sequence
        
    return t_str_v_varied
                
    

#-------------------------------------------------------------------------------
'''(2-2) — Initialize the arrival and departure time of a truck at all the hubs'''

def v_arr_dep_hubs0(OD_jun_dict, t_str_v):
    v_arr_dep_hubs={}
    
    for i in OD_jun_dict.keys():
        arr_dep={}
        for n in range(len(OD_jun_dict[i])):
            hub=OD_jun_dict[i][n]
            if n!=len(OD_jun_dict[i])-1:
                arr_dep[hub]={'t_a': [t_str_v[i][n][0]],'t_d': [t_str_v[i][n][0]], 'label': 'I'}
            else:
                arr_dep[hub]={'t_a': [t_str_v[i][n-1][-1]], 't_d':[]} # the destination
            
        v_arr_dep_hubs[i]=arr_dep
        
    return v_arr_dep_hubs



#-------------------------------------------------------------------------------
'''(3) — Obtain the arrival times of related trucks in P_i(k) at every hubs'''
import copy

def arr_dep_hubs(OD_jun_dict, v_jun_p, v_arr_dep_hubs):
    
    # Add the arrival times of related trucks in v_jun_p
    v_jun_p_t=copy.deepcopy(v_jun_p)
    
    for i in v_jun_p.keys():
        for n in range(len(OD_jun_dict[i])):
            h=OD_jun_dict[i][n]#hub
            set_arr_t=[]
            # P_i at hub h is not empty
            if v_jun_p[i][h]!=[]:
                set_arr_t.append(v_jun_p[i][h])
                arr_dep_t={}
                for m in range(len(v_jun_p[i][h])):
                    v=v_jun_p[i][h][m] #related vehicle
                    t_arr=v_arr_dep_hubs[v][h]['t_a']
                    t_dep=v_arr_dep_hubs[v][h]['t_d']
                    arr_dep_t[v]={'t_a': t_arr,'t_d': t_dep}
                set_arr_t.append(arr_dep_t)
            else:
                set_arr_t.append([])
                arr_dep_t={}
                v=i
                t_arr=v_arr_dep_hubs[v][h]['t_a']
                t_dep=v_arr_dep_hubs[v][h]['t_d']
                arr_dep_t[v]={'t_a': t_arr, 't_d': t_dep}
                set_arr_t.append(arr_dep_t)
            v_jun_p_t[i][h]=set_arr_t
            
    return v_jun_p_t
    
#-------------------------------------------------------------------------------
'''(4) — Determine all the decision makers at system time t_c'''
import numpy as np
from dateutil.parser import parse

def v_decision_makers(OD_jun_dict, v_arr_dep_hubs, t_c):
    t_start='2021-11-20 08:00:00'
    #find vehicles arriving at a hub at system time t_c
    
    v_make_decision={}
    for i in v_arr_dep_hubs.keys():
        decision=[]
        for n in range(len(OD_jun_dict[i])):
            # the decision maker should not be a vehicle at the destination
            if n!=len(OD_jun_dict[i])-1:
                h=OD_jun_dict[i][n]#hub
                arr_v=v_arr_dep_hubs[i][h]['t_a']
                t_diff=np.array([(parse(arr_v[0])-parse(t_start)).total_seconds()-t_c*60])
                t_diff_norm=np.linalg.norm(t_diff, ord=None)
                if (t_diff_norm<=30):
                    decision.append(h)
                    decision.append({'t_a':arr_v})
                    break
        if decision!=[]:
            v_make_decision[i]=decision

    return v_make_decision    

#-------------------------------------------------------------------------------
'''(5) — Deal with the travel time'''

def jun_travel_time(OD_jun_dict, v_edge_time_l):
    #v_edge_time_l: travel time on segments, dic
    
    # obtain the travel time from hubs
    OD_jun_travel={}
    for i in OD_jun_dict.keys():
        #the list includes all the travel time of truck i
        tra_time_list=[]
        for n in v_edge_time_l[i].keys():
            tra_time_list.append(v_edge_time_l[i][n][0])
        
        truck_tra_time=[]
        for h in range(len(OD_jun_dict[i])-1):#the destination has no travel time
            hub_time=[]
            hub=OD_jun_dict[i][h]
            time=tra_time_list[h]#float
            hub_time.append(hub)
            hub_time.append(time)
            truck_tra_time.append(hub_time)
        OD_jun_travel[i]=truck_tra_time
        
    return OD_jun_travel

#-------------------------------------------------------------------------------
'''(6) — Parameter setting for t_i^{end}'''
from datetime import timedelta

def t_arr_end(OD_jun_dict, v_arr_dep_hubs, t_wait_hub):
    #t_wait_hub: parameter, the waiting time at each hub(a value between lower and upper bounds of input)
    
    v_t_end={}
    for i in v_arr_dep_hubs.keys():
        #h_ori=OD_jun_dict[i][0]#origin
        h_end=OD_jun_dict[i][-1]#destination
        #t_start=v_arr_dep_hubs[i][h_ori]['t_a']
        t_end=v_arr_dep_hubs[i][h_end]['t_a']
        num_hubs=len(OD_jun_dict[i])
        max_w_t=t_wait_hub*(num_hubs-1)#seconds
        max_w_tn=np.array([timedelta(seconds=max_w_t)])
        t_end_n=np.append(parse(t_end[0]),max_w_tn).cumsum()
        t_end_bound=str(t_end_n[-1])# the latest arrival time at destination, str
        v_t_end[i]=[t_end_bound]
        
    return v_t_end

#--------------------------------------------------------------------------------
'''(6-2) — Constant Parameter setting for t_i^{end}'''

def t_arr_end_2(OD_jun_dict, v_arr_dep_hubs, t_extend_end):
    #t_wait_hub: parameter, the waiting time at each hub(a value between lower and upper bounds of input)
    
    v_t_end_2={}
    for i in v_arr_dep_hubs.keys():
        h_end=OD_jun_dict[i][-1]#destination
        t_end=v_arr_dep_hubs[i][h_end]['t_a']
        max_w_tn=np.array([timedelta(seconds=t_extend_end)])
        t_end_n=np.append(parse(t_end[0]),max_w_tn).cumsum()
        t_end_bound=str(t_end_n[-1])# the latest arrival time at destination, str
        v_t_end_2[i]=[t_end_bound]
        
    return v_t_end_2

#-------------------------------------------------------------------------------
'''(6-3) — Constant Parameter setting for t_i^{end}-- set as 10% of the total travel time of each truck'''

def t_arr_end_3(OD_jun_dict, v_arr_dep_hubs, t_extend_end_v):
    #t_wait_hub: parameter, the waiting time at each hub(a value between lower and upper bounds of input)
    # t_extend_end_v: a dict, which includes the extended waiting time at the destination for different trucks
    
    v_t_end_3={}
    for i in v_arr_dep_hubs.keys():
        h_end=OD_jun_dict[i][-1]#destination
        t_end=v_arr_dep_hubs[i][h_end]['t_a']
        max_w_tn=np.array([timedelta(seconds=t_extend_end_v[i])])
        t_end_n=np.append(parse(t_end[0]),max_w_tn).cumsum()
        t_end_bound=str(t_end_n[-1])# the latest arrival time at destination, str
        v_t_end_3[i]=[t_end_bound]
        
    return v_t_end_3
#--------------------------------------------------------------------------------
'''(7) — Update the arrival and departure times of a truck at future hubs'''

def v_arr_dep_hubs_update(i, hub_k, x_val, y_val, v_arr_dep_hubs, OD_jun_dict):
    
    v_arr_dep_hubs_update=copy.deepcopy(v_arr_dep_hubs)
    
    k = OD_jun_dict[i].index(hub_k)
    for n in range(k, len(v_arr_dep_hubs[i])):
        h=OD_jun_dict[i][n]
        v_arr_dep_hubs_update[i][h]['t_a']=[x_val[n-k]]
        if n!=len(v_arr_dep_hubs[i])-1:
            v_arr_dep_hubs_update[i][h]['t_d']=[y_val[n-k]]
            
    return v_arr_dep_hubs_update
            




        

