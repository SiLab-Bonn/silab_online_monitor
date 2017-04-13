from online_monitor.receiver.receiver import Receiver
import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from pyqtgraph.dockarea import DockArea, Dock


from online_monitor.utils import utils


class PybarFEI4(Receiver):

    def setup_receiver(self):
        self.set_bidirectional_communication()  # We want to change converter settings

    def setup_widgets(self, parent, name):
        dock_area = DockArea()
        parent.addTab(dock_area, name)
        # Docks
        dock_status = Dock("Status", size=(800, 40))
        dock_area.addDock(dock_status, 'top')
        
        dock_tdc_chip01 = Dock("Time digital converter values (TDC)", size=(400, 400))
        dock_tot_chip01 = Dock("Time over threshold values (TOT)", size=(400, 400))
        
        dock_tdc_chip02 = Dock("Time digital converter values (TDC)", size=(400, 400))
        dock_tot_chip02 = Dock("Time over threshold values (TOT)", size=(400, 400))
        
        dock_tdc_chip03 = Dock("Time digital converter values (TDC)", size=(400, 400))
        dock_tot_chip03 = Dock("Time over threshold values (TOT)", size=(400, 400))
        
        dock_tdc_chip04 = Dock("Time digital converter values (TDC)", size=(400, 400))
        dock_tot_chip04 = Dock("Time over threshold values (TOT)", size=(400, 400))
        
        dock_tdc_chip05 = Dock("Time digital converter values (TDC)", size=(400, 400))
        dock_tot_chip05 = Dock("Time over threshold values (TOT)", size=(400, 400))        


        dock_area.addDock(dock_tdc_chip01, 'bottom', dock_status)
        dock_area.addDock(dock_tdc_chip02, 'right', dock_tdc_chip01)
        dock_area.addDock(dock_tdc_chip03, 'right', dock_tdc_chip02)
        dock_area.addDock(dock_tdc_chip04, 'right', dock_tdc_chip03)
        dock_area.addDock(dock_tdc_chip05, 'right', dock_tdc_chip04)
        
        dock_area.addDock(dock_tot_chip01, 'bottom', dock_tdc_chip01)
        dock_area.addDock(dock_tot_chip02, 'bottom', dock_tdc_chip02)
        dock_area.addDock(dock_tot_chip03, 'bottom', dock_tdc_chip03)
        dock_area.addDock(dock_tot_chip04, 'bottom', dock_tdc_chip04)
        dock_area.addDock(dock_tot_chip05, 'bottom', dock_tdc_chip05)

        # Different plot docks
    
        tdc_plot_widget_01 = pg.PlotWidget(background="w")
        self.tdc_plot_01 = tdc_plot_widget_01.plot(np.linspace(-0.5, 4095.5, 4097), np.zeros((4096)), stepMode=True)
        tdc_plot_widget_01.showGrid(y=True)
        tdc_plot_widget_01.setXRange(0, 200, update=True)
        dock_tdc_chip01.addWidget(tdc_plot_widget_01)
        
        tot_plot_widget_01 = pg.PlotWidget(background="w")
        self.tot_plot_01 = tot_plot_widget_01.plot(np.linspace(-0.5, 15.5, 17), np.zeros((16)), stepMode=True)
        tot_plot_widget_01.showGrid(y=True)
        dock_tot_chip01.addWidget(tot_plot_widget_01)
        
        tdc_plot_widget_02 = pg.PlotWidget(background="w")
        self.tdc_plot_02 = tdc_plot_widget_02.plot(np.linspace(-0.5, 4095.5, 4097), np.zeros((4096)), stepMode=True)
        tdc_plot_widget_02.showGrid(y=True)
        tdc_plot_widget_02.setXRange(0, 200, update=True)
        dock_tdc_chip02.addWidget(tdc_plot_widget_02)
        
        tot_plot_widget_02 = pg.PlotWidget(background="w")
        self.tot_plot_02 = tot_plot_widget_02.plot(np.linspace(-0.5, 15.5, 17), np.zeros((16)), stepMode=True)
        tot_plot_widget_02.showGrid(y=True)
        dock_tot_chip02.addWidget(tot_plot_widget_02)
        
        tdc_plot_widget_03 = pg.PlotWidget(background="w")
        self.tdc_plot_03 = tdc_plot_widget_03.plot(np.linspace(-0.5, 4095.5, 4097), np.zeros((4096)), stepMode=True)
        tdc_plot_widget_03.showGrid(y=True)
        tdc_plot_widget_03.setXRange(0, 200, update=True)
        dock_tdc_chip03.addWidget(tdc_plot_widget_03)
         
        tot_plot_widget_03 = pg.PlotWidget(background="w")
        self.tot_plot_03 = tot_plot_widget_03.plot(np.linspace(-0.5, 15.5, 17), np.zeros((16)), stepMode=True)
        tot_plot_widget_03.showGrid(y=True)
        dock_tot_chip03.addWidget(tot_plot_widget_03)
         
        tdc_plot_widget_04 = pg.PlotWidget(background="w")
        self.tdc_plot_04 = tdc_plot_widget_04.plot(np.linspace(-0.5, 4095.5, 4097), np.zeros((4096)), stepMode=True)
        tdc_plot_widget_04.showGrid(y=True)
        tdc_plot_widget_04.setXRange(0, 200, update=True)
        dock_tdc_chip04.addWidget(tdc_plot_widget_04)
         
        tot_plot_widget_04 = pg.PlotWidget(background="w")
        self.tot_plot_04 = tot_plot_widget_04.plot(np.linspace(-0.5, 15.5, 17), np.zeros((16)), stepMode=True)
        tot_plot_widget_04.showGrid(y=True)
        dock_tot_chip04.addWidget(tot_plot_widget_04)
 
        tdc_plot_widget_05 = pg.PlotWidget(background="w")
        self.tdc_plot_05 = tdc_plot_widget_05.plot(np.linspace(-0.5, 4095.5, 4097), np.zeros((4096)), stepMode=True)
        tdc_plot_widget_05.showGrid(y=True)
        tdc_plot_widget_05.setXRange(0, 200, update=True)
        dock_tdc_chip05.addWidget(tdc_plot_widget_05)
         
        tot_plot_widget_05 = pg.PlotWidget(background="w")
        self.tot_plot_05 = tot_plot_widget_05.plot(np.linspace(-0.5, 15.5, 17), np.zeros((16)), stepMode=True)
        tot_plot_widget_05.showGrid(y=True)
        dock_tot_chip05.addWidget(tot_plot_widget_05)
        
