# SPDX-FileCopyrightText: 2017 Carter Nelson for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_onewire.device`
====================================================

Provides access to a single device on the 1-Wire bus.

* Author(s): Carter Nelson
"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_OneWire.git"

try:
    from typing import Optional, Type
    from circuitpython_typing import ReadableBuffer, WriteableBuffer
    from types import TracebackType
    from adafruit_onewire.bus import OneWireBus, OneWireAddress
except ImportError:
    pass

_MATCH_ROM = b"\x55"


class OneWireDevice:
    """A class to represent a single device on the 1-Wire bus."""

    def __init__(self, bus: OneWireBus, address: OneWireAddress):
        self._bus = bus
        self._address = address

    def __enter__(self) -> "OneWireDevice":
        self._select_rom()
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[type]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        return False

    def readinto(
        self, buf: WriteableBuffer, *, start: int = 0, end: Optional[int] = None
    ) -> None:
        """
        Read into ``buf`` from the device. The number of bytes read will be the
        length of ``buf``.

        If ``start`` or ``end`` is provided, then the buffer will be sliced
        as if ``buf[start:end]``. This will not cause an allocation like
        ``buf[start:end]`` will so it saves memory.

        :param WriteableBuffer buf: Buffer to write into
        :param int start: Index to start writing at
        :param int end: Index to write up to but not include
        """
        self._bus.readinto(buf, start=start, end=end)
        if start == 0 and end is None and len(buf) >= 8:
            if self._bus.crc8(buf):
                raise RuntimeError("CRC error.")

    def write(
        self, buf: ReadableBuffer, *, start: int = 0, end: Optional[int] = None
    ) -> None:
        """
        Write the bytes from ``buf`` to the device.

        If ``start`` or ``end`` is provided, then the buffer will be sliced
        as if ``buffer[start:end]``. This will not cause an allocation like
        ``buffer[start:end]`` will so it saves memory.

        :param ReadableBuffer buf: buffer containing the bytes to write
        :param int start: Index to start writing from
        :param int end: Index to read up to but not include
        """
        return self._bus.write(buf, start=start, end=end)

    def _select_rom(self) -> None:
        self._bus.reset()
        self.write(_MATCH_ROM)
        self.write(self._address.rom)
