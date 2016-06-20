from online_monitor.receiver.receiver import Receiver
from zmq.utils import jsonapi
import numpy as np
import time

from PyQt4 import Qt
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.ptime as ptime
from pyqtgraph.dockarea import DockArea, Dock


from online_monitor.utils import utils


class PybarMimosa26(Receiver):

    def setup_receiver(self):
        self.set_bidirectional_communication()  # We want to change converter settings

    def setup_widgets(self, parent, name):
        dock_area = DockArea()
        parent.addTab(dock_area, name)
        #parent.setTabsClosable(True)
        # Occupancy Docks
        self.occupancy_images = []

        for plane in range(3):  # Loop over 3 * 2 plot widgets
            # Dock left
            dock_occcupancy = Dock("Occupancy plane %d" % (2 * plane +1), size=(100, 200))
            dock_area.addDock(dock_occcupancy)
            occupancy_graphics = pg.GraphicsLayoutWidget()  # Plot docks
            occupancy_graphics.show()
            view = occupancy_graphics.addViewBox()
            self.occupancy_images.append(pg.ImageItem(border='w'))
            view.addItem(self.occupancy_images[2 * plane])
            #vew.setRange(QtCore.QRectF(0, 0, 80, 336))
            dock_occcupancy.addWidget(occupancy_graphics)

            # Dock right
            dock_occcupancy_2 = Dock("Occupancy plane %d" % (2 * plane + 2), size=(100, 200))
            dock_area.addDock(dock_occcupancy_2, 'right', dock_occcupancy)  
            occupancy_graphics = pg.GraphicsLayoutWidget()  # Plot docks
            occupancy_graphics.show()
            view = occupancy_graphics.addViewBox()
            self.occupancy_images.append(pg.ImageItem(border='w'))
            view.addItem(self.occupancy_images[2 * plane + 1])
            #view.setRange(QtCore.QRectF(0, 0, 80, 336))
            dock_occcupancy_2.addWidget(occupancy_graphics)

        # dock_event_status = Dock("Event status", size=(400, 400))
        # dock_trigger_status = Dock("Trigger status", size=(400, 400))

        # dock_area.addDock(dock_trigger_status, 'above', dock_service_records)
        # dock_area.addDock(dock_event_status, 'above', dock_trigger_status)
        dock_status = Dock("Status", size=(800, 40))
        dock_area.addDock(dock_status, 'top')

        # Status dock on top
        cw = QtGui.QWidget()
        cw.setStyleSheet("QWidget {background-color:white}")
        layout = QtGui.QGridLayout()
        cw.setLayout(layout)
        self.rate_label = QtGui.QLabel("Readout Rate\n0 Hz")
        self.hit_rate_label = QtGui.QLabel("Hit Rate\n0 Hz")
        self.event_rate_label = QtGui.QLabel("Event Rate\n0 Hz")
        self.timestamp_label = QtGui.QLabel("Data Timestamp\n")
        self.plot_delay_label = QtGui.QLabel("Plot Delay\n")
        self.scan_parameter_label = QtGui.QLabel("Scan Parameters\n")
        self.spin_box = Qt.QSpinBox(value=0)
        self.spin_box.setMaximum(1000000)
        self.spin_box.setSuffix(" Readouts")
        self.reset_button = QtGui.QPushButton('Reset')
        self.noisy_checkbox = QtGui.QCheckBox('Mask noisy pixels')
        layout.addWidget(self.timestamp_label, 0, 0, 0, 1)
        layout.addWidget(self.plot_delay_label, 0, 1, 0, 1)
        layout.addWidget(self.rate_label, 0, 2, 0, 1)
        layout.addWidget(self.hit_rate_label, 0, 3, 0, 1)
        layout.addWidget(self.event_rate_label, 0, 4, 0, 1)
        layout.addWidget(self.scan_parameter_label, 0, 5, 0, 1)
        layout.addWidget(self.spin_box, 0, 6, 0, 1)
        layout.addWidget(self.noisy_checkbox, 0, 7, 0, 1)
        layout.addWidget(self.reset_button, 0, 8, 0, 1)
        dock_status.addWidget(cw)

        # Connect widgets
        self.reset_button.clicked.connect(lambda: self.send_command('RESET'))
        self.spin_box.valueChanged.connect(lambda value: self.send_command(str(value)))
        self.noisy_checkbox.stateChanged.connect(lambda value: self.send_command('MASK %d' % value))

#         event_status_widget = pg.PlotWidget()
#         self.event_status_plot = event_status_widget.plot(np.linspace(-0.5, 15.5, 17), np.zeros((16)), stepMode=True)
#         event_status_widget.showGrid(y=True)
#         dock_event_status.addWidget(event_status_widget)

#         trigger_status_widget = pg.PlotWidget()
#         self.trigger_status_plot = trigger_status_widget.plot(np.linspace(-0.5, 7.5, 9), np.zeros((8)), stepMode=True)
#         trigger_status_widget.showGrid(y=True)
#         dock_trigger_status.addWidget(trigger_status_widget)

        self.plot_delay = 0

    def deserialze_data(self, data):

        datar, meta  = utils.simple_dec(data)
        if 'occupancies' in meta:
            meta['occupancies'] = datar
        return meta
        
        #return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)

    def handle_data(self, data):
        def update_rate(fps, hps, recent_total_hits, eps, recent_total_events):
            self.rate_label.setText("Readout Rate\n%d Hz" % fps)
            if self.spin_box.value() == 0:  # show number of hits, all hits are integrated
                self.hit_rate_label.setText("Total Hits\n%d" % int(recent_total_hits))
            else:
                self.hit_rate_label.setText("Hit Rate\n%d Hz" % int(hps))
            if self.spin_box.value() == 0:  # show number of events
                self.event_rate_label.setText("Total Events\n%d" % int(recent_total_events))
            else:
                self.event_rate_label.setText("Event Rate\n%d Hz" % int(eps))
        if 'meta_data' not in data:
            for plane in range(6):
                self.occupancy_images[plane].setImage(data['occupancies'][plane], autoDownsample=True)
#             self.event_status_plot.setData(x=np.linspace(-0.5, 15.5, 17), y=data['error_counters'], stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))
#             self.trigger_status_plot.setData(x=np.linspace(-0.5, 7.5, 9), y=data['trigger_error_counters'], stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))
        else:
            update_rate(data['meta_data']['fps'], data['meta_data']['hps'], data['meta_data']['total_hits'], data['meta_data']['eps'], data['meta_data']['total_events'])
            self.timestamp_label.setText("Data Timestamp\n%s" % time.asctime(time.localtime(data['meta_data']['timestamp_stop'])))
            self.scan_parameter_label.setText("Scan Parameters\n%s" % ', '.join('%s: %s' % (str(key), str(val)) for key, val in data['meta_data']['scan_parameters'].iteritems()))
            now = ptime.time()
            self.plot_delay = self.plot_delay * 0.9 + (now - data['meta_data']['timestamp_stop']) * 0.1
            self.plot_delay_label.setText("Plot Delay\n%s" % 'not realtime' if abs(self.plot_delay) > 5 else "%1.2f ms" % (self.plot_delay * 1.e3))
