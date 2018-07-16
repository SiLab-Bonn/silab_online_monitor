from online_monitor.receiver.receiver import Receiver
from zmq.utils import jsonapi
import numpy as np
from numba import jit

from PyQt5 import Qt
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from pyqtgraph.dockarea import DockArea, Dock

from online_monitor.utils import utils


@jit
def hot_threshold_calc(nparray):

    # use np.ravel to flatten since it returns view and is much faster than flatten()
    a = nparray.ravel()

    # remove all zeroes from flattened view
    b = a[a != 0]

    # only take entries above the mean
    c = b[b >= np.mean(b)]

    # the ratio of the mean of all values between the mean and maximum and the maximum occupancy for
    # normal (not noisy) hit pixels scales with an almost constant factor (~ 7 empirically)
    return np.mean(c), np.amax(c)


# this cannot be used so far since the jitted function always only returns a view it seems
# which causes a crash since the input array is cleared in the meantime
@jit
def hot_mask_calc(nparray, factor, upper_mean):

    # get occupancy array with mask, dtype is np.MaskedArray
    o = np.ma.masked_where(nparray > (factor * upper_mean), nparray)

    # extract mask
    m = np.ma.getmask(o)

    # extract data from o
    d = o.data

    # set data to 0 wherever mask is True
    d[m] = 0

    # return masked data and mask
    return d, m


