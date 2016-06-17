# -*- coding: utf-8 -*-
# from topology import Topology
from workload import *
from random import shuffle
import fnss
import networkx as nx
import sqlite3 as sql
# from cache import *
from skimage.io import imshow
import sys
from analyze import *
import matplotlib.pyplot as plt



class Network():
    def __init__(self, core, k, h):
        self.CACHE_BUDGET_FRACTION = .05
        self.N_CONTENTS = 3 * 10 ** 4
        self.N_WARMUP_REQUESTS = 4 * 10 ** 4
        self.N_MEASURED_REQUESTS = 1 * 10 ** 4
        self.GAMMA = 1
        self.ALPHA = .8

        self.INTERNAL_COST = 2
        self.EXTERNAL_COST = 10

        self.on_path_routing = True
        self.on_path_winner = True
        self.relative_popularity = True
        self.cache_placement = 'uniform'
        self.scenario = 'AUC'
        
        self.saved_shots = []
        self.shots = []

        self.max_delay = h * self.INTERNAL_COST + self.EXTERNAL_COST

        # Uniform cache assignement
        self.core, self.k, self.h = core, k, h
        
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
        self.cr_hit = []
        self.winners = []

        

        self.cnt = 0

#        self.ind = [ 0.21561868,  0.91459301,  0.        ,  0.25700366,  0.358362  ,\
#        0.54709407,  0.99226817,  0.12912687,  0.39532304,  0.11537119,\
#        0.52464204,  0.66921722,  0.66034903,  0.03366341]

    def run(self):
        self._cache_budget = (self.CACHE_BUDGET_FRACTION * self.N_CONTENTS)
        self.cache = self.place_caches()
        self.workload = StationaryWorkload(self.clients.keys(), self.N_CONTENTS, self.ALPHA,
                                           n_warmup=self.N_WARMUP_REQUESTS,
                                           n_measured=self.N_MEASURED_REQUESTS)
        self.hits = 0
        self.all_delays = []
        self.cr_hit = []
        self.winners = []
        
        counter = 1
        for time, client, content in self.workload:            
            if not counter % 100:
#                sys.stdout.write('\rProgress: {0:.2f}%\tHit rate: {1:.3f}%'.
#                                 format(100 * counter / float(self.N_MEASURED_REQUESTS + self.N_WARMUP_REQUESTS),
#                                        (100 * self.hits / float(counter - self.N_WARMUP_REQUESTS + 10e-10))))
                sys.stdout.write('\rProgress: {0:.2f}%\t'.
                                 format(100 * counter / float(self.N_MEASURED_REQUESTS + self.N_WARMUP_REQUESTS)))
           
                sys.stdout.flush()
            counter += 1
            self.event_run(time, client, content, measured=counter > self.N_WARMUP_REQUESTS + 1)
            if counter in self.shots:
                self.saved_shots.append(self)
#        sys.stdout.write('\r')
#        sys.stdout.flush()

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
                        self.hit(content, node)
                        self.all_delays.append(delay)
                    break
                # Hit from a neighbor
                elif neighbor is not False and self.on_path_routing is False:
                    self.cache[neighbor].get_content(content)
                    # self.cache_hit[neighbor][content] += 1
                    delay += [2, 1][neighbor in self.topology.neighbors(node)] * self.INTERNAL_COST
                    
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
                
                winner = self._winner_determination(path, content, time)
                if measured:
                    # self.delays[content].append((len(path)-1)*self.INTERNAL_COST+self.EXTERNAL_COST)
                    delay = self.max_delay # (len(path) - 1) * self.INTERNAL_COST + self.EXTERNAL_COST
                    self.all_delays.append(delay)
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
                        self.hit(content, node)
