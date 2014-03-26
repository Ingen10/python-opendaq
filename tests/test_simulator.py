import pytest
from opendaq.common import mkcmd
from opendaq.simulator import DAQSimulator

ERROR_CMD = mkcmd(160, '')


@pytest.fixture
def daq():
    return DAQSimulator()


def test_set_led(daq):
    daq.write(mkcmd(18, 'B', 1))
    assert daq.read(5) == mkcmd(18, 'B', 1)
    assert daq.led_color == 1

    # invalid color
    daq.write(mkcmd(18, 'B', 4))
    assert daq.read(5) == ERROR_CMD
