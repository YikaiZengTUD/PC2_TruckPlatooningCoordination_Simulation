# -*- coding: utf-8 -*-
# In this file we define class and function of global information of all trucks
import random
from datetime import datetime,timedelta
import networkx as nx
import csv
class TruckSwarm:
    # This is a class that globally generate parameters for all truck

    def __init__(self,n_of_truck:int,task_set:dict) -> None:
        self.amount = n_of_truck
        self.task_set = task_set
        self.carrier_index_list = []
        self.finished_counter = 0
        if self.amount < 5000:
            self.generate_virtual_random_truck_index()

    def init_communication_graph(self) -> None:
        self.commun_graph = nx.Graph()

    def generate_random_start_time(self) -> list:
        # for each truck we generate a random start time within one hour
        random_time_dirft = [random.randint(0, 36) for _ in range(self.amount)]
        return random_time_dirft
            
    def collect_travel_duration(self,data:dict) -> dict:
        ts_time_duration_dict = {}
        for _key_index in data.keys():
            duration_list = []
            _this_entry = data[_key_index]
            for node_time_pair in _this_entry:
                duration_list.append(node_time_pair[1])
            ts_time_duration_dict[_key_index] = duration_list
        return ts_time_duration_dict

    def extract_departure_time(self,data:dict) -> list:
        date_format = '%Y-%m-%d %H:%M:%S.%f'
        ts_departure_time = []
        for truck_index in data.keys():
            _this_entry = data[truck_index]
            # this is a dict
            t_d = _this_entry[next(iter(_this_entry))]['t_d']
            ts_departure_time.append(datetime.strptime(t_d[0], date_format))
        return ts_departure_time
    
    def assign_carrier_index(self,truck_index: int,_is_random: bool) -> int:
        if _is_random:
            if self.amount == 5000:
                i = truck_index
            else:
                i = self.random_index[self._random_index_pointer]
                self._random_index_pointer += 1
            # vehicle 0-4999, fleet 1-855
            # small size fleet Type 1: where each fleet has only one truck (total: 325 trucks, f1-f325)
            if i>=0 and i<=324:
                f_i=i+1
            # small-size fleet Type 2: where each fleet has 3 trucks (total: 1086 trucks, f326-f687)
            if i>=325 and i<=1410:
                f_i=326+int((i-325)/3)
            
            # small-size fleet Type 3: where each fleet has 7 trucks (total: 560 trucks, f688-767)
            if i>=1411 and i<=1970:
                f_i=688+int((i-1411)/7)
            
            # medium-size fleet Type 4: where each fleet has 15 trucks (total:735 trucks, f768-f816)
            if i>=1971 and i<=2705: 
                f_i=768+int((i-1971)/15)
            
            # medium-size fleet Type 5: where each fleet has 34 trucks (total: 918 trucks, f817-f843)
            if i>=2706 and i<=3623:
                f_i=817+int((i-2706)/34)
            
            # medium-size fleet Type 6: where each fleet has 74 trucks (total: 592 trucks, f844-f851)
            if i>=3624 and i<=4215:
                f_i=844+int((i-3624)/74)
            
            # large-size fleet Type 7: where each fleet has 148 trucks (total: 444 trucks, f852-f854)
            if i>=4216 and i<=4659:
                f_i=852+int((i-4216)/148)
            
            # lareg-size fleet Type 8: where each fleet has 340 trucks (total: 340 trucks)
            if i>=4660 and i<=4999:
                f_i=855

        else:
            with open('start_configuration.csv', newline='') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip the header row if it exists

                for row in reader:
                    # Extract truck index and carrier index from the row
                    row_truck_index = int(row[0])  # Assuming the truck index is in the first column
                    carrier_index = int(row[1])     # Assuming the carrier index is in the second column
                    
                    # Check if the truck index matches the input truck index
                    if row_truck_index == truck_index:
                        # return carrier_index  # Return the carrier index if found
                        f_i = carrier_index
                    
        if not f_i in self.carrier_index_list:
            self.carrier_index_list.append(f_i) # record all carrier index in this simulation
        return f_i
            
    def generate_virtual_random_truck_index(self):
        # only in use for smaller data set in debugging
        self.random_index = random.sample(range(5000),self.amount)
        self._random_index_pointer = 0


    def get_max_simulation_time(self,start_time_list:list,travel_time_dict:dict,waiting_budget:list) -> datetime:
        for _truck_index,start_time in enumerate(start_time_list):
            travel_duration_list = travel_time_dict[_truck_index]
            travel_duration_all  = sum(travel_duration_list)
            t_max = start_time + timedelta(seconds=(travel_duration_all)) + timedelta(seconds=waiting_budget[_truck_index])
            if _truck_index == 0:
                max_time = t_max
            else:
                if t_max > max_time:
                    max_time = t_max
        return max_time

        

