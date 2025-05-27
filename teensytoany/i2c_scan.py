import click
import teensytoany


@click.command(epilog=f"Version {teensytoany.__version__}")
@click.option('--serial-number', '-s', type=str, default=None,
              help='Serial number of the Teensy device.')
@click.option('--interface', '-i', type=int, default=0,
              help='I2C interface to use (0 for I2C, 1 for I2C1).')
@click.option('--seven-bit-mode', '-7', is_flag=True, default=False,
              help='Report addresses in 7-bit mode instead of 8-bit mode.')
@click.version_option(teensytoany.__version__)
def main(
    serial_number=None,
    interface=0,
    seven_bit_mode=False,
):
    i2c_scan(
        serial_number=serial_number,
        interface=interface,
        seven_bit_mode=seven_bit_mode,
    )


def i2c_scan(serial_number=None, interface=0, seven_bit_mode=False):
    from teensytoany import TeensyToAny  # noqa
    teensy = TeensyToAny(serial_number=serial_number)

    for address_7bit in range(1, 128):
        address = address_7bit << 1
        try:
            if interface == 0:
                teensy.i2c_ping(address=address)
            elif interface == 1:
                teensy.i2c_1_ping(address=address)
            if seven_bit_mode:
                print(f"Found device at address 0x{address_7bit:02X}")
            else:
                print(f"Found device at address 0x{address:02X}")
        finally:
            pass

    teensy.close()


if __name__ == "__main__":
    main()
