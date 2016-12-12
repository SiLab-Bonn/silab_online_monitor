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
        dock_status_m26 = Dock("Mimosaxis_current6 Status")
        dock_status_fei4 = Dock("FE-I4 Status")
        dock_status_m26.setMaximumHeight(200)
        dock_status_fei4.setMaximumHeight(200)
        status_widget_m26 = QtGui.QWidget()
        status_widget_fei4 = QtGui.QWidget()
        status_layout_m26 = QtGui.QGridLayout()
        status_layout_fei4 = QtGui.QGridLayout()
        status_widget_m26.setLayout(status_layout_m26)
        status_widget_fei4.setLayout(status_layout_fei4)
        self.reset_m26 = QtGui.QPushButton('Reset')
        self.reset_fei4 = QtGui.QPushButton('Reset')
        self.reset_m26.setMaximumSize(150,50)
        self.reset_fei4.setMaximumSize(150,50)
        status_layout_m26.addWidget(self.reset_m26, 0,0,0,1)
        status_layout_fei4.addWidget(self.reset_fei4, 0,0,0,1)
        dock_status_m26.addWidget(status_widget_m26)
        dock_status_fei4.addWidget(status_widget_fei4)
        
        # add dock for Mimosaxis_current6 power supply
        dock_m26 = Dock("Mimosaxis_current6 power supply")
        # add plot with two axes for volatge and current
        plot_graphics = pg.GraphicsView()
        plot_graphics.show()
        axis_current = pg.AxisItem("left")
        view_current = pg.ViewBox()
        plot_layout = pg.GraphicsLayout()
        plot_graphics.setCentralWidget(plot_layout)
        plot_layout.addItem(axis_current, row = 2, col = 5,  rowspan=1, colspan=1)
        plot_item = pg.PlotItem()
        plot_item.showGrid(x=True,y=True,alpha=0.15)
        view_voltage = plot_item.vb # reference to viewbox of the plotitem
        plot_layout.addItem(plot_item, row = 2, col = 6,  rowspan=1, colspan=1) # add plotitem to layout
        plot_layout.scene().addItem(view_current)
        #view_current.disableAutoRange(axis=view_current.YAxis)
        axis_current.linkToView(view_current)
        view_current.setXLink(view_voltage)
        plot_item.getAxis("left").setLabel('Voltage / V')
        plot_item.getAxis("bottom").setLabel('Time / s')
        plot_item.setYRange(2,10, padding=0)
        axis_current.setLabel('Current / mA')
        dock_m26.addWidget(plot_graphics)
        # update view
        def update_views():
            view_current.setGeometry(view_voltage.sceneBoundingRect())
        view_voltage.sigResized.connect(update_views)
        view_current.enableAutoRange(axis= pg.ViewBox.XYAxes, enable=True)
        # add dock for FE-I4 power supply
        dock_fei4 = Dock("FE-I4 power supply")
        self.fei4_plot_v = pg.PlotWidget(background='w', labels={'left': 'Voltage / V', 'bottom': 'Time / s'})
        self.fei4_plot_c = pg.PlotWidget(background='w', labels={'left': 'Current / mA', 'bottom': 'Time / s'})
        self.fei4_plot_v.addLegend(offset=(20,20))
        self.fei4_plot_c.addLegend(offset=(20,20))
        self.fei4_plot_v.setXRange(0, 60)
        self.fei4_plot_v.setYRange(0,2,padding=0)
        self.fei4_plot_c.showGrid(x=True,y=True,alpha=0.15)
        self.fei4_plot_v.showGrid(x=True,y=True,alpha=0.15)
        self.fei4_plot_c.setXRange(0, 60)
        self.fei4_plot_c.setYRange(60,120,padding=0)
        dock_fei4.addWidget(self.fei4_plot_v)
        dock_fei4.addWidget(self.fei4_plot_c)

        # add Docks to DockArea
        dock_area.addDock(dock_status_m26, 'top')
        dock_area.addDock(dock_status_fei4, 'right', dock_status_m26)
        dock_area.addDock(dock_m26, 'bottom', dock_status_m26)
        dock_area.addDock(dock_fei4, 'bottom', dock_status_fei4)
        
        # test data for plots
        test_vdda = np.random.uniform(low=1.495, high=1.505, size=60)
        test_vddd = np.random.uniform(low=1.195, high=1.205, size=60)
        test_vddd_c = np.random.uniform(low=84.5, high=85.0, size=60)
        test_vdda_c = np.random.uniform(low=99.5, high=100.0, size=60)
        test_mimosa_v = np.random.uniform(low=7.95,high=8.0, size=60)
        test_mimosa_i = np.random.uniform(low=74.5,high=75.0, size=60)
        # test plots
        self.fei4_plot_v.plot(test_vdda, name='VDDA', pen='r', lw=4)
        self.fei4_plot_v.plot(test_vddd, name='VDDD', pen='g',lw=4)
        self.fei4_plot_c.plot(test_vdda_c, name='VDDA_current', pen='r')
        self.fei4_plot_c.plot(test_vddd_c, name='VDDD_current', pen='g')
        view_voltage.addItem(pg.PlotCurveItem(test_mimosa_v, pen='r'))
        view_current.addItem(pg.PlotCurveItem(test_mimosa_i, pen='k'))
                
    def deserialze_data(self, data):
        return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)
        
    def handle_data(self, data):
        return
        
