from zmq.utils import jsonapi
import numpy as np
import sys
import time
import logging
from online_monitor.converter.transceiver import Transceiver
from online_monitor.utils import utils


class TelescopeStatus(Transceiver):

    def setup_transceiver(self):
        self.set_bidirectional_communication()  # We want to be able to change the histogrammmer settings

    def setup_interpretation(self):
        # variables to determine whether to do sth or not
        self.active_tab = None  # stores name (str) of active tab in online monitor
        self.tel_stat_tab = 'Telescope_Status'  # store name (str) of Telescope_Status tab
        
        # dict for status data
        #self.status_data = np.zeros(shape=(10), dtype=[('m26_voltage','f8'),('m26_current','f8'),('vdda_v','f8'),('vdda_c','f8'),('vddd_v','f8'),('vddd_c','f8')])
        self.status_data = 0
        # start timer
        self.start_time = time.time()
        # time axis
        self.time_axis = []
        
    def deserialze_data(self, data):  # According to pyBAR data serilization
        datar, meta = utils.simple_dec(data)
        if 'hits' in meta:
            meta['hits'] = datar
        return meta

    def interpret_data(self, data):
        
        if self.active_tab != self.tel_stat_tab:  # if active tab in online monitor is not telescope status, return
            return
        
        for actual_data in data:

            if 'meta_data' in actual_data[1]:  # meta_data is skipped
                continue
            if 'status' in actual_data[1]:
                if actual_data[1]['status'].shape[0] = 0: # empty array is skipped
                    continue
                else:
                    time = time.time() - self.start_time
                    self.time_axis.append(time)
                    self.status_data = actual_data[1]['status']
                    
        return [{'status': self.status_data, 'time': self.time_axis}]
        #~ for name in self.status_data.dtype.names:
            #~ print name
            #~ self.status_data[name] = np.random.uniform(low=1.0,high=8.0, size=self.status_data.shape[0])
            
        #~ return [self.status_data]

    def serialze_data(self, data):
        return jsonapi.dumps(data, cls=utils.NumpyEncoder)

    def handle_command(self, command):
        
        if 'ACTIVETAB' in command[0]:  # received signal is 'ACTIVETAB tab' where tab is the name (str) of the selected tab in online monitor
            self.active_tab = str(command[0].split()[1])
            
        if 'RESET' in command[0]:
            if 'M26' in command[0]:
                if 'CURRENT' in command[0]:
                    print 'm26_current'
                    self.status_data['m26_current'] = 0
                elif 'VOLTAGE' in command[0]:
                    print 'm26_voltage'
                    self.status_data['m26_voltage'] = 0
            elif 'FEI4' in command[0]:
                if 'VDDA' in command[0]:
                    print 'VDDA'
                    self.status_data['vdda_v'] = 0
                    self.status_data['vdda_c'] = 0
                elif 'VDDD' in command[0]:
                    print 'VDDD'
                    self.status_data['vddd_v'] = 0
                    self.status_data['vddd_c'] = 0
