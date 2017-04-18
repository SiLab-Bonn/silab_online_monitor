''' Histograms the Mimosa26 hit table'''

import time
import numpy as np

# Online monitor imports
from online_monitor.converter.transceiver import Transceiver
from online_monitor.utils import utils

from pybar_fei4_interpreter.data_histograming import PyDataHistograming

n_fes = 5

def frontend_name_to_fe_index(self, frontend_name):
    for index, frontend in enumerate(self.frontends):
        if frontend_name == frontend[0]:
            return index

class BeastHistogrammer(Transceiver):

    def setup_transceiver(self):
        self.set_bidirectional_communication()  # We want to be able to change the histogrammmer settings

    def setup_interpretation(self):
        self.stave_occupancy_arrays = np.zeros(shape=(n_fes * 80, 336), dtype=np.int32)  # Five Fe per stave
        self.eps_array = np.zeros(shape=(1, n_fes), dtype=np.int32)
        self.hps_array = np.zeros(shape=(1, n_fes,), dtype=np.int32)
        self.time_array = np.zeros(shape=(1, n_fes,), dtype=np.float64)
        self.tot_hist = np.zeros(shape=(n_fes, 16), dtype=np.float64)    #a list to hold the objects
                
        self.histogrammers = []
        for _ in range(n_fes):
            histograming = PyDataHistograming()
            histograming.set_no_scan_parameter()
            histograming.create_occupancy_hist(True)
            histograming.create_rel_bcid_hist(False)
            histograming.create_tot_hist(True)
            histograming.create_tdc_hist(True)
            self.histogrammers.append(histograming)
        
        
        self.n_readouts = 0
        self.readout = 0
        self.fps = [0, 0, 0, 0, 0]  # data frames per second   , a list to store the values for each front end
        self.hps = [0, 0, 0, 0, 0]  # hits per second
        self.eps = [0, 0, 0, 0, 0]  # events per second
        self.plot_delay = 0
        self.total_hits = [0, 0, 0, 0, 0]
        self.total_events = [0, 0, 0, 0, 0]
        self.time = [0, 0, 0, 0, 0]
        self.start = time.time()
        self.temp = [0.0]
        self.mask_noisy_pixel = False
        self.mean_fps = 0
        self.mean_hps = 0
        self.mean_eps = 0
        self.mean_rth = 0  # rth : recent_total_hits
        self.mean_rte = 0  # rte : recent_total_events
        # Histogrammes from interpretation stored for summing
        self.tdc_counters = np.zeros(shape=(n_fes, 4096), dtype=None)
#        self.tdc_counters = [None] * 4096
        
        
    def deserialze_data(self, data):
        # return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)
        datar, meta = utils.simple_dec(data)  # meta is a list
        if 'hits' in meta:
            meta['hits'] = datar
#        print meta
        return meta
        print meta.shape
        print type()
    def interpret_data(self, data):
        for actual_device_data in data:  # Loop over all devices of actual received data which is type 'list'
            frontend_name, frontend_data = actual_device_data  # type of actual_device_data is 'tuple' of frontend_name and it's data, where data is frontend_data and type 'dict'
            frontend_index = frontend_name_to_fe_index(self, frontend_name)
            self.recent_total_hits = [0, 0, 0, 0, 0]
            self.recent_total_events = [0, 0, 0, 0, 0]
            recent_time = [0, 0, 0, 0, 0]
            recent_fps = [0, 0, 0, 0, 0]
            recent_hps = [0, 0, 0, 0, 0]
            recent_eps = [0, 0, 0, 0, 0]
            
            if 'hits' in frontend_data:
                frontend_hits = frontend_data['hits']
                self.histogrammers[frontend_index].add_hits(frontend_hits)
                self.stave_occupancy_arrays[frontend_index * 80:(frontend_index + 1) * 80, :] = self.histogrammers[frontend_index].get_occupancy()[::-1, :, 0]
#                print np.any(frontend_data['tdc_counters'])
                self.tot_hist[frontend_index] = self.histogrammers[frontend_index].get_tot_hist()
                
#                 print type(self.tdc_counters)
#                 print frontend_data.has_key('tdc_counters')
#                 print "#############",frontend_index
#                 print np.count_nonzero((frontend_data['tdc_counters']))
                 
                # Sum up interpreter histograms
                if self.tdc_counters[frontend_index] is not None:
                    self.tdc_counters[frontend_index] += frontend_data['tdc_counters']
                else:
                    self.tdc_counters[frontend_index] = frontend_data['tdc_counters'].copy()  # Copy needed to give ownage to histogrammer