#                        self.cr_hit.append((content, node))
                        self.all_delays.append(delay)
                    break
                    
                    
                elif neighbor is not False and self.on_path_routing is False:
                    self.cache[neighbor].get_content(content)
                    delay += [2, 1][neighbor in self.topology.neighbors(node)] * self.INTERNAL_COST
                    if measured:
                        self.hit(content, neighbor)
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
                neighbor = self._neighbors_has_content(node, content)
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
                        self.hit(content, node)
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
                        self.hit()
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

        if self.on_path_winner:
            nodes = path[1:]
        else:
            for node in path:
                for v in self.neighbors2[node]:
                # for v in self.topology.neighbors(node):
                    if v not in self.clients:
                        nodes.append(v)
            nodes = list(set(nodes))
        

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
#                for u in self.neighbors2[other]:
                '''
                cache of a content effects on nodes in neighbors2
                '''
                        
                if other == v:# and u == v:
                    #v_value
                    value = popularity + 10 * (self.cache[v].cache_size <> len(self.cache[v].contents))
                    #v_value
                    if print_res:
                        print v, self.topology.node[v]['depth'], value, average_distance
                else:
                    if content in self.informations[other]:
                        average_distance_u, popularity_u, last_req_u, total_req_u = self.get_node_information(other, content, time)
                    #u_value
                    value = 0
                    #u_value
#                    value = popularity_u / (average_distance_u+[1,2][other in self.topology.neighbors(v)]*self.INTERNAL_COST)
                sum_value += value

            # if sum_value > 0:
            #     print sum_value
            if sum_value >= max_val:
                max_val = sum_value
                winner = v
            # sum_value = 0
        return winner #if max_val > 0 else None

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
            total_req = self.informations[node]['total_req']
        else:
            average_distance = self.EXTERNAL_COST
            last_req = time
            popularity = 0
            total_req = 1
        if self.relative_popularity:
            popularity /= float(total_req)
        return float(average_distance), float(popularity), last_req, float(total_req)

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

    def place_caches(self):
        cache_budget = self._cache_budget
        if self.cache_placement == 'betweenness':
            betweenness = nx.betweenness_centrality(self.topology)
        elif self.cache_placement == 'uniform':
            betweenness = {node: .1 for node in self.routers}
        total_betweenness = float(sum(betweenness.values()))
        return {node: Cache(int(round(cache_budget * betweenness[node] / total_betweenness)))
                for node in self.routers}
        # cache_size = cache_budget / len(self.routers)
        # return {node: Cache(int(round(cache_size))) for node in self.routers}

    def reset(self):
        self.hits = 0
        self.all_delays = []
        self.informations = {node: {} for node in self.topology.node}
        self.cr_hit = []
        self.winners = []

    def write_result(self):
        sys.stdout.write('\rHit rate = {0:.2f}%'.format(100 * self.hits / float(self.N_MEASURED_REQUESTS)))
        print '\nAverage delay = %f' % (sum(self.all_delays) / float(self.N_MEASURED_REQUESTS))

    def hit(self, *args):
        self.hits += 1
        if len(args)==2:
            content = args[0]
            router = args[1]
            n.cr_hit.append((content, router))
