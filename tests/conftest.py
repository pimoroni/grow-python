"""Test configuration.
These allow the mocking of various Python modules
that might otherwise have runtime side-effects.
"""
import sys

import mock
import pytest
from i2cdevice import MockSMBus


class SMBusFakeDevice(MockSMBus):
    def __init__(self, i2c_bus):
        MockSMBus.__init__(self, i2c_bus)
        self.regs[0x00:0x01] = 0x0f, 0x00


@pytest.fixture(scope='function', autouse=True)
def cleanup():
    yield None
    try:
        del sys.modules['grow']
    except KeyError:
        pass
    try:
        del sys.modules['grow.moisture']
    except KeyError:
        pass
    try:
        del sys.modules['grow.pump']
    except KeyError:
        pass


@pytest.fixture(scope='function', autouse=False)
def GPIO():
    """Mock RPi.GPIO module."""
    GPIO = mock.MagicMock()
    # Fudge for Python < 37 (possibly earlier)
    sys.modules['RPi'] = mock.Mock()
    sys.modules['RPi'].GPIO = GPIO
    sys.modules['RPi.GPIO'] = GPIO
    yield GPIO
    del sys.modules['RPi']
    del sys.modules['RPi.GPIO']


@pytest.fixture(scope='function', autouse=False)
def spidev():
    """Mock spidev module."""
    spidev = mock.MagicMock()
    sys.modules['spidev'] = spidev
    yield spidev
    del sys.modules['spidev']


@pytest.fixture(scope='function', autouse=False)
def smbus():
    """Mock smbus module."""
    smbus = mock.MagicMock()
    smbus.SMBus = SMBusFakeDevice
    sys.modules['smbus'] = smbus
    yield smbus
    del sys.modules['smbus']


@pytest.fixture(scope='function', autouse=False)
def atexit():
    """Mock atexit module."""
    atexit = mock.MagicMock()
    sys.modules['atexit'] = atexit
    yield atexit
    del sys.modules['atexit']
