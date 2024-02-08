# -*- coding: utf-8 -*-
"""
Created on Tue Nov 7 12:59:41 2023

—— The main DP algorithm for solving the multi-fleet platoon coordination problem of 1000 trucks
—— No constraint on the waiting time at each hub

@author: tingbai
"""

#--------------------------------------------------------------------
''' 1 — Upload data'''

from Initialization_2023 import edges_between_OD, hub_inf
from Functions_2023 import Potential_partner_set, t_arr_end_3, arr_dep_hubs
from Functions_2023 import v_decision_makers, v_arr_dep_hubs_update
from DP_functions_Journal_2023 import data_td_groups, data_add_ta, remove_td_e, data_DP_graph_new, DMPC_DP_algorithm, Solution_org
import copy

f=open('data/OD_hubs_new_1000Trucks','r')
a=f.read()
OD_hubs_dict=eval(a) # hubs between the origin and destination
f.close()

# f=open('time_str_new_1000Trucks','r')
# a=f.read()
# time_str_ordered=eval(a) # ordered time sequence of each truck
# f.close()

f=open('data/travel_dd_1000Trucks','r')
a=f.read()
t_extend_end_v=eval(a) # a dict, which includes the allowed total waiting time (seconds) of each truck in the whole trip
f.close()

f=open('data/OD_hubs_travel_1000Trucks','r')
a=f.read()
OD_hubs_travel=eval(a) # travel times of different trucks on road segments
f.close()

f=open('data/vehicle_arr_dep_hubs0_1000Trucks','r') # the initial departure times from the origins 
a=f.read()
vehicle_arr_dep_hubs0=eval(a)
f.close()

#----------------------------------------------
#----------------------------------------------
''' 2 — Initialization'''

# 1) Compute P_i(k) offline, i.e., the potential platoon partners
edges_od=edges_between_OD(OD_hubs_dict)
common_edge=hub_inf(edges_od)
vehicle_jun_p =Potential_partner_set(OD_hubs_dict, common_edge) #Potential partner set

# 2-1) Vary the departure times of each truck that leaves from the origin (revised)
#t_str_v_new=Ini_td_variation(OD_hubs_dict, time_str_ordered) # the departure time is varied within 1 hour, from 08:00-09:00

# 2-2) Initialize the arrival and depature time of each truck at hubs
#vehicle_arr_dep_hubs0=v_arr_dep_hubs0(OD_hubs_dict, t_str_v_new)

# 3) The time bound of every truck at the destination
vehicle_t_end=t_arr_end_3(OD_hubs_dict, vehicle_arr_dep_hubs0, t_extend_end_v)


#----------------------------------------------
'''3 — Main Algorithm'''
import time
vehicle_arr_dep_hubs1=copy.deepcopy(vehicle_arr_dep_hubs0)

# Main loop: 
delta_t=1 #min

optimal_decision_v={}
optimal_cost_v={}
computation_time_v={}

for i in OD_hubs_dict.keys():
    optimal_decision_v[i]={}
    optimal_cost_v[i]={}
    computation_time_v[i]={}
    
tc_make_decision={}

from tqdm import tqdm # used to show the progress bar

for t_c in tqdm(range(0,750,delta_t)): 

    # 1. Find the vehicles to make a decision (i.e., those arriving at a hub) at time t_c:
    v_make_decision=v_decision_makers(OD_hubs_dict, vehicle_arr_dep_hubs1, t_c)
    if len(v_make_decision)!=0:
        tc_make_decision[t_c]=v_make_decision
         
        # 2. For decision makers, solve the DMPC problem:
        for i in v_make_decision.keys():   
            
            # set a clock
            start_time=time.perf_counter()
        
            hub_k=v_make_decision[i][0] # the current hub index
            hub_end=OD_hubs_dict[i][-1] # the destination of vehicle i
            t_start_k=v_make_decision[i][1]['t_a'][0]#str
            t_end=vehicle_t_end[i][0]#str arrival time deadline--> t_dd
        
            # 3. Obtain the arrival and departure times of every related trucks (in P_i) at hubs
            vehicle_jun_p_t=arr_dep_hubs(OD_hubs_dict, vehicle_jun_p, vehicle_arr_dep_hubs1)
            
            # 4. Choose the required information from vehicle_jun_p_t to generate the DP graph
            # 4-1. obtain the different td and the corresponding set of vehicles that departure at td
            hub_td_P=data_td_groups(vehicle_jun_p_t, i, hub_k)
            # 4-2. add the arrival time 
            hub_ta_td=data_add_ta(hub_td_P, OD_hubs_travel, OD_hubs_dict, i)
            # 4-3. remove the td earlier than ta
            hub_ta_td_new=remove_td_e(hub_ta_td, i)
           
            
            # 4-5. generate DP graph for vehicle i (revised: update the fleet distribution, which changes the value of each edge in DP graph)
            DP_graph=data_DP_graph_new(hub_ta_td_new, OD_hubs_travel, i)
            
            # 5. Solve the DMPC problem via DP (Dynamical Programming)
            Opt_decision_s=DMPC_DP_algorithm(DP_graph, i, hub_k, hub_end, t_end, OD_hubs_travel)
            
            
            # 6. Calculate the optimal arrival time x_opt, waiting time u_opt, and departure time y_opt according to the result in Opt_decision_v
            x_opt, u_opt, y_opt, J_i, Opt_decision_dict=Solution_org(Opt_decision_s, OD_hubs_travel, OD_hubs_dict)
 
            #end_time = datetime.datetime.now()  
            end_time=time.perf_counter()
            interval = round(end_time-start_time,4)
            
            #record the optimal decision of each truck
            optimal_decision_v[i][hub_k]=u_opt[0]
            optimal_cost_v[i][hub_k]=J_i
            computation_time_v[i][hub_k]=interval #seconds
        
            # 7. Update arrival and departure times at future hubs from hub_k
            vehicle_arr_dep_hubs_update=v_arr_dep_hubs_update(i, hub_k, x_opt, y_opt, vehicle_arr_dep_hubs1, OD_hubs_dict)
            vehicle_arr_dep_hubs1=copy.deepcopy(vehicle_arr_dep_hubs_update)


#f=open('vehicle_arr_dep_hubs0_1000','w')
#f.write(str(vehicle_arr_dep_hubs0)) # the initial information of trucks
#f.close()

f=open('vehicle_arr_dep_hubs1_1000Trucks_2023','w') 
f.write(str(vehicle_arr_dep_hubs1))
f.close()

f=open('optimal_decision_1000Trucks_2023','w')
f.write(str(optimal_decision_v)) # the optimal solution, input
f.close()

f=open('optimal_cost_1000Trucks_2023','w')
f.write(str(optimal_cost_v)) # the optimal cost function
f.close()

f=open('computation_time_1000Trucks_2023','w')
f.write(str(computation_time_v))
f.close()
        

        
        
    
    
        




