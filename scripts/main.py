# -*- coding: utf-8 -*-

from map import GeoMap

from truck_swarm_parameters import TruckSwarm
 # global action. virtual instance, applied

from truck_parameter import Truck
from carrier_parameter import Carrier

from global_clock_parameter import VirtualGlobalClock

test_with_small_data = True

'''
Data Input
'''
if test_with_small_data:
    # small data segements for test. Comment out and replaced with input file
    task_dict = {
    0: [(16.21247986026327, 59.75805915309397), (16.06903491037792, 60.20902572311321),(16.32098233050319, 56.6727356017633)],
    1: [(18.02546160254861, 59.38157382906624), (16.50658561538482, 58.28150384602444), (16.48374131130608, 57.56893497161655), (16.3883782476514, 56.9467696413148)]
    } # small test data for debugging

    travel_time_dict = {
        0: [[(16.21247986026327, 59.75805915309397), 5409.8719]], 
        1: [[(18.02546160254861, 59.38157382906624), 12703.2895], [(16.50658561538482, 58.28150384602444), 5755.7795], [(16.48374131130608, 57.56893497161655), 4285.0585], [(16.3883782476514, 56.9467696413148), 1894.0153]]
    } # This dict contains the starting node and the travel time duration on the edge, it must to cross-referenced with the Geo map
    
    vehicle_arr_dep_test = {
        0: {(16.21247986026327, 59.75805915309397): {'t_a': ['2021-11-20 09:00:00.0000'], 't_d': ['2021-11-20 09:00:00.0000'], 'label': 'I'}, (16.06903491037792, 60.20902572311321): {'t_a': ['2021-11-20 10:30:09.8719'], 't_d': []}}, 
        1: {(18.02546160254861, 59.38157382906624): {'t_a': ['2021-11-20 08:01:40.0000'], 't_d': ['2021-11-20 08:01:40.0000'], 'label': 'I'}, (16.50658561538482, 58.28150384602444): {'t_a': ['2021-11-20 11:33:23.2895'], 't_d': ['2021-11-20 11:33:23.2895'], 'label': 'I'}, (16.48374131130608, 57.56893497161655): {'t_a': ['2021-11-20 13:09:19.0690'], 't_d': ['2021-11-20 13:09:19.0690'], 'label': 'I'}, (16.3883782476514, 56.9467696413148): {'t_a': ['2021-11-20 14:20:44.1275'], 't_d': ['2021-11-20 14:20:44.1275'], 'label': 'I'}, (16.32098233050319, 56.6727356017633): {'t_a': ['2021-11-20 14:52:18.1428'], 't_d': []}}
    } # From this we need need extract the starting time

    travel_dd_test = {
        0: 540.9872, 1: 2463.8143
    }

else:
    pass 

n_of_truck = len(task_dict)

# Extract Map information from the OD pairs 
M = GeoMap(task_dict)

'''
This class init with the transformation labeling each (x,y) to an index
From the path of trucks, it also extract the concerned edge list of the 
road network

-------------------------------------------------------------------------

In the privacy preserving methods, a truck does not know anything about the 
potential parteners as they may belong to another fleet
'''

# Instantiation of trucks
# collect the travel time on each edge of each truck with truck swarm method
TS = TruckSwarm(n_of_truck,M.task_dict_node)
ts_travel_duration_list = TS.collect_travel_duration(travel_time_dict)
ts_departure_time_list  = TS.extract_departure_time(vehicle_arr_dep_test)
ts_waiting_budget       = travel_dd_test
truck_list = [] # refer each truck with its index as key
for truck_index in range(n_of_truck):
    T = Truck(
        M.task_dict_node[truck_index],
        truck_index,
        ts_departure_time_list[truck_index],
        ts_travel_duration_list[truck_index],
        TS.assign_carrier_index(truck_index),
        ts_waiting_budget[truck_index])
    truck_list.append(T)

print('Initlization: Truck Instantiation finished, Truck Amount: ',n_of_truck)
carrier_list = []
for carrier_index in TS.carrier_index_list:
    C = Carrier(carrier_index,0) # type is not applied for now
    for truck in truck_list:
        if truck.carrier_index == carrier_index:
            C.add_truck_into_this_carrier(truck2add=truck)
    carrier_list.append(C)

print('Initlization: Carrier Instantiation finished, Carrier Amount: ',len(carrier_list))

# ------
CLK = VirtualGlobalClock(start_clk=min(ts_departure_time_list))

# Generate the starting communication graph
# This will be checked by nodes, as a global action

'''
Some assumptions and simplication are made for the starting graph due to the dataset limitation

Trucks will suddenly "appear" on the first hub (as they turn it on and become online). So before that there is nothing, 
Carriers, trucks appear one by one as time goes and will disapear (goes offline) when tasks finished.

'''
TS.init_communication_graph()
# an empty graph has been created




