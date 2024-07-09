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

''' Parameter Settings'''

step_length_ms                    = 1000  # period for the carrier to perform communications

consensus_table_resolution_second = 10
consensus_table_range_second      = 3600

row_of_consensus        = int(consensus_table_range_second/consensus_table_resolution_second)

debug_flag              = False

com_slots               = 50 

public_key              = 103

''' Instantiations '''

print('Instantiations Process Start')

# Virtual geographical map, contains hubs and edges between hubs
geo_map = GeoMap() 

# Import data from data files

[geo_map.hub_list,travel_path_dict,travel_time_dict,geo_map.edge_list,start_time_dict] = import_data_from(
    filepath            = 'testdata',
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
    Assumption 1: that all carriers are online all time, as a service user and a contributor
    Assumption 2: there is a service provider that provide a fully connected network
    Assumption 3: each communication period, each carrier is able to perform an attempt of communication
    Assumption 4: the period is divided into serval slots, and a carrier which chose a random slot to communicate, if the targeted carrier happens to be in communication as well, 
    this attempt is aborted
    Assumption 5: the amount of carriers are known to all as a common prior knowledge
    '''

    # Prepare phase

    # if this is a clock that a new row of the consensus table is to be updated

    # it is not necessary for time_ms = 0 since the plan has just been loaded

    if (time_ms/1000) % consensus_table_resolution_second == 0:

        if time_ms == 0:
            # this is the starting point, a full scale encrpytion is needed
            for _carrier in carrier_list:
                _carrier.divide_secrets_into_two_parts(public_key)
                EP.record_secret_part(_carrier.secret_part1,_carrier.carrier_index)
            
            EP.process_secret_parts()

            for _carrier in carrier_list:
                _carrier.get_secrets_pieces(EP.return_carrier_parts(carrier_index=_carrier.carrier_index))
                
        else:
            if len(depart_info_this_row) > 0:
                depart_info[CLK.cur_plan_base] = depart_info_this_row
            depart_info_this_row = {}
            CLK.cur_plan_base = CLK.current_clk - timedelta(seconds=consensus_table_resolution_second)
            # only the latest row requires updating
            EP.clear_secret_cache()
            for _carrier in carrier_list:
                _carrier.update_ego_table(CLK.cur_plan_base)
                # the update is also required for the self.consensus table
                _carrier.update_consensus_table()
                _carrier.process_update_row(public_key)
                EP.record_secret_part(_carrier.row_part1,_carrier.carrier_index)
            EP.process_secret_parts()
            for _carrier in carrier_list:
                _carrier.latest_row = _carrier.row_part2 + EP.return_carrier_parts(_carrier.carrier_index)
                _carrier.update_average_intermedia()

            # record depart information
                
    # Information exchange phase

    # each carrier get a communication slot 
    # this is to reduce the conflicts in communication
    comun_schedule_by_carrier = {}

    for _carrier in carrier_list:
        _carrier.select_a_com_slot(com_slots)
        _carrier.in_commun = False
    
        comun_schedule_by_carrier[_carrier.carrier_index] = _carrier.com_slot

    inverse_comun_schedule = {}
    for carrier_index, com_slot in comun_schedule_by_carrier.items():
        if com_slot not in inverse_comun_schedule:
            inverse_comun_schedule[com_slot] = []
        inverse_comun_schedule[com_slot].append(carrier_index)
    
    for com_slot, this_slot_carrier_list in inverse_comun_schedule.items():
        concerned_carrier_list = []
        concerned_carrier_list = this_slot_carrier_list.copy()

        for _carrier_index in this_slot_carrier_list:
            _carrier = carrier_list[carrier_index_list.index(_carrier_index)]
            _carrier.in_commun  = True
            _com_target_index   = _carrier.select_a_random_carrier(carrier_index_list)
            _tar_carrier = carrier_list[carrier_index_list.index(_com_target_index)]

            if _tar_carrier.carrier_index in this_slot_carrier_list:
                _carrier.in_commun = False
                continue
                # this carrier abort this trial because the selected carrier is also in communication 
            
            if _tar_carrier.in_commun:
                _carrier.in_commun = False
                continue

            _tar_carrier.in_commun = True

            concerned_carrier_list.append(_tar_carrier.carrier_index)

            avg = (_tar_carrier.average_intermedia + _carrier.average_intermedia)/2
            _tar_carrier.average_intermedia = avg.copy()
            _carrier.average_intermedia = avg.copy()

        for _carrier_index in concerned_carrier_list:
            _carrier = carrier_list[carrier_index_list.index(_carrier_index)]
            _carrier.in_commun = False

    # a carrier will be making decision with based on self.consensus_table, 
    # therefore, they would hold a latest reliable table for making decison since the consensus may still remain unreliable
    for _carrier in carrier_list:
        _carrier.check_validate_intermedia(public_key)
    # NOTE: Too slow, make it event trigger (?)
    
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
                    combined_options = _truck.validate_options_from_two_sources(ego_options,agg_options,CLK.cur_plan_base,consensus_table_range_second)
                    # truck actions
                    decide_options_on_edge[_edge] = combined_options
                # generate dp graph based on these options
                _truck.dp_graph = _truck.generate_dp_graph(decide_options_on_edge,CLK.current_clk,step_length_ms)
                dp_path         = _truck.find_shortest_path(_truck.dp_graph)
                if len(dp_path) == 0:
                    raise ValueError('Path Error')
                change_flag = _truck.update_waiting_plan(dp_path,edge_to_decide)
                if change_flag:
                    ego_table = _carrier.load_plan_into_ego_matrix(table_base=CLK.cur_plan_base)
                    delta = ego_table - _carrier.ego_table
                    _carrier.ego_table = ego_table
                    _carrier.consensus_table    += delta
                    _carrier.average_intermedia += delta
    
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