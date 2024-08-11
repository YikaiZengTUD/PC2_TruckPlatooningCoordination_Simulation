# -*- coding: utf-8 -*-
import numpy as np
from tqdm import tqdm
from datetime import timedelta,datetime
from data_process.import_data_from_files import import_data_from
from virtual_env.virtual_geo import GeoMap
from virtual_env.virtual_time import GlobalClock
from virtual_env.virtual_handler import VirtualHandler
from carrier.truck import Truck
from carrier.carrier import Carrier
from thridparty.encryptor import Encryptor

import json
import matplotlib.pyplot as plt

''' Parameter Settings'''

step_length_ms                    = 2000  # period for the carrier to perform communications

consensus_table_resolution_second = 10
consensus_table_range_second      = 3600

row_of_consensus        = int(consensus_table_range_second/consensus_table_resolution_second)

debug_flag              = False

com_slots               = 100 

public_key              = 103

# debug settings
slice_history = []
select_index = (0,0)
true_average = 0
''' Instantiations '''

print('Instantiations Process Start')

# Virtual geographical map, contains hubs and edges between hubs
geo_map = GeoMap() 

# Import data from data files

[geo_map.hub_list,travel_path_dict,travel_time_dict,geo_map.edge_list,start_time_dict] = import_data_from(
    filepath            = 'data',
    node_list_file      = 'OD_hubs_new_1000Trucks',
    travel_time_file    = 'OD_hubs_travel_1000Trucks',
    start_time_file     = 'vehicle_arr_dep_hubs0_1000Trucks'
    )

# template for consensus table

consensus_table = np.zeros(shape=(row_of_consensus,len(geo_map.edge_list)))

# Virtual time manager

CLK = GlobalClock(start_time=min(start_time_dict.values()),step_ms=step_length_ms,table_row_sec=consensus_table_resolution_second)
print("Instantiations -> Clock (Assume microsecond = 0):",CLK.current_clk.strftime('%Y-%m-%d %H:%M:%S'))
# This is a list that when we wish to build a smaller (substracted dataset, you use only carrier index from this list)
filtered_carrier_list = [] 

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
    if debug_flag:
        if not T.carrier_index in filtered_carrier_list:
            continue
    T.generate_edge_list(geo_map.edge_list)
    if not T.carrier_index in carrier_index_list:
        carrier_index_list.append(T.carrier_index)
    truck_list.append(T)

print('Instantiations -> Truck amout:',len(truck_list))
# To store all carriers
carrier_list = []

# Build carriers
for _carrier_index in carrier_index_list:
    C = Carrier(_carrier_index,consensus_table,consensus_table_range_second)
    carrier_list.append(C)
# 
for _truck in truck_list:
    _order = carrier_index_list.index(_truck.carrier_index)
    carrier_list[_order].involve_a_truck(_truck)

truck_2_carrier_dict = {}
for _truck in truck_list:
    truck_2_carrier_dict[_truck.truck_index] = _truck.carrier_index

print('Instantiations -> Carrier amout:',len(carrier_list))

for _carrier in carrier_list:
    _carrier.carrier_qty        = len(carrier_index_list)
    _carrier.update_ego_table(CLK.cur_plan_base)
    _carrier.ego_table_record   = _carrier.ego_table
    _carrier.consensus_table    = _carrier.ego_table

print('Load Setup: plan table established')

latest_concerned_clk = max(start_time_dict.values())

for _truck in truck_list:
    if _truck.deadline > latest_concerned_clk:
        latest_concerned_clk = _truck.deadline

print('Latest possible operating time:',latest_concerned_clk)

Simu_Handle = VirtualHandler()

print('Simulation handlder generated')

total_length    = latest_concerned_clk - CLK.current_clk
total_length_ms = total_length.total_seconds() * 1000
total_iterations = int(total_length_ms) // step_length_ms + 1

print('Main process started, progress bar generated')

EP = Encryptor(public_key)
print("Third party encryption service start")

# recorder of time window
depart_info          = {}
depart_info_this_row = {}


