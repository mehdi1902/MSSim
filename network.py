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
        self.CACHE_BUDGET_FRACTION = .001
        self.N_CONTENTS = 3 * 10 ** 5
        self.N_WARMUP_REQUESTS = 4 * 10 ** 5
        self.N_MEASURED_REQUESTS = 1 * 10 ** 5
        self.GAMMA = 1
        self.ALPHA = 1
        self._cache_budget = (self.CACHE_BUDGET_FRACTION * self.N_CONTENTS)
        self.INTERNAL_COST = 2
        self.EXTERNAL_COST = 10

        self.max_delay = h * self.INTERNAL_COST + self.EXTERNAL_COST

        # Uniform cache assignement

        self.topology = self._create_topology(core, k, h)
        self.clients = {node: self.topology.node[node] for node in self.topology.node \
                        if self.topology.node[node]['type'] == 'leaf'}
        self.pops = {node: self.topology.node[node] for node in self.topology.node \
                     if self.topology.node[node]['type'] == 'root'}
        self.routers = {node: self.topology.node[node] for node in self.topology.node \
                        if self.topology.node[node]['type'] in ['root', 'intermediate']}

        self.cache = self.cache_placement()
        self.informations = {node: {} for node in self.topology.node}

        self.workload = StationaryWorkload(self.clients.keys(), self.N_CONTENTS, self.ALPHA,
                                           n_warmup=self.N_WARMUP_REQUESTS,
                                           n_measured=self.N_MEASURED_REQUESTS)
        self.shortest_path = self._symmetrify_paths(nx.all_pairs_dijkstra_path(self.topology))
        self.neighbors2 = {node: self._neighbors_of_neighbors(node) for node in self.topology.node}

        self.hits = 0
        #        self.cache_hit = {node:{i:0 for i in range(1, 1+self.N_CONTENTS)} for node in self.topology.node}
        #        self.delays = {i:[] for i in range(1, 1+self.N_CONTENTS)}
        self.all_delays = []
        
        self.cnt = 0

        self.scenario = 'AUC'

    def run(self):
        # TODO: separete warmup and test
        counter = 1
        for time, client, content in self.workload:
            if not counter % 10000:
                sys.stdout.write('\rProgress: {0:.2f}%\t\tHit rate: {1:.3f}%'. \
                                 format(100 * counter / float(self.N_MEASURED_REQUESTS + self.N_WARMUP_REQUESTS), \
                                        (100 * self.hits / float(counter - self.N_WARMUP_REQUESTS + 10e-10))))
                sys.stdout.flush()
            #                sleep(10e-4)
            #            if not counter%10000:
            #                print 'round %d' % counter
            counter += 1
            self.event_run(time, client, content, measured=counter > self.N_WARMUP_REQUESTS + 1)

    def event_run(self, time, client, content, measured=True):
        if self.scenario == 'AUC':
            path = self.shortest_path[client][self.clients[client]['server']]
            #        print path
            for node in path[1:]:
                delay = path.index(node) * self.INTERNAL_COST
                self.update_node_information(node, content, delay, time)

                neighbor = self._neighbors_has_content(node, content)

                if self.cache[node].has_content(content):
                    if measured:
                        self.hits += 1
                        # self.cache_hit[node][content] += 1
                        # self.delays[content].append(delay)
                        # self.all_delays.append(delay)
                    break
                ###############################
                # if content cached in neighbors
                elif neighbor is not False:
                    # self.cache_hit[neighbor][content] += 1
                    delay += [2, 1][neighbor in self.topology.neighbors(node)] * self.INTERNAL_COST

                    semi_path = self.shortest_path[node][neighbor]
                    # TODO: update informations of neighbor with cached content
                    self.update_node_information(neighbor, content, delay, time)
                    if measured:
                        self.hits += 1
                        # self.delays[content].append(delay)
                        self.all_delays.append(delay)
                    break

            # Cache miss and decision for cache placement
            else:
                if measured:
                    # self.delays[content].append((len(path)-1)*self.INTERNAL_COST+self.EXTERNAL_COST)
                    self.all_delays.append((len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST)

                winner = self._winner_determination(path, content, time)
                if winner:
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
                        # self.cache_hit[node][content] += 1
                        # self.delays[content].append(delay)
                        # print 'hit'
                        self.all_delays.append(delay)
                    break
                self.cache[node].put_content(content)
            else:
                if measured:
                    delay = (len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST
                    self.all_delays.append(delay)

        elif self.scenario == 'RND':
            path = self.shortest_path[client][self.clients[client]['server']]
            for node in path[1:]:
                delay = path.index(node) * self.INTERNAL_COST

                if self.cache[node].has_content(content):
                    self.cache[node].get_content(content)
                    if measured:
                        self.hits += 1
                        # self.cache_hit[node][content] += 1
                        # self.delays[content].append(delay)
                        # print 'hit'
                        self.all_delays.append(delay)
                    break

            else:
                if measured:
                    delay = (len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST
                    self.all_delays.append(delay)

            self.cache[path[random.randint(1, len(path) - 1)]].put_content(content)

    def _winner_determination(self, path, content, time):
        # TODO: complete value
        max_val = -10e10
        winner = None
        nodes = []

        '''
        Last state of popularity is not suitable for comparing
        So all of popularity values must updated
        '''

        # for node in path:
        #     for v in self.neighbors2[node]:
        #         # for v in self.topology.neighbors(node):
        #         if v not in self.clients:
        #             nodes.append(v)
        # nodes = list(set(nodes))
        nodes = path[1:]

        for v in nodes:
            if self.cache[v].cache_size == 0:
                continue
            sum_value = 0
            if content in self.informations[v]:
                average_distance = self.informations[v][content]['average_distance']
                last_req = self.informations[v][content]['last_req']
                popularity = self.GAMMA ** ((time - last_req) / 10000.) * self.informations[v][content]['popularity']
                popularity /= self.informations[v]['total_req']
            else:
                average_distance = self.EXTERNAL_COST
                last_req = time
                popularity = 0

            ################################
            # Values for evict candidate
            content_prim = self.cache[v].get_replace_candidate()


            # Replacement: evict least popular content
            # min_pop = 10e10
            # min_pop_candidates = []
            # if len(self.cache[v].contents):
            #    for content in self.cache[v].contents:
            #        if content in self.informations[v]:
            #            p = self.informations[v][content]['popularity']
            # #                        print p
            #            if min_pop > p:
            #                min_pop = p
            #                min_pop_candidates = [content]
            #            elif min_pop==p:
            #                min_pop_candidates.append(content)
            #            shuffle(min_pop_candidates)
            #            content_prim = min_pop_candidates[0]
            # else: content_prim=None
                
            
            #            print v, content_prim
            if content_prim is not None and content_prim in self.informations[v]:
                last_req_prim = self.informations[v][content_prim]['last_req']
                popularity_prim = self.informations[v][content_prim]['popularity']
                popularity_prim *= self.GAMMA ** (time - last_req_prim)
                popularity_prim /= self.informations[v]['total_req']
                average_distance_prim = self.informations[v][content_prim]['average_distance']
            #                value = - popularity_prim
            else:
                # value = 0
                average_distance_prim = 1
                popularity_prim = 0

            for u in self.neighbors2[v]:
                '''
                cache of a content effects on nodes in neighbors2
                '''
                if content in self.informations[u]:
                    average_distance_u = self.informations[u][content]['average_distance']
                    last_req_u = self.informations[u][content]['last_req']
                    popularity_u = self.GAMMA ** ((time - last_req_u) / 10000.) * self.informations[u][content]['popularity']

                    if u == v:
                        value = popularity - popularity_prim
                        # value = (self.max_delay-average_distance) + (popularity-popularity_prim)
                        # value =
                        # value = (-average_distance / float(self.max_delay) +\
                        #         10*(popularity*average_distance /float(popularity*average_distance + popularity_prim*average_distance_prim + 10e-10)))
                    else:
                        value = 0
#                        value = popularity_u
                        # value = -(average_distance_u + len(self.shortest_path[u][v]) - 1) / float(self.max_delay)
                    sum_value += value

            if sum_value >= max_val:
                max_val = sum_value
                winner = v
        return winner

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
            if self.topology.node[n]['type'] is not 'root':
                for neighbor in self.topology.neighbors(n):
                    if self.topology.node[neighbor]['type'] is 'intermediate':
                        nodes.append(neighbor)
                if self.topology.node[n]['type'] is 'intermediate':
                    nodes.append(n)
        # if node in nodes:
        #     nodes.remove(node)
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
        total_betweenness = float(sum(betweenness.values()))
        return {node: Cache(int(round(cache_budget * betweenness[node] / total_betweenness)))
                for node in self.routers}


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
    print '------CEE------'
    n = Network(4, 2, 5)
    n.scenario = 'CEE'
    n.run()
    print '\nhit rate = %.2f%%' % (100 * n.hits / float(n.N_MEASURED_REQUESTS))
    print 'average delay = %f' % (sum(n.all_delays) / float(n.N_MEASURED_REQUESTS))

    print '------RND------'
    n = Network(4, 2, 5)
    n.scenario = 'RND'
    n.run()
    print '\nhit rate = %.2f%%' % (100 * n.hits / float(n.N_MEASURED_REQUESTS))
    print 'average delay = %f' % (sum(n.all_delays) / float(n.N_MEASURED_REQUESTS))

    print '------AUC------'
    n = Network(4, 2, 5)
    n.run()
    print '\nhit rate = %.2f%%' % (100 * n.hits / float(n.N_MEASURED_REQUESTS))
    print 'average delay = %f' % (sum(n.all_delays) / float(n.N_MEASURED_REQUESTS))
