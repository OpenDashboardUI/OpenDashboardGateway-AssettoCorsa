#!/usr/bin/env python3

from .utils import *
from .gateway import run_cli_gateway
from .gateway_ui import run_gui_gateway


import sys
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="GUI and CLI to forward AssettoCorsa telemetry data to OpenDashboard.")
    parser.add_argument("--cli", action="store_true",
                        help="Run headless CLI version instead of GUI.")
    parser.add_argument("-s", "--source", dest="source", default="127.0.0.1:9666",
                        help="Source IP address and port of AssettoCorsa (e.g. 127.0.0.1:9666).")
    parser.add_argument("-d", "--destination", dest="destination", default="127.0.0.1:50000",
                        help="Destination IP address and port of OpenDashboard (e.g. 127.0.0.1:50000).")
    args = parser.parse_args()

    if not validate_address_with_port(args.source):
        print("Invalid parameter: Source address '{}' has wrong format.".format(args.source))
        sys.exit(-1)

    if not validate_address_with_port(args.destination):
        print("Invalid parameter: Source address '{}' has wrong format.".format(args.destination))
        sys.exit(-1)

    return args


def get_address_and_port(address_port_string: str) -> tuple:
    address_port_splitted = address_port_string.split(":")
    return address_port_splitted[0], int(address_port_splitted[1])


def main():
    args = parse_args()

    if args.cli:
        run_cli_gateway(get_address_and_port(args.source), get_address_and_port(args.destination))
    else:
        run_gui_gateway()


if __name__ == "__main__":
    main()




