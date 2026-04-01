##!
##! Copyright(c) 2025 Stanford Research Systems, All rights reserved
##! Subject to the MIT License
##!


class Keys:
    # Gain (voltage-to-current conversion)
    G1nA   = '1nA'
    G10nA  = '10nA'
    G100nA = '100nA'
    G1uA   = '1uA'
    G10uA  = '10uA'
    G100uA = '100uA'
    G1mA   = '1mA'
    G10mA  = '10mA'
    G50mA  = '50mA'

    # Speed (filter response)
    Fast = 'fast'
    Slow = 'slow'

    # Shield (inner shield connection)
    Guard  = 'guard'
    Return = 'return'

    # Isolation
    Ground = 'ground'
    Float  = 'float'

    # Generic on/off
    Off = 'off'
    On  = 'on'

    # Overload status
    NoOverload    = 'none'
    OutputOverload = 'output'
    InputOverload  = 'input'
    BothOverload   = 'input and output'

    # Status register bits
    OPC = 'OPC'
    QYE = 'QYE'
    DDE = 'DDE'
    EXE = 'EXE'
    CME = 'CME'
    ESB = 'ESB'
    MSS = 'MSS'
