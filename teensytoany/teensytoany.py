from typing import Sequence

from serial import Serial, LF
from serial.tools.list_ports import comports
from os import strerror
from distutils.version import LooseVersion as Version

__all__ = ['TeensyToAny', 'known_devices', 'known_serial_numbers']


known_devices = [
    # Example device structure
    # These include useful information about the hardware that is created and
    # burned in with the serial numbers.
    # Since the same VID/PID can be assigned to multiple devices,
    # We must log the individual serial numbers to know what they all do.
    {
        'serial_number': '4725230',
        'device_name': 'teensytoany',
    },
    {
        'serial_number': '5032260',
        'device_name': 'teensytoany',
    },
    {
        'serial_number': '4725070',
        'device_name': 'teensytoany',
    },
    {
        'serial_number': '4726520',
        'device_name': 'teensytoany',
    },
    {
        'serial_number': '5032540',
        'device_name': 'teensytoany',
    },
    {
        'serial_number': '4728790',
        'device_name': 'teensytoany',
    },
    {
        'serial_number': '5955040',
        'device_name': 'teensytoany',
    },
]

known_serial_numbers = [
    d['serial_number']
    for d in known_devices
]


class TeensyToAny:
    # I've noticed that this is extremely slow. Simply asking the device
    # for the version number seems to take 100 ms exactly.

    # %timeit teensytoany._ask('version')
    # 101 ms

    # This was due to it timeing out on the reads instead of stopping when it
    # received the newline character.

    # Currently, the roundtrip time is about 6ms. This is with version 0.0.1-2
    # of the firmware.
    VID_PID_s = [
        (0x16C0, 0x0483),
    ]

    _known_device = known_devices
    _known_serial_numbers = known_serial_numbers

    @staticmethod
    def find(serial_numbers=None):
        """Find all the serial ports that are associated with debuggers.

        Parameters
        ----------
        serial_numbers: list of str, or None
            If provided, will only match the serial numbers that are contained
            in the provided list.

        Returns
        -------
        devices: list of serial devices
            List of serial devices

        Note
        ----
        If a list of serial numbers is not provided, then this function may
        match Teensy 3.1/3.2 microcontrollers that are connected to the
        computer but that may not be associated with the TeensyToAny boards.

        """
        pairs = TeensyToAny._device_serial_number_pairs(
            serial_numbers=serial_numbers)
        devices, _ = zip(*pairs)
        return devices

    @staticmethod
    def list_all_serial_numbers(serial_numbers=None):
        """Find all the currently connected TeensyToAny serial numbers.

        Parameters
        ----------
        serial_numbers: list of str, or None
            If provided, will only match the serial numbers that are contained
            in the provided list.

        Returns
        -------
        serial_numbers: list of serial numbers
            List of connected serial numbers.

        Note
        ----
        If a list of serial numbers is not provided, then this function may
        match Teensy 3.1/3.2 microcontrollers that are connected to the
        computer but that may not be associated with the TeensyToAny boards.

        """
        pairs = TeensyToAny._device_serial_number_pairs(
            serial_numbers=serial_numbers)
        _, serial_numbers = zip(*pairs)
        return serial_numbers

    @staticmethod
    def _device_serial_number_pairs(serial_numbers=None):
        com = comports()
        pairs = [
            (c.device, c.serial_number)
            for c in com
            if ((c.vid, c.pid) in TeensyToAny.VID_PID_s and
                (serial_numbers is None or
                 c.serial_number in serial_numbers))
        ]
        if len(pairs) == 0:
            raise RuntimeError(
                "Could not find any device for provided serial number: "
                f"{serial_numbers}.")
        return pairs

    def __init__(self, serial_number=None, *,
                 baudrate=115200, timeout=0.1, open=True):
        """A class to control the TeensyToAny Debugger.

        Parameters
        ----------
        serial_number: optional
            If provided, will attempt to open the specified serial number

        """

        self._requested_serial_number = serial_number
        self._baudrate = baudrate
        self._timeout = timeout
        self._serial = None
        if open:
            self.open()

    def open(self):
        if self._requested_serial_number is None:
            serial_numbers = self._known_serial_numbers
        else:
            serial_numbers = [self._requested_serial_number]

        port, found_serial_number = self._device_serial_number_pairs(
            serial_numbers=serial_numbers)[0]

        self._serial = Serial(
            port=port, baudrate=self._baudrate, timeout=self._timeout)
        self.serial_number = found_serial_number

    def close(self):
        if self._serial is not None:
            self._serial.close()

        self._serial = None
        self.serial_number = None

    def __del__(self):
        # Do we want to call close on this delete instance????
        self.close()

    def _write(self, data) -> None:
        """Write data to the port.

        If it is a string, encode it as 'utf-8'.
        """

        if self._serial is None:
            raise RuntimeError("Device must be opened first")

        if isinstance(data, str):
            data = (data + '\n').encode('utf-8')
        self._serial.write(data)

    def _read(self, *, size=1024, decode=True) -> str:
        """Read data from the serial port.

        Returns
        -------
        data: bytes or string
            string of data read.

        """
        if self._serial is None:
            raise RuntimeError("Device must be opened first")

        data = self._serial.read_until(LF, size=size)
        if decode:
            return data.decode()
        else:
            return data

    def _ask(self, data, *, size=1024, decode=True) -> str:
        self._write(data)
        returned = self._read(size=size, decode=decode)

        returned_list = returned.split(' ', 1)
        error = returned_list[0]
        message = None if len(returned_list) == 1 else returned_list[1]
        error = int(error)
        if error != 0:
            if message is None:
                message = strerror(error)
            raise RuntimeError(f"Responded with Error Code {error}: {message}")

        if message is not None:
            message = message.strip()
        return message

    def i2c_init(self, baud_rate: int=100_100, timeout=200_000, register_space=1):
        cmd = f"i2c_init {baud_rate:d} {timeout:d} {register_space:d}"
        self._ask(cmd)

    def i2c_read_uint8(self, address: int, register_address: int):
        cmd = f"i2c_read_uint8 0x{address:02x} 0x{register_address:x}"
        returned = self._ask(cmd)
        return int(returned, base=0)

    def i2c_read_uint16(self, address: int, register_address: int):
        cmd = f"i2c_read_uint16 0x{address:02x} 0x{register_address:x}"
        returned = self._ask(cmd)
        return int(returned, base=0)

    def i2c_write_uint8(self, address: int, register_address: int, data: int):
        data = data & 0xFF
        cmd = f"i2c_write_uint8 0x{address:02x} 0x{register_address:x} 0x{data:x}"
        self._ask(cmd)

    def i2c_write_uint16(self, address: int, register_address: int, data: int):
        data = data & 0xFFFF
        cmd = f"i2c_write_uint16 0x{address:02x} 0x{register_address:x} 0x{data:x}"
        self._ask(cmd)

    def i2c_write_read(self,
                       address: int,
                       data: Sequence,
                       num_bytes: int) -> Sequence:
        if len(data) != 2:
            raise ValueError("data must be of length 2")
        if num_bytes not in [1, 2]:
            raise ValueError("Can only read 1 or 2 bytes at a time.")

        register_address = int.from_bytes(
            data, byteorder='big', signed=False)
        if num_bytes == 2:
            returned = self._ask(
                f"i2c_read_uint16 0x{address:02x} 0x{register_address:04x}")
        else:
            returned = self._ask(
                f"i2c_read_uint8 0x{address:02x} 0x{register_address:04x}")
        register_data = int(returned, base=0)
        # The other I2C function has this interface
        return int.to_bytes(
            int(register_data),
            length=num_bytes, byteorder='big',
            signed=False)

    def i2c_write_payload(self, address: int, register_address: int, payload: Sequence) -> None:

        if self.version >= Version("0.0.14"):
            data =  ' '.join([f"0x{val:02x}" for val in payload])
            cmd = f"i2c_write_payload 0x{address:02x} 0x{register_address:02x} {data}"
            self._ask(cmd)

        else:
            if len(payload) == 1:
                # Trying to write the network chips
                data = int(payload[0])
                self._ask(
                    f"i2c_write_no_register_uint8 0x{address:02x} 0x{data:02x}")
            elif len(payload) == 3:
                # uint8
                register_address = int.from_bytes(
                    payload[0:2], byteorder='big', signed=False)
                data = int.from_bytes(
                    payload[2:3], byteorder='big', signed=False)
                self._ask(
                    f"i2c_write_uint8 "
                    f"0x{address:02x} 0x{register_address:04x} 0x{data:02x}")
            elif len(payload) == 4:
                register_address = int.from_bytes(
                    payload[0:2], byteorder='big', signed=False)
                data = int.from_bytes(
                    payload[2:4], byteorder='big', signed=False)
                self._ask(
                    f"i2c_write_uint16 "
                    f"0x{address:02x} 0x{register_address:04x} 0x{data:04x}")
            else:
                raise NotImplementedError()
        

    def i2c_read_payload(self, address: int, register_address: int, num_bytes: int) -> Sequence:

        if self.version >= Version("0.0.14"):
            cmd = f"i2c_read_payload 0x{address:02x} 0x{register_address:02x} {num_bytes}"
            returned = self._ask(cmd)
            register_data = [int(val, base=0) for val in returned.split()] # returns big endian
            return register_data

        else:
            if num_bytes != 1:
                raise NotImplementedError()
            returned = self._ask(f"i2c_read_no_register_uint8 0x{address:02x}")
            register_data = int(returned, base=0)
            return int.to_bytes(
                int(register_data),
                length=num_bytes, byteorder='big',
                signed=False)
    
    def gpio_digital_write(self, pin, value):
        """Call the ardunio DigitalWrite function.


        Parameters
        ----------
        pin: int
            Pin number to control.
        value: 0, 1, "HIGH", "LOW"
            Value to assign to the pin

        """
        self._ask(f"gpio_digital_write {pin} {value}")

    def gpio_pin_mode(self, pin, mode):
        """Call the arduino PinMode function.

        Parameters
        ----------
        pin: int
            Pin number to control.
        mode: 0, 1, "INPUT", "OUTPUT"
            Mode which to set the pin to.
        """
        self._ask(f"gpio_pin_mode {pin} {mode}")

    def gpio_digital_read(self, pin):
        """Call the arduino DigitalRead function.

        Parameters
        ----------
        pin: int
            Pin number to read.

        Returns
        -------
        value: int, 0, 1
            Read value.

        """
        returned = self._ask(f"gpio_digital_read {pin}")
        return bool(int(returned, base=0))

    @property
    def version(self):
        return self._ask("version")

    def spi_begin(self):
        self._ask("spi_begin")

    def spi_end(self):
        self._ask("spi_end")

    def spi_set_miso(self, pin):
        self._ask(f"spi_set_miso {pin}")

    def spi_set_mosi(self, pin):
        self._ask(f"spi_set_mosi {pin}")

    def spi_set_sck(self, pin):
        self._ask(f"spi_set_sck {pin}")

    def spi_settings(self,
                     frequency: int=1_000_000,
                     bit_order: str='MSBFIRST',
                     data_mode: str='SPI_MODE0'):
        """

        Parameters
        ----------
        bit_order: 'MSBFIRST' or 'LSBFIRST'
        data_mode: 'SPI_MODE0', 'SPI_MODE1', 'SPI_MODE2', or 'SPI_MODE3'

        References
        ----------
          1. https://www.pjrc.com/teensy/td_libs_SPI.html
          2. https://www.arduino.cc/en/Reference/SPISetDataMode

        """
        return self._ask(f"spi_settings {frequency} {bit_order} {data_mode}")

    def spi_begin_transaction(self):
        return self._ask("spi_begin_transaction")

    def spi_end_transaction(self):
        return self._ask("spi_end_transaction")

    def spi_transfer(self, data):
        return self._ask(f"spi_transfer {data}")

    def spi_transfer_bulk(self, data):
        return self._ask("spi_transfer_bulk " + " ".join(str(d) for d in data))

    def analog_write_frequency(self, pin: int, frequency: int):
        frequency = int(frequency)
        self._ask(f"analog_write_frequency {pin} {frequency}")

    def analog_write_resolution(self, resolution: int):
        resolution = int(resolution)
        self._ask(f"analog_write_resolution {resolution}")

    def analog_write(self, pin: int, value: int):
        # https://www.arduino.cc/reference/en/language/functions/analog-io/analogwrite/
        value = int(value)
        self._ask(f"analog_write {pin} {value}")
