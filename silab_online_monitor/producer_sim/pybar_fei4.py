''' This is a producer faking data coming from pyBAR by taking real data and sending these in chunks'''

import time
import numpy as np
import tables as tb
import zmq
import os

from online_monitor.utils.producer_sim import ProducerSim


class pyBarFEI4Sim(ProducerSim):

    def setup_producer_device(self):
        ProducerSim.setup_producer_device(self)
        with tb.openFile(self.config['data_file'], mode="r") as in_file_h5:
            self.meta_data = in_file_h5.root.meta_data[:]
            self.raw_data = in_file_h5.root.raw_data[:]
            self.scan_parameter_name = in_file_h5.root.scan_parameters.dtype.names
            self.scan_parameters = in_file_h5.root.scan_parameters[:]

    def get_data(self):
        for index, (index_start, index_stop) in enumerate(np.column_stack((self.meta_data['index_start'], self.meta_data['index_stop']))):
            data = []
            data.append(self.raw_data[index_start:index_stop])
            data.extend((float(self.meta_data[index]['timestamp_start']), float(self.meta_data[index]['timestamp_stop']), int(self.meta_data[index]['error'])))
            time.sleep(self.meta_data[index]['timestamp_stop'] - self.meta_data[index]['timestamp_start'])
            return data, {"PlsrDAC": int(self.scan_parameters[index][0])}

    def send_data(self):
        '''Sends the data of every read out (raw data and meta data) via ZeroMQ to a specified socket
        '''
        time.sleep(float(self.config['delay']))  # Delay is given in seconds

        data, scan_parameters = self.get_data()
 
        data_meta_data = dict(
            name='ReadoutData',
            dtype=str(data[0].dtype),
            shape=data[0].shape,
            timestamp_start=data[1],  # float
            timestamp_stop=data[2],  # float
            readout_error=data[3],  # int
            scan_parameters=scan_parameters  # dict
        )
        try:
            self.sender.send_json(data_meta_data, flags=zmq.SNDMORE | zmq.NOBLOCK)
            self.sender.send(data[0], flags=zmq.NOBLOCK)  # PyZMQ supports sending numpy arrays without copying any data
        except zmq.Again:
            pass