##!
##! Copyright(c) 2023 Stanford Research Systems, All rights reserved
##! Subject to the MIT License
##!

import pytest
from srsinst.cs580 import CS580


def pytest_addoption(parser):
    parser.addoption(
        "--port",
        default=None,
        help="COM port for CS580 RS-232 connection (e.g. COM9)",
    )


@pytest.fixture(scope="session")
def cs(request):
    port = request.config.getoption("--port")
    print("\n" + "=" * 60)
    print("CS580 Integration Test Suite")
    print("=" * 60)
    print("Please connect the PC to the RS-232 interface on the CS580.")
    if port is None:
        port = input("Enter the COM port (e.g. COM9): ").strip()

    inst = CS580("serial", port)
    inst.interface.token_mode = False  # ensure integer token responses throughout
    inst.status.clear()
    # Discard any stale errors
    _ = inst.status.last_execution_error
    _ = inst.status.last_command_error

    yield inst

    # Teardown: restore defaults and release the port
    try:
        inst.reset()
    finally:
        inst.disconnect()
