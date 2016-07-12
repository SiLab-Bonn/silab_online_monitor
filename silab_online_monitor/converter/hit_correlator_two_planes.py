from zmq.utils import jsonapi
import numpy as np
#import logging
import time
import sys
import psutil

from online_monitor.converter.transceiver import Transceiver
from online_monitor.utils import utils

#from testbeam_analysis.tools import analysis_utils
#from numpy import corrcoef
from pyBAR_mimosa26_interpreter import correlation_functions
#from pybar_fei4_interpreter import analysis_functions

class HitCorrelator(Transceiver):
    
    def setup_transceiver(self):
        self.set_bidirectional_communication()  # We want to be able to change the histogrammmer settings
    
    def setup_interpretation(self):
        #variables to determine whether to do sth or not
        self.active_tab = None  #'Hit_Correlator' # stores index of active tab in online monitor
        self.hit_corr_tab = 'Hit_Correlator' # store string of hit_correlator tab
        self.start_signal = 1 # correlation starts if this is set to 0
        #variables to store integer value of active duts
        self.active_dut1 = 0 
        self.active_dut2 = 0
        #variables fps
        self.fps = 0
        self.updateTime = 0
        #data buffers
        self.data_buffer = {} # The data does not have to arrive at the same receive command since ZMQ buffers data and the DUT can have different time behavior
        #self.data_buffer_max = np.zeros(2) #  store maximum event_number of each incoming data of each DUT 
        #self.data_buffer_done = 0 #store event_number of already correlated events
        #self.event_n_step = 2000 #amount of event_numbers in buffer
        self.hist_cols_corr = np.zeros((self.config['max_n_columns_m26'],self.config['max_n_columns_m26']), dtype=np.uint32) # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
        self.hist_rows_corr = np.zeros((self.config['max_n_rows_m26'],self.config['max_n_rows_m26']), dtype=np.uint32)  # used to be self.hists_row_corr /

    def deserialze_data(self, data):  # According to pyBAR data serilization
        datar, meta  = utils.simple_dec(data)
        if 'hits' in meta:
            meta['hits'] = datar
        return meta
        
    def interpret_data(self, data):
        
        if self.active_tab != self.hit_corr_tab: # Only do something when user clicked on 'hit_correlator' in online_monitor
            return
        
        self.active_duts = [self.active_dut1,self.active_dut2] #store both active DUTs in array

        if self.start_signal != 0: #wait for user to press start
            #print "Press 'Start'-button"
            return
        
        if 'meta_data' in data[0][1]: # Meta data is directly forwarded to the receiver, only hit data is correlated; 0 from frontend index, 1 for data dict
            meta_data = data[0][1]['meta_data']
            now = float(meta_data['timestamp_stop'])
            if now != self.updateTime: #FIXME: sometimes = ZeroDivisionError: because of https://github.com/SiLab-Bonn/pyBAR/issues/48
                recent_fps = 1.0 / (now - self.updateTime)  #FIXME: does not show real rate, shows rate data was recorded with
                self.updateTime = now
                self.fps = self.fps * 0.7 + recent_fps * 0.3
                meta_data.update({'fps': self.fps})
                return [data[0][1]]
        
        ## find data type
        for actual_dut_data in data:
            
            if 'meta_data' in actual_dut_data[1]:  #meta_data is skipped
                continue
            if actual_dut_data[1]['hits'].shape[0] == 0: # Empty array
                continue
            
            if 'plane' in actual_dut_data[1]['hits'].dtype.names:
                mimosa_hits = actual_dut_data[1]['hits']
            else:
                fe_hits = actual_dut_data[1]['hits']
                      
        ## copy data to buffer
        for i,active_dut in enumerate(self.active_duts):
            if active_dut == 0 and 'fe_hits' in locals():### active dut is fei4
                if i in self.data_buffer.keys():
                        self.data_buffer[i] = np.append(self.data_buffer[i],fe_hits)
                else:
                        self.data_buffer[i] = fe_hits
            elif active_dut != 0 and 'mimosa_hits' in locals(): ### active dut is mimosa
                if i in self.data_buffer.keys():
                    self.data_buffer[i] = np.append(self.data_buffer[i],mimosa_hits[mimosa_hits['plane']==active_dut])
                else:
                    self.data_buffer[i] = mimosa_hits[mimosa_hits['plane']==active_dut]
                    
        #### if no data to process return 
        if len(self.data_buffer)!=2: #wait until there is data of both selected duts
            print 'Loading data of selected DUTs...'
            return
        
        elif len(self.data_buffer[0]) == 0 or len(self.data_buffer[1]) == 0:
            return 
        
        ### debug print 
        #process = psutil.Process(self.ident)  # access this process info
        #print 'MEMORY', process.memory_info()
        
        ### make corr
        if self.active_dut1 != 0 and self.active_dut2 != 0: #correlate m26 to m26    
            m0_index, m1_index = correlation_functions.correlate_mm(self.data_buffer[0], self.data_buffer[1], self.hist_cols_corr, self.hist_rows_corr)
            if m0_index == -1 and m1_index == -1:
                print "Error! Outer loop terminated"
                return
            
            self.data_buffer[0] =np.delete(self.data_buffer[0], np.arange(0,m0_index))
            self.data_buffer[1] =np.delete(self.data_buffer[1], np.arange(0,m1_index))
            #self.data_buffer[0] = self.data_buffer[0][m0_index:]
            #self.data_buffer[1] = self.data_buffer[1][m1_index:]
            return [{'column' : self.hist_cols_corr, 'row' : self.hist_rows_corr}]
                
        elif self.active_dut1 == 0 and self.active_dut2 == 0: #correlate fe to fe, useless fei4 correlation with itself will be shown, instead of nothing
            f0_index = correlation_functions.correlate_ff(self.data_buffer[0], self.hist_cols_corr, self.hist_rows_corr)
            self.data_buffer[0] = self.data_buffer[0][f0_index:]
            self.data_buffer[1] = self.data_buffer[1][f0_index:]
            return [{'column' : self.hist_cols_corr, 'row' : self.hist_rows_corr}]
            
            old_correaltion_on_event_number = """
    
            active_dut1_data = self.data_buffer[0][self.data_buffer[0]['event_number'] <= (self.event_n_step + self.data_buffer_done)]
            active_dut2_data = self.data_buffer[1][self.data_buffer[1]['event_number'] <= (self.event_n_step + self.data_buffer_done)]
    
            merged_active_dut1_data, merged_active_dut2_data = analysis_utils.merge_on_event_number(active_dut1_data, active_dut2_data)
            
            try:
                if self.active_dut1 != 0 and self.active_dut2 != 0:
                    hist_row_corr = analysis_utils.hist_2d_index(merged_active_dut1_data['row'], merged_active_dut2_data['row'], shape=(self.config['max_n_rows_m26'], self.config['max_n_rows_m26']))
                    hist_column_corr = analysis_utils.hist_2d_index(merged_active_dut1_data['column'], merged_active_dut2_data['column'], shape=(self.config['max_n_columns_m26'], self.config['max_n_columns_m26']))
                else:
                    hist_row_corr = analysis_utils.hist_2d_index(merged_active_dut1_data['row'], merged_active_dut2_data['row'], shape=(self.config['max_n_rows_fei4'], self.config['max_n_rows_fei4']))
                    hist_column_corr = analysis_utils.hist_2d_index(merged_active_dut1_data['column'], merged_active_dut2_data['column'], shape=(self.config['max_n_columns_fei4'], self.config['max_n_columns_fei4']))

            except IndexError:
                logging.warning('Histogram indices out of range!')
                return   
                
            self.hist_cols_corr += hist_column_corr    
            self.hist_rows_corr += hist_row_corr
                
            for i in range(2):
                self.data_buffer[i] = self.data_buffer[i][self.data_buffer[i]['event_number'] > (self.event_n_step + self.data_buffer_done)] #clearing buffer
              
            self.data_buffer_done = self.event_n_step + self.data_buffer_done #setting the new data_buffer_done
              
            return [{'column' : self.hist_cols_corr, 'row' : self.hist_rows_corr}]
            """
        
        elif self.active_dut1 == 0 and self.active_dut2 != 0: #correlate fei4 to m26
            
            fe_index , m26_index = correlation_functions.correlate_fm(self.data_buffer[0],self.data_buffer[1], self.hist_cols_corr ,self.hist_rows_corr,self.active_dut1,self.active_dut2)
            self.data_buffer[0]=self.data_buffer[0][fe_index :]
            self.data_buffer[1]=self.data_buffer[1][m26_index :]
            return [{'column' : self.hist_cols_corr, 'row' : self.hist_rows_corr}]
            
        elif self.active_dut1 != 0 and self.active_dut2 == 0: #correlate m26 to fei4
            
            fe_index , m26_index = correlation_functions.correlate_fm(self.data_buffer[1],self.data_buffer[0], self.hist_cols_corr ,self.hist_rows_corr,self.active_dut1,self.active_dut2)
            self.data_buffer[1]=self.data_buffer[1][fe_index :]
            self.data_buffer[0]=self.data_buffer[0][m26_index :]
            return [{'column' : self.hist_cols_corr, 'row' : self.hist_rows_corr}]
        else:
            return


    
    def serialze_data(self, data):
        return jsonapi.dumps(data, cls=utils.NumpyEncoder)
        #return utils.simple_enc(None, data)
        
    def handle_command(self, command):
        #declare functions
        def reset():
            self.hist_cols_corr = np.zeros_like(self.hist_cols_corr)
            self.hist_rows_corr = np.zeros_like(self.hist_rows_corr)
            self.data_buffer={}
        def get_hist_size(dut1, dut2):
            if dut1 == 0 and dut2 == 0:
                self.hist_cols_corr = np.zeros((self.config['max_n_columns_fei4'],self.config['max_n_columns_fei4']), dtype=np.uint32) # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
                self.hist_rows_corr = np.zeros((self.config['max_n_rows_fei4'],self.config['max_n_rows_fei4']), dtype=np.uint32)  # used to be self.hists_row_corr /
                reset()
            elif dut1 == 0 and dut2 != 0:
                self.hist_cols_corr = np.zeros((self.config['max_n_rows_fei4'],self.config['max_n_columns_m26']), dtype=np.uint32) # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
                self.hist_rows_corr = np.zeros((self.config['max_n_columns_fei4'],self.config['max_n_rows_m26']), dtype=np.uint32)  # used to be self.hists_row_corr /
                reset()
            elif dut1 != 0 and dut2 == 0:
                self.hist_cols_corr = np.zeros((self.config['max_n_columns_m26'],self.config['max_n_rows_fei4']), dtype=np.uint32) # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
                self.hist_rows_corr = np.zeros((self.config['max_n_rows_m26'],self.config['max_n_columns_fei4']), dtype=np.uint32)  # used to be self.hists_row_corr /
                reset()
            else:
                self.hist_cols_corr = np.zeros((self.config['max_n_columns_m26'],self.config['max_n_columns_m26']), dtype=np.uint32) # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
                self.hist_rows_corr = np.zeros((self.config['max_n_rows_m26'],self.config['max_n_rows_m26']), dtype=np.uint32)  # used to be self.hists_row_corr /
                reset()
        #commands
        if command[0] == 'RESET':
            reset()
        elif 'combobox1'in command[0]:
            self.active_dut1 = int(command[0].split()[1])
            reset()
        elif 'combobox2'in command[0]:
            self.active_dut2 = int(command[0].split()[1])
            reset()
        elif 'START' in command[0]: # first choose two telescope planes and then press start button to correlate
            self.start_signal = int(command[0].split()[1])
        elif 'ACTIVETAB' in command[0]: # 
            self.active_tab = str(command[0].split()[1])
        elif 'STOP' in command[0]:
            self.start_signal = int(command[0].split()[1])+1
            reset()
            #return [{'column' : np.zeros((1000,1000),dtype=np.uint32), 'row' : np.zeros((1000,1000),dtype=np.uint32)}] #try to set empty image in viewbox
        get_hist_size(self.active_dut1, self.active_dut2)
#             elif 'MASK' in command[0]:    #FIXME: make noisy pixel remover later
#                 if '0' in command[0]:
#                     self.mask_noisy_pixel = False
#                 else:
#                     self.mask_noisy_pixel = True   
                

