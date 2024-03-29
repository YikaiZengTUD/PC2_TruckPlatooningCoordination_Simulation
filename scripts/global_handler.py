# -*- coding: utf-8 -*-
from datetime import datetime,timedelta
import csv
import random
from truck_methods import Truck
import networkx as nx
import json

class global_handler:

    # This is a virtual class that used in this case handling the problem setup
    # It is applied in problem setup
    def __init__(self) -> None:
        self.amount             = 0
        self.carrier_index_list = []
        if self.amount < 5000:
            self.generate_virtual_random_truck_index()
        
        self.truck_2_carrier    = {}

        self.truck_result       = {}
        self.wait_time_result   = {}
        self.on_edge_result     = {}
        self.comm_topo          = {}

        self.t_cost     = 25/3600  # euro/seconds
        self.t_travel   = 56/3600  # euro/seconds
        self.xi         = 0.1 
    
    def load_data(self,debug_data_select:bool) -> list:
        if not debug_data_select:
            f = open('data\OD_hubs_new_1000Trucks','r')
            a = f.read()
            task_dict = eval(a) # hubs between the origin and destination
            f.close()

            f=open('data\OD_hubs_travel_1000Trucks','r')
            a=f.read()
            travel_time_dict=eval(a) # travel times of different trucks on road segments
            f.close()

            f=open('data\\vehicle_arr_dep_hubs0_1000Trucks','r') # the initial departure times from the origins 
            a=f.read()
            vehicle_arr_dep_test=eval(a)
            f.close()
            # ---
            f=open('data\\travel_dd_1000Trucks','r')
            a=f.read()
            travel_dd_test=eval(a) # a dict, which includes the allowed total waiting time (seconds) of each truck in the whole trip
            f.close()
        else:
            # This is a small test set, to verfiy the function of this simulation
            task_dict               = {1: [(18.02546160254861, 59.38157382906624), (16.50658561538482, 58.28150384602444), (16.48374131130608, 57.56893497161655), (16.3883782476514, 56.9467696413148), (16.32098233050319, 56.6727356017633)],
                                       577: [(11.82842433708403, 58.35084770729797), (12.0100484809166, 57.69305990943261)],
                                       317: [(11.82842433708403, 58.35084770729797), (12.0100484809166, 57.69305990943261)],
                                       405: [(11.82842433708403, 58.35084770729797), (12.0100484809166, 57.69305990943261), (12.9235479241113, 57.71549970054969), (14.15662952188514, 57.75197484564614), (14.07668139189311, 57.15992894233719)],
                                       177: [(13.10271132053603, 55.38218924904132), (14.09604530011136, 55.4879185585079)],
                                       947: [(13.10271132053603, 55.38218924904132), (12.7860903072887, 56.01801572566561), (14.77870801731729, 56.89565675229857)],
                                       342: [(22.06332834731737, 65.62200924609067), (20.96014349272004, 64.75038578544915)],
                                       544: [(22.06332834731737, 65.62200924609067), (20.96014349272004, 64.75038578544915)]}
            travel_time_dict        = {1: [[(18.02546160254861, 59.38157382906624), 12703.2895], [(16.50658561538482, 58.28150384602444), 5755.7795], [(16.48374131130608, 57.56893497161655), 4285.0585], [(16.3883782476514, 56.9467696413148), 1894.0153]],
                                       577: [[(11.82842433708403, 58.35084770729797), 5018.2878]],
                                       317: [[(11.82842433708403, 58.35084770729797), 5018.2878]],
                                       405: [[(11.82842433708403, 58.35084770729797), 5018.2878], [(12.0100484809166, 57.69305990943261), 3588.4145], [(12.9235479241113, 57.71549970054969), 5176.933], [(14.15662952188514, 57.75197484564614), 3513.3958]],
                                       177: [[(13.10271132053603, 55.38218924904132), 5516.1927]],
                                       947: [[(13.10271132053603, 55.38218924904132), 5035.2804], [(12.7860903072887, 56.01801572566561), 10082.9701]],
                                       342: [[(22.06332834731737, 65.62200924609067), 8390.1522]],
                                       544: [[(22.06332834731737, 65.62200924609067), 8390.1522]]}
            vehicle_arr_dep_test    = { 1: {(18.02546160254861, 59.38157382906624): {'t_a': ['2021-11-20 08:01:40.0000'], 't_d': ['2021-11-20 08:01:40.0000'], 'label': 'I'}, (16.50658561538482, 58.28150384602444): {'t_a': ['2021-11-20 11:33:23.2895'], 't_d': ['2021-11-20 11:33:23.2895'], 'label': 'I'}, (16.48374131130608, 57.56893497161655): {'t_a': ['2021-11-20 13:09:19.0690'], 't_d': ['2021-11-20 13:09:19.0690'], 'label': 'I'}, (16.3883782476514, 56.9467696413148): {'t_a': ['2021-11-20 14:20:44.1275'], 't_d': ['2021-11-20 14:20:44.1275'], 'label': 'I'}, (16.32098233050319, 56.6727356017633): {'t_a': ['2021-11-20 14:52:18.1428'], 't_d': []}},
                                        577: {(11.82842433708403, 58.35084770729797): {'t_a': ['2021-11-20 08:00:00.0000'], 't_d': ['2021-11-20 08:00:00.0000'], 'label': 'I'}, (12.0100484809166, 57.69305990943261): {'t_a': ['2021-11-20 09:23:38.2878'], 't_d': []}},
                                        317: {(11.82842433708403, 58.35084770729797): {'t_a': ['2021-11-20 08:01:40.0000'], 't_d': ['2021-11-20 08:01:40.0000'], 'label': 'I'}, (12.0100484809166, 57.69305990943261): {'t_a': ['2021-11-20 09:25:18.2878'], 't_d': []}},
                                        405: {(11.82842433708403, 58.35084770729797): {'t_a': ['2021-11-20 08:01:40.0000'], 't_d': ['2021-11-20 08:01:40.0000'], 'label': 'I'}, (12.0100484809166, 57.69305990943261): {'t_a': ['2021-11-20 09:25:18.2878'], 't_d': ['2021-11-20 09:25:18.2878'], 'label': 'I'}, (12.9235479241113, 57.71549970054969): {'t_a': ['2021-11-20 10:25:06.7023'], 't_d': ['2021-11-20 10:25:06.7023'], 'label': 'I'}, (14.15662952188514, 57.75197484564614): {'t_a': ['2021-11-20 11:51:23.6353'], 't_d': ['2021-11-20 11:51:23.6353'], 'label': 'I'}, (14.07668139189311, 57.15992894233719): {'t_a': ['2021-11-20 12:49:57.0311'], 't_d': []}},
                                        177: {(13.10271132053603, 55.38218924904132): {'t_a': ['2021-11-20 08:10:00.0000'], 't_d': ['2021-11-20 08:10:00.0000'], 'label': 'I'}, (14.09604530011136, 55.4879185585079): {'t_a': ['2021-11-20 09:41:56.1927'], 't_d': []}},
                                        947: {(13.10271132053603, 55.38218924904132): {'t_a': ['2021-11-20 08:10:00.0000'], 't_d': ['2021-11-20 08:10:00.0000'], 'label': 'I'}, (12.7860903072887, 56.01801572566561): {'t_a': ['2021-11-20 09:33:55.2804'], 't_d': ['2021-11-20 09:33:55.2804'], 'label': 'I'}, (14.77870801731729, 56.89565675229857): {'t_a': ['2021-11-20 12:21:58.2505'], 't_d': []}},
                                        342: {(22.06332834731737, 65.62200924609067): {'t_a': ['2021-11-20 08:26:40.0000'], 't_d': ['2021-11-20 08:26:40.0000'], 'label': 'I'}, (20.96014349272004, 64.75038578544915): {'t_a': ['2021-11-20 10:46:30.1522'], 't_d': []}},
                                        544: {(22.06332834731737, 65.62200924609067): {'t_a': ['2021-11-20 08:23:20.0000'], 't_d': ['2021-11-20 08:23:20.0000'], 'label': 'I'}, (20.96014349272004, 64.75038578544915): {'t_a': ['2021-11-20 10:43:10.1522'], 't_d': []}}
                                        }
            travel_dd_test          = {1:2463.8143,577:501.8288,317:501.8288,405:1729.7031,177:551.6193,947:1511.8251,342: 839.0152,544: 839.0152}
        n_of_truck = len(task_dict)
        self.amount = n_of_truck
        return [task_dict,travel_time_dict,vehicle_arr_dep_test,travel_dd_test]

    def collect_travel_duration(self,data:dict) -> dict:
        ts_time_duration_dict = {}
        for _key_index in data.keys():
            duration_list = []
            _this_entry = data[_key_index]
            for node_time_pair in _this_entry:
                duration_list.append(node_time_pair[1])
            ts_time_duration_dict[_key_index] = duration_list
        return ts_time_duration_dict

    def extract_departure_time(self,data:dict) -> list:
        date_format = '%Y-%m-%d %H:%M:%S.%f'
        ts_departure_time = []
        for truck_index in data.keys():
            _this_entry = data[truck_index]
            # this is a dict
            t_d = _this_entry[next(iter(_this_entry))]['t_d']
            ts_departure_time.append(datetime.strptime(t_d[0], date_format))
        return ts_departure_time
    
    def get_max_simulation_time(self,start_time_list:list,travel_time_dict:dict,waiting_budget:list,step:int) -> datetime:
        _truck_key = list(travel_time_dict.keys())
        for _truck_index,start_time in enumerate(start_time_list):
            travel_duration_list = travel_time_dict[_truck_key[_truck_index]]
            travel_duration_all  = sum(travel_duration_list)
            t_max = start_time + timedelta(seconds=(travel_duration_all)) + timedelta(seconds=waiting_budget[_truck_key[_truck_index]])
            if _truck_index == 0:
                max_time = t_max
            else:
                if t_max > max_time:
                    max_time = t_max
            # print(max_time)
            max_time = max_time.replace(microsecond=0)
        return max_time
    
    def generate_virtual_random_truck_index(self):
        # only in use for smaller data set in debugging
        self.random_index = random.sample(range(5000),self.amount)
        self._random_index_pointer = 0
    
    def assign_carrier_index(self,truck_index: int,_is_random: bool) -> int:
        if _is_random:
            if self.amount == 5000:
                i = truck_index
            else:
                i = self.random_index[self._random_index_pointer]
                self._random_index_pointer += 1
            # vehicle 0-4999, fleet 1-855
            # small size fleet Type 1: where each fleet has only one truck (total: 325 trucks, f1-f325)
            if i>=0 and i<=324:
                f_i=i+1
            # small-size fleet Type 2: where each fleet has 3 trucks (total: 1086 trucks, f326-f687)
            if i>=325 and i<=1410:
                f_i=326+int((i-325)/3)
            
            # small-size fleet Type 3: where each fleet has 7 trucks (total: 560 trucks, f688-767)
            if i>=1411 and i<=1970:
                f_i=688+int((i-1411)/7)
            
            # medium-size fleet Type 4: where each fleet has 15 trucks (total:735 trucks, f768-f816)
            if i>=1971 and i<=2705: 
                f_i=768+int((i-1971)/15)
            
            # medium-size fleet Type 5: where each fleet has 34 trucks (total: 918 trucks, f817-f843)
            if i>=2706 and i<=3623:
                f_i=817+int((i-2706)/34)
            
            # medium-size fleet Type 6: where each fleet has 74 trucks (total: 592 trucks, f844-f851)
            if i>=3624 and i<=4215:
                f_i=844+int((i-3624)/74)
            
            # large-size fleet Type 7: where each fleet has 148 trucks (total: 444 trucks, f852-f854)
            if i>=4216 and i<=4659:
                f_i=852+int((i-4216)/148)
            
            # lareg-size fleet Type 8: where each fleet has 340 trucks (total: 340 trucks)
            if i>=4660 and i<=4999:
                f_i=855

        else:
            with open('start_configuration.csv', newline='') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip the header row if it exists

                for row in reader:
                    # Extract truck index and carrier index from the row
                    row_truck_index = int(row[0])  # Assuming the truck index is in the first column
                    carrier_index = int(row[1])     # Assuming the carrier index is in the second column
                    
                    # Check if the truck index matches the input truck index
                    if row_truck_index == truck_index:
                        # return carrier_index  # Return the carrier index if found
                        f_i = carrier_index
                    
        if not f_i in self.carrier_index_list:
            self.carrier_index_list.append(f_i) # record all carrier index in this simulation
        self.truck_2_carrier[truck_index] = f_i
        return f_i
    
    def next_int_row_clk(self,this_clk:datetime,base_clk:datetime,table_resolution:int) -> datetime:
        time_gap = this_clk - base_clk
        time_gap_seconds = time_gap.total_seconds()
        row_lower = time_gap_seconds/(table_resolution * 60)
        return base_clk + timedelta(minutes=table_resolution*(row_lower+1))
    
    def register_this_traveledge_cost(self,truck:Truck) -> None:
        if truck.current_edge == -1 and truck.current_node == -1:
           pass
        else: 
            # this truck has not done

            if truck.current_edge == -1:
                _order = truck.node_list.index(truck.current_node)
            else:
                _order = truck.edge_list.index(truck.current_edge)

            n_of_partener = len(truck.platooning_partener)

            fuel_cost = truck.travel_duration[_order] * (self.t_travel)
            time_cost = truck.travel_duration[_order] * (self.t_cost)

            _factor = (1 + (1 - self.xi) * n_of_partener) / ( 1 + n_of_partener)
            cost = fuel_cost * _factor + time_cost

            if not truck.truck_index in self.truck_result.keys():
                _index = truck.truck_index
                self.truck_result[_index] = []

            self.truck_result[truck.truck_index].append(cost)

    def save_fuel_cost_result(self) -> None:
        with open("result/travel_cost.txt", "w") as fp:
            json.dump(self.truck_result,fp)
        print('Termination: Travel cost saved to travel_cost.txt')

    def register_this_on_edge_timing(self,edge_dict:dict,time:datetime) -> None:
        if len(edge_dict) > 0:
            self.on_edge_result[time.timestamp()] = edge_dict

    def save_on_edge_result(self) -> None:
        with open("result/on_edge.txt", "w") as fp:
            json.dump(self.on_edge_result,fp)
        print('Termination: Departure timing recorded')

    def record_waittime_result(self,truck:Truck):
        wait_time = truck.waiting_plan
        self.wait_time_result[truck.truck_index] = wait_time
    
    def save_wait_time_result(self) -> None:
        with open("result/wait_time.txt", "w") as fp:
            json.dump(self.wait_time_result,fp)
        print('Termination: Wait time recorded')  

    def record_comm_topo(self,input_graph:nx.Graph,time:datetime):
        self.comm_topo[time.timestamp()] = input_graph

    def save_comm_topo_result(self) -> None:
        with open('result/graphs.txt', 'w') as file:
        # Iterate over each graph in the dictionary
            for key, graph in self.comm_topo.items():
                # Write a header indicating the start of a new graph
                file.write(f'Graph: {key}\n')
                adjlist_str = str(nx.to_numpy_array(graph))
                # Write the graph data in the adjacency list format
                file.write(str(list(graph.nodes())))
                file.write('\n')
                file.write(adjlist_str)
            
                # Write a separator to indicate the end of the graph
                file.write('\n---\n')
        print('Termination: Communication network changes recorded')      