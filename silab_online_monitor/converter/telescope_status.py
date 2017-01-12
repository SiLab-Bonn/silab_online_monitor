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
        
        # variables to determine whether to send data to receiver or not
        self.active_tab = None  # stores name (str) of active tab in online monitor
        self.tel_stat_tab = 'Telescope_Status'  # store name (str) of Telescope_Status tab
        
        # array for simulated status data
        self.status_data = np.zeros(shape=1, dtype=[('m26_v','f4'),('m26_c','f4'),('vdda_v','f4'),('vdda_c','f4'),('vddd_v','f4'),('vddd_c','f4')])
        
        # set array size; must be shape=(2, x); increase x to plot longer time span
        self.array_size = (2,3200)
        
        # add arrays for plots; array[0] is time axis
        self.vdda_v_array = np.zeros(shape=self.array_size)
        self.vdda_c_array = np.zeros(shape=self.array_size)
        self.vddd_v_array = np.zeros(shape=self.array_size)
        self.vddd_c_array = np.zeros(shape=self.array_size)
        self.m26_v_array = np.zeros(shape=self.array_size)
        self.m26_c_array = np.zeros(shape=self.array_size)
        
        # add dicts, dtypes and arrays for individual handling of each parameter
        
        # Using structured np.arrays produces weird VisibleDeprecationWarning
        #data_dtype = [('vdda_v','f4'), ('vdda_c','f4'), ('vddd_v','f4'), ('vddd_c','f4'), ('m26_v','f4'), ('m26_c','f4')]
        #index_dtype = [('vdda_v','i4'), ('vdda_c','i4'), ('vddd_v','i4'), ('vddd_c','i4'), ('m26_v','i4'), ('m26_c','i4')]
        #self.array_indices = np.zeros(shape=1, dtype=index_dtype)
        #self.update_time_indices = np.zeros(shape=1, dtype=index_dtype)
        #self.shift_cycle_times = np.zeros(shape=1, dtype=data_dtype)
        #self.now = np.zeros(shape=1, dtype=data_dtype)
        
        # dict with all data arrays
        self.all_arrays = {'vdda_v': self.vdda_v_array, 'vdda_c': self.vdda_c_array, 'vddd_v': self.vddd_v_array, 'vddd_c': self.vddd_c_array, 'm26_v': self.m26_v_array, 'm26_c': self.m26_c_array}
        
        # dict with set of current data indices
        self.array_indices = {'vdda_v': 0, 'vdda_c': 0, 'vddd_v': 0, 'vddd_c': 0, 'm26_v': 0, 'm26_c': 0}
        
        # dict with set of start times of each key since last shifted through 
        self.shift_cycle_times = {'vdda_v': 0, 'vdda_c': 0, 'vddd_v': 0, 'vddd_c': 0, 'm26_v': 0, 'm26_c': 0}
        
        # dict with set of current time indices
        self.update_time_indices = {'vdda_v': 0, 'vdda_c': 0, 'vddd_v': 0, 'vddd_c': 0, 'm26_v': 0, 'm26_c': 0}
        
        # dict with set of current times corresponding current data
        self.now = {'vdda_v': 0, 'vdda_c': 0, 'vddd_v': 0, 'vddd_c': 0, 'm26_v': 0, 'm26_c': 0}
        
    def deserialze_data(self, data):  # According to pyBAR data serilization
        datar, meta = utils.simple_dec(data)
        if 'hits' in meta:
            meta['hits'] = datar
        return meta

    def interpret_data(self, data):
        
        # simulate data for testing
        self.status_data['m26_c'] = np.random.uniform(3.0,3.31)
        self.status_data['m26_v'] = np.random.uniform(8.0,8.31)
        self.status_data['vdda_v'] = np.random.uniform(1.5,1.31)
        self.status_data['vddd_v'] = np.random.uniform(1.2,1.31)
        self.status_data['vdda_c'] = np.random.uniform(0.3,0.35)
        self.status_data['vddd_c'] = np.random.uniform(0.1,0.15)
        
        # add function to fill arrays with data and shift through
        def fill_arrays(array, data, time, time_index):
            array[0][time_index] = time
            array[1] = np.roll(array[1], 1)
            array[1][0] = data
            return array
            
        # handle timing of data
        for key in self.all_arrays:
            
            # update starting time (self.shift_cycle_time) if we just started or once shifted through the data array
            if self.array_indices[key] == 0 or self.array_indices[key] % self.array_size[1] == 0:
                
                self.shift_cycle_times[key] = time.time()
                self.update_time_indices[key] = 0
            
            # time since we started or last shifted through
            self.now[key] = self.shift_cycle_times[key] - time.time()
        
        '''
        # this is how it should look like without simulating data
        
        if 'meta_data' in data: # apparently this is where scan_paramters are
            if 'scan_parameters' in data:
                for key in data['meta_data']['scan_parameters']:
                    self.all_arrays[key] = fill_arrays(self.all_arrays[key], data['meta_data']['scan_parameters'][key][0], self.now[key], self.update_time_indices[key])
        '''
        
        # placeholder for if 'status'/'scan_parameters'/'meta_data' in data
        if True:
            
            # fill time and data axes of each array
            for key in self.all_arrays:
                
                self.all_arrays[key] = fill_arrays(self.all_arrays[key], self.status_data[key][0], self.now[key], self.update_time_indices[key])
                
                # increase indices for timing and data
                self.update_time_indices[key] += 1
                self.array_indices[key] += 1
            
            # if we are looking at status receiver send data
            if self.active_tab == self.tel_stat_tab:
                
                # if array ist not completely filled, send array and current index, so receiver can plot only up to this index
                if self.array_indices[key] < self.array_size[1]:
                    
                    return [{'status': self.all_arrays, 'indices': self.array_indices}]
                
                # once array is completely filled send entire data
                elif self.array_indices[key] >= self.array_size[1]:
                    
                    return [{'status': self.all_arrays}]
            
            # if we are not looking at status receiver just pass
            else:
                pass
        
        
    def serialze_data(self, data):
        return jsonapi.dumps(data, cls=utils.NumpyEncoder)

    def handle_command(self, command):
        
        if 'ACTIVETAB' in command[0]:  # received signal is 'ACTIVETAB tab' where tab is the name (str) of the selected tab in online monitor
            self.active_tab = str(command[0].split()[1])
        elif 'RESET' in command[0]:
            if 'M26' in command[0]:
                if 'VOLTAGE' in command[0]:
                    self.m26_v_array = np.zeros_like(self.m26_v_array)
                    self.array_indices['m26_v'] = 0
                    self.update_time_indices['m26_v'] = 0
                elif 'CURRENT' in command[0]:
                    self.m26_c_array = np.zeros_like(self.m26_c_array)
                    self.array_indices['m26_c'] = 0
                    self.update_time_indices['m26_c'] = 0
            elif 'FEI4' in command[0]:
                if 'VDDA' in command[0]:
                    self.vdda_v_array = np.zeros_like(self.vdda_v_array)
                    self.vdda_c_array = np.zeros_like(self.vdda_c_array)
                    self.array_indices['vdda_v'] = 0
                    self.update_time_indices['vdda_v'] = 0
                    self.array_indices['vdda_c'] = 0
                    self.update_time_indices['vdda_c'] = 0
                elif 'VDDD' in command[0]:
                    self.vddd_v_array = np.zeros_like(self.vddd_v_array)
                    self.vddd_c_array = np.zeros_like(self.vddd_c_array)
                    self.array_indices['vddd_v'] = 0
                    self.update_time_indices['vddd_v'] = 0
                    self.array_indices['vddd_c'] = 0
                    self.update_time_indices['vddd_c'] = 0
