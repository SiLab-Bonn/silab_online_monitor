''' Script to check the pybar modules (simulation producer, interpreter/histogrammer converster and receiver).
'''

import os
import sys
import unittest
import yaml
import subprocess
import time
import psutil
from PyQt5.QtWidgets import QApplication

from online_monitor import OnlineMonitor


# creates a yaml config with all pybar related entities
def create_config_yaml():
    conf = {}
    # Add producer
    devices = {}
    devices['DAQ0'] = {'backend': 'tcp://127.0.0.1:5500',
                       'kind': 'pybar_fei4',
                       'delay': 0.1,
                       'data_file': os.path.join(os.path.dirname(__file__), 'pybar_data.h5')
                       }
    devices['DAQ1'] = {'backend': 'tcp://127.0.0.1:5501',
                       'kind': 'pybar_fei4',
                       'delay': 0.1,
                       'data_file': os.path.join(os.path.dirname(__file__), 'pybar_data.h5')
                       }
    conf['producer_sim'] = devices
    # Add converter
    devices = {}
    devices['DUT0'] = {'kind': 'pybar_fei4',
                       'frontend': 'tcp://127.0.0.1:5500',
                       'backend': 'tcp://127.0.0.1:5600',
                       'max_cpu_load': None
                       }
    devices['DUT0_histogrammer'] = {'kind': 'pybar_fei4_histogrammer',
                                    'frontend': 'tcp://127.0.0.1:5600',
                                    'backend': 'tcp://127.0.0.1:5700',
                                    'max_cpu_load': None
                                    }
    devices['DUT1'] = {'kind': 'pybar_fei4',
                       'frontend': 'tcp://127.0.0.1:5501',
                       'backend': 'tcp://127.0.0.1:5601',
                       'max_cpu_load': None
                       }
    devices['DUT1_histogrammer'] = {'kind': 'pybar_fei4_histogrammer',
                                    'frontend': 'tcp://127.0.0.1:5601',
                                    'backend': 'tcp://127.0.0.1:5701',
                                    'max_cpu_load': None
                                    }
    conf['converter'] = devices
    # Add receiver
    devices = {}
    devices['DUT0'] = {'kind': 'pybar_fei4',
                       'frontend': 'tcp://127.0.0.1:5700'
                       }
    devices['DUT1'] = {'kind': 'pybar_fei4',
                       'frontend': 'tcp://127.0.0.1:5701'
                       }
    conf['receiver'] = devices
    return yaml.dump(conf, default_flow_style=False)


# kill process by id, including subprocesses; works for linux and windows
def kill(proc):
    process = psutil.Process(proc.pid)
    for child_proc in process.children(recursive=True):
        child_proc.kill()
    process.kill()


def get_python_processes():  # return the number of python processes
    n_python = 0
    for proc in psutil.process_iter():
        try:
            if 'python' in proc.name():
                n_python += 1
        except psutil.AccessDenied:
            pass
    return n_python


def run_script_in_shell(script, arguments, command=None):
    return subprocess.Popen("%s %s %s" % ('python' if not command else command, script, arguments), shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)


class TestOnlineMonitor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tmp_cfg.yml', 'w') as outfile:
            config_file = create_config_yaml()
            outfile.write(config_file)
        # Linux CIs run usually headless, thus virtual x server is needed for gui testing
        if os.getenv('TRAVIS', False):
            from xvfbwrapper import Xvfb
            cls.vdisplay = Xvfb()
            cls.vdisplay.start()
        # Start the simulation producer to create some fake data
        cls.producer_sim_process = run_script_in_shell('', 'tmp_cfg.yml', 'start_producer_sim')
        # Start converter
        cls.converter_manager_process = run_script_in_shell('', 'tmp_cfg.yml', command='start_converter')
        # Create Gui
        time.sleep(2)
        cls.app = QApplication(sys.argv)
        cls.online_monitor = OnlineMonitor.OnlineMonitorApplication('tmp_cfg.yml')
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):  # Remove created files
        time.sleep(1)
        kill(cls.producer_sim_process)
        kill(cls.converter_manager_process)
        time.sleep(1)
        os.remove('tmp_cfg.yml')
        cls.online_monitor.close()
        time.sleep(1)

    def test_receiver(self):
        self.app.processEvents()
        self.assertEqual(len(self.online_monitor.receivers), 2, 'Number of receivers wrong')
        self.app.processEvents()  # Clear event queue
        # Activate status widget, no data should be received
        self.online_monitor.tab_widget.setCurrentIndex(0)
        self.app.processEvents()  # Event loop does not run in tests, thus we have to trigger the event queue manually
        time.sleep(1)
        self.app.processEvents()
        time.sleep(0.2)
        data_received_0 = []
        self.app.processEvents()
        for receiver in self.online_monitor.receivers:
            data_received_0.append(receiver.occupancy_img.getHistogram())
        # Activate DUT widget, receiver 1 should show data
        self.online_monitor.tab_widget.setCurrentIndex(1)
        self.app.processEvents()
        time.sleep(1)
        self.app.processEvents()
        time.sleep(0.2)
        data_received_1 = []
        for receiver in self.online_monitor.receivers:
            data_received_1.append(receiver.occupancy_img.getHistogram())
        # Activate DUT widget, receiver 2 should show data
        self.online_monitor.tab_widget.setCurrentIndex(2)
        self.app.processEvents()
        time.sleep(1)
        self.app.processEvents()
        time.sleep(1)
        data_received_2 = []
        for receiver in self.online_monitor.receivers:
            data_received_2.append(receiver.occupancy_img.getHistogram())

        self.assertListEqual(data_received_0, [(None, None), (None, None)])
        self.assertTrue(data_received_1[0][0] is not None)
        self.assertTupleEqual(data_received_0[1], (None, None))
        self.assertTrue(data_received_2[1][0] is not None)

    #  Test the Ui
    def test_ui(self):
        self.assertEqual(self.online_monitor.tab_widget.count(), 3, 'Number of tab widgets wrong')  # 2 receiver + status widget expected

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOnlineMonitor)
    unittest.TextTestRunner(verbosity=2).run(suite)
