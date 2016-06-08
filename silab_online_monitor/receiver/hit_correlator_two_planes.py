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
from PyQt4.Qt import QWidget, QSize


class HitCorrelator(Receiver):

    def setup_receiver(self):
        self.set_bidirectional_communication()  # We want to change converter settings
        self.active_dut1 = 0
        self.active_dut2 = 0
    def setup_widgets(self, parent, name):
        
        self.occupancy_images_columns =  {}
        self.occupancy_images_rows = {}
        
        DUTS = []
        
        for dut_index in range(7):
            
            if dut_index == 0:
                DUTS.append('FE-I4')
            else:
                DUTS.append('MIMOSA%i' % dut_index)
                
        dock_area = DockArea()
        parent.addTab(dock_area, name)   
            
        dock_status = Dock("status")
        dock_status.setMaximumHeight(100)
        dock_select_dut1 = Dock("Select DUT1")
        dock_select_dut1.setMaximumHeight(100)
        dock_select_dut2 = Dock("Select DUT2")
        dock_select_dut2.setMaximumHeight(100)
        dock_corr_column = Dock('Column-correlation')
        dock_corr_column.setMinimumSize(500,500)
        dock_corr_row = Dock('Row-correlation') 
        dock_corr_row.setMinimumSize(500,500)
        
        self.combobox1 = Qt.QComboBox()
        self.combobox1.addItems(DUTS)
        layout1 = QtGui.QGridLayout()
        self.combobox1.setMaximumSize(200, 50)
        self.combobox1.setLayout(layout1)
        dock_select_dut1.addWidget(self.combobox1)
        self.combobox1.activated.connect(lambda value: self.send_command('combobox1 %d' % value))
        #
        self.combobox2 = Qt.QComboBox()
        self.combobox2.addItems(DUTS)
        layout2 = QtGui.QGridLayout()
        self.combobox2.setMaximumSize(200, 50)
        self.combobox2.setLayout(layout2)
        dock_select_dut2.addWidget(self.combobox2)
        self.combobox2.activated.connect(lambda value: self.send_command('combobox2 %d' % value))
        #
        cw = QtGui.QWidget()
        cw.setStyleSheet("QWidget {background-color:white}")
        layout = QtGui.QGridLayout()
        cw.setLayout(layout)
        reset_button = QtGui.QPushButton('Reset')
        layout.addWidget(reset_button, 0, 0, 0, 1)
        dock_status.addWidget(cw)
        reset_button.clicked.connect(lambda: self.send_command('RESET'))
        #
        #Add plot docks for column corr
        occupancy_graphics = pg.GraphicsLayoutWidget()
        occupancy_graphics.show()
        view = occupancy_graphics.addViewBox()
        occupancy_img_col = pg.ImageItem(border='w')
        view.addItem(occupancy_img_col)
        view.setRange(QtCore.QRectF(0, 0, self.config['max_n_columns_m26'], self.config['max_n_columns_m26'])) 
        dock_corr_column.addWidget(occupancy_graphics)
        self.occupancy_images_columns = occupancy_img_col
        #Add plot docks for row corr
        occupancy_graphics = pg.GraphicsLayoutWidget()
        occupancy_graphics.show()
        view = occupancy_graphics.addViewBox()
        occupancy_images_rows = pg.ImageItem(border='w')
        view.addItem(occupancy_images_rows)
        view.setRange(QtCore.QRectF(0, 0, self.config['max_n_rows_m26'], self.config['max_n_rows_m26'])) 
        dock_corr_row.addWidget(occupancy_graphics)
        self.occupancy_images_rows = occupancy_images_rows  
        
        #
        dock_area.addDock(dock_status, 'top')
        dock_area.addDock(dock_select_dut1, 'left')
        dock_area.addDock(dock_select_dut2, 'right', dock_select_dut1)
        dock_area.addDock(dock_corr_column, 'bottom')
        dock_area.addDock(dock_corr_row, 'right', dock_corr_column)


    def deserialze_data(self, data):
        return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)
    
    def handle_data(self, data):
        if 'meta_data' not in data:
            for key in data:
                if 'column' == key:
                    self.occupancy_images_columns.setImage(data[key][:,:], autoDownsample=True)
                if 'row' == key:
                    self.occupancy_images_rows.setImage(data[key][:,:], autoDownsample=True)
    
    def handle_command(self, command):
        if 'combobox1'in command[0]:
            self.active_dut1 = int(command[0].split()[1])
        if 'combobox2'in command[0]:
            self.active_dut2 = int(command[0].split()[1])          

