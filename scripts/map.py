# -*- coding: utf-8 -*-

# This is the class defination file for the geographical map

class GeoMap:

    def __init__(self,map_coord:dict) -> None:
        self._x_list = []
        self._y_list = []
        self.build_map_from_coordinates(map_coord)
        self.task_dict_node = self.transfrom_task_list_to_hub_index(map_coord)
        self.edge_set = self.collect_edge_table_from_hubdict(self.task_dict_node)
        
    def collect_edge_table_from_hubdict(self,data:dict) -> set:
        edge_set = []
        for key_index in data.keys():
            _this_entry = data[key_index] # this is a list
            for itx,item in enumerate(_this_entry):
                if itx == 0:
                    continue
                else:
                    _this_origin      = _this_entry[itx-1]
                    _this_destination = item 
                    edge_set.append((_this_origin,_this_destination))
        return set(edge_set)
        

    def transfrom_task_list_to_hub_index(self,data:dict) -> dict:
        trans_data = {}
        for key_index in data.keys():
            _this_entry = data[key_index] # this is a list
            _this_node_list = []
            for _cordnates in _this_entry:
                _x = _cordnates[0]
                _y = _cordnates[1]
                _node_index = self._get_hub_index_from_cord(_x,_y)
                _this_node_list.append(_node_index)
                # print(_this_node_list)
            trans_data[key_index] = _this_node_list
        return trans_data

    def build_map_from_coordinates(self,data:dict):
        for key_index in data.keys():
            # check every truck index
            _this_entry = data[key_index] # this is a list
            for _cordnates in _this_entry:
                _x = _cordnates[0]
                _y = _cordnates[1]
                # check if this node has already been translated
                _find_repeat = False
                if _x in self._x_list:
                    _check_index = self._x_list.index(_x)
                    if type(_check_index) == int:
                        _check_index = [_check_index]
                    for _index in _check_index:
                        if _y == self._y_list[_index]:
                            # match with another node
                            _find_repeat = True
                            break
                    if _find_repeat:
                        continue
                    else:
                        self._x_list.append(_x)
                        self._y_list.append(_y)
                else:
                    self._x_list.append(_x)
                    self._y_list.append(_y)

    def _get_hub_index_from_cord(self,x:float,y:float) -> int:
        if x in self._x_list:
            index_list = self._x_list.index(x)
            if type(index_list) == int:
                index_list = [index_list] # in case of same x but differnt y
            for _index in index_list:
                if self._y_list[_index] == y:
                    # found a match
                    return _index
            print('Error in finding node index [y], returning error')
            return -1
        else:
            print('Error in finding node index [x], returning error')
            return -1
                    

if __name__ == '__main__':
    
    test_data = {
        0: [(16.21247986026327, 59.75805915309397), (16.06903491037792, 60.20902572311321),(16.32098233050319, 56.6727356017633)],
        1: [(18.02546160254861, 59.38157382906624), (16.50658561538482, 58.28150384602444), (16.48374131130608, 57.56893497161655), (16.3883782476514, 56.9467696413148), (16.32098233050319, 56.6727356017633)]
    }

    test_map = GeoMap(test_data)