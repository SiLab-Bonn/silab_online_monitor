from online_monitor.receiver.receiver import Receiver
from zmq.utils import jsonapi
import numpy as np
import time

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.dockarea import DockArea, Dock

from online_monitor.utils import utils


class TelescopeStatus(Receiver):
    def setup_receiver(self):

        self.set_bidirectional_communication()  # We want to change converter settings

    def setup_widgets(self, parent, name):

        # add timing stuff
        self.start_time = time.time()
        self.count_seconds = 0

        # add status tab to online monitor
        dock_area = DockArea()
        parent.addTab(dock_area, name)

        # send active tab index to converter so it only does something when user is looking at corresponding receiver
        parent.currentChanged.connect(lambda value: self.send_command('ACTIVETAB %s' % str(parent.tabText(value))))

        # add status docks
        dock_status_m26 = Dock("Mimosa Status")
        dock_status_fei4 = Dock("FE-I4 Status")

        # get screen dimensions for dynamic dock width
        screen = QtGui.QDesktopWidget().screenGeometry()
        dock_status_m26.setMaximumSize(screen.width() / 2, 150)
        dock_status_fei4.setMaximumSize(screen.width() / 2, 150)

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
        self.reset_fei4_vdda.setMinimumSize(100, 50)
        self.reset_fei4_vddd.setMinimumSize(100, 50)
        self.reset_fei4_vdda.setMaximumSize(150, 50)
        self.reset_fei4_vddd.setMaximumSize(150, 50)
        self.current_vdda_v = QtGui.QLCDNumber()
        self.current_vddd_v = QtGui.QLCDNumber()
        self.current_vdda_c = QtGui.QLCDNumber()
        self.current_vddd_c = QtGui.QLCDNumber()
        self.current_vdda_v.setDecMode()
        self.current_vddd_v.setDecMode()
        self.current_vdda_v.setNumDigits(4)
        self.current_vddd_v.setNumDigits(4)
        self.current_vdda_v.setSmallDecimalPoint(True)
        self.current_vddd_v.setSmallDecimalPoint(True)
        self.current_vdda_c.setDecMode()
        self.current_vddd_c.setDecMode()
        self.current_vdda_c.setNumDigits(4)
        self.current_vddd_c.setNumDigits(4)
        self.current_vdda_c.setSmallDecimalPoint(True)
        self.current_vddd_c.setSmallDecimalPoint(True)
        self.current_vdda_v.setMaximumSize(150, 50)
        self.current_vddd_v.setMaximumSize(150, 50)
        self.current_vdda_c.setMaximumSize(150, 50)
        self.current_vddd_c.setMaximumSize(150, 50)
        self.current_vdda_v.setMinimumSize(100, 50)
        self.current_vddd_v.setMinimumSize(100, 50)
        self.current_vdda_c.setMinimumSize(100, 50)
        self.current_vddd_c.setMinimumSize(100, 50)
        vddd_label = QtGui.QLabel('VDDD:')
        vdda_label = QtGui.QLabel('VDDA:')
        vdda_label.setMinimumSize(75, 35)
        vddd_label.setMinimumSize(75, 35)
        vdda_label.setMaximumSize(100, 50)
        vddd_label.setMaximumSize(100, 50)
        vdda_label.setFont(QtGui.QFont('System', 16))
        vddd_label.setFont(QtGui.QFont('System', 16))
        vddd_label_v = QtGui.QLabel('V ;')
        vdda_label_v = QtGui.QLabel('V ;')
        vdda_label_v.setMinimumSize(15, 50)
        vddd_label_v.setMinimumSize(15, 50)
        vdda_label_v.setMaximumSize(50, 50)
        vddd_label_v.setMaximumSize(50, 50)
        vdda_label_v.setFont(QtGui.QFont('System', 12))
        vddd_label_v.setFont(QtGui.QFont('System', 12))
        vddd_label_c = QtGui.QLabel('A')
        vdda_label_c = QtGui.QLabel('A')
        vdda_label_c.setMinimumSize(30, 50)
        vddd_label_c.setMinimumSize(30, 50)
        vdda_label_c.setMaximumSize(50, 50)
        vddd_label_c.setMaximumSize(50, 50)
        vdda_label_c.setFont(QtGui.QFont('System', 12))
        vddd_label_c.setFont(QtGui.QFont('System', 12))
        status_layout_fei4.addWidget(self.reset_fei4_vdda, 0, 0, 1, 1)
        status_layout_fei4.addWidget(self.reset_fei4_vddd, 1, 0, 1, 1)
        status_layout_fei4.addWidget(vdda_label, 0, 1, 1, 1)
        status_layout_fei4.addWidget(vddd_label, 1, 1, 1, 1)
        status_layout_fei4.addWidget(self.current_vdda_v, 0, 2, 1, 1)
        status_layout_fei4.addWidget(self.current_vddd_v, 1, 2, 1, 1)
        status_layout_fei4.addWidget(vdda_label_v, 0, 3, 1, 1)
        status_layout_fei4.addWidget(vddd_label_v, 1, 3, 1, 1)
        status_layout_fei4.addWidget(self.current_vdda_c, 0, 4, 1, 1)
        status_layout_fei4.addWidget(self.current_vddd_c, 1, 4, 1, 1)
        status_layout_fei4.addWidget(vdda_label_c, 0, 5, 1, 1)
        status_layout_fei4.addWidget(vddd_label_c, 1, 5, 1, 1)

        # add buttons etc. to m26 dock
        self.reset_m26_c = QtGui.QPushButton('Reset current')
        self.reset_m26_v = QtGui.QPushButton('Reset voltage')
        self.reset_m26_c.setMinimumSize(100, 50)
        self.reset_m26_v.setMinimumSize(100, 50)
        self.reset_m26_c.setMaximumSize(150, 50)
        self.reset_m26_v.setMaximumSize(150, 50)
        self.current_m26_c = QtGui.QLCDNumber()
        self.current_m26_v = QtGui.QLCDNumber()
        self.current_m26_c.setDecMode()
        self.current_m26_v.setDecMode()
        self.current_m26_v.setNumDigits(4)
        self.current_m26_v.setSmallDecimalPoint(True)
        self.current_m26_c.setNumDigits(4)
        self.current_m26_c.setSmallDecimalPoint(True)
        self.current_m26_c.setMaximumSize(150, 50)
        self.current_m26_v.setMaximumSize(150, 50)
        self.current_m26_c.setMinimumSize(100, 50)
        self.current_m26_v.setMinimumSize(100, 50)
        m26_label_c = QtGui.QLabel('Current:')
        m26_label_v = QtGui.QLabel('Voltage:')
        m26_label_c.setMinimumSize(75, 35)
        m26_label_v.setMinimumSize(75, 35)
        m26_label_c.setMaximumSize(100, 50)
        m26_label_v.setMaximumSize(100, 50)
        m26_label_c.setFont(QtGui.QFont('System', 16))
        m26_label_v.setFont(QtGui.QFont('System', 16))
        c_label_m26 = QtGui.QLabel('A')
        v_label_m26 = QtGui.QLabel('V')
        c_label_m26.setMinimumSize(30, 50)
        v_label_m26.setMinimumSize(30, 50)
        c_label_m26.setMaximumSize(50, 50)
        v_label_m26.setMaximumSize(50, 50)
        c_label_m26.setFont(QtGui.QFont('System', 12))
        v_label_m26.setFont(QtGui.QFont('System', 12))
        status_layout_m26.addWidget(self.reset_m26_v, 0, 0, 1, 1)
        status_layout_m26.addWidget(self.reset_m26_c, 1, 0, 1, 1)
        status_layout_m26.addWidget(m26_label_c, 0, 2, 1, 1)
        status_layout_m26.addWidget(m26_label_v, 1, 2, 1, 1)
        status_layout_m26.addWidget(self.current_m26_c, 0, 3, 1, 1)
        status_layout_m26.addWidget(self.current_m26_v, 1, 3, 1, 1)
        status_layout_m26.addWidget(c_label_m26, 0, 4, 1, 1)
        status_layout_m26.addWidget(v_label_m26, 1, 4, 1, 1)

        # add buttons etc to layout widgets and to docks
        dock_status_m26.addWidget(status_widget_m26)
        dock_status_fei4.addWidget(status_widget_fei4)

        # add dock for Mimosa power supply
        dock_m26 = Dock("Mimosa power supply")

        # add graphicslayout and plots
        plot_graphics_m26 = pg.GraphicsLayoutWidget()
        plot_graphics_m26.show()
        plot_m26_v = pg.PlotItem(labels={'left': 'Voltage / V', 'bottom': 'Time / s'})
        plot_m26_c = pg.PlotItem(labels={'left': 'Current / A', 'bottom': 'Time / s'})
        self.m26_v = pg.PlotCurveItem(pen='r')
        self.m26_c = pg.PlotCurveItem(pen='g')

        # add horizontal lines and pens for plotting max and min values
        # need to create these for having same pen in legend as in plot since
        # pg.InfiniteLine cant be put as item in LegendItem
        green_pen = pg.PlotCurveItem()
        red_pen = pg.PlotCurveItem()
        green_pen.setPen(color='g', style=QtCore.Qt.DashLine)
        red_pen.setPen(color='r', style=QtCore.Qt.DashLine)
        self.m26_v_max = pg.InfiniteLine(angle=0)
        self.m26_v_min = pg.InfiniteLine(angle=0)
        self.m26_c_max = pg.InfiniteLine(angle=0)
        self.m26_c_min = pg.InfiniteLine(angle=0)
        self.m26_v_max.setPen(color='r', style=QtCore.Qt.DashLine)
        self.m26_v_min.setPen(color='r', style=QtCore.Qt.DashLine)
        self.m26_c_max.setPen(color='g', style=QtCore.Qt.DashLine)
        self.m26_c_min.setPen(color='g', style=QtCore.Qt.DashLine)

        # add legends for plots
        legend_m26_v = pg.LegendItem(offset=(80, 10))
        legend_m26_v.setParentItem(plot_m26_v)
        legend_m26_v.addItem(self.m26_v, 'M26_voltage')
        legend_m26_v_min_max = pg.LegendItem(offset=(680, 10))
        legend_m26_v_min_max.setParentItem(plot_m26_v)
        legend_m26_v_min_max.addItem(red_pen, 'min./max. M26_voltage')
        legend_m26_c = pg.LegendItem(offset=(80, 10))
        legend_m26_c.setParentItem(plot_m26_c)
        legend_m26_c.addItem(self.m26_c, 'M26_current')
        legend_m26_c_min_max = pg.LegendItem(offset=(680, 10))
        legend_m26_c_min_max.setParentItem(plot_m26_c)
        legend_m26_c_min_max.addItem(green_pen, 'min./max. M26_current')

        # add items to plots and customize plots viewboxes
        plot_m26_v.addItem(self.m26_v)
        plot_m26_c.addItem(self.m26_c)
        plot_m26_v.addItem(self.m26_v_max)
        plot_m26_v.addItem(self.m26_v_min)
        plot_m26_c.addItem(self.m26_c_max)
        plot_m26_c.addItem(self.m26_c_min)
        plot_m26_v.vb.setBackgroundColor('#545454')
        plot_m26_c.vb.setBackgroundColor('#545454')
        plot_m26_v.setYRange(7, 9, padding=0)
        plot_m26_c.setYRange(2, 4, padding=0)
        plot_m26_v.setXRange(-60, 0)
        plot_m26_c.setXRange(-60, 0)
        plot_m26_v.getAxis('left').setZValue(0)
        plot_m26_c.getAxis('left').setZValue(0)
        plot_m26_v.getAxis('left').setGrid(155)
        plot_m26_c.getAxis('left').setGrid(155)

        # add plots to graphicslayout and layout to dock
        plot_graphics_m26.addItem(plot_m26_v, row=0, col=1, rowspan=1, colspan=2)
        plot_graphics_m26.addItem(plot_m26_c, row=1, col=1, rowspan=1, colspan=2)
        dock_m26.addWidget(plot_graphics_m26)

        # complicated approach with two y axis for m26 v and c

        # add plot with two axes for volatge and current
        #        plot_graphics_m26 = pg.GraphicsView()
        #        plot_graphics_m26.show()
        #        plot_layout = pg.GraphicsLayout()
        #        plot_graphics_m26.setCentralWidget(plot_layout)
        #        axis_current = pg.AxisItem("left")
        #        plot_layout.addItem(axis_current, row = 2, col = 5,  rowspan=1, colspan=1)
        #        view_current = pg.ViewBox()
        #        self.plot_current = pg.PlotItem(viewBox=view_current)
        #        view_voltage = pg.ViewBox()
        #        self.plot_voltage = pg.PlotItem(viewBox=view_voltage)
        #        plot_layout.addItem(self.plot_voltage, row = 2, col = 6,  rowspan = 1, colspan = 1)
        #        plot_layout.scene().addItem(view_current)
        #        view_current.disableAutoRange(axis=view_current.YAxis)
        #        axis_current.linkToView(view_current)
        #        view_current.setXLink(view_voltage)
        #        view_current.setBackgroundColor('#545454')
        #        self.plot_voltage.getAxis("left").setLabel('Voltage / V')
        #        self.plot_voltage.getAxis("bottom").setLabel('Time / s')
        #        self.plot_voltage.addLegend(offset=(20,20))
        #        self.plot_current.addLegend(offset=(120,20))
        #        voltage_pen = QtGui.QPen()
        #        voltage_pen.setStyle(QtCore.Qt.SolidLine)
        #        voltage_pen.setWidthF(1)
        #        current_pen = QtGui.QPen()
        #        current_pen.setStyle(QtCore.Qt.DashLine)
        #        current_pen.setWidthF(1)
        #        self.plot_voltage.getAxis('left').setPen(voltage_pen)
        #        self.plot_voltage.getAxis('left').setGrid(155)
        #        axis_current.setPen(current_pen)
        #        axis_current.setGrid(155)
        #        view_voltage.setLimits(minYRange=1)
        #        view_current.setLimits(minYRange=10)
        #        axis_current.setLabel('Current / mA')
        #        dock_m26.addWidget(plot_graphics_m26)
        #
        #        # update view
        #        def update_views():
        #            view_current.setGeometry(view_voltage.sceneBoundingRect())
        #
        #        # update view when viewbox was scaled
        #        view_voltage.sigResized.connect(update_views)
        #        view_current.enableAutoRange(axis= pg.ViewBox.XYAxes, enable=True)

        # add dock for FE-I4 power supply
        dock_fei4 = Dock("FE-I4 power supply")

        # add graphicslayout and plots
        plot_graphics_fei4 = pg.GraphicsLayoutWidget()
        plot_graphics_fei4.show()
        plot_fei4_v = pg.PlotItem(labels={'left': 'Voltage / V', 'bottom': 'Time / s'})
        plot_fei4_c = pg.PlotItem(labels={'left': 'Current / A', 'bottom': 'Time / s'})
        self.vdda_v = pg.PlotCurveItem(pen='r')
        self.vddd_v = pg.PlotCurveItem(pen='g')
        self.vdda_c = pg.PlotCurveItem(pen='r')
        self.vddd_c = pg.PlotCurveItem(pen='g')

        # add horizontal lines and pens for plotting max and min values
        self.vdda_v_max = pg.InfiniteLine(angle=0)
        self.vdda_v_min = pg.InfiniteLine(angle=0)
        self.vddd_v_max = pg.InfiniteLine(angle=0)
        self.vddd_v_min = pg.InfiniteLine(angle=0)
        self.vdda_c_max = pg.InfiniteLine(angle=0)
        self.vdda_c_min = pg.InfiniteLine(angle=0)
        self.vddd_c_max = pg.InfiniteLine(angle=0)
        self.vddd_c_min = pg.InfiniteLine(angle=0)
        self.vdda_v_max.setPen(color='r', style=QtCore.Qt.DashLine)
        self.vdda_v_min.setPen(color='r', style=QtCore.Qt.DashLine)
        self.vddd_v_max.setPen(color='g', style=QtCore.Qt.DashLine)
        self.vddd_v_min.setPen(color='g', style=QtCore.Qt.DashLine)
        self.vdda_c_max.setPen(color='r', style=QtCore.Qt.DashLine)
        self.vdda_c_min.setPen(color='r', style=QtCore.Qt.DashLine)
        self.vddd_c_max.setPen(color='g', style=QtCore.Qt.DashLine)
        self.vddd_c_min.setPen(color='g', style=QtCore.Qt.DashLine)

        # add legends for plots
        legend_fei4_v = pg.LegendItem(offset=(80, 10))
        legend_fei4_v.setParentItem(plot_fei4_v)
        legend_fei4_v_min_max = pg.LegendItem(offset=(740, 10))
        legend_fei4_v_min_max.setParentItem(plot_fei4_v)
        legend_fei4_v.addItem(self.vdda_v, 'VDDA_voltage')
        legend_fei4_v.addItem(self.vddd_v, 'VDDD_voltage')
        legend_fei4_v_min_max.addItem(green_pen, 'min./max. VDDA_voltage')
        legend_fei4_v_min_max.addItem(red_pen, 'min./max. VDDD_voltage')
        legend_fei4_c = pg.LegendItem(offset=(80, 10))
        legend_fei4_c.setParentItem(plot_fei4_c)
        legend_fei4_c_min_max = pg.LegendItem(offset=(740, 10))
        legend_fei4_c_min_max.setParentItem(plot_fei4_c)
        legend_fei4_c.addItem(self.vdda_c, 'VDDA_current')
        legend_fei4_c.addItem(self.vddd_c, 'VDDD_current')
        legend_fei4_c_min_max.addItem(green_pen, 'min./max. VDDA_current')
        legend_fei4_c_min_max.addItem(red_pen, 'min./max. VDDD_current')

        # add items to plots and customize plots viewboxes
        plot_fei4_v.addItem(self.vdda_v)
        plot_fei4_v.addItem(self.vddd_v)
        plot_fei4_v.addItem(self.vdda_v_max)
        plot_fei4_v.addItem(self.vdda_v_min)
        plot_fei4_v.addItem(self.vddd_v_max)
        plot_fei4_v.addItem(self.vddd_v_min)
        plot_fei4_c.addItem(self.vdda_c)
        plot_fei4_c.addItem(self.vddd_c)
        plot_fei4_c.addItem(self.vdda_c_max)
        plot_fei4_c.addItem(self.vdda_c_min)
        plot_fei4_c.addItem(self.vddd_c_max)
        plot_fei4_c.addItem(self.vddd_c_min)
        plot_fei4_v.vb.setBackgroundColor('#545454')
        plot_fei4_c.vb.setBackgroundColor('#545454')
        plot_fei4_v.setYRange(1.0, 2.0, padding=0)
        plot_fei4_c.setYRange(0, 0.5, padding=0)
        plot_fei4_v.setXRange(-60, 0)
        plot_fei4_c.setXRange(-60, 0)
        plot_fei4_v.getAxis('left').setZValue(0)
        plot_fei4_c.getAxis('left').setZValue(0)
        plot_fei4_v.getAxis('left').setGrid(155)
        plot_fei4_c.getAxis('left').setGrid(155)

        # add plots to graphicslayout and layout to dock
        plot_graphics_fei4.addItem(plot_fei4_v, row=0, col=1, rowspan=1, colspan=2)
        plot_graphics_fei4.addItem(plot_fei4_c, row=1, col=1, rowspan=1, colspan=2)
        dock_fei4.addWidget(plot_graphics_fei4)

        # connect reset buttons
        self.reset_m26_c.clicked.connect(lambda: self.send_command('RESET_M26_CURRENT'))
        self.reset_m26_v.clicked.connect(lambda: self.send_command('RESET_M26_VOLTAGE'))
        self.reset_fei4_vdda.clicked.connect(lambda: self.send_command('RESET_FEI4_VDDA'))
        self.reset_fei4_vddd.clicked.connect(lambda: self.send_command('RESET_FEI4_VDDD'))

        # add dict of all used plotcurveitems for individual handling of each plot
        self.plots = {'m26_c': self.m26_c, 'm26_v': self.m26_v, 'vdda_c': self.vdda_c,
                      'vdda_v': self.vdda_v, 'vddd_c': self.vddd_c, 'vddd_v': self.vddd_v}

        self.maxima = {'m26_c': self.m26_c_max, 'm26_v': self.m26_v_max, 'vdda_c': self.vdda_c_max,
                       'vdda_v': self.vdda_v_max, 'vddd_c': self.vddd_c_max, 'vddd_v': self.vddd_v_max}

        self.minima = {'m26_c': self.m26_c_min, 'm26_v': self.m26_v_min, 'vdda_c': self.vdda_c_min,
                       'vdda_v': self.vdda_v_min, 'vddd_c': self.vddd_c_min, 'vddd_v': self.vddd_v_min}

        self.max_values = {'m26_c': 0, 'm26_v': 0, 'vdda_c': 0, 'vdda_v': 0, 'vddd_c': 0, 'vddd_v': 0}

        self.min_values = {'m26_c': 0, 'm26_v': 0, 'vdda_c': 0, 'vdda_v': 0, 'vddd_c': 0, 'vddd_v': 0}

        self.QLCD_displays = {'m26_c': self.current_m26_c, 'm26_v': self.current_m26_v,
                              'vdda_c': self.current_vdda_c, 'vdda_v': self.current_vdda_v,
                              'vddd_c': self.current_vddd_c, 'vddd_v': self.current_vddd_v}

        # add min_max_dock
        dock_min_max_vals = Dock("min./max.\n values")
        dock_min_max_vals.setMaximumWidth(screen.width())
        dock_min_max_vals.setMaximumHeight(80)

        # add min_max_widget with layout
        min_max_widget = QtGui.QWidget()
        min_max_layout = QtGui.QGridLayout()
        min_max_layout.setHorizontalSpacing(25)
        min_max_widget.setLayout(min_max_layout)

        # add table of min max values to minmax dock
        self.min_max_table = QtGui.QTableWidget()
        self.min_max_table.setMaximumSize(screen.width() * 0.8, 80)
        min_max_horizontal = self.min_max_table.horizontalHeader()
        # min_max_horizontal.setFont(QtGui.QFont('Times',12))
        min_max_vertical = self.min_max_table.verticalHeader()
        # min_max_vertical.setFont(QtGui.QFont('Times',12))
        min_max_horizontal.setResizeMode(QtGui.QHeaderView.Stretch)
        min_max_vertical.setResizeMode(QtGui.QHeaderView.Stretch)
        self.min_max_table.setRowCount(1)
        self.min_max_table.setColumnCount(6)
        self.min_max_table.setVerticalHeaderLabels(['min./max. values:'])
        self.min_max_table.setHorizontalHeaderLabels(['M26_voltage', 'M26_current',
                                                      'VDDA_voltage', 'VDDA_current',
                                                      'VDDD_voltage', 'VDDD_current'])
        self.min_max_table.showGrid()
        self.font = QtGui.QFont()
        self.font.setPointSize(12)
        self.min_max_table.setFont(self.font)

        # add reset button for min max values
        reset_min_max = QtGui.QPushButton('Reset global \n min./max. values')
        reset_min_max.setMaximumSize(150, 50)
        reset_min_max.setMinimumWidth(150)

        # add table and reset button to layoutwidget and min max widget to dock
        min_max_layout.addWidget(self.min_max_table, 0, 1, 1, 1)
        min_max_layout.addWidget(reset_min_max, 0, 0, 1, 1)
        dock_min_max_vals.addWidget(min_max_widget)

        # add reset func for min max values
        def reset_min_max_values():
            for key in self.max_values:
                self.min_values[key] = 0
                self.max_values[key] = 0

        # connect reset min max button
        reset_min_max.clicked.connect(lambda: reset_min_max_values())

        # add Docks to DockArea
        dock_area.addDock(dock_status_m26, 'top')
        dock_area.addDock(dock_status_fei4, 'right', dock_status_m26)
        dock_area.addDock(dock_m26, 'bottom', dock_status_m26)
        dock_area.addDock(dock_fei4, 'bottom', dock_status_fei4)
        dock_area.addDock(dock_min_max_vals, 'bottom')

    def deserialze_data(self, data):

        return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)

    def handle_data(self, data):

        # status data has this keyword
        if 'status' in data:

            # update QLCDDisplays every second with latest entry of each data
            if time.time() - self.start_time >= self.count_seconds:

                for key in data['status']:
                    self.QLCD_displays[key].display(format(data['status'][key][1][0], '.3f'))

                    # ~ # three decimal places for vdda/vdda currents
                    # ~ if key == 'vdda_c' or key == 'vddd_c':
                    # ~ self.QLCD_displays[key].display(format(data['status'][key][1][0], '.3f'))

                    # ~ # two decimal places for the rest
                    # ~ else:
                    # ~ self.QLCD_displays[key].display(format(data['status'][key][1][0], '.2f'))

                self.count_seconds += 1.0

            # add temporary copy of min and max values to check whether they changed in new data
            tmp_max_values = self.max_values.copy()
            tmp_min_values = self.min_values.copy()

            # fill plots
            for key in data['status']:

                # if array not full, plot data only up to current array_index, 'indices' is keyword
                if data['indices'][key] < data['status'][key].shape[1]:

                    # set the plot data up to self.array_index to the corresponding arrays
                    self.plots[key].setData(data['status'][key][0][:data['indices'][key]],
                                            data['status'][key][1][:data['indices'][key]],
                                            autoDownsample=True)

                    # check if max value of current data is bigger than last max value
                    if self.max_values[key] < np.amax(data['status'][key][1][:data['indices'][key]]):

                        self.max_values[key] = np.amax(data['status'][key][1][:data['indices'][key]])

                    # check if min value of current data is smaller than last min value
                    elif self.min_values[key] == 0 or self.min_values[key] > np.amin(data['status'][key][1][:data['indices'][key]]):

                        self.min_values[key] = np.amin(data['status'][key][1][:data['indices'][key]])

                # if array full, plot entire array
                elif data['indices'][key] >= data['status'][key].shape[1]:

                    # set the plot data to the corresponding arrays
                    self.plots[key].setData(data['status'][key][0], data['status'][key][1], autoDownsample=True)

                    # check if max value of current data is bigger than last max value
                    if self.max_values[key] < np.amax(data['status'][key][1]):

                        self.max_values[key] = np.amax(data['status'][key][1])

                    # check if min value of current data is smaller than last min value
                    elif self.min_values[key] == 0 or self.min_values[key] > np.amin(data['status'][key][1]):

                        self.min_values[key] = np.amin(data['status'][key][1])

                # update max min values in table only if values changed
                if tmp_max_values[key] != self.max_values[key] or tmp_min_values[key] != self.min_values[key]:

                    # loop over table header indices
                    for i in range(0, self.min_max_table.columnCount()):

                        # get table header and creat tablewidgetitem
                        header = self.min_max_table.horizontalHeaderItem(i).text()
                        newItem = QtGui.QTableWidgetItem()
                        # newItem.setFont(QtGui.QFont('Serif', 11, QtGui.QFont.Bold))
                        newItem.setFont(self.font)
                        newItem.setTextAlignment(QtCore.Qt.AlignCenter)

                        # if data key is in header text
                        if key in header.lower():

                            # set text of tablewidgetitem; separate currents from voltages
                            if '_c' in key:

                                newItem.setText(format(self.min_values[key], '.3f') + '  A  /  '
                                                +
                                                format(self.max_values[key], '.3f') + '  A')
                            elif '_v' in key:

                                newItem.setText(format(self.min_values[key], '.3f') + '  V  /  '
                                                +
                                                format(self.max_values[key], '.3f') + '  V')

                            # set cell entry to min max value, then break
                            self.min_max_table.setItem(0, i, newItem)

                            break

                # set max and min lines for each plot
                self.maxima[key].setValue(self.max_values[key])
                self.minima[key].setValue(self.min_values[key])
