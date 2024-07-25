# This is the result chekcing script for the final result

# Target 1: actual costs spent comparing with or without the method involved

from virtual_env.virtual_geo import GeoMap
from data_process.import_data_from_files import import_data_from
from carrier.truck import Truck
from carrier.carrier import Carrier


import json
import os
import csv

import matplotlib.pyplot as plt
import numpy as np

# Virtual geographical map, contains hubs and edges between hubs
geo_map = GeoMap() 

from datetime import datetime, timedelta



[geo_map.hub_list,travel_path_dict,travel_time_dict,geo_map.edge_list,start_time_dict] = import_data_from(
    filepath            = 'data',
    node_list_file      = 'OD_hubs_new_1000Trucks',
    travel_time_file    = 'OD_hubs_travel_1000Trucks',
    start_time_file     = 'vehicle_arr_dep_hubs0_1000Trucks'
    )


# To store all truck instantiations
truck_list = []

# To store all carrier index from truck instantiations

carrier_index_list = []


for _truck_index in travel_path_dict.keys():
    T = Truck(
        truck_index         = _truck_index,
        task_by_hub_index   = travel_path_dict[_truck_index],
        travel_time_list    = travel_time_dict[_truck_index],
        start_time          = start_time_dict[_truck_index]
    )

    T.get_carrier_number_fixed('start_configuration.csv')

    T.generate_edge_list(geo_map.edge_list)
    if not T.carrier_index in carrier_index_list:
        carrier_index_list.append(T.carrier_index)
    truck_list.append(T)

carrier_list = []

# Build carriers
for _carrier_index in carrier_index_list:
    C = Carrier(_carrier_index,None,None)
    carrier_list.append(C)
# 
for _truck in truck_list:
    _order = carrier_index_list.index(_truck.carrier_index)
    carrier_list[_order].involve_a_truck(_truck)

truck_2_carrier_dict = {}
for _truck in truck_list:
    truck_2_carrier_dict[_truck.truck_index] = _truck.carrier_index

print('generation process finished')

# we first caculate the cost of all trucks, without the efforts, or even without platooning

cost_no_reduction = {}

for _truck in truck_list:

    cost_no_reduction[_truck.truck_index] = 0

    total_time = sum(_truck.travel_time)

    cost_no_reduction[_truck.truck_index] = (_truck.t_cost + _truck.t_travel) * total_time

print('caculated baseline: no platooning')

# now cacualte the opportunstic platooning result

depart_info = {}

for _truck in truck_list:

    depart_time_list = _truck.generate_depart_time_list()

    for edge_order,depart_time in enumerate(depart_time_list):
        if edge_order >= len(_truck.edge_list):
            continue

        if depart_time in depart_info.keys():
            
            if _truck.edge_list[edge_order] in depart_info[depart_time]:

                depart_info[depart_time][_truck.edge_list[edge_order]].append(_truck.truck_index)

            else:
                depart_info[depart_time][_truck.edge_list[edge_order]] = [_truck.truck_index]

        else:

            depart_info[depart_time] = {_truck.edge_list[edge_order]:[_truck.truck_index]}
        
print('original depart info generated')

cost_oppo = cost_no_reduction.copy()

def caculate_platoon_savings_each(travel_time:float,num_of_trucks:int) -> float:

    t_travel_weight = 56/3600  # euro/seconds
    xi = 0.1

    return t_travel_weight * xi * travel_time


for depart_info_this_time in depart_info.values():

    for edge_index,edge_trucks in depart_info_this_time.items():
        if len(edge_trucks) > 1:
            # there is a platooning
            num_of_trucks = len(edge_trucks)

            for truck_index in edge_trucks:
                this_truck      = truck_list[truck_index]
                this_edge_order = this_truck.edge_list.index(edge_index)

                this_travel_time = this_truck.travel_time[this_edge_order]

                platoon_reward = caculate_platoon_savings_each(this_travel_time,num_of_trucks)

                cost_oppo[truck_index] -= platoon_reward

                # print(f"Truck {truck_index} departs from edge {edge_index} saves {platoon_reward} in platooning {edge_trucks}")

