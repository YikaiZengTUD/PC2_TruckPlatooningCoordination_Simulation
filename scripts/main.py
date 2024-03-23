# -*- coding: utf-8 -*-

# import self-defined classes in truck platooning problem
from map import GeoMap
from global_handler import global_handler
from truck_methods import Truck
from carrier_methods import Carrier
from global_clock import VirtualGlobalClock
from encryption_methods import Encrpytion_Platfrom

from datetime import timedelta
from tqdm import tqdm
import networkx as nx
# simulation settings
# test_with_small_data = False

# planning matirx size defined
planning_horizon    = 60 # minutes -> consensus window, carrier only reach planning average for the xx minutes from this moment
planning_resolution = 1  # We assume that the turcks in n minutes, departures at the same time

# frequency of start a average process with neighbor for a carrier
communication_period = 100 # ms -> this is also the step length of simulation
communication_slots  = 50  # there are xx slots in this communication phases

steps_rolling_horizon_forward = planning_resolution * 60 * 1000 / communication_period
## every these steps that the table is rolling (one more row added and first row removed)

# addictive secret sharing public key
public_key = 1009

# ==============================

'''
Data Input
'''
# load from dict style files
# contents are quite reduant since these are intermedia results from previous studies
f=open('data\OD_hubs_new_1000Trucks','r')
a=f.read()
task_dict=eval(a) # hubs between the origin and destination
f.close()
# ----
f=open('data\OD_hubs_travel_1000Trucks','r')
a=f.read()
travel_time_dict=eval(a) # travel times of different trucks on road segments
f.close()
# ----
f=open('data\\vehicle_arr_dep_hubs0_1000Trucks','r') # the initial departure times from the origins 
a=f.read()
vehicle_arr_dep_test=eval(a)
f.close()
# ---
f=open('data\\travel_dd_1000Trucks','r')
a=f.read()
travel_dd_test=eval(a) # a dict, which includes the allowed total waiting time (seconds) of each truck in the whole trip
f.close()

n_of_truck = len(task_dict)

# Extract Map information from the OD pairs 
M = GeoMap(task_dict)
## Only paths recored in the task_dict is built in this map

Simu_Setter     = global_handler(n_of_truck,task_dict)

# collect the travel time on each geographical edge
travel_duration     = Simu_Setter.collect_travel_duration(travel_time_dict)
# extract the when the truck depart from its first hub (by default, on waitting at hub)
first_dep_time      = Simu_Setter.extract_departure_time(vehicle_arr_dep_test)

truck_online_time   = []
for _dep_time in first_dep_time:
    truck_online_time.append(_dep_time - timedelta(seconds=60))
# the truck is considered 'existed' in the map, one minute before the first dep time
    
truck_waiting_budget = travel_dd_test

max_operating_time = Simu_Setter.get_max_simulation_time(
    first_dep_time,
    travel_duration,
    truck_waiting_budget,
    planning_resolution
    )
# from this we decide how many steps the simulation takes

truck_list = [] # refer each truck with its index as key
# truck_index_list = []
for truck_index in range(n_of_truck):
    T = Truck(
        M.task_dict_node[truck_index],
        truck_index,
        truck_online_time[truck_index],
        travel_duration[truck_index],
        Simu_Setter.assign_carrier_index(truck_index,False),
        truck_waiting_budget[truck_index])
    T.generate_edge_list(M.edge_list)
    truck_list.append(T)
    # truck_index_list.append(truck_index)

# record this set up
# convert_setup_to_csv(truck_list)

print('Initialization: Truck Instantiation finished, Truck Amount:',n_of_truck)

carrier_list = []
for carrier_index in Simu_Setter.carrier_index_list:
    C = Carrier(carrier_index,0,public_key) # type is not applied for now
    for _truck in truck_list:
        if _truck.carrier_index == carrier_index:
            C.add_truck_into_this_carrier(truck2add=_truck)
    C.next_period_plan_matrix = C.space_time_plan_table_init(
        edge_list=range(0,M.n_of_edge),
        future_range=planning_horizon,
        time_resolution=planning_resolution)
    # create a all zero array to store the planning array
    carrier_list.append(C)

print('Initialization: Carrier Instantiation finished, Carrier Amount:',len(carrier_list))

start_clk = min(truck_online_time)
start_clk = start_clk.replace(second=0, microsecond=0) # round to the closet int MINUTES

# global clock
CLK = VirtualGlobalClock(start_clk) 
cur_table_base = CLK.current_clk
'''
Some assumptions and simplication are made for the starting graph due to the dataset limitation

Trucks will suddenly "appear" on the first hub (as they turn it on and become online). So before that there is nothing, 
Carriers, trucks appear one by one as time goes and will disapear (goes offline) when tasks finished.

'''
# now init a third-party encryption center that serves the encyption

