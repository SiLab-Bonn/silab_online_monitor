from online_monitor.receiver.receiver import Receiver
import numpy as np
from PyQt5 import Qt
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from pyqtgraph.dockarea import DockArea, Dock

from online_monitor.utils import utils
n_fes=5

class ColorBar(pg.GraphicsObject):

    def __init__(self, cmap, width, height, ticks=None, tick_labels=None, label=None):
        pg.GraphicsObject.__init__(self)

        # handle args
        label = label or ''
        w, h = width, height
        stops, colors = cmap.getStops('float')
        smn, spp = stops.min(), stops.ptp()
        stops = (stops - stops.min())/stops.ptp()
        if ticks is None:
            ticks = np.r_[0.0:1.0:2j, 1.0] * spp + smn
        tick_labels = tick_labels or ["%0.2g" % (t,) for t in ticks]

        # setup picture
        self.pic = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.pic)

        # draw bar with gradient following colormap
        p.setPen(pg.mkPen('k'))
        grad = pg.QtGui.QLinearGradient(w/2.0, 0.0, w/2.0, h*1.0)
        for stop, color in zip(stops, colors):
            grad.setColorAt(1.0 - stop, pg.QtGui.QColor(*[255*c for c in color]))
        p.setBrush(pg.QtGui.QBrush(grad))
        p.drawRect(pg.QtCore.QRectF(0, 0, w, h))

        # draw ticks & tick labels
        mintx = 0.0
        for tick, tick_label in zip(ticks, tick_labels):
            y_ = (1.0 - (tick - smn)/spp) * h
            p.drawLine(0.0, y_, -5.0, y_)
            br = p.boundingRect(0, 0, 0, 0, pg.QtCore.Qt.AlignLeft, tick_label)
            if br.x() < mintx:
                mintx = br.x()
            p.drawText(br.x() - 8.0, y_ + br.height() / 30.0, tick_label)

        # draw label
        br = p.boundingRect(0, 0, 0, 0, pg.QtCore.Qt.AlignLeft, label)
        p.drawText(-br.width() / 10.0, h + br.height() + 5.0, label)
        
        # done
        p.end()

        # compute rect bounds for underlying mask
        self.zone = mintx - 12.0, -15.0, br.width() - mintx, h + br.height() + 30.0
        
    def paint(self, p, *args):
        # paint underlying mask
        p.setPen(pg.QtGui.QColor(255, 255, 255, 0))
        p.setBrush(pg.QtGui.QColor(255, 255, 255, 200))
        p.drawRoundedRect(*(self.zone + (0.9, 9.0)))
        
        # paint colorbar
        p.drawPicture(0, 50, self.pic)
        
    def boundingRect(self):
        return pg.QtCore.QRectF(self.pic.boundingRect())
    
    
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

        lut = cm.getLookupTable(0.0, 1.0, 50)
        self.occupancy_img.setLookupTable(lut, update=True)
         
        plot = pg.PlotWidget(viewBox=view,labels={'bottom':'Column','left':'Row'}, )  # Axis Labelling
        cb = ColorBar(cm, 3, 250, tick_labels=('min','max'), label='#')
        cb.translate(410.0, 5.0)
        plot.addItem(self.occupancy_img)
        dock_occcupancy.addWidget(plot)

       
        hitrate_plot=pg.PlotWidget(labels={'bottom':'Time (s)','left':'Hz'})
        hitrate_plot.plot()
        self.hit_curves=[]
        dock_hitrate.addWidget(hitrate_plot)
          
        for i in range(n_fes):
            c1 = pg.PlotCurveItem(pen=(i,n_fes))
            hitrate_plot.addItem(c1)
            self.hit_curves.append(c1)
        
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

    def deserialize_data(self, data):
        datar, meta  = utils.simple_dec(data)
        if 'occupancies' in meta:
            meta['occupancies'] = datar
        return meta

    def handle_data(self, data):
        self.occupancy_img.setImage(data['occupancies'], autoDownsample=True)
        self.rate_label.setText("Readout Rate\n%d Hz" % data['fps'])
        if self.spin_box.value() == 0:  # show number of hits, all hits are integrated
            self.hit_rate_label.setText("Hit Rate\n%d" % int(data['total_hits']))
        else:
            self.hit_rate_label.setText("Hit Rate\n%d Hz" % int(data['hps']))
        if self.spin_box.value() == 0:  # show number of events
            self.event_rate_label.setText("Event Rate\n%d" % int(data['total_events']))
        else:
            self.event_rate_label.setText("Event Rate\n%d Hz" % int(data['eps']))       
        for i in range(n_fes):
            self.hit_curves[i].setData(data['time'],data['hps_array'].T[i],autoDownsample=True )
            self.event_curves[i].setData(data['time'],data['eps_array'].T[i],autoDownsample=True )
