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


class HitCorrelator(Receiver):

    def setup_receiver(self):
        self.set_bidirectional_communication()  # We want to change converter settings

    def setup_widgets(self, parent, name):
        
        self.tab_widget = Qt.QTabWidget()
        parent.addTab(self.tab_widget, name)
        
        self.occupancy_images_columns = {}
        self.occupancy_images_rows = {}
        
        for dut_index in range(7):#len(self.config['devices'])):
            if dut_index==0:
                dock_area = DockArea()
                dock_status = Dock("status", size=(100, 10))
                self.tab_widget.addTab(dock_area, 'FEI4')
                #creating reset button in status dock
                cw = QtGui.QWidget()
                cw.setStyleSheet("QWidget {background-color:white}")
                layout = QtGui.QGridLayout()
                cw.setLayout(layout)
                self.reset_button = QtGui.QPushButton('Reset')
                layout.addWidget(self.reset_button, 0, 7, 0, 1)
                dock_status.addWidget(cw)
                
                for i in range(1,7):
                    dock_corr_column=Dock("Cols FEI4 to M26 %d" % i, size=(50, 50))# % dut_index+1 #, size=(400, 400))
                    dock_corr_row=Dock("Rows FEI4 to M26 %d" % i, size=(50, 50))  
                
                    dock_area.addDock(dock_status, 'top')
                    dock_area.addDock(dock_corr_column)
                    dock_area.addDock(dock_corr_row, 'right', dock_corr_column) 
                
            else:
                dock_area = DockArea()
                dock_status = Dock("status", size=(100, 10))
                self.tab_widget.addTab(dock_area, 'MIMOSA%d' % dut_index)
                #creating reset button in status dock
                cw = QtGui.QWidget()
                cw.setStyleSheet("QWidget {background-color:white}")
                layout = QtGui.QGridLayout()
                cw.setLayout(layout)
                self.reset_button = QtGui.QPushButton('Reset')
                layout.addWidget(self.reset_button, 0, 7, 0, 1)
                dock_status.addWidget(cw)
                
                for i in range(1,7):
                    if i==dut_index:
                        continue
                    else:
                        
                        dock_corr_column=Dock("Cols M26 %d - %d" % (dut_index , i), size=(50, 50))# % dut_index+1 #, size=(400, 400))
                        dock_corr_row=Dock("Rows M26 %d - %d" % (dut_index , i), size=(50, 50))  
                
                        dock_area.addDock(dock_status, 'top')
                        dock_area.addDock(dock_corr_column)
                        dock_area.addDock(dock_corr_row, 'right', dock_corr_column) 
                        #Add plot docks for column corr
                        occupancy_graphics = pg.GraphicsLayoutWidget()
                        occupancy_graphics.show()
                        view = occupancy_graphics.addViewBox()
                        occupancy_img_col = pg.ImageItem(border='w')
                        view.addItem(occupancy_img_col)
                        view.setRange(QtCore.QRectF(0, 0, self.config['max_n_columns_m26'], self.config['max_n_columns_m26'])) 
                        dock_corr_column.addWidget(occupancy_graphics)
                        self.occupancy_images_columns[dut_index] = occupancy_img_col
                        #Add plot docks for row corr
                        occupancy_graphics = pg.GraphicsLayoutWidget()
                        occupancy_graphics.show()
                        view = occupancy_graphics.addViewBox()
                        occupancy_images_rows = pg.ImageItem(border='w')
                        view.addItem(occupancy_images_rows)
                        view.setRange(QtCore.QRectF(0, 0, self.config['max_n_rows_m26'], self.config['max_n_rows_m26'])) 
                        dock_corr_row.addWidget(occupancy_graphics)
                        self.occupancy_images_rows[dut_index] = occupancy_images_rows
                        
        self.tab_widget.currentChanged.connect(lambda value: self.send_command(str(value)))
        self.reset_button.clicked.connect(lambda: self.send_command('RESET'))
        #self.spin_box.valueChanged.connect(lambda value: self.send_command(str(value)))
        
        
#         
#         dock_area.addDock(dock_status, 'top')
#         dock_area.addDock(dock_corr_column, 'bottom', dock_status)
#         dock_area.addDock(dock_corr_row, 'right', dock_corr_column)
# 
#         # Status dock on top
#         cw = QtGui.QWidget()
#         cw.setStyleSheet("QWidget {background-color:white}")
#         layout = QtGui.QGridLayout()
#         cw.setLayout(layout)
#         self.spin_box = Qt.QSpinBox(value=0)
#         self.spin_box.setMaximum(1000000)
#         self.spin_box.setSuffix(" Readouts")
#         self.reset_button = QtGui.QPushButton('Reset')
#         layout.addWidget(self.spin_box, 0, 6, 0, 1)
#         layout.addWidget(self.reset_button, 0, 7, 0, 1)
#         dock_status.addWidget(cw)
# 
#         # Connect widgets
#         self.reset_button.clicked.connect(lambda: self.send_command('RESET'))
#         
#         
#         
# 
#         # Different plot docks
#         occupancy_graphics = pg.GraphicsLayoutWidget()
#         occupancy_graphics.show()
#         view = occupancy_graphics.addViewBox()
#         self.occupancy_img_col = pg.ImageItem(border='w')
#         view.addItem(self.occupancy_img_col)
#         view.setRange(QtCore.QRectF(0, 0, 80, 80)) 
#         dock_corr_column.addWidget(occupancy_graphics)
#        
#         # Different plot docks
#         occupancy_graphics = pg.GraphicsLayoutWidget()
#         occupancy_graphics.show()
#         view = occupancy_graphics.addViewBox()
#         self.occupancy_img_row = pg.ImageItem(border='w')
#         view.addItem(self.occupancy_img_row)
#         view.setRange(QtCore.QRectF(0, 0, 336, 336))
#         dock_corr_row.addWidget(occupancy_graphics)


    def deserialze_data(self, data):
        return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)

    def handle_data(self, data):
        #print data
        return
        if 'meta_data' not in data:
            self.occupancy_images_columns.setImage(data['column_correlation'][:], autoDownsample=True)
            self.occupancy_images_rows.setImage(data['row_correlation'][:], autoDownsample=True)
