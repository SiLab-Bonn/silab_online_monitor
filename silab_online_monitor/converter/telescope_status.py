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
        
        # array for status data
        self.status_data = np.zeros(shape=(1), dtype=[('time','f8'),('m26_voltage','f4'),('m26_current','f4'),('vdda_v','f4'),('vdda_c','f4'),('vddd_v','f4'),('vddd_c','f4')])
    
        # start timer
        self.start_time = time.time()
        
    def deserialze_data(self, data):  # According to pyBAR data serilization
        datar, meta = utils.simple_dec(data)
        if 'hits' in meta:
            meta['hits'] = datar
        return meta

    def interpret_data(self, data):
        
        if self.active_tab != self.tel_stat_tab:  # if active tab in online monitor is not telescope status, return
            return
        
        if 'meta_data' in data: # apparently this is where scan_paramters are
            #print data[0][1]['meta_data']['scan_parameters']
            pass
        
        '''
        This works if with each meta_data we get one value for each scan_parameter (which is correct i guess)
        '''
        
        # get time passed since converter was started
        now = time.time() - self.start_time
        self.status_data['time'] = now
        
        # simulate data for testing
        self.status_data['m26_current'] = np.random.uniform(3.0,3.31)
        self.status_data['m26_voltage'] = np.random.uniform(8.0,8.31)
        self.status_data['vdda_v'] = np.random.uniform(1.5,1.31)
        self.status_data['vddd_v'] = np.random.uniform(1.2,1.31)
        self.status_data['vdda_c'] = np.random.uniform(0.3,0.35)
        self.status_data['vddd_c'] = np.random.uniform(0.1,0.15)
        
        return [{'status': self.status_data}] # this is the format the serializer needs; dict
        
        
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
