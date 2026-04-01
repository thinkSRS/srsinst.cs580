# srsinst.cs580

`srsinst.cs580` is a Python package to control
[Stanford Research Systems (SRS) CS580 Voltage Controlled Current Source](https://thinksrs.com/products/cs580.html).

## Installation

You need a working Python 3.7 or later with `pip` installed.

To install `srsinst.cs580` as an instrument driver, use `pip` from the command line:

    python -m pip install srsinst.cs580

## Use `srsinst.cs580` as instrument driver

```python
from srsinst.cs580 import CS580

cs580 = CS580('serial', 'COM3')
cs580.check_id()

# Configure
cs580.config.gain = '1uA'          # 1 uA/V gain
cs580.config.isolation = 'float'   # floating output
cs580.config.shield = 'return'     # inner shield to return
cs580.settings.voltage = 10.0      # 10 V compliance limit
cs580.settings.current = 1e-6      # 1 uA DC current

# Enable output
cs580.config.output = True

# Check status
print(cs580.get_status())
print('Overload:', cs580.status.overload)

# Disable output and reset
cs580.config.output = False
cs580.reset()
```

`CS580` is built on [srsgui](https://pypi.org/project/srsgui/).

## Components

| Attribute         | Class           | Description                              |
|-------------------|-----------------|------------------------------------------|
| `cs580.config`    | `Configuration` | Gain, input, speed, shield, isolation, output |
| `cs580.settings`  | `Settings`      | DC current, compliance voltage           |
| `cs580.setup`     | `Setup`         | Audible alarms                           |
| `cs580.interface` | `Interface`     | IDN, token mode, operation complete      |
| `cs580.status`    | `Status`        | Overload, status registers, error codes  |

## Remote interface

The CS580 communicates via RS-232 at a fixed 9600 baud, 8-bit, no parity, no flow control.
Isolated connectivity to GPIB, RS-232, and Ethernet is available through the SX199
Optical Interface Controller (not yet implemented in this driver).

## Running the integration tests

The test suite exercises every driver command and method against a live CS580 over RS-232.
`pytest` must be installed:

    pip install pytest

Connect the CS580 to the PC via RS-232, then run:

    pytest -v -s tests/ --port COM3

Replace `COM3` with the actual COM port. The `-s` flag is required so the
confirmation prompt is visible in the terminal.

If `--port` is omitted you will be prompted to enter the port interactively.
Either way, a confirmation prompt is shown before any commands are sent to the
instrument, giving you a chance to verify the connection first.

> **Note:** These tests require physical hardware. All 98 tests should pass
> against a normally functioning CS580. Unexpected failures most likely
> indicate a driver issue rather than an instrument fault.
