from zmq.utils import jsonapi
import numpy as np
import sys
import logging

from online_monitor.converter.transceiver import Transceiver
from online_monitor.utils import utils

from testbeam_analysis.tools import analysis_utils
from numpy import corrcoef


class HitCorrelator(Transceiver):
    
    def setup_transceiver(self):
        self.set_bidirectional_communication()  # We want to be able to change the histogrammmer settings
    
    def setup_interpretation(self):
        self.active_dut = 0 # variable to store integer value of active dut
        self.data_buffer = {} # The data does not have to arrive at the same receive command since ZMQ buffers data and the DUT can have different time behavior
        self.data_buffer_max = np.zeros(7) # store maximum event_number of each incoming data of each DUT 
        self.data_buffer_done = 0 #store event_number of already correlated events
        self.all_hists_col_corr = {} # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
        self.all_hists_row_corr = {} # used to be self.hists_row_corr /

        #for frontend in self.frontends:
            #print 'frontend', frontend
            #self.all_hists_col_corr[frontend[0]] = np.zeros(shape=(self.config['max_n_columns'], self.config['max_n_columns']))
            #self.all_hists_row_corr[frontend[0]] = np.zeros(shape=(self.config['max_n_rows'], self.config['max_n_rows']))

    def deserialze_data(self, data):  # According to pyBAR data serilization
        return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)
    
    def interpret_data(self, data):
        event_n_step = 2000
        for actual_dut_data in data:
            frontend_data = actual_dut_data[1]
            
            if 'meta_data' in frontend_data:  # Meta data is directly forwarded to the receiver, only hit data, event counters are histogramed; 0 from frontend index, 1 for data dict
                return
            
            frontend_hits = frontend_data['hits']
            frontend_type = frontend_data['device_type']
            
            if frontend_hits.shape[0] == 0: # Empty array
                return  
                        
            if frontend_type == 'm26':    #key for actual mimosa plane is its plane number
                for actual_plane in range(1,7):
                    if actual_plane in self.data_buffer.keys():
                        self.data_buffer[actual_plane]=np.append(self.data_buffer[actual_plane],frontend_hits[frontend_hits['plane']==actual_plane])
                    else:
                        self.data_buffer[actual_plane]=frontend_hits[frontend_hits['plane']==actual_plane]
                    self.data_buffer_max[actual_plane]=np.max(self.data_buffer[actual_plane]['event_number'])
                    #print 'max_mimosa plane',actual_plane ,self.data_buffer_max[actual_plane],len(self.data_buffer[actual_plane])
            if frontend_type == 'fei4': #key for fei4 plane is 0
                    if 0 in self.data_buffer.keys():
                        self.data_buffer[0]=np.append(self.data_buffer[0],frontend_hits)
                    else:
                        self.data_buffer[0]=frontend_hits
                    self.data_buffer_max[0]=np.max(self.data_buffer[0]['event_number'])
                    #print 'max_fei4', self.data_buffer_max[0]
        
        number_duts = len(self.data_buffer)
        
        if number_duts < 7:
            print 'Filling data buffer...'
            return
        if number_duts > 7:
            logging.warning('More data than DUTs! 7 DUTs expected, actually %i', number_duts)
            return
        
        #needs to be in for loop
        #active_device_data, device_other_data = analysis_utils.merge_on_event_number(active_device_data, device_other_data[1])
        
        if np.min(self.data_buffer_max) > (event_n_step + self.data_buffer_done): # >
            active_device_data = self.data_buffer[self.active_dut][self.data_buffer[self.active_dut]['event_number'] <= (event_n_step + self.data_buffer_done)]
            #device_other_data=
            #corr
            for actual_plane in range(7):
                self.data_buffer[actual_plane] = self.data_buffer[actual_plane][self.data_buffer[actual_plane]['event_number'] > (event_n_step + self.data_buffer_done)]
            
            self.data_buffer_done = event_n_step + self.data_buffer_done
        else:
            return
        print 'active_dut', self.active_dut,'active device data', active_device_data 
        
        
    
    def serialze_data(self, data):
        return jsonapi.dumps(data, cls=utils.NumpyEncoder)
    
    def handle_command(self, command):
            if command[0] == 'RESET':
                return
                self.hist_column_corr = np.zeros_like(self.hist_column_corr)
                self.hist_row_corr = np.zeros_like(self.hist_row_corr)
            else:
                    self.active_dut = int(command[0])
'''      
    def interpret_data(self, data):
        
        for actual_device_data in data:  # Loop over all devices of actual received data which ist type 'list'
            frontend_name, frontend_data = actual_device_data #type of actual_decice_data is 'tuple' of frontend_name and it's data, where data is frontend_data and type 'dict'
            if 'hits' in frontend_data:
                frontend_hits = frontend_data['hits']
                self.data_buffer[frontend_name] = frontend_hits

        if len(self.data_buffer) < 2:
            return
        
        
        active_device_data = self.data_buffer[self.frontends[self.active_dut][0]]
        
        for device_other_data in self.data_buffer.items():
            # Main function to correlate data in time
            active_device_data, device_other_data = analysis_utils.merge_on_event_number(active_device_data, device_other_data[1])
              
            # Function to correlate positions
            try:
                hist_row_corr = analysis_utils.hist_2d_index(active_device_data['row'], device_other_data['row'], shape=(self.config['max_n_rows'], self.config['max_n_rows']))
                hist_column_corr = analysis_utils.hist_2d_index(active_device_data['column'], device_other_data['column'], shape=(self.config['max_n_columns'], self.config['max_n_columns']))
            except IndexError:
                logging.warning('Histogram indices out of range!')
                return
 
            self.all_hists_col_corr[self.frontends[self.active_dut][0]] += hist_column_corr    
            self.all_hists_row_corr[self.frontends[self.active_dut][0]] += hist_row_corr
         
        return [{'column_%s' % self.frontends[self.active_dut][0]: self.all_hists_col_corr[self.frontends[self.active_dut][0]], 
                 'row_%s' % self.frontends[self.active_dut][0]: self.all_hists_row_corr[self.frontends[self.active_dut][0]]}]
'''

