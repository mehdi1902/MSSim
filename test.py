# -*- coding: utf-8 -*-
from network import *
import matplotlib.pylab as plt
import numpy as np
import pickle



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

        print 'hit rate = %f' % (network.hits/float(network.N_MEASURED_REQUESTS))
        
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
        print '-------%s %d with BUDGET=%f-------'%(scenario, cnt, budget)
        
        network.CACHE_BUDGET_FRACTION = budget
        network.scenario = scenario
        network.run()

        print 'hit rate = %f'%(network.hits/float(network.N_MEASURED_REQUESTS))
        
        hit_rates.append(network.hits/float(network.N_MEASURED_REQUESTS))
        delays.append(sum(network.all_delays)/float(network.N_MEASURED_REQUESTS))
        
    return hit_rates, delays

        
def alpha_test(core, k, h, alpha_values, scenario):
    hit_rates = []
    delays = []
    cnt = 0
    for alpha in alpha_values:
        network = Network(core, k, h)
        cnt += 1
        print '-------%s %d with ALPHA=%f-------' % (scenario, cnt, alpha)
        
        network.ALPHA = alpha
        network.scenario = scenario
        network.run()

        print 'hit rate = %f'% (network.hits/float(network.N_MEASURED_REQUESTS))
        
        hit_rates.append(network.hits/float(network.N_MEASURED_REQUESTS))
        delays.append(sum(network.all_delays)/float(network.N_MEASURED_REQUESTS))
        
    return hit_rates, delays


if __name__ == '__main__':
    core = 4
    k = 2
    h = 6
    repeat = 3

    network = Network(core, k, h)
    
#    gamma_values = np.array(range(50, 102, 2))/100.
#    hit_rates, delays = gamma_test(core, k, h, gamma_values)
#    

    # budget_values = [.002, .004, .006, .008, .01, .03, .05, .07, .1, .3, .5, .7, .9, 1]
    budget_values = np.array(range(0, 1000, 10))/10000.
    # hit_rates, delays = cache_budget_test(core, k, h, budget_values)

    scenarios = ['CEE', 'RND', 'LCD', 'AUC']

    H = []
    D = []
    for scenario in scenarios:
        # alpha_values = np.array(range(1, 30))/10.
        for i in range(repeat):
            hit_rates, delays = cache_budget_test(core, k, h, budget_values, scenario)
            # hit_rates, delays = alpha_test(core, k, h, alpha_values, scenario)
            H.append(hit_rates)
            D.append(delays)

    H = np.array(H)
    D = np.array(D)

    np.save('./Results/H', H)
    np.save('./Results/D', D)
    np.save('./Results/B', budget_values)

#    f = open('./Results/H', 'w+')
#    f.write(str(H))
#    f.close()
#
#    f = open('./Results/D', 'w+')
#    f.write(str(D))
#    f.close()
#
#    f = open('./Results/B', 'w+')
#    f.write(str(budget_values))
#    f.close()

    for i in range(len(scenarios)):
        plt.plot(budget_values, np.mean(H[i*repeat:(i+1)*repeat], axis=0), label=scenarios[i])
        # plt.plot(budget_values, np.mean(H[3:6]), label='RND')
        # plt.plot(budget_values, np.mean(H[6:9]), label='AUC')
        # plt.plot(budget_values, np.mean(H[9:12]), label='LCD')
    plt.legend(loc='lower right')
    plt.savefig('./Results/%s-budget-hitrate-alpha=%d-gamma=%d' % (scenario, network.ALPHA, network.GAMMA))
    plt.clf()
    
    for i in range(len(scenarios)):
        plt.plot(budget_values, np.mean(D[i*repeat:(i+1)*repeat], axis=0), label=scenarios[i])
        # plt.plot(budget_values, np.mean(D[3:6]), label='RND')
        # plt.plot(budget_values, np.mean(D[6:9]), label='AUC')
        # plt.plot(budget_values, np.mean(D[9:12]), label='LCD')
    plt.legend(loc='upper right')
    plt.savefig('./Results/%s-budget-delay-alpha=%d-gamma=%d' % (scenario, network.ALPHA, network.GAMMA))
    plt.clf()
    

