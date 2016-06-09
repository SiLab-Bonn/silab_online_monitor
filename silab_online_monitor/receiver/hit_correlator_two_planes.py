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
#         self.active_dut1 = 0
#         self.active_dut2 = 0
    def setup_widgets(self, parent, name):
        #
        self.occupancy_images_columns =  {}
        self.occupancy_images_rows = {}
        #
        DUTS = []
        #
        for dut_index in range(7):
            
            if dut_index == 0:
                DUTS.append('FE-I4')
            else:
                DUTS.append('MIMOSA%i' % dut_index)
        #        
        dock_area = DockArea()
        parent.addTab(dock_area, name)   
        #    
        dock_status = Dock("status")
        dock_status.setMaximumHeight(100)
        dock_select_duts = Dock("Select DUT's")
        dock_select_duts.setMinimumSize(500,100)
        dock_select_duts.setMaximumSize(800, 100)
        dock_corr_column = Dock('Column-correlation')
        dock_corr_column.setMinimumSize(500,500)
        dock_corr_row = Dock('Row-correlation') 
        dock_corr_row.setMinimumSize(500,500)
        #
        cb = QtGui.QWidget()
        layout0 = QtGui.QGridLayout()
        cb.setLayout(layout0)
        self.combobox1 = Qt.QComboBox()
        self.combobox1.addItems(DUTS)
        self.combobox1.setMinimumSize(175, 50)
        self.combobox2 = Qt.QComboBox()
        self.combobox2.addItems(DUTS)
        self.combobox2.setMinimumSize(175, 50)
        self.select_label = QtGui.QLabel('Correlate:')
        self.select_label1 = QtGui.QLabel('    to    ')
        self.start_button = QtGui.QPushButton('Start')
        layout0.addWidget(self.select_label, 0, 0, 0, 1)
        layout0.addWidget(self.combobox1, 0, 1, 0, 1)
        layout0.addWidget(self.select_label1, 0, 2, 0, 1)
        layout0.addWidget(self.combobox2, 0, 3, 0, 1)
        layout0.addWidget(self.start_button, 0, 4, 0, 1)
        dock_select_duts.addWidget(cb)
        self.combobox1.activated.connect(lambda value: self.send_command('combobox1 %d' % value))
        self.combobox2.activated.connect(lambda value: self.send_command('combobox2 %d' % value))
        self.start_button.clicked.connect(lambda value: self.send_command('START %d' % value))
        #
        cw = QtGui.QWidget()
        layout = QtGui.QGridLayout()
        cw.setLayout(layout)
        reset_button = QtGui.QPushButton('Reset')
        layout.addWidget(reset_button, 0, 0, 0, 1)
        noisy_checkbox = QtGui.QCheckBox('Mask noisy pixels')
        layout.addWidget(noisy_checkbox, 0, 1, 0, 1)
        dock_status.addWidget(cw)
        reset_button.clicked.connect(lambda: self.send_command('RESET'))
        noisy_checkbox.stateChanged.connect(lambda value: self.send_command('MASK %d' % value))
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
        dock_area.addDock(dock_select_duts, 'left')
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
    
#     def handle_command(self, command):
#         if 'combobox1'in command[0]:
#             self.active_dut1 = int(command[0].split()[1])
#         if 'combobox2'in command[0]:
#             self.active_dut2 = int(command[0].split()[1])          

