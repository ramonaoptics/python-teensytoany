from .teensytoany import TeensyToAny

__all__ = ['TeensyHBridge']


class TeensyHBridge():
    def __init__(self, *,
                 open=True, start_poweroff=True, **kwargs):
        """Open an H Bridge switch controlled by a Teensy microcontroller.

        Parameters
        ----------

        start_poweroff: bool
            If ``True``, the device will set the power to the off state upon
            startup. If ``False`` the device will set the power to the on
            state upon startup.

        **kwargs:
            Additional keyword arguments are passed to the ``TeensyToAny``
            constructor.

        """
        # auto_poweroff is used in the destructor. create it first
        # initialize other used variables to safe values
        self.auto_poweroff = True
        self._teensy = None
        # registries are set up to work with these two pins
        self.pin_number_a = 7
        self.pin_number_b = 8
        # this seems to be the minimum frequency we can set the pins to.
        self.poweron_frequency = 0x900

        self._teensy = TeensyToAny(open=open, **kwargs)
        if open:
            self.open(start_poweroff=start_poweroff)

    def poweron(self):
        """Turn the power outlet on.

        The outlets denoted ``Nominally Off`` will turn **on**.

        The outlets denoted ``Nominally On`` will turn **off**.
        """
        self._teensy._ask(f"analog_write_resolution 8")
        self._teensy._ask(f"analog_write_frequency {self.pin_number_a} {self.poweron_frequency}")
        self._teensy._ask(f"analog_write {self.pin_number_a} 128")

        base = 0x403DC000  # Submodule 1
        # using timer FlexPWM1.3 - for pins 7 and 8
        value_register_1 = base + 0x12E
        value_register_4 = base + 0x13A
        value_register_5 = base + 0x13E
        master_control_register = base + 0x188
        control_register = base + 0x126

        # from imxrt.h
        FLEXPWM_SMCTRL_FULL = 1 << 10

        def FLEXPWM_MCTRL_CLDOK(mask):
            return (mask & 0x0F) << 4

        def FLEXPWM_MCTRL_LDOK(mask):
            return mask & 0x0F

        def FLEXPWM_MCTRL_RUN(mask):
            return (mask & 0x0F) << 8

        def str2hex(s):
            return int(s, 16)

        def float2hex(s):
            return hex(int(s))

        submodule = 3  # this is the submodule of the submodule
        mask = 1 << submodule

        self._teensy._ask(f"register_write_uint16 {master_control_register} {FLEXPWM_MCTRL_CLDOK(mask)}")
        # set the LDMOD bit - Buffered registers of this submodule are loaded and
        # take effect immediately upon MCTRL[LDOK] being set.
        self._teensy._ask(f"register_write_uint16 {control_register} {FLEXPWM_SMCTRL_FULL | 4}")

        value_1 = self._teensy._ask(f"register_read_uint16 {value_register_1}")
        new_value_4 = float2hex((str2hex(value_1) // 2))
        self._teensy._ask(f"register_write_uint16 {value_register_4} {new_value_4}")
        new_value_5 = float2hex((str2hex(value_1)))
        self._teensy._ask(f"register_write_uint16 {value_register_5} {new_value_5}")

        self._teensy._ask(f"register_write_uint16 {master_control_register} "
                          f"{FLEXPWM_MCTRL_LDOK(mask) | FLEXPWM_MCTRL_RUN(mask)}")
        self._teensy._ask(f"analog_write {self.pin_number_b} 128")

    def poweroff(self):
        # pins will go HIGH once set to output tie power to ground and bypassing pdlc
        self._teensy.gpio_pin_mode(self.pin_number_a, 'OUTPUT')
        self._teensy.gpio_pin_mode(self.pin_number_b, 'OUTPUT')

    def open(self, *, start_poweroff=True):
        """Open the device.

        Parameters
        ----------

        start_poweroff: bool
            If ``True``, the device will set the power to the off state upon
            startup. If ``False`` the device will set the power to the on
            state upon startup.

        """
        self._teensy.open()
        self._teensy.gpio_pin_mode(self.pin_number_a, 'OUTPUT')
        self._teensy.gpio_pin_mode(self.pin_number_b, 'OUTPUT')
        self._teensy.gpio_digital_write(self.pin_number_a, 'HIGH')
        self._teensy.gpio_digital_write(self.pin_number_b, 'HIGH')
        if start_poweroff:
            self.poweroff()
        else:
            self.poweron()

    def __del__(self):
        self.close()

    def close(self):
        if self._teensy is not None:
            if self.auto_poweroff:
                if self._teensy._serial is not None:
                    self.poweroff()
            self._teensy.close()
