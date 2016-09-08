# -*- coding: utf-8 -*-
from random import shuffle, random, choice, randint
import fnss
import networkx as nx
import numpy as np


class Topology(object):
    def __init__(self, status):
        
        self.status = status
        
        self.INTERNAL_COST = self.status.INTERNAL_COST
        self.EXTERNAL_COST = self.status.EXTERNAL_COST
        
        self.core = self.status.core
        self.k = self.status.k
        self.h = self.status.h
        
        self.max_delay = self.h * self.INTERNAL_COST + self.EXTERNAL_COST

        if self.status.topo_type == 'tree':
            self.topology = self._create_topology(self.core, self.k, self.h)
        elif self.status.topo_type == 'rocket':
            self.topology = self._parse_rocketfuel_topology()
        
        self.clients = {node: self.topology.node[node] for node in self.topology.node
                        if self.topology.node[node]['type'] == 'leaf'}
        self.pops = {node: self.topology.node[node] for node in self.topology.node
                     if self.topology.node[node]['type'] == 'root'}
        self.routers = {node: self.topology.node[node] for node in self.topology.node
                        if self.topology.node[node]['type'] in ['root', 'intermediate']}        
        
        self.shortest_path = self._symmetrify_paths(nx.all_pairs_dijkstra_path(self.topology))
        self.neighbors2 = {node: self._neighbors_of_neighbors(node) for node in self.topology.node}


    def _create_topology(self, core, k, h):
        topology = fnss.Topology()
        for core in range(core):
            tmp = fnss.k_ary_tree_topology(k, h)
            for node in tmp.node:
                if tmp.node[node]['type'] <> 'root':
                    tmp.node[node]['server'] = core * (k ** (h + 1) - 1)
            tmp_tree = nx.relabel_nodes(tmp, {node: node + core * (k ** (h + 1) - 1) for node in tmp.node})
            topology = nx.union(topology, tmp_tree)
            # Full mesh in the core of network
            for i in range(core):
                topology.edge[i * (k ** (h + 1) - 1)][core * (k ** (h + 1) - 1)] = {}
                topology.edge[core * (k ** (h + 1) - 1)][i * (k ** (h + 1) - 1)] = {}

        return topology
        
    def _parse_rocketfuel_topology(self):
        topo = fnss.parse_rocketfuel_isp_map('3257.r0.cch').to_undirected()
        degree = nx.degree(topo)
        server, = [i for i in degree if degree[i]==max(degree.values())]
        topo.node[server]['type'] = 'root'
        
        edges = [i for i in degree if degree[i]==1]        
        for i in edges:
            topo.node[i]['type'] = 'leaf'
            
        for i in topo.node.keys():
            topo.node[i]['server'] = server
            if i not in edges and i is not server:
                topo.node[i]['type'] = 'intermediate'

        return topo


    def _symmetrify_paths(self, shortest_paths):
        for u in shortest_paths:
            for v in shortest_paths[u]:
                shortest_paths[u][v] = list(reversed(shortest_paths[v][u]))
        return shortest_paths

    def _neighbors_of_neighbors(self, node):
        """

        Parameters
        ----------
        node

        Returns
        -------
        2 level neighbors of node
        """
        nodes = []
        for n in self.topology.neighbors(node):
            if self.topology.node[n]['type'] is not 'leaf':
                for neighbor in self.topology.neighbors(n):
                    if self.topology.node[neighbor]['type'] is 'intermediate':
                        nodes.append(neighbor)
                # if self.topology.node[n]['type'] is not 'leaf':
                nodes.append(n)
        # if node in nodes:
        #     nodes.remove(node)
        nodes.append(node)
        neighbors = list(set(nodes))
        shuffle(neighbors)
        return neighbors


    def place_caches(self):
        cache_budget = self.status.CACHE_BUDGET_FRACTION * self.status.N_CONTENTS
        if self.status.cache_placement == 'betweenness':
            betweenness = nx.betweenness_centrality(self.topology)
        elif self.status.cache_placement == 'uniform':
            betweenness = {node: 1. for node in self.routers}
        total_betweenness = float(sum(betweenness.values()))
#        print self.status.cache_replacement
        return {node: Cache(int(round(cache_budget * betweenness[node] / total_betweenness)), self.status, node)
                for node in self.routers}
                    

    def reset_topology(self):
        if self.status.topo_type == 'tree':
            self.topology = self._create_topology(self.core, self.k, self.h)
        elif self.status.topo_type == 'rocket':
            self.topology = self._parse_rocketfuel_topology()
        
        self.clients = {node: self.topology.node[node] for node in self.topology.node
                        if self.topology.node[node]['type'] == 'leaf'}
        self.pops = {node: self.topology.node[node] for node in self.topology.node
                     if self.topology.node[node]['type'] == 'root'}
        self.routers = {node: self.topology.node[node] for node in self.topology.node
                        if self.topology.node[node]['type'] in ['root', 'intermediate']}        
        
        self.shortest_path = self._symmetrify_paths(nx.all_pairs_dijkstra_path(self.topology))
        self.neighbors2 = {node: self._neighbors_of_neighbors(node) for node in self.topology.node}
        self.place_caches()


