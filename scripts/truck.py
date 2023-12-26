# -*- coding: utf-8 -*-

class Truck:
    
    def __init__(self,node_list:list,truck_index:int) -> None:
        # init a truck entity and each of them has an truck index and a node list to travel through
        self.node_list      = node_list
        self.truck_index    = truck_index
        self.edge_list      = self._generate_edges_from_nodes()

    def _generate_edges_from_nodes_cord(self) -> dict:
        # create a set of edges that the truck is to travel through
        edge_dict = {}
        for itx,node in enumerate(self.node_list):
            if itx == len(self.node_list) - 1: 
                break
            edge = [node,self.node_list[itx+1]]
            edge_dict[itx] = edge
        
        return edge_dict

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