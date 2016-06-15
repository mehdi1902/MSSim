# -*- coding: utf-8 -*-
import numpy as np

def content_router_map(contents, routers, winners):
    c = {}
    for i in zip(contents, range(len(contents))):
        c[i[0]] = i[1]
        
    r = {}
    for i in zip(routers, range(len(routers))):
        r[i[0]] = i[1]
        
#    print r
    cr_map = np.zeros((len(contents), len(routers)))
    for w in winners:
        content = w[0]
        router = w[1]
        if content in contents and router in routers:
            cr_map[c[content], r[router]] += 1
    return cr_map
    
def normalize_contents(cr_map):
    for i in cr_map:
        i /= max(np.max(i), 10e-10)
    return cr_map