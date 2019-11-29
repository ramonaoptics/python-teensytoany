import teensytoany
import serial

class TeensyPower():
    def __init__(self, pin_number=13):
        self._teensy = teensytoany.TeensyToAny()
        self.pin_number = pin_number
        self._teensy.gpio_pin_mode(self.pin_number, 'OUTPUT')
        self.poweroff()

    def poweron(self):
        self._teensy.gpio_digital_write(self.pin_number, 1)

    def poweroff(self):
        self._teensy.gpio_digital_write(self.pin_number, 0)
