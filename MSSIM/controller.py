# -*- coding: utf-8 -*-
from model import Topology, Workload, Status, Cache
from view import *
import sys
import numpy as np


class Network(object):
    def __init__(self):
        self.status = Status()
        self.topology = Topology(self.status)

        self.CACHE_BUDGET_FRACTION = self.status.CACHE_BUDGET_FRACTION
        self.workload = None

        self.hits = 0
        self.all_delays = []
        self.cr_hit = []
        self.winners = []

        self.content_threshold = 1

        self.status.information = {node: {} for node in self.topology.topology.node}

        self.workload = Workload(self.topology.clients.keys(),
                                 self.status.N_CONTENTS,
                                 self.status.ALPHA,
                                 self.status.N_WARMUP_REQUESTS,
                                 self.status.N_MEASURED_REQUESTS)

        self.cache = None
        self.time_scale = 10000.
#        self.shortest_path = self.topology.shortest_path
#        self.clients = self.topology.clients
#        self.routers = self.topology.routers

    def _winner_determination(self, path, content, time):
        # TODO: complete value
        max_val = -10e10
        winner = None
        nodes = []
        print_res = False

#        min_err = 10e10

        '''
        ** Last state of popularity is not suitable for comparing
            So all of popularity values must updated
        ** On-path is better for decision :)
        '''

        if self.status.on_path_winner:
            nodes = path[1:]
        else:
            for node in path:
                for v in self.topology.neighbors2[node]:
#                for v in self.topology.neighbors(node):
                    if v not in self.topology.clients:
                        nodes.append(v)
            nodes = list(set(nodes))

        total_cache = [0]
#        for c in path[1:]:
#            total_cache.append(self.cache[c].cache_size + total_cache[-1])

#        p = self.pops/float(max(self.pops))
#        total_cache[-1] * (content**-self.ALPHA/float(max(self.pops)))

#        for v in nodes:
#            _, p, _, t = self.get_node_information(v, content, time)
#            if p/t < .2:
#                nodes.remove(v)

        #############################
        # v is caching node candidate
        if print_res:
            print '--------------'
#        ind = self.ind
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
#            total_pop = 0
#            for content in self.status.information[v]:
#                if content is not 'total_req':
#                    total_pop += self.status.information[v][content]['popularity']
#                    print total_pop
            
#            print popularity, total_req

            ############################
            # Values for evict candidate
            content_prim = self.cache[v].get_replace_candidate()
#            print v, content_prim
            ##################################
            # Information of evicted candidate
            if content_prim is not None:
                average_distance_prim, popularity_prim, last_req_prim, _ = self.get_node_information(v, content_prim, time)
            else:
                average_distance_prim, popularity_prim, last_req_prim = 1, -10e5, time

#            print popularity_prim
#             print content, popularity, '----', content_prim, popularity_prim
            
            for other in nodes:
#                for u in self.neighbors2[other]:
                '''
                cache of a content effects on nodes in neighbors2
                '''
#                value = 0
                if other == v:# and u == v:
                    value = (- popularity_prim) #/ average_distance #+ 10e5 * (self.cache[v].cache_size<>len(self.cache[v].contents))
#                    print (popularity - popularity_prim)
#                    value = - popularity*average_distance + 10 * (self.cache[v].cache_size<>len(self.cache[v].contents))
                    #v_value
#                    value = popularity / average_distance#average_distance #(content-self.N_CONTENTS/2) / (average_distance - self.max_delay/2)
#                    value = (2 * average_distance / self.max_delay - 1) * popularity
#                    value = self.v_value(popularity, average_distance, v, popularity_prim, average_distance_prim)
                    #v_value
#                    value = popularity / float(total_pop) * total_req / time
#                    value = popularity + 10 * (self.cache[v].cache_size <> len(self.cache[v].contents))
                    if print_res:
                        print v, self.topology.node[v]['depth'], value, average_distance
                else:
