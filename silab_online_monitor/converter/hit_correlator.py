from zmq.utils import jsonapi
import numpy as np
import sys, time
import psutil
import logging
import gc
from online_monitor.converter.transceiver import Transceiver
from online_monitor.utils import utils
from numba import njit

#from testbeam_analysis.tools import analysis_utils
#from numpy import corrcoef
from pyBAR_mimosa26_interpreter import correlation_functions, correlatefm_test
#from pybar_fei4_interpreter import analysis_functions

class HitCorrelator(Transceiver):
    
    def setup_transceiver(self):
        self.set_bidirectional_communication()  # We want to be able to change the histogrammmer settings
    
    def setup_interpretation(self):
        ### variables to determine whether to do sth or not
        self.active_tab = None # stores name (str) of active tab in online monitor
        self.hit_corr_tab = 'Hit_Correlator' # store name (str) of hit_correlator tab
        self.start_signal = 1 # will be set in handle_command function; correlation starts if this is set to 0
        ### variables to store integer value of active duts
        self.active_dut1 = 0 
        self.active_dut2 = 0
        ### variables fps
        self.fps = 0
        self.updateTime = 0
        ### mask noisy pixels
        self.mask_noisy_pixel = False
        self.mask_noisy_checkbox = 0
        ### transpose cols and rows due to fei4 rotation
        self.transpose = True # this is true for our setup
        self.transpose_checkbox = 0
        ### data buffer and histogramms
        self.data_buffer = {} # the data does not have to arrive at the same receive command since ZMQ buffers data and the DUT can have different time behavior
        self.hist_cols_corr = 0 # must be a np.array with dimensions cols x cols; will be set by get_hist_size function in handle_command function
        self.hist_rows_corr = 0 # must be a np.array with dimensions rows x rows; will be set by get_hist_size function in handle_command function

#         ### make measurements of avg cpu load and memory
#          self.procss = psutil.Process(self.ident)
#          self.prs_avg_cpu = 0
#          self.avg_cpu = 0
#          self.n = 1.0
#          self.avg_ram = 0

    def deserialze_data(self, data):  # According to pyBAR data serilization
        datar, meta  = utils.simple_dec(data)
        if 'hits' in meta:
            meta['hits'] = datar
        return meta
      
    def interpret_data(self, data):

        if self.active_tab != self.hit_corr_tab: # if active tab in online monitor is not hit correlator, return
            return
        
        self.active_duts = [self.active_dut1,self.active_dut2] # create arry of active DUTs; their values are set in handle_command

        if self.start_signal != 0: # default value is 1; if start-button is pressed, it is set to 0, if stop-button is pressed, back to 1
            #print "Press 'Start'-button"
            return
        
        ### only needed to show readout rate in GUI
        if 'meta_data' in data[0][1]: # Meta data is directly forwarded to the receiver, only hit data is correlated; 0 from frontend index, 1 for data dict
            meta_data = data[0][1]['meta_data']
            now = float(meta_data['timestamp_stop'])
            if now != self.updateTime: #FIXME: sometimes = ZeroDivisionError: because of https://github.com/SiLab-Bonn/pyBAR/issues/48
                recent_fps = 1.0 / (now - self.updateTime)  #FIXME: does not show real rate, shows rate data was recorded with
                self.updateTime = now
                self.fps = self.fps * 0.7 + recent_fps * 0.3
                meta_data.update({'fps': self.fps})
                return [data[0][1]]

       
        ### loop over data and determine whether it is fe or mimosa data 
        for actual_dut_data in data:
            
            if 'meta_data' in actual_dut_data[1]:  # meta_data is skipped
                continue
            if actual_dut_data[1]['hits'].shape[0] == 0: # empty array is skipped
                continue
            
            if 'plane' in actual_dut_data[1]['hits'].dtype.names: # mimosa data has keyword 'plane'
                mimosa_hits = actual_dut_data[1]['hits'] 
            else: # fe data
                fe_hits = actual_dut_data[1]['hits']
                      
        ### copy hits to buffer; self.active_duts[0]/[1] will have key 0/1
        for i,active_dut in enumerate(self.active_duts):
            
            if active_dut == 0 and 'fe_hits' in locals(): # active dut is fei4 and fe_hits exists
                if i in self.data_buffer.keys():
                    self.data_buffer[i] = np.append(self.data_buffer[i],fe_hits) # if key already is in buffer, append fe_data
                else:
                    self.data_buffer[i] = fe_hits # create key and value where value is fe_data
            
            elif active_dut != 0 and 'mimosa_hits' in locals(): # active dut is mimosa and mimosa_hits exists
                if i in self.data_buffer.keys(): 
                    self.data_buffer[i] = np.append(self.data_buffer[i],mimosa_hits[mimosa_hits['plane']==active_dut]) # if key already is in buffer, append m26_data with plane == active dut
                else: 
                    self.data_buffer[i] = mimosa_hits[mimosa_hits['plane']==active_dut] # create key and value where value is m26_data with plane == active dut
         
        ### if no data to process return 
        if len(self.data_buffer)!=2: #wait until there is data of both selected duts
            print 'Loading data of selected DUTs...'
            return
        ### if one of the data buffer keys data is empty return
        elif len(self.data_buffer[0]) == 0 or len(self.data_buffer[1]) == 0:
            return
        