#                 print "**************************", frontend_index
#                 print np.count_nonzero(self.tdc_counters[frontend_index])
                    
            if 'meta_data' in frontend_data:
                meta_data = frontend_data['meta_data']
                t = time.time()-self.start
                
                # Get current readout data
                self.recent_total_hits[frontend_index] = meta_data['n_hits']
                self.recent_total_events[frontend_index] = meta_data['n_events']
                recent_time[frontend_index] = meta_data['timestamp_start']
                
                # Calculate actual readout rates
                recent_fps[frontend_index] = 1.0 / (recent_time[frontend_index] - self.time[frontend_index])
                recent_eps[frontend_index] = (self.recent_total_events[frontend_index] - self.total_events[frontend_index]) / (recent_time[frontend_index] - self.time[frontend_index])
                recent_hps[frontend_index] = (self.recent_total_hits[frontend_index] - self.total_hits[frontend_index]) / (recent_time[frontend_index] - self.time[frontend_index])   
                
                # Update counter variables
                self.time[frontend_index] = recent_time[frontend_index]
                self.total_hits[frontend_index] = self.recent_total_hits[frontend_index]
                self.total_events[frontend_index] = self.recent_total_events[frontend_index]
        
                # Filter and update rate values
                self.fps[frontend_index] = (self.fps[frontend_index] * 0.7 + recent_fps[frontend_index] * 0.3)
                self.eps[frontend_index] = (self.eps[frontend_index] * 0.7 + recent_eps[frontend_index] * 0.3)
                self.hps[frontend_index] = (self.hps[frontend_index] * 0.7 + recent_hps[frontend_index] * 0.3)
                
                self.eps_array = np.absolute(np.concatenate((self.eps_array, np.array([self.eps])), axis=0))
                self.hps_array = np.absolute(np.concatenate((self.hps_array, np.array([self.hps])), axis=0))
                self.time_array = np.concatenate((self.time_array, np.array([self.time])), axis=0)
                self.temp.append(t)
                
                self.mean_fps = sum(self.fps) / n_fes  #change the dividing number as per the number of chips 
                self.mean_hps = sum(self.hps) / n_fes
                self.mean_eps = sum(self.eps) / n_fes
                self.mean_rth = sum(self.hps) / n_fes
                self.mean_rte = sum(self.eps) / n_fes
#                meta_data.update_rate({'fps': self.mean_fps, 'hps': self.mean_hps, 'total_hits': self.mean_rth, 'eps': self.mean_eps, 'total_events': self.self.mean_rte})
            

            self.readout += 1

        if self.n_readouts != 0:  # = 0 for infinite integration
            if self.readout % self.n_readouts == 0:
                for frontend_index in range(n_fes):
                    self.histogrammers[frontend_index].reset()
                    self.tdc_counters[frontend_index] = np.zeros(shape=(1, 4096), dtype=None)
                self.readouts = 0
        
        
        
            
        histogrammed_data = {'occupancies': self.stave_occupancy_arrays, 
                             'eps_array': self.eps_array, 
                             'hps_array': self.hps_array, 
                             'time_stamp':self.time_array, 
                             'fps': self.mean_fps, 
                             'hps': self.mean_hps, 
                             'total_hits': self.mean_rth, 
                             'eps': self.mean_eps, 
                             'total_events': self.mean_rte, 
                             'time': self.temp,
                             'tdc_counters': self.tdc_counters,
                             'tot_hist': self.tot_hist}
        return [histogrammed_data]
            
    def serialze_data(self, data):
        # return jsonapi.dumps(data, cls=utils.NumpyEncoder)
        
        if 'occupancies' in data:
            hits_data = data['occupancies']
            data['occupancies'] = None
            return utils.simple_enc(hits_data, data)
        else:
            return utils.simple_enc(None, data)
            
        
    def handle_command(self, command):
        if command[0] == 'RESET':
            for frontend_index in range(n_fes):
                self.histogrammers[frontend_index].reset()
                self.tdc_counters[frontend_index] = np.zeros(shape=(1, 4096), dtype=None)
            self.eps_array = np.zeros(shape=(1, n_fes), dtype=np.int32)
            self.hps_array = np.zeros(shape=(1, n_fes,), dtype=np.int32)
            self.start = time.time()
            self.temp = [0.0]
            self.time = [0, 0, 0, 0, 0]
            self.total_hits = [0, 0, 0, 0, 0]
            self.total_events = [0, 0, 0, 0, 0]
            #self.recent_total_events = [0, 0, 0, 0, 0]
            #self.recent_total_hits = [0, 0, 0, 0, 0]
           
        else:
            self.n_readouts = int(command[0])

