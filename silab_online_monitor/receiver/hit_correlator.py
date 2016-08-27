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
                DUTS.append('MIMOSA %i' % dut_index)
        #        
        dock_area = DockArea()
        parent.addTab(dock_area, name)
        parent.currentChanged.connect(lambda value: self.send_command('ACTIVETAB %s' % str(parent.tabText(value)))) # send active tab index to converter so that it only does something when user is looking at corresponding receiver
        #    
        dock_status = Dock("status")
        dock_status.setMinimumSize(400,90)
        dock_status.setMaximumHeight(110)
        dock_select_duts = Dock("Select DUT's")
        dock_select_duts.setMinimumSize(400,90)
        dock_select_duts.setMaximumHeight(110)
        dock_corr_column = Dock('Column-correlation')
        dock_corr_column.setMinimumSize(400,400)
        dock_corr_row = Dock('Row-correlation') 
        dock_corr_row.setMinimumSize(400,400)
        #
        cb = QtGui.QWidget()
        layout0 = QtGui.QGridLayout()
        cb.setLayout(layout0)
        self.combobox1 = Qt.QComboBox()
        self.combobox1.addItems(DUTS)
        self.combobox1.setMinimumSize(100, 50)
        self.combobox1.setMaximumSize(200, 50)
        self.combobox2 = Qt.QComboBox()
        self.combobox2.addItems(DUTS)
        self.combobox2.setMinimumSize(100, 50)
        self.combobox2.setMaximumSize(200, 50)
        self.select_label = QtGui.QLabel('Correlate:')
        self.select_label1 = QtGui.QLabel('    to    ')
        self.start_button = QtGui.QPushButton('Start')
        self.stop_button = QtGui.QPushButton('Stop')
