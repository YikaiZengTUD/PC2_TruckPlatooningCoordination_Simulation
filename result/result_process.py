import json
def find_keys_with_non_zero(file_path):
    """
    Reads a JSON-formatted file and finds keys that contain non-zero elements.

    Args:
    - file_path (str): The file path of the JSON file to check.

    Returns:
    - list: A list of keys that contain non-zero elements.
    """
    keys_with_non_zero = []  # Initialize an empty list to hold keys with non-zero elements
    
    with open(file_path, 'r') as file:
        data = json.load(file)  # Load JSON data from file

        # Iterate through the data to find keys with non-zero elements
        for key, values in data.items():
            if any(value != 0 for value in values):  # Check if any value is non-zero
                keys_with_non_zero.append(key)  # Add the key to the list if it has non-zero elements

    return keys_with_non_zero  # Return the list of keys

file_path = 'result/wait_time.txt'
# Running the function to find keys with non-zero elements.
res = find_keys_with_non_zero(file_path)

print(res)