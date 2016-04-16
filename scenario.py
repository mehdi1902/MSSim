# -*- coding: utf-8 -*-

#from network import Network
from workload import StationaryWorkload

class run(object):
    def __init__(self, network):
        self.N_CONTENTS = 3*10**4
        self.N_WARMUP_REQUESTS = 3*10**5
        self.N_MEASURED_REQUESTS = 6*10**5
        self.GAMMA = .9
        self.ALPHA = .6
        
        self.INTERNAL_COST = 2
        self.EXTERNAL_COST = 10
        
        
        self.network = network
        self.workload = StationaryWorkload(self.clients.keys(), self.N_CONTENTS, self.ALPHA, 
                                           n_warmup=self.N_WARMUP_REQUESTS,
                                           n_measured=self.N_MEASURED_REQUESTS)
        
        
                                          
    def execute(self):
        #TODO: separete warmup and test
        counter = 1
        for time, client, content in self.workload:
            if not counter%100000:
                print 'round %d' % counter
            counter += 1
            self.event_run(time, client, content, measured=counter>self.N_WARMUP_REQUESTS+1)
                                    
    def event_run(self, time, client, content, measured=True):
        path = self.shortest_path[client][self.clients[client]['server']]
        for node in path[1:]:
            delay = path.index(node)*self.INTERNAL_COST
            self.update_node_information(node, content, delay, time)

            neighbor = self._neighbors_has_content(node, content)
            
            if self.cache[node].has_content(content):
                if measured:
                    self.hits += 1
#                self.cache_hit[node][content] += 1
#                self.delay[content].append(delay)
#                print 'hit'
                break
            

            #if content cached in neighbors            
            
            elif neighbor:
#                self.cache_hit[neighbor][content] += 1
                delay += [2,1][neighbor in self.topology.neighbors(node)]*self.INTERNAL_COST

                self.update_node_information(neighbor, content, delay, time)
                if measured:
                    self.hits += 1
#                    print 'hit'
#                    self.delays[content].append(delay)
                break
            self.cache[node].put_content(content)
        #Cache miss and decision for cache placement
#        else:
#            self.delays[content].append((len(path)-1)*self.INTERNAL_COST+self.EXTERNAL_COST)
            
#            winner = self._winner_determination(path, content)
#            print winner
#            self.cache[winner].put_content(content)


    def update_node_information(self, node, content, delay, time):
        if content in self.informations[node]:
            info = self.informations[node][content]
            popularity = info['popularity']
            average_delay = info['average_delay']
            last_req = info['last_req']

            popularity = self.GAMMA**(time-last_req)*popularity + 1            
            #TODO: currect beta value
#            beta = max( min(self.GAMMA**(time-last_req), .8), .1 )
            beta = .8
            if average_delay!=None:
                average_delay = (1-beta)*average_delay + beta*delay
            else:
                average_delay = delay
        else:
            popularity = 0
            average_delay = delay
        self.informations[node][content] = {'popularity':popularity,
                                            'average_delay':average_delay,
                                            'last_req':time}
        


