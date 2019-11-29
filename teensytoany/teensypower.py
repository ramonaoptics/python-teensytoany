from teensytoany import TeensyToAny

__all__ = ['TeensyPower']


class TeensyPower():
    def __init__(self, pin_number=13, **kwargs):
        """Open an AC power switch controlled by a Teensy microcontroller.

        Parameters
        ==========
        pin_number:
            The pin number on the teensy that is used to control the switch.

        **kwargs:
            Additional keyword arguments are passed to the ``TeensyToAny``
            constructor.

        """
        self._teensy = TeensyToAny(**kwargs)
        self.pin_number = pin_number
        self._teensy.gpio_pin_mode(self.pin_number, 'OUTPUT')
        self.poweroff()

        self.auto_poweroff = True

    def __del__(self):
        self._close()

    def _close(self):
        if self.auto_poweroff:
            self.poweroff()
        self._teensy.close()

    def poweron(self):
        """Turn the power outlet on.

        The outlets denoted `Nominally Off` will turn **on**.

        The outlets denoted `Nominally On` will turn **off**.
        """
        self._teensy.gpio_digital_write(self.pin_number, 1)

    def poweroff(self):
        """Turn the power outlet on.

        The outlets denoted `Nominally Off` will turn **off**.

        The outlets denoted `Nominally On` will turn **on**.
        """
        self._teensy.gpio_digital_write(self.pin_number, 0)
