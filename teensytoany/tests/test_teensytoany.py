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


class FakeSerial:
    """Hands back one scripted chunk per read_until call, then nothing."""

    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.written = []
        self.flushes = 0
        self.in_waiting = 0

    def write(self, data):
        self.written.append(data)

    def read_until(self, expected=b'\n', size=None):  # pylint: disable=unused-argument
        return self.chunks.pop(0) if self.chunks else b''

    def reset_input_buffer(self):
        self.flushes += 1

    def close(self):
        pass


@pytest.fixture(name='make_teensy')
def fixture_make_teensy(monkeypatch):
    # Resynchronizing waits for the port to go quiet; there is nothing to wait
    # for here.
    monkeypatch.setattr('teensytoany.teensytoany.sleep', lambda seconds: None)

    def make_teensy(chunks, version='0.22.0'):
        teensy = TeensyToAny(open=False)
        # pylint: disable=protected-access
        teensy._serial = FakeSerial(chunks)
        teensy._version = version
        return teensy

    return make_teensy


def test_read_finishes_reply_cut_off_by_late_wakeup(make_teensy):
    teensy = make_teensy([b'0', b' 0x1840\n'])
    # pylint: disable=protected-access
    assert teensy._read() == '0 0x1840\n'


def test_read_leaves_next_reply_in_buffer(make_teensy):
    teensy = make_teensy([b'0 1\n', b'0 2\n'])
    # pylint: disable=protected-access
    assert teensy._read() == '0 1\n'
    assert teensy._serial.chunks == [b'0 2\n']


def test_read_returns_partial_reply_when_nothing_more_arrives(make_teensy):
    teensy = make_teensy([b'0', b''])
    # pylint: disable=protected-access
    assert teensy._read() == '0'


def test_ask_returns_own_value_after_late_wakeup(make_teensy):
    teensy = make_teensy([b'0', b' 0x1840\n'])
    # pylint: disable=protected-access
    assert teensy._ask('i2c_read_uint16 0x92 0x0') == '0x1840'
    assert teensy._serial.written == [b'i2c_read_uint16 0x92 0x0\n']
    assert teensy._serial.flushes == 0


@pytest.mark.parametrize('chunks', [
    [b''],          # nothing within the timeout
    [b'0', b''],    # part of a reply, and nothing more
    [b'\n'],        # the end of another command's reply
    [b'FC0\n'],     # the value of another command's reply
], ids=['empty', 'incomplete', 'stray-newline', 'stray-value'])
def test_ask_resynchronizes_after_bad_reply(make_teensy, chunks):
    teensy = make_teensy(chunks + [b'0 0.22.0\n'])
    with pytest.raises(teensytoany.TeensyToAnyReplyError, match='back in step') as error:
        # pylint: disable=protected-access
        teensy._ask('gpio_digital_read 22')
    assert isinstance(error.value, RuntimeError)
    # pylint: disable=protected-access
    assert teensy._serial.written == [b'gpio_digital_read 22\n', b'version\n']
    assert teensy._serial.flushes == 1


def test_ask_device_error_does_not_resynchronize(make_teensy):
    teensy = make_teensy([b'5\n'])
    with pytest.raises(RuntimeError, match='Error Code 5') as error:
        # pylint: disable=protected-access
        teensy._ask('i2c_read_uint16 0x92 0x0')
    assert not isinstance(error.value, teensytoany.TeensyToAnyReplyError)
    # pylint: disable=protected-access
    assert teensy._serial.flushes == 0


def test_ask_says_to_power_cycle_when_resync_fails(make_teensy):
    # Every version check gets some other command's reply.
    teensy = make_teensy([b'\n'] + [b'0 0x1840\n'] * 5)
    with pytest.raises(teensytoany.TeensyToAnyReplyError, match='power cycle'):
        # pylint: disable=protected-access
        teensy._ask('gpio_digital_read 22')
    # pylint: disable=protected-access
    assert teensy._serial.flushes == 5


def test_resync_accepts_any_version_while_opening(make_teensy):
    teensy = make_teensy([b'\n', b'0 0.9.0\n'], version=None)
    with pytest.raises(teensytoany.TeensyToAnyReplyError, match='back in step'):
        # pylint: disable=protected-access
        teensy._ask('version')
