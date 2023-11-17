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
    for module in ['grow', 'grow.moisture', 'grow.pump']:
        try:
            del sys.modules[module]
        except KeyError:
            continue


@pytest.fixture(scope='function', autouse=False)
def GPIO():
    """Mock gpiod module."""
    gpiod = mock.MagicMock()
    sys.modules['gpiod'] = gpiod
    yield gpiod
    del sys.modules['gpiod']


@pytest.fixture(scope='function', autouse=False)
def spidev():
    """Mock spidev module."""
    spidev = mock.MagicMock()
    sys.modules['spidev'] = spidev
    yield spidev
    del sys.modules['spidev']


@pytest.fixture(scope='function', autouse=False)
def smbus2():
    """Mock smbus2 module."""
    smbus2 = mock.MagicMock()
    smbus2.SMBus = SMBusFakeDevice
    sys.modules['smbus2'] = smbus2
    yield smbus2
    del sys.modules['smbus2']


@pytest.fixture(scope='function', autouse=False)
def atexit():
    """Mock atexit module."""
    atexit = mock.MagicMock()
    sys.modules['atexit'] = atexit
    yield atexit
    del sys.modules['atexit']
