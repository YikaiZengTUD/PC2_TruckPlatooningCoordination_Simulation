
class GeoMap:

    def __init__(self) -> None:
        self.hub_list   = []
        self.edge_list  = []

        self.cur_truck_loc = {}

    def clear_loc_history(self) -> None:
        self.cur_truck_loc = {}

    def register_this_truck_position(self,truck_index:int,coordinates:tuple):
        if not coordinates == (0,0):
            self.cur_truck_loc[truck_index] = coordinates
