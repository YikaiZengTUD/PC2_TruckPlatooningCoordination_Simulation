# -*- coding: utf-8 -*-
# In this file we define class and function of global information of all trucks
import random

class TruckSwarm:
    # This is a class that globally generate parameters for all truck
    
    def __init__(self,n_of_truck:int,task_set:dict) -> None:
        self.amount = n_of_truck
        self.task_set = task_set

    def generate_random_start_time(self):
        # for each truck we generate a random start time within one hour
        for truck_index in range(self.amount)：
            