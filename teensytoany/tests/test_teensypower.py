#!/usr/bin/env python3
# vim: set ts=8 sw=4 tw=0 et :
from teensytoany import TeensyPower
import pytest

def test_contructor_bad_device():
    with pytest.raises(RuntimeError, match="Could not find any device*"):
        _ = TeensyPower(serial_number='123213')
