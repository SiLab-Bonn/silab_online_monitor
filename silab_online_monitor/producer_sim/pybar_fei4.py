''' This is a producer faking data coming from pyBAR by taking real data and sending these in chunks'''

import time
import numpy as np
import tables as tb
import zmq
import logging

from pybar.daq.fei4_raw_data import send_data

from online_monitor.utils.producer_sim import ProducerSim


class pyBarFEI4Sim(ProducerSim):

    def setup_producer_device(self):
        ProducerSim.setup_producer_device(self)
        self.delay = float(self.config.get('delay', 0.))

    def _get_data(self):  # Return the data of one readout
        ''' Yield data of one readout

            Delay return if replay is too fast
        '''
        with tb.open_file(self.config['data_file'], mode="r") as in_file_h5:
            meta_data = in_file_h5.root.meta_data[:]
            raw_data = in_file_h5.root.raw_data
            n_readouts = meta_data.shape[0]

            try:
                self.scan_parameter_name = in_file_h5.root.scan_parameters.dtype.names
                self.scan_parameters = in_file_h5.root.scan_parameters[:]
            except tb.NoSuchNodeError:
                self.scan_parameter_name = 'No parameter'
                self.scan_parameters = None

            self.last_readout_time = time.time()

            for i in range(n_readouts):
                # Raw data indeces of readout
                i_start = meta_data['index_start'][i]
                i_stop = meta_data['index_stop'][i]

                # Time stamp of readout
                t_start = meta_data[i]['timestamp_start']

                data = []
                data.append(raw_data[i_start:i_stop])
                data.extend((float(meta_data[i]['timestamp_start']),
                             float(meta_data[i]['timestamp_stop']),
                             int(meta_data[i]['error'])))

                # Determine replay delays
                if i == 0:  # Initialize on first readout
                    self.last_timestamp_start = t_start
                now = time.time()
                delay = now - self.last_readout_time
                additional_delay = t_start - self.last_timestamp_start - delay
                if additional_delay > 0:
                    # Wait if send too fast, especially needed when readout was
                    # stopped during data taking (e.g. for mask shifting)
                    time.sleep(additional_delay)
                self.last_readout_time = time.time()
                self.last_timestamp_start = t_start

                if self.scan_parameters is not None:
                    yield data, {str(self.scan_parameter_name): int(self.scan_parameters[i][0])}
                else:
                    yield data, {'No parameter': 0}

    def send_data(self):
        '''Sends the data of every read out (raw data and meta data)

            Sending via ZeroMQ to a specified socket.
        '''
        for data, scan_parameters in self._get_data():
            time.sleep(self.delay)
            send_data(socket=self.sender, data=data, scan_parameters=scan_parameters)

    def __del__(self):
        self.in_file_h5.close()
