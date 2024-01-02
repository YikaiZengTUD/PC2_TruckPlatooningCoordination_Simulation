# -*- coding: utf-8 -*-

class Truck:
    
    def __init__(
            self,node_list:list,
            truck_index:int,
            departure_time:int,
            travel_duration:list,
            carrier_index:int,
            time_buddget:float
            ) -> None:
        # init a truck entity and each of them has an truck index and a node list to travel through
        self.node_list          = node_list
        self.truck_index        = truck_index
        self.departure_time     = departure_time 
        self.travel_duration    = travel_duration
        self.waiting_buddget    = time_buddget

        self.carrier_index      = carrier_index

        self.current_node       = self.node_list[0]
        try:
            self.next_node          = self.node_list[1]
        except:
            print("Error: Only one node found in this planning of Truck index: ",self.truck_index)

        self.current_edge       = -1
        # self.edge_list      = self._generate_edges_from_nodes()

    def _generate_edges_from_nodes_cord(self) -> dict:
        # create a set of edges that the truck is to travel through
        edge_dict = {}
        for itx,node in enumerate(self.node_list):
            if itx == len(self.node_list) - 1: 
                break
            edge = [node,self.node_list[itx+1]]
            edge_dict[itx] = edge 
        return edge_dict
    
    def give_current_node(self) -> int:
        return self.current_node
    
    def get_edge_index(self,global_edge_list:list) -> int:
        my_edge = (self.current_node,self.next_node)
        return global_edge_list.index(my_edge)



if __name__ == '__main__':
    test_nodes = [
        (18.02546160254861, 59.38157382906624), 
        (16.50658561538482, 58.28150384602444), 
        (16.48374131130608, 57.56893497161655), 
        (16.3883782476514, 56.9467696413148), 
        (16.32098233050319, 56.6727356017633)
        ]
    Test_truck = Truck(test_nodes,0)
    print(Test_truck.edge_list)