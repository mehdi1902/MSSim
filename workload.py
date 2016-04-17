# -*- coding: utf-8 -*-
from stats import TruncatedZipfDist
import random

class StationaryWorkload(object):
    def __init__(self, clients, n_contents, alpha, 
                    n_warmup, n_measured, rate=1.0, seed=None, **kwargs):
        if alpha < 0:
            raise ValueError('alpha must be positive')
        self.clients = clients
        self.zipf = TruncatedZipfDist(alpha, n_contents)
        self.n_contents = n_contents
        self.contents = range(1, n_contents + 1)
        self.alpha = alpha
        self.rate = rate
        self.n_warmup = n_warmup
        self.n_measured = n_measured
#        random.seed(seed)
        
        
    def __iter__(self):
        req_counter = 0
        t_event = 0.0
        while req_counter < self.n_warmup + self.n_measured:
            t_event += (random.expovariate(self.rate))
#            t_event += 1
            client = random.choice(self.clients)
            content = int(self.zipf.rv())
#            client = 30
#            content = 0
#            event = {'client':client, 'content': content}
            yield (t_event, client, content)
            req_counter += 1
        raise StopIteration()
#