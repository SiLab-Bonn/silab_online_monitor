from online_monitor.converter.transceiver import Transceiver
from zmq.utils import jsonapi
import numpy as np

# pyBAR related imports
from pyBAR_mimosa26_interpreter.raw_data_interpreter import RawDataInterpreter

from online_monitor.utils import utils


class PybarMimosa26(Transceiver):

    def setup_interpretation(self):
        self.interpreter = RawDataInterpreter()
        self.n_hits = 0
        self.n_events = 0

    def deserialze_data(self, data):  # According to pyBAR data serilization
        try:
            self.meta_data = jsonapi.loads(data)
        except ValueError:
            try:
                dtype = self.meta_data.pop('dtype')
                shape = self.meta_data.pop('shape')
                if self.meta_data:
                    try:
                        raw_data_array = np.frombuffer(buffer(data), dtype=dtype).reshape(shape)
                        return raw_data_array
                    except (KeyError, ValueError):  # KeyError happens if meta data read is omitted; ValueError if np.frombuffer fails due to wrong sha
                        return None
            except AttributeError:  # Happens if first data is not meta data
                return None
        return {'meta_data': self.meta_data}

    def interpret_data(self, data):
        if isinstance(data[0][1], dict):  # Meta data is omitted, only raw data is interpreted
            # Add info to meta data
            data[0][1]['meta_data'].update({'n_hits': self.n_hits, 'n_events': self.n_events})
            return [data[0][1]]
        hits = self.interpreter.interpret_raw_data(data[0][1])

        interpreted_data = {
            'hits': hits,
            'device_type': 'm26'
        }

        self.n_hits = hits.shape[0]
        self.n_events = np.unique(hits['frame']).shape[0]

        # self.interpreter.reset_histograms()  # Not implemented yet
        return [interpreted_data]

    def serialze_data(self, data):
        return jsonapi.dumps(data, cls=utils.NumpyEncoder)
