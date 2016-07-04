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
Effect of height of the tree
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
#        network = Network(core, k, h)
        network.reset()
        cnt += 1
        print '-------%s %d with BUDGET=%f-------'%(scenario, cnt, budget)
        
        network.CACHE_BUDGET_FRACTION = budget
        network.scenario = scenario
        network.run()
        print network.cache[20].cache_size

        print 'hit rate = %f'%(network.hits/float(network.N_MEASURED_REQUESTS))
        
        hit_rates.append(network.hits/float(network.N_MEASURED_REQUESTS))
        delays.append(sum(network.all_delays)/float(network.N_MEASURED_REQUESTS))
        
    return hit_rates, delays
    
def cache_budget_alpha_test(core, k, h, budget_values, alpha_values, scenario):
#    hit_rates = []
#    delays = []
    cnt = 0
    H = np.zeros((len(alpha_values), len(budget_values)))
    D = np.zeros((len(alpha_values), len(budget_values)))
    i, j = 0, 0
    
    for alpha in alpha_values:
        j = 0
        for budget in budget_values:
    #        network = Network(core, k, h)
            network.reset()
            network.ALPHA = alpha
            cnt += 1
            print '-------%s %d with BUDGET=%.3f ALPHA=%.2f-------'%(scenario, i*len(budget_values)+j, budget, alpha)
            
            network.CACHE_BUDGET_FRACTION = budget
            network.scenario = scenario
            network.run()
    
            print 'hit rate = %f'%(network.hits/float(network.N_MEASURED_REQUESTS))
            
            H[i, j] = (network.hits/float(network.N_MEASURED_REQUESTS))
            D[i, j] = (sum(network.all_delays)/float(network.N_MEASURED_REQUESTS))
            
            j += 1
        i += 1
        
    return H, D

        
def alpha_test(core, k, h, alpha_values, scenario):
    hit_rates = []
    delays = []
    cnt = 0
    for alpha in alpha_values:
#        network = Network(core, k, h)
        network.reset()
        cnt += 1
        print '-------%s %d with ALPHA=%f-------'%(scenario, cnt, alpha)
        
#        network.CACHE_BUDGET_FRACTION = budget
        network.ALPHA = alpha
        network.scenario = scenario
        network.run()

        print 'hit rate = %f'%(network.hits/float(network.N_MEASURED_REQUESTS))
        
        hit_rates.append(network.hits/float(network.N_MEASURED_REQUESTS))
        delays.append(sum(network.all_delays)/float(network.N_MEASURED_REQUESTS))
        
    return hit_rates, delays


if __name__ == '__main__':
    core = 4
    k = 2
    h = 6
    repeat = 1

    network = Network(core, k, h)
    network.CACHE_BUDGET_FRACTION = .05
    network.N_CONTENTS = 3 * 10 ** 4
    network.N_WARMUP_REQUESTS = 4 * 10 ** 4
    network.N_MEASURED_REQUESTS = 1 * 10 ** 4
    network.GAMMA = 1
    network.ALPHA = .4

    network.INTERNAL_COST = 2
    network.EXTERNAL_COST = 10

    network.on_path_routing = True
    network.on_path_winner = True
    network.relative_popularity = True
    network.cache_placement = 'betweenness'
#    gamma_values = np.array(range(50, 102, 2))/100.
#    hit_rates, delays = gamma_test(core, k, h, gamma_values)
#    

    
    budget_values = np.array(range(0, 1000, 50))/10000.
    alpha_values = np.array(range(1, 13, 1))/10.

    scenarios = [
#                 'CEE', 
#                 'RND', 
                 'LCD',
                 'AUC'
                 ]

    H = []
    D = []
    for scenario in scenarios:
        # alpha_values = np.array(range(1, 30))/10.
        for i in range(repeat):
#                hit_rates, delays = cache_budget_alpha_test(core, k, h, budget_values, alpha_values, scenario)    
                hit_rates, delays = cache_budget_test(core, k, h, budget_values, scenario)
    #            hit_rates, delays = alpha_test(core, k, h, alpha_values, scenario)
                # hit_rates, delays = alpha_test(core, k, h, alpha_values, scenario)
                H.append(hit_rates)
                D.append(delays)

    H = np.array(H)
    D = np.array(D)
    
    colors = ['black', 'red', 'black', 'red']

    np.save('./Results/H', H)
    np.save('./Results/D', D)
    np.save('./Results/B', budget_values)

    X = np.array([list(budget_values)]*len(alpha_values))
    Y = np.array([list(alpha_values)]*len(budget_values))



#    fig = plt.figure()
#    ax = fig.add_subplot(111, projection='3d')
#    for (i,c) in zip(range(1, len(scenarios)),colors[:2]): 
#        ax.plot_surface(X, Y.transpose(), np.mean(H[i*repeat:(i+1)*repeat,:,:], axis=0),
#                        label = scenarios[i],
#                        color = c,
#                        alpha=.8)
#    plt.legend(loc='best')
#    plt.savefig('./Results/budget-hitrate-alpha=%.2f-gamma=%.2f.png' % (network.ALPHA, network.GAMMA))
#    plt.clf()
#
#    for i in range(1, len(scenarios)):
#        fig = plt.figure()
#        ax = fig.add_subplot(111, projection='3d')
#        ax.plot_wireframe(X, Y, np.mean(D[i*repeat:(i+1)*repeat,:,:], axis=0), rstride=10, cstride=10)
#    plt.legend(loc='best')
#    plt.savefig('./Results/%s-budget-hitrate-alpha=%.2f-gamma=%.2f.png' % (scenario, network.ALPHA, network.GAMMA))
#    plt.clf()
    
#    for i in range(len(scenarios)):
##        plt.plot(alpha_values, np.mean(D[i*repeat:(i+1)*repeat], axis=0), label=scenarios[i])
#        plt.plot(budget_values, np.mean(H[i*repeat:(i+1)*repeat], axis=0), label=scenarios[i])
#        # plt.plot(budget_values, np.mean(D[3:6]), label='RND')
#        # plt.plot(budget_values, np.mean(D[6:9]), label='AUC')
#        # plt.plot(budget_values, np.mean(D[9:12]), label='LCD')
#    plt.legend(loc='best')
#    plt.savefig('./Results/%s-budget-hitrate-alpha=%f-gamma=%f.png' % (scenario, network.ALPHA, network.GAMMA))
#    plt.clf()
#
#    for i in range(len(scenarios)):
##        plt.plot(alpha_values, np.mean(D[i*repeat:(i+1)*repeat], axis=0), label=scenarios[i])
#        plt.plot(budget_values, np.mean(D[i*repeat:(i+1)*repeat], axis=0), label=scenarios[i])
#        # plt.plot(budget_values, np.mean(D[3:6]), label='RND')
#        # plt.plot(budget_values, np.mean(D[6:9]), label='AUC')
#        # plt.plot(budget_values, np.mean(D[9:12]), label='LCD')
#    plt.legend(loc='best')
#    plt.savefig('./Results/%s-budget-delay-alpha=%f-gamma=%f.png' % (scenario, network.ALPHA, network.GAMMA))
#    plt.clf()


