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
        self.active_dut = 1 # variable to store integer value of active dut
        self.data_buffer = {} # The data does not have to arrive at the same receive command since ZMQ buffers data and the DUT can have different time behavior
        self.data_buffer_max = np.zeros(7) # store maximum event_number of each incoming data of each DUT 
        self.data_buffer_done = 0 #store event_number of already correlated events
        self.all_hists_col_corr = np.zeros([6,1152,1152], dtype=np.uint32) # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
        self.all_hists_row_corr = np.zeros([6,576,576], dtype=np.uint32)  # used to be self.hists_row_corr /

    def deserialze_data(self, data):  # According to pyBAR data serilization
        datar, meta  = utils.simple_dec(data)
        if 'hits' in meta:
            meta['hits'] = datar
        return meta
        
    def interpret_data(self, data):
        if self.active_dut==0:  ####TODO add FEI4 corr later
            return
        
        event_n_step = 100 #amount of event_numbers in buffer
        
        for actual_dut_data in data:
            frontend_data = actual_dut_data[1]
            
            if 'meta_data' in frontend_data:  # Meta data is directly forwarded to the receiver, only hit data, event counters are histogramed; 0 from frontend index, 1 for data dict
                continue #used to be return: we don't want to return , we just want to skip
            
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
                    if len(self.data_buffer[actual_plane])!=0:
                        self.data_buffer_max[actual_plane]=np.max(self.data_buffer[actual_plane]['event_number'])
                    
            if frontend_type == 'fei4': #key for fei4 plane is 0
                    if 0 in self.data_buffer.keys():
                        self.data_buffer[0]=np.append(self.data_buffer[0],frontend_hits)
                    else:
                        self.data_buffer[0]=frontend_hits
                    if len(self.data_buffer[0])!=0:
                        self.data_buffer_max[0]=np.max(self.data_buffer[0]['event_number'])
                    
        
        number_duts = len(self.data_buffer)
        
        if number_duts < 7:
            print 'Filling data buffer...'
            return
        if number_duts > 7:
            logging.warning('More data than DUTs! 7 DUTs expected, actually %i', number_duts)
            return
        
        other_device_data={} #declare dict for data of other devices except actual device
        
        i=1 #avoiding to correlate mimosa and fei4 by not correlating plane 0 which is fei4   ####TODO add FEI4 corr later
        
        if np.min(self.data_buffer_max) > (event_n_step + self.data_buffer_done): 
            active_device_data = self.data_buffer[self.active_dut][self.data_buffer[self.active_dut]['event_number'] <= (event_n_step + self.data_buffer_done)]
            
            for actual_plane in range(1,7):
                
                if actual_plane != self.active_dut:
                    #print "actual plane", actual_plane
                    other_device_data = self.data_buffer[actual_plane][self.data_buffer[actual_plane]['event_number'] <= (event_n_step + self.data_buffer_done)]
                    merged_active_device_data, other_device_data = analysis_utils.merge_on_event_number(active_device_data, other_device_data)
                    try:
                        hist_row_corr = analysis_utils.hist_2d_index(merged_active_device_data['row'], other_device_data['row'], shape=(self.config['max_n_rows_m26'], self.config['max_n_rows_m26']))
                        hist_column_corr = analysis_utils.hist_2d_index(merged_active_device_data['column'], other_device_data['column'], shape=(self.config['max_n_columns_m26'], self.config['max_n_columns_m26']))
                    except IndexError:
                        logging.warning('Histogram indices out of range!')
                        return
                    
                    self.all_hists_col_corr[i,:,:] += hist_column_corr    
                    self.all_hists_row_corr[i,:,:] += hist_row_corr
                    i+=1
                
                self.data_buffer[actual_plane] = self.data_buffer[actual_plane][self.data_buffer[actual_plane]['event_number'] > (event_n_step + self.data_buffer_done)]            
            
            self.data_buffer_done = event_n_step + self.data_buffer_done
            
            
            
            return [{'column': self.all_hists_col_corr, 'row' : self.all_hists_row_corr}]
        
        else:
            return
        
        
#         #print 'active_dut', self.active_dut,'active device data', active_device_data 
#         print "lets go"
#         i=0
#         for actual_plane in range(7):
#             print "start",actual_plane,i,self.active_dut
#             if actual_plane != self.active_dut:               
#                 # Main function to correlate data in time
#                 print 'before merge', actual_plane,i,len(other_device_data[actual_plane]),other_device_data[actual_plane]
#                 active_device_data, not_active_data = analysis_utils.merge_on_event_number(active_device_data, other_device_data[actual_plane])
#                 print 'after merge', actual_plane,i
#                 #try:
#                 if True:
#                     print np.max(active_device_data['row']), np.max(not_active_data['row']), self.config['max_n_rows_m26'], self.config['max_n_rows_m26']
#                     print np.max(active_device_data['column']), np.max(not_active_data['column']), self.config['max_n_columns_m26'], self.config['max_n_columns_m26']
#                     hist_row_corr = analysis_utils.hist_2d_index(active_device_data['row'], not_active_data['row'], shape=(self.config['max_n_rows_m26'], self.config['max_n_rows_m26']))
#                     hist_column_corr = analysis_utils.hist_2d_index(active_device_data['column'], not_active_data['column'], shape=(self.config['max_n_columns_m26'], self.config['max_n_columns_m26']))
#                 #except IndexError:
#                 else:
#                     logging.warning('Histogram indices out of range!')
#                     return
# 
# #             print 'CORR HIST FILL', np.count_nonzero(self.all_hists_col_corr[self.active_dut,:,:])
#                 print 'ggggggggggggggggggggggg'
#                 print 'actual plane', actual_plane,i
#                 
#                 self.all_hists_col_corr[i,:,:] += hist_column_corr    
#                 self.all_hists_row_corr[i,:,:] += hist_row_corr
#                 i+=1
#                 print "done", actual_plane, i
#             self.data_buffer[actual_plane] = self.data_buffer[actual_plane][self.data_buffer[actual_plane]['event_number'] > (event_n_step + self.data_buffer_done)]
# 
#         print 'jjjjjjjjjjjjjjjjjjjjj'
        
#        return [{'column': self.all_hists_col_corr, 
#                 'row' : self.all_hists_row_corr}]

    
    def serialze_data(self, data):
        return jsonapi.dumps(data, cls=utils.NumpyEncoder)
        #return utils.simple_enc(None, data)
        
    def handle_command(self, command):
            if command[0] == 'RESET':
                self.all_hists_col_corr = np.zeros_like(self.all_hists_col_corr)
                self.all_hists_row_corr = np.zeros_like(self.all_hists_row_corr)
            else:
                self.all_hists_col_corr = np.zeros_like(self.all_hists_col_corr)
                self.all_hists_row_corr = np.zeros_like(self.all_hists_row_corr)
                self.active_dut = int(command[0])