#         self.start_button.setStyleSheet('QPushButton {border-style: outset}'
#                                         'QPushButton {border-width: 2px}'
#                                         'QPushButton {border-radius: 10px}'
#                                         'QPushButton {border-color: black}'
#                                         'QPushButton {font: bold 14px}'
#                                         'QPushButton {min-width: 10em}'
#                                         'QPushButton {padding: 6px}'
#                                         'QPushButton:pressed {border-style: inset}')
        self.start_button.setMinimumSize(75, 38)
        self.start_button.setMaximumSize(150,38)
        self.stop_button.setMinimumSize(75, 38)
        self.stop_button.setMaximumSize(150,38)
        layout0.setHorizontalSpacing(25)
        layout0.addWidget(self.select_label, 0, 0, 0, 1)
        layout0.addWidget(self.combobox1, 0, 1, 0, 1)
        layout0.addWidget(self.select_label1, 0, 2, 0, 1)
        layout0.addWidget(self.combobox2, 0, 3, 0, 1)
        layout0.addWidget(self.start_button, 0, 4, 0, 1)
        layout0.addWidget(self.stop_button, 0, 5, 0, 1)
        dock_select_duts.addWidget(cb)
        self.combobox1.activated.connect(lambda value: self.send_command('combobox1 %d' % value))
        self.combobox2.activated.connect(lambda value: self.send_command('combobox2 %d' % value))
        self.start_button.clicked.connect(lambda value: self.send_command('START %d' % value))
        self.stop_button.clicked.connect(lambda value: self.send_command('STOP %d' % value))
        #
        cw = QtGui.QWidget()
        layout = QtGui.QGridLayout()
        cw.setLayout(layout)
        reset_button = QtGui.QPushButton('Reset')
        reset_button.setMinimumSize(100,30)
        reset_button.setMaximumSize(300,30)
        layout.setHorizontalSpacing(25)
        layout.addWidget(reset_button, 0, 1, 0, 1)
        noisy_checkbox = QtGui.QCheckBox('Mask noisy pixels')
        layout.addWidget(noisy_checkbox, 0, 3, 1, 1)
        transpose_checkbox = QtGui.QCheckBox('Transpose columns and rows (FE-I4)')
        layout.addWidget(transpose_checkbox, 1, 2, 1, 1)
        self.convert_checkbox = QtGui.QCheckBox('Axis in um')
        layout.addWidget(self.convert_checkbox, 0, 2, 1, 1)
        self.rate_label = QtGui.QLabel("Readout Rate: Hz")
        layout.addWidget(self.rate_label, 1, 3, 1, 1)
        dock_status.addWidget(cw)
        reset_button.clicked.connect(lambda: self.send_command('RESET'))
        transpose_checkbox.stateChanged.connect(lambda value: self.send_command('TRANSPOSE %d' % value))
        noisy_checkbox.stateChanged.connect(lambda value: self.send_command('MASK %d' % value)) #FIXME: Does not do anything now
        #
        #Add plot docks for column corr
        occupancy_graphics1 = pg.GraphicsLayoutWidget()
        occupancy_graphics1.show()
        view1 = occupancy_graphics1.addViewBox()
        occupancy_img_col = pg.ImageItem(border='w')
        #color occupancy
        poss = np.array([0.0, 0.6, 1.0])
        color = np.array([[25,25,112,255],[173,255,47,255],[255,0,0,255]], dtype=np.ubyte) #[RED,GREEN,BLUE,BLACK/WHITE]
        mapp = pg.ColorMap(poss, color)
        lutt = mapp.getLookupTable(0.0, 1.0, 100)
        #
        occupancy_img_col.setLookupTable(lutt, update=True)
        #make plotwidget with axis
        self.plot1 = pg.PlotWidget(viewBox=view1)#,labels={'left': 'Column','bottom':'Column'})
        self.plot1.getAxis('bottom').setLabel(text='Columns')
        self.plot1.getAxis('left').setLabel(text='Columns')
        self.plot1.addItem(occupancy_img_col)
        dock_corr_column.addWidget(self.plot1)
        self.occupancy_images_columns = occupancy_img_col
        #Add plot docks for row corr
        occupancy_graphics2 = pg.GraphicsLayoutWidget()
        occupancy_graphics2.show()
        view2 = occupancy_graphics2.addViewBox()
        occupancy_img_rows = pg.ImageItem(border='w')
        #color occupancy
        occupancy_img_rows.setLookupTable(lutt)
        #make plotwidget with axis
        self.plot2 =pg.PlotWidget(viewBox=view2)#, labels={'left': 'Row','bottom':'Row'})
        self.plot2.getAxis('bottom').setLabel(text='Rows')
        self.plot2.getAxis('left').setLabel(text='Rows')
        self.plot2.addItem(occupancy_img_rows)
        dock_corr_row.addWidget(self.plot2)
        self.occupancy_images_rows = occupancy_img_rows  
        #
        dock_area.addDock(dock_status, 'top')
        dock_area.addDock(dock_select_duts, 'left')
        dock_area.addDock(dock_corr_column, 'bottom')
        dock_area.addDock(dock_corr_row, 'right', dock_corr_column)
        
        ### function to scale axis in um
        def scale_axis(state,dut1,dut2):
            ### function to label axis correctly regarding transposed cols/rows for fe/m26
            def label_axis(state,dut1,dut2):
                if state == 0:
                    if dut1 >= 1 and dut2 == 0:
                        self.plot1.getAxis('left').setLabel(text='FEI4 Rows')
                        self.plot1.getAxis('bottom').setLabel(text='M26 Columns')
                        self.plot2.getAxis('left').setLabel(text='FEI4 Columns')
                        self.plot2.getAxis('bottom').setLabel(text='M26 Rows')
                    elif dut1 == 0 and dut2 >= 1:
                        self.plot1.getAxis('left').setLabel(text='M26 Columns')
                        self.plot1.getAxis('bottom').setLabel(text='FEI4 Rows')
                        self.plot2.getAxis('left').setLabel(text='M26 Rows')
                        self.plot2.getAxis('bottom').setLabel(text='FEI4 Columns')
                    else:
                        self.plot1.getAxis('bottom').setLabel(text='Columns')
                        self.plot1.getAxis('left').setLabel(text='Columns')
                        self.plot2.getAxis('bottom').setLabel(text='Rows')
                        self.plot2.getAxis('left').setLabel(text='Rows')
                elif state == 2:
                    if dut1 >= 1 and dut2 == 0:
                        self.plot1.getAxis('left').setLabel(text='FEI4 Rows / um')
                        self.plot1.getAxis('bottom').setLabel(text='M26 Columns / um')
                        self.plot2.getAxis('left').setLabel(text='FEI4 Columns / um')
                        self.plot2.getAxis('bottom').setLabel(text='M26 Rows / um')
                    elif dut1 == 0 and dut2 >= 1:
                        self.plot1.getAxis('left').setLabel(text='M26 Columns / um')
                        self.plot1.getAxis('bottom').setLabel(text='FEI4 Rows / um')
                        self.plot2.getAxis('left').setLabel(text='M26 Rows / um')
                        self.plot2.getAxis('bottom').setLabel(text='FEI4 Columns / um')
                    else:
                        self.plot1.getAxis('bottom').setLabel(text='Columns / um')
                        self.plot1.getAxis('left').setLabel(text='Columns / um')
                        self.plot2.getAxis('bottom').setLabel(text='Rows / um')
                        self.plot2.getAxis('left').setLabel(text='Rows / um')
                    
            
            if state == 2:
                if dut1 == 0 and dut2 ==0:
                    self.plot1.getAxis('bottom').setScale(250.0)
                    self.plot1.getAxis('left').setScale(250.0)
                    self.plot2.getAxis('bottom').setScale(50.0)
                    self.plot2.getAxis('left').setScale(50.0)
                    self.plot1.getAxis('bottom').setTickSpacing(major=2000,minor=500)
                    self.plot1.getAxis('left').setTickSpacing(major=2000,minor=500)
                if dut1 >=1 and dut2 >= 1:
                    self.plot1.getAxis('bottom').setScale(18.4)
                    self.plot1.getAxis('left').setScale(18.4)
                    self.plot2.getAxis('bottom').setScale(18.4)
                    self.plot2.getAxis('left').setScale(18.4)
                if dut1 >= 1 and dut2 == 0:
                    self.plot1.getAxis('bottom').setScale(18.4)
                    self.plot1.getAxis('left').setScale(50.0)
                    self.plot2.getAxis('bottom').setScale(18.4)
                    self.plot2.getAxis('left').setScale(250.0)
                    self.plot2.getAxis('left').setTickSpacing(major=2000,minor=500)
                if dut1 == 0 and dut2 >= 1:
                    self.plot1.getAxis('bottom').setScale(50.0)
                    self.plot1.getAxis('left').setScale(18.4)
                    self.plot2.getAxis('bottom').setScale(250.0)
                    self.plot2.getAxis('bottom').setTickSpacing(major=2000,minor=500)
                    self.plot2.getAxis('left').setScale(18.4)
            if state == 0:
                self.plot1.getAxis('bottom').setScale(1.0)
                self.plot1.getAxis('left').setScale(1.0)
                self.plot2.getAxis('bottom').setScale(1.0)
                self.plot2.getAxis('left').setScale(1.0)
                self.plot1.getAxis('bottom').setTickSpacing()
                self.plot1.getAxis('left').setTickSpacing()
                self.plot2.getAxis('bottom').setTickSpacing()
                self.plot2.getAxis('left').setTickSpacing()
            
            label_axis(state,dut1,dut2)
        
        self.convert_checkbox.stateChanged.connect(lambda value: scale_axis(value,self.combobox1.currentIndex(),self.combobox2.currentIndex()))
        self.combobox1.activated.connect(lambda value: scale_axis(self.convert_checkbox.checkState(),value,self.combobox2.currentIndex()))
        self.combobox2.activated.connect(lambda value: scale_axis(self.convert_checkbox.checkState(),self.combobox1.currentIndex(),value))


    def deserialze_data(self, data):
        return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)
    
    def handle_data(self, data):
        
        if 'meta_data' not in data:
            for key in data:
                if 'column' == key:
                    self.occupancy_images_columns.setImage(data[key][:,:], autoDownsample = True)
                if 'row' == key:
                    self.occupancy_images_rows.setImage(data[key][:,:], autoDownsample = True)
        else:
            self.rate_label.setText('Readout Rate: %d Hz' % data['meta_data']['fps'])