#                    value = 0
                    if content in self.status.information[other]:
                        average_distance_u, popularity_u, last_req_u, total_req_u = self.get_node_information(other, content, time)
                        #u_value
                        value = 0
#                        value = self.u_value(popularity_u, average_distance_u, other, path, v)
#                        if other in path[:path.index(v)]:
#                            value = popularity_u
                        #u_value
                    else:value=0
#                    value = popularity_u / (average_distance_u+[1,2][other in self.topology.neighbors(v)]*self.INTERNAL_COST)
                sum_value += value

#            proportion = (content/float(self.N_CONTENTS))**.2
#            diff = abs(proportion - average_distance/float(self.max_delay-self.EXTERNAL_COST))
            
#            print self.topology.node[v]['depth'], proportion, average_distance/float(self.max_delay-self.EXTERNAL_COST), diff
            
#            if diff < min_err:
#                min_err = diff
#                winner = v
#
#
            # if sum_value > 0:
            #     print sum_value
            if sum_value >= max_val:
                max_val = sum_value
                winner = v
#            # sum_value = 0
#        print self.topology.node[winner]['depth']
#        if content<10:
#            print content, self.topology.node[winner]['depth']
        return winner #if max_val > 0 else None

    def update_node_information(self, node, content, delay, time):
        if content in self.status.information[node]:
            info = self.status.information[node][content]
            popularity = info['popularity']
            average_distance = info['average_distance']
            last_req = info['last_req']
            total_req = self.status.information[node]['total_req']
            
#            pops = [self.status.information[node][c]['popularity'] for c in self.status.information[node]
#                                                    if c is not 'total_req']
#            k = len(pops) - np.searchsorted(np.array(pops), popularity)
#
#            popularity += k**-self.ALPHA * (time-last_req) * (total_req / time)

#            popularity += popularity/float(total_req)

            popularity2 = self.status.GAMMA ** ((time - last_req) / self.time_scale) * popularity + 1
#            popularity *= total_req/time
            # TODO: correct beta value
            # beta = max(min(self.GAMMA ** ((time - last_req) / 10000.), .8), .1)
            beta = .8
            if average_distance is not None:
                average_distance = beta * average_distance + (1 - beta) * delay
            else:
                average_distance = delay
        else:
            popularity = 1
            popularity2 = 1.
            average_distance = delay
            
        self.status.information[node][content] = {'popularity': popularity2,
                                            'average_distance': average_distance,
                                            'last_req': time}
        if 'total_req' in self.status.information[node]:
            total_req = self.status.information[node]['total_req']
        else:
            total_req = 10e-10
        self.status.information[node]['total_req'] = total_req - popularity + popularity2 #popularity/float(total_req)

    def get_node_information(self, node, content, time):
        if content in self.status.information[node]:
            info = self.status.information[node][content]
            average_distance = info['average_distance']
            last_req = info['last_req']
            popularity = info['popularity']
#            print popularity
            total_req = self.status.information[node]['total_req']
            
#            pops = [self.status.information[node][c]['popularity'] for c in self.status.information[node]
#                                        if c is not 'total_req']
#                                            
#            k = len(pops) - np.searchsorted(np.array(pops), popularity)
#
#            popularity += k**-self.ALPHA * (time-last_req) * (total_req / time)            
            
#            popularity +=
            
            popularity = self.status.GAMMA ** ((time - last_req) / self.time_scale) * info['popularity']
#            popularity *= total_req/time
            # popularity /= self.cnt

        else:
            average_distance = self.status.INTERNAL_COST #self.topology.topology.node[node]['depth']
            last_req = time
            popularity = 0.
            total_req = 1
