from datetime import datetime,timedelta

class GlobalClock:

    def __init__(self,start_time:datetime,step_ms:int,table_row_sec:int) -> None:
        self.start_time = start_time
        self.current_clk = self.start_time - timedelta(seconds=60) 

        self.cur_plan_base = self.current_clk - timedelta(seconds=table_row_sec)

    def clk_tick(self,step_ms:int):
        self.current_clk = self.current_clk + timedelta(milliseconds=step_ms)