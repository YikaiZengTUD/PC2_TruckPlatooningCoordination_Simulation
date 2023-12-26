# -*- coding: utf-8 -*-

from map import GeoMap

if __name__ == '__main__':
    
    test_data = {
    0: [(16.21247986026327, 59.75805915309397), (16.06903491037792, 60.20902572311321),(16.32098233050319, 56.6727356017633)],
    1: [(18.02546160254861, 59.38157382906624), (16.50658561538482, 58.28150384602444), (16.48374131130608, 57.56893497161655), (16.3883782476514, 56.9467696413148), (16.32098233050319, 56.6727356017633)]
    } # small test data for debugging

    # Extract Map information from the OD pairs 
    M = GeoMap(test_data)

    # In the privacy preserving methods, a truck does not know anything about the 
    # potential parteners as they may belong to another fleet

    
    