#         ###get average system characteristics over hit correlator runtime
#         self.prs_avg_cpu += self.procss.cpu_percent()
#         self.avg_cpu += psutil.cpu_percent()
#         memoryy = psutil.virtual_memory()
#         self.avg_ram += (memoryy.total-memoryy.available)/1024.0**2 #(memory.total - memory.available) - (memory.buffers + memory.cached) #according to htop
#         self.n += 1.0
        
        ### make correlation
        if self.active_dut1 != 0 and self.active_dut2 != 0: #correlate m26 to m26
            
            ### main correlation function
            m0_index, m1_index = correlation_functions.correlate_mm(self.data_buffer[0], self.data_buffer[1], self.hist_cols_corr, self.hist_rows_corr)
            
            if m0_index == -1 and m1_index == -1:
                print "Error! Outer loop terminated"
                return
            
            self.data_buffer[0] = np.delete(self.data_buffer[0], np.arange(0,m0_index)) # delete the already correlated data
            self.data_buffer[1] = np.delete(self.data_buffer[1], np.arange(0,m1_index)) # delete the already correlated data
            return [{'column' : self.hist_cols_corr, 'row' : self.hist_rows_corr}]
                
        elif self.active_dut1 == 0 and self.active_dut2 == 0: #correlate fe to fe, fei4 correlation with itself will be shown, instead of nothing
            ### main correlation function
            f0_index = correlation_functions.correlate_ff(self.data_buffer[0], self.hist_cols_corr, self.hist_rows_corr)
            
            self.data_buffer[0] = np.delete(self.data_buffer[0], np.arange(0,f0_index))
            self.data_buffer[1] = np.delete(self.data_buffer[1], np.arange(0,f0_index))
            return [{'column' : self.hist_cols_corr, 'row' : self.hist_rows_corr}]
                    
        elif self.active_dut1 == 0 and self.active_dut2 != 0: #correlate fei4 to m26
            ### main correlation function
            fe_index , m26_index = correlation_functions.correlate_fm(self.data_buffer[0],self.data_buffer[1], self.hist_cols_corr ,self.hist_rows_corr,self.active_dut1,self.active_dut2, self.transpose)
            #print fe_index,m26_index
            if fe_index == -1 and m26_index == -1:
                logging.error('Outer loop terminated! Mimosa index equal or greater then length of data array!')
                return
            
            self.data_buffer[0] = np.delete(self.data_buffer[0], np.arange(0,fe_index))
            self.data_buffer[1] = np.delete(self.data_buffer[1], np.arange(0,m26_index))
            return [{'column' : self.hist_cols_corr, 'row' : self.hist_rows_corr}]
            
        elif self.active_dut1 != 0 and self.active_dut2 == 0: #correlate m26 to fei4
            ### main correlation function
            fe_index , m26_index = correlation_functions.correlate_fm(self.data_buffer[1],self.data_buffer[0], self.hist_cols_corr ,self.hist_rows_corr,self.active_dut1,self.active_dut2, self.transpose)
            #print fe_index, m26_index
            if fe_index == -1 and m26_index == -1:
                logging.error('Outer loop terminated! Mimosa index equal or greater then length of data array!')
                return
            
            self.data_buffer[0] = np.delete(self.data_buffer[0], np.arange(0,m26_index))
            self.data_buffer[1] = np.delete(self.data_buffer[1], np.arange(0,fe_index))
            return [{'column' : self.hist_cols_corr, 'row' : self.hist_rows_corr}]
        
        else:
            return
    
    def serialze_data(self, data):
        return jsonapi.dumps(data, cls=utils.NumpyEncoder)
        #return utils.simple_enc(None, data)
        
    def handle_command(self, command):
        ### declare functions
        
        ### reset histogramms and data buffer, call garbage collector
        def reset():
            self.hist_cols_corr = np.zeros_like(self.hist_cols_corr)
            self.hist_rows_corr = np.zeros_like(self.hist_rows_corr)
            self.data_buffer={}
            gc.collect() #garbage collector is called to free unused memory
        
        ### determine the needed histogramm size according to selected DUTs and transposed FEI4
        def get_hist_size(dut1, dut2, transpose):
            if dut1 == 0 and dut2 == 0:
                self.hist_cols_corr = np.zeros((self.config['max_n_columns_fei4'],self.config['max_n_columns_fei4']), dtype=np.uint32) # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
                self.hist_rows_corr = np.zeros((self.config['max_n_rows_fei4'],self.config['max_n_rows_fei4']), dtype=np.uint32)  # used to be self.hists_row_corr /
                reset()
            elif dut1 == 0 and dut2 != 0:
                if transpose == True:
                    self.hist_cols_corr = np.zeros((self.config['max_n_rows_fei4'],self.config['max_n_columns_m26']), dtype=np.uint32) # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
                    self.hist_rows_corr = np.zeros((self.config['max_n_columns_fei4'],self.config['max_n_rows_m26']), dtype=np.uint32)  # used to be self.hists_row_corr /
                else:
                    self.hist_cols_corr = np.zeros((self.config['max_n_columns_fei4'],self.config['max_n_columns_m26']), dtype=np.uint32) # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
                    self.hist_rows_corr = np.zeros((self.config['max_n_rows_fei4'],self.config['max_n_rows_m26']), dtype=np.uint32)  # used to be self.hists_row_corr /
                reset()
            elif dut1 != 0 and dut2 == 0:
                if transpose == True:
                    self.hist_cols_corr = np.zeros((self.config['max_n_columns_m26'],self.config['max_n_rows_fei4']), dtype=np.uint32) # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
                    self.hist_rows_corr = np.zeros((self.config['max_n_rows_m26'],self.config['max_n_columns_fei4']), dtype=np.uint32)  # used to be self.hists_row_corr /
                else:
                    self.hist_cols_corr = np.zeros((self.config['max_n_columns_m26'],self.config['max_n_columns_fei4']), dtype=np.uint32) # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
                    self.hist_rows_corr = np.zeros((self.config['max_n_rows_m26'],self.config['max_n_rows_fei4']), dtype=np.uint32)  # used to be self.hists_row_corr /
                reset()
            else:
                self.hist_cols_corr = np.zeros((self.config['max_n_columns_m26'],self.config['max_n_columns_m26']), dtype=np.uint32) # used to be self.hists_column_corr / empty dict to save every dut with its IP as key and data as value
                self.hist_rows_corr = np.zeros((self.config['max_n_rows_m26'],self.config['max_n_rows_m26']), dtype=np.uint32)  # used to be self.hists_row_corr /
                reset()
        ### end of declaration
        
        ### commands
        if command[0] == 'RESET':
            reset()
        elif 'combobox1'in command[0]: # received signal is 'combobox1 value' where value is position of combobox 1; 0 ==fe, 1-6 == m26_1 -m26_6
            self.active_dut1 = int(command[0].split()[1])
            get_hist_size(self.active_dut1, self.active_dut2, self.transpose) # execute get_hist_size after DUTs have been selected in GUI
        elif 'combobox2'in command[0]: # received signal is 'combobox2 value' where value is position of combobox 2; 0 ==fe, 1-6 == m26_1 -m26_6
            self.active_dut2 = int(command[0].split()[1])
            get_hist_size(self.active_dut1, self.active_dut2, self.transpose) # execute get_hist_size after DUTs have been selected in GUI
        elif 'START' in command[0]: # first choose two telescope planes and then press start button to correlate
            self.start_signal = int(command[0].split()[1])
            get_hist_size(self.active_dut1, self.active_dut2, self.transpose) # execute get_hist_size after DUTs have been selected in GUI
            print '\n'
            print '#######################', ' START ', '#######################\n'
        elif 'ACTIVETAB' in command[0]: # received signal is 'ACTIVETAB tab' where tab is the name (str) of the selected tab in online monitor
            self.active_tab = str(command[0].split()[1])
        elif 'STOP' in command[0]: # received whenever 'Stop'-button is pressed; set start signal to 1
            self.start_signal = int(command[0].split()[1])+1
            print '\n'
            print '#######################', ' STOP ', '#######################\n'
#             print "AVERAGE CPU ==", self.avg_cpu / self.n
#             print "AVERAGE PROCESS CPU ==", self.prs_avg_cpu / self.n
#             print "AVERAGE RAM ==", self.avg_ram / self.n
            reset()
        elif 'MASK' in command[0]: # FIXME
            self.mask_noisy_checkbox = int(command[0].split()[1])
            if self.mask_noisy_checkbox == 0:
                self.mask_noisy_pixel = False
            elif self.mask_noisy_checkbox == 2:
                self.mask_noisy_pixel = True
            print 'Noisy pixel cut not implemented yet!' # FIXME
        elif 'TRANSPOSE' in command[0]:
            self.transpose_checkbox = int(command[0].split()[1])
            if self.active_dut1 == 0 or self.active_dut2 == 0:
                if self.transpose_checkbox == 0: # transpose_checkbox is not checked
                    self.transpose = True
                elif self.transpose_checkbox == 2: # transpose_checkbox is checked
                    self.transpose = False
                get_hist_size(self.active_dut1, self.active_dut2, self.transpose) # execute get_hist_size after DUTs have been selected in GUI
                
                

