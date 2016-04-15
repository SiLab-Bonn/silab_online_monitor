''' Histograms the Mimosa26 hit table'''

import time
from zmq.utils import jsonapi
import numpy as np

# Online monitor imports
from online_monitor.converter.transceiver import Transceiver
from online_monitor.utils import utils

# pyBAR related imports
from silab_utils import analysis_utils


class PybarMimosa26Histogrammer(Transceiver):

    def setup_transceiver(self):
        self.set_bidirectional_communication()  # We want to be able to change the histogrammmer settings

    def setup_interpretation(self):
        self.occupancy_arrays = np.zeros(shape=(6, 1152, 576), dtype=np.int32)
        # Variables
        self.n_readouts = 0
        self.readout = 0
        self.fps = 0  # data frames per second
        self.hps = 0  # hits per second
        self.eps = 0  # events per second
        self.plot_delay = 0
        self.total_hits = 0
        self.total_events = 0
        self.updateTime = time.time()
        self.mask_noisy_pixel = False
        # Histogrammes from interpretation stored for summing
#         self.error_counters = None
#         self.trigger_error_counters = None

    def deserialze_data(self, data):
        return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)

    def interpret_data(self, data):
        if 'meta_data' in data[0][1]:  # Meta data is directly forwarded to the receiver, only hit data, event counters are histogramed; 0 from frontend index, 1 for data dict
            meta_data = data[0][1]['meta_data']
            now = time.time()
            recent_total_hits = meta_data['n_hits']
            recent_total_events = meta_data['n_events']
            recent_fps = 1.0 / (now - self.updateTime)  # calculate FPS
            recent_hps = (recent_total_hits - self.total_hits) / (now - self.updateTime)
            recent_eps = (recent_total_events - self.total_events) / (now - self.updateTime)
            self.updateTime = now
            self.total_hits += recent_total_hits
            self.total_events += recent_total_events
            self.fps = self.fps * 0.7 + recent_fps * 0.3
            self.hps = self.hps + (recent_hps - self.hps) * 0.3 / self.fps
            self.eps = self.eps + (recent_eps - self.eps) * 0.3 / self.fps
            meta_data.update({'fps': self.fps, 'hps': self.hps, 'total_hits': self.total_hits, 'eps': self.eps, 'total_events': self.total_events})
            return [data[0][1]]

        self.readout += 1

        if self.n_readouts != 0:  # 0 for infinite integration
            if self.readout % self.n_readouts == 0:
                self.occupancy_arrays = np.zeros(shape=(6, 1152, 576), dtype=np.int32)  # Reset occ hists
#                 self.error_counters = np.zeros_like(self.error_counters)
#                 self.trigger_error_counters = np.zeros_like(self.trigger_error_counters)
                self.readouts = 0

        hits = data[0][1]['hits']

        if hits.shape[0] == 0:  # Empty array
            return

        for plane in range(6):  # Loop over Mimosa planes
            actual_plane_hits = hits[hits['plane'] == plane]  # Select plane hits
            self.occupancy_arrays[plane] += analysis_utils.hist_2d_index(actual_plane_hits['column'], actual_plane_hits['row'], shape=(1152, 576))
            if self.mask_noisy_pixel:
                self.occupancy_arrays[plane][self.occupancy_arrays[plane] > np.percentile(self.occupancy_arrays[plane], 100 - self.config['noisy_threshold'])] = 0

#         # Sum up interpreter histograms
#         if self.error_counters is not None:
#             self.error_counters += interpreted_data['error_counters']
#         else:
#             self.error_counters = interpreted_data['error_counters'].copy()  # Copy needed to give ownage to histogrammer
#         if self.trigger_error_counters is not None:
#             self.trigger_error_counters += interpreted_data['trigger_error_counters']
#         else:
#             self.trigger_error_counters = interpreted_data['trigger_error_counters'].copy()  # Copy needed to give ownage to histogrammer

        histogrammed_data = {
            'occupancies': self.occupancy_arrays
        }

        return [histogrammed_data]

    def serialze_data(self, data):
        return jsonapi.dumps(data, cls=utils.NumpyEncoder)

    def handle_command(self, command):
        if command[0] == 'RESET':
            self.occupancy_arrays = np.zeros(shape=(6, 1152, 576), dtype=np.int32)  # Reset occ hists
            self.total_hits = 0
            self.total_events = 0
        elif 'MASK' in command[0]:
            if '0' in command[0]:
                self.mask_noisy_pixel=False
            else:
                self.mask_noisy_pixel=True
        else:
            self.n_readouts = int(command[0])
            self.occupancy_arrays = np.zeros(shape=(6, 1152, 576), dtype=np.int32)  # Reset occ hists
