# -*- coding: utf-8 -*-
#from topology import Topology
from workload import *
from random import shuffle
import fnss
import networkx as nx
#from cache import *

class Network():
    def __init__(self, core, k, h):
        self.CACHE_BUDGET_FRACTION = .04
        self.N_CONTENTS = 3*10**4
        self.N_WARMUP_REQUESTS = 3*10**5
        self.N_MEASURED_REQUESTS = 6*10**5
        self.GAMMA = .9
        self.ALPHA = .6
        self._cache_budget = (self.CACHE_BUDGET_FRACTION*self.N_CONTENTS)
        self.INTERNAL_COST = 2
        self.EXTERNAL_COST = 10
        
        # Uniform cache assignement
        
        self.topology = self._create_topology(core, k, h)
        self.clients = {node:self.topology.node[node] for node in self.topology.node \
                        if self.topology.node[node]['type']=='leaf'}
        self.pops = {node:self.topology.node[node] for node in self.topology.node \
                        if self.topology.node[node]['type']=='root'}
        self.routers = {node:self.topology.node[node] for node in self.topology.node \
                        if self.topology.node[node]['type'] in ['root','intermediate']}
        
#        cache_size = self._cache_budget/float(len(self.routers))
        #cast cache_size to int
#        self.cache = {node:Cache(int(cache_size)) for node in self.routers}
        self.cache = self.cache_placement()
        self.informations = {node:{} for node in self.topology.node}
        
#        self.topology = Topology(4, 2, 5, self._cache_budget)
        self.workload = StationaryWorkload(self.clients.keys(), self.N_CONTENTS, self.ALPHA, 
                                           n_warmup=self.N_WARMUP_REQUESTS,
                                           n_measured=self.N_MEASURED_REQUESTS)
        self.shortest_path = self.symmetrify_paths(nx.all_pairs_dijkstra_path(self.topology))
#        self.has_cache = {node:False for node in topology.nodes()}
#        self.caches = {node:[] for node in topology.nodes()}


        self.hits = 0
#        self.cache_hit = {node:{i:0 for i in range(1, 1+self.N_CONTENTS)} for node in self.topology.node}
#        self.delays = {i:[] for i in range(1, 1+self.N_CONTENTS)}


    def cache_placement(self):
        cache_budget = self._cache_budget
        betweenness = nx.betweenness_centrality(self.topology)
        total_betweenness = sum(betweenness.values())
#        for node in self.routers:
#            print int(round(cache_budget*betweenness[node]/float(total_betweenness)))
        return {node:Cache(int(round(cache_budget*betweenness[node]/float(total_betweenness))))\
                                for node in self.routers}
            
        
                                    
    def run(self):
        #TODO: separete warmup and test
        counter = 1
        for time, client, content in self.workload:
            if not counter%10000:
                print 'round %d' % counter
            counter += 1
            self.event_run(time, client, content, measured=counter>self.N_WARMUP_REQUESTS)
                                    
    def event_run(self, time, client, content, measured=True):
        path = self.shortest_path[client][self.clients[client]['server']]
        for node in path[1:]:
            delay = path.index(node)*self.INTERNAL_COST
            self.update_node_information(node, content, delay, time)
            if self.cache[node].has_content(content):
                if measured:
                    self.hits += 1
#                self.cache_hit[node][content] += 1
#                self.delay[content].append(delay)
#                print 'hit'
                break

            #if content cached in neighbors            
            neighbor = self._neighbors_has_content(node, content)
            if neighbor:
#                self.cache_hit[neighbor][content] += 1
                delay += [2,1][neighbor in self.topology.neighbors(node)]*self.INTERNAL_COST

                self.update_node_information(neighbor, content, delay, time)
                if measured:
                    self.hits += 1
#                    print 'hit'
#                    self.delays[content].append(delay)
                break
        #Cache miss and decision for cache placement
        else:
#            self.delays[content].append((len(path)-1)*self.INTERNAL_COST+self.EXTERNAL_COST)
            
            winner = self._winner_determination(path, content)
#            print winner
            self.cache[winner].put_content(content)


    def update_node_information(self, node, content, delay, time):
        if content in self.informations[node]:
            info = self.informations[node][content]
            popularity = info['popularity']
            average_delay = info['average_delay']
            last_req = info['last_req']
#            print self.informations[node][content]
#            print type(popularity)
            popularity = self.GAMMA**(time-last_req)*popularity + 1
            
#            beta = max( min(self.GAMMA**(time-last_req), .8), .1 )
            beta = .8
            if average_delay!=None:
                average_delay = (1-beta)*average_delay + beta*delay
            else:
                average_delay = delay
        else:
            popularity = 0
#            delay = 1
            average_delay = delay
#            last_req = time
#            neighbor_cache = []
        self.informations[node][content] = {'popularity':popularity,
                                            'average_delay':average_delay,
                                            'last_req':time}
        
    def _neighbors_of_neighbors(self, node):
        nodes = []
        for n in self.topology.neighbors(node):
            for neighbor in self.topology.neighbors(n):
                if self.topology.node[neighbor]['type'] in ['intermediate','core']:
                    nodes.append(neighbor)
            nodes.append(n)
        return list(set(nodes))
        
    def _neighbors_has_content(self, node, content):
        neighbors = self._neighbors_of_neighbors(node)
        for neighbor in neighbors:
            if self.cache[node].has_content(content):
                return neighbor
            
                
    def _winner_determination(self, path, content):
        max_val = 0
        winner = None
        for node in path:
            for v in self._neighbors_of_neighbors(node):
                if content in self.informations[v]:
                    popularity, average_delay, last_req = self.informations[v][content]
                    if popularity>max_val:
                        max_val = popularity
                        winner = v
        return winner

            
    def symmetrify_paths(self, shortest_paths): 
        for u in shortest_paths:
            for v in shortest_paths[u]:
                shortest_paths[u][v] = list(reversed(shortest_paths[v][u]))
        return shortest_paths
        
    
    def _create_topology(self, PoP, k, h):
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



class Cache():
    '''
    Cache with LRU for replacement
    '''
    def __init__(self, cache_size):
        self.contents = []
        self._len = 0
#        self._max_len = cache_size
        self._has_cache = True
        self.cache_size = cache_size
        
    def get_content(self, content):
        if content in self.contents:
            self.contents.remove(content)
            self.contents = [content]+self.contents
        else:
            return False
        
    def has_content(self, content):
        return content in self.contents if self.has_cache() else False

    def put_content(self, content):
        if content not in self.contents:
            self.contents = ([content]+self.contents)[:self.cache_size]
        else:
            self.get_content(content)

    def set_cache(self, cache_size):
        self.cache_size = cache_size
        self.set_cache = True
        
    def has_cache(self):
        return self._has_cache
        
    def get_cache_size(self):
        return self.cache_size
        
        
if __name__=='__main__':
    n = Network(3,2,4)
    n.run()