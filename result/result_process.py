
import json
import csv
from datetime import datetime

with open("result/on_edge.txt", "r") as fp:
    depart_time_dict = json.load(fp)

filename = 'depart_time.csv'

data = []
for depart_time in depart_time_dict.keys():
    dt_object = datetime.fromtimestamp(float(depart_time))
    formatted_datetime = dt_object.strftime('%Y-%m-%d %H:%M:%S')
    this_item = depart_time_dict[depart_time]
    for edge in this_item.keys():
        for truck in this_item[edge]:
            this_line = (formatted_datetime,truck,edge)
            if len(this_item[edge]) > 2:
                print(this_line)
            data.append(this_line)


with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['timestamp', 'truck index', 'edge_index'])
    writer.writerows(data)


