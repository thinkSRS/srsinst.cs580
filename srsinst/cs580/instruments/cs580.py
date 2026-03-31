##!
##! Copyright(c) 2023 Stanford Research Systems, All rights reserved
##! Subject to the MIT License
##!

from srsgui import Instrument
from srsgui.inst import SerialInterface
from srsgui.task.inputs import FindListInput

from .components import Configuration, Settings, Setup, Interface, Status


class CS580(Instrument):
    _IdString = 'CS580'

    available_interfaces = [
        [
            SerialInterface,
            {
                'port': FindListInput(),
                'baud_rate': 9600,
            }
        ],
    ]

    def __init__(self, interface_type=None, *args):
        if interface_type in (SerialInterface, SerialInterface.NAME) and len(args) == 1:
            args = (args[0], 9600)
        super().__init__(interface_type, *args)

        self.config    = Configuration(self)
        self.settings  = Settings(self)
        self.setup     = Setup(self)
        self.interface = Interface(self)
        self.status    = Status(self)

    def connect(self, interface_type, *args):
        if interface_type in (SerialInterface, SerialInterface.NAME) and len(args) == 1:
            args = (args[0], 9600)
        super().connect(interface_type, *args)

    def reset(self):
        self.send('*RST')

    def get_status(self):
        output_str = 'ON' if self.config.output else 'OFF'
        input_str  = 'ON' if self.config.analog_input else 'OFF'
        return (
            f'Output: {output_str}\n'
            f' Analog input: {input_str}\n'
            f' Gain: {self.config.gain}\n'
            f' Speed: {self.config.speed}\n'
            f' Shield: {self.config.shield}\n'
            f' Isolation: {self.config.isolation}\n'
            f' DC current: {self.settings.current:.4e} A\n'
            f' Compliance voltage: {self.settings.voltage:.1f} V\n\n'
            + self.status.get_status_text()
        )

    allow_run_button = [reset]
