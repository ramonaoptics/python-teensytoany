import os
import subprocess
from pathlib import Path
from threading import RLock
from time import sleep
from warnings import warn

import pandas as pd
from multiuserfilelock import MultiUserFileLock, Timeout, tmpdir

from .teensytoany import TeensyToAny, known_serial_numbers
from .utils import with_thread_lock

locks_dir = tmpdir / 'teensytoany'


class PlateTapper:
    _ACTUATOR_A_CONTROL_1_PIN = 13
    _ACTUATOR_B_CONTROL_1_PIN = 14
    _PWM_A_PIN = 18
    _PWM_B_PIN = 19
    _VSENSE_PIN = 17
    # _MINIMUM_PWM_DUTY_CYCLE = 156

    def __init__(self, serial_number: str=None,):
        self._teensy = None
        self._serial_number = serial_number
        self._use_lock = True
        self._thread_lock = RLock()
        self.open(_stacklevel_increment=2)

    @with_thread_lock
    def open(self, *, _stacklevel_increment=1) -> None:
        """Open the device for communication.

        See also
        --------
        close
        """
        serial_number = self._serial_number
        if serial_number is None:
            serial_number = TeensyToAny.list_all_serial_numbers(
                known_serial_numbers, device_name="PlateTapper"
            )[0]

        if serial_number not in known_serial_numbers:
            warn(f"The serial number {serial_number} is not known to Ramona Optics.",
                 stacklevel=2 + _stacklevel_increment)
        else:
            self._serial_number = serial_number

        self._lock_acquire(serial_number)
        try:
            self._teensy = TeensyToAny(serial_number)
        except Exception as e:
            self._lock_release()
            raise e

        self._teensy.gpio_pin_mode(self._ACTUATOR_A_CONTROL_1_PIN, "OUTPUT")
        self._teensy.gpio_pin_mode(self._ACTUATOR_B_CONTROL_1_PIN, "OUTPUT")
        self._teensy.gpio_pin_mode(self._VSENSE_PIN, "INPUT")
        self._teensy.gpio_pin_mode(self._PWM_A_PIN, "OUTPUT")
        self._teensy.gpio_pin_mode(self._PWM_B_PIN, "OUTPUT")

        self._teensy.gpio_digital_write(self._ACTUATOR_A_CONTROL_1_PIN, 1)
        self._teensy.gpio_digital_write(self._ACTUATOR_B_CONTROL_1_PIN, 1)

        self._teensy.analog_write_frequency(self._PWM_A_PIN, 100000)

        if serial_number in known_devices.index:
            self._has_direct_tap = known_devices.loc[serial_number].direct_tap
            self._has_dampened_tap = known_devices.loc[serial_number].dampened_tap
        else:
            # By default enable both....
            self._has_direct_tap = True
            self._has_dampened_tap = True

    @property
    def has_direct_tap(self):
        return self._has_direct_tap

    @property
    def has_dampened_tap(self):
        return self._has_dampened_tap

    def close(self) -> None:
        """Close the device for communication.

        See also
        --------
        open
        """
        if self._teensy is not None:
            self._teensy.gpio_digital_write(self._ACTUATOR_A_CONTROL_1_PIN, 0)
            self._teensy.gpio_digital_write(self._ACTUATOR_B_CONTROL_1_PIN, 0)
            self._teensy.analog_write(self._PWM_A_PIN, 0)
            self._teensy.analog_write(self._PWM_B_PIN, 0)
            self._teensy.close()
            self._teensy = None
        self._lock_release()

    @property
    def firmware_version(self):
        return self._teensy.version

    @staticmethod
    def _make_lock(serial_number,
                   group='dialout',
                   chmod=0o666) -> MultiUserFileLock:
        # 0o666 is chosen because that is the default permission set
        # by most people installing the teensy by default
        # https://www.pjrc.com/teensy/loader_linux.html
        # Check the udev rules file
        unique_plate_tapper_locktxt = locks_dir / f"plate_tapper_{serial_number}.lock"
        # lock will only be called if the device is closed
        # (when isOpen is called).
        return MultiUserFileLock(unique_plate_tapper_locktxt,
                                 group=group, chmod=chmod,
                                 timeout=0.001)

    def _lock_acquire(self, serial_number) -> None:
        if not self._use_lock:
            # If the user isn't requesting to use a lock, simply return
            # immediately
            return
        lock = self._make_lock(serial_number)
        try:
            lock.acquire()
        except Timeout:
            raise RuntimeError(
                "This PlateTapper system has been opened already. "
                "Establish a new connection by closing this system in the other program."
            )

        # Only assign the new lock object after it has been acquired.
        self._lock = lock

    def _lock_release(self) -> None:
        # During garbage collection, the serial
        # device might have been closed first.
        # Make sure we clean up the lock in either case.
        if self._lock is not None:
            self._lock.release()
            self._lock = None

    @property
    def serial_number(self):
        return self._serial_number

    @property
    def tap_duration(self):
        "The default tap duration. Tuned to get the maximum power delivery."
        # Through experiments we found that a tap duration of 0.1
        # was enough to fully extend the solenoid without energizing it
        # and thus heating it up for too long
        return 0.1

    @with_thread_lock
    def dampened_tap(self, strength=1., *, duration=None):
        """Deliver a single dampened tap."""
        if strength < 0 or strength > 1.:
            raise ValueError("strength must be between 0 and 1.")
        if duration is None:
            duration = self.tap_duration

        strength = 1.06 * strength * 100 + 150
        self._teensy.analog_pulse(
            self._PWM_B_PIN, strength, duration=duration
        )

    @with_thread_lock
    def direct_tap(self, strength=1., *, duration=None):
        """Deliver a single direct tap."""
        if strength < 0 or strength > 1.:
            raise ValueError("strength_percentage must be between 0 and 1.")
        if duration is None:
            duration = self.tap_duration
        strength = 1.06 * strength * 100 + 150
        self._teensy.analog_pulse(
            self._PWM_A_PIN, strength, duration=duration
        )

    @property
    def power_good(self):
        return self._teensy.gpio_digital_read(self._VSENSE_PIN)

    @staticmethod
    def reboot_stuck_device(serial_number=None, mcu=None):
        if mcu is None:
            if serial_number is not None:
                mcu = known_devices.loc[serial_number].mcu
            else:
                mcu = 'TEENSY40'

        cmd_list = [
            'teensy_loader_cli',
            '-b',
            '-s',
            f'--mcu={mcu}',
        ]

        if serial_number is not None and os.name != 'nt':
            # This feature needs
            # https://github.com/PaulStoffregen/teensy_loader_cli/pull/57
            cmd_list.append(f'--serial-number={serial_number}')

        # Acquire lock so that we don't destroy a user's running application.
        if serial_number is not None:
            lock = PlateTapper._make_lock(serial_number)
        else:
            # Dummy context manager
            lock = memoryview(b'')
        with lock:
            subprocess.check_call(cmd_list)