class Cache(object):
    """
    Cache with LRU for replacement
    """

    def __init__(self, cache_size, status, node):
        self.status = status
        if self.status.cache_replacement == 'LRU':
            self.contents = []#{}
        elif self.status.cache_replacement == 'POP':
            self.contents = {}
#        self._len = 0
#        self._max_len = cache_size
        self._has_cache = True
        self.cache_size = cache_size
        self.min_popularity = 0
        self.min_content = None
        self.node = node
#        self.info = info

    def get_content(self, content):
        if self.status.cache_replacement == 'LRU':
            if content in self.contents:
                self.contents.remove(content)
                self.contents = [content] + self.contents
        else:
            return False

    def has_content(self, content):
        return content in self.contents if self.has_cache() else False

    def put_content(self, content):
        if self.status.cache_replacement == 'LRU':
            if content not in self.contents:
                self.contents = ([content] + self.contents)[:self.cache_size]
            else:
                self.get_content(content)
                
        elif self.status.cache_replacement == 'POP' and self.status.scenario is 'AUC':
#            self.min_popularity = self.contents
            for c in self.contents.keys() + [content]:
                pop = self.status.information[self.node][c]['popularity']
                self.contents[c] = pop
#                if pop < self.min_popularity:
#                    self.min_popularity = pop
#                    self.min_content = c
            
            self.min_popularity = min(self.contents.values())
            if len(self.contents) > self.cache_size:                
                min_content = [k for k, v in self.contents.items() if v==self.min_popularity][0]
                del self.contents[min_content]#self.contents[min_content]
#                    if popularity[0] > self.min_popularity:
                self.min_popularity = min(self.contents.values())
            
    def set_cache(self, cache_size):
        self.cache_size = cache_size
        self.has_cache = True

    def has_cache(self):
        return self._has_cache

    def get_cache_size(self):
        return self.cache_size

    def get_replace_candidate(self):
        if self.status.cache_replacement == 'LRU':
            return self.contents[-1] if len(self.contents) == self.cache_size else None
        elif self.status.cache_replacement == 'POP':
            if len(self.contents) == self.cache_size:
                for c in self.contents.keys():
                    pop = self.status.information[self.node][c]['popularity']
                    self.contents[c] = pop
#                    if pop < self.min_popularity:
#                        self.min_popularity = pop
#                        self.min_content = c
                self.min_popularity = min(self.contents.values())
                return [k for k, v in self.contents.items() if v==self.min_popularity][0]
            else:
                return None

        
class Workload(object):
    def __init__(self, clients, n_contents, alpha, n_warmup, n_measured):
        self.clients = clients
        self.n_contents = n_contents
        self.contents = range(1, n_contents+1)
        self.alpha = alpha
        self.n_warmup = n_warmup
        self.n_measured = n_measured
        
        self.pdf = (np.arange(1.,self.n_contents+1.)**-self.alpha)
        self.pdf /= np.sum(self.pdf)
        self.cdf = np.cumsum(self.pdf)
        
    def _get_zipf(self):
        rnd = random()
        return np.searchsorted(self.cdf, rnd)+1
    
    def __iter__(self):
        req_counter = 0
        t_event = 0.0
        while req_counter < self.n_warmup + self.n_measured:
#            t_event += (random.expovariate(self.rate))
            t_event += 1
            ## for spatial locality
#            if not t_event % 10000:
#                r = randint(0, len(self.clients))
#                self.clients = self.clients[r:]+self.clients[:r]
#
#            client = self.clients[int(min(max(random.gauss(len(self.clients)/2, len(self.clients)/3), 0), len(self.clients)-1))]
            client = choice(self.clients)
            content = int(self._get_zipf())
#            client = 30
#            content = 0
#            event = {'client':client, 'content': content}
            yield (t_event, client, content)
            req_counter += 1
        raise StopIteration()
        
        
class Status(object):
    def __init__(self):
        self.core = 1
        self.k = 2
        self.h = 6
        
        self.CACHE_BUDGET_FRACTION = 0.05
        self.N_CONTENTS = 3 * 10 ** 4
        self.N_WARMUP_REQUESTS = 4 * 10 ** 4
        self.N_MEASURED_REQUESTS = 1 * 10 ** 4
        self.GAMMA = .8
        self.ALPHA = .4

        self.INTERNAL_COST = 2
        self.EXTERNAL_COST = 34

        self.on_path_routing = True
        self.on_path_winner = True
        self.relative_popularity = True
        self.cache_placement = 'uniform'
        self.scenario = 'AUC'
        
        self.parameters = {}
        
        self.hits = 0
        self.all_delays = []
        self.cr_hit = []
        self.winners = []
    
        self.topo_type = 'tree'
        self.cache_replacement = 'POP'
        
        self.information = None
        
        
    def set_parameters_dictionary(self, parameters):
        for param in parameters:
            self.parameters[param] = parameters[param]
        
    def set_parameter(self, key, value):
        self.parameters[key] = value
        

        
        
        
        
    
    
    
    