class HitCorrelator(Receiver):

    def setup_receiver(self):

        # We want to change converter settings
        self.set_bidirectional_communication()

        # Send name of Receiver Tab to converter to correlate only when looked at tab
        self.send_command('RECEIVER %s' % self.name)

    def setup_widgets(self, parent, name):

        self.mask_hot_pixels = False
        self.have_mask_col = False
        self.have_mask_row = False
        self.mask_col = None
        self.mask_row = None
        self.hot_pixels_col = 0
        self.hot_pixels_row = 0

        self.occupancy_image_columns = None
        self.occupancy_image_rows = None

        DUTS = []

        for dut_index in range(7):

            if dut_index == 0:
                DUTS.append('FE-I4')
            else:
                DUTS.append('MIMOSA %i' % dut_index)

        dock_area = DockArea()
        parent.addTab(dock_area, name)
        # send active tab index to converter so it only does something when user is looking at corresponding receiver
        parent.currentChanged.connect(lambda value: self.send_command('ACTIVETAB %s' % str(parent.tabText(value))))

        dock_status = Dock("status")
        dock_status.setMinimumSize(400, 90)
        dock_status.setMaximumHeight(110)
        dock_select_duts = Dock("Select DUT's")
        dock_select_duts.setMinimumSize(400, 90)
        dock_select_duts.setMaximumHeight(110)
        dock_corr_column = Dock('Column-correlation')
        dock_corr_column.setMinimumSize(400, 400)
        dock_corr_row = Dock('Row-correlation')
        dock_corr_row.setMinimumSize(400, 400)

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
        self.start_button.setMinimumSize(75, 38)
        self.start_button.setMaximumSize(150, 38)
        self.stop_button.setMinimumSize(75, 38)
        self.stop_button.setMaximumSize(150, 38)
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

        cw = QtGui.QWidget()
        layout = QtGui.QGridLayout()
        cw.setLayout(layout)
        reset_button = QtGui.QPushButton('Reset')
        reset_button.setMinimumSize(100, 30)
        reset_button.setMaximumSize(300, 30)
        layout.setHorizontalSpacing(25)
        layout.addWidget(reset_button, 0, 1, 0, 1)
        self.mask_hot_pixels_checkbox = QtGui.QCheckBox('Mask hot pixels')
        layout.addWidget(self.mask_hot_pixels_checkbox, 0, 2, 1, 1)
        mask_hot_pixels_spinbox = QtGui.QDoubleSpinBox()
        mask_hot_pixels_spinbox.setRange(0.0, 100.0)
        mask_hot_pixels_spinbox.setValue(10.0)
        mask_hot_pixels_spinbox.setSingleStep(1.0)
        mask_hot_pixels_spinbox.setDecimals(1)
        mask_hot_pixels_spinbox.setPrefix('> ')
        mask_hot_pixels_spinbox.setSuffix(' x avg. center occupancy')
        layout.addWidget(mask_hot_pixels_spinbox, 0, 3, 1, 1)
        self.transpose_checkbox = QtGui.QCheckBox('Transpose columns and rows (FE-I4)')
        layout.addWidget(self.transpose_checkbox, 1, 3, 1, 1)
        self.convert_checkbox = QtGui.QCheckBox('Axes in ' + u'\u03BC' + 'm')
        layout.addWidget(self.convert_checkbox, 1, 2, 1, 1)
        self.rate_label = QtGui.QLabel("Readout Rate: Hz")
        layout.addWidget(self.rate_label, 0, 4, 1, 1)
        dock_status.addWidget(cw)
        reset_button.clicked.connect(lambda: self.send_command('RESET'))
        self.transpose_checkbox.stateChanged.connect(lambda value: self.send_command('TRANSPOSE %d' % value))

        # Add plot docks for column corr
        occupancy_graphics1 = pg.GraphicsLayoutWidget()
        occupancy_graphics1.show()
        view1 = occupancy_graphics1.addViewBox()
        occupancy_img_col = pg.ImageItem(border='w')
        # color occupancy
        poss = np.array([0.0, 0.6, 1.0])
        color = np.array([[25, 25, 112, 255], [173, 255, 47, 255], [255, 0, 0, 255]], dtype=np.ubyte)
        mapp = pg.ColorMap(poss, color)
        lutt = mapp.getLookupTable(0.0, 1.0, 100)

        occupancy_img_col.setLookupTable(lutt, update=True)
        # make plotwidget with axis
        self.plot1 = pg.PlotWidget(viewBox=view1)  # ,labels={'left': 'Column','bottom':'Column'})
        self.plot1.getAxis('bottom').setLabel(text='Columns')
        self.plot1.getAxis('left').setLabel(text='Columns')
        self.plot1.addItem(occupancy_img_col)
        dock_corr_column.addWidget(self.plot1)
        self.occupancy_image_columns = occupancy_img_col
        # Add plot docks for row corr
        occupancy_graphics2 = pg.GraphicsLayoutWidget()
        occupancy_graphics2.show()
        view2 = occupancy_graphics2.addViewBox()
        occupancy_img_rows = pg.ImageItem(border='w')
        # color occupancy
        occupancy_img_rows.setLookupTable(lutt, update=True)
        # make plotwidget with axis
        self.plot2 = pg.PlotWidget(viewBox=view2)  # , labels={'left': 'Row','bottom':'Row'})
        self.plot2.getAxis('bottom').setLabel(text='Rows')
        self.plot2.getAxis('left').setLabel(text='Rows')
        self.plot2.addItem(occupancy_img_rows)
        dock_corr_row.addWidget(self.plot2)
        self.occupancy_image_rows = occupancy_img_rows
        #
        dock_area.addDock(dock_status, 'top')
        dock_area.addDock(dock_select_duts, 'left')
        dock_area.addDock(dock_corr_column, 'bottom')
        dock_area.addDock(dock_corr_row, 'right', dock_corr_column)

        # function to set rm hot pixel flag and set factor
        def config_hot_pixels():

            if self.mask_hot_pixels_checkbox.isChecked():
                self.factor = mask_hot_pixels_spinbox.value()
                self.mask_hot_pixels = True
                self.have_mask_row = False
                self.have_mask_col = False

            else:
                self.mask_hot_pixels = False
                self.mask_hot_pixels_checkbox.setText('Mask hot pixels')

        self.mask_hot_pixels_checkbox.stateChanged.connect(config_hot_pixels)
        mask_hot_pixels_spinbox.valueChanged.connect(config_hot_pixels)

        # function to label and scale axis in um
        def scale_and_label_axes(scale_state, dut1, dut2, dut1_name, dut2_name, transpose_state):

            if scale_state == 0:

                # scaling
                self.plot1.getAxis('bottom').setScale(1.0)
                self.plot1.getAxis('left').setScale(1.0)
                self.plot2.getAxis('bottom').setScale(1.0)
                self.plot2.getAxis('left').setScale(1.0)
                self.plot1.getAxis('bottom').setTickSpacing()
                self.plot1.getAxis('left').setTickSpacing()
                self.plot2.getAxis('bottom').setTickSpacing()
                self.plot2.getAxis('left').setTickSpacing()

                # labeling
                if dut1 == 0 and dut2 != 0:

                    if transpose_state == 0:

                        self.plot1.getAxis('bottom').setLabel(text=dut1_name + ' Rows')
                        self.plot2.getAxis('bottom').setLabel(text=dut1_name + ' Columns')

                    elif transpose_state == 2:

                        self.plot1.getAxis('bottom').setLabel(text=dut1_name + ' Columns')
                        self.plot2.getAxis('bottom').setLabel(text=dut1_name + ' Rows')

                    self.plot1.getAxis('left').setLabel(text=dut2_name + ' Columns')
                    self.plot2.getAxis('left').setLabel(text=dut2_name + ' Rows')

                elif dut1 != 0 and dut2 == 0:

                    if transpose_state == 0:

                        self.plot1.getAxis('left').setLabel(text=dut2_name + ' Rows')
                        self.plot2.getAxis('left').setLabel(text=dut2_name + ' Columns')

                    elif transpose_state == 2:

                        self.plot1.getAxis('left').setLabel(text=dut2_name + ' Columns')
                        self.plot2.getAxis('left').setLabel(text=dut2_name + ' Rows')

                    self.plot1.getAxis('bottom').setLabel(text=dut1_name + ' Columns')
                    self.plot2.getAxis('bottom').setLabel(text=dut1_name + ' Rows')

                elif (dut1 != 0 and dut2 != 0) or (dut1 == 0 and dut2 == 0):

                    self.plot1.getAxis('bottom').setLabel(text=dut1_name + ' Columns')
                    self.plot2.getAxis('bottom').setLabel(text=dut1_name + ' Rows')
                    self.plot1.getAxis('left').setLabel(text=dut2_name + ' Columns')
                    self.plot2.getAxis('left').setLabel(text=dut2_name + ' Rows')

            elif scale_state == 2:

                # scaling and labeling
                if dut1 == 0 and dut2 != 0:

                    if transpose_state == 0:

                        self.plot1.getAxis('bottom').setScale(50.0)
                        self.plot2.getAxis('bottom').setScale(250.0)
                        self.plot2.getAxis('bottom').setTickSpacing(major=2000, minor=500)

                        # label
                        self.plot1.getAxis('bottom').setLabel(text=dut1_name + ' Rows / ' + u'\u03BC' + 'm')
                        self.plot2.getAxis('bottom').setLabel(text=dut1_name + ' Columns / ' + u'\u03BC' + 'm')

                    elif transpose_state == 2:

                        self.plot1.getAxis('bottom').setScale(250.0)
                        self.plot2.getAxis('bottom').setScale(50.0)
                        self.plot1.getAxis('bottom').setTickSpacing(major=2000, minor=500)

                        # label
                        self.plot1.getAxis('bottom').setLabel(text=dut1_name + ' Columns / ' + u'\u03BC' + 'm')
                        self.plot2.getAxis('bottom').setLabel(text=dut1_name + ' Rows / ' + u'\u03BC' + 'm')

                    self.plot1.getAxis('left').setScale(18.4)
                    self.plot2.getAxis('left').setScale(18.4)

                    # label
                    self.plot1.getAxis('left').setLabel(text=dut2_name + ' Columns / ' + u'\u03BC' + 'm')
                    self.plot2.getAxis('left').setLabel(text=dut2_name + ' Rows / ' + u'\u03BC' + 'm')

                elif dut1 != 0 and dut2 == 0:

                    if transpose_state == 0:

                        self.plot1.getAxis('left').setScale(50.0)
                        self.plot2.getAxis('left').setScale(250.0)
                        self.plot2.getAxis('left').setTickSpacing(major=2000, minor=500)

                        # label
                        self.plot1.getAxis('left').setLabel(text=dut2_name + ' Rows / ' + u'\u03BC' + 'm')
                        self.plot2.getAxis('left').setLabel(text=dut2_name + ' Columns / ' + u'\u03BC' + 'm')

                    elif transpose_state == 2:
                        self.plot1.getAxis('left').setScale(50.0)
                        self.plot2.getAxis('left').setScale(250.0)
                        self.plot2.getAxis('left').setTickSpacing(major=2000, minor=500)

                        # label
                        self.plot1.getAxis('left').setLabel(text=dut2_name + ' Columns / ' + u'\u03BC' + 'm')
                        self.plot2.getAxis('left').setLabel(text=dut2_name + ' Rows / ' + u'\u03BC' + 'm')

                    self.plot1.getAxis('bottom').setScale(18.4)
                    self.plot2.getAxis('bottom').setScale(18.4)

                    # label
                    self.plot1.getAxis('bottom').setLabel(text=dut1_name + ' Columns / ' + u'\u03BC' + 'm')
                    self.plot2.getAxis('bottom').setLabel(text=dut1_name + ' Rows / ' + u'\u03BC' + 'm')

                else:
                    if dut1 == 0 and dut2 == 0:

                        self.plot1.getAxis('bottom').setScale(250.0)
                        self.plot2.getAxis('bottom').setScale(50.0)
                        self.plot1.getAxis('left').setScale(250.0)
                        self.plot2.getAxis('left').setScale(50.0)
                        self.plot1.getAxis('bottom').setTickSpacing(major=2000, minor=500)
                        self.plot1.getAxis('left').setTickSpacing(major=2000, minor=500)

                    elif dut1 != 0 and dut2 != 0:

                        self.plot1.getAxis('bottom').setScale(18.4)
                        self.plot2.getAxis('bottom').setScale(18.4)
                        self.plot1.getAxis('left').setScale(18.4)
                        self.plot2.getAxis('left').setScale(18.4)

                    self.plot1.getAxis('bottom').setLabel(text=dut1_name + ' Columns / ' + u'\u03BC' + 'm')
                    self.plot2.getAxis('bottom').setLabel(text=dut1_name + ' Rows / ' + u'\u03BC' + 'm')
                    self.plot1.getAxis('left').setLabel(text=dut2_name + ' Columns / ' + u'\u03BC' + 'm')
                    self.plot2.getAxis('left').setLabel(text=dut2_name + ' Rows / ' + u'\u03BC' + 'm')

        self.convert_checkbox.stateChanged.connect(lambda value:
                                                   scale_and_label_axes(value,
                                                                        self.combobox1.currentIndex(),
                                                                        self.combobox2.currentIndex(),
                                                                        self.combobox1.currentText(),
                                                                        self.combobox2.currentText(),
                                                                        self.transpose_checkbox.checkState()))

        self.combobox1.activated.connect(lambda value:
                                         scale_and_label_axes(self.convert_checkbox.checkState(),
                                                              value,
                                                              self.combobox2.currentIndex(),
                                                              self.combobox1.currentText(),
                                                              self.combobox2.currentText(),
                                                              self.transpose_checkbox.checkState()))

        self.combobox2.activated.connect(lambda value:
                                         scale_and_label_axes(self.convert_checkbox.checkState(),
                                                              self.combobox1.currentIndex(),
                                                              value,
                                                              self.combobox1.currentText(),
                                                              self.combobox2.currentText(),
                                                              self.transpose_checkbox.checkState()))

        self.transpose_checkbox.stateChanged.connect(lambda value:
                                                     scale_and_label_axes(self.convert_checkbox.checkState(),
                                                                          self.combobox1.currentIndex(),
                                                                          self.combobox2.currentIndex(),
                                                                          self.combobox1.currentText(),
                                                                          self.combobox2.currentText(),
                                                                          value))

    def deserialize_data(self, data):

        return jsonapi.loads(data, object_hook=utils.json_numpy_obj_hook)

    def handle_data(self, data):

        if 'meta_data' not in data:

            for key in data:

                if 'column' == key:

                    if self.mask_hot_pixels:

                        # if we dont have a mask for the current confuguration yet, make one
                        if not self.have_mask_col:

                            # get mean center occupancy and maximum occupancy
                            occ_upper_mean, occ_max = hot_threshold_calc(self.occupancy_image_columns.image)

                            if occ_max > (self.factor * occ_upper_mean):

                                # get data and mask
                                occupancy = np.ma.masked_where(
                                    self.occupancy_image_columns.image > (self.factor * occ_upper_mean),
                                    self.occupancy_image_columns.image)
                                self.mask_col = np.ma.getmask(occupancy)

