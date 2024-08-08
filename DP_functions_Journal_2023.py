# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 18:11:00 2023
Functions need to solve the platoon coordination problem using DP
 
    Truck Platooning:
    1. Initial DP Graph generation
    2. Sum the reward for every hub (does not include the destination (i.e., N-th hub ) and (N-1)-th hub)
    3. Add a new function: DMPC_DP_algorithm_app, which is used to compute the optimal solution of the problem using approximization

@author: tingbai
"""

#-------------------------------------------------------------------------------
'''1. — Generate DP graph for vehicle i at hub_k

(1-1). Function: divide the potential partners into different groups according to the same 't_d' '''

def data_td_groups(vehicle_jun_p_t, i, hub_k):
    
    l_hubs=list(vehicle_jun_p_t[i].keys()) # the list of hubs
    h_index=l_hubs.index(hub_k)                # the index of the current hub hub_k
    t_a=vehicle_jun_p_t[i][hub_k][1][i]['t_a'] # the arrival time of vehicle i at current hub
    
    hub_td_P={}
    hub_td_P[i]=[hub_k, t_a[0]]
    hub_td_P[i].append({})
    
    for h_k in range(h_index, len(l_hubs)):
        hub=l_hubs[h_k] # the coordinate of the hub
        hub_td_P[i][-1][hub]={}
        P_i=vehicle_jun_p_t[i][hub][0]
        for j in P_i:
            if j!=i:
                td_j=vehicle_jun_p_t[i][hub][1][j]['t_d'][0] # the departure time of truck j
                if td_j not in hub_td_P[i][-1][hub].keys():
                    hub_td_P[i][-1][hub][td_j]=[j]
                else:
                    hub_td_P[i][-1][hub][td_j].append(j)
    
    return hub_td_P       

#--------------------------------------------------------------------
'''(1-2). Function: add the arrival time at each hub for vehicle i'''

from datetime import timedelta
from dateutil.parser import parse

def data_add_ta(hub_td_P, OD_jun_travel, OD_jun_dict, i):
    
    v_hub_ta_td={}
    v_hub_ta_td[i]={}
    h_k_0=hub_td_P[i][0] # current hub (coordinate) on the route of vehicle i 
    h_k_end=list(hub_td_P[i][2].keys())[-1]
    t_a_0=hub_td_P[i][1] # the arrival time at current hub (str)
    
    for h_k in hub_td_P[i][2].keys():
        # add the dict information for the hub of h_k
        v_hub_ta_td[i][h_k]={}
        hub_id=OD_jun_dict[i].index(h_k) # the hub_index of "hub"
        
        # if "hub" is the current hub
        if h_k==h_k_0:
            t_a_h=t_a_0 # the arrival time at "hub"
            v_hub_ta_td[i][h_k][t_a_h]=hub_td_P[i][2][h_k]
            
            # add the departure time td=t_a_h --vehicle i leaves the hub alone
            if t_a_h not in v_hub_ta_td[i][h_k][t_a_h].keys(): # if there is no departure time = arrival time of vehicle i 
                v_hub_ta_td[i][h_k][t_a_h][t_a_h]=[i] 
    
            
        else:
            # 1. calculate the arrival time
            hub_ip=hub_id-1 # the previous hub
            t_w=OD_jun_travel[i][hub_ip][-1] # travel time from hub_ip to hub_id
            hub_p=OD_jun_dict[i][hub_ip] # coordinate of the previous hub
            
            # 2. add the arrival time
            for t_a in v_hub_ta_td[i][hub_p].keys():
                for t_d in v_hub_ta_td[i][hub_p][t_a].keys():
                    t_a_str=(parse(t_d)+timedelta(seconds=t_w)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
                    v_hub_ta_td[i][h_k][t_a_str]={}
            
            # if "hub" is the destination --then do not need to add the departure time
            if h_k==h_k_end:
                break
            else:
                # 3. add the departure times for each arrival time
                for t_a in v_hub_ta_td[i][h_k].keys():
                    for t_d in hub_td_P[i][2][h_k].keys():
                        if t_d>=t_a:
                            v_hub_ta_td[i][h_k][t_a][t_d]=hub_td_P[i][2][h_k][t_d]
                
                    # 4. add the departure time td=ta(i.e., vehicle i leaves alone) 
                    if t_a not in v_hub_ta_td[i][h_k][t_a].keys():
                        v_hub_ta_td[i][h_k][t_a][t_a]=[i]
                    
    #return v_hub_ta_td
    
 # sorted    time: small-->big
    # sorted ta
    v_hub_ta_td_s1={}
    v_hub_ta_td_s1[i]={}
    for h in v_hub_ta_td[i].keys():
        dic_ta=v_hub_ta_td[i][h]
        dic_ta_s=sorted(dic_ta.items(), key=lambda item:item[0])
        v_hub_ta_td_s1[i][h]=dict(dic_ta_s)
    # sorted td
    v_hub_ta_td_s2={}
    v_hub_ta_td_s2[i]={}
    for h in v_hub_ta_td_s1[i].keys():
        v_hub_ta_td_s2[i][h]={}
        for t_a in v_hub_ta_td_s1[i][h].keys():
            dic_td=v_hub_ta_td_s1[i][h][t_a]
            dic_td_s=sorted(dic_td.items(), key=lambda item:item[0])
            v_hub_ta_td_s2[i][h][t_a]=dict(dic_td_s)
                    
    return v_hub_ta_td_s2 # {v: {(hub): {ta:{td: [platoon partners]}}}}

#-------------------------------------------------------
''' (1-3). Function: remove the departure times that are earlier than the arrival time at the same hub'''
def remove_td_e(v_hub_ta_td_s2, i):
    v_hub_ta_td_s2_c=copy.deepcopy(v_hub_ta_td_s2)
    
    for h in v_hub_ta_td_s2[i].keys():
        for t_a in v_hub_ta_td_s2[i][h].keys():
            for t_d in v_hub_ta_td_s2[i][h][t_a].keys():
                if t_d<t_a:
                    del v_hub_ta_td_s2_c[i][h][t_a][t_d]
                    
    return v_hub_ta_td_s2_c
    
#-----------------------------------------------------------------------------------------------
''' (1-4). New Function: calculate the weight on each edge, i.e., the utility of joining one platoon or leaving alone 
           (revised: the fleet distribution is changed for multiple fleets)'''

def data_DP_graph_new(v_hub_ta_td_s2_c, OD_jun_travel, i):
    
    DP_graph={}
    DP_graph[i]={}
    #epsilon=0.07 #ser/s constant: waiting cost, i.e., 180sek/h
    #xi=0.016 # ser/s constant: platooning reward
    epsilon = 25/3600 # euro/sec
    xi = 5.6/3600     # euro/sec
    h_end=list(v_hub_ta_td_s2_c[i].keys())[-1] # the destination 
   
    
    # calculate the reward when joining different platoons
    # 1. define the fleet of a given vehicle
    def fleet_v(i):
    # vehicle 0-999, fleet 1-755
        f_i = 0
        if i <= 747:
            f_i = i + 1
        
        if i > 747 and i <= 750:
            f_i = 749
        
        if i > 750 and i <= 753:
            f_i = 750
        
        if i > 753 and i <= 768:
            f_i = 751
        
        if i > 768 and i <= 783:
            f_i = 752
        
        if i > 783 and i <= 817:
            f_i = 753
        
        if i > 817 and i <= 851:
            f_i = 754
        
        if i > 851:
            f_i = 755

        return f_i
        
    f_i=fleet_v(i) # the fleet that vehicle i belongs to
    
    
    # 2. calculate the reward of joining different platoons
    for h in v_hub_ta_td_s2_c[i].keys():
        DP_graph[i][h]={}
        if h!=h_end:
            t_travel=dict(OD_jun_travel[i])[h] # the travel time from hub h to the next hub--seconds
            for t_a in v_hub_ta_td_s2_c[i][h].keys():
                DP_graph[i][h][t_a]={}
                for t_d in v_hub_ta_td_s2_c[i][h][t_a].keys():
                    # the waiting cost
                    t_wait=(parse(t_d)-parse(t_a)).total_seconds()
                    cost=epsilon*t_wait
                
                    # --the reward
                    # calculate delta_fi
                    v_partners=v_hub_ta_td_s2_c[i][h][t_a][t_d]# the set of partners
                    b_norm=len(v_partners)# does not include i itself if b_norm>1
                    if b_norm>1:
                        v_other_f=[]
                        for v in v_partners:
                            f_v=fleet_v(v)
                            if f_v!=f_i:
                                v_other_f.append(v)
                        delta_fi=1-len(v_other_f)/((b_norm+1)*b_norm)
                        
                    if b_norm==1:
                        # the partner may be truck i itself
                        p=v_partners[0]
                        if p!=i:
                            f_p=fleet_v(p)
                            if f_p!=f_i:
                                delta_fi=1-1/((b_norm+1)*b_norm) # the single partner is a truck from a different fleet 
                            else:
                                delta_fi=1 # the single partner comes from the same fleet with truck i
                        else:
                            delta_fi=0 # truck i leaves alone
                    
                        
                    # calculate the reward
                    reward=xi*t_travel*delta_fi
                
                    # utility
                    w=reward-cost
                    DP_graph[i][h][t_a][t_d]=[v_partners, round(w,4)]
        else:
            DP_graph[i][h]=v_hub_ta_td_s2_c[i][h]
                
    return DP_graph


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
'''2 . — Function 2: Solve the DMPC problem for each decision maker, i.e., the MINLP problem'''         
  
import copy
import numpy as np

def DMPC_DP_algorithm(DP_graph, i, h, h_end, t_dd, OD_jun_travel):
    
    ''' — sub-function 2-1: remove the infeasible t_a from destination'''
    def remove_infeasible_ta(DP_graph, i, h_end, t_dd):
        # DP_graph: given information of vehicle i
        # h_end: coordinate of the destination
        # t_dd: the delivery deadline at the destination
        DP_graph_f1=copy.deepcopy(DP_graph)
        for t_a in DP_graph[i][h_end].keys():
            t_diff=(parse(t_dd)-parse(t_a)).total_seconds()# may be too strict
            if t_diff<0:
                del DP_graph_f1[i][h_end][t_a]
            
        return DP_graph_f1
    #--------------------------------------------------------------------------
    
    ''' — sub-function 2-2: obtain the feasible (ta,td) pairs for every hub'''
    def feasible_p(DP_graph, i, h, DP_ta_td_f, OD_jun_travel): 
        # DP_ta_td_f:  the feasible (ta,td) at next hub, i.e., hub h+1
    
        DP_graph_F={}
        DP_graph_F[i]={}
        DP_graph_F[i][h]={}
    
        t_w=dict(OD_jun_travel[i])[h]# the travel time from hub h to hub h+1
        td_feasible=[]
    
        for t_a in DP_ta_td_f.keys():
            t_d=(parse(t_a)-timedelta(seconds=t_w)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
            td_feasible.append(t_d) # all the feasible departure times for hub h
        
        # 1. remove the infeasible t_d
        for t_a in DP_graph[i][h].keys():
            DP_graph_F[i][h][t_a]={}
            for t_d in DP_graph[i][h][t_a].keys():
                for t_d_f in td_feasible:
                    t_diff=np.array((parse(t_d)-parse(t_d_f)).total_seconds())
                    t_diff_norm=np.linalg.norm(t_diff, ord=None)
                    if (t_diff_norm<3):
                        DP_graph_F[i][h][t_a][t_d]=DP_graph[i][h][t_a][t_d]
    
        # 2. remove the infeasible t_a
        DP_graph_F_p=copy.deepcopy(DP_graph_F)
        for t_a in DP_graph_F[i][h].keys():
            if DP_graph_F[i][h][t_a]=={}:
                del DP_graph_F_p[i][h][t_a]
    
        return DP_graph_F_p # {v_i: {(h): {ta: {td: [[partners],utility],td2:...}, ta2: ...}}}
    #--------------------------------------------------------------------------
    ''' — sub-function 2-3: sum the utility for td'''
    def utility_sum_td(opt_dec_v, v_hub_ta_td_f, i, h, h_next, t_w):
        # opt_dec_v: the optimal decision at hub h_next
        # v_hub_ta_td_f: the feasible (ta,td) pairs at hub h
        # h: current hub
        # h_next: next hub (coordinate)
        # OD_jun_travel: used to find the travel time from hub h to hub h_next --from system model
        
        u_sum_td={}
        u_sum_td[i]={}
        u_sum_td[i][h]={}
        ta_td_fc=copy.deepcopy(v_hub_ta_td_f[i][h])
        
        for t_a in v_hub_ta_td_f[i][h].keys():
            for t_d in v_hub_ta_td_f[i][h][t_a].keys():
                # calculate the arrival time at hub h_next, according to t_d at current hub h
                ta_next=(parse(t_d)+timedelta(seconds=t_w)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2] #Notice: may not be accurate!!!!!
                u_to_add=list(opt_dec_v[i][h_next][ta_next].values())[0][-1] # the utility to be added, the departure times may be different, but the utility is the same 
                ta_td_fc[t_a][t_d][-1]=round(v_hub_ta_td_f[i][h][t_a][t_d][-1]+u_to_add,4) # update the utility for ta
        
        u_sum_td[i][h]=ta_td_fc
        
        return u_sum_td # {i: {(hub): {ta: {td: [[partners, utility]]}}}}
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------
    ''' — sub-function 2-4: determine the optimal solution'''
    def optimal_dec(v_hub_ta_td_f, i, h):
        # Input: v_hub_ta_td_f: the feasible (ta,td) pairs at hub h
        
        opt_dec_v={} # the optimal decision at hub h
        opt_dec_v[i]={}
        opt_dec={}
        v_hub_ta_td_fc=copy.deepcopy(v_hub_ta_td_f)
        
        # find the optimal departure time for ta
        for t_a in v_hub_ta_td_fc[i][h].keys():
            all_td=v_hub_ta_td_fc[i][h][t_a] # all the possible departure times corresponding to t_a
            all_td_o=sorted(all_td.items(), key=lambda x:x[1][-1], reverse=True) # the ordered utility
            
            # choose the maximized solutions (may not be unique)
            all_td_od=dict(all_td_o) # change tuple into dict
            max_utility_td={} # the departure times whoes utility is maximized
            for t_d in all_td_od.keys():
                if max_utility_td=={}:
                    max_utility_td[t_d]=all_td_od[t_d]
                else:
                    u=all_td_od[t_d][-1] # the utility
                    t_d2=list(max_utility_td.keys())[0] # the first key
                    u0=max_utility_td[t_d2][-1] # the utility of t_d2
                    if u==u0:
                        max_utility_td[t_d]=all_td_od[t_d] # add other solutions with the same utility
                    else:
                        break # otherwise, u<u0, break
            opt_dec[t_a]=max_utility_td
            
        opt_dec_v[i][h]=opt_dec
        
        return opt_dec_v # {i:{hub: {t_a: {t_d: [[partners], utility]}}}}
    #--------------------------------------------------------------------------
    
    ''' — Main Loop: DP Algorithm'''
     
    h_set=list(DP_graph[i].keys())[::-1] # the set of hubs of vehicle i(the inversed order), the last one--to--the current hub
    
    # —— Step 1. obtain the feasible (ta, td) pairs
    v_hub_ta_td={} # all the feasible (ta,td) pairs at hubs of vehicle i
    v_hub_ta_td[i]={}
    for hub in h_set:
        if hub==h_end:
            DP_graph_fd=remove_infeasible_ta(DP_graph, i, h_end, t_dd)
            v_hub_ta_td[i][hub]=DP_graph_fd[i][hub]
        else:
            h_pre=h_set[h_set.index(hub)-1] # the next hub
            DP_graph_fk=feasible_p(DP_graph, i, hub, v_hub_ta_td[i][h_pre], OD_jun_travel)
            v_hub_ta_td[i][hub]=DP_graph_fk[i][hub]
            
    del v_hub_ta_td[i][h_end]# remove the information of destination (inversed order)
    
    # —— Step 2. find the optimal decision at each hub for each arrival time
    
    Opt_decision={} # the final optimal decision
    Opt_decision[i]={}
    v_hub_ta_td_c=copy.deepcopy(v_hub_ta_td) # the feasible (ta,td) pairs are dynamically updated during the computation
    h_n_pre=h_set[h_set.index(h_end)+1] # the hub before the destination
    
    for hub in v_hub_ta_td[i].keys():
        
        # (1). update the utility of t_d at hub N-1
        if hub==h_n_pre: # the hub before the destination
            # find the optimal solution
            opt_dec_v=optimal_dec(v_hub_ta_td, i, hub)
            
        else:
            # sum the utility of current and next hub for td
            hub_next=h_set[h_set.index(hub)-1]
            t_w=dict(OD_jun_travel[i])[hub]
            td_new=utility_sum_td(opt_dec_v, v_hub_ta_td, i, hub, hub_next, t_w) # add the utility of next hub
            
            # update the utility in v_hub_ta_td_c
            v_hub_ta_td_c[i][hub]=td_new[i][hub]
            # find the optimal solution
            opt_dec_v=optimal_dec(v_hub_ta_td_c, i, hub)
        # update the decision dictory
        Opt_decision[i][hub]=opt_dec_v[i][hub] # the hub has an inversed order !!!
        
    # sort the order of hubs
    Opt_decision_v={}
    Opt_decision_v[i]={}
    for h in DP_graph[i].keys():
        if h!=h_end:
            Opt_decision_v[i][h]=Opt_decision[i][h]
            
    # sort the order of t_a
    Opt_decision_f={}
    Opt_decision_f[i]={}
    for h in Opt_decision_v[i].keys():
        Opt_decision_f[i][h]={}
        Opt_decision_f[i][h]=dict(sorted(Opt_decision_v[i][h].items(), key=lambda x:x[0]))
        
    # sort the order of t_d
    Opt_decision_s={}
    Opt_decision_s[i]={}
    for h in Opt_decision_f[i].keys():
        Opt_decision_s[i][h]={}
        for t_a in Opt_decision_f[i][h].keys():
            Opt_decision_s[i][h][t_a]={}
            Opt_decision_s[i][h][t_a]=dict(sorted(Opt_decision_f[i][h][t_a].items(), key=lambda x:x[0]))
            
    return Opt_decision_s
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
'''3 . — Function 3: Solve the DMPC problem for each decision maker using DP with approximization'''         

def DMPC_DP_algorithm_app(DP_graph, i, h, h_end, t_dd, OD_jun_travel, OD_jun_dict):
    
    ''' — sub-function 3-1: remove the infeasible t_a from destination'''
    def remove_infeasible_ta(DP_graph, i, h_end, t_dd):
        # DP_graph: given information of vehicle i
        # h_end: coordinate of the destination
        # t_dd: the delivery deadline at the destination
        DP_graph_f1=copy.deepcopy(DP_graph)
        for t_a in DP_graph[i][h_end].keys():
            t_diff=(parse(t_dd)-parse(t_a)).total_seconds()# may be too strict
            if t_diff<0:
                del DP_graph_f1[i][h_end][t_a]
            
        return DP_graph_f1
    #--------------------------------------------------------------------------
    
    ''' — sub-function 3-2: obtain the feasible (ta,td) pairs for every hub'''
    def feasible_p(DP_graph, i, h, DP_ta_td_f, OD_jun_travel): 
        # DP_ta_td_f:  the feasible (ta,td) at next hub, i.e., hub h+1
    
        DP_graph_F={}
        DP_graph_F[i]={}
        DP_graph_F[i][h]={}
    
        t_w=dict(OD_jun_travel[i])[h]# the travel time from hub h to hub h+1
        td_feasible=[]
    
        for t_a in DP_ta_td_f.keys():
            t_d=(parse(t_a)-timedelta(seconds=t_w)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
            td_feasible.append(t_d) # all the feasible departure times for hub h
        
        # 1. remove the infeasible t_d
        for t_a in DP_graph[i][h].keys():
            DP_graph_F[i][h][t_a]={}
            for t_d in DP_graph[i][h][t_a].keys():
                for t_d_f in td_feasible:
                    t_diff=np.array((parse(t_d)-parse(t_d_f)).total_seconds())
                    t_diff_norm=np.linalg.norm(t_diff, ord=None)
                    if (t_diff_norm<3):
                        DP_graph_F[i][h][t_a][t_d]=DP_graph[i][h][t_a][t_d]
    
        # 2. remove the infeasible t_a
        DP_graph_F_p=copy.deepcopy(DP_graph_F)
        for t_a in DP_graph_F[i][h].keys():
            if DP_graph_F[i][h][t_a]=={}:
                del DP_graph_F_p[i][h][t_a]
    
        return DP_graph_F_p # {v_i: {(h): {ta: {td: [[partners],utility],td2:...}, ta2: ...}}
    #--------------------------------------------------------------------------
    
    ''' — sub-function 3-3: sum the utility for td'''
    def utility_sum_td(opt_dec_v, v_hub_ta_td_f, i, h, h_next, t_w):
        # opt_dec_v: the optimal decision at hub h_next
        # v_hub_ta_td_f: the feasible (ta,td) pairs at hub h
        # h: current hub
        # h_next: next hub (coordinate)
        # OD_jun_travel: used to find the travel time from hub h to hub h_next --from system model
        
        u_sum_td={}
        u_sum_td[i]={}
        u_sum_td[i][h]={}
        ta_td_fc=copy.deepcopy(v_hub_ta_td_f[i][h])
        
        for t_a in v_hub_ta_td_f[i][h].keys():
            for t_d in v_hub_ta_td_f[i][h][t_a].keys():
                # calculate the arrival time at hub h_next, according to t_d at current hub h
                ta_next=(parse(t_d)+timedelta(seconds=t_w)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2] #Notice: may not be accurate!!!!!
                u_to_add=list(opt_dec_v[i][h_next][ta_next].values())[0][-1] # the utility to be added, the departure times may be different, but the utility is the same 
                ta_td_fc[t_a][t_d][-1]=round(v_hub_ta_td_f[i][h][t_a][t_d][-1]+u_to_add,4) # update the utility for ta
        
        u_sum_td[i][h]=ta_td_fc
        
        return u_sum_td # {i: {(hub): {ta: {td: [[partners, utility]]}}}}
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------
    ''' — sub-function 3-4: determine the optimal solution'''
    def optimal_dec(v_hub_ta_td_f, i, h):
        # Input: v_hub_ta_td_f: the feasible (ta,td) pairs at hub h
        
        opt_dec_v={} # the optimal decision at hub h
        opt_dec_v[i]={}
        opt_dec={}
        v_hub_ta_td_fc=copy.deepcopy(v_hub_ta_td_f)
        
        # find the optimal departure time for ta
        for t_a in v_hub_ta_td_fc[i][h].keys():
            all_td=v_hub_ta_td_fc[i][h][t_a] # all the possible departure times corresponding to t_a
            all_td_o=sorted(all_td.items(), key=lambda x:x[1][-1], reverse=True) # the ordered utility
            
            # choose the maximized solutions (may not be unique)
            all_td_od=dict(all_td_o) # change tuple into dict
            max_utility_td={} # the departure times whoes utility is maximized
            for t_d in all_td_od.keys():
                if max_utility_td=={}:
                    max_utility_td[t_d]=all_td_od[t_d]
                else:
                    u=all_td_od[t_d][-1] # the utility
                    t_d2=list(max_utility_td.keys())[0] # the first key
                    u0=max_utility_td[t_d2][-1] # the utility of t_d2
                    if u==u0:
                        max_utility_td[t_d]=all_td_od[t_d] # add other solutions with the same utility
                    else:
                        break # otherwise, u<u0, break
            opt_dec[t_a]=max_utility_td
            
        opt_dec_v[i][h]=opt_dec
        
        return opt_dec_v # {i:{hub: {t_a: {t_d: [[partners], utility]}}}}
    #--------------------------------------------------------------------------
    
    ''' — Main Loop: DP Algorithm with approximization'''
     
    h_set=list(DP_graph[i].keys())[::-1] # the set of hubs of vehicle i(the inversed order), the last one--to--the current hub
    # —— Step 1. obtain the feasible (ta, td) pairs
    v_hub_ta_td={} # all the feasible (ta,td) pairs at hubs of vehicle i
    v_hub_ta_td[i]={}
    for hub in h_set:
        if hub==h_end:
            DP_graph_fd=remove_infeasible_ta(DP_graph, i, h_end, t_dd)
            v_hub_ta_td[i][hub]=DP_graph_fd[i][hub]
        else:
            h_pre=h_set[h_set.index(hub)-1] # the next hub
            DP_graph_fk=feasible_p(DP_graph, i, hub, v_hub_ta_td[i][h_pre], OD_jun_travel)
            v_hub_ta_td[i][hub]=DP_graph_fk[i][hub] # all the feasible (ta,td) pairs at hubs 
            
    del v_hub_ta_td[i][h_end]# remove the information of destination (the hubs have an inversed order)
    
    # —— Step 2-1. remove the partners after the hub k, k+1, and k+2, i.e., only consider the platooning opportunities at 3 hubs
    n_hub=len(v_hub_ta_td[i].keys())-2 # the number of hubs whose partners need to be removed; -2, only consider two hubs
    hub_to_remove=list(v_hub_ta_td[i].keys())[0:n_hub] # the coordination of the hubs to be removed
    v_hub_ta_td_app=copy.deepcopy(v_hub_ta_td)
    for hub in hub_to_remove:
        for ta in v_hub_ta_td[i][hub].keys():
            for td in v_hub_ta_td[i][hub][ta].keys():
                if td!=ta: # Note that: for td==ta, the partner-set can be non-empty, i.e., although t_wait=0, the reward may be larger than 0
                    del v_hub_ta_td_app[i][hub][ta][td]
                    
    # —— Step 2-2. remove the arrival time at the following hubs that has no corresponding departure times.
    v_hub_ta_td_app2=copy.deepcopy(v_hub_ta_td_app)
    
    # remove the arrival times having no corresponding departure times at the previous hub
    td_hub={}
    td_hub[i]={}
    for hub in hub_to_remove[::-1]:
        if hub==hub_to_remove[::-1][0]:
            tds=[]
            for ta in v_hub_ta_td_app[i][hub].keys():
                tds.append(list(v_hub_ta_td_app[i][hub][ta].keys())[0])
            td_hub[i][hub]=tds
            
        else:
            index_h_p=OD_jun_dict[i].index(hub)-1 # the index of the previous hub
            hub_p=OD_jun_dict[i][index_h_p] # the coordination of the previous hub
            t_s=OD_jun_travel[i][index_h_p][-1] # the travel time from hub_p to hub
            tds_p=td_hub[i][hub_p] # the departure times at hub_p           
            # remove the arrival times that have no corresponding departure times at hub_p
            tas_h=[] # the arrival times at hub 
            tds_h=[]# the departure times at current hub
            for td in tds_p:
                ta_h=(parse(td)+timedelta(seconds=t_s)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2] # the arrival time at current hub
                tas_h.append(ta_h)
                
            for ta in v_hub_ta_td_app[i][hub].keys():
                if ta not in tas_h:
                    del v_hub_ta_td_app2[i][hub][ta] # remove ta
                    
            for ta in v_hub_ta_td_app2[i][hub].keys():
                tds_h.append(list(v_hub_ta_td_app2[i][hub][ta].keys())[0])
            td_hub[i][hub]=tds_h
            # v_hub_ta_td_app2 is the final DP graph with approximization
    
        
    # —— Step 3. find the optimal decision at each hub for each arrival time
    
    Opt_decision={} # the final optimal decision
    Opt_decision[i]={}
    v_hub_ta_td_c=copy.deepcopy(v_hub_ta_td_app2) # the feasible (ta,td) pairs are dynamically updated during the computation
    h_n_pre=h_set[h_set.index(h_end)+1] # the hub before the destination
    
    for hub in v_hub_ta_td_app2[i].keys():
        
        # (1). update the utility of t_d at hub N-1
        if hub==h_n_pre: # the hub before the destination
            # find the optimal solution
            opt_dec_v=optimal_dec(v_hub_ta_td_app2, i, hub)
            
        else:
            # sum the utility of current and next hub for td
            hub_next=h_set[h_set.index(hub)-1]
            t_w=dict(OD_jun_travel[i])[hub]
            td_new=utility_sum_td(opt_dec_v, v_hub_ta_td_app2, i, hub, hub_next, t_w) # add the utility of next hub
            
            # update the utility in v_hub_ta_td_c
            v_hub_ta_td_c[i][hub]=td_new[i][hub]
            # find the optimal solution
            opt_dec_v=optimal_dec(v_hub_ta_td_c, i, hub)
        # update the decision dictory
        Opt_decision[i][hub]=opt_dec_v[i][hub] # the hub has an inversed order !!!
        
    # sort the order of hubs
    Opt_decision_v={}
    Opt_decision_v[i]={}
    for h in DP_graph[i].keys():
        if h!=h_end:
            Opt_decision_v[i][h]=Opt_decision[i][h]
            
    # sort the order of t_a
    Opt_decision_f={}
    Opt_decision_f[i]={}
    for h in Opt_decision_v[i].keys():
        Opt_decision_f[i][h]={}
        Opt_decision_f[i][h]=dict(sorted(Opt_decision_v[i][h].items(), key=lambda x:x[0]))
        
    # sort the order of t_d
    Opt_decision_s={}
    Opt_decision_s[i]={}
    for h in Opt_decision_f[i].keys():
        Opt_decision_s[i][h]={}
        for t_a in Opt_decision_f[i][h].keys():
            Opt_decision_s[i][h][t_a]={}
            Opt_decision_s[i][h][t_a]=dict(sorted(Opt_decision_f[i][h][t_a].items(), key=lambda x:x[0]))
            
    return Opt_decision_s

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
'''4. — Function 4: Calculate the optimal state (x) and input (u,i.e., waiting time) at the following hubs according to Opt_decision_v''' 

def Solution_org(Opt_decision_s, OD_jun_travel, OD_jun_dict):
    # define the optimal arrival time, waiting time and departure time of vehicle i

    x_opt=[]
    y_opt=[]
    u_opt=[]
    
    i=list(Opt_decision_s.keys())[0] # vehicle i
    Opt_decision_org={}
    Opt_decision_org[i]={}
    h_cur=list(Opt_decision_s[i].keys())[0] # coordinate of the current hub
    
    # -- 1. Inalization
    ta_h_cur=list(Opt_decision_s[i][h_cur].keys())[0] # only one arrival time at the current hub
    td_h_cur=list(Opt_decision_s[i][h_cur][ta_h_cur].keys())[0] # the optimal departure time from hub h_cur
     
    # -- 2. The utility:
    J_i=list(Opt_decision_s[i][h_cur][ta_h_cur].values())[0][-1]

        
    # -- 3. Calculate the optimal arrival time x_opt, waiting time u_opt, and departure time y_opt:
    for hub in Opt_decision_s[i].keys():
        Opt_decision_org[i][hub]=[]
        if hub==h_cur:
            t_a=ta_h_cur
            t_d=td_h_cur
            
        else:
            hub_index=list(Opt_decision_s[i].keys()).index(hub)
            hub_pre=list(Opt_decision_s[i].keys())[hub_index-1]
            t_d_pre=Opt_decision_org[i][hub_pre][1] 
            t_w=dict(OD_jun_travel[i])[hub_pre] # the travel time from previous hub to current hub 
            t_a=(parse(t_d_pre)+timedelta(seconds=t_w)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
            # the same t_a may have different t_d that have the same utility, here we choose the earliest one
            t_d=list(Opt_decision_s[i][hub][t_a].keys())[0]
            
        t_u=(parse(t_d)-parse(t_a)).total_seconds()
        v_uti=Opt_decision_s[i][hub][t_a][t_d] # the partners and the correponding utility
        
        x_opt.append(t_a)
        y_opt.append(t_d)
        u_opt.append(t_u)
        Opt_decision_org[i][hub].append(t_a)
        Opt_decision_org[i][hub].append(t_d)
        Opt_decision_org[i][hub].append(v_uti)
    
    # add the arrival time at the destination
    hub_end=OD_jun_dict[i][-1] # destination
    hub_end_p=list(Opt_decision_s[i].keys())[-1]
    t_d_p=Opt_decision_org[i][hub_end_p][1]
    t_w_d=dict(OD_jun_travel[i])[hub_end_p]
    t_a_end=(parse(t_d_p)+timedelta(seconds=t_w_d)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
    # add the state
    x_opt.append(t_a_end)
    # add the information in Opt_decision_org
    Opt_decision_org[i][hub_end]=[t_a_end]
    
        
    return x_opt, u_opt, y_opt, J_i, Opt_decision_org
