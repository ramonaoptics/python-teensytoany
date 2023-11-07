# History

## 0.2.0 (2023-11-07)

* Add a `timeout` property to simplify modifying the command timeout.

## 0.1.0 (2023-09-29)

* Provide access the new `mcu` command that reveals the microcontroller used at
  the time of firmware programming.

* Provide an internal method that can be used by developers to update to the
  latest firmware.

## 0.0.34 (2023-08-26)

* Small fixup in how reading the Teensy's registers is done to ensure better
  forward compatibility.

## 0.0.33 (2023-08-26)

The following features require teensy-to-any version 0.0.23 or greater
* Add support for `gpio_digital_pulse`.
* Add support for `analog_pulse`.
* Add support for new `value` parameter for `gpio_pin_mode`.
* Add support to read the data returned from `spi_transfer_bulk`.

## 0.0.32 (2023-08-30)

* Address bugs in reading the values from Teensy's registers.

## 0.0.31 (2023-08-21)

* Add the ability to read and write to the teensy's registers.

## 0.0.30 (2023-04-03)

* Increase default timeout to 0.2 seconds from 0.1. This helps receive error
  messages from missed I2C communications.
* Return an error if no response is returned from a standard command indicating
  a timeout.

## 0.0.29 (2023-03-06)

* Try to avoid racy conditions in version reading
* Flush buffers upon startup to help with crash recovery.

## 0.0.28 (2023-03-04)

* Make the error message when no device is found more human friendly.

## 0.0.27 (2022-10-16)

* Use packaging instead of distutils for version identification

## 0.0.26 (2021-09-13)

* added function `spi_read_byte` enabling the user to read SPI register.

## 0.0.25 (2021-07-14)

* added function `analog_read` enabling the user to read analog signals.

## 0.0.24 (2021-06-03)

* added `i2c_read_payload and` `i2c_write_payload functions` which allows users to read and write a contiguous payload of bytes

## 0.0.23 (2021-02-13)

* Ensure compatibility with pyserial 3.X
* Power a ``start_poweroff`` parameter to ``TeensyPower`` to start the device
  in the on state.
* Added the ability to close and open the device without deleting the python
  object.

## 0.0.22 (2020-06-18)

* Added the ability to control a power switch that is connected to the
  nominally on port.

## 0.0.20 (2019-12-14)

* Added capabilities for SPI and Analog functions

## 0.0.16 (2019-11-30)

* `TeensyPower` destructor will not raise an error when the device had failed
   to open.

## 0.0.15 (2019-11-29)

* `TeensyPower` devices will automatically poweroff the output when
  closed.

## 0.0.14 (2019-11-29)

* Added the specialized `TeensyPower` driver.

## 0.0.13 (2019-11-20)

* Added a few more serial numbers to the `teensytoany.known_devices`

## 0.0.1 (2019-11-07)

* First release on PyPI.
