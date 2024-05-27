from carrier.truck import Truck

import numpy as np
from datetime import datetime,timedelta
import networkx as nx
import random
class Carrier:

    def __init__(self,carrier_index:int,consensus_table:np.array,consensus_range:int) -> None:
        
        self.carrier_index = carrier_index
        self.truck_list    = []

        self.consensus_table    = consensus_table
        self.ego_table          = consensus_table
        self.ego_table_record   = self.ego_table

        self.consensus_range_sec        = consensus_range
        self.consensus_resolution_sec   = int(consensus_range/consensus_table.shape[0])
        
        self.neighbor_carrier = []

        self.average_intermedia = np.zeros(self.consensus_table.shape)
        self.connected_peer_qty = 1

        

    def _clear_neighbor_info(self):
        self.neighbor_carrier = []

    def get_neighbors(self,com_network:nx.Graph):
        self._clear_neighbor_info()

        # Check if the current carrier index exists in the network
        if self.carrier_index in list(com_network.nodes):
            # Fetch all neighbors (connected nodes)
            
            self.neighbor_carrier = list(com_network[self.carrier_index])


    def involve_a_truck(self,truck:Truck) -> None:
        # accept a truck into this fleet
        self.truck_list.append(truck)

    def load_plan_into_ego_matrix(self,table_base:datetime) -> np.array:

        plan_table = np.zeros(shape=self.consensus_table.shape)

        table_end_time = table_base + timedelta(seconds=self.consensus_range_sec)
        for _truck in self.truck_list:
            _depart_times = _truck.generate_depart_time_list()
            for _order,t_d in enumerate(_depart_times):
                if _order == len(_depart_times) - 1:
                    # no depart time in last hub
                    break
                if t_d > table_end_time:
                    break # This depart time is out of the consensus `range at this moment
                
                _gap        = t_d - table_base
                _gap_sec    = _gap.total_seconds()

                _gap_row    = int(_gap_sec/self.consensus_resolution_sec)

                if _gap_sec % self.consensus_resolution_sec == 0:
                    # happens to be on the edge
                    n_of_row = _gap_row - 1
                    if n_of_row < 0:
                        continue # this is when the departing moment has just gone
                else:
                    n_of_row = _gap_row
            
                _edge = _truck.edge_list[_order]

                plan_table[n_of_row,_edge] += 1

        return plan_table
    
    def update_ego_table(self,table_base:datetime) -> None:

        self.ego_table = self.load_plan_into_ego_matrix(table_base)


    def divide_secrets_into_two_parts(self, public_key: int) -> None:
        """
        Divides self.ego_table into two parts such that (part1 + part2) % public_key = self.ego_table.
        
        Parameters:
            public_key (int): The public key used as the modulus for dividing the ego_table.
        """
        # Generate a random matrix the same shape as self.ego_table with values in the range [0, public_key-1]
        part1 = np.random.randint(0, public_key, self.ego_table.shape)
        
        # Calculate part2 such that the sum of part1 and part2 modulo public_key equals self.ego_table
        part2 = (self.ego_table - part1) % public_key
        
        # Store the parts as attributes for further use or verification
        self.secret_part1 = part1
        self.secret_part2 = part2

    def get_secrets_pieces(self,secret_part:np.array):
        self.average_intermedia = secret_part + self.secret_part2

    def get_connected_qty(self,peer_qty:int):
        if peer_qty <= 2:
            raise ValueError('insufficient amount of connected carriers')
        self.connected_peer_qty = peer_qty

    def select_random_neighbor(self):
        if not self.neighbor_carrier:
            raise ValueError("neighbor_carrier list is empty")
        return random.choice(self.neighbor_carrier)
    
    def check_validate_intermedia(self,public_key:int):
        value = self.average_intermedia * self.connected_peer_qty

        # Ensure value is a NumPy array
        if not isinstance(value, np.ndarray):
            raise ValueError("The computed value must be a NumPy array.")
        
        if np.all(np.abs(value - np.round(value)) < 0.15):
            decode_raw = np.round(value) % public_key
            # Check if 80% or more elements in decode_raw are zero
            zero_count = np.sum(decode_raw == 0)
            total_count = decode_raw.size
            zero_percentage = zero_count / total_count
            if zero_percentage >= 0.8:
                self.consensus_table = decode_raw
    
    def update_consensus_table(self):
        # this function is called everytime the ego plan table is updated when the table needs rolling
        # Ensure the tables are initialized and not empty
        if self.consensus_table is None or self.consensus_table.size == 0:
            print("Consensus table is empty or not initialized.")
            return
        if self.ego_table is None or self.ego_table.size == 0:
            print("Ego table is empty or not initialized.")
            return
        
        ego_table_slice         = self.ego_table[:-1, :]
        ego_table_record_slice  = self.ego_table_record[1:, :]
        delta = ego_table_slice - ego_table_record_slice
        self.ego_table_record = self.ego_table

        # Remove the first row of consensus_table
        self.consensus_table = np.delete(self.consensus_table, 0, axis=0)
        self.consensus_table += delta
        # Append the last row of ego_table to consensus_table
        last_row = self.ego_table[-1, :].reshape(1, -1)
        self.consensus_table = np.vstack((self.consensus_table, last_row))

    def answer_samecarrier_options(self,edge_index:int,time_window:list,row_resolution_sec:int,asking_truck_index:int):

        time_window_start = time_window[0][0]
        time_window_end   = time_window[0][1]
        
        time_options = []
        depart_qty   = []

        for _truck in self.truck_list:
            if _truck.truck_index == asking_truck_index:
                continue # exclude itself from this option
            if edge_index in _truck.edge_list:
                dep_time_list = _truck.generate_depart_time_list()
                dep_time      = dep_time_list[_truck.edge_list.index(edge_index)]
                if dep_time >= time_window_start and dep_time <= time_window_end:
                    # this car has a concerned time
                    # however we have to round this time, that it fits in a grid of the consensus table
                    # so we can align this with information from the consensus table
                    dep_time_rounded = self._round_continuous_time_in_grid(row_resolution_sec,dep_time)

                    if dep_time_rounded in time_options:
                        depart_qty[time_options.index(dep_time_rounded)] += 1
                    else:
                        time_options.append(dep_time_rounded)
                        depart_qty.append(1)

        return time_options,depart_qty
        
    def _round_continuous_time_in_grid(self, resolution_sec: int, raw_time: datetime) -> datetime:
        # Calculate the number of seconds from the start of the day, including microseconds
        total_seconds = raw_time.hour * 3600 + raw_time.minute * 60 + raw_time.second + raw_time.microsecond / 1_000_000

        # Calculate the remainder when dividing by resolution_sec
        remainder = total_seconds % resolution_sec

        # If the remainder is zero, return the original time (preserving microseconds)
        if remainder == 0:
            return raw_time  # Reset microseconds to zero

        # Calculate the rounded seconds
        rounded_seconds = total_seconds + (resolution_sec - remainder)

        # Calculate the number of seconds past midnight for the rounded time
        rounded_time_past_midnight = timedelta(seconds=rounded_seconds)

        # Combine the rounded seconds with the date of raw_time
        rounded_time = datetime.combine(raw_time.date(), datetime.min.time()) + rounded_time_past_midnight

        return rounded_time

    def answer_carrieragg_options(self,edge_index:int,time_window:list,table_base:datetime,row_resolution_sec:int,asking_truck_index:int):
        time_window_start = time_window[0][0]
        time_window_end   = time_window[0][1]
        
        time_options = []
        depart_qty   = []

        concerned_col = self.consensus_table[:,edge_index]

        n_of_row = self.consensus_table.shape[0]

        last_row_tick = table_base + timedelta(seconds=n_of_row*row_resolution_sec)

        if last_row_tick < time_window_start:
            return time_options,depart_qty

        if table_base > time_window_end:
            raise ValueError('Incorrect time window, not a future edge')
        
        _gap1 = (time_window_start - table_base).total_seconds()
        row_1 = int(_gap1 / row_resolution_sec)
        if _gap1 % row_resolution_sec == 0:
            # it happens to be on the grid 
            row_1 = row_1 -1
            if row_1 < 0:
                raise ValueError('Negative row values')
            
        _gap2 = (time_window_end - table_base).total_seconds()
        row_2 = int(_gap2 / row_resolution_sec)
        if _gap2 % row_resolution_sec == 0:
            row_2 = row_2 - 1
        if row_2 <= row_1:
            raise ValueError("Incorrect time window projection on consensus table")
        row_2 = min(row_2,n_of_row-1)

        # Populate the time options and depart quantities, only for non-zero elements
        for row in range(row_1, row_2 + 1):
            if concerned_col[row] != 0:
                current_time = table_base + timedelta(seconds=(row+1) * row_resolution_sec)
                time_options.append(current_time)
                depart_qty.append(concerned_col[row])

        # remove the asking truck itself from this return list
        
        for _truck in self.truck_list:
            if _truck.truck_index == asking_truck_index:
                dep_time_list = _truck.generate_depart_time_list()
                edge_order    = _truck.edge_list.index(edge_index)
                dep_time      = dep_time_list[edge_order]

        dep_time_grid = self._round_continuous_time_in_grid(row_resolution_sec,dep_time) 
        
        if not dep_time_grid in time_options:
            raise ValueError("Missing this truck time in consensus table")

        index_to_adjust = time_options.index(dep_time_grid)
    
        if depart_qty[index_to_adjust] == 1:
            del time_options[index_to_adjust]
            del depart_qty[index_to_adjust]
        else:
            depart_qty[index_to_adjust] -= 1

        return time_options, depart_qty