#            if self.scenario == 'AUC':
#                self.informations[router][content]['popularity'] *= 20
        # self.cache_hit[node][content] += 1
        # self.delays[content].append(delay)
        # self.all_delays.append(delay)

    def gather_parameters(self, mode=None, *arg):
        info = dict()
        info['cache_budget_fraction'] = self.CACHE_BUDGET_FRACTION
        info['N_CONTENTS'] = self.N_CONTENTS
        info['N_MEASURED_REQ'] = self.N_MEASURED_REQUESTS
        info['N_WARMUP_REQ'] = self.N_WARMUP_REQUESTS
        info['alpha'] = self.ALPHA
        info['on_path_routing'] = self.on_path_routing
        info['on_path_winner'] = self.on_path_winner
        info['rel_pop'] = self.relative_popularity
        info['cache_placement'] = self.cache_placement
        info['scenario'] = self.scenario
        info['core'] = self.core
        info['k'] = self.k
        info['h'] = self.h
        info['v_value'] = self._v_value()
        info['u_value'] = self._u_value()
        info['hit_rate'] = 100 * self.hits / float(self.N_MEASURED_REQUESTS)
        info['delay'] = sum(self.all_delays) / float(self.N_MEASURED_REQUESTS)
        if mode == 'budget':
            info['cache_budget_fraction'] = arg[0]
        if mode == 'alpha':
            info['alpha'] = arg[0]
        return info
    
    def save_latex(self, n):
        f = open('./Steps/results.tex', 'r+')
        tex = f.read()
        image = '\n\n\\begin{figure}[h]\n\\centering\n\\includegraphics[scale=.6]{%i.png}\n\\end{figure}\n'%(n)
        i = tex.find('%%here%%')
        
        info = str(self.gather_parameters())
        info = info.replace(', ', '\n\n')
        info = info.replace('{', '')
        info = info.replace('}', '')
        info = info.replace('_', ' ')
                
        res = tex[:i] + image + '\n\n\n' + 'id: ' + str(n) + info 
        res +=  '\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n' + tex[i:] 
        res += '\\pagebreak\n'
        
        f.seek(0)
        f.write(res)
        f.close()
        
    
    def save_db(self):
        db = sql.connect('./Steps/data.db', timeout=4)
        cur = db.cursor()
        n = cur.execute('SELECT COUNT(*) FROM parameters').fetchone()[0]
        cur.execute('INSERT INTO parameters VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (n+1,
             self.CACHE_BUDGET_FRACTION,
             self.N_MEASURED_REQUESTS,
             self.N_WARMUP_REQUESTS,
             self.N_CONTENTS,
             self.ALPHA,
             self.INTERNAL_COST,
             self.EXTERNAL_COST,
             self.on_path_routing,
             self.on_path_winner,
             str(self.relative_popularity),
             str(self.cache_placement),
             str(self.scenario),
             str(self.cr_hit),
             str(self.winners),
             self.core,
             self.k,
             self.h,
             self.GAMMA,
             self._v_value(),
             self._u_value(),
             100 * self.hits / float(self.N_MEASURED_REQUESTS),
             sum(self.all_delays) / float(self.N_MEASURED_REQUESTS)
             ))
        db.commit()
        db.close()
        return n+1
    
    def _v_value(self):
        f = open('network.py', 'r').read().split('#v_value')[1].split('=')[1]
        return f.replace('\n', '')
        
    def _u_value(self):
        f = open('network.py', 'r').read().split('#u_value')[1].split('=')[1]
        return f.replace('\n', '')
    
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
        self.has_cache = True

    def has_cache(self):
        return self._has_cache

    def get_cache_size(self):
        return self.cache_size

    def get_replace_candidate(self):
        return self.contents[-1] if len(self.contents) == self.cache_size else None


if __name__ == '__main__':
    n = Network(2, 2, 6)
    
    scenarios = [
#                 ('CEE', True),
                 ('AUC', True),
#                 ('RND', True),
#                 ('MCD', True),
#                 ('LCD', True),
#                 ('CEE', False),
#                 ('AUC', False),                 
#                 ('RND', False),
#                 ('MCD', False),                 
                ]

    n.on_path_winner = True                
#    n.relative_popularity = True
#    n.cache_placement = 'betweenness'
#    
    RP = [
        True, 
#        False,
        ]
        
    CP = [
#        'uniform', 
        'betweenness',
        ]
        
    n.shots = [400001]
    

    for (scr, op) in scenarios:
        fig = plt.figure()
        i = 0
        for rp in RP:
            for cp in CP:

                print '------%s-%s-----'%(scr, ['Off', 'On'][op])
                n.reset()
                n.on_path_routing = op
                n.scenario = scr
                
                n.relative_popularity = rp
                n.cache_placement = cp
                
                n.run()
                n.write_result()
        
                    
        
#                if n.scenario == 'AUC':
                cr_hits = content_router_map(range(1000), n.routers.keys(), n.cr_hit)
                cr_winners = content_router_map(range(1000), n.routers.keys(), n.winners)
                
                w = 4
                a=fig.add_subplot(len(RP),w*len(CP),i+1)
                a.set_title('hits')
                imshow(cr_hits/np.max(cr_hits)>0)
                
                a=fig.add_subplot(len(RP),w*len(CP),i+2)
                a.set_title('winners')
                imshow(cr_winners/np.max(cr_winners)>0)
                
                a=fig.add_subplot(len(RP),w*len(CP),i+3)
                a.set_title('n hits')
                imshow(normalize_contents(cr_hits/np.max(cr_hits)))
                
                a=fig.add_subplot(len(RP),w*len(CP),i+4)
                a.set_title('n winners')
                imshow(normalize_contents(cr_winners/np.max(cr_winners)))

                c_id = n.save_db()
                plt.savefig('./Steps/%i.png'%(c_id))
                n.save_latex(c_id)
                
                i += w
