from online_monitor.converter.transceiver import Transceiver
from zmq.utils import jsonapi
import numpy as np

# pyBAR related imports
from pybar_fei4_interpreter.data_interpreter import PyDataInterpreter

from online_monitor.utils import utils


class PybarFEI4(Transceiver):

    def setup_interpretation(self):
        self.interpreter = PyDataInterpreter()
        self.interpreter.set_warning_output(False)

    def deserialze_data(self, data):  # According to pyBAR data serilization
        try:
            self.meta_data = jsonapi.loads(data)
        except ValueError:
            try:
                dtype = self.meta_data.pop('dtype')
                shape = self.meta_data.pop('shape')
                if self.meta_data:
                    try:
                        raw_data_array = np.frombuffer(buffer(data),
                                                       dtype=dtype).reshape(shape)
                        return raw_data_array
                    # KeyError happens if meta data read is omitted; ValueError
                    # if np.frombuffer fails due to wrong shape
                    except (KeyError, ValueError):
                        return None
            except AttributeError:  # Happens if first data is not meta data
                return None
        return {'meta_data': self.meta_data}

    def interpret_data(self, data):
        # Meta data is omitted, only raw data is interpreted
        if isinstance(data[0][1], dict):
            # Add info to meta data
            data[0][1]['meta_data'].update(
                {'n_hits': self.interpreter.get_n_hits(),
                 'n_events': self.interpreter.get_n_events()})
            return [data[0][1]]

        # For the summing of histograms the histogrammer converter is used
        self.interpreter.reset_histograms()
        self.interpreter.interpret_raw_data(data[0][1])

        interpreted_data = {
            'hits': self.interpreter.get_hits(),
            'tdc_counters': self.interpreter.get_tdc_counters(),
            'error_counters': self.interpreter.get_error_counters(),
            'service_records_counters': self.interpreter.get_service_records_counters(),
            'trigger_error_counters': self.interpreter.get_trigger_error_counters(),
        }

        return [interpreted_data]

    def serialze_data(self, data):
        # return jsonapi.dumps(data, cls=utils.NumpyEncoder)
        if 'hits' in data:
            hits_data = data['hits']
            data['hits'] = None
            return utils.simple_enc(hits_data, data)
        else:
            return utils.simple_enc(None, data)
