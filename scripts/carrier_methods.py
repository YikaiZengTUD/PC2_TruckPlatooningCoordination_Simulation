# -*- coding: utf-8 -*-
from truck_methods import Truck
import numpy as np
from datetime import datetime, timedelta
import random
import networkx as nx
import math
class Carrier:

    def __init__(
            self,
            carrier_index:int,
            carrier_size_type:int,
            public_prime:int
            ) -> None:
        
        self.truck_index_list   = []
        self.carrier_index      = carrier_index
        self.carrier_size_type  = carrier_size_type # Not in used for now
        self.truck_list         = []

        self.current_slot_com       = 0
        self.is_in_communication    = False
        self.public_prime           = public_prime
        self.carrier_qty_est        = 1

        self.enc_data_table_base = datetime(year=1990,month=1,day=1)

        self.neighoring_carrier_index = []
        # self.encrypted_data
        # self.secret_part_kept       = np.array()

        # with all trucks in the list, it should be able to generate the matrix for transmitting
        # self.next_period_plan_matrix = np.array()

        # self.next_period_plan_matrix_memory = self.next_period_plan_matrix

        self.enc_service_flag = False

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

    def space_time_plan_table_init(self,edge_list:list,future_range:int,time_resolution:int) -> np.array:
        # all unit given in minute
        # it presented if the truck leaves in [left,right)
        # therefore, if we look forward 1 hour, and we need to know the depature trucks per minute
        # future_range = 60, time_resolution = 1

        # record these information
        self.future_range       = future_range
        self.time_resolution    = time_resolution
        # build empty matrix
        n_of_rows = int(future_range/time_resolution)
        n_of_cols = len(edge_list)
        return np.zeros((n_of_rows, n_of_cols))
    
    def load_truck_plan_into_table(self,base_line_clk:datetime) -> None:
        _temp = np.zeros(self.ego_plan.shape)
        for _truck in self.truck_list:
            _this_truck_departure_time = _truck.generate_depature_time_list()
            for _relative_node_order,_d_time in enumerate(_this_truck_departure_time):
                if _relative_node_order == len(_this_truck_departure_time) - 1:
                    # this is the last node
                    break
                if _d_time < base_line_clk + timedelta(minutes=self.future_range) and _d_time >= base_line_clk:
                    # +1 for the corresponding matrix
                    # determine which row it is gonna be
                    # the row time window is (left,right]
                    _gap = _d_time - base_line_clk
                    n_of_row = int(_gap.total_seconds()/60)
                    if _gap.total_seconds() % 60 == 0:
                        n_of_row += -1
                    if n_of_row < 0:
                        n_of_row = 0
                    # we now need to select the edge
                    n_of_col = _truck.edge_list[_relative_node_order]
                    # n_of_col = _truck.node_list[_relative_node_order]
                    _temp[n_of_row,n_of_col] += 1
                else:
                    break
        self.ego_plan = _temp
    
    def select_communication_slot(self,max_slot:int):
        self.current_slot_com = random.randint(1,max_slot)

    def random_select_one_neighbor(self,commun_graph:nx.graph) -> int:
        # return the carrier index selected, return -1 if not neighbor
        _neighbors = list(commun_graph.neighbors(self.carrier_index))
        if len(_neighbors) == 0:
            return -1
        return random.choice(_neighbors)
    
    def split_plan_table_into_two_part(self) -> list:
        # self.public_prime = key_prime
        key_prime = self.public_prime
        matrix_shape = self.consensus_matrix.shape
        A = np.random.randint(0, key_prime, size=matrix_shape, dtype=np.int64)
        B = (self.consensus_matrix - A) % key_prime
        return [A,B]

    def answer_known_departure_list_for_this_edge(self,edge_index:int,start_time:datetime,end_time:datetime,table_base_clk:datetime):
        # the carrier the asking truck, all the carrier knows about depature parteners
        # depending on required time window
        agg_depart_time = [] # all combined
        agg_qty         = []
        ego_depart_time = [] # only this carrier
        ego_qty         = []

        # start time is the current matrix base
        # so it means everything happens in this timeframe are considered happend together
        # (A row in the time plan matrix)
        # self.next_period_agg = self.encrypted_data
        if start_time < table_base_clk + timedelta(minutes=self.time_resolution*self.future_range):
            # something make senses in this window
            edge_array_raw = self.consensus_matrix[:,edge_index].copy()
            sum_col        = (edge_array_raw)

            for row_index,row in enumerate(list(sum_col)):
                if row == 0:
                    continue
                else:
                    this_time = table_base_clk + timedelta(minutes=(row_index + 1) * self.time_resolution)
                    # the depart time is set at the latest of this window
                    if this_time <= end_time:
                        agg_depart_time.append(this_time)
                        agg_qty.append(row)

        for _truck in self.truck_list:
            if edge_index in _truck.edge_list:
                [t_a,t_d] = _truck.answer_my_plan_at_hub(_truck.node_list[_truck.edge_list.index(edge_index)])
                if t_d >= start_time and t_d <= end_time:
                    if t_d.second == 0 and t_d.microsecond == 0:
                        _t_round = t_d
                    else:
                        _t_round = t_d.replace(second=0,microsecond=0) + timedelta(minutes=self.time_resolution)
                    # this round time should exist in the list already
                    if _t_round in ego_depart_time:
                        ego_qty[ego_depart_time.index(_t_round)] += 1
                    else:
                        ego_depart_time.append(_t_round)
                        ego_qty.append(1) 
                     
        if not len(ego_depart_time) == len(agg_depart_time):
            # there is such case that part of the ego plan is not in the agg data, that we align the length of data
            for ego_depart_time_index,ego_depart_time_ele in enumerate(ego_depart_time):
                if not ego_depart_time_ele in agg_depart_time:
                    agg_depart_time.append(ego_depart_time_ele)
                    agg_qty.append(ego_qty[ego_depart_time_index]) 
                    # it must be noted that, the ego time may not be properly order

        return agg_qty,ego_qty,ego_depart_time,agg_depart_time


    def est_current_carrier_number(self) -> None:
        # at some point, this carrier will estimate the current carrier number
        # everytime I perform a new information exchange
        _sum_matrix = self.next_period_plan_matrix % self.public_prime
        non_zero_indices    = np.nonzero(_sum_matrix>0)
        if len(non_zero_indices[0]) == 0:
            # all elements now are zero,
            # the carrier have very bad estimation on only itself is online
            # but this should not happen
            self.carrier_qty_est = 1
        else:
            min_value = np.min(_sum_matrix[non_zero_indices])
            # it is assumed that this value is the average of the sum '1'
            self.carrier_qty_est = math.floor(1/min_value)
        
    def get_current_carrier_number(self,est_qty:int) -> None:
        self.carrier_qty_est = est_qty

    def select_a_random_neighbor(self) -> int:
        return random.choice(self.neighoring_carrier_index)

    def _is_enc_data_pausible(self) -> bool:
        raw_data = self.encrypted_data * self.carrier_qty_est
            # Check if elements are very close to integers
        is_close_to_integers = np.isclose(a=raw_data, b=np.round(raw_data),atol=0.01)
        is_plausible = np.all(is_close_to_integers)
        return is_plausible
    
    def decode_enc_table(self,cur_table_base:datetime) -> None:
        if cur_table_base - self.enc_data_table_base > timedelta(minutes=self.future_range):
            # all information too old, rolling out
            self.consensus_matrix   = self.ego_plan
        else:
            if self._is_enc_data_pausible():
                decoded_data            = np.round(self.encrypted_data * self.carrier_qty_est)
                _gap                    = (cur_table_base - self.enc_data_table_base).total_seconds()
                if _gap != 0:
                    _gap_row                = int(_gap/(60*self.time_resolution))
                    _vaild_part             = decoded_data[_gap_row:,:]
                    _comp_part              = self.ego_plan[-_gap_row:,:]

                    self.consensus_matrix   = np.vstack((_vaild_part,_comp_part)) % self.public_prime
                else:
                    self.consensus_matrix   = decoded_data % self.public_prime
            else:
                pass # do nothing, kept the valid consensus

    def update_encryption_data(self,base_clk:datetime) -> None:
        new_plan = self.return_current_ego_plan_in_matrix(base_clk)
        diff_mat = new_plan - self.ego_plan
        try:
            self.encrypted_data     += diff_mat         # changes are loaded in for communication
            # the update data above only stays alive for this communication period (before next table roll)

            self.consensus_matrix   += diff_mat         # changes are loaded for next round of EP
            self.ego_plan = new_plan
        except:
            pass

    def return_current_ego_plan_in_matrix(self,base_clk:datetime) -> np.array:
        temp = np.zeros(shape=self.ego_plan.shape)
        base_line_clk = base_clk
        for _truck in self.truck_list:
            _this_truck_departure_time = _truck.generate_depature_time_list()
            for _relative_node_order,_d_time in enumerate(_this_truck_departure_time):
                if _relative_node_order == len(_this_truck_departure_time) - 1:
                    # this is the last node
                    break
                if _d_time < base_line_clk + timedelta(minutes=self.future_range) and _d_time >= base_line_clk:
                    # +1 for the corresponding matrix
                    # determine which row it is gonna be
                    if _d_time == base_line_clk:
                        continue
                    _gap = _d_time - base_line_clk
                    # FIXME: 8:01:40 -> row 0 -> incorrect
                    # but if 8:01:00 -> row 0 -> correct
                    if _gap.total_seconds()%60 == 0:
                        # this is a correct minute
                        n_of_row = int(_gap.total_seconds()/60) - 1
                        if n_of_row < 0:
                            n_of_row = 0
                    else:
                        n_of_row = int(_gap.total_seconds()/60)
                    # we now need to select the edge
                    n_of_col = _truck.edge_list[_relative_node_order]
                    # n_of_col = _truck.node_list[_relative_node_order]
                    temp[n_of_row,n_of_col] += 1
                else:
                    continue
        return temp
    
    def rolling_consensus_table(self,cur_clk:datetime) -> None:
        # first update ego plan
        ego_plan_new    = self.return_current_ego_plan_in_matrix(cur_clk)
        # comparing to the last timing, the waiting plan of trucks and the base timing will be changed
        # Not sure this has been done at other steps. But this make sure consensus reached before
        # which may come from a disconnected peer, will remain valid
        delta_ego_plan  = ego_plan_new[0:-1,:] - self.ego_plan[1:,:]
        # The new consensus is based on the previous plan
        new_consensus_part      = self.consensus_matrix[1:,:] + delta_ego_plan
        self.consensus_matrix   = np.vstack((new_consensus_part,ego_plan_new[-1,:]))
        self.ego_plan           = ego_plan_new
    
    def rolliing_encryption_table(self) -> None:
        enc_valid = self.encrypted_data[1:,:]
        new_data  = np.vstack((enc_valid,self.ego_plan[-1:,:]))
        self.encrypted_data = new_data

    def answer_latest_raw_depart_time(self,t_round:datetime,edge_index:int):
        depart_time_raw = []
        for _truck in self.truck_list:
            if edge_index in _truck.edge_list:
                _this_truck_departure_time = _truck.generate_depature_time_list()
                for _d_time in _this_truck_departure_time:
                    if _d_time <= t_round and _d_time > t_round - timedelta(minutes=self.time_resolution):
                        # this is the raw time
                        depart_time_raw.append(_d_time)
        return max(depart_time_raw)