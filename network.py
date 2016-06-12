# -*- coding: utf-8 -*-
# from topology import Topology
from workload import *
from random import shuffle
import fnss
import networkx as nx
# from cache import *
import sys
from time import sleep


class Network():
    def __init__(self, core, k, h):
        self.CACHE_BUDGET_FRACTION = .05
        self.N_CONTENTS = 3 * 10 ** 4
        self.N_WARMUP_REQUESTS = 4 * 10 ** 5
        self.N_MEASURED_REQUESTS = 1 * 10 ** 5
        self.GAMMA = 1
        self.ALPHA = .8

        self.INTERNAL_COST = 2
        self.EXTERNAL_COST = 10

        self.on_path = False

        self.max_delay = h * self.INTERNAL_COST + self.EXTERNAL_COST

        # Uniform cache assignement

        self.topology = self._create_topology(core, k, h)
        self.clients = {node: self.topology.node[node] for node in self.topology.node
                        if self.topology.node[node]['type'] == 'leaf'}
        self.pops = {node: self.topology.node[node] for node in self.topology.node
                     if self.topology.node[node]['type'] == 'root'}
        self.routers = {node: self.topology.node[node] for node in self.topology.node
                        if self.topology.node[node]['type'] in ['root', 'intermediate']}

        self.informations = {node: {} for node in self.topology.node}

        self.workload = None
        self._cache_budget = None
        self.cache = None

        self.shortest_path = self._symmetrify_paths(nx.all_pairs_dijkstra_path(self.topology))
        self.neighbors2 = {node: self._neighbors_of_neighbors(node) for node in self.topology.node}

        self.hits = 0
        #        self.cache_hit = {node:{i:0 for i in range(1, 1+self.N_CONTENTS)} for node in self.topology.node}
        #        self.delays = {i:[] for i in range(1, 1+self.N_CONTENTS)}
        self.all_delays = []
        self.winners = []

        self.scenario = 'AUC'

        self.cnt = 0

        self.ind = [ 0.21561868,  0.91459301,  0.        ,  0.25700366,  0.358362  ,\
        0.54709407,  0.99226817,  0.12912687,  0.39532304,  0.11537119,\
        0.52464204,  0.66921722,  0.66034903,  0.03366341]

    def run(self):
        self._cache_budget = (self.CACHE_BUDGET_FRACTION * self.N_CONTENTS)
        self.cache = self.cache_placement()
        self.workload = StationaryWorkload(self.clients.keys(), self.N_CONTENTS, self.ALPHA,
                                           n_warmup=self.N_WARMUP_REQUESTS,
                                           n_measured=self.N_MEASURED_REQUESTS)

        counter = 1
        for time, client, content in self.workload:
            if not counter % 100:
                sys.stdout.write('\rProgress: {0:.2f}%\t\tHit rate: {1:.3f}%'.
                                 format(100 * counter / float(self.N_MEASURED_REQUESTS + self.N_WARMUP_REQUESTS),
                                        (100 * self.hits / float(counter - self.N_WARMUP_REQUESTS + 10e-10))))
           
                sys.stdout.flush()
            counter += 1
            self.event_run(time, client, content, measured=counter > self.N_WARMUP_REQUESTS + 1)

    def event_run(self, time, client, content, measured=True):
        self.cnt += 1
        if self.scenario == 'AUC':
            path = self.shortest_path[client][self.clients[client]['server']]
            #        print path
            for node in path[1:]:
                delay = path.index(node) * self.INTERNAL_COST
                self.update_node_information(node, content, delay, time)

                neighbor = self._neighbors_has_content(node, content)

                # On-path hit occurs
                if self.cache[node].has_content(content):
                    self.cache[node].get_content(content)
                    if measured:
                        self.hit()
                        self.all_delays.append(delay)
                    break
                # Hit from a neighbor
                elif neighbor is not False and self.on_path is False:
                    self.cache[neighbor].get_content(content)
                    # self.cache_hit[neighbor][content] += 1
                    delay += [2, 1][neighbor in self.topology.neighbors(node)] * self.INTERNAL_COST
