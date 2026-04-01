##!
##! Copyright(c) 2025 Stanford Research Systems, All rights reserved
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
    if port is None:
        print("Please connect the PC to the RS-232 interface on the CS580.")
        port = input("Enter the COM port (e.g. COM9): ").strip()

    # Attempt connection; prompt for intervention only if it fails
    inst = CS580()
    while True:
        try:
            inst.connect("serial", port)
            inst.check_id()  # verify the CS580 is actually responding
            break
        except Exception as exc:
            try:
                inst.disconnect()
            except Exception:
                pass
            print(f"\nConnection failed: {exc}")
            new_port = input(
                f"Please ensure the CS580 is connected and powered on.\n"
                f"Press Enter to retry on {port}, or enter a different port: "
            ).strip()
            if new_port:
                port = new_port

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
