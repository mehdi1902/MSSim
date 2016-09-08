# -*- coding: utf-8 -*-
import sqlite3 as sql
from model import Status
import sys
import analyze
#from skimage.io import imshow
import matplotlib.pyplot as plt
from matplotlib.pylab import imshow
import numpy as np


class Log(object):
    def __init__(self, status):
        self.status = status
    
    def save_db(self):
        status = Status()
        db = sql.connect('./Steps/data.db', timeout=4)
        cur = db.cursor()
        n = cur.execute('SELECT COUNT(*) FROM parameters').fetchone()[0]
        cur.execute('INSERT INTO parameters VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (n+1,
             status.CACHE_BUDGET_FRACTION,
             status.N_MEASURED_REQUESTS,
             status.N_WARMUP_REQUESTS,
             status.N_CONTENTS,
             status.ALPHA,
             status.INTERNAL_COST,
             status.EXTERNAL_COST,
             status.on_path_routing,
             status.on_path_winner,
             str(status.relative_popularity),
             str(status.cache_placement),
             str(status.scenario),
             str(self.cr_hit),
             str(self.winners),
             status.core,
             status.k,
             status.h,
             status.GAMMA,
             self._v_value(),
             self._u_value(),
             100 * self.hits / float(self.N_MEASURED_REQUESTS),
             sum(self.all_delays) / float(self.N_MEASURED_REQUESTS)
             ))
        db.commit()
        db.close()
        return (n+1)

    def write_result(self):
        hit_rate = 100 * self.status.hits / float(self.status.N_MEASURED_REQUESTS)
        average_delay = sum(self.status.all_delays) / float(self.status.N_MEASURED_REQUESTS)
        print '\rHit rate = >>>>>>>>>>>>>>>> %.2f' % (hit_rate)
        print 'Average delay = %f' % (average_delay)

    def gather_parameters(self, mode=None, *arg):
        info = dict()
        info['cache_budget_fraction'] = self.status.CACHE_BUDGET_FRACTION
        info['N_CONTENTS'] = self.status.N_CONTENTS
        info['N_MEASURED_REQ'] = self.status.N_MEASURED_REQUESTS
        info['N_WARMUP_REQ'] = self.status.N_WARMUP_REQUESTS
        info['hit_rate'] = 100 * self.status.hits / float(self.status.N_MEASURED_REQUESTS)
        info['delay'] = sum(self.status.all_delays) / float(self.status.N_MEASURED_REQUESTS)
        info['alpha'] = self.status.ALPHA
        info['on_path_routing'] = self.status.on_path_routing
        info['on_path_winner'] = self.status.on_path_winner
        info['rel_pop'] = self.status.relative_popularity
        info['cache_placement'] = self.status.cache_placement
        info['scenario'] = self.status.scenario
        info['core'] = self.status.core
        info['k'] = self.status.k
        info['h'] = self.status.h
        info['v_value'] = None #self._v_value()
        info['u_value'] = None #self._u_value()

        if mode == 'budget':
            info['cache_budget_fraction'] = arg[0]
        if mode == 'alpha':
            info['alpha'] = arg[0]
        return info

    def show_mapping(self, routers, number):
        cr_hits = analyze.content_router_map(range(number), routers, self.status.cr_hit)
        cr_winners = analyze.content_router_map(range(number), routers, self.status.winners)

        fig = plt.figure()

        a = fig.add_subplot(1, 4, 1)
        a.set_title('hits')
        imshow((cr_hits / np.max(cr_hits)) > 0)

        a = fig.add_subplot(1, 4, 2)
        a.set_title('winners')
        imshow((cr_winners / np.max(cr_winners)) > 0)

        a = fig.add_subplot(1, 4, 3)
        a.set_title('n hits')
        imshow(analyze.normalize_contents(cr_hits / np.max(cr_hits)))

        a = fig.add_subplot(1, 4, 4)
        a.set_title('n winners')
        imshow(analyze.normalize_contents(cr_winners / np.max(cr_winners)))

#        c_id = n.save_db()
#        plt.savefig('./Steps/%i.png'%(c_id))

