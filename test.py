# -*- coding: utf-8 -*-
from network import *
import matplotlib.pylab as plt
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
        
        
        
def cache_budget_test(core, k, h, budget_values, scenario):
    hit_rates = []
    delays = []
    cnt = 0
    for budget in budget_values:
        network = Network(core, k, h)
        cnt += 1
        print '-------Experiment %d with BUDGET=%f-------'%(cnt, budget)
        
        network.CACHE_BUDGET_FRACTION = budget
        network.scenario = scenario
        network.run()

        print 'hit rate = %f'%(network.hits/float(network.N_MEASURED_REQUESTS))
        
        hit_rates.append(network.hits/float(network.N_MEASURED_REQUESTS))
        delays.append(sum(network.all_delays)/float(network.N_MEASURED_REQUESTS))
        
    return hit_rates, delays
#   
        
        
        
def alpha_test(core, k, h, alpha_values, scenario):
    hit_rates = []
    delays = []
    cnt = 0
    for alpha in alpha_values:
        network = Network(core, k, h)
        cnt += 1
        print '-------Experiment %d with ALPHA=%f-------'%(cnt, alpha)
        
        network.ALPHA = alpha
        network.scenario = scenario
        network.run()

        print 'hit rate = %f'%(network.hits/float(network.N_MEASURED_REQUESTS))
        
        hit_rates.append(network.hits/float(network.N_MEASURED_REQUESTS))
        delays.append(sum(network.all_delays)/float(network.N_MEASURED_REQUESTS))
        
    return hit_rates, delays
#   
#    plot(gamma_values, hit_rates)
#    plot(gamma_values)
        

if __name__=='__main__':
    core = 4
    k = 2
    h = 4

    network = Network(core, k, h)
    
#    gamma_values = np.array(range(50, 102, 2))/100.
#    hit_rates, delays = gamma_test(core, k, h, gamma_values)
#    

    # budget_values = [.002, .004, .006, .008, .01, .03, .05, .07, .1, .3, .5, .7, .9, 1]
    budget_values = np.array(range(0, 100, 5))/10000.
    # hit_rates, delays = cache_budget_test(core, k, h, budget_values)


#    H = []
#    D = []
    for scenario in ['LCD']:
        # alpha_values = np.array(range(1, 30))/10.
        hit_rates, delays = cache_budget_test(core, k, h, budget_values, scenario)
        # hit_rates, delays = alpha_test(core, k, h, alpha_values, scenario)
        H.append(hit_rates)
        D.append(delays)
        
    plt.plot(budget_values, H[0], label='CEE')
    plt.plot(budget_values, H[1], label='RND')
    plt.plot(budget_values, H[2], label='AUC')
    plt.plot(budget_values, H[3], label='LCD')
    plt.legend(loc='lower right')
    plt.savefig('./Results/%s-budget-hitrate-alpha=%d-gamma=%d' % (scenario, network.ALPHA, network.GAMMA))
    plt.clf()
    
    plt.plot(budget_values, D[0], label='CEE')
    plt.plot(budget_values, D[1], label='RND')
    plt.plot(budget_values, D[2], label='AUC')
    plt.plot(budget_values, D[3], label='LCD')
    plt.legend(loc='upper right')
    plt.savefig('./Results/%s-budget-delay-alpha=%d-gamma=%d' % (scenario, network.ALPHA, network.GAMMA))
    plt.clf()



