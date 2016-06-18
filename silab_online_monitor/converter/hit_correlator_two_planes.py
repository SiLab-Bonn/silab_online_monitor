from zmq.utils import jsonapi
import numpy as np
import sys
import logging
import time

from online_monitor.converter.transceiver import Transceiver
from online_monitor.utils import utils

from testbeam_analysis.tools import analysis_utils
from numpy import corrcoef


class HitCorrelator(Transceiver):
    
    def setup_transceiver(self):
        self.set_bidirectional_communication()  # We want to be able to change the histogrammmer settings
    
    def setup_interpretation(self):
        #variables to determine whether to do sth or not
        self.active_tab = None # stores index of active tab in online monitor
        self.hit_corr_tab = 3 # FIXME: maybe better to do sth like hit_corr.tabPosition() to get tab index of hit correlator
        self.start_signal = 1 # correlation starts if this is set to 0
        #variables to store integer value of active duts
        self.active_dut1 = 0 
        self.active_dut2 = 0
        #variables fps
        self.fps = 0
        self.updateTime = time.time()
        #data buffers
        self.data_buffer = {} # The data does not have to arrive at the same receive command since ZMQ buffers data and the DUT can have different time behavior
        self.data_buffer_max = np.zeros(2) #  store maximum event_number of each incoming data of each DUT 
        self.data_buffer_done = 0 #store event_number of already correlated events
        self.event_n_step = 2000 #amount of event_numbers in buffer
        self.hist_cols_corr = np.zeros([self.config['max_n_columns_m26'],self.config['max_n_columns_m26']], dtype=np.uint32) # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
        self.hist_rows_corr = np.zeros([self.config['max_n_rows_m26'],self.config['max_n_rows_m26']], dtype=np.uint32)  # used to be self.hists_row_corr /
        
    def deserialze_data(self, data):  # According to pyBAR data serilization
        datar, meta  = utils.simple_dec(data)
        if 'hits' in meta:
            meta['hits'] = datar
        return meta
        
    def interpret_data(self, data):
        
        if self.active_tab != self.hit_corr_tab: # Only do something when user clicked on 'hit_correlator' in online_monitor ; hit_correlator-tab is #3
            #print 'hit corr doing nothing'
            return
        
        self.active_duts = [self.active_dut1,self.active_dut2] #store both active DUTs in array for reasons

        if self.start_signal != 0: #wait for user to press start
            #print "Press 'Start'-button"
            return
        
        if 'meta_data' in data[0][1]: # Meta data is directly forwarded to the receiver, only hit data is correlated; 0 from frontend index, 1 for data dict
            meta_data = data[0][1]['meta_data']
            now = time.time()
            recent_total_hits = meta_data['n_hits']
            recent_total_events = meta_data['n_events']
            recent_fps = 1.0 / (now - self.updateTime)  # calculate FPS
            self.updateTime = now
            self.fps = self.fps * 0.7 + recent_fps * 0.3
            meta_data.update({'fps': self.fps})
            return [data[0][1]]
			
        for actual_dut_data in data:
            frontend_data = actual_dut_data[1]
            
            if 'meta_data' in frontend_data:  #meta_data is skipped
                continue #used to be return: we don't want to return , we just want to skip
            
            frontend_hits = frontend_data['hits']
            frontend_type = frontend_data['device_type']
            
            if frontend_hits.shape[0] == 0: # Empty array
                return
        
            for i,active_dut in enumerate(self.active_duts):
                if frontend_type == 'm26': #m26 key is the actual plane number from 1-6
                    if active_dut == 0: # fei4 key is 0
                        continue
                    if i in self.data_buffer.keys():
                        self.data_buffer[i] = np.append(self.data_buffer[i],frontend_hits[frontend_hits['plane']==active_dut])
                    else:
                        self.data_buffer[i] = frontend_hits[frontend_hits['plane']==active_dut]
                    if len(self.data_buffer[i]) != 0:
                        self.data_buffer_max[i]=np.max(self.data_buffer[i]['event_number'])
                if frontend_type == 'fei4':
                    if active_dut != 0: #fei4 key is 0
                        continue
                    if i in self.data_buffer.keys():
                        self.data_buffer[i] = np.append(self.data_buffer[i],frontend_hits)
                    else:
                        self.data_buffer[i] = frontend_hits
                    if len(self.data_buffer[i]) != 0:
                        self.data_buffer_max[i]=np.max(self.data_buffer[i]['event_number'])        
        
        if len(self.data_buffer)!=2: #wait until there is data of both selected duts
            print 'Loading data of selected DUTs...'
            return
        
        if np.min(self.data_buffer_max) > (self.event_n_step + self.data_buffer_done):
            
            active_dut1_data = self.data_buffer[0][self.data_buffer[0]['event_number'] <= (self.event_n_step + self.data_buffer_done)]
            active_dut2_data = self.data_buffer[1][self.data_buffer[1]['event_number'] <= (self.event_n_step + self.data_buffer_done)]
            merged_active_dut1_data, merged_active_dut2_data = analysis_utils.merge_on_event_number(active_dut1_data, active_dut2_data)
            
            try:
                hist_row_corr = analysis_utils.hist_2d_index(merged_active_dut1_data['row'], merged_active_dut2_data['row'], shape=(self.config['max_n_rows_m26'], self.config['max_n_rows_m26']))
                hist_column_corr = analysis_utils.hist_2d_index(merged_active_dut1_data['column'], merged_active_dut2_data['column'], shape=(self.config['max_n_columns_m26'], self.config['max_n_columns_m26']))
            except IndexError:
                logging.warning('Histogram indices out of range!')
                return   
            
            self.hist_cols_corr[:,:] += hist_column_corr    
            self.hist_rows_corr[:,:] += hist_row_corr
            for i in range(2):
                self.data_buffer[i] = self.data_buffer[i][self.data_buffer[i]['event_number'] > (self.event_n_step + self.data_buffer_done)] 

            self.data_buffer_done = self.event_n_step + self.data_buffer_done
            
            return [{'column' : self.hist_cols_corr, 'row' : self.hist_rows_corr}]
        else:
            return

    
    def serialze_data(self, data):
        return jsonapi.dumps(data, cls=utils.NumpyEncoder)
        #return utils.simple_enc(None, data)
        
    def handle_command(self, command):
            if command[0] == 'RESET':
                self.hist_cols_corr = np.zeros_like(self.hist_cols_corr)
                self.hist_rows_corr = np.zeros_like(self.hist_rows_corr)
                self.data_buffer={}
            elif 'combobox1'in command[0]:
                self.active_dut1 = int(command[0].split()[1])
                self.hist_cols_corr = np.zeros_like(self.hist_cols_corr)#reset everytime you change dut
                self.hist_rows_corr = np.zeros_like(self.hist_rows_corr)
                self.data_buffer={}
            elif 'combobox2'in command[0]:
                self.active_dut2 = int(command[0].split()[1])
                self.hist_cols_corr = np.zeros_like(self.hist_cols_corr)#reset everytime you change dut
                self.hist_rows_corr = np.zeros_like(self.hist_rows_corr)
                self.data_buffer={}
            elif 'START' in command[0]: # first choose two telescope planes and then press start button to correlate
                self.start_signal = int(command[0].split()[1])
            elif 'ACTIVETAB' in command[0]: # 
                self.active_tab = int(command[0].split()[1])
#             elif 'MASK' in command[0]:    # make noisy pixel remover later
#                 if '0' in command[0]:
#                     self.mask_noisy_pixel = False
#                 else:
#                     self.mask_noisy_pixel = True   
                

