import re

address_reg_ex = \
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
address_with_port_reg_ex = \
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):\d{1,5}$"


def validate_address(address) -> bool:
    match = re.fullmatch(address_reg_ex, address)
    return bool(match)


def validate_address_with_port(address_with_port) -> bool:
    match = re.fullmatch(address_with_port_reg_ex, address_with_port)
    return bool(match)