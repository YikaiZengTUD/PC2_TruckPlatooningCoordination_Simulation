# -*- coding: utf-8 -*-

# In this file we define a virtual global clock that starts at the earliest departure time

from datetime import datetime, timedelta
import numpy as np

class VirtualGlobalClock:

    def __init__(self,start_clk:datetime) -> None:
        self.start_clk      = start_clk
        self.current_clk    = self.start_clk
        print("Initialization: Virtual Clock initialized at",start_clk.strftime("%Y-%m-%d %H:%M:%S"))

    def clock_step_plus_ms(self,time_increment_ms:int):
        self.current_clk = self.current_clk + timedelta(microseconds=time_increment_ms*1000)
    
    def clock_step_minus_ms(self,time_decrement_ms:int):
        self.current_clk = self.current_clk - timedelta(microseconds=time_decrement_ms*1000)
