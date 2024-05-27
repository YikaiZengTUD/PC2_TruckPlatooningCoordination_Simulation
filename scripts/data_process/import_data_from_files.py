import os
import ast
import datetime

def import_data_from(filepath:str,node_list_file:str,travel_time_file:str,start_time_file:str) -> list:

    node_list_dir = os.path.join(filepath,node_list_file)

    with open(node_list_dir,'r') as file:
        travel_node_list_dict = ast.literal_eval(file.read())

    all_node_list,travel_node_index_list_dict, edge_list  = _process_coordinates(travel_node_list_dict)

    # Reading and converting the dictionary from the file

    travel_time_file_path = os.path.join(filepath,travel_time_file)
    with open(travel_time_file_path, 'r') as file:
        travel_time_dict_raw = ast.literal_eval(file.read())

    travel_time_dict = _extract_travel_times(travel_time_dict_raw)

    start_time_file_raw = os.path.join(filepath,start_time_file)

    with open(start_time_file_raw,'r') as file:
        start_time_dict_raw = ast.literal_eval(file.read())

    start_times = _extract_first_arrival_times(start_time_dict_raw)

    return all_node_list, travel_node_index_list_dict, travel_time_dict, edge_list, start_times

def _extract_travel_times(travel_time_dict):
    # New dictionary to hold just the travel times
    travel_times_only_dict = {}

    # Iterate over each key and extract the travel times from each sublist
    for key, travel_lists in travel_time_dict.items():
        travel_times_only_dict[key] = [travel_time for _, travel_time in travel_lists]

    return travel_times_only_dict

def _extract_first_arrival_times(start_time_dict):
    # Dictionary to hold the first arrival times converted to datetime objects
    first_arrival_times = {}
    
    # Iterate through each entry in the start_time_dict
    for key, vehicles in start_time_dict.items():
        # Get the first vehicle's coordinate (first key of the inner dictionary)
        first_coord = next(iter(vehicles))
        # Extract the 't_a' list and convert the first element to datetime
        t_a_str = vehicles[first_coord]['t_a'][0]
        # Convert string to datetime object
        t_a_datetime = datetime.datetime.strptime(t_a_str, '%Y-%m-%d %H:%M:%S.%f')
        # Store in the dictionary
        first_arrival_times[key] = t_a_datetime
    
    return first_arrival_times

def _process_coordinates(travel_node_list_dict):

    # Extract all unique coordinates and create a list
    all_coordinates = []
    # To maintain a mapping of coordinate to index
    coordinates_index_map = {}
    # To store unique edges
    unique_edges = set()

    # Iterate over the dictionary and extract unique coordinates
    for key, coordinates in travel_node_list_dict.items():
        indexed_path = []
        for coord in coordinates:
            if coord not in coordinates_index_map:
                coordinates_index_map[coord] = len(all_coordinates)
                all_coordinates.append(coord)
            indexed_path.append(coordinates_index_map[coord])
        
        # Extract edges from indexed path
        edges = list(zip(indexed_path, indexed_path[1:]))
        unique_edges.update(edges)

    # Replace original coordinates with their corresponding index
    for key, coordinates in travel_node_list_dict.items():
        travel_node_list_dict[key] = [coordinates_index_map[coord] for coord in coordinates]

    return all_coordinates, travel_node_list_dict, list(unique_edges)

if __name__ == "__main__":

    filepath    = 'data'
    filename1   = "OD_hubs_new_1000Trucks"
    filename2   = "OD_hubs_travel_1000Trucks"
    filename3   = "vehicle_arr_dep_hubs0_1000Trucks"

    data1,data2,data3,data4,data5 = import_data_from(filepath,filename1,filename2,filename3)
    print(data1)