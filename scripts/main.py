# -*- coding: utf-8 -*-

from map import GeoMap

from truck_swarm_parameters import TruckSwarm
 # global action. virtual instance, applied

from truck_parameter import Truck
from carrier_parameter import Carrier

from global_clock_parameter import VirtualGlobalClock

from tqdm import tqdm
from datetime import timedelta

# simulation settings

test_with_small_data = False

next_period_duration    = 60 # min -> consensus window, carrier only reach planning average for the xx minutes from this moment
next_period_resolution  = 1  # We assume that the turcks in n minutes, departures at the same time

communication_period    = 100 #ms
communication_slot      = 50

plan_table_row_rolling  = next_period_resolution * 60 * 1000 / communication_period # every * rounds of communication, the table should be updated

# ---
secret_prime = 5009 # With a lot of reduancy

# ==============================

'''
Data Input
'''
if test_with_small_data:
    # small data segements for test. Comment out and replaced with input file
    task_dict = {
    0: [(16.21247986026327, 59.75805915309397), (16.06903491037792, 60.20902572311321)],
    1: [(18.02546160254861, 59.38157382906624), (16.50658561538482, 58.28150384602444), (16.48374131130608, 57.56893497161655), (16.3883782476514, 56.9467696413148),(16.32098233050319, 56.6727356017633)]

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

ts_travel_duration_list = TS.collect_travel_duration(travel_time_dict) #FIXME: This is a dictionary

ts_start_time_list  = TS.extract_departure_time(vehicle_arr_dep_test) #FIXME: Inconsistent in naming

for t_index,_timing in enumerate(ts_start_time_list):
    ts_start_time_list[t_index] = _timing - timedelta(seconds=60)

# So we discuss about the timing here, we give DP search 90s for perform and another 30s for quick communication
# This is to say that 2 mins before a truck arrive a hub, which we may say the truck is within the 300 m range of the hub

# we move the 'starting operation' timing 60s earlier

ts_waiting_budget       = travel_dd_test
ts_max_operating_time   = TS.get_max_simulation_time(ts_start_time_list,ts_travel_duration_list,ts_waiting_budget)


truck_list = [] # refer each truck with its index as key
for truck_index in range(n_of_truck):
    T = Truck(
        M.task_dict_node[truck_index],
        truck_index,
        ts_start_time_list[truck_index],
        ts_travel_duration_list[truck_index],
        TS.assign_carrier_index(truck_index),
        ts_waiting_budget[truck_index])
    T.generate_edge_list(M.edge_list)
    truck_list.append(T)

print('Initlization: Truck Instantiation finished, Truck Amount:',n_of_truck)
carrier_list = []
for carrier_index in TS.carrier_index_list:
    C = Carrier(carrier_index,0) # type is not applied for now
    for truck in truck_list:
        if truck.carrier_index == carrier_index:
            C.add_truck_into_this_carrier(truck2add=truck)
    C.next_period_plan_matrix = C.space_time_plan_table_init(
        node_list=range(0,M.n_of_node),
        future_range=next_period_duration,
        time_resolution=next_period_resolution)
    # create a all zero array to store the planning array
    carrier_list.append(C)

# Though the truck is not yet online, the original plan is supposed be known by the carrier
# TODO: Truck plan -> truck 
#       Carrier -> generate the matrix form


print('Initlization: Carrier Instantiation finished, Carrier Amount:',len(carrier_list))

# ------
CLK = VirtualGlobalClock(start_clk=min(ts_start_time_list)) 

'''
Some assumptions and simplication are made for the starting graph due to the dataset limitation

Trucks will suddenly "appear" on the first hub (as they turn it on and become online). So before that there is nothing, 
Carriers, trucks appear one by one as time goes and will disapear (goes offline) when tasks finished.

'''

TS.init_communication_graph()
# an empty graph has been created

# The carrier will mathmaically convert its trucks' plan into table form
for _carrier in carrier_list:
    _carrier.load_truck_plan_into_table(base_line_clk = CLK.current_clk)
# load current plan into the matrix form 

Total_length = ts_max_operating_time - min(ts_start_time_list)
total_length_ms = Total_length.total_seconds() * 1000

loop_counter = 0

total_iterations = int(total_length_ms) // communication_period + 1
for time_ms in tqdm(range(0, int(total_length_ms), communication_period)):
    
    # main loop start, we consider the step length 100 ms -> 10Hz communicating rate
    
    # The sequence is set on the prespective of a truck

    # -----

    ts_node_trucks = {i: [] for i in range(M.n_of_node)} 
    # This dict contains the truck object in this node (node index)
    # This is reconstructed every clk to catch the dynamic of truck movement with less coding size
    for _this_carier in carrier_list:

        for this_truck in  _this_carier.truck_list:
            
            if CLK.current_clk >= this_truck.start_time:

                # The truck is online, the truck should locate itself, in real world this 
                # is achieved with a global localization service such as GPS

                this_truck.locate_myself_based_on_time_and_plan(CLK.current_clk)
        
                # now we use global method, to see the current communication graph
                        
                # there are two kinds of communication links
                
                # 1. the truck is arriving/parking at the same node -> current node indentical and not -1
                if not this_truck.current_node == -1:
                    ts_node_trucks[this_truck.current_node].append(this_truck) # register the truck to the node
                
                # 2. the truck is in platooning 
                # TODO: carefully design the process of entering/leaving a platoon -> when does the communication edge break?
                
                _in_this_platoon = this_truck.platooning_partener # itself should be excluded

                if not len(_in_this_platoon) == 0:
                    _carrier_index = this_truck.carrier_index
                    for _truck in _in_this_platoon:
                        # if in a platoon, this carrier should already be registered in the previous hub
                        # add in edge
                        if not TS.commun_graph.has_edge( _carrier_index,_truck.carrier_index):
                            TS.commun_graph.add_edge()

    # Now check node by node, to generate the communication graph link -> 1 above 
            
    for _node_index in range(M.n_of_node):

        this_node_trucks_list = ts_node_trucks[_node_index]
        if len(this_node_trucks_list) < 1:
            # no connection in this hub with 0
            continue

        for _truck in this_node_trucks_list:
            
            _carrier_index = _truck.carrier_index

            if not _carrier_index in TS.commun_graph.nodes:
                TS.commun_graph.add_node(_carrier_index)
        
        if len(this_node_trucks_list) == 1:
            continue

        for i in range(len(this_node_trucks_list)):
            for j in range(i+1,len(this_node_trucks_list)):
                if not TS.commun_graph.has_edge(this_node_trucks_list[i].carrier_index,this_node_trucks_list[j].carrier_index):
                    TS.commun_graph.add_edge(this_node_trucks_list[i].carrier_index,this_node_trucks_list[j].carrier_index)
                    # This adge may already formed at other hubs or platoons
    
    # Do we specify which physical trucks to transmit the message?
    # Not used in the main algorithm and not easy to do
    # TODO: Maybe add methods to record the actual physical path of information transmission
                    
    '''
    Assumption: the communication cross carriers happens all time, at certain frequency
    In simulation, we may globally random select a carrier, which is not the most presentative way
    Therefore, we propose a random way for the carrier itself
    
    Based on ref [35], we first consider there is 50 available slots in this 100ms for communication
    The carrier will randomly pick one to start the 'push' action. Basically this is done in a random order 
    
    It may considered that we shift the time of each truck randomly so they are less likely to crash
    
    '''    

    if loop_counter > 0 and loop_counter % plan_table_row_rolling == 0:
        # load a new row into the table -> Throw away the oldest one
        for _carrier in carrier_list:
            if _carrier.carrier_index in list(TS.commun_graph.nodes):
                _carrier.row_rolling_plan_table(CLK.current_clk)

    for _carrier in carrier_list:
        if _carrier.carrier_index in list(TS.commun_graph.nodes):
            _carrier.select_communication_slot(communication_slot)
    
    for com_slot in range(1,communication_slot+1):
        for _carrier in carrier_list:
            if not _carrier.carrier_index in list(TS.commun_graph.nodes):
                continue
            if _carrier.current_slot_com == com_slot:
                # randomly select one of the neighbors
                _select_negibors = _carrier.random_select_one_neighbor(TS.commun_graph)
                if _select_negibors == -1:
                    continue # no connecting neighbors
            
                if carrier_list[_select_negibors].current_slot_com == com_slot:
                    continue # failed to make connection since the selected neighbor is busy

                    #TODO: Maybe find an alternative connecting neighbor

                # A neigbor is selected to communicate
                # 1. addictive secret sharing
                [A1,B1] = _carrier.split_plan_table_into_two_part(secret_prime)
                [A2,B2] = carrier_list[_select_negibors].split_plan_table_into_two_part(secret_prime)
                _carrier.update_plan_matrix(A1,A2)
                carrier_list[_select_negibors].update_plan_matrix(B1,B2)
                # now the data, even the most recent one, is blurred
                # 2. gossip-based averaging
                _avg_table = (_carrier.next_period_plan_matrix + carrier_list[_select_negibors] .next_period_plan_matrix)/2
                _carrier.next_period_plan_matrix = _avg_table
                carrier_list[_select_negibors] .next_period_plan_matrix = _avg_table
        
    #  check now if a truck arriving the hub
    for _carrier in carrier_list:
        for _truck in _carrier.truck_list:
            # check the arrival time
            is_a_arriving_clk = _truck.is_now_the_arrving_clk(CLK.current_clk,communication_period)[0]
            if is_a_arriving_clk:
                # This is the moment that is 60s towards before the physical hub
                # The optimization process for the hub is triggered
                future_plan = _carrier.sync_future_plan(
                    requried_hub = _truck.generate_future_hubs(),
                    arrival_time = _truck.deadline,
                    current_clk  = CLK.current_clk,
                    truck_index  = _truck.truck_index,
                    est_carrier  = len(TS.commun_graph.nodes)
                    ) # truck -> carrier manager, get latest estimation on truck distribuitions
                

                
            


    # TODO: loop_counter += 1


        




