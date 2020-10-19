from .open_dashboard_idl import open_dashboard_pb2

from google.protobuf.json_format import MessageToJson

import struct
import socket
import select
from collections import namedtuple


class Gateway(object):

    RECEIVE_TIMEOUT = 1

    AssettoCorsaData = namedtuple('AssettoCorsaData', [
        'velocity',
        'rotation',
        'throttle',
        'brake',
        'clutch',
        'gear',
        'ax',
        'az',
        'ay'
    ])

    class TimeoutException(RuntimeError):
        def __init__(self, arg):
            self.args = arg

    def __init__(self, assetto_corsa_connection: tuple, open_dashboard_connection: tuple):
        self.assetto_corsa_connection = assetto_corsa_connection
        self.open_dashboard_connection = open_dashboard_connection

        self.assetto_corsa_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.open_dashboard_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.powertrain = open_dashboard_pb2.Powertrain()
        self.vehicle_dynamic = open_dashboard_pb2.VehicleDynamic()
        self.driver_input = open_dashboard_pb2.DriverInput()

        self.data_string = self.generate_data_string()

    def transmit_first_handshake(self):
        handshake_format = 'iii'
        handshake = struct.pack(handshake_format, 1, 1, 0)
        self.assetto_corsa_sock.sendto(handshake, self.assetto_corsa_connection)

    def transmit_second_handshake(self):
        handshake_format = 'iii'
        handshake = struct.pack(handshake_format, 1, 1, 1)
        self.assetto_corsa_sock.sendto(handshake, self.assetto_corsa_connection)

    def receive_header(self):
        ready = select.select([self.assetto_corsa_sock], [], [], Gateway.RECEIVE_TIMEOUT)
        if not ready[0]:
            raise Gateway.TimeoutException('Timeout while receiving header')
        header_data, none = self.assetto_corsa_sock.recvfrom(408)
        header_format = '100s100sii100s100s'
        header = struct.unpack(header_format, header_data)
        car, none = header[0].decode('U16', 'ignore').split('%')
        player, none = header[1].decode('U16', 'ignore').split('%')
        track, none = header[4].decode('U16', 'ignore').split('%')
        info, none = header[5].decode('U16', 'ignore').split('%')

    def receive_data_packet(self) -> AssettoCorsaData:
        data_format = 'sifff????????fffiiiifffffif4f4f4f4f4f4f4f4f4f4f4f4f4f4fff3f'

        ready = select.select([self.assetto_corsa_sock], [], [], Gateway.RECEIVE_TIMEOUT)
        if not ready[0]:
            raise Gateway.TimeoutException('Timeout while receiving data frame')
        data_raw, address = self.assetto_corsa_sock.recvfrom(328)
        data = struct.unpack(data_format, data_raw)

        assetto_corsa_data = Gateway.AssettoCorsaData(
            ax=data[15],
            ay=data[14],
            az=data[13],
            throttle=data[20],
            brake=data[21],
            clutch=data[22],
            gear=data[25],
            velocity=data[2],
            rotation=data[23]
        )
        return assetto_corsa_data

    def generate_data_string(self) -> str:
        data_string = ''
        data_string = data_string + 'Powertrain:'
        data_string = data_string + MessageToJson(self.powertrain, including_default_value_fields=True) + '\n'
        data_string = data_string + 'VehicleDynamic:'
        data_string = data_string + MessageToJson(self.vehicle_dynamic, including_default_value_fields=True) + '\n'
        data_string = data_string + 'DriverInput:'
        data_string = data_string + MessageToJson(self.driver_input, including_default_value_fields=True) + '\n'
        return data_string

    def init(self):
        self.transmit_first_handshake()
        self.receive_header()
        self.transmit_second_handshake()

    def forward_packet(self):
        data_frame = self.receive_data_packet()

        self.powertrain.rotation = data_frame.rotation
        self.powertrain.gear = data_frame.gear

        self.vehicle_dynamic.velocity = data_frame.velocity
        self.vehicle_dynamic.ax = data_frame.ax * 9.81
        self.vehicle_dynamic.ay = data_frame.ay * 9.81
        self.vehicle_dynamic.az = data_frame.az * 9.81

        self.driver_input.throttle = data_frame.throttle
        self.driver_input.brake = data_frame.brake
        # self.driver_input.clutch = 0.0000001

        powertrain_data = self.powertrain.SerializeToString()
        vehicle_dynamic_data = self.vehicle_dynamic.SerializeToString()
        driver_input_data = self.driver_input.SerializeToString()

        fmt = '!iiii{}sii{}sii{}s'.format(len(powertrain_data), len(vehicle_dynamic_data), len(driver_input_data))

        raw_data = struct.pack(
            fmt,
            0x42, 3,
            open_dashboard_pb2.POWERTRAIN_MSG, len(powertrain_data), powertrain_data,
            open_dashboard_pb2.VEHICLE_DYNAMIC_MSG, len(vehicle_dynamic_data), vehicle_dynamic_data,
            open_dashboard_pb2.DRIVER_INPUT_MSG, len(driver_input_data), driver_input_data
        )

        self.open_dashboard_sock.sendto(raw_data, self.open_dashboard_connection)
        self.data_string = self.generate_data_string()


def run_cli_gateway(source: tuple, destination: tuple):
    while True:
        try:
            gateway = Gateway(source, destination)
            gateway.init()

            while True:
                gateway.forward_packet()
                print(gateway.generate_data_string())
        except Gateway.TimeoutException as e:
            print("AssettoCorsa unavailable - retry attempt...")