for time_ms in tqdm(range(0, int(total_length_ms), step_length_ms)):
    
    '''
    In this branch, we consider an ideal communication process that directly transmit information perfeactly for all carriers
    '''
    
    ego_table_sum = np.zeros(shape=(row_of_consensus,len(geo_map.edge_list)))
    for _carrier in carrier_list:
        _carrier.ego_table = _carrier.load_plan_into_ego_matrix(table_base=CLK.cur_plan_base)
        ego_table_sum += _carrier.ego_table

    for _carrier in carrier_list:
        _carrier.consensus_table = ego_table_sum

    if (time_ms/1000) % consensus_table_resolution_second == 0:

        CLK.cur_plan_base = CLK.current_clk - timedelta(seconds=consensus_table_resolution_second)
        

    # Decision making process

    # we need to check if this a timing of arrival a hub - when decsion is made
    for _carrier in carrier_list:
        for _truck in _carrier.truck_list:
            if _truck.is_finish:
                continue # this truck has already arrived
            if _truck.is_arrival_moment(CLK.current_clk,1e-3*step_length_ms):
                # this is when a truck arrives and needs making decisons
                # generate the dp graph and search weight cheapest trips
                edge_to_decide = _truck.future_edges(CLK.current_clk,step_length_ms)
                decide_options_on_edge = {}
                for _edge in edge_to_decide:
                    time_window = _truck.time_window_on_edge(CLK.current_clk,_edge,step_length_ms)
                    # steps presenting truck <-> carrier communication
                    ego_options = _carrier.answer_samecarrier_options(_edge,time_window,consensus_table_resolution_second,_truck.truck_index)
                    agg_options = _carrier.answer_carrieragg_options(_edge,time_window,CLK.cur_plan_base,consensus_table_resolution_second,_truck.truck_index)
                    # FIX: check if options are the same
                    _time_opt = ego_options[0]
                    for _order,_time in enumerate(_time_opt):
                        if _time in agg_options[0]:
                            _ego_order = _order
                            _agg_order = agg_options[0].index(_time)
                            if ego_options[1][_ego_order] == agg_options[1][_agg_order]:
                                # this is a fully ego platoon, no need to move to the grid point.
                                raw_time = _carrier.reverse_gridtime_2_raw_time(_time,_edge,_truck.truck_index,consensus_table_resolution_second)
                                if raw_time == _time:
                                    continue
                                else:
                                    ego_options[0][_ego_order] = raw_time
                                    agg_options[0][_agg_order] = raw_time

                    combined_options = _truck.validate_options_from_two_sources(ego_options,agg_options,CLK.cur_plan_base,consensus_table_range_second)
                    # truck actions
                    decide_options_on_edge[_edge] = combined_options
                # generate dp graph based on these options
                _truck.dp_graph = _truck.generate_dp_graph(decide_options_on_edge,CLK.current_clk,step_length_ms,consensus_table_resolution_second)
                dp_path         = _truck.find_shortest_path(_truck.dp_graph)
                if len(dp_path) == 0:
                    raise ValueError('Path Error')
                change_flag = _truck.update_waiting_plan(dp_path,edge_to_decide)
                if change_flag:
                    ego_table = _carrier.load_plan_into_ego_matrix(table_base=CLK.cur_plan_base)
                    delta = ego_table - _carrier.ego_table
                    _carrier.ego_table = ego_table
                    _carrier.consensus_table    += delta
                    # _carrier.average_intermedia += delta
    
    for _carrier in carrier_list:
        for _truck in _carrier.truck_list:
            if _truck.is_finish:
                continue # this truck has already arrived
            is_departing, edge_to_depart = _truck.is_departing_moment(CLK.current_clk,1e-3*step_length_ms)
                # which edge this is 
            if is_departing:

                if edge_to_depart not in depart_info_this_row:
                    depart_info_this_row[edge_to_depart] = []
                depart_info_this_row[edge_to_depart].append(_truck.truck_index)
    
    if (time_ms/1000) % consensus_table_resolution_second == 0 and time_ms > 0:
        if len(depart_info_this_row) > 0:
            depart_info[CLK.current_clk - timedelta(seconds=consensus_table_resolution_second)] = depart_info_this_row
        depart_info_this_row = {}
    CLK.clk_tick(step_length_ms)

def serialize_depart_info(depart_info):
    return {k.isoformat() if isinstance(k, datetime) else k: v for k, v in depart_info.items()}
# Save departure information to a JSON file
with open('result/depart_info.json', 'w') as json_file:

    print("Depart info saved to result/depart_info.json")
    json.dump(serialize_depart_info(depart_info), json_file, indent=4)

def save_wait_plans(carrier_list, file_path):
    wait_plans = {}
    for carrier in carrier_list:
        for truck in carrier.truck_list:
            wait_plans[truck.truck_index] = truck.wait_plan

    with open(file_path, 'w') as json_file:
        json.dump(wait_plans, json_file, indent=4)

    print(f"Wait plans saved to {file_path}")

save_wait_plans(carrier_list,'result/wait_plan.json')


# for i in range(len(carrier_list)):
#     plt.plot(slice_history[i], label=f'Agent {i}')

# plt.xlabel('Iteration')
# plt.ylabel('Value')
# plt.title('Changes in Agent Values Over Iterations (First Run)')
# plt.show()