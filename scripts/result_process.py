import json
import os
import csv
def load_json_data(filepath):
    """ Load the JSON data from the specified filepath """
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

def load_csv_data(filepath):
    """ Load CSV data and create a mapping from truck index to carrier index """
    truck_to_carrier = {}
    with open(filepath, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row if there is one
        for row in reader:
            truck_to_carrier[row[0]] = row[1]
    return truck_to_carrier

def main():
    results_dir = 'result'
    wait_plan_file = 'wait_plan.json'
    depart_info_file = 'depart_info.json'
    truck_info_path = 'start_configuration.csv'
    try:
        # Load both JSON files
        wait_plan_path = os.path.join(results_dir, wait_plan_file)
        depart_info_path = os.path.join(results_dir, depart_info_file)
        wait_plan_data = load_json_data(wait_plan_path)
        depart_info_data = load_json_data(depart_info_path)
        truck_to_carrier_map = load_csv_data(truck_info_path)
        print("Data loaded successfully!")

        vaild_platooning_counter = 0

        for depart_info in depart_info_data.values():
            for depart_info_per_edge in depart_info.values():
                if len(depart_info_per_edge) >= 2:
                    # there is a platooning
                    carrier_list = [truck_to_carrier_map[str(truck)] for truck in depart_info_per_edge]
                    if len(set(carrier_list)) > 1:
                        
                        # now check if this an opportunstic or not
                        for _truck in depart_info_per_edge:
                            if not set(wait_plan_data[str(_truck)]) == {0}:
                                # intentional
                                    print('cross_carrier platooning among carrier',carrier_list)
                                    vaild_platooning_counter += 1

        print('cross carrier chances created: ',vaild_platooning_counter)    

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except json.JSONDecodeError:
        print("Error: One of the files is not a valid JSON.")

if __name__ == "__main__":
    main()
