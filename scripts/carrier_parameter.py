# -*- coding: utf-8 -*-
from truck_parameter import Truck
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
        self.connecting_carrier = []

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

