# SPDX-FileCopyrightText: 2017 Carter Nelson for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ds18x20`
====================================================

Driver for Dallas 1-Wire temperature sensor.

* Author(s): Carter Nelson

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_DS18x20.git"

import time
from micropython import const
from adafruit_onewire.device import OneWireDevice

try:
    import typing  # pylint: disable=unused-import
    from typing_extensions import Literal
    from circuitpython_typing import WriteableBuffer
    from adafruit_onewire.bus import OneWireBus  # pylint: disable=ungrouped-imports
except ImportError:
    pass

_CONVERT = b"\x44"
_RD_SCRATCH = b"\xBE"
_WR_SCRATCH = b"\x4E"
_CONVERSION_TIMEOUT = const(1)
RESOLUTION = (9, 10, 11, 12)
# Maximum conversion delay in seconds, from DS18B20 datasheet.
_CONVERSION_DELAY = {9: 0.09375, 10: 0.1875, 11: 0.375, 12: 0.750}


class DS18X20:
    """Class which provides interface to DS18X20 temperature sensor

    :param  bus: The bus the DS18X20 is connected to
    :param int address: The device address.

    **Quickstart: Importing and using the device**

        Here is an example of using the :class:`DS18X20` class.
        First you will need to import the libraries to use the sensor

        .. code-block:: python

            import board
            from adafruit_onewire.bus import OneWireBus
            from adafruit_ds18x20 import DS18X20

        Once this is done you can define your :class:`adafruit_onewire.bus.OneWireBus`
        object and define your sensor object

        .. code-block:: python

            ow_bus = OneWireBus(board.D5)
            ds18 = DS18X20(ow_bus, ow_bus.scan()[0])

        Now you have access to the :attr:`temperature` attribute

        .. code-block:: python

            temperature = ds18.temperature

    """

    def __init__(self, bus: OneWireBus, address: int) -> None:
        if address.family_code in (0x10, 0x28):
            self._address = address
            self._device = OneWireDevice(bus, address)
            self._buf = bytearray(9)
            self._conv_delay = _CONVERSION_DELAY[12]  # pessimistic default
        else:
            raise ValueError("Incorrect family code in device address.")

    @property
    def temperature(self):
        """The temperature in degrees Celsius."""
        self._convert_temp()
        return self._read_temp()

    @property
    def resolution(self) -> Literal[9, 10, 11, 12]:
        """The programmable resolution. 9, 10, 11, or 12 bits."""
        return RESOLUTION[self._read_scratch()[4] >> 5 & 0x03]

    @resolution.setter
    def resolution(self, bits: Literal[9, 10, 11, 12]) -> None:
        if bits not in RESOLUTION:
            raise ValueError("Incorrect resolution. Must be 9, 10, 11, or 12.")
        self._buf[0] = 0  # TH register
        self._buf[1] = 0  # TL register
        self._buf[2] = RESOLUTION.index(bits) << 5 | 0x1F  # configuration register
        self._write_scratch(self._buf)

    def _convert_temp(self, timeout: int = _CONVERSION_TIMEOUT) -> float:
        with self._device as dev:
            dev.write(_CONVERT)
            start_time = time.monotonic()
            if timeout > 0:
                dev.readinto(self._buf, end=1)
                # 0 = conversion in progress, 1 = conversion done
                while self._buf[0] == 0x00:
                    if time.monotonic() - start_time > timeout:
                        raise RuntimeError(
                            "Timeout waiting for conversion to complete."
                        )
                    dev.readinto(self._buf, end=1)
        return time.monotonic() - start_time

    def _read_temp(self) -> float:
        # pylint: disable=invalid-name
        buf = self._read_scratch()
        if self._address.family_code == 0x10:
            if buf[1]:
                t = buf[0] >> 1 | 0x80
                t = -((~t + 1) & 0xFF)
            else:
                t = buf[0] >> 1
            return t - 0.25 + (buf[7] - buf[6]) / buf[7]
        t = buf[1] << 8 | buf[0]
        if t & 0x8000:  # sign bit set
            t = -((t ^ 0xFFFF) + 1)
        return t / 16

    def _read_scratch(self) -> bytearray:
        with self._device as dev:
            dev.write(_RD_SCRATCH)
            dev.readinto(self._buf)
        return self._buf

    def _write_scratch(self, buf: WriteableBuffer) -> None:
        with self._device as dev:
            dev.write(_WR_SCRATCH)
            dev.write(buf, end=3)

    def start_temperature_read(self) -> float:
        """Start asynchronous conversion, returns immediately.
        Returns maximum conversion delay [seconds] based on resolution."""
        with self._device as dev:
            dev.write(_CONVERT)
        return _CONVERSION_DELAY[self.resolution]

    def read_temperature(self) -> float:
        """Read the temperature. No polling of the conversion busy bit
        (assumes that the conversion has completed)."""
        return self._read_temp()