#        Status dock on top
        cw = QtGui.QWidget()
        cw.setStyleSheet("QWidget {background-color:white}")
        layout = QtGui.QGridLayout()
        cw.setLayout(layout)
        
        self.reset_button = QtGui.QPushButton('Reset')
        layout.addWidget(self.reset_button, 0, 7, 0, 1)
        dock_status.addWidget(cw)
        
        # Connect widgets
        self.reset_button.clicked.connect(lambda: self.send_command('RESET'))
        
        self.plot_delay = 0

    def deserialze_data(self, data):
        datar, meta = utils.simple_dec(data)
        if 'occupancies' in meta:
            meta['occupancies'] = datar
        return meta

    def handle_data(self, data):
        if 'meta_data' not in data:
            self.tot_plot_01.setData(x=np.linspace(-0.5, 15.5, 17), y=data['tot_hist'][0], fillLevel=0, brush=(0, 0, 255, 150))
            self.tdc_plot_01.setData(x=np.linspace(-0.5, 4096.5, 4097), y=data['tdc_counters'][0], fillLevel=0, brush=(0, 0, 255, 150))
            
            self.tot_plot_02.setData(x=np.linspace(-0.5, 15.5, 17), y=data['tot_hist'][1], fillLevel=0, brush=(0, 0, 255, 150))
            self.tdc_plot_02.setData(x=np.linspace(-0.5, 4096.5, 4097), y=data['tdc_counters'][1], fillLevel=0, brush=(0, 0, 255, 150))
            
            self.tot_plot_03.setData(x=np.linspace(-0.5, 15.5, 17), y=data['tot_hist'][2], fillLevel=0, brush=(0, 0, 255, 150))
            self.tdc_plot_03.setData(x=np.linspace(-0.5, 4096.5, 4097), y=data['tdc_counters'][2], fillLevel=0, brush=(0, 0, 255, 150))
            
            self.tot_plot_04.setData(x=np.linspace(-0.5, 15.5, 17), y=data['tot_hist'][3], fillLevel=0, brush=(0, 0, 255, 150))
            self.tdc_plot_04.setData(x=np.linspace(-0.5, 4096.5, 4097), y=data['tdc_counters'][3], fillLevel=0, brush=(0, 0, 255, 150))
            
            self.tot_plot_05.setData(x=np.linspace(-0.5, 15.5, 17), y=data['tot_hist'][4], fillLevel=0, brush=(0, 0, 255, 150))
            self.tdc_plot_05.setData(x=np.linspace(-0.5, 4096.5, 4097), y=data['tdc_counters'][4], fillLevel=0, brush=(0, 0, 255, 150))
