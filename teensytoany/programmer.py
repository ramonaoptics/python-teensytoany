import click
import teensytoany

@click.command()
@click.option(
    '--serial-number',
    default=None,
    help=(
        'Serial number of the Teensy device to program. '
        'If not provided and only one Teensy device found, '
        'it will be programmed.'
    )
)
# Create an option with 2 valid inputs TEENSY40 and TEENSY32
@click.option(
    '--mcu',
    type=click.Choice(['TEENSY40', 'TEENSY32']),
    default='TEENSY40',
    help='Microcontroller to program.'
)
@click.option(
    '--firmware-version',
    default=None,
    type=str,
    help='Firmware version to program. If not provided, the latest version will be programmed.'
)
# Make the epligue print the version
@click.version_option(teensytoany.__version__)
def teensytoany_programmer(serial_number=None, mcu='TEENSY40', firmware_version=None):
    """Program a Teensy device with a given firmware version"""
    print(f'Programming irmware version {mcu} {firmware_version}', end='')
    teensytoany.TeensyToAny.program_firmware(serial_number, mcu=mcu, version=firmware_version)
    teensy = teensytoany.TeensyToAny(serial_number)
    print(f"TeensyToAny version: {teensy.version}")
    print(f"TeensyToAny serial_number: {teensy.serial_number}")
    teensy.close()

if  __name__ == '__main__':
    teensytoany_programmer()
