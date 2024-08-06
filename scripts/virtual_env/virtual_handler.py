import networkx as nx
import math
class VirtualHandler:

    # from this class we introduce some methods, that are only applied because the simulation
    # in the real world, it will get generated automatically

    def __init__(self) -> None:
        self.com_network = nx.Graph()

    def build_comm_graph_from_v2v_pos(self, pos_dict: dict, t2c_dict: dict, range_km=1.0):
        # Create a new graph
        graph = nx.Graph()

        # Add nodes to the graph (nodes are carriers of trucks present in pos_dict)
        for t, pos in pos_dict.items():
            if pos != (0, 0):  # Ignore trucks at position (0, 0)
                carrier = t2c_dict[t]
                graph.add_node(carrier)

        # Add edges based on proximity within the threshold
        keys_list = [k for k, v in pos_dict.items() if v != (0, 0)]
        for i in range(len(keys_list)):
            for j in range(i + 1, len(keys_list)):
                t1, t2 = keys_list[i], keys_list[j]
                distance = self._haversine(pos_dict[t1], pos_dict[t2])
                if distance <= range_km:
                    c1, c2 = t2c_dict[t1], t2c_dict[t2]
                    graph.add_edge(c1, c2)

        self.com_network = graph


    def _haversine(self,coord1, coord2):
        # Coordinates in decimal degrees (lat, long)
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Radius of Earth in kilometers (change this constant to customize the unit)
        R = 6371.0
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c  # Output distance in kilometers
        return distance

        
    