#                    print delay
                    semi_path = self.shortest_path[node][neighbor]
                    # TODO: update informations of neighbor with cached content
                    for n in semi_path[1:]:
                        self.update_node_information(n, content, delay, time)
                    if measured:
                        self.hit()
                        # self.delays[content].append(delay)
                        self.all_delays.append(delay)
                    break

            # Cache miss and decision for cache placement
            #     self.winners.append(None)
            else:
                if measured:
                    # self.delays[content].append((len(path)-1)*self.INTERNAL_COST+self.EXTERNAL_COST)
                    delay = self.max_delay # (len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST
                    self.all_delays.append(delay)

                winner = self._winner_determination(path, content, time)
                self.winners.append((content, winner))
                if winner is None:
                    print 'Winner is None!!'
                if winner is not None:
                    self.cache[winner].put_content(content)

        elif self.scenario == 'CEE':
            path = self.shortest_path[client][self.clients[client]['server']]
            for node in path[1:]:
                delay = path.index(node) * self.INTERNAL_COST
                
                neighbor = self._neighbors_has_content(node, content)
                
                if self.cache[node].has_content(content):
                    self.cache[node].get_content(content)
                    if measured:
                        self.hits += 1
                        self.all_delays.append(delay)
                    break
                    
                    
                elif neighbor is not False and self.on_path is False:
                    self.cache[neighbor].get_content(content)
                    delay += [2, 1][neighbor in self.topology.neighbors(node)] * self.INTERNAL_COST
                    if measured:
                        self.hit()
                        # self.delays[content].append(delay)
                        self.all_delays.append(delay)
                    break
            else:
                if measured:
                    delay = self.max_delay# (len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST
                    self.all_delays.append(delay)
            for node in path[1:]:
                self.cache[node].put_content(content)

        elif self.scenario == 'RND':
            path = self.shortest_path[client][self.clients[client]['server']]
            for node in path[1:]:
                delay = path.index(node) * self.INTERNAL_COST

                if self.cache[node].has_content(content):
                    self.cache[node].get_content(content)
                    if measured:
                        self.hits += 1
                        self.all_delays.append(delay)
                    break

            else:
                if measured:
                    delay = self.max_delay#(len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST
                    self.all_delays.append(delay)

            self.cache[path[random.randint(1, len(path) - 1)]].put_content(content)
            
        elif self.scenario == 'LCD':
            path = self.shortest_path[client][self.clients[client]['server']]
            for node in path[1:]:
                delay = path.index(node) * self.INTERNAL_COST

                neighbor = self._neighbors_has_content(node, content)

                if self.cache[node].has_content(content):
                    self.cache[node].get_content(content)
                    idx = path.index(node)
#                    print path, idx, path[idx-1]
                    if idx > 1:
                        self.cache[path[idx-1]].put_content(content)
                    if measured:
                        self.hits += 1
                        # self.cache_hit[node][content] += 1
                        # self.delays[content].append(delay)
                        # print 'hit'
                        self.all_delays.append(delay)
                    break
                
            else:
                self.cache[path[-1]].put_content(content)
                if measured:
                    delay = self.max_delay # (len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST
                    self.all_delays.append(delay)
                    
        elif self.scenario == 'MCD':
            path = self.shortest_path[client][self.clients[client]['server']]
            for node in path[1:]:
                delay = path.index(node) * self.INTERNAL_COST

                neighbor = self._neighbors_has_content(node, content)

                if self.cache[node].has_content(content):
                    self.cache[node].get_content(content)
                    idx = path.index(node)
#                    print path, idx, path[idx-1]
                    if idx > 1:
                        self.cache[path[idx-1]].put_content(content)
                    if measured:
                        self.hits += 1
                        # self.cache_hit[node][content] += 1
                        # self.delays[content].append(delay)
                        # print 'hit'
                        self.all_delays.append(delay)
                    break
                
            else:
                self.cache[path[-1]].put_content(content)
                if measured:
                    delay = self.max_delay # (len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST
                    self.all_delays.append(delay)

    def _winner_determination(self, path, content, time):
        # TODO: complete value
        max_val = -10e10
        winner = None
        nodes = []
        print_res = False

        '''
        ** Last state of popularity is not suitable for comparing
            So all of popularity values must updated
        ** On-path is better for decision :)
        '''

        # for node in path:
        #     for v in self.neighbors2[node]:
        #     # for v in self.topology.neighbors(node):
        #         if v not in self.clients:
        #             nodes.append(v)
        # nodes = list(set(nodes))
        nodes = path[1:]

        #############################
        # v is caching node candidate
        if print_res:
            print '--------------'
        ind = self.ind
        for v in nodes:
            ################################
            # If node doesn't have cache
            if self.cache[v].cache_size == 0:
                continue

            sum_value = 0
            # print sum_value

            ###############################
            # Information of candidate node
            average_distance, popularity, last_req, total_req = self.get_node_information(v, content, time)
            
