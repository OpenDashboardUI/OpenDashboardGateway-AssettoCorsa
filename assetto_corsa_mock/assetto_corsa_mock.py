#!/usr/bin/env python3

import socket
import struct
import _thread
import time
import pyshark
from pathlib import Path


def wait_for_first_handshake(sock):
    rec_data, client = sock.recvfrom(12)
    client_address = client[0]
    client_port = int(client[1])
    return client_address, client_port


def wait_for_second_handshake(sock):
    sock.recvfrom(12)


def transmit_header(sock, address, port):
    header_format = "100s100sii100s100s"

    car_name = "car_name%foo".encode("U16")
    player_name = "player_name%foo".encode("U16")
    info = "info%foo".encode("U16")
    track_name = "track_name%foo".encode("U16")

    header_data = struct.pack(header_format, car_name, player_name, 1, 1, info, track_name)
    sock.sendto(header_data, (address, port))


def transmit_data(address, port):
    # Transmit header
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    path = Path(__file__).parent / "assetto_corsa_network_capture_monza.pcap"
    file_capture = pyshark.FileCapture(str(path.absolute()))
    i = 0
    for pkt in file_capture:
        sock.sendto(bytearray.fromhex(pkt.data.data), (address, port))
        print("Transmit to {}:{} packet[{}]".format(address, port, i))
        i = i+1
        time.sleep(0.01)


def run_mock():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 20000))

    while True:
        address, port = wait_for_first_handshake(sock)
        transmit_header(sock, address, port)
        wait_for_second_handshake(sock)
        _thread.start_new_thread(transmit_data, (address, port))


if __name__ == "__main__":
    run_mock()
