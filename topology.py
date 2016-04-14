# -*- coding: utf-8 -*-
import fnss
from cache import cache
import networkx as nx
#from random import randint


def create_topology(self, PoP, k, h):
    topology = fnss.Topology()
    for core in range(PoP):
        tmp = fnss.k_ary_tree_topology(k, h)
        for node in tmp.node:
            if tmp.node[node]['type']<>'root':
                tmp.node[node]['server']=core*(k**(h+1)-1)
        tmp_tree = nx.relabel_nodes(tmp, {node:node+core*(k**(h+1)-1) for node in tmp.node})
        topology = nx.union(topology, tmp_tree)
        # Full mesh in the core of network
        for i in range(core):
            topology.edge[i*(k**(h+1)-1)][core*(k**(h+1)-1)] = {}
            topology.edge[core*(k**(h+1)-1)][i*(k**(h+1)-1)] = {}
            
    return topology


#class Topology(fnss.Topology):
#    def __init__(self, core, k, h, cache_budget):
#        cache_size = cache_budget/float(core*(k**h-1))
#        self.topology = self._create_topology(core, k, h)
#        self.clients = {node:self.topology.node[node] for node in self.topology.node \
#                        if self.topology.node[node]['type']=='leaf'}
#        self.pops = {node:self.topology.node[node] for node in self.topology.node \
#                        if self.topology.node[node]['type']=='root'}
#        self.routers = {node:self.topology.node[node] for node in self.topology.node \
#                        if self.topology.node[node]['type'] in ['leaf','intermediate']}
##        props = open('properties', 'r').readlines()
#        
#
#        self.content_store = {node:cache(cache_size) for node in self.topology.nodes_iter()}
#        self.informations = {node:{} for node in self.topology.nodes_iter()}
#        
#        
#    def _create_topology(self, PoP, k, h):
#        topology = fnss.Topology()
#        for core in range(PoP):
#            tmp = fnss.k_ary_tree_topology(k, h)
#            for node in tmp.node:
#                if tmp.node[node]['type']<>'leaf':
#                    tmp.node[node]['server']=core*(k**(h+1)-1)
#            tmp_tree = nx.relabel_nodes(tmp, {node:node+core*(k**(h+1)-1) for node in tmp.node})
#            topology = nx.union(topology, tmp_tree)
#            # Full mesh in the core of network
#            for i in range(core):
#                topology.edge[i*(k**(h+1)-1)][core*(k**(h+1)-1)] = {}
#                topology.edge[core*(k**(h+1)-1)][i*(k**(h+1)-1)] = {}
#                
#        return topology
#
#        
    
        
    