#            print popularity, total_req

            ############################
            # Values for evict candidate
            content_prim = self.cache[v].get_replace_candidate()

            ##################################
            # Information of evicted candidate
            if content_prim is not None:
                average_distance_prim, popularity_prim, last_req_prim, _ = self.get_node_information(v, content_prim, time)
            else:
                average_distance_prim, popularity_prim, last_req_prim = 1, +10e5, time

            # print content, popularity, '----', content_prim, popularity_prim

            for other in nodes:
                for u in self.neighbors2[other]:
                    '''
                    cache of a content effects on nodes in neighbors2
                    '''
                    if content in self.informations[u]:
                        average_distance_u, popularity_u, last_req_u, total_req_u = self.get_node_information(u, content, time)
                        
                        if other == v and u == v:
                            ########################
                            # caching node candidate
                            # d = 5 - self.topology.node[v]['depth']
                            value = (popularity / average_distance) + 10 * (self.cache[v].cache_size != len(self.cache[v].contents))
                            # (self.max_delay - average_distance)
                            # value = (popularity/total_req) + 10*(self.cache[v].cache_size != len(self.cache[v].contents))
                            # value = (popularity/average_distance) + 10*(self.cache[v].cache_size != len(self.cache[v].contents))
#                            value = (ind[0]*popularity**ind[1] - ind[2]*popularity_prim**ind[3]) / (ind[4]*total_req**ind[5]) * ind[6]*average_distance**ind[7]


#                            value = popularity/float(total_req)#*average_distance**.1
                            # print 'val:', (popularity / total_req) #* average_distance #+ 10 * (self.cache[v].cache_size != len(self.cache[v].contents))
                            # value = (popularity * average_distance) - (popularity_prim * average_distance_prim)
                            # value = (self.max_delay-average_distance) + (popularity-popularity_prim)
                            # value =
                            # value = (-average_distance / float(self.max_delay) -\
                            # 10*(popularity*average_distance /float(popularity*average_distance + popularity_prim*average_distance_prim + 10e-10)))
                            if print_res:
                                print v, self.topology.node[v]['depth'], value, average_distance

                        elif other == u and other != v:
                            ###############################
                            # Just other nodes (themselves)
                            if u in self.routers:
                                value = 0
                                if u in path or not self.on_path:
                                    value = 0
                                    # value = popularity_u/(average_distance_u+[4,2][u in self.topology.neighbors(v)])