#            print popularity
        if self.status.relative_popularity:
            
            popularity /= float(total_req)
            
        return float(average_distance), float(popularity), last_req, float(total_req)


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
        neighbors = self.topology.neighbors2[node]
        for neighbor in neighbors:
            if self.cache[neighbor].has_content(content):
                return neighbor
        return False
        
    def hit(self, *args):
        self.hits += 1
        if len(args)==2:
            content = args[0]
            router = args[1]
            self.cr_hit.append((content, router))
            
    
    def run(self):
        self.reset()
        
        counter = 1
        for time, client, content in self.workload:            
            if not counter % 100:
                sys.stdout.write('\rProgress: {0:.2f}%\t'.
                                 format(100 * counter / 
                                 float(self.status.N_MEASURED_REQUESTS + self.status.N_WARMUP_REQUESTS)))
           
                sys.stdout.flush()
            counter += 1
            self.event_run(time, client, content, 
                           measured=counter > self.status.N_WARMUP_REQUESTS + 1)
#            if counter in self.shots:
#                self.saved_shots.append(self)
                           
        self.status.hits = self.hits
        self.status.all_delays = self.all_delays
        self.status.cr_hit = self.cr_hit
        self.status.winners = self.winners
        
        self.topology.reset_topology()

    def reset(self):
        self.topology = Topology(self.status)
#        self._cache_budget = (self.status.CACHE_BUDGET_FRACTION * self.status.N_CONTENTS)
        self.CACHE_BUDGET_FRACTION = self.status.CACHE_BUDGET_FRACTION
        self.cache = self.topology.place_caches()
        
        self.workload = Workload(self.topology.clients.keys(),
                                 self.status.N_CONTENTS,
                                 self.status.ALPHA,
                                 self.status.N_WARMUP_REQUESTS,
                                 self.status.N_MEASURED_REQUESTS)

        self.hits = 0
        self.all_delays = []
        self.cr_hit = []
        self.winners = []
        
        self.status.information = {node: {} for node in self.topology.topology.node}
        

    def event_run(self, time, client, content, measured=True):
#        self.cnt += 1
        if self.status.scenario == 'AUC':
            
            path = self.topology.shortest_path[client][self.topology.clients[client]['server']]
            #        print path
            for node in path[1:]:
                delay = path.index(node) * self.status.INTERNAL_COST
                self.update_node_information(node, content, delay, time)

                neighbor = self._neighbors_has_content(node, content)

                # On-path hit occurs
                if self.cache[node].has_content(content):
                    self.cache[node].get_content(content)
#                    idx = path.index(node)
#                    if idx > 1:
#                        self.cache[path[idx-1]].put_content(content)
                    if measured:
                        self.hit(content, node)
                        self.all_delays.append(delay)
                    break
                # Hit from a neighbor
                elif neighbor is not False and self.status.on_path_routing is False:
                    self.cache[neighbor].get_content(content)
                    # self.cache_hit[neighbor][content] += 1
                    delay += [2, 1][neighbor in self.topology.topology.neighbors(node)] * self.status.INTERNAL_COST
                    
#                    semi_path = self.shortest_path[node][neighbor]
                    # TODO: update informations of neighbor with cached content
#                    for n in semi_path[1:]:
#                        self.update_node_information(n, content, delay, time)
                    if measured:
                        self.hit(content, neighbor)
                        # self.delays[content].append(delay)
                        self.all_delays.append(delay)
                    break

            # Cache miss and decision for cache placement
            #     self.cr_hit.append(None)
            else:
                
                if content < self.content_threshold * self.status.N_CONTENTS:
                    winner = self._winner_determination(path, content, time)
                    
                    if winner is not None:
#                        popularity = self.status.information[winner][content]['popularity']
                        self.cache[winner].put_content(content)
                    if measured:
                        self.winners.append((content, winner))

                if measured:
                    # self.delays[content].append((len(path)-1)*self.INTERNAL_COST+self.EXTERNAL_COST)
                    delay = len(path)*self.status.INTERNAL_COST + self.status.EXTERNAL_COST
#                    self.topology.max_delay # (len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST
                    self.all_delays.append(delay)
