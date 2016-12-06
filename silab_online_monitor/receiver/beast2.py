from online_monitor.receiver.receiver import Receiver
from zmq.utils import jsonapi
import numpy as np
import time
from PyQt5 import Qt
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.ptime as ptime
from pyqtgraph.dockarea import DockArea, Dock
from Colorbar import ColorBar

from online_monitor.utils import utils
n_fes=5
    
    
class Beast(Receiver):

    def setup_receiver(self):
        self.set_bidirectional_communication()  # We want to change converter settings

    def setup_widgets(self, parent, name):
        dock_area = DockArea()
        parent.addTab(dock_area, name)
        
        # Docks
        dock_status = Dock("Status", size=(800, 40))
        dock_area.addDock(dock_status, 'top')
        
        dock_hitrate = Dock("Hit_Rate", size=(400, 400))                 #For Hit Rate
        dock_area.addDock(dock_hitrate, 'bottom', dock_status)
        
        dock_eventrate = Dock("Event_Rate", size=(400, 400))             #For event rate 
        dock_area.addDock(dock_eventrate, 'bottom', dock_status)
         
        dock_occcupancy = Dock("Occupancy_Stave", size=(400, 400))       #For Hit Maps of all front-ends
        dock_area.addDock(dock_occcupancy, 'bottom', dock_status)
        

        # Different plot docks                               
        occupancy_graphics = pg.GraphicsLayoutWidget()
        occupancy_graphics.show()
        
        view = occupancy_graphics.addViewBox()
        self.occupancy_img = pg.ImageItem(border='w')
        stops = np.r_[0.0, 1.0] 
        colors = np.array([[0,1.0,1.0,1.0],[1.0,0.0,1.0,1.0]])
        cm = pg.ColorMap(stops, colors)
# make colorbar, placing by hand

        lut = cm.getLookupTable(0.0, 1.0, 100)
        self.occupancy_img.setLookupTable(lut, update=True)
         
        plot = pg.PlotWidget(viewBox=view,labels={'bottom':'Column','left':'Row'}, )      #Axis Labelling
        cb = ColorBar(cm, 10, 180, tick_labels=('min','max'), label='#')#, [0., 0.5, 1.0])
        plot.scene().addItem(cb)
        cb.translate(1637.0, 0.0)
        plot.addItem(self.occupancy_img)
        dock_occcupancy.addWidget(plot)

       
        hitrate_plot=pg.PlotWidget(labels={'bottom':'Time (s)','left':'Hz'})
        hitrate_plot.plot()
#         l = pg.LegendItem((100,60), offset=(70,30))
#         l.setParentItem(hitrate_plot.graphicsItem())
        self.hit_curves=[]
        dock_hitrate.addWidget(hitrate_plot)
          
        for i in range(n_fes):
            c1 = pg.PlotCurveItem(pen=(i,n_fes))
            hitrate_plot.addItem(c1)
            self.hit_curves.append(c1)
#            l.addItem(c1, 'module')
#        print("self.hit_curves", len(self.hit_curves))
        
        eventrate_plot = pg.PlotWidget(labels={'bottom':'Time (s)','left':'Hz'}) 
        eventrate_plot.plot()
        self.event_curves=[]
        dock_eventrate.addWidget(eventrate_plot) 
        
        for i in range(n_fes):
            c2 = pg.PlotCurveItem(pen=(i,n_fes))
            eventrate_plot.addItem(c2)
            self.event_curves.append(c2)
        
#         Status dock on top
        cw = QtGui.QWidget()
        cw.setStyleSheet("QWidget {background-color:white}")
        layout = QtGui.QGridLayout()
        cw.setLayout(layout)
        self.rate_label = QtGui.QLabel("Readout Rate\n0 KHz")
        self.hit_rate_label = QtGui.QLabel("Hit Rate\n0 KHz")
        self.event_rate_label = QtGui.QLabel("Event Rate\n0 KHz")
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

        self.plot_delay = 0

    def deserialze_data(self, data):
        datar, meta  = utils.simple_dec(data)
        if 'occupancies' in meta:
            meta['occupancies'] = datar
        return meta

    def handle_data(self, data):
        self.occupancy_img.setImage(data['occupancies'], autoDownsample=True)
        self.rate_label.setText("Readout Rate\n%d Hz" % data['fps'])
#         self.hit_rate_label.setText("Hit Rate\n%d KHz" % int(data['hps']))
#         self.event_rate_label.setText("Event Rate\n%d KHz" % int(data['eps'])) 
        if self.spin_box.value() == 0:  # show number of hits, all hits are integrated
            self.hit_rate_label.setText("Total Hits\n%d" % int(data['total_hits']))
        else:
            self.hit_rate_label.setText("Hit Rate\n%d Hz" % int(data['hps']))
        if self.spin_box.value() == 0:  # show number of events
            self.event_rate_label.setText("Total Events\n%d" % int(data['total_events']))
        else:
            self.event_rate_label.setText("Event Rate\n%d Hz" % int(data['eps']))       
#         print("data[hps_array] ", data['hps_array'].shape)
        for i in range(n_fes):
#             pass
            self.hit_curves[i].setData(data['time'],data['hps_array'].T[i],autoDownsample=True )
            self.event_curves[i].setData(data['time'],data['eps_array'].T[i],autoDownsample=True )
        
#         self.timestamp_label.setText("Data Timestamp\n%s" % time.asctime(time.localtime(data['time_stamp'])))
#         self.scan_parameter_label.setText("Scan Parameters\n%s" % ', '.join('%s: %s' % (str(key), str(val)) for key, val in data['meta_data']['scan_parameters'].iteritems()))
#         now = ptime.time()
#         self.plot_delay = self.plot_delay * 0.9 + (now - data['time_stamp']) * 0.1
#         self.plot_delay_label.setText("Plot Delay\n%s" % 'not realtime' if abs(self.plot_delay) > 5 else "%1.2f ms" % (self.plot_delay * 1.e3))       
