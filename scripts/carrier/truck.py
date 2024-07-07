import csv
import warnings
from datetime import datetime, timedelta
import networkx as nx
import time
class Truck:

    def __init__(self,truck_index:int,task_by_hub_index:list,travel_time_list:list,start_time:datetime) -> None:
        
        self.truck_index    = truck_index
        self.hub_list       = task_by_hub_index
        self.travel_time    = travel_time_list

        self.carrier_index  = 0
        self.edge_list      = []
        self.waiting_budget = 0.0

        self.start_time     = start_time

        self.wait_plan      = [0] * (len(self.hub_list))

        self.is_finish      = False

        self.position       = (0,0)

        self.waiting_budget = 0.1 * sum(self.travel_time)

        self.deadline       = self.start_time + timedelta(seconds=(sum(self.travel_time))) + timedelta(seconds=self.waiting_budget)

        self.dp_graph       = nx.DiGraph()

        # platooning settings
        self.t_cost     = 25/3600  # euro/seconds
        self.t_travel   = 56/3600  # euro/seconds
        self.xi         = 0.1 

    def get_carrier_number_fixed(self,record_file:str) -> None:

        # this function reads truck -> carrier file,
        # we have a fixed data set for testing
        # TODO: there is a twin function and may randomly generate this projection

        with open(record_file, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header row if it exists
            for row in reader:
                # Extract truck index and carrier index from the row
                row_truck_index = int(row[0])       # Assuming the truck index is in the first column
                carrier_index   = int(row[1])       # Assuming the carrier index is in the second column

                if row_truck_index == self.truck_index:
                    self.carrier_index = carrier_index

    def generate_edge_list(self,map_edges:list) -> None:

        for hub_index, start_hub in enumerate(self.hub_list):

            if hub_index == len(self.hub_list) - 1:
                break

            end_hub     = self.hub_list[hub_index+1]
            this_edge   = (start_hub,end_hub)

            edge_index  = map_edges.index(this_edge)

            self.edge_list.append(edge_index) 

    def generate_arrival_time_list(self) -> list:
        t_last_a = self.start_time

        t_a_list = [self.start_time]

        for _hub_order,_hub in enumerate(self.hub_list):

            if _hub_order == 0:
                continue
            

            t_gap = self.wait_plan[_hub_order] + self.travel_time[_hub_order-1]
            t_a = t_last_a + timedelta(seconds=t_gap)

            t_a_list.append(t_a)

            t_last_a = t_a

        return t_a_list

    def generate_depart_time_list(self) -> list:

        # the depart time of the last hub is virtual, but kept in this list

        t_a_list = self.generate_arrival_time_list()

        t_d_list = []

        for _order,t_a in enumerate(t_a_list):

            t_d = t_a + timedelta(seconds=self.wait_plan[_order])
            t_d_list.append(t_d)

        return t_d_list

    # def return_cur_position(self,now_time:datetime,map_node_coordinates:dict,step_ms:int) -> tuple:
    #     # with time and the plan, we now caculate an estimated coordinates for this truck
    #     # Noted: if a truck will 'appear' in the first hub 60s before the first arrival time
    #     if now_time < self.start_time - timedelta(seconds=60):
    #         return (0,0) # does not exist on map
        
    #     t_a_list = self.generate_arrival_time_list()
    #     t_d_list = self.generate_depart_time_list()
        
    #     # Check if now_time is after the last arrival time
    #     if now_time >= t_a_list[-1]:
    #         self.is_finish = True
    #         return (0, 0)       # Move the truck out by assigning it to (0,0)

    #     for i in range(len(t_a_list)):
            
    #         if t_a_list[i] == t_d_list[i]:
    #             if now_time >= t_a_list[i] and now_time - timedelta(seconds=1e-3*step_ms) < t_d_list[i]:
    #                 return map_node_coordinates[self.hub_list[i]]

    #         if t_a_list[i] <= now_time <= t_d_list[i]:
    #             # FIXME: 由于时间间隔的愿意，无等待时间的节点会判断出问题
    #             # the truck is on this hub

    #             return map_node_coordinates[self.hub_list[i]]
            
    #         if now_time < t_a_list[i] and i == 0:

    #             # speacial handle of the first node

    #             return map_node_coordinates[self.hub_list[i]]
            
    #         if now_time > t_d_list[i] and now_time <= t_a_list[i+1]:

    #             # on the edge for the next hub
    #             this_travel_time    = self.travel_time[i]

    #             this_hub_pos        = map_node_coordinates[self.hub_list[i]]
    #             next_hub_pos        = map_node_coordinates[self.hub_list[i+1]]

    #             progress_time       = now_time - t_d_list[i]
    #             progress            = (progress_time.total_seconds())/this_travel_time

    #             new_x               = this_hub_pos[0] + (next_hub_pos[0] - this_hub_pos[0]) * progress
    #             new_y               = this_hub_pos[1] + (next_hub_pos[1] - this_hub_pos[1]) * progress

    #             return (new_x,new_y)

    # def update_position(self,now:datetime,map:dict,step_ms:int) -> None:

    #     self.position = self.return_cur_position(now_time=now,map_node_coordinates=map,step_ms=step_ms)

    def is_arrival_moment(self, now_time: datetime, time_step: int) -> bool:
        t_a_list = self.generate_arrival_time_list()
        for index, t_a in enumerate(t_a_list):
            if t_a <= now_time < t_a + timedelta(seconds=time_step):
                if index == len(t_a_list) - 1:
                    self.is_finish = True
                    print('start check done',time.time() - start)
                    return False # arrive at final destination is not counted here
                print('start check done',time.time() - start)
                return True
        return False
    
    def is_departing_moment(self, now_time: datetime, time_step: int) -> bool:
        t_d_list = self.generate_depart_time_list()
        for index, t_d in enumerate(t_d_list):
            if t_d <= now_time < t_d + timedelta(seconds=time_step):
                if index <= len(self.edge_list)-1:
                    return True, self.edge_list[index]
                else:
                    return False, None
        return False, None
    
    def current_hub_order_at_time(self, now_time: datetime,step_ms:int) -> int:
        t_a_list = self.generate_arrival_time_list()
        for hub_index, arrival_time in enumerate(t_a_list):
            # if arrival_time <= now_time <= arrival_time + timedelta(seconds=self.wait_plan[hub_index]):
            #     return self.hub_list[hub_index]
            if arrival_time <= now_time:
                if (arrival_time + timedelta(seconds=self.wait_plan[hub_index])) >= now_time:
                    return hub_index
                if self.wait_plan[hub_index] < step_ms * 1e-3:
                    # case that it walk past the check point
                    if arrival_time > now_time - timedelta(seconds=step_ms*1e-3):
                        return hub_index
        return -1  # Return -1 if the truck is not currently at any hub


    def time_window_on_edge(self, now_time: datetime, geo_edge_index: int,step_ms:int) -> list:
        current_hub_index = self.current_hub_order_at_time(now_time,step_ms)
        if current_hub_index == -1:
            raise ValueError("The truck is not currently at any hub.")
        
        current_edge_order = current_hub_index
        
        required_edge_order = self.edge_list.index(geo_edge_index)

        if required_edge_order < current_edge_order:
            # this is request for the past, should not answer
            raise ValueError("The truck has already pass this hub.")
    
         # Calculate the earliest possible arrival time at the hub where the edge is
        dep_time_list = self.generate_depart_time_list()
        earliest_possible_arrival = dep_time_list[current_edge_order]
        for i in range(current_hub_index, required_edge_order + 1):
             if i > current_hub_index:  # Skip adding travel time for the current hub
                earliest_possible_arrival += timedelta(seconds=self.travel_time[i - 1] + self.wait_plan[i])

        # Calculate the time window for the specified edge
        time_window_start   = earliest_possible_arrival
        time_window_end     = earliest_possible_arrival + timedelta(seconds=self.waiting_budget)

        return [(time_window_start, time_window_end)]

    def future_edges(self, now_time: datetime,step_ms:int) -> list:
        current_hub_index = self.current_hub_order_at_time(now_time,step_ms)
        if current_hub_index == -1:
            raise ValueError("The truck is not currently at any hub.")

        future_edges_list = []

        for i in range(current_hub_index, len(self.edge_list)):
            future_edges_list.append(self.edge_list[i])

        return future_edges_list

    def validate_options_from_two_sources(self,ego_options:tuple,agg_options:tuple,table_base:datetime,predict_range_sec:int) -> tuple:
        # two options, one from same carrier plan, which should be accurate and long term (the whole time window)
        # and the consensus plan

        predict_endline = table_base + timedelta(seconds=predict_range_sec)

        ego_time_options = ego_options[0]
        agg_time_options = agg_options[0]
        
        ego_options_qty = ego_options[1]
        agg_options_qty = agg_options[1]
        combined_time_options = []
        ego_qty = []
        agg_qty = []

        if len(ego_time_options) == 0 and len(agg_time_options) == 0:
            # both empty
            return combined_time_options,ego_qty,agg_qty
        
        for _index,time_slot in enumerate(ego_time_options):
            if time_slot > predict_endline:
                combined_time_options.append(time_slot)
                ego_qty.append(ego_options_qty[_index])
                agg_qty.append(ego_options_qty[_index])
            else:
            # so within the prediction zone, this has to be corrcet
                if not time_slot in agg_time_options:
                    # this is a questionalbe case that the consensus lose its own information
                    warnings.warn('Time options exist only in ego plan with in the consensus range')
                else:
                    combined_time_options.append(time_slot)
                    _index_agg = agg_time_options.index(time_slot)
                    if agg_options_qty[_index_agg] < ego_options_qty[_index]:
                        raise ValueError('The aggregated data qty is less than the single carrier qty')
                    ego_qty.append(ego_options_qty[_index])
                    agg_qty.append(agg_options_qty[_index_agg])
        
        for _index,time_slot in enumerate(agg_time_options):

            # every slot here should be in the predict window
            if not time_slot in combined_time_options:
                # something purely unknown ego cases
                combined_time_options.append(time_slot)
                ego_qty.append(0)
                agg_qty.append(agg_options_qty[_index])

        return combined_time_options,ego_qty,agg_qty
    
    def calculate_earliest_times_to_edges(self, now_time: datetime,step_ms:int) -> dict:
        earliest_times = {}
        current_hub_index = self.current_hub_order_at_time(now_time,step_ms)

        if current_hub_index == -1:
            raise ValueError("The truck is not currently at any hub.")

        # Calculate earliest possible times for all future edges
        cumulative_time = 0
        for i in range(current_hub_index, len(self.edge_list)):
            edge = self.edge_list[i]
            if i > current_hub_index:  # Add travel time only for edges after the current hub
                cumulative_time += self.travel_time[i - 1]
            earliest_times[edge] = now_time + timedelta(seconds=cumulative_time)
        
        return earliest_times
    
    def caculate_weight_cost(self,ego_veh:int,agg_veh:int,wait_time:float,t_travel:float) -> float:
        cost_const = t_travel * self.t_cost + t_travel * self.t_travel
        cost_wait  = wait_time * self.t_cost
        if ego_veh == 0 and agg_veh == 0:
            reward_of_carrier = 0
        else:
            agg_veh += 1
            ego_veh += 1

            reward_of_carrier = (((agg_veh - 1) * self.xi)/agg_veh) * ego_veh * self.t_travel * t_travel
        cost_edge = cost_wait + cost_const - reward_of_carrier
        if cost_edge < 0:
            warnings.warn('Warning: Negative weigt cost -> leading Dijkstra’s Algorithm not fit, losing solving speed')

        return cost_edge

    def generate_dp_graph(self,options:dict,now_time:datetime,step_ms:int) -> nx.DiGraph:

        graph = nx.DiGraph()
        edges_to_decide = self.future_edges(now_time,step_ms)

        # first create a virtual search start point, with id = 0, and with an attribute called 'time_dep' as now_time,
        graph.add_node(0, time_dep=now_time,edge_index=-1,time_dep_lastnode=now_time)
        dp_id = 1
        # Add dp nodes for each future edge
        dp_edge_start = [0]
        dp_edge_end   = []
        t_earliest_dict = self.calculate_earliest_times_to_edges(now_time,step_ms)

        options_popout = {}

        for edge in edges_to_decide:
            # First caculate the earliest possible time to that edge
            # current time is now, time and we have a self.travel_time (list) for travel time on each edge

            time_options_tuple  = options[edge]
            time_options        = time_options_tuple[0]
            ego_qty             = time_options_tuple[1]
            agg_qty             = time_options_tuple[2]

            t_earliest          = t_earliest_dict[edge]

            if edges_to_decide.index(edge) > 0:
                t_travel = self.travel_time[self.edge_list.index(edge)-1]
            else:
                t_travel = 0
            t_cost = self.travel_time[self.edge_list.index(edge)]
            
            # if not t_earliest in time_options:
            #     # this is likely to happen

            #     dep_last_node = t_earliest - timedelta(seconds=t_travel)
            #     graph.add_node(dp_id,time_dep_lastnode=dep_last_node,time_dep=t_earliest,edge_index=edge)
            #     dp_edge_end.append(dp_id)
            #     dp_id += 1
                
            # list_next_node_options = []
            for index,opt in enumerate(time_options):
                ego_amount = ego_qty[index]
                agg_amount = agg_qty[index]

                dep_last_node = opt - timedelta(seconds=t_travel)
                graph.add_node(dp_id,time_dep_lastnode=dep_last_node,time_dep=opt,edge_index=edge,ego_veh=ego_amount,agg_veh=agg_amount)
                dp_edge_end.append(dp_id)
                dp_id += 1

            # now check those missing but necessary nodes
            ego_amount = 0
            agg_amount = 0
            # it is fully solo, otherwise being listed in the above method
            for node_index in dp_edge_start:
                this_nx_node       = graph.nodes[node_index]
                dep_time_last_node = this_nx_node['time_dep']
                dep_time_this_node = dep_time_last_node + timedelta(seconds=t_travel)
                graph.add_node(dp_id,time_dep_lastnode=dep_time_last_node,time_dep=dep_time_this_node,edge_index=edge,ego_veh=ego_amount,agg_veh=agg_amount)
                dp_edge_end.append(dp_id)
                dp_id += 1
                
            #     if not opt == t_earliest: # this option is auto added in the last step
            #         time_opt_to_add = opt  + timedelta(seconds=t_cost)
            #         list_next_node_options.append(time_opt_to_add)

            # if edges_to_decide.index(edge) <= len(edges_to_decide) - 2:
            #     options_popout[edges_to_decide[edges_to_decide.index(edge)+1]] = list_next_node_options

            # if edges_to_decide.index(edge) >= 1:
            #     # that we should consider plug in other nodes
            #     list_last_node_options = options_popout[edge]

            #     for index,opt in enumerate(list_last_node_options):
            #         if opt in time_options:
            #             continue # this node has already been added because there is platooning chance
            #         ego_amount = 1
            #         agg_amount = 1 # it should be a fully solo, otherwise will be processed in the above steps

            #         dep_last_node = opt - timedelta(seconds=t_travel) # the truck must start from last node no later than this time
            #         graph.add_node(dp_id,time_dep_lastnode=dep_last_node,time_dep=opt,edge_index=edge,ego_veh=ego_amount,agg_veh=agg_amount)
            #         dp_edge_end.append(dp_id)
            #         dp_id += 1                    


            for dp_node_start in dp_edge_start:

                for dp_node_end in dp_edge_end:

                    #  if the time_dep_lastnode of dp_node_end >= the time_dep of dp_node_start, there should be an edge in between
                    # a attribute 'wait_time' = time_dep_lastnode - time_dep converted to seconds from timedelta
                    time_dep_lastnode = graph.nodes[dp_node_end]['time_dep_lastnode']
                    time_dep          = graph.nodes[dp_node_start]['time_dep']

                    ego_amount = graph.nodes[dp_node_end].get('ego_veh', 0)
                    agg_amount = graph.nodes[dp_node_end].get('agg_veh', 0)
                    if time_dep_lastnode >= time_dep:
                        wait_time = (time_dep_lastnode - time_dep).total_seconds()
                        cost      = self.caculate_weight_cost(ego_amount,agg_amount,wait_time,t_cost)
                        graph.add_edge(dp_node_start, dp_node_end, wait_time=wait_time,weight=cost)

            dp_edge_start = dp_edge_end
            dp_edge_end   = []
        # Add a virtual end node
        end_node_id = dp_id
        graph.add_node(end_node_id, time_dep=None, edge_index=-2)
        for dp_node_start in dp_edge_start:
            graph.add_edge(dp_node_start, end_node_id, weight=0)

        return graph
        
    def find_shortest_path(self, graph: nx.DiGraph) -> list:
        start_node = 0
        end_node = max(graph.nodes)  # Find the maximum node ID to identify the end node
        try:
            path = nx.shortest_path(graph, source=start_node, target=end_node, weight='weight')
            return path
        except nx.NetworkXNoPath:
            print("No path found from start to end node.")
            return []
        
    def update_waiting_plan(self,dp_path:list,edge_list_future:list) -> bool:
        dp_graph = self.dp_graph
        wait_plan = self.wait_plan.copy()
        for index,edge in enumerate(edge_list_future):
            node_depart    = dp_path[index]
            node_arrival   = dp_path[index+1]
            # get the wait time attribute in dp graph on the node: node_arrival 
            edge_index_all = self.edge_list.index(edge)
            wait_edge = dp_graph.edges[(node_depart,node_arrival)].get('wait_time',0)
            wait_plan[edge_index_all] = wait_edge
        
        if wait_plan != self.wait_plan:
            self.wait_plan = wait_plan
            return True
        else:
            return False

if __name__ == "__main__":
    T = Truck(
        truck_index=0,
        task_by_hub_index=[0,1],
        travel_time_list=[10]
    )
    T.get_carrier_number_fixed('start_configuration.csv')
    print(T)