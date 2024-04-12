import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

import re
import numpy as np

# Read the CSV file
# Updated function to also count the occurrences of each carrier index
def read_csv_extract_unique_indices_and_count(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Assume the second column contains the carrier index
    # Extract unique elements from this column and create a set
    unique_indices = set(df.iloc[:, 1].unique())
    
    # Count occurrences of each carrier index
    counts = df.iloc[:, 1].value_counts()
    
    return unique_indices, counts

# Uncomment the line below to run the function with your specific file path
# unique_carrier_indices, carrier_index_counts = read_csv_extract_unique_indices_and_count('start_configuration.csv')


def create_and_visualize_graph_improved(file_path):
    # Using the previously defined function to get indices and their counts
    unique_indices, counts = read_csv_extract_unique_indices_and_count(file_path)
    
    # Create a graph
    G = nx.Graph()
    
    # Add nodes with the node size attribute
    for index in unique_indices:
        G.add_node(index, size=counts[index])
    
    # Apply a non-linear scaling for the node sizes (square root is commonly used)
    max_count = counts.max()
    node_sizes = [(counts[node] / max_count) ** 0.5 * 1000 for node in G.nodes()]  # Normalize and scale

    # Set up plot size
    plt.figure(figsize=(20, 20))  # Increase figure size to help spread out the nodes

    # Draw the graph with a spring layout which should also help with crowding
    pos = nx.spring_layout(G, iterations=50)
    nx.draw(G, pos, node_size=node_sizes, with_labels=True)

    # Show the graph
    plt.show()

# Uncomment the line below to run the function with your specific file path
# create_and_visualize_graph_improved('start_configuration.csv')



# file_path = 'start_configuration.csv'

# create_and_visualize_graph_improved(file_path)


# Define the function to parse the text file and create graphs
def parse_and_create_graphs(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    # Split the content by '---' which is the divider in the file
    graph_sections = content.split('---\n')[1:]  # Skip the first split as it will be empty
    
    # List to store graphs data (timestamp, adjacency matrix)
    graphs_data = []

    # Regular expression pattern to match the graph timestamp and adjacency matrix
    timestamp_pattern = r'Graph: (\d+\.\d+)\n'
    matrix_pattern = r'\[(\[[^\]]+\])\]'

    for section in graph_sections:
        # Find timestamp
        timestamp = re.search(timestamp_pattern, section)
        if timestamp:
            timestamp = float(timestamp.group(1))
        
        # Find adjacency matrix
        matrix = re.search(matrix_pattern, section)
        if matrix:
            # Convert the string representation of the matrix into a numpy array
            adj_matrix = np.array(eval(matrix.group(1)))
        
        # Store the tuple of timestamp and adjacency matrix
        graphs_data.append((timestamp, adj_matrix))
    
    return graphs_data

# Function to visualize the graphs
def visualize_graphs(graphs_data):
    for timestamp, adj_matrix in graphs_data:
        # Create a graph for each timestamp
        G = nx.Graph()
        for i, row in enumerate(adj_matrix):
            for j, val in enumerate(row):
                if val == 1:
                    G.add_edge(i, j)  # Add an edge if the adjacency matrix has a 1
        
        # Draw the graph
        plt.figure(figsize=(8, 8))
        plt.title(f"Graph at timestamp: {timestamp}")
        nx.draw_spectral(G, with_labels=True)
        plt.show()

# Uncomment the lines below to parse the file and visualize the graphs
graphs_data = parse_and_create_graphs('result/graphs.txt')
visualize_graphs(graphs_data)
