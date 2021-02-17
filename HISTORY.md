# History

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
