import networkx as nx
import numpy as np

class Encryptor:

    def __init__(self,key_prime:int) -> None:
        self.public_key = key_prime
        self.cur_communication_graph = nx.Graph()
        self.received_secrets = {}
        self.qualified_subgraphs = []
        self.divided_parts = {}
        self.subgraph_node_qty = {}
    # the Ecryptor will check connections

    def clear_cache(self) -> None:
        self.cur_communication_graph    = nx.Graph()
        self.qualified_carrier_list     = []
        self.received_secrets           = {}
        self.qualified_subgraphs        = []

    def receive_carrier_reported_neighbor(self, carrier_index: int, neighbor_list: list) -> None:
        """
        Updates the communication graph with new edges from the specified carrier to its neighbors.

        Parameters:
        carrier_index (int): The index of the carrier node in the graph.
        neighbor_list (list): A list of indices representing the neighbors of the carrier.
        """
        # Check if the carrier is already in the graph; add it if it's not
        if carrier_index not in self.cur_communication_graph.nodes:
            self.cur_communication_graph.add_node(carrier_index)

        # Add edges from the carrier to each neighbor in the list
        for neighbor in neighbor_list:
            # Add the neighbor node if it's not already in the graph
            if neighbor not in self.cur_communication_graph.nodes:
                self.cur_communication_graph.add_node(neighbor)
            # Create an edge between the carrier and the neighbor
            self.cur_communication_graph.add_edge(carrier_index, neighbor)


    def find_qualified_connected_components(self) -> None:
        """
        Finds all connected components in the communication graph with three or more nodes
        and stores the list of nodes in self.qualified_carrier_list.
        """
        # Find all connected components in the graph
        connected_components = nx.connected_components(self.cur_communication_graph)

        # Filter components with at least three nodes
        qualified_components = [component for component in connected_components if len(component) >= 3]

        # Flatten the list of sets into a single list of nodes
        self.qualified_carrier_list = [node for component in qualified_components for node in component]
        self.qualified_subgraphs    = qualified_components

    def receive_secret_part(self, carrier_index: int, secret_part: np.array) -> None:
        graph_id = None
        # Identify the graph ID based on carrier index
        for graph_index, sub_graph in enumerate(self.qualified_subgraphs):
            if carrier_index in sub_graph:
                graph_id = graph_index
                break

        # Check if graph_id was found
        if graph_id is None:
            raise ValueError("Carrier index not found in any subgraph")

        # Initialize the array if the key doesn't exist
        if graph_id not in self.received_secrets:
            self.received_secrets[graph_id] = np.zeros(secret_part.shape)
        
        # Add the secret part to the existing array
        self.received_secrets[graph_id] += secret_part

    def divide_secrets(self):
        """
        Divides each secret in received_secrets into n parts such that the sum of these parts equals the original secret.
        The number of parts, n, is determined by the length of the corresponding subgraph in qualified_subgraphs.
        """
        self.divided_parts = {}

        for key, secret in self.received_secrets.items():
            # Get the number of parts to divide the secret into
            n = len(self.qualified_subgraphs[key])
            if n == 0:
                continue  # Prevent division by zero or meaningless division

            # Create n-1 random parts
            random_parts = [np.random.randint(0, self.public_key, secret.shape) for _ in range(n - 1)]
            # Compute the last part such that the sum of all parts equals the original secret
            last_part = secret - np.sum(random_parts, axis=0) % self.public_key
            # Ensure that all parts sum up exactly to the original secret
            random_parts.append(last_part)
            for _index,send_back_values in enumerate(random_parts):
                this_subgraph = self.qualified_subgraphs[key]
                carrier_index = list(this_subgraph)[_index]
                self.divided_parts[carrier_index] = send_back_values

    def prepare_subgraph_participants_qty(self):
        self.subgraph_node_qty = {}
        for sub_graphs in self.qualified_subgraphs:
            # Get the number of parts to divide the secret into
            n = len(sub_graphs)
            if n == 0:
                continue  # Prevent division by zero or meaningless division

            for carrier_index in sub_graphs:
                self.subgraph_node_qty[carrier_index] = len(sub_graphs)

    def answer_subgraph_node_qty(self, carrier_index: int) -> int:
        if carrier_index in self.subgraph_node_qty:
            return self.subgraph_node_qty[carrier_index]
        else:
            raise KeyError(f"Key {carrier_index} not found in subgraph_node_qty")

    # def answer_secrets_parts_reply(self,carrier_index:int) -> np.array:
    #     for graph_index,subgraphs in self.qualified_subgraphs:
    #         if carrier_index in subgraphs:
    #             _index = list(subgraphs).index(carrier_index)
    #             return self.divide_secrets[graph_index][_index]