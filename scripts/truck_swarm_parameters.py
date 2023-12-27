# -*- coding: utf-8 -*-
# In this file we define class and function of global information of all trucks
import random

class TruckSwarm:
    # This is a class that globally generate parameters for all truck

    def __init__(self,n_of_truck:int,task_set:dict) -> None:
        self.amount = n_of_truck
        self.task_set = task_set

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