#                    self.winners.append((content, winner))

        elif self.status.scenario == 'CEE':
            path = self.topology.shortest_path[client][self.topology.clients[client]['server']]
            for node in path[1:]:
                delay = path.index(node) * self.status.INTERNAL_COST
                
                neighbor = self._neighbors_has_content(node, content)
                
                if self.cache[node].has_content(content):
                    self.cache[node].get_content(content)
                    if measured:
                        self.hit(content, node)
#                        self.cr_hit.append((content, node))
                        self.all_delays.append(delay)
                    break
                    
                    
                elif neighbor is not False and self.status.on_path_routing is False:
                    self.cache[neighbor].get_content(content)
                    delay += [2, 1][neighbor in self.topology.neighbors(node)] * self.status.INTERNAL_COST
                    if measured:
                        self.hit(content, neighbor)
                        # self.delays[content].append(delay)
                        self.all_delays.append(delay)
                    break
            else:
                if measured:
#                    delay = self.topology.max_delay# (len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST
                    delay = len(path)*self.status.INTERNAL_COST + self.status.EXTERNAL_COST

                    self.all_delays.append(delay)
                    
            if content<self.content_threshold*self.status.N_CONTENTS:
                for node in path[1:]:
                    self.cache[node].put_content(content)

        elif self.status.scenario == 'RND':
            path = self.topology.shortest_path[client][self.topology.clients[client]['server']]
            for node in path[1:]:
                delay = path.index(node) * self.status.INTERNAL_COST
                neighbor = self.topology._neighbors_has_content(node, content)
                if self.cache[node].has_content(content):
                    self.cache[node].get_content(content)
                    if measured:
                        self.hit(content, node)
                        self.all_delays.append(delay)
                    break
                
                elif neighbor is not False and self.on_path_routing is False:
                    self.cache[neighbor].get_content(content)
                    delay += [2, 1][neighbor in self.topology.neighbors(node)] * self.INTERNAL_COST
                    if measured:
                        self.hit(content , neighbor)
                        # self.delays[content].append(delay)
                        self.all_delays.append(delay)
                    break
            else:
                if measured:
                    delay = len(path)*self.status.INTERNAL_COST + self.status.EXTERNAL_COST
                    
#                    delay = self.max_delay#(len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST
                    self.all_delays.append(delay)

            self.cache[path[random.randint(1, len(path) - 1)]].put_content(content)
            
        elif self.status.scenario == 'LCD':
            path = self.topology.shortest_path[client][self.topology.clients[client]['server']]
            for node in path[1:]:
                delay = path.index(node) * self.status.INTERNAL_COST

                neighbor = self._neighbors_has_content(node, content)

                if self.cache[node].has_content(content):
                    self.cache[node].get_content(content)
                    idx = path.index(node)
#                    print path, idx, path[idx-1]
                    if idx > 1:
                        self.cache[path[idx-1]].put_content(content)
                    if measured:
                        self.hit(content, node)
                        # self.cache_hit[node][content] += 1
                        # self.delays[content].append(delay)
                        # print 'hit'
                        self.all_delays.append(delay)
                    break
                
            else:
                if content < self.content_threshold * self.status.N_CONTENTS:
#                    popularity = self.status.information[path[-1]][content]['popularity']
                    self.cache[path[-1]].put_content(content)
                if measured:
                    delay = len(path)*self.status.INTERNAL_COST + self.status.EXTERNAL_COST

#                    delay = self.topology.max_delay # (len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST
                    self.all_delays.append(delay)
                    
        elif self.status.scenario == 'MCD':
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
                        self.hit()
                        # self.cache_hit[node][content] += 1
                        # self.delays[content].append(delay)
                        # print 'hit'
                        self.all_delays.append(delay)
                    break
                
            else:
                self.cache[path[-1]].put_content(content)
                if measured:
                    delay = len(path)*self.status.INTERNAL_COST + self.status.EXTERNAL_COST
                    
#                    delay = self.max_delay # (len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST
                    self.all_delays.append(delay)


       
if __name__=='__main__':
    n2 = Network()
    n2.run()
    print 'hit rate', n2.hits/float(n2.status.N_MEASURED_REQUESTS)


