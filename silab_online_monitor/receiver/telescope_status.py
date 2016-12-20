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
from PyQt5.Qt import QWidget, QSize


class TelescopeStatus(Receiver):

    def setup_receiver(self):
        self.set_bidirectional_communication()  # We want to change converter settings

    def setup_widgets(self, parent, name):
        
        # add status tab to online monitor
        dock_area = DockArea()
        parent.addTab(dock_area, name)
        parent.currentChanged.connect(lambda value: self.send_command('ACTIVETAB %s' % str(parent.tabText(value))))  # send active tab index to converter so that it only does something when user is looking at corresponding receiver
        
        # add status dock with widgets
        dock_status_m26 = Dock("Mimosa Status")
        dock_status_fei4 = Dock("FE-I4 Status")
        
        # get screen dimensions for dynamic dock width
        screen = QtGui.QDesktopWidget().screenGeometry()
        dock_status_m26.setMaximumSize(screen.width()/2,200)
        dock_status_fei4.setMaximumSize(screen.width()/2,200)
        
        # add layout widgets
        status_widget_m26 = QtGui.QWidget()
        status_widget_fei4 = QtGui.QWidget()
        status_layout_m26 = QtGui.QGridLayout()
        status_layout_fei4 = QtGui.QGridLayout()
        status_widget_m26.setLayout(status_layout_m26)
        status_widget_fei4.setLayout(status_layout_fei4)
        
        # add buttons etc. to fei4 dock
        self.reset_fei4_vdda = QtGui.QPushButton('Reset VDDA c/v')
        self.reset_fei4_vddd = QtGui.QPushButton('Reset VDDD c/v')
        self.reset_fei4_vdda.setMinimumSize(100,50)
        self.reset_fei4_vddd.setMinimumSize(100,50)
        self.reset_fei4_vdda.setMaximumSize(150,50)
        self.reset_fei4_vddd.setMaximumSize(150,50)
        self.current_vdda_v = QtGui.QLCDNumber()
        self.current_vddd_v = QtGui.QLCDNumber()
        self.current_vdda_c = QtGui.QLCDNumber()
        self.current_vddd_c = QtGui.QLCDNumber()
        self.current_vdda_v.setDecMode()
        self.current_vddd_v.setDecMode()
        self.current_vdda_v.setNumDigits(5)
        self.current_vddd_v.setNumDigits(5)
        self.current_vdda_c.setDecMode()
        self.current_vddd_c.setDecMode()
        self.current_vdda_c.setNumDigits(5)
        self.current_vddd_c.setNumDigits(5)
        self.current_vdda_v.setMaximumSize(150,50)
        self.current_vddd_v.setMaximumSize(150,50)
        self.current_vdda_c.setMaximumSize(150,50)
        self.current_vddd_c.setMaximumSize(150,50)
        self.current_vdda_v.setMinimumSize(100,50)
        self.current_vddd_v.setMinimumSize(100,50)
        self.current_vdda_c.setMinimumSize(100,50)
        self.current_vddd_c.setMinimumSize(100,50)
        vddd_label = QtGui.QLabel('VDDD:')
        vdda_label = QtGui.QLabel('VDDA:')
        vdda_label.setMinimumSize(75,35)
        vddd_label.setMinimumSize(75,35)
        vdda_label.setMaximumSize(100,50)
        vddd_label.setMaximumSize(100,50)
        vdda_label.setFont(QtGui.QFont('System', 16))
        vddd_label.setFont(QtGui.QFont('System', 16))
        vddd_label_v = QtGui.QLabel('V ;')
        vdda_label_v = QtGui.QLabel('V ;')
        vdda_label_v.setMinimumSize(15,50)
        vddd_label_v.setMinimumSize(15,50)
        vdda_label_v.setMaximumSize(50,50)
        vddd_label_v.setMaximumSize(50,50)
        vdda_label_v.setFont(QtGui.QFont('System', 12))
        vddd_label_v.setFont(QtGui.QFont('System', 12))
        vddd_label_c = QtGui.QLabel('mA')
        vdda_label_c = QtGui.QLabel('mA')
        vdda_label_c.setMinimumSize(30,50)
        vddd_label_c.setMinimumSize(30,50)
        vdda_label_c.setMaximumSize(50,50)
        vddd_label_c.setMaximumSize(50,50)
        vdda_label_c.setFont(QtGui.QFont('System', 12))
        vddd_label_c.setFont(QtGui.QFont('System', 12))
        status_layout_fei4.addWidget(self.reset_fei4_vdda, 0,0,1,1)
        status_layout_fei4.addWidget(self.reset_fei4_vddd, 1,0,1,1)
        status_layout_fei4.addWidget(vdda_label, 0,1,1,1)
        status_layout_fei4.addWidget(vddd_label, 1,1,1,1)
        status_layout_fei4.addWidget(self.current_vdda_v, 0,2,1,1)
        status_layout_fei4.addWidget(self.current_vddd_v, 1,2,1,1)
        status_layout_fei4.addWidget(vdda_label_v, 0,3,1,1)
        status_layout_fei4.addWidget(vddd_label_v, 1,3,1,1)
        status_layout_fei4.addWidget(self.current_vdda_c, 0,4,1,1)
        status_layout_fei4.addWidget(self.current_vddd_c, 1,4,1,1)
        status_layout_fei4.addWidget(vdda_label_c, 0,5,1,1)
        status_layout_fei4.addWidget(vddd_label_c, 1,5,1,1)
        
        # add buttons etc. to m26 dock
        self.reset_m26_c = QtGui.QPushButton('Reset current')
        self.reset_m26_v = QtGui.QPushButton('Reset voltage')
        self.reset_m26_c.setMinimumSize(100,50)
        self.reset_m26_v.setMinimumSize(100,50)
        self.reset_m26_c.setMaximumSize(150,50)
        self.reset_m26_v.setMaximumSize(150,50)
        self.current_m26_c = QtGui.QLCDNumber()
        self.current_m26_v = QtGui.QLCDNumber()
        self.current_m26_c.setDecMode()
        self.current_m26_v.setDecMode()
        self.current_m26_v.setNumDigits(5)
        self.current_m26_c.setNumDigits(5)
        self.current_m26_c.setMaximumSize(150,50)
        self.current_m26_v.setMaximumSize(150,50)
        self.current_m26_c.setMinimumSize(100,50)
        self.current_m26_v.setMinimumSize(100,50)
        m26_label_c = QtGui.QLabel('Current:')
        m26_label_v = QtGui.QLabel('Voltage:')
        m26_label_c.setMinimumSize(75,35)
        m26_label_v.setMinimumSize(75,35)
        m26_label_c.setMaximumSize(100,50)
        m26_label_v.setMaximumSize(100,50)
        m26_label_c.setFont(QtGui.QFont('System', 16))
        m26_label_v.setFont(QtGui.QFont('System', 16))
        c_label_m26 = QtGui.QLabel('mA')
        v_label_m26 = QtGui.QLabel('V')
        c_label_m26.setMinimumSize(30,50)
        v_label_m26.setMinimumSize(30,50)
        c_label_m26.setMaximumSize(50,50)
        v_label_m26.setMaximumSize(50,50)
        c_label_m26.setFont(QtGui.QFont('System', 12))
        v_label_m26.setFont(QtGui.QFont('System', 12))
        status_layout_m26.addWidget(self.reset_m26_c, 0,0,1,1)
        status_layout_m26.addWidget(self.reset_m26_v, 1,0,1,1)
        status_layout_m26.addWidget(m26_label_c, 0,2,1,1)
        status_layout_m26.addWidget(m26_label_v, 1,2,1,1)
        status_layout_m26.addWidget(self.current_m26_c, 0,3,1,1)
        status_layout_m26.addWidget(self.current_m26_v, 1,3,1,1)
        status_layout_m26.addWidget(c_label_m26, 0,4,1,1)
        status_layout_m26.addWidget(v_label_m26, 1,4,1,1)
        
        # add buttons etc to layout widgets and to docks
        dock_status_m26.addWidget(status_widget_m26)
        dock_status_fei4.addWidget(status_widget_fei4)
        
        # connect reset buttons
        self.reset_m26_c.clicked.connect(lambda: self.send_command('RESET_M26_CURRENT'))
        self.reset_m26_v.clicked.connect(lambda: self.send_command('RESET_M26_VOLTAGE'))
        self.reset_fei4_vdda.clicked.connect(lambda: self.send_command('RESET_FEI4_VDDA'))
        self.reset_fei4_vddd.clicked.connect(lambda: self.send_command('RESET_FEI4_VDDD'))
        
        # add dock for Mimosa power supply
        dock_m26 = Dock("Mimosa power supply")
        
        # add plot with two axes for volatge and current
        plot_graphics_m26 = pg.GraphicsView()
        plot_graphics_m26.show()
        plot_layout = pg.GraphicsLayout()
        plot_graphics_m26.setCentralWidget(plot_layout)
        axis_current = pg.AxisItem("left")
        plot_layout.addItem(axis_current, row = 2, col = 5,  rowspan=1, colspan=1)
        view_current = pg.ViewBox()
        self.plot_current = pg.PlotItem(viewBox=view_current)
        view_voltage = pg.ViewBox()
        self.plot_voltage = pg.PlotItem(viewBox=view_voltage)
        plot_layout.addItem(self.plot_voltage, row = 2, col = 6,  rowspan=1, colspan=1) # add plotitem to layout
        plot_layout.scene().addItem(view_current)
        view_current.disableAutoRange(axis=view_current.YAxis)
        axis_current.linkToView(view_current)
        view_current.setXLink(view_voltage)
        view_current.setBackgroundColor('#545454')
        self.plot_voltage.getAxis("left").setLabel('Voltage / V')
        self.plot_voltage.getAxis("bottom").setLabel('Time / s')
        self.plot_voltage.addLegend(offset=(20,20))
        self.plot_current.addLegend(offset=(120,20))
        voltage_pen = QtGui.QPen()
        voltage_pen.setStyle(QtCore.Qt.SolidLine)
        voltage_pen.setWidthF(1)
        current_pen = QtGui.QPen()
        current_pen.setStyle(QtCore.Qt.DashLine)
        current_pen.setWidthF(1)
        self.plot_voltage.getAxis('left').setPen(voltage_pen)
        self.plot_voltage.getAxis('left').setGrid(155)
        axis_current.setPen(current_pen)
        axis_current.setGrid(155)
        view_voltage.setLimits(minYRange=1)
        view_current.setLimits(minYRange=10)
        axis_current.setLabel('Current / mA')
        dock_m26.addWidget(plot_graphics_m26)
        
        # update view
        def update_views():
            view_current.setGeometry(view_voltage.sceneBoundingRect())
        
        # update view when viewbox was scaled
        view_voltage.sigResized.connect(update_views)
        view_current.enableAutoRange(axis= pg.ViewBox.XYAxes, enable=True)
        
        # add dock for FE-I4 power supply
        dock_fei4 = Dock("FE-I4 power supply")
        plot_graphics_fei4 = pg.GraphicsLayoutWidget()
        plot_graphics_fei4.show()
        self.fei4_plot_v = pg.PlotItem(labels={'left': 'Voltage / V', 'bottom': 'Time / s'})
        self.fei4_plot_c = pg.PlotItem(labels={'left': 'Current / mA', 'bottom': 'Time / s'})
        self.fei4_plot_v.vb.setBackgroundColor('#545454')
        self.fei4_plot_c.vb.setBackgroundColor('#545454')
        self.fei4_plot_v.addLegend(offset=(20,20))
        self.fei4_plot_c.addLegend(offset=(20,20))
        self.fei4_plot_v.setXRange(0, 60)
        self.fei4_plot_v.setYRange(0,2,padding=0)
        self.fei4_plot_c.setXRange(0, 60)
        self.fei4_plot_c.setYRange(60,120,padding=0)
        self.fei4_plot_v.getAxis('left').setZValue(0)
        self.fei4_plot_c.getAxis('left').setZValue(0)
        self.fei4_plot_v.getAxis('left').setGrid(155)
        self.fei4_plot_c.getAxis('left').setGrid(155)
        plot_graphics_fei4.addItem(self.fei4_plot_v, row = 0, col = 1,  rowspan=1, colspan=2)
        plot_graphics_fei4.addItem(self.fei4_plot_c, row = 1, col = 1,  rowspan=1, colspan=2)
        dock_fei4.addWidget(plot_graphics_fei4)
        #dock_fei4.addWidget(self.fei4_plot_c)

        # add Docks to DockArea
        dock_area.addDock(dock_status_m26, 'top')
        dock_area.addDock(dock_status_fei4, 'right', dock_status_m26)
        dock_area.addDock(dock_m26, 'bottom', dock_status_m26)
        dock_area.addDock(dock_fei4, 'bottom', dock_status_fei4)
        
        # display values for testing
        self.current_vdda_v.display(np.random.uniform(1.5,1.55))
        self.current_vddd_v.display(np.random.uniform(1.2,1.25))
        self.current_vdda_c.display(np.random.uniform(100,100.5))
        self.current_vddd_c.display(np.random.uniform(110,110.5))
        self.current_m26_c.display(np.random.uniform(100,100.5))
        self.current_m26_v.display(np.random.uniform(8.0,8.05))
        
        # make test data
        test_vdda = np.random.uniform(low=1.495, high=1.505, size=60)
        test_vddd = np.random.uniform(low=1.195, high=1.205, size=60)
        test_vddd_c = np.random.uniform(low=84.5, high=85.0, size=60)
        test_vdda_c = np.random.uniform(low=99.5, high=100.0, size=60)
        test_mimosa_v = np.random.uniform(low=7.95,high=8.0, size=60)
        test_mimosa_i = np.random.uniform(low=74.5,high=75.0, size=60)
        
        # test plots
        self.fei4_plot_v.plot(test_vdda, pen='r', name='VDDA')
        self.fei4_plot_v.plot(test_vddd, pen='g', name='VDDD')
        self.fei4_plot_c.plot(test_vdda_c, pen='r', name='VDDA_current')
        self.fei4_plot_c.plot(test_vddd_c, pen='g', name='VDDD_current')
        #voltage_plot_pen = QtGui.QPen()
        #voltage_plot_pen.setStyle(QtCore.Qt.DashLine)
        #voltage_plot_pen.setWidthF(0.005)
        #voltage_plot_pen.setColor(QtGui.QColor('red'))
        self.plot_voltage.plot(test_mimosa_v, pen='r', name="Voltage")
        self.plot_current.plot(test_mimosa_i, pen='g', name="Current")
        
                
    def deserialze_data(self, data):
        return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)
        
    def handle_data(self, data):
        #~ status_data = np.zeros(shape=(10), dtype=[('m26_voltage','f8'),('m26_current','f8'),('vdda_v','f8'),('vdda_c','f8'),('vddd_v','f8'),('vddd_c','f8')])
        #~ for name in status_data.dtype.names:
            #~ print name
            #~ status_data[name] = np.random.uniform(low=1.0,high=8.0, size=status_data.shape[0])
            
        #~ self.fei4_plot_v.plot(status_data['vdda_v'], pen='r', name='VDDA')
        #~ self.fei4_plot_v.plot(status_data['vddd_v'], pen='g', name='VDDD')
        #~ self.fei4_plot_c.plot(status_data['vdda_c'], pen='r', name='VDDA_current')
        #~ self.fei4_plot_c.plot(status_data['vddd_c'], pen='g', name='VDDD_current')
        #~ self.plot_voltage.plot(status_data['m26_voltage'], pen='r', name="Voltage")
        #~ self.plot_current.plot(status_data['m26_current'], pen='g', name="Current")
        return