EP = Encrpytion_Platfrom(key=public_key)

# for _carrier in carrier_list:
#     _carrier.load_truck_plan_into_table(base_line_clk = CLK.current_clk)

# set up for progress bar
Total_length    = max_operating_time - min(truck_online_time)
total_length_ms = Total_length.total_seconds() * 1000
loop_counter = 0

total_iterations = int(total_length_ms) // communication_period + 1

for time_ms in tqdm(range(0, int(total_length_ms), communication_period)):
    
    # main loop start, we consider the step length 100 ms -> 10Hz communicating rate
    
    # The sequence is set on the prespective of a truck

    # -----
    trucks_in_this_node = {i: [] for i in range(M.n_of_node)} 
    # In this setup, a carrier would first check neighboring carriers
    
    for _carrier in carrier_list:
        _carrier.neighoring_carrier_index = [] 
        # reconstruct the list everytime
        for _truck in _carrier.truck_list:
            if CLK.current_clk >= _truck.start_time:
                # The truck is online, the truck should locate itself, in real world this 
                # is achieved with a global localization service such as GPS.
                _truck.locate_myself_based_on_time_and_plan(CLK.current_clk)

                # 1. the truck is arriving/parking at the same node -> current node indentical and not -1
                if not _truck.current_node == -1:
                    trucks_in_this_node[_truck.current_node].append(_truck) 
                    # register the truck to the node, and we assign this after the loop

                # 2. the truck is in platooning 
                _in_this_platoon = _truck.platooning_partener # itself should be excluded
                if not len(_in_this_platoon) == 0:
                    # _carrier_index = _truck.carrier_index
                    for _truck_index_in_platoon in _in_this_platoon:
                        partener_carrier_index = Simu_Setter.truck_2_carrier[_truck_index_in_platoon]
                        if partener_carrier_index != _truck.carrier_index:
                            if not partener_carrier_index in _carrier.neighoring_carrier_index:
                                _carrier.neighoring_carrier_index.append(partener_carrier_index)


    # Now check node by node, to generate add neighbor to the list
    for _node_index in range(M.n_of_node):
        this_node_trucks_list = trucks_in_this_node[_node_index]

        if len(this_node_trucks_list) < 1:
            # no connection in this hub with 0
            continue
    
        for _truck in this_node_trucks_list:
            for _another_truck in this_node_trucks_list:
                if not _truck.carrier_index == _another_truck.carrier_index:
                    # we may add this to each other
                    _index_1 = Simu_Setter.carrier_index_list.index(_truck.carrier_index)
                    _index_2 = Simu_Setter.carrier_index_list.index(_another_truck.carrier_index)

                    if not _another_truck.carrier_index in carrier_list[_index_1].neighoring_carrier_index:
                        carrier_list[_index_1].neighoring_carrier_index.append(_another_truck.carrier_index)
                    
                    if not _truck.carrier_index in carrier_list[_index_2].neighoring_carrier_index:
                        carrier_list[_index_2].neighoring_carrier_index.append(_truck.carrier_index)
    '''
                Assumption: Now the carrier will send its neighboring information the EP, the EP is to deciede who will 
                be doing secrective averaging
    
                '''

    if loop_counter >= 0 and loop_counter % (planning_resolution * 60 * 1000/communication_period) == 0:
        cur_table_base = CLK.current_clk
        EP.init_communication_graph()
        for _carrier in carrier_list:
            _carrier.load_truck_plan_into_table(base_line_clk = cur_table_base) 
            # this load will overwrite the result in the last gap, which we allow this repeat so a new carrier may join
            # current setup : the dynamic averaging happens in this 60s window, during which, the change in the planning remain
            # less affective to the convergence 
            if len(_carrier.neighoring_carrier_index) > 0:
                # there are some neighbor
                EP.process_carrier_neighbor_list(_carrier.neighoring_carrier_index)
                # The EP is about to first build a (very likely not connected graph)
        EP.encryption_platform_prepare()
        # in this process, the platform knows which carrier is okay to provide service
        # Now the encryption platform must find sub groups that is internally connected 
        # and have at least three members
        
        for _carrier in carrier_list:
            # _carrier.carrier_qty_est = 1 # reset
            # _carrier.row_rolling_plan_table(CLK.current_clk)
            _carrier.enc_service_flag = True
            # call this service every rolling-in all new data timing
                # but if not qualified, nothing happens
            if EP.answer_if_qualified(_carrier.carrier_index) and _carrier.enc_service_flag:
                # the carrier is qualified
                [A,_carrier.secret_part_kept] = _carrier.split_plan_table_into_two_part()
                # carrier -> EP: send secretive parts to the platform
                EP.recieve_carrier_data(_carrier.carrier_index,A)
        EP.redistribute_secret_parts() # EP -> carriers: send back data if qualified
    else:
        for _carrier in carrier_list:
            _carrier.enc_service_flag = False

    loop_counter += 1
    # com attempts made every loop
    for _carrier in carrier_list:
        if EP.answer_if_qualified(_carrier.carrier_index) and _carrier.enc_service_flag:
            _carrier.encrypted_data = EP.answer_distribute_values(_carrier.carrier_index) + _carrier.secret_part_kept
            _carrier.enc_data_table_base = cur_table_base
        
    # The third party service has been finished, we do it once every minute
    # if qualified, then a carrier may randomly chose a neighbor to contact
    for _carrier in carrier_list:
        if not EP.answer_if_qualified(_carrier.carrier_index):
            continue # not qualified, no information exchanged
        if len(_carrier.neighoring_carrier_index) == 0:
            continue # topology broken but not yet updated to the EP

        _selected_neighbor_index = _carrier.select_a_random_neighbor()

        # what may gose wrong now is that, at this point, a new neighbor, who has not been through EP may 
        # already be a new neighbor -> 
        if not EP.check_if_enc_communiation_between_two_carriers(_carrier.carrier_index,_selected_neighbor_index):
            continue # fail to find a qualified at this trial, may not have one at all, thus abort, no retry

        _neighbor = carrier_list[Simu_Setter.carrier_index_list.index(_selected_neighbor_index)]
        _avg_data = (_carrier.encrypted_data + _neighbor.encrypted_data)/2
        _carrier.encrypted_data     = _avg_data
        _neighbor.encrypted_data    = _avg_data
        carrier_list[Simu_Setter.carrier_index_list.index(_selected_neighbor_index)] = _neighbor
        _carrier.get_current_carrier_number(EP.answer_subgraph_number(_carrier.carrier_index))
    
    actual_on_edge_trucks_this_clk = {} # this variable records the depart data of this timing
    # this is used to register actually on edge trucks that we update (platoonig_partener) of every truck
    # this is done by simulation setter, as in the real world, the truck depature within the same time will be treated as a platoon
    #  check now if a truck arriving the hub
    for _carrier in carrier_list:
        _carrier.decode_agg_truck_table(cur_table_base) # for those who are not connected, this will just pass through
        for _truck in _carrier.truck_list:
            is_a_arriving_clk = _truck.is_now_the_arrving_clk(CLK.current_clk,communication_period)[0]
            if is_a_arriving_clk:
            # This is the moment that is 60s towards before the physical hub
            # The optimization process for the hub is triggered
                _truck.platooning_partener = []  # when at hub, the platoonig ends virtually
                _truck.dp_graph = nx.DiGraph()      
                _truck.dp_graph.add_node(
                    0,
                    left_time=CLK.current_clk,
                    right_time=CLK.current_clk + timedelta(seconds=60),
                    hub=-1,edge=-1) # A virtual search start point
                dp_node_id = 1
                left_hub_options    = [0]
                right_hub_options   = []
                t_earliest = CLK.current_clk + timedelta(seconds=60)
                # t_next     = Simu_Setter.next_int_row_clk(t_earliest,cur_table_base,planning_resolution)
                for _edge in _truck.generate_future_edges():
                    _hub = _truck.node_list[_truck.edge_list.index(_edge)]
                    # it must exist by defination and above filtered
                    [window_e,window_l] = _truck.answer_time_window_for_edge(_edge,CLK.current_clk)
                    # this gives us the time window of when the truck may departure
                    options_raw = _carrier.answer_known_departure_list_for_this_edge(_edge,window_e,window_l,cur_table_base)
                    # These data include the truck itself, now we have to exclude it so that a fair comparsion is made
                    # we also sort the timing list in the following function

                    [depart_time_list,agg_qty,ego_qty] = _truck.exclude_this_truck_for_this_edge_plan(options_raw,_edge)
                    # build dp graph from this result edge by edge
                    # this hub is one of concerned -> It must get contained in the agg data and ego data
                    this_edge_duration = timedelta(seconds=_truck.travel_duration[_truck.edge_list.index(_edge)])
                    if not t_earliest in depart_time_list:
                        # the non-waitting is of course a possible choice that should be added here
                        _truck.dp_graph.add_node(dp_node_id,left_time=t_earliest,right_time=t_earliest+this_edge_duration,edge=_edge,hub=_hub)
                        right_hub_options.append(dp_node_id)
                        dp_node_id += 1
                    else:
                        # if not t_next in depart_time_list:
                        #     _truck.dp_graph.add_node(dp_node_id,left_time=t_next,right_time=t_next+this_edge_duration,edge=_edge,hub=_hub)
                        #     right_hub_options.append(dp_node_id)
                        #     dp_node_id += 1
                            # this is the option that a truck shall wait to the integer point travel
                        for depart_time in depart_time_list:
                            _truck.dp_graph.add_node(dp_node_id,left_time=depart_time,right_time=depart_time+this_edge_duration,edge=_edge,hub=_hub)
                            right_hub_options.append(dp_node_id)
                            # for the next hub, it may see incoming options in this list
                            dp_node_id += 1

                    for dp_node_left in left_hub_options:
                        for _index,dp_node_right in enumerate(right_hub_options):
                            if _truck.dp_graph.nodes[dp_node_left]['right_time'] <= _truck.dp_graph.nodes[dp_node_right]['left_time']:
                                wait_time_delta = _truck.dp_graph.nodes[dp_node_right]['left_time'] - _truck.dp_graph.nodes[dp_node_left]['right_time']
                                wait_seconds    = wait_time_delta.total_seconds()
                                if wait_seconds != 0:
                                    # this is not a non-stop option
                                    wait_seconds += planning_resolution * 60 # because the Discretization, we do not want underestimate the waiting cost
                                edge_weight     = _truck.caculate_dp_edge_weight(_edge,agg_qty[_index],ego_qty[_index],wait_seconds)
                                _truck.dp_graph.add_edge(dp_node_left,dp_node_right,weight=edge_weight,wait_time=wait_seconds)                                

                    # move to next edge
                    t_earliest          += this_edge_duration
                    left_hub_options    = right_hub_options
                    right_hub_options   = []
                    # now we put a virtual destination 
                _truck.dp_graph.add_node(dp_node_id)
                for dp_node in left_hub_options:
                    _truck.dp_graph.add_edge(dp_node,dp_node_id,weight=0,wait_time=0) # no cost after arrive destination
                    # this is to say, once the waiting time at the second last hub is determined, no more decisons
                    
                # the truck will update its planning based on such dp graph
                path_raw = _truck.optimize_plan(dp_node_id)
                _truck.update_waiting_plan(path_raw)
                # this will affect the carrier's planning

            [is_a_depart_clk,depart_edge] = _truck.is_now_the_departing_clk(CLK.current_clk,communication_period)
            if is_a_depart_clk:
                # this is the timing of this truck to depart current hub
                # register this to a global check list, that we know true platooning
                if not depart_edge in actual_on_edge_trucks_this_clk.keys():
                    actual_on_edge_trucks_this_clk[depart_edge] = []
                _truck.use_waiting_budget() # cut down waiting budget

                actual_on_edge_trucks_this_clk[depart_edge].append(_truck.truck_index)
            # _truck.platooning_partener = [] 
        # now the carrier shall prepare the new enc data for next communication
        if is_a_arriving_clk:
            _carrier.update_encryption_data(cur_table_base) # if there is 

    # check through all adge
    for _edge_index in actual_on_edge_trucks_this_clk.keys():
        if len(actual_on_edge_trucks_this_clk[_edge_index]) >= 2:
            for _truck_index in actual_on_edge_trucks_this_clk[_edge_index]:
                _carrier_index      = truck_list[_truck_index].carrier_index
                _carrier_order      = Simu_Setter.carrier_index_list.index(_carrier_index)
                _in_truck_order     = carrier_list[_carrier_order].truck_index_list.index(_truck_index)
                _list_to_add        = actual_on_edge_trucks_this_clk[_edge_index].copy()
                _list_to_add.pop(_list_to_add.index(_truck_index))
                # _list = carrier_list[_carrier_order].truck_list[_in_truck_order].platooning_partener
                # _list = _list + _list_to_add
                carrier_list[_carrier_order].truck_list[_in_truck_order].platooning_partener += _list_to_add
    Simu_Setter.register_this_on_edge_timing(actual_on_edge_trucks_this_clk,CLK.current_clk)
    # This part is for the simulation handler to record result
    for _carrier in carrier_list:
        for _truck in _carrier.truck_list:
            [is_a_depart_clk,depart_edge] = _truck.is_now_the_departing_clk(CLK.current_clk,communication_period)
            if is_a_depart_clk:
                Simu_Setter.register_this_traveledge_cost(_truck)

    CLK.clock_step_plus_ms(communication_period) # move to the next time

Simu_Setter.save_fuel_cost_result()
Simu_Setter.save_on_edge_result()