##!
##! Copyright(c) 2023 Stanford Research Systems, All rights reserved
##! Subject to the MIT License
##!

from srsgui import Component
from srsgui import Command, GetCommand, \
                   BoolCommand, BoolGetCommand, \
                   IntCommand, IntGetCommand, IntSetCommand, \
                   FloatCommand, FloatSetCommand, FloatGetCommand, \
                   DictCommand, DictGetCommand

from .keys import Keys


class Configuration(Component):
    """
    Configuration commands: gain, analog input, speed, shield, isolation, output.
    """

    GainDict = {
        Keys.G1nA:   0,
        Keys.G10nA:  1,
        Keys.G100nA: 2,
        Keys.G1uA:   3,
        Keys.G10uA:  4,
        Keys.G100uA: 5,
        Keys.G1mA:   6,
        Keys.G10mA:  7,
        Keys.G50mA:  8,
    }

    SpeedDict = {
        Keys.Fast: 0,
        Keys.Slow: 1,
    }

    ShieldDict = {
        Keys.Guard:  0,
        Keys.Return: 1,
    }

    IsolationDict = {
        Keys.Ground: 0,
        Keys.Float:  1,
    }

    # GAIN(?) {z} — voltage-to-current gain setting
    # Note: GAIN may not be set while analog input AND output are both enabled.
    gain = DictCommand('GAIN', GainDict)

    # INPT(?) {z} — analog input BNC enable (OFF=0, ON=1)
    # Controlled independently of output (SOUT).
    analog_input = BoolCommand('INPT')

    # RESP(?) {z} — current source filter response speed (FAST=0, SLOW=1)
    speed = DictCommand('RESP', SpeedDict)

    # SHLD(?) {z} — inner shield connection (GUARD=0, RETURN=1)
    # Note: SHLD may not be set while output is enabled.
    shield = DictCommand('SHLD', ShieldDict)

    # ISOL(?) {z} — current source isolation mode (GROUND=0, FLOAT=1)
    # Note: ISOL may not be set while output is enabled.
    isolation = DictCommand('ISOL', IsolationDict)

    # SOUT(?) {z} — current source output enable (OFF=0, ON=1)
    # Controlled independently of analog input (INPT).
    output = BoolCommand('SOUT')


class Settings(Component):
    """
    Setting commands: DC current and compliance voltage.
    """

    # CURR(?) {f} — internally-generated DC current, in amperes.
    # Default: 0.0 A. Range: ±2V × gain (e.g. ±20e-6 A at G10uA).
    # Bounds below cover the widest possible range (G50mA: ±100 mA).
    current = FloatCommand('CURR', 'A', -0.11, 0.11, 1e-13, 4, 0.0)

    # VOLT(?) {g} — compliance voltage limit, in volts.
    # Default: 10.0 V. Range: 0 to 50 V.
    voltage = FloatCommand('VOLT', 'V', 0.0, 50.0, 0.1, 3, 10.0)


class Setup(Component):
    """
    Setup commands: audible alarms.
    """

    # ALRM(?) {z} — audible alarms enable (OFF=0, ON=1).
    # No front-panel equivalent; remote interface only.
    alarms = BoolCommand('ALRM')


class Interface(Component):
    """
    Interface commands: identify, token mode, operation complete.
    """

    # *IDN? — identification string query.
    # Response: Stanford_Research_Systems,CS580,s/n######,ver#.##
    id_string = GetCommand('*IDN')

    # TOKN(?) {z} — token response mode (OFF=0 returns integers, ON=1 returns keywords).
    # Default: OFF. Leave OFF so DictCommand integer responses work correctly.
    token_mode = BoolCommand('TOKN')

    # *OPC(?) — operation complete.
    # Set form sets OPC bit in ESR; query form returns 1.
    operation_complete = IntGetCommand('*OPC')


class Status(Component):
    """
    Status commands: overload, status registers, error codes.
    """

    OverloadDict = {
        0: Keys.NoOverload,
        1: Keys.OutputOverload,
        2: Keys.InputOverload,
        3: Keys.BothOverload,
    }

    # OVLD? — overload status (query only).
    # 0=none, 1=compliance limit (output), 2=analog input, 3=both.
    overload = IntGetCommand('OVLD')

    # LEXE? — last execution error code (query clears it).
    # 0=none, 1=illegal value, 2=wrong token, 3=invalid bit,
    # 4=queue full, 5=not compatible.
    last_execution_error = IntGetCommand('LEXE')

    # LCME? — last command error code (query clears it).
    # 0=none, 1=illegal command, 2=undefined command, 3=illegal query,
    # 4=illegal set, 5=missing parameter(s), 6=extra parameter(s),
    # 7=null parameter(s), 8=parameter buffer overflow, 9=bad float,
    # 10=bad integer, 11=bad integer token, 12=bad token value,
    # 13=bad hex block, 14=unknown token.
    last_command_error = IntGetCommand('LCME')

    def get_status_byte(self, bit=None):
        """Read the Status Byte register, or a single bit *STB? [i]."""
        if bit is None:
            return int(self.comm.query_text('*STB?'))
        else:
            return int(self.comm.query_text(f'*STB? {bit}'))

    def get_esr(self, bit=None):
        """Read (and clear) the Standard Event Status Register, or a single bit."""
        if bit is None:
            return int(self.comm.query_text('*ESR?'))
        else:
            return int(self.comm.query_text(f'*ESR? {bit}'))

    def get_sre(self, bit=None):
        """Read the Service Request Enable register, or a single bit."""
        if bit is None:
            return int(self.comm.query_text('*SRE?'))
        else:
            return int(self.comm.query_text(f'*SRE? {bit}'))

    def set_sre(self, bit, value):
        """Set a single bit in the Service Request Enable register."""
        self.comm.send(f'*SRE {bit},{int(bool(value))}')

    def get_ese(self, bit=None):
        """Read the Standard Event Status Enable register, or a single bit."""
        if bit is None:
            return int(self.comm.query_text('*ESE?'))
        else:
            return int(self.comm.query_text(f'*ESE? {bit}'))

    def set_ese(self, bit, value):
        """Set a single bit in the Standard Event Status Enable register."""
        self.comm.send(f'*ESE {bit},{int(bool(value))}')

    def clear(self):
        """Clear the ESR register (*CLS)."""
        self.comm.send('*CLS')

    def get_status_text(self):
        """Return a human-readable summary of current status."""
        ovld = self.overload
        ovld_str = self.OverloadDict.get(ovld, f'unknown ({ovld})')
        stb  = self.get_status_byte()
        esr  = self.get_esr()
        lexe = self.last_execution_error
        lcme = self.last_command_error
        return (
            f' Overload: {ovld_str}\n'
            f' Status byte: {stb}\n'
            f' Event status: {esr}\n'
            f' Last execution error: {lexe}\n'
            f' Last command error: {lcme}\n'
        )
