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
        #
        dock_area = DockArea()
        parent.addTab(dock_area, name)
        parent.currentChanged.connect(lambda value: self.send_command('ACTIVETAB %s' % str(parent.tabText(value))))  # send active tab index to converter so that it only does something when user is looking at corresponding receiver
        #
        dock_status = Dock("Telescope status")
        dock_area.addDock(dock_status)

    def handle_data(self, data):
        return
