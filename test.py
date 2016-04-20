# -*- coding: utf-8 -*-
from network import *
from matplotlib.pylab import plot
import numpy as np


'''
Effect of CACHE_BUDGET
Effect of GAMMA
Effect of topology parameters
Test for on-path winner determination and off-path
Effect of caching everything or select
'''

def gamma_test(core, k, h, gamma_values):
    hit_rates = []
    delays = []
    cnt = 0
    for gamma in gamma_values:
        network = Network(core, k, h)
        cnt += 1
        print '-------Experiment %d with GAMMA=%f-------'%(cnt, gamma)
        
        network.GAMMA = gamma
        network.run()

        print 'hit rate = %f'%(network.hits/float(network.N_MEASURED_REQUESTS))
        
        hit_rates.append(network.hits/float(network.N_MEASURED_REQUESTS))
        delays.append(sum(network.all_delays)/float(network.N_MEASURED_REQUESTS))
        
    return hit_rates, delays
#    plot(gamma_values, hit_rates)
#    plot(gamma_values)
        
        
        
def cache_budget_test(core, k, h, budget_values):
    hit_rates = []
    delays = []
    cnt = 0
    for budget in budget_values:
        network = Network(core, k, h)
        cnt += 1
        print '-------Experiment %d with BUDGET=%f-------'%(cnt, budget)
        
        network.CACHE_BUDGET_FRACTION = budget
        network.run()

        print 'hit rate = %f'%(network.hits/float(network.N_MEASURED_REQUESTS))
        
        hit_rates.append(network.hits/float(network.N_MEASURED_REQUESTS))
        delays.append(sum(network.all_delays)/float(network.N_MEASURED_REQUESTS))
        
    return hit_rates, delays
#   
        
        
        
        
        
        
        
        
        
if __name__=='__main__':
#    network = Network(4,2,4)
    
    core = 4
    k = 2
    h = 4    
    
#    gamma_values = np.array(range(50, 102, 2))/100.
#    hit_rates, delays = gamma_test(core, k, h, gamma_values)
#    

    budget_values = [.002, .004, .006, .008, .01, .03, .05, .07, 1]
    hit_rates, delays = cache_budget_test(core, k, h, budget_values)