#                                    value = (ind[8]*popularity_u**ind[9]) / (ind[10]*total_req_u**ind[11]) * (ind[12]*total_req_u**ind[13])
#                                    value = popularity / float(total_req_u**.5)
                                # value = (popularity_u * average_distance_u)
                                # value = popularity_u
                                # value = -(average_distance_u + len(self.shortest_path[u][v]) - 1) / float(self.max_delay)
                        else:
                            value = 0
                        sum_value += value

            # if sum_value > 0:
            #     print sum_value
            if sum_value >= max_val:
                max_val = sum_value
                winner = v
            # sum_value = 0
        if print_res and self.topology.node[winner]['depth']<5:
            print 'winner:', winner, self.topology.node[winner]['depth']
        # if self.topology.node[winner]['depth']<5:
        #     print winner, self.topology.node[winner]['depth']
        return winner if max_val > 0 else None

    def update_node_information(self, node, content, delay, time):
        if content in self.informations[node]:
            info = self.informations[node][content]
            popularity = info['popularity']
            average_distance = info['average_distance']
            last_req = info['last_req']

            popularity = self.GAMMA ** ((time - last_req) / 10000.) * popularity + 1
            # TODO: correct beta value
            # beta = max(min(self.GAMMA ** ((time - last_req) / 10000.), .8), .1)
            beta = .8
            if average_distance is not None:
                average_distance = beta * average_distance + (1 - beta) * delay
            else:
                average_distance = delay
        else:
            popularity = 1
            average_distance = delay
        self.informations[node][content] = {'popularity': popularity,
                                            'average_distance': average_distance,
                                            'last_req': time}
        if 'total_req' in self.informations[node]:
            total_req = self.informations[node]['total_req']
        else:
            total_req = 0
        self.informations[node]['total_req'] = total_req + 1

    def get_node_information(self, node, content, time):
        if content in self.informations[node]:
            info = self.informations[node][content]
            average_distance = info['average_distance']
            last_req = info['last_req']
            popularity = self.GAMMA ** ((time - last_req) / 10000.) * info['popularity']
            # popularity /= self.cnt
        else:
            average_distance = self.EXTERNAL_COST
            last_req = time
            popularity = 0
        total_req = self.informations[node]['total_req']
        return average_distance, popularity, last_req, float(total_req)

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

    def _neighbors_has_content(self, node, content):
        """

        Parameters
        ----------
        node
        content

        Returns
        -------
        neighbor id of content owner or False if nobody has it
        """
        neighbors = self.neighbors2[node]
        for neighbor in neighbors:
            if self.cache[neighbor].has_content(content):
                return neighbor
        return False

    def _symmetrify_paths(self, shortest_paths):
        for u in shortest_paths:
            for v in shortest_paths[u]:
                shortest_paths[u][v] = list(reversed(shortest_paths[v][u]))
        return shortest_paths

    def _create_topology(self, PoP, k, h):
        topology = fnss.Topology()
        for core in range(PoP):
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

    def cache_placement(self):
        cache_budget = self._cache_budget
        betweenness = nx.betweenness_centrality(self.topology)
        # betweenness = nx.degree_centrality(self.topology)
        # betweenness = {node: .1 for node in self.routers}
        total_betweenness = float(sum(betweenness.values()))
        return {node: Cache(int(round(cache_budget * betweenness[node] / total_betweenness)))
                for node in self.routers}
        # cache_size = cache_budget / len(self.routers)
        # return {node: Cache(int(round(cache_size))) for node in self.routers}

    def reset(self):
        self.hits = 0
        self.all_delays = []
        self.informations = {node: {} for node in self.topology.node}

    def write_result(self):
        print '\nhit rate = %.2f%%' % (100 * self.hits / float(self.N_MEASURED_REQUESTS))
        print 'average delay = %f' % (sum(self.all_delays) / float(self.N_MEASURED_REQUESTS))

    def hit(self):
        self.hits += 1
        # self.cache_hit[node][content] += 1
        # self.delays[content].append(delay)
        # self.all_delays.append(delay)


class Cache(object):
    """
    Cache with LRU for replacement
    """

    def __init__(self, cache_size):
        self.contents = []
        #        self._len = 0
        #        self._max_len = cache_size
        self._has_cache = True
        self.cache_size = cache_size

    def get_content(self, content):
        if content in self.contents:
            self.contents.remove(content)
            self.contents = [content] + self.contents
        else:
            return False

    def has_content(self, content):
        return content in self.contents if self.has_cache() else False

    def put_content(self, content):
        if content not in self.contents:
            self.contents = ([content] + self.contents)[:self.cache_size]
        else:
            self.get_content(content)

    def set_cache(self, cache_size):
        self.cache_size = cache_size
        self.set_cache = True

    def has_cache(self):
        return self._has_cache

    def get_cache_size(self):
        return self.cache_size

    def get_replace_candidate(self):
        return self.contents[-1] if len(self.contents) == self.cache_size else None


if __name__ == '__main__':
    n = Network(4, 2, 6)
    
    scenarios = [('CEE', True),
                 ('CEE', False),
                 ('AUC', True),
                 ('AUC', False),
                ]
    for (scr, op) in scenarios:
        print '------%s-%s-----'%(scr, ['Off', 'On'][op])
        n.reset()
        n.on_path = op
        n.scenario = scr
        n.run()
        n.write_result()
    # #
    # print '------RND------'
    # n.reset()
    # n.scenario = 'RND'
    # n.run()
    # n.write_result()
    # #
    # print '------LCD------'
    # n.reset()
    # n.scenario = 'LCD'
    # n.run()
    # n.write_result()

#    print '------AUC----on-path--'
#    n.reset()
#    n.on_path = True
#    n.scenario = 'AUC'
#    n.run()
#    n.write_result()
#
#
#    print '------AUC------'
#    n.reset()
#    n.on_path = False
#    n.scenario = 'AUC'
#    n.run()
#    n.write_result()