from zmq.utils import jsonapi
import numpy as np
import sys
import logging

from online_monitor.converter.transceiver import Transceiver
from online_monitor.utils import utils

from testbeam_analysis.tools import analysis_utils


class HitCorrelator(Transceiver):
    
    def setup_transceiver(self):
        self.set_bidirectional_communication()  # We want to be able to change the histogrammmer settings
    
    def setup_interpretation(self):
        self.active_dut = 0 # variable to store integer value of active dut
        self.data_buffer = {}  # The data does not have to arrive at the same receive command since ZMQ buffers data and the DUT can have different time behavior
        self.all_hists_col_corr = {} # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
        self.all_hists_row_corr = {} # used to be self.hists_row_corr /
        
        for frontend in self.frontends:
            self.all_hists_col_corr[frontend[0]] = np.zeros(shape=(self.config['max_n_columns'], self.config['max_n_columns']))
            self.all_hists_row_corr[frontend[0]] = np.zeros(shape=(self.config['max_n_rows'], self.config['max_n_rows']))

    def deserialze_data(self, data):  # According to pyBAR data serilization
        return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)
        
    def interpret_data(self, data):
        
        for actual_device_data in data:  # Loop over all devices of actual received data which ist type 'list'
            frontend_name, frontend_data = actual_device_data #type of actual_decice_data is 'tuple' of frontend_name and it's data, where data is frontend_data and type 'dict'
            if 'hits' in frontend_data:
                frontend_hits = frontend_data['hits']
                self.data_buffer[frontend_name] = frontend_hits

        if len(self.data_buffer) < 2:
            return
        
        
        active_device_data = self.data_buffer[self.frontends[self.active_dut][0]]
        
        print "active device data",active_device_data #FIXMEEEEEEEEEEEEEEEE
        return #FIXMEE
    
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

    def serialze_data(self, data):
        return jsonapi.dumps(data, cls=utils.NumpyEncoder)


    def handle_command(self, command):
        if command[0] == 'RESET': #hope that this works, not sure
            self.all_hists_col_corr[self.frontends[self.active_dut][0]] = np.zeros(shape=(self.config['max_n_columns'], self.config['max_n_columns']))
            self.all_hists_row_corr[self.frontends[self.active_dut][0]] = np.zeros(shape=(self.config['max_n_rows'], self.config['max_n_rows']))
        else:
            self.active_dut = int(command[0])
