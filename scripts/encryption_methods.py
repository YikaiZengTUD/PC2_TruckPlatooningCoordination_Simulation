import networkx as nx
import numpy as np
import random
class Encrpytion_Platfrom:

    def __init__(self,key:int) -> None:
        # self.init_communication_graph()
        self.prime_key = key
        self.qualified_sub_graphs = []
        self.quali_carrier_list   = []
        self.encryption_buffer    = []
        print("Initialization: Encrpytion platform established")

    def init_communication_graph(self) -> None:
        self.commun_graph = nx.Graph() # this is the all-in graph for all carrier comminication
    
    def process_carrier_neighbor_list(self,_input_list:list) -> None:
        for _index in _input_list:
            if not _index in self.commun_graph.nodes:
                self.commun_graph.add_node(_index)
        for _index in _input_list:
            for _another_index in _input_list:
                if _index == _another_index:
                    continue
                self.commun_graph.add_edge(_index,_another_index)

    def find_qualified_sub_grps(self) -> list:
        subgraphs = []
        # Find connected components in the graph
        connected_components = nx.connected_components(self.commun_graph)
        # Iterate over connected components
        for component in connected_components:
            # Convert the component into a subgraph
            subgraph = self.commun_graph.subgraph(component)
            # Check if the subgraph has at least 3 nodes
            if len(subgraph.nodes) >= 3:
                subgraphs.append(subgraph)
        return subgraphs
    
    def generate_qualified_carrier_list(self,sub_list:list) -> list:
        quali_list = []
        for subgraph in sub_list:
            quali_list += list(subgraph.nodes)
        return quali_list
    
    def encryption_platform_prepare(self) -> None:
        self.qualified_sub_graphs   = self.find_qualified_sub_grps()
        self.quali_carrier_list     = self.generate_qualified_carrier_list(self.qualified_sub_graphs)
        self.encryption_buffer      = [0] * len(self.qualified_sub_graphs)
    
    def answer_if_qualified(self,carrier_index:int) -> bool:
        if carrier_index in self.quali_carrier_list:
            return True
        return False
    
    def answer_subgraph_index_of_this_carrier(self,carrier_index:int) -> int:
        for _sb_index,subgraph in enumerate(self.qualified_sub_graphs):
            if carrier_index in list(subgraph.nodes):
                return _sb_index

    def recieve_carrier_data(self,carrier_index:int,input_block:np.array) -> None:
        sub_index = self.answer_subgraph_index_of_this_carrier(carrier_index)
        self.encryption_buffer[sub_index] += input_block

    def redistribute_secret_parts(self) -> None:
        self.redistribute_dict = {}
        for sub_index, buffer_data in enumerate(self.encryption_buffer):
            this_subgraph = self.qualified_sub_graphs[sub_index]
            n_of_carrier  = len(list(this_subgraph.nodes))
            _array_size   = buffer_data.shape

            _part_buffer  = []
            for _carrier_order in range(0,n_of_carrier-1):
                _part_buffer.append(np.random.randint(low=0,high=self.prime_key,size=_array_size))
            _sum_buffer = np.zeros(shape=_array_size)
            for item in _part_buffer:
                _sum_buffer += item
            
            _last_piece = (buffer_data - _sum_buffer) % self.prime_key
            _part_buffer.append(_last_piece)
            
            for carrier_order,part in enumerate(_part_buffer):
                self.redistribute_dict[list(this_subgraph.nodes)[carrier_order]] = part
    
    def answer_distribute_values(self,carrier_index:int) -> np.array:
        return self.redistribute_dict[carrier_index]
    
    def answer_subgraph_number(self,carrier_index:int) -> int:
        sub_index = self.answer_subgraph_index_of_this_carrier(carrier_index)
        sub_graph = self.qualified_sub_graphs[sub_index]
        return len(list(sub_graph.nodes))
    
    def check_if_enc_communiation_between_two_carriers(self,carrier1:int,carrier2:int) -> bool:
        sub1 = self.answer_subgraph_index_of_this_carrier(carrier1)
        sub2 = self.answer_subgraph_index_of_this_carrier(carrier2)
        if sub1 == sub2:
            return True
        else:
            return False