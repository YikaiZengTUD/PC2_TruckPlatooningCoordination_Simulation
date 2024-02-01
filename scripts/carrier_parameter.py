# -*- coding: utf-8 -*-
from truck_parameter import Truck
import numpy as np
from datetime import datetime, timedelta
import random
import networkx as nx

class Carrier:

    def __init__(
            self,
            carrier_index:int,
            carrier_size_type:int
            ) -> None:
        
        self.truck_index_list   = []
        self.carrier_index      = carrier_index
        self.carrier_size_type  = carrier_size_type # Not in used for now
        self.truck_list         = []

        self.current_slot_com       = 0
        self.is_in_communication    = False
        
        # with all trucks in the list, it should be able to generate the matrix for transmitting
        # self.next_period_plan_matrix = np.array()

        # self.next_period_plan_matrix_memory = self.next_period_plan_matrix

    def add_truck_into_this_carrier(self,truck2add:Truck) -> None:
        self.truck_list.append(truck2add)
        self.truck_index_list.append(truck2add.truck_index)

    def get_my_neighbor_carrier(self,data:dict) -> None:
        for _truck in self.truck_list:
            conn_truck_list = data[_truck.current_node]
            for _truck_index in conn_truck_list:
                if _truck_index == _truck.truck_index:
                    continue
                # how do I know who is there?

    def space_time_plan_table_init(self,node_list:list,future_range:int,time_resolution:int) -> np.array:
        # all unit given in minute
        # it presented if the truck leaves in [left,right)
        # therefore, if we look forward 1 hour, and we need to know the depature trucks per minute
        # future_range = 60, time_resolution = 1

        # record these information
        self.future_range       = future_range
        self.time_resolution    = time_resolution
        # build empty matrix
        n_of_rows = int(future_range/time_resolution)
        n_of_cols = len(node_list)
        return np.zeros((n_of_rows, n_of_cols))
    
    def load_truck_plan_into_table(self,base_line_clk:datetime) -> None:
        for _truck in self.truck_list:
            _this_truck_departure_time = _truck.generate_depature_time_list()
            for _relative_node_order,_d_time in enumerate(_this_truck_departure_time):
                if _d_time < base_line_clk + timedelta(minutes=self.future_range) and _d_time >= base_line_clk:
                    # +1 for the corresponding matrix
                    # determine which row it is gonna be
                    _gap = _d_time - base_line_clk
                    n_of_row = int(_gap.total_seconds()/60)
                    n_of_col = _truck.node_list[_relative_node_order]
                    self.next_period_plan_matrix[n_of_row,n_of_col]
                else:
                    break
    
    def select_communication_slot(self,max_slot:int):
        self.current_slot_com = random.randint(1,max_slot)

    def random_select_one_neighbor(self,commun_graph:nx.graph) -> int:
        # return the carrier index selected, return -1 if not neighbor
        _neighbors = list(commun_graph.neighbors(self.carrier_index))
        if len(_neighbors) == 0:
            return -1
        return random.choice(_neighbors)
    
    def split_plan_table_into_two_part(self,key_prime:int) -> list:
        self.public_prime = key_prime
        matrix_shape = self.next_period_plan_matrix.shape
        A = np.random.randint(0, key_prime, size=matrix_shape, dtype=np.int64)
        B = (self.next_period_plan_matrix - A) % key_prime
        return [A,B]

    def row_rolling_plan_table(self,base_line_clk:datetime) -> None:
        self.next_period_plan_matrix[:-1, :] = self.next_period_plan_matrix[1:, :]
        self.next_period_plan_matrix[-1, :] = 0
        concerned_time_slot_left  = base_line_clk + timedelta(self.future_range - self.time_resolution)
        concerned_time_slot_right = concerned_time_slot_left + timedelta(self.time_resolution)
        for _truck in self.truck_list:
            # ask for the latest departure time information again
            _this_list = _truck.generate_depature_time_list()
            # check the if any departure at this row
            for _this_truck_node_index,_d_time in enumerate(_this_list):
                if _d_time >= concerned_time_slot_left and _d_time < concerned_time_slot_right:
                    # there is a departure in this node
                    self.next_period_plan_matrix[_truck.node_list[_this_truck_node_index],-1] += 1
                    break 
                if _d_time >= concerned_time_slot_right:
                    break

    def update_plan_matrix(self,input1:np.array,input2:np.array) -> None:
        self.next_period_plan_matrix = input1 + input2
    
    def explain_encrypted_matrix(self,input_array:np.array,est_carrier:int) -> np.array:
        return round((input_array * est_carrier) % self.public_prime)

    def sync_future_plan(self,requried_hub:list,arrival_time:datetime,current_clk:datetime,truck_index:int,est_carrier:int) -> list:
        # return a list of dictionary of each future hub, the possible depature time for platooning
        # the truck does not care the peers that leave already before

        # But for trucks from other carriers, the information is limited to the consensus period
        # It also requries the carrier to sync the planning of ther trucks in the list

        # FIXME: Arrival time here means the latest arrival time of this truck

        # first floor this clk to a time resolution
        seconds_since_epoch = (current_clk - datetime(1970, 1, 1)).total_seconds()
        rounded_seconds = int(seconds_since_epoch // self.time_resolution) * self.time_resolution
        current_clk = datetime.utcfromtimestamp(rounded_seconds)

        time_gap = arrival_time - current_clk
        In_range_aggreated = {}
        if time_gap <= self.future_range:
            t_a_row = int(time_gap/self.time_resolution) # counting from 0, this row is the start of interested
            for _hub in requried_hub:
                In_range_aggreated_at_hub   = self.next_period_plan_matrix[t_a_row:, _hub]

                In_range_aggreated[_hub]    = self.explain_encrypted_matrix(In_range_aggreated_at_hub,est_carrier)

        # also give the plan in this carrier
        same_carrier_dict = {}
        for _hub in requried_hub:
            same_carrier_list = []
            for _truck in self.truck_list:
                if _truck.truck_index == truck_index:
                # itself does not include
                    continue
                if _hub in _truck.node_list:
                    # this truck has an overlap hub
                    [t_a,t_d] = _truck.answer_my_plan_at_hub(_hub)
                    if t_a >= arrival_time:
                        # potential platooning same-carrier peer
                        same_carrier_list.append(t_a)
            same_carrier_dict[_hub] = same_carrier_list
        
        return [In_range_aggreated,same_carrier_dict]
                

