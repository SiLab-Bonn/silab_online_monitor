''' Histograms the ATLAS-FEI4 hit table and integrates histograms'''

from zmq.utils import jsonapi
import numpy as np

# Online monitor imports
from online_monitor.converter.transceiver import Transceiver
from online_monitor.utils import utils

# pyBAR related imports
from pybar_fei4_interpreter.data_histograming import PyDataHistograming


class PybarFEI4Histogrammer(Transceiver):

    def setup_transceiver(self):
        # We want to be able to change the histogrammmer settings
        # thus bidirectional communication needed
        self.set_bidirectional_communication()

    def setup_interpretation(self):
        self.histograming = PyDataHistograming()
        self.histograming.set_no_scan_parameter()
        self.histograming.create_occupancy_hist(True)
        self.histograming.create_rel_bcid_hist(True)
        self.histograming.create_tot_hist(True)
        self.histograming.create_tdc_value_hist(True)
        # Variables
        self.n_readouts = 0
        self.readout = 0
        self.fps = 0  # data frames per second
        self.hps = 0  # hits per second
        self.eps = 0  # events per second
        self.plot_delay = 0
        self.total_hits = 0
        self.total_events = 0
        self.updateTime = 0
        # Histogrammes from interpretation stored for summing
        self.tdc_counters = None
        self.error_counters = None
        self.sr_counters = None
        self.trig_err_counters = None

    def deserialize_data(self, data):
        # return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)

        datar, meta = utils.simple_dec(data)
        if 'hits' in meta:
            meta['hits'] = datar
        return meta

    def interpret_data(self, data):

        # Meta data is directly forwarded to the receiver, only hit data and
        # event counters are histogramed; index 0 for frontend index, 1
        # 1 for data dict
        if 'meta_data' in data[0][1]:
            meta_data = data[0][1]['meta_data']
            try:
                now = float(meta_data['timestamp_stop'])
                recent_total_hits = meta_data['n_hits']
                recent_total_events = meta_data['n_events']
                recent_fps = 1.0 / (now - self.updateTime)  # calculate FPS
                delta_hits = recent_total_hits - self.total_hits
                recent_hps = delta_hits / (now - self.updateTime)
                delta_events = recent_total_events - self.total_events
                recent_eps = delta_events / (now - self.updateTime)
                self.updateTime = now
                self.total_hits = recent_total_hits
                self.total_events = recent_total_events
                self.fps = self.fps * 0.7 + recent_fps * 0.3
                self.hps = self.hps + (recent_hps - self.hps) * 0.3 / self.fps
                self.eps = self.eps + (recent_eps - self.eps) * 0.3 / self.fps
                meta_data.update({'fps': self.fps, 'hps': self.hps,
                                  'total_hits': self.total_hits,
                                  'eps': self.eps,
                                  'total_events': self.total_events})
                return [data[0][1]]
            except KeyError:
                import logging
                logging.fatal('META DATA WEIRD %s', str(meta_data))

        self.readout += 1

        if self.n_readouts != 0:  # = 0 for infinite integration
            if self.readout % self.n_readouts == 0:
                self.histograming.reset()
                self.tdc_counters = np.zeros_like(self.tdc_counters)
                self.error_counters = np.zeros_like(self.error_counters)
                self.sr_counters = np.zeros_like(self.sr_counters)
                self.trig_err_counters = np.zeros_like(self.trig_err_counters)
                self.readouts = 0

        interpreted_data = data[0][1]

        self.histograming.add_hits(interpreted_data['hits'])

        # Sum up interpreter histograms
        if self.tdc_counters is not None:
            self.tdc_counters += interpreted_data['tdc_counters']
        else:
            # Copy needed to give ownage to histogrammer
            self.tdc_counters = interpreted_data['tdc_counters'].copy()
        if self.error_counters is not None:
            self.error_counters += interpreted_data['error_counters']
        else:
            # Copy needed to give ownage to histogrammer
            self.error_counters = interpreted_data['error_counters'].copy()
        if self.sr_counters is not None:
            self.sr_counters += interpreted_data['service_records_counters']
        else:
            # Copy needed to give ownage to histogrammer
            self.sr_counters = interpreted_data['service_records_counters'].copy()
        if self.trig_err_counters is not None:
            self.trig_err_counters += interpreted_data['trigger_error_counters']
        else:
            # Copy needed to give ownage to histogrammer
            self.trig_err_counters = interpreted_data['trigger_error_counters'].copy()

        histogrammed_data = {
            'occupancy': self.histograming.get_occupancy(),
            'tot_hist': self.histograming.get_tot_hist(),
            'tdc_counters': self.tdc_counters,
            'error_counters': self.error_counters,
            'service_records_counters': self.sr_counters,
            'trigger_error_counters': self.trig_err_counters,
            'rel_bcid_hist': self.histograming.get_rel_bcid_hist()
        }

        return [histogrammed_data]

    def serialize_data(self, data):
        # return jsonapi.dumps(data, cls=utils.NumpyEncoder)

        if 'occupancies' in data:
            hits_data = data['occupancies']
            data['occupancies'] = None
            return utils.simple_enc(hits_data, data)
        else:
            return utils.simple_enc(None, data)

    def handle_command(self, command):
        if command[0] == 'RESET':
            self.histograming.reset()
            self.tdc_counters = np.zeros_like(self.tdc_counters)
            self.error_counters = np.zeros_like(self.error_counters)
            self.sr_counters = np.zeros_like(self.sr_counters)
            self.trig_err_counters = np.zeros_like(self.trig_err_counters)
        else:
            self.n_readouts = int(command[0])
