''' Histograms the ATLAS-FEI4 hit table and integrated the interpretation histograms'''

import time
from zmq.utils import jsonapi
import numpy as np

# Online monitor imports
from online_monitor.converter.transceiver import Transceiver
from online_monitor.utils import utils

# pyBAR related imports
from pybar_fei4_interpreter.data_histograming import PyDataHistograming


class PybarFEI4Histogrammer(Transceiver):

    def setup_transceiver(self):
        self.set_bidirectional_communication()  # We want to be able to change the histogrammmer settings

    def setup_interpretation(self):
        self.histograming = PyDataHistograming()
        self.histograming.set_no_scan_parameter()
        self.histograming.create_occupancy_hist(True)
        self.histograming.create_rel_bcid_hist(True)
        self.histograming.create_tot_hist(True)
        self.histograming.create_tdc_hist(True)
        # Variables
        self.n_readouts = 0
        self.readout = 0
        self.fps = 0  # data frames per second
        self.hps = 0  # hits per second
        self.eps = 0  # events per second
        self.plot_delay = 0
        self.total_hits = 0
        self.total_events = 0
        self.updateTime = time.time()
        # Histogrammes from interpretation stored for summing
        self.tdc_counters = None
        self.error_counters = None
        self.service_records_counters = None
        self.trigger_error_counters = None
        self.active_tab = None
        self.dut1_hist_tab = 1 # FIXME: maybe better to do sth like DUT1.tabPosition() to get tab index of DUT1 histogrammer
        
    def deserialze_data(self, data):
        #return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)
        
        datar, meta  = utils.simple_dec(data)
        if 'hits' in meta:
            meta['hits'] = datar
        return meta
        

    def interpret_data(self, data):
        if self.active_tab != self.dut1_hist_tab: # Only do something when user clicked on 'DUT1' in online_monitor ; DUT1-tab is #1
            #print 'FEI4 hist doing nothing'
            return
        if 'meta_data' in data[0][1]:  # Meta data is directly forwarded to the receiver, only hit data, event counters are histogramed; 0 from frontend index, 1 for data dict
            meta_data = data[0][1]['meta_data']
            now = time.time()
            recent_total_hits = meta_data['n_hits']
            recent_total_events = meta_data['n_events']
            recent_fps = 1.0 / (now - self.updateTime)  # calculate FPS
            recent_hps = (recent_total_hits - self.total_hits) / (now - self.updateTime)
            recent_eps = (recent_total_events - self.total_events) / (now - self.updateTime)
            self.updateTime = now
            self.total_hits = recent_total_hits
            self.total_events = recent_total_events
            self.fps = self.fps * 0.7 + recent_fps * 0.3
            self.hps = self.hps + (recent_hps - self.hps) * 0.3 / self.fps
            self.eps = self.eps + (recent_eps - self.eps) * 0.3 / self.fps
            meta_data.update({'fps': self.fps, 'hps': self.hps, 'total_hits': self.total_hits, 'eps': self.eps, 'total_events': self.total_events})
            return [data[0][1]]

        self.readout += 1

        if self.n_readouts != 0:  # = 0 for infinite integration
            if self.readout % self.n_readouts == 0:
                self.histograming.reset()
                self.tdc_counters = np.zeros_like(self.tdc_counters)
                self.error_counters = np.zeros_like(self.error_counters)
                self.service_records_counters = np.zeros_like(self.service_records_counters)
                self.trigger_error_counters = np.zeros_like(self.trigger_error_counters)
                self.readouts = 0

        interpreted_data = data[0][1]

        self.histograming.add_hits(interpreted_data['hits'])

        # Sum up interpreter histograms
        if self.tdc_counters is not None:
            self.tdc_counters += interpreted_data['tdc_counters']
        else:
            self.tdc_counters = interpreted_data['tdc_counters'].copy()  # Copy needed to give ownage to histogrammer
        if self.error_counters is not None:
            self.error_counters += interpreted_data['error_counters']
        else:
            self.error_counters = interpreted_data['error_counters'].copy()  # Copy needed to give ownage to histogrammer
        if self.service_records_counters is not None:
            self.service_records_counters += interpreted_data['service_records_counters']
        else:
            self.service_records_counters = interpreted_data['service_records_counters'].copy()  # Copy needed to give ownage to histogrammer
        if self.trigger_error_counters is not None:
            self.trigger_error_counters += interpreted_data['trigger_error_counters']
        else:
            self.trigger_error_counters = interpreted_data['trigger_error_counters'].copy()  # Copy needed to give ownage to histogrammer

        histogrammed_data = {
            'occupancy': self.histograming.get_occupancy(),
            'tot_hist': self.histograming.get_tot_hist(),
            'tdc_counters': self.tdc_counters,
            'error_counters': self.error_counters,
            'service_records_counters': self.service_records_counters,
            'trigger_error_counters': self.trigger_error_counters,
            'rel_bcid_hist': self.histograming.get_rel_bcid_hist()
        }

        return [histogrammed_data]

    def serialze_data(self, data):
        #return jsonapi.dumps(data, cls=utils.NumpyEncoder)
        
        if 'occupancies' in data:
            hits_data  = data['occupancies']
            data['occupancies'] = None
            return utils.simple_enc(hits_data, data)
        else:
            return utils.simple_enc(None, data)
            
    def handle_command(self, command):
        if command[0] == 'RESET':
            self.histograming.reset()
            self.tdc_counters = np.zeros_like(self.tdc_counters)
            self.error_counters = np.zeros_like(self.error_counters)
            self.service_records_counters = np.zeros_like(self.service_records_counters)
            self.trigger_error_counters = np.zeros_like(self.trigger_error_counters)
        elif 'ACTIVETAB' in command[0]:
            self.active_tab = int(command[0].split()[1])
        else:
            self.n_readouts = int(command[0])
