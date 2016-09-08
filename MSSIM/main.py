# -*- coding: utf-8 -*-
from controller import Network
from view import Log
import numpy as np


if __name__ == '__main__':
    n = Network()

    n.status.CACHE_BUDGET_FRACTION = .1
    n.status.ALPHA = 1.
    n.status.GAMMA = 1
    n.time_scale = 1000.
#    n.status.cache_placement = 'betweenness'
#    n.status.N_CONTENTS = 3 * 10 ** 4
    n.status.N_WARMUP_REQUESTS = 3 * 10 ** 4
    n.status.N_MEASURED_REQUESTS = 1 * 10 ** 4
    n.status.N_CONTENTS = 10 ** 4

    n.status.scenario = 'LCD'
    n.status.on_path_winner = True
    n.status.on_path_routing = True
    n.status.relative_popularity = True
    n.content_threshold = 1 #100. / n.status.N_CONTENTS
#    n.status.cache_placement = 'betweenness'

    n.status.core = 4

    n.status.topo_type = 'tree'
    if n.status.scenario == 'AUC':
        n.status.cache_replacement = 'POP'
    else:
        n.status.cache_replacement = 'LRU'

    n.run()
    log = Log(n.status)
    log.write_result()

    log.show_mapping(n.topology.routers.keys(), 500)

#
    #### Check for cache only fraction of contents
#    res = []
#    for i in np.arange(0, 500, 10)/10000.:
#        print i
#        n.content_threshold = i
#        n.run()
#        log = Log(n.status)
#        log.write_result()
#        res.append(n.hits/float(n.status.N_MEASURED_REQUESTS))

    