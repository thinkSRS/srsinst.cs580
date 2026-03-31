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
