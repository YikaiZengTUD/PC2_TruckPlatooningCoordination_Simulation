# -*- coding: utf-8 -*-

# In this file we define a virtual global clock that starts at the earliest departure time

from datetime import datetime, timedelta

class VirtualGlobalClock:

    def __init__(self,start_clk:datetime) -> None:
        self.start_clk      = start_clk
        self.current_clk    = self.start_clk
        print("Initlization: Virtual Clock initialized at ",start_clk.strftime("%Y-%m-%d %H:%M:%S"))
        pass

    def clock_step_plus_ms(self,time_increment_ms:int):
        self.current_clk = self.current_clk + timedelta(microseconds=time_increment_ms)
    