#                                # get masked data and mask
#                                masked_data, self.mask_col = hot_mask_calc(self.occupancy_image_columns,
#                                                                           self.factor,
#                                                                           occ_upper_mean)

                                # if we have a mask, count masked pixels
                                if self.mask_col is not None:
                                    self.have_mask_col = True
                                    self.hot_pixels_col = np.count_nonzero(self.mask_col)

                                # extract data and mask
                                masked_data = occupancy.data
                                masked_data[self.mask_col] = 0

                                # clear occupancy image
                                self.occupancy_image_columns.clear()

                                # set new occupancy; free from masked pixels
                                self.occupancy_image_columns.setImage(masked_data, autoDownsample=True)

                            else:
                                # we dont have a mask but we dont need one since no pixels are masked
                                self.hot_pixels_col = 0

                                # plot
                                self.occupancy_image_columns.setImage(data[key][:, :], autoDownsample=True)

                        else:
                            # plot data with static mask
                            mask_data = data[key][:, :]

                            # be able to overwrite entries in input data
                            mask_data.setflags(write=1)

                            # apply mask
                            mask_data[self.mask_col] = 0

                            # plot
                            self.occupancy_image_columns.setImage(mask_data, autoDownsample=True)

                    else:
                        # reset if we stopped masking pixels in plots once; skip if we not have masked at all
                        if self.mask_col is not None:
                            self.mask_col = None
                            self.have_mask_col = False

                        # plot without masking
                        self.occupancy_image_columns.setImage(data[key][:, :], autoDownsample=True)

                if 'row' == key:

                    if self.mask_hot_pixels:

                        # if we dont have a mask for the current confuguration yet, make one
                        if not self.have_mask_row:

                            # get mean center occupancy and maximum occupancy
                            occ_upper_mean, occ_max = hot_threshold_calc(self.occupancy_image_rows.image)

                            if occ_max > (self.factor * occ_upper_mean):

                                # get data and mask
                                occupancy = np.ma.masked_where(
                                    self.occupancy_image_rows.image > (self.factor * occ_upper_mean),
                                    self.occupancy_image_rows.image)
                                self.mask_row = np.ma.getmask(occupancy)

