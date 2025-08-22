import pytest

import teensytoany
from teensytoany import TeensyToAny


def test_project_import():
    assert teensytoany.__version__
    assert teensytoany.TeensyToAny


@pytest.mark.hardware
def test_nop():
    with TeensyToAny() as t:
        t.nop()


@pytest.mark.hardware
@pytest.mark.parametrize("i", range(256, 2048, 256))
def test_nop_buffer_size(i):
    # We shouldn't fail with up to 2048 bytes of input
    with TeensyToAny() as t:
        # pylint: disable=protected-access
        t._ask("nop" + " " * (2048 - len("nop\n") - i))


@pytest.mark.hardware
@pytest.mark.parametrize("i", range(2048, 8096 + 1, 2048))
def test_nop_buffer_size_fail(i):
    with TeensyToAny() as t:
        # We should fail with more than 2048 bytes of input
        with pytest.raises(Exception):
            # pylint: disable=protected-access
            t._ask("nop" + " " * (i + 1 - len("nop\n")))