# load test result

def load_json_data(filepath):
    """ Load the JSON data from the specified filepath """
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

results_dir = 'result'
wait_plan_file = 'wait_plan.json'
depart_info_file = 'depart_info.json'

wait_plan_path = os.path.join(results_dir, wait_plan_file)
depart_info_path = os.path.join(results_dir, depart_info_file)

wait_plan_data = load_json_data(wait_plan_path)
depart_info_data = load_json_data(depart_info_path)

print('load optimizaed data from the proposed methods')
cost_opti = cost_no_reduction.copy()
for depart_time,depart_this_clk in depart_info_data.items():

    for edge_index,edge_trucks in depart_this_clk.items():

        if len(edge_trucks) > 1:
            num_of_trucks = len(edge_trucks)

            for truck_index in edge_trucks:
                this_truck      = truck_list[truck_index]
                this_edge_order = this_truck.edge_list.index(int(edge_index))
                this_travel_time = this_truck.travel_time[this_edge_order]
                platoon_reward = caculate_platoon_savings_each(this_travel_time,num_of_trucks)
                cost_opti[truck_index] -= platoon_reward



for truck_index,wait_time in wait_plan_data.items():
    t_cost = 25/3600
    if sum(wait_time) > 0:
        t_wait = sum(wait_time)
        extra_cost = t_cost * t_wait

        cost_opti[int(truck_index)] += extra_cost

'''Figure 1'''

# # Define number of trucks per subplot
# trucks_per_subplot = 100

# # Get sorted list of truck keys
# trucks = sorted(cost_no_reduction.keys())

# # Calculate the number of subplots needed
# num_subplots = len(trucks) // trucks_per_subplot + (1 if len(trucks) % trucks_per_subplot > 0 else 0)

# # Setup the figure and subplots
# fig, axes = plt.subplots(num_subplots, 1, figsize=(10, 5 * num_subplots))

# # Iterate over the number of subplots
# for i in range(num_subplots):
#     ax = axes[i] if num_subplots > 1 else axes
#     start = i * trucks_per_subplot
#     end = start + trucks_per_subplot
#     current_trucks = trucks[start:end]

#     # Extract data for current set of trucks
#     no_reduction_costs = [cost_no_reduction[truck] for truck in current_trucks]
#     oppo_costs = [cost_oppo[truck] for truck in current_trucks]
#     opti_costs = [cost_opti[truck] for truck in current_trucks]

#     # Create indices for the current subplot
#     index = np.arange(len(current_trucks))
#     bar_width = 0.25
#     opacity = 0.8

#     # Plot each bar chart
#     ax.bar(index, no_reduction_costs, bar_width, alpha=opacity, color='b', label='No Reduction')
#     ax.bar(index + bar_width, oppo_costs, bar_width, alpha=opacity, color='g', label='Opportunistic')
#     ax.bar(index + 2 * bar_width, opti_costs, bar_width, alpha=opacity, color='r', label='Optimized')

#     ax.set_xlabel('Truck')
#     ax.set_ylabel('Costs')
#     # ax.set_title(f'Costs by Truck and Strategy for Trucks {start+1} to {end}')
    
#     # Adjust font size here and manage label density
#     ax.set_xticks(index + bar_width)
#     ax.set_xticklabels(current_trucks, rotation=90, fontsize=8)  # Smaller font size
#     # Optionally skip some labels if still too crowded
#     for label in ax.get_xticklabels()[::2]:
#         label.set_visible(False)

#     # ax.legend()

# plt.tight_layout()
# plt.show()

# Create the directory if it does not exist
directory = 'plot_result'
os.makedirs(directory, exist_ok=True)

# File paths
file_paths = {
    'cost_no_reduction.json': cost_no_reduction,
    'cost_oppo.json': cost_oppo,
    'cost_opti.json': cost_opti
}

# Write each dictionary to a separate file in the directory
for file_name, data in file_paths.items():
    full_path = os.path.join(directory, file_name)
    with open(full_path, 'w') as file:
        json.dump(data, file, indent=4)

print(f"All files have been saved in the '{directory}' directory.")