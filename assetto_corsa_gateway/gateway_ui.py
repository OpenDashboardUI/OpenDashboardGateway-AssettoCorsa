from .gateway import Gateway
from .utils import *

import sys
from pathlib import Path
from PyQt5 import QtCore, QtWidgets, uic
from enum import Enum

from PyQt5.QtCore import QThread, pyqtSignal


mainwindow_ui_file = path = Path(__file__).parent / "mainwindow.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(mainwindow_ui_file)


def show_error(message):
    error_dialog = QtWidgets.QErrorMessage()
    error_dialog.setWindowTitle("Error")
    error_dialog.showMessage("Error: {}".format(message))
    error_dialog.exec()


class GatewayState(Enum):
    DISCONNECTED = 1
    CONNECTED = 2
    CONNECTING = 3


class GatewayMainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.gateway_thread = None
        self.setupUi(self)
        self.create_connections()

    def create_connections(self):
        self.start_button.clicked.connect(self.start_button_pressed)
        self.stop_button.clicked.connect(self.stop_button_pressed)
        pass

    def validate_input(self):
        if not validate_address(self.assetto_corsa_address_line_edit.text()):
            show_error("AssettoCorsa address \"{}\" has invalid format.".format(
                self.assetto_corsa_address_line_edit.text()))
            return False

        if not validate_address(self.open_dashboard_address_line_edit.text()):
            show_error("OpenDashboard address \"{}\" has invalid format.".format(
                self.open_dashboard_address_line_edit.text()))
            return False

        return True

    def set_inputs_enabled(self, inputs_enabled: bool):
        self.open_dashboard_address_line_edit.setEnabled(inputs_enabled)
        self.open_dashboard_port_spin_box.setEnabled(inputs_enabled)
        self.assetto_corsa_address_line_edit.setEnabled(inputs_enabled)
        self.assetto_corsa_port_spin_box.setEnabled(inputs_enabled)
        self.start_button.setEnabled(inputs_enabled)
        self.stop_button.setEnabled(not inputs_enabled)

    def handle_timeout(self):
        self.gateway_thread = None
        show_error("Unable to receive packets from AssettoCorsa")
        self.set_inputs_enabled(True)

    def handle_data_received(self, data_string: str):
        self.data_label.setText(data_string)

    def handle_gateway_state_changed(self, gateway_state: GatewayState):
        if gateway_state == GatewayState.CONNECTED:
            self.gateway_state_label.setStyleSheet("background-color: green")
            self.gateway_state_label.setText("Connected")
        if gateway_state == GatewayState.DISCONNECTED:
            self.gateway_state_label.setStyleSheet("background-color: white")
            self.gateway_state_label.setText("Disconnected")
        if gateway_state == GatewayState.CONNECTING:
            self.gateway_state_label.setStyleSheet("background-color: yellow")
            self.gateway_state_label.setText("Connecting")

    def start_button_pressed(self):
        if not self.validate_input():
            return

        assetto_corsa_address = self.assetto_corsa_address_line_edit.text()
        assetto_corsa_port = self.assetto_corsa_port_spin_box.value()

        open_dashboard_address = self.open_dashboard_address_line_edit.text()
        open_dashboard_port = self.open_dashboard_port_spin_box.value()

        self.set_inputs_enabled(False)

        self.gateway_thread = GatewayThread(
                (assetto_corsa_address, assetto_corsa_port), (open_dashboard_address, open_dashboard_port))
        self.gateway_thread.timeout_received.connect(self.handle_timeout)
        self.gateway_thread.data_received.connect(self.handle_data_received)
        self.gateway_thread.gateway_state.connect(self.handle_gateway_state_changed)
        self.gateway_thread.start()

    def stop_button_pressed(self):
        self.gateway_thread.requestInterruption()
        self.gateway_thread.wait()
        self.gateway_thread = None
        self.set_inputs_enabled(True)
        self.handle_gateway_state_changed(GatewayState.DISCONNECTED)


class GatewayThread(QThread):

    timeout_received = pyqtSignal()
    data_received = pyqtSignal(str, name="data_string")
    gateway_state = pyqtSignal(GatewayState, name="gateway_state")

    def __init__(self, assetto_corsa_connection, open_dashboard_connection):
        QtCore.QThread.__init__(self)
        self.assetto_corsa_connection = assetto_corsa_connection
        self.open_dashboard_connection = open_dashboard_connection
        print("GatewayThread created: {}:{} -> {}:{}".format(
            assetto_corsa_connection[0], assetto_corsa_connection[1],
            open_dashboard_connection[0], open_dashboard_connection[1]
        ))

    def __del__(self):
        print("GatewayThread destroyed")

    def run(self):
        while not self.isInterruptionRequested():
            try:
                self.gateway_state.emit(GatewayState.CONNECTING)
                gateway = Gateway(self.assetto_corsa_connection, self.open_dashboard_connection)
                gateway.init()
                while True:
                    gateway.forward_packet()
                    self.gateway_state.emit(GatewayState.CONNECTED)
                    self.data_received.emit(gateway.data_string)
            except Gateway.TimeoutException as e:
                pass


def run_gui_gateway():
    app = QtWidgets.QApplication(sys.argv)
    window = GatewayMainWindow()
    window.show()
    sys.exit(app.exec_())