#                                # get masked data and mask
#                                masked_data, self.mask_row = hot_mask_calc(self.occupancy_image_rows,
#                                                                           self.factor,
#                                                                           occ_upper_mean)

                                # if we have a mask, count masked pixels
                                if self.mask_row is not None:
                                    self.have_mask_row = True
                                    self.hot_pixels_row = np.count_nonzero(self.mask_row)

                                # extract data and mask
                                masked_data = occupancy.data
                                masked_data[self.mask_row] = 0

                                # clear occupancy image
                                self.occupancy_image_rows.clear()

                                # set new occupancy; free from masked pixels
                                self.occupancy_image_rows.setImage(masked_data, autoDownsample=True)

                            else:
                                # we dont have a mask but we dont need one since no pixels are masked
                                self.hot_pixels_row = 0

                                # plot
                                self.occupancy_image_rows.setImage(data[key][:, :], autoDownsample=True)
                        else:
                            # plot data with static mask
                            mask_data = data[key][:, :]

                            # be able to overwrite entries in input data
                            mask_data.setflags(write=1)

                            # apply mask
                            mask_data[self.mask_row] = 0

                            # plot
                            self.occupancy_image_rows.setImage(mask_data, autoDownsample=True)
                    else:
                        # reset if we stopped masking pixels in plots once; skip if we not have masked at all
                        if self.mask_row is not None:
                            self.mask_row = None
                            self.have_mask_row = False

                        # plot without masking
                        self.occupancy_image_rows.setImage(data[key][:, :], autoDownsample=True)

            # show amount of masked pixels in GUI
            if self.mask_hot_pixels:
                self.mask_hot_pixels_checkbox.setText('Masking (%i column plot, %i row plot) pixels'
                                                      % (self.hot_pixels_col, self.hot_pixels_row))


        else:
            self.rate_label.setText('Readout Rate: %d Hz' % data['meta_data']['fps'])
