from online_monitor.receiver.receiver import Receiver
from zmq.utils import jsonapi
import numpy as np
import time

from PyQt5 import Qt
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.ptime as ptime
from pyqtgraph.dockarea import DockArea, Dock


from online_monitor.utils import utils


class PybarFEI4(Receiver):

    def setup_receiver(self):
        self.set_bidirectional_communication()  # We want to change converter settings

    def setup_widgets(self, parent, name):
        dock_area = DockArea()
        parent.addTab(dock_area, name)
        # Docks
        dock_occcupancy = Dock("Occupancy", size=(400, 400))
        dock_run_config = Dock("Run configuration", size=(400, 400))
        dock_global_config = Dock("Global configuration", size=(400, 400))
        dock_tot = Dock("Time over threshold values (TOT)", size=(400, 400))
        dock_tdc = Dock("Time digital converter values (TDC)", size=(400, 400))
        dock_event_status = Dock("Event status", size=(400, 400))
        dock_trigger_status = Dock("Trigger status", size=(400, 400))
        dock_service_records = Dock("Service records", size=(400, 400))
        dock_hit_timing = Dock("Hit timing (rel. BCID)", size=(400, 400))
        dock_status = Dock("Status", size=(800, 40))
        dock_area.addDock(dock_global_config, 'left')
        dock_area.addDock(dock_run_config, 'above', dock_global_config)
        dock_area.addDock(dock_occcupancy, 'above', dock_run_config)
        dock_area.addDock(dock_tdc, 'right', dock_occcupancy)
        dock_area.addDock(dock_tot, 'above', dock_tdc)
        dock_area.addDock(dock_service_records, 'bottom', dock_occcupancy)
        dock_area.addDock(dock_trigger_status, 'above', dock_service_records)
        dock_area.addDock(dock_event_status, 'above', dock_trigger_status)
        dock_area.addDock(dock_hit_timing, 'bottom', dock_tot)
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
        layout.addWidget(self.timestamp_label, 0, 0, 0, 1)
        layout.addWidget(self.plot_delay_label, 0, 1, 0, 1)
        layout.addWidget(self.rate_label, 0, 2, 0, 1)
        layout.addWidget(self.hit_rate_label, 0, 3, 0, 1)
        layout.addWidget(self.event_rate_label, 0, 4, 0, 1)
        layout.addWidget(self.scan_parameter_label, 0, 5, 0, 1)
        layout.addWidget(self.spin_box, 0, 6, 0, 1)
        layout.addWidget(self.reset_button, 0, 7, 0, 1)
        dock_status.addWidget(cw)

        # Connect widgets
        self.reset_button.clicked.connect(lambda: self.send_command('RESET'))
        self.spin_box.valueChanged.connect(lambda value: self.send_command(str(value)))

        # Run config dock
        self.run_conf_list_widget = Qt.QListWidget()
        dock_run_config.addWidget(self.run_conf_list_widget)

        # Global config dock
        self.global_conf_list_widget = Qt.QListWidget()
        dock_global_config.addWidget(self.global_conf_list_widget)

        # color occupancy
        poss = np.array([0.0, 0.6, 1.0])
        color = np.array([[25, 25, 112, 255], [173, 255, 47, 255], [255, 0, 0, 255]], dtype=np.ubyte)  # [RED,GREEN,BLUE,BLACK/WHITE]
        mapp = pg.ColorMap(poss, color)
        lutt = mapp.getLookupTable(0.0, 1.0, 100)

        # Different plot docks
        occupancy_graphics = pg.GraphicsLayoutWidget()
        occupancy_graphics.show()
        view = occupancy_graphics.addViewBox()
        self.occupancy_img = pg.ImageItem(border='w')
        self.occupancy_img.setLookupTable(lutt, update=True)
        # view.addItem(self.occupancy_img)
        plot = pg.PlotWidget(viewBox=view, labels={'bottom': 'Column', 'left': 'Row'})
        plot.addItem(self.occupancy_img)
        #view.setRange(QtCore.QRectF(0, 0, 80, 336))
        dock_occcupancy.addWidget(plot)

        tot_plot_widget = pg.PlotWidget(background="w")
        self.tot_plot = tot_plot_widget.plot(np.linspace(-0.5, 15.5, 17), np.zeros((16)), stepMode=True)
        tot_plot_widget.showGrid(y=True)
        dock_tot.addWidget(tot_plot_widget)

        tdc_plot_widget = pg.PlotWidget(background="w")
        self.tdc_plot = tdc_plot_widget.plot(np.linspace(-0.5, 4095.5, 4097), np.zeros((4096)), stepMode=True)
        tdc_plot_widget.showGrid(y=True)
        tdc_plot_widget.setXRange(0, 800, update=True)
        dock_tdc.addWidget(tdc_plot_widget)

        event_status_widget = pg.PlotWidget()
        self.event_status_plot = event_status_widget.plot(np.linspace(-0.5, 15.5, 17), np.zeros((16)), stepMode=True)
        event_status_widget.showGrid(y=True)
        dock_event_status.addWidget(event_status_widget)

        trigger_status_widget = pg.PlotWidget()
        self.trigger_status_plot = trigger_status_widget.plot(np.linspace(-0.5, 7.5, 9), np.zeros((8)), stepMode=True)
        trigger_status_widget.showGrid(y=True)
        dock_trigger_status.addWidget(trigger_status_widget)

        service_record_widget = pg.PlotWidget()
        self.service_record_plot = service_record_widget.plot(np.linspace(-0.5, 31.5, 33), np.zeros((32)), stepMode=True)
        service_record_widget.showGrid(y=True)
        dock_service_records.addWidget(service_record_widget)

        hit_timing_widget = pg.PlotWidget()
        self.hit_timing_plot = hit_timing_widget.plot(np.linspace(-0.5, 15.5, 17), np.zeros((16)), stepMode=True)
        hit_timing_widget.showGrid(y=True)
        dock_hit_timing.addWidget(hit_timing_widget)

        self.plot_delay = 0

    def deserialize_data(self, data):
        datar, meta = utils.simple_dec(data)
        if 'occupancies' in meta:
            meta['occupancies'] = datar
        return meta

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
            self.occupancy_img.setImage(data['occupancy'][:, :, 0], autoDownsample=True)
            self.tot_plot.setData(x=np.linspace(-0.5, 15.5, 17), y=data['tot_hist'], fillLevel=0, brush=(0, 0, 255, 150))
            self.tdc_plot.setData(x=np.linspace(-0.5, 4096.5, 4097), y=data['tdc_counters'], fillLevel=0, brush=(0, 0, 255, 150))
            self.event_status_plot.setData(x=np.linspace(-0.5, 15.5, 17), y=data['error_counters'], stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))
            self.service_record_plot.setData(x=np.linspace(-0.5, 31.5, 33), y=data['service_records_counters'], stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))
            self.trigger_status_plot.setData(x=np.linspace(-0.5, 7.5, 9), y=data['trigger_error_counters'], stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))
            self.hit_timing_plot.setData(x=np.linspace(-0.5, 15.5, 17), y=data['rel_bcid_hist'][:16], stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))
        else:
            update_rate(data['meta_data']['fps'], data['meta_data']['hps'], data['meta_data']['total_hits'], data['meta_data']['eps'], data['meta_data']['total_events'])
            self.timestamp_label.setText("Data Timestamp\n%s" % time.asctime(time.localtime(data['meta_data']['timestamp_stop'])))
            self.scan_parameter_label.setText("Scan Parameters\n%s" % ', '.join('%s: %s' % (str(key), str(val)) for key, val in data['meta_data']['scan_parameters'].iteritems()))
            now = ptime.time()
            self.plot_delay = self.plot_delay * 0.9 + (now - data['meta_data']['timestamp_stop']) * 0.1
            self.plot_delay_label.setText("Plot Delay\n%s" % 'not realtime' if abs(self.plot_delay) > 5 else "%1.2f ms" % (self.plot_delay * 1.e3))
