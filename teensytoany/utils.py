import logging
import signal
import threading
from functools import wraps


class DelayedKeyboardInterrupt:
    def __enter__(self):
        self.signal_received = False
        self._is_main_thread = threading.current_thread() is threading.main_thread()
        if self._is_main_thread:
            # the signal api is only available to the main thread in python
            self.old_handler = signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig, frame):
        self.signal_received = (sig, frame)
        logging.debug('SIGINT received. Delaying KeyboardInterrupt.')

    def __exit__(self, type, value, traceback):
        # During the cleanup of objects, the signal handler of the main
        # Thread might have already been set to None or something
        if self._is_main_thread and self.old_handler is not None:
            signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received:
            self.old_handler(*self.signal_received)


def with_thread_lock(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        with self._thread_lock:
            # We only want to prevent interrupts after the
            # thread lock has been received. We want to be able
            # to kill the system in case of deadlock
            with DelayedKeyboardInterrupt():
                return func(self, *args, **kwargs)
    return wrapper
