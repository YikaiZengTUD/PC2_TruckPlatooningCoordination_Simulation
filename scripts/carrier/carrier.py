from carrier.truck import Truck
import numpy as np
from datetime import datetime,timedelta
import networkx as nx
import random
from numba import njit,prange


@njit(parallel=True)
def numba_check_validate_intermedia(average_intermedia, previous_average_intermedia, stable_threshold, carrier_qty, public_key, validate_counter, consensus_table, stable_rounds_settings=5):

    rows, cols = average_intermedia.shape
    diff = np.abs(average_intermedia - previous_average_intermedia)
    is_stable = diff <= stable_threshold

    for i in prange(rows):
        for j in prange(cols):
            if is_stable[i, j]:
                validate_counter[i, j] += 1
            else:
                validate_counter[i, j] = 0

    stable_long_enough = validate_counter >= stable_rounds_settings

    if np.any(stable_long_enough):
        decode_raw = np.zeros_like(average_intermedia)
        for i in prange(rows):
            for j in prange(cols):
                if stable_long_enough[i, j]:
                    decode_raw[i, j] = average_intermedia[i, j] * carrier_qty
        decode_round = np.round(decode_raw)
        is_close_to_int = np.abs(decode_raw - decode_round) < 0.05
        decode_round = decode_round % public_key

        for i in prange(rows):
            for j in prange(cols):
                if stable_long_enough[i, j] and is_close_to_int[i, j]:
                    consensus_table[i, j] = decode_round[i, j]

    for i in prange(rows):
        for j in prange(cols):
            previous_average_intermedia[i, j] = average_intermedia[i, j]

class Carrier:

    def __init__(self,carrier_index:int,consensus_table:np.array,consensus_range:int) -> None:
        
        self.carrier_index = carrier_index
        self.truck_list    = []

        self.consensus_table    = consensus_table
        self.ego_table          = consensus_table
        self.ego_table_record   = self.ego_table

        self.consensus_range_sec        = consensus_range
        if not consensus_table.any() == None:
            self.consensus_resolution_sec   = int(consensus_range/consensus_table.shape[0])

            self.average_intermedia          = np.zeros(self.consensus_table.shape)
            self.previous_average_intermedia = np.zeros(self.consensus_table.shape)
            self.validate_counter            = np.zeros(self.consensus_table.shape)

        self.stable_threshold            = 0.002

        self.row_part1 = None
        self.row_part2 = None

        self.latest_row = None
        self.in_commun  = False
        self.com_slot   = None

        self.carrier_qty = 1

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

                if t_d <= table_base:
                    # this is past edge, not involved here, therefore pass
                    continue
                
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
                if n_of_row < 0:
                    raise ValueError('Invalid row')
                plan_table[n_of_row,_edge] += 1

        return plan_table
    
    def update_ego_table(self,table_base:datetime) -> None:
        self.ego_table = self.load_plan_into_ego_matrix(table_base)

    def process_update_row(self,public_key:int) -> None:
        self.row_part1,self.row_part2 = self._divide_last_row_into_two_parts(public_key=public_key)

    def update_average_intermedia(self) -> None:
        # first stack self.average_intermedia and self.latest_row, and then remove the first row of the stacked array
         # Stack self.average_intermedia and self.latest_row
        if self.average_intermedia.size == 0:
            self.average_intermedia = self.latest_row.reshape(1, -1)
        else:
            self.average_intermedia = np.vstack((self.average_intermedia, self.latest_row))
        
        # Now remove the first row of the stacked array
        if self.average_intermedia.shape[0] > 1:  # Check if there are at least two rows to remove one
            self.average_intermedia = self.average_intermedia[1:]  # Removes the first row

        self.previous_average_intermedia = np.vstack((self.previous_average_intermedia,self.latest_row))
        self.previous_average_intermedia = self.previous_average_intermedia[1:]
    
    def select_a_com_slot(self,options:int):
        self.com_slot = random.randint(1,options)


    def _extract_last_row_ego_table(self) -> np.array:
        # Extract and return the last row of the ego table
        if self.ego_table.size == 0:
            return np.array([])  # Return an empty array if the table is empty
        return self.ego_table[-1]  # Return the last row
    
    def _divide_last_row_into_two_parts(self,public_key:int) -> list:
        last_row = self._extract_last_row_ego_table()
        if last_row.size == 0:
            return [np.array([]), np.array([])]  # Return two empty arrays if there's no last row
    
        part1 = np.random.randint(0, public_key, size=last_row.shape)
        part2 = (last_row - part1) % public_key  # Ensure part2 values also respect the modulus condition

        return [part1, part2]


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

    def check_validate_intermedia(self, public_key: int):
        numba_check_validate_intermedia(self.average_intermedia, 
                                        self.previous_average_intermedia, 
                                        self.stable_threshold, 
                                        self.carrier_qty, 
                                        public_key, 
                                        self.validate_counter, 
                                        self.consensus_table)


    def update_consensus_table(self):
        # this function is called everytime the ego plan table is updated when the table needs rolling
        # Ensure the tables are initialized and not empty
        if self.consensus_table is None or self.consensus_table.size == 0:
            print("Consensus table is empty or not initialized.")
            return
        if self.ego_table is None or self.ego_table.size == 0:
            print("Ego table is empty or not initialized.")
            return
        
        # ego_table_slice         = self.ego_table[:-1, :]
        # ego_table_record_slice  = self.ego_table_record[1:, :]
        # delta = ego_table_slice - ego_table_record_slice
        # self.ego_table_record = self.ego_table

        # Remove the first row of consensus_table
        self.consensus_table = np.delete(self.consensus_table, 0, axis=0)
        # self.consensus_table += delta
        # Append the last row of ego_table to consensus_table
        last_row = self.ego_table[-1, :].reshape(1, -1)
        self.consensus_table = np.vstack((self.consensus_table, last_row))

    def select_a_random_carrier(self,option_list:list) -> int:
        # Make a copy of the list to modify it without affecting the original list
        modified_list = option_list.copy()
        
        # Remove self.carrier_index from the list if it exists
        if self.carrier_index in modified_list:
            modified_list.remove(self.carrier_index)
        
        # Check if the list is empty after removal
        if not modified_list:
            raise ValueError("No carriers available for selection")
        
        # Randomly select and return an element from the modified list
        return random.choice(modified_list)


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
            time_options.append(dep_time_grid)
            depart_qty.append(1)

        index_to_adjust = time_options.index(dep_time_grid)
    
        if depart_qty[index_to_adjust] == 1:
            del time_options[index_to_adjust]
            del depart_qty[index_to_adjust]
        else:
            depart_qty[index_to_adjust] -= 1

        return time_options, depart_qty
    
    def sync_decision_changes(self,table_base:datetime):
        
        ego_table = self.load_plan_into_ego_matrix(table_base=table_base)
        # the ego table is updated 

        delta = ego_table - self.ego_table
        self.ego_table          = ego_table
        self.consensus_table    += delta
        self.average_intermedia += delta


