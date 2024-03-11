# -*- coding: utf-8 -*-

from map import GeoMap
from truck_swarm_parameters import TruckSwarm
from datetime import timedelta,datetime
from scripts.truck_methods import Truck

import csv

# # load from dict style files
# # contents are quite reduant since these are intermedia results from previous studies
# f=open('data\OD_hubs_new_1000Trucks','r')
# a=f.read()
# task_dict=eval(a) # hubs between the origin and destination
# f.close()
# # ----
# f=open('data\OD_hubs_travel_1000Trucks','r')
# a=f.read()
# travel_time_dict=eval(a) # travel times of different trucks on road segments
# f.close()
# # ----
# f=open('data\\vehicle_arr_dep_hubs0_1000Trucks','r') # the initial departure times from the origins 
# a=f.read()
# vehicle_arr_dep_test=eval(a)
# f.close()
# # ---
# f=open('data\\travel_dd_1000Trucks','r')
# a=f.read()
# travel_dd_test=eval(a) # a dict, which includes the allowed total waiting time (seconds) of each truck in the whole trip
# f.close()

# n_of_truck = len(task_dict)


# # Extract Map information from the OD pairs 
# M = GeoMap(task_dict)

# TS = TruckSwarm(n_of_truck,M.task_dict_node)

# ts_travel_duration_list = TS.collect_travel_duration(travel_time_dict) #FIXME: This is a dictionary

# ts_start_time_list  = TS.extract_departure_time(vehicle_arr_dep_test) #FIXME: Inconsistent in naming

# for t_index,_timing in enumerate(ts_start_time_list):
#     ts_start_time_list[t_index] = _timing - timedelta(seconds=60)

# # So we discuss about the timing here, we give DP search 90s for perform and another 30s for quick communication
# # This is to say that 2 mins before a truck arrive a hub, which we may say the truck is within the 300 m range of the hub

# # we move the 'starting operation' timing 60s earlier

# ts_waiting_budget       = travel_dd_test
# ts_max_operating_time   = TS.get_max_simulation_time(ts_start_time_list,ts_travel_duration_list,ts_waiting_budget)


# truck_list = [] # refer each truck with its index as key
# for truck_index in range(n_of_truck):
#     T = Truck(
#         M.task_dict_node[truck_index],
#         truck_index,
#         ts_start_time_list[truck_index],
#         ts_travel_duration_list[truck_index],
#         TS.assign_carrier_index(truck_index),
#         ts_waiting_budget[truck_index])
#     T.generate_edge_list(M.edge_list)
#     truck_list.append(T)

# print('Initlization: Truck Instantiation finished, Truck Amount:',n_of_truck)

def convert_setup_to_csv(truck_list:list):

    Header = ['Truck Index','Carrier Index','First Hub','First Edge','Start Time - 1min']

    data = []

    data.append(Header)

    for _truck in truck_list:
        this_line = []
        this_line.append(_truck.truck_index)
        this_line.append(_truck.carrier_index)
        this_line.append(_truck.node_list[0])
        this_line.append(_truck.edge_list[0])
        this_truck_time = _truck.start_time
        this_truck_time_string = this_truck_time.strftime("%m/%d/%Y, %H:%M:%S")
        this_line.append(this_truck_time_string)
        data.append(this_line)

    filename = 'start_configuration.csv'

    with open(filename,'w',newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

    print('Initlization: Task Configuration Output!')