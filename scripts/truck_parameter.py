# -*- coding: utf-8 -*-

from datetime import datetime,timedelta
import networkx as nx
import numpy as np
class Truck:
    
    def __init__(
            self,node_list:list,
            truck_index:int,
            start_time:int,
            travel_duration:list,
            carrier_index:int,
            time_buddget:float
            ) -> None:
        
        # init a truck entity and each of them has an truck index and a node list to travel through
        self.node_list          = node_list         # This is the list of node that this truck must travel through
        self.carrier_index      = carrier_index     # which carrier does this truck belong to
        self.truck_index        = truck_index

        self.start_time         = start_time
        # This is the timing that this truck will be taken as 'online' and seek for communication
        # It is now considered as the 't_arrival' of the first hub.

        self.travel_duration    = travel_duration

        self.waiting_buddget    = time_buddget

        self.waiting_plan       = [0 for _ in self.node_list]

        self.deadline           = self.get_deadline() 
        # This list should hold the same amount of elements as the node list. We record the plan of how long the truck is planning to wait.
        # By default, (No platooning) it does not wait at all

        # At start, the truck does not 'exist' on the map until the start time
    
        self.current_node       = -1
        self.current_edge       = -1
        self.last_node          = -1
        self.platooning_partener = [] # start with no partener

        # platooning settings
        self.t_cost     = 25/3600  # euro/seconds
        self.t_travel   = 56/3600  # euro/seconds
        self.xi         = 0.1 

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value,Truck):
            return self.truck_index == __value.truck_index
        return False

    def _generate_edges_from_nodes_cord(self) -> dict:
        # create a set of edges that the truck is to travel through
        edge_dict = {}
        for itx,node in enumerate(self.node_list):
            if itx == len(self.node_list) - 1: 
                break
            edge = [node,self.node_list[itx+1]]
            edge_dict[itx] = edge 
        return edge_dict
    
    def give_current_node(self) -> int:
        return self.current_node
    
    def arrive_node(self,target_node:int,current_edge:int) -> None:
        self.current_node = target_node
        self.current_edge = -1
    
    def get_on_edge(self,target_edge:int) -> None:
        self.current_node = -1
        self.current_edge = target_edge

    def generate_edge_list(self,global_edge_list:list) -> None:
        self.edge_list = []
        for _n_index,_n in enumerate(self.node_list):
            if _n_index == 0:
                continue
            else:
                _edge = (self.node_list[_n_index-1],_n)
                _edge_index = global_edge_list.index(_edge)
                self.edge_list.append(_edge_index)

    def locate_myself_based_on_time_and_plan(self,this_clk:datetime) -> None:
        # This function updates the states of the truck of on current time and where it should be based on the time it is now

        # The function is only called when the earlist time is achieved

        # online and travel phase
        _pointer = 1
        _clk_of_arrival = self.start_time + timedelta(seconds=60)
        
        while True:
            
            _clk_of_this_departure  =  _clk_of_arrival        + timedelta(seconds=self.waiting_plan[_pointer-1])
            _clk_of_next            =  _clk_of_this_departure + timedelta(seconds=self.travel_duration[_pointer-1]) - timedelta(seconds=60)

            if this_clk < _clk_of_this_departure:
                # still waiting at this hub
                self.current_node = self.node_list[_pointer-1]
                # not at any edge
                self.current_edge = -1
                break
            elif this_clk < _clk_of_next:
                # already move to the edge
                self.last_node    = self.current_node
                self.current_node = -1
                self.current_edge = self.edge_list[_pointer-1]
                break
            else:
                # we have move to the phase of the next node
                _clk_of_arrival = _clk_of_next + timedelta(seconds=60)
                _pointer += 1
                if _pointer > len(self.node_list)-1:
                    # The truck has arrived its destination
                    self.last_node    = -1 
                    self.current_node = -1
                    self.current_edge = -1
                    # This truck goes offline -> it disappear from the 'real' map
                    break

    def generate_depature_time_list(self) -> list:
        # return a list that contains datetime element of depature time at each hub
        depature_time = []
        _d_time = self.start_time + timedelta(seconds=60)
        for _node_index,_node in enumerate(self.node_list):
            if _node_index == 0:
                _d_time = _d_time + timedelta(self.waiting_plan[_node_index])
            else:
                _d_time = _d_time + timedelta(self.travel_duration[_node_index-1]+self.waiting_plan[_node_index])
            depature_time.append(_d_time)
        return depature_time
    
    def is_now_the_arrving_clk(self,current_clk:datetime,time_gap:int) -> tuple:
        # return (True/False, the node_index)
        for _n_order,_node_index in enumerate(self.node_list):
            if _n_order == 0:
                _this_arrival_time = self.start_time
                # first node
            else:
                _this_arrival_time += self.waiting_plan[_n_order-1] + self.travel_duration[_n_order-1]
            if current_clk >= _this_arrival_time and current_clk < _this_arrival_time + timedelta(microseconds=time_gap):
                # this clk has passed the arrival time and and not yet reaching the next step
                return (True,_node_index)
            else:
                return (False,-1)

    def answer_my_plan_at_hub(self,node_index:int) -> list:
        if node_index in self.node_list:
            self_node_order = self.node_list.index(node_index)
            t_a = self.start_time + timedelta(seconds=60)
            for i in range(self_node_order):
                t_a += timedelta(seconds=self.waiting_plan[i])
                t_a += timedelta(seconds=self.travel_duration[i])

            t_d = t_a + timedelta(seconds=self.waiting_plan[self_node_order])
            return [t_a,t_d]
        else:
            return [-1]
    
    def generate_future_hubs(self) -> list:
        # returned a subset of hubs that the truck is about to visit
        # this will include the 'current node', since by the time this function is called, the truck is 
        # about to arrive
        if not self.current_node == -1:
            current_node_index = self.node_list.index(self.current_node)
            return self.node_list[current_node_index:]
        elif not self.last_node == -1:
            current_node_index = self.node_list.index(self.last_node) + 1
            return self.node_list[current_node_index:]
        else:
            print('%s: No concerned nodes found for this truck',str(self.truck_index))
            return []
    
    def generate_dp_graph(self,base_clk:datetime,synced_plan_from_carrier:list,time_resolution:int,prediction_range:int) -> None:
        
        # The dp graph, for this truck at this hub optimzation round
        self.dp_graph       = nx.Graph()
        dp_node_id = 0
        
        # planning from the carrier, now the matrix has been rounded
        plan_matrix         = synced_plan_from_carrier[0]
        plan_carrier_peer   = synced_plan_from_carrier[1]

        # platooning settings
        t_cost = 25/3600    # euro/seconds
        t_travel = 56/3600  # euro/seconds
        xi = 0.1  

        time_to_hub = 60    # FIXME: should be adaptive to global settings, the simulation sets this process to be triggered only at this timing

        # remaining hubs to travel
        hubs_to_go          = self.node_list[self.node_list.index(self.current_node):]
        duration_slices     = self.travel_duration[self.node_list.index(self.current_node):]
        # current time, also applied for finding window for next hub
        t_a                 = self.answer_my_plan_at_hub(hub)[hubs_to_go[0]]
        t_lower             = t_a + timedelta(seconds=time_to_hub)
        for i,hub in enumerate(hubs_to_go):
            # filter the concerned region for this hub
            if i == len(hubs_to_go) - 1:
                # this is the last hub -> destination, no need to plan
                break
            if not i == 0:
                # the lower bound is defined by the fastest travel time to this node
                t_lower += self.travel_duration[i-1]
            # the upper bound use the whole waiting budget in this hub   
            t_upper = t_lower + timedelta(seconds=self.waiting_buddget)

            # setting the starting hub
            self.dp_graph.add_node(dp_node_id,time_a=t_a,time_d=t_a)
            dp_node_id += 1
            if t_lower > base_clk + timedelta(seconds=prediction_range):
                # the hub is too far, the consensus is not yet there
                pass
            else:
                t_lower_row = int((t_lower - base_clk)/timedelta(seconds=time_resolution))
                t_upper_row = min(int((t_upper - base_clk)/timedelta(seconds=time_resolution)),(prediction_range/time_resolution)-1)
                # now, remove the truck itself from this schedule
                t_d     = self.answer_my_plan_at_hub(hub)[1]
                t_d_row = int((t_d - base_clk)/timedelta(seconds=time_resolution))
                plan_matrix[t_d_row,hub] += -1
                # this is the column part that coresponding to the concerned plan in this hub
                # each of the none 0 element is an optional waiting time 
                this_hub_schedule = plan_matrix[t_lower_row:t_upper_row,hub]
                # get the travel time for this edge
                travel_time = timedelta(seconds=duration_slices[i])
                # record the nodes in dp graph for cross connections
                # the first hub has only one -> which is 0
                arrival_nodes = [0]
                for row_index,all_trucks_qty in enumerate(this_hub_schedule):
                    if row_index == 0 or all_trucks_qty != 0:
                        _temp = []
                        # either this is a none-stop option or there are other trucks
                        # this node represents arrive the next hub at this time
                        t_d_this_hub = t_a + timedelta(seconds=row_index * time_resolution)
                        # this node represents departure from thi
                        t_a_next_hub =  t_d_this_hub + travel_time
                        self.dp_graph.add_node(dp_node_id,time_d=t_d_this_hub,time_a=t_a_next_hub)
                        _temp.append(dp_node_id)
                        dp_node_id += 1

    def get_deadline(self) -> datetime:
        return self.start_time + timedelta(seconds=sum(self.travel_duration) + self.waiting_buddget)

    def answer_time_window_at_hub(self,hub_index:int,now_clk:datetime) -> list:
        # this function is only called after generate incoming hubs, thus no past hubs will be checked here
        # the earlist time is either right now or travel there without any stop

        # also

        if self.current_edge == -1:
            # the truck is on a node
            if self.current_node == hub_index:
                t_e = now_clk + timedelta(seconds=60)
                t_l = t_e + timedelta(seconds=self.waiting_buddget)
            else:
                i1 = self.node_list.index(self.current_node)
                i2 = self.node_list.index(hub_index)
                t_travel = sum(self.travel_duration[i1:i2])
                t_e = now_clk + timedelta(seconds=t_travel)
                t_l = t_e + timedelta(seconds=self.waiting_buddget)
            return [t_e,t_l]
        else:
            # the truck is still travling
            print('Error! This function can not handle when the truck is not arriving a hub')
            return [-1]
    
    def caculate_dp_edge_weight(self,edge_now:int,agg_qty:int,ego_qty:int,wait_time:float) -> float:
        
        edge_order = self.edge_list.index(edge_now)
        t_travel   = self.travel_duration[edge_order]
        
        cost_const = t_travel * self.t_cost + t_travel * self.t_travel
        cost_wait  = wait_time * self.t_cost

        if agg_qty == 0 and ego_qty == 0:
            reward_of_carrier = 0
        else:
            agg_qty += 1
            ego_qty += 1
            reward_of_carrier = (((agg_qty - 1) * self.xi)/agg_qty) * ego_qty * self.t_travel * t_travel

        cost_edge = cost_wait + cost_const - reward_of_carrier
        if cost_edge < 0:
            print('Warning: Negative weigt cost -> leading Dijkstra’s Algorithm not fit, losing solving speed')
        
        return cost_edge
    
    def exclude_this_truck_from_this_hub_plan(self,options_raw:list,hub_index:int) -> list:
        depart_time_ego = options_raw[2]
        depart_time_agg = options_raw[3]

        qty_ego = options_raw[1]
        qty_agg = options_raw[0]

        qty_ego_sorted = qty_ego
        qty_agg_sorted = qty_agg

        time_list_sorted = sorted(depart_time_agg)
        for _t_index,_timing in enumerate(time_list_sorted):
            qty_agg_sorted[_t_index] = qty_agg[depart_time_agg.index(_timing)]
            qty_ego_sorted[_t_index] = qty_ego[depart_time_ego.index(_timing)]

        qty_ego = qty_ego_sorted
        qty_agg = qty_agg_sorted

        if len(depart_time_agg) != len(depart_time_ego):
            print('Error: Inconsistent in planning Aggreated and Ego')
        else:
            [t_a,t_d] = self.answer_my_plan_at_hub(hub_index)
            t_round   = t_d.replace(second=0,microsecond=0)
            _this_truck_index = depart_time_agg.index(t_round)
            qty_ego[_this_truck_index] -= 1
            qty_agg[_this_truck_index] -= 1
        return [time_list_sorted,qty_agg,qty_ego]
    
    def exclude_this_truck_for_this_edge_plan(self,options_raw:list,edge_index:int) -> list:

        hub_index = self.node_list[self.edge_list.index(edge_index)]

        return self.exclude_this_truck_from_this_hub_plan(options_raw,hub_index)

    def generate_future_edges(self) -> list:
        # return the edges
        # this function is called when the truck is about to arrive a hub (decison-making point)
        # the truck is at the self.current_node
        _index = self.node_list.index(self.current_node)
        # it has been checked before, this will not get called when truck finished
        return self.edge_list[_index:]

    def answer_time_window_for_edge(self,this_edge:int,now_clk:datetime) -> list:
        _index = self.edge_list.index(this_edge)
        _hub   = self.node_list[_index]
        return self.answer_time_window_at_hub(hub_index=_hub,now_clk=now_clk)
    
    def optimize_plan(self,des:int) -> list:
        dp_graph = self.dp_graph
        return nx.shortest_path(dp_graph,source=0,target=des,weight='weight')

    def update_waiting_plan(self,dp_shortest_path:list) -> None:
        waiting_times = []
        for u,v in zip(dp_shortest_path[:-1],dp_shortest_path[1:]):
            edge_attributes = self.dp_graph[u][v]
            if 'wait_time' in edge_attributes:
            # Extract the waiting time and add it to the list
                waiting_times.append(edge_attributes['wait_time'])
                # if edge_attributes['wait_time'] > 0:
                #     print('change of plans',self.truck_index)
        _node_order = self.node_list.index(self.current_node)
        self.waiting_plan[_node_order:-1] = waiting_times



if __name__ == '__main__':
    test_nodes = [
        (18.02546160254861, 59.38157382906624), 
        (16.50658561538482, 58.28150384602444), 
        (16.48374131130608, 57.56893497161655), 
        (16.3883782476514, 56.9467696413148), 
        (16.32098233050319, 56.6727356017633)
        ]
    Test_truck = Truck(test_nodes,0)
    print(Test_truck.edge_list)