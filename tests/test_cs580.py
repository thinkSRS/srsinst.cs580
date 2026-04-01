##!
##! Copyright(c) 2023 Stanford Research Systems, All rights reserved
##! Subject to the MIT License
##!
"""
Integration tests for the srsinst.cs580 driver.

These tests exercise every command and method in the driver against a live
CS580 instrument over RS-232.  The goal is to validate the *driver* — correct
SCPI strings, correct read-back parsing, correct error propagation, and
correct handling of invalid parameters.  The CS580 itself is assumed to be
working correctly.

Run with:
    pytest -v -s tests/ --port COM9
(Use -s so that input() works when --port is omitted.)
"""

import re
import pytest
from srsinst.cs580 import CS580, Keys


# ── Shared helpers ────────────────────────────────────────────────────────────

def no_errors(cs):
    """Assert that no LEXE or LCME errors have occurred since the last read."""
    lexe = cs.status.last_execution_error
    lcme = cs.status.last_command_error
    assert lexe == 0, f"Unexpected execution error: {lexe}"
    assert lcme == 0, f"Unexpected command error: {lcme}"


def clear_errors(cs):
    """Read and discard any pending LEXE / LCME errors and clear the ESR."""
    _ = cs.status.last_execution_error
    _ = cs.status.last_command_error
    cs.status.clear()


# ── TestConnection ─────────────────────────────────────────────────────────────

class TestConnection:
    """Smoke tests — verifies that the driver can communicate at all."""

    def test_id_string_contains_cs580(self, cs):
        assert "CS580" in cs.interface.id_string

    def test_check_id_returns_model(self, cs):
        model, serial, firmware = cs.check_id()
        assert model is not None
        assert "CS580" in model

    def test_comm_baud_rate_is_9600(self, cs):
        assert cs.comm.get_info()["baud_rate"] == 9600


# ── TestReset ─────────────────────────────────────────────────────────────────

class TestReset:
    """
    Send *RST and verify every settable parameter against the defaults
    listed in the manual (§3.4.7).

    Note: TOKN is *not* affected by *RST (retained in non-volatile memory).
    """

    def test_reset_defaults(self, cs):
        cs.reset()
        assert cs.config.gain         == Keys.G1mA,   "GAIN default should be G1mA"
        assert cs.config.analog_input is True,         "INPT default should be ON"
        assert cs.config.speed        == Keys.Fast,   "RESP default should be FAST"
        assert cs.config.shield       == Keys.Return, "SHLD default should be RETURN"
        assert cs.config.isolation    == Keys.Float,  "ISOL default should be FLOAT"
        assert cs.config.output       is False,        "SOUT default should be OFF"
        assert abs(cs.settings.voltage - 10.0) < 0.01, "VOLT default should be 10.0 V"
        assert abs(cs.settings.current - 0.0) < 1e-9,  "CURR default should be 0.0 A"
        assert cs.setup.alarms        is True,         "ALRM default should be ON"


# ── TestConfiguration ─────────────────────────────────────────────────────────

class TestConfiguration:
    """
    Tests for every command in the Configuration component:
    GAIN, INPT, SOUT, RESP, SHLD, ISOL.

    Precondition: output is disabled before each test (SHLD, ISOL, and GAIN
    have restrictions when SOUT is ON).
    """

    @pytest.fixture(autouse=True)
    def output_off(self, cs):
        cs.config.output = False
        clear_errors(cs)
        yield
        cs.config.output = False
        clear_errors(cs)

    # ── GAIN ──────────────────────────────────────────────────────────────────

    def test_gain_key_min(self, cs):
        cs.config.gain = Keys.G1nA
        assert cs.config.gain == Keys.G1nA
        no_errors(cs)

    def test_gain_key_mid(self, cs):
        cs.config.gain = Keys.G10uA
        assert cs.config.gain == Keys.G10uA
        no_errors(cs)

    def test_gain_key_max(self, cs):
        cs.config.gain = Keys.G50mA
        assert cs.config.gain == Keys.G50mA
        no_errors(cs)

    def test_gain_integer_min(self, cs):
        cs.send("GAIN 0")
        assert cs.config.gain == Keys.G1nA
        no_errors(cs)

    def test_gain_integer_mid(self, cs):
        cs.send("GAIN 4")
        assert cs.config.gain == Keys.G10uA
        no_errors(cs)

    def test_gain_integer_max(self, cs):
        cs.send("GAIN 8")
        assert cs.config.gain == Keys.G50mA
        no_errors(cs)

    def test_gain_out_of_range(self, cs):
        cs.send("GAIN 9")
        assert cs.status.last_execution_error == 1  # illegal value

    def test_gain_unknown_token(self, cs):
        cs.send("GAIN BADTOKEN")
        assert cs.status.last_command_error == 14  # unknown token

    def test_gain_not_compatible_with_both_enabled(self, cs):
        """GAIN may not be set while both INPT and SOUT are ON."""
        cs.config.analog_input = True
        cs.config.output = True
        cs.send("GAIN G1MA")
        assert cs.status.last_execution_error == 5  # not compatible
        cs.config.output = False

    # ── INPT ──────────────────────────────────────────────────────────────────

    def test_inpt_on(self, cs):
        cs.config.analog_input = True
        assert cs.config.analog_input is True
        no_errors(cs)

    def test_inpt_off(self, cs):
        cs.config.analog_input = False
        assert cs.config.analog_input is False
        no_errors(cs)

    def test_inpt_token_on(self, cs):
        cs.send("INPT ON")
        assert cs.config.analog_input is True
        no_errors(cs)

    def test_inpt_token_off(self, cs):
        cs.send("INPT OFF")
        assert cs.config.analog_input is False
        no_errors(cs)

    def test_inpt_bad_token(self, cs):
        cs.send("INPT MAYBE")
        assert cs.status.last_command_error == 14  # unknown token

    # ── SOUT ──────────────────────────────────────────────────────────────────

    def test_sout_on(self, cs):
        cs.config.output = True
        assert cs.config.output is True
        no_errors(cs)
        cs.config.output = False

    def test_sout_off(self, cs):
        cs.config.output = False
        assert cs.config.output is False
        no_errors(cs)

    def test_sout_token_on(self, cs):
        cs.send("SOUT ON")
        assert cs.config.output is True
        no_errors(cs)
        cs.config.output = False

    def test_sout_token_off(self, cs):
        cs.config.output = True
        cs.send("SOUT OFF")
        assert cs.config.output is False
        no_errors(cs)

    def test_sout_bad_token(self, cs):
        cs.send("SOUT MAYBE")
        assert cs.status.last_command_error == 14  # unknown token

    # ── RESP ──────────────────────────────────────────────────────────────────

    def test_resp_fast(self, cs):
        cs.config.speed = Keys.Fast
        assert cs.config.speed == Keys.Fast
        no_errors(cs)

    def test_resp_slow(self, cs):
        cs.config.speed = Keys.Slow
        assert cs.config.speed == Keys.Slow
        no_errors(cs)

    def test_resp_integer_0(self, cs):
        cs.send("RESP 0")
        assert cs.config.speed == Keys.Fast
        no_errors(cs)

    def test_resp_integer_1(self, cs):
        cs.send("RESP 1")
        assert cs.config.speed == Keys.Slow
        no_errors(cs)

    def test_resp_out_of_range(self, cs):
        cs.send("RESP 2")
        assert cs.status.last_execution_error == 1  # illegal value

    def test_resp_unknown_token(self, cs):
        cs.send("RESP BADTOKEN")
        assert cs.status.last_command_error == 14  # unknown token

    # ── SHLD ──────────────────────────────────────────────────────────────────

    def test_shld_guard(self, cs):
        cs.config.shield = Keys.Guard
        assert cs.config.shield == Keys.Guard
        no_errors(cs)

    def test_shld_return(self, cs):
        cs.config.shield = Keys.Return
        assert cs.config.shield == Keys.Return
        no_errors(cs)

    def test_shld_integer_0(self, cs):
        cs.send("SHLD 0")
        assert cs.config.shield == Keys.Guard
        no_errors(cs)

    def test_shld_integer_1(self, cs):
        cs.send("SHLD 1")
        assert cs.config.shield == Keys.Return
        no_errors(cs)

    def test_shld_out_of_range(self, cs):
        cs.send("SHLD 2")
        assert cs.status.last_execution_error == 1  # illegal value

    def test_shld_unknown_token(self, cs):
        cs.send("SHLD BADTOKEN")
        assert cs.status.last_command_error == 14  # unknown token

    def test_shld_not_compatible_with_output_on(self, cs):
        """SHLD may not be set while SOUT is ON."""
        cs.config.output = True
        cs.send("SHLD GUARD")
        assert cs.status.last_execution_error == 5  # not compatible
        cs.config.output = False

    # ── ISOL ──────────────────────────────────────────────────────────────────

    def test_isol_ground(self, cs):
        cs.config.isolation = Keys.Ground
        assert cs.config.isolation == Keys.Ground
        no_errors(cs)

    def test_isol_float(self, cs):
        cs.config.isolation = Keys.Float
        assert cs.config.isolation == Keys.Float
        no_errors(cs)

    def test_isol_integer_0(self, cs):
        cs.send("ISOL 0")
        assert cs.config.isolation == Keys.Ground
        no_errors(cs)

    def test_isol_integer_1(self, cs):
        cs.send("ISOL 1")
        assert cs.config.isolation == Keys.Float
        no_errors(cs)

    def test_isol_out_of_range(self, cs):
        cs.send("ISOL 2")
        assert cs.status.last_execution_error == 1  # illegal value

    def test_isol_unknown_token(self, cs):
        cs.send("ISOL BADTOKEN")
        assert cs.status.last_command_error == 14  # unknown token

    def test_isol_not_compatible_with_output_on(self, cs):
        """ISOL may not be set while SOUT is ON."""
        cs.config.output = True
        cs.send("ISOL GROUND")
        assert cs.status.last_execution_error == 5  # not compatible
        cs.config.output = False


# ── TestSettings ──────────────────────────────────────────────────────────────

class TestSettings:
    """
    Tests for CURR and VOLT.

    Precondition: *RST so GAIN = G1mA, giving CURR range = ±2 V × 1 mA/V
    = ±0.002 A.
    """

    @pytest.fixture(autouse=True)
    def reset_first(self, cs):
        cs.reset()
        clear_errors(cs)
        yield
        cs.settings.current = 0.0
        cs.settings.voltage = 10.0
        clear_errors(cs)

    # ── CURR ──────────────────────────────────────────────────────────────────

    def test_curr_zero(self, cs):
        cs.settings.current = 0.0
        assert abs(cs.settings.current - 0.0) < 1e-9
        no_errors(cs)

    def test_curr_midpoint(self, cs):
        cs.settings.current = 0.001
        assert abs(cs.settings.current - 0.001) < 1e-9
        no_errors(cs)

    def test_curr_max(self, cs):
        cs.settings.current = 0.002
        assert abs(cs.settings.current - 0.002) < 1e-9
        no_errors(cs)

    def test_curr_min(self, cs):
        cs.settings.current = -0.002
        assert abs(cs.settings.current - (-0.002)) < 1e-9
        no_errors(cs)

    def test_curr_out_of_range(self, cs):
        """CURR 12.0 is the exact out-of-range example from the manual."""
        cs.send("CURR 12.0")
        assert cs.status.last_execution_error == 1  # illegal value

    def test_curr_bad_float(self, cs):
        """A non-numeric argument should produce a command error."""
        cs.send("CURR BADVAL")
        assert cs.status.last_command_error != 0  # LCME 9 (bad float) or 14 (unknown token)

    # ── VOLT ──────────────────────────────────────────────────────────────────

    def test_volt_min(self, cs):
        cs.settings.voltage = 0.0
        assert abs(cs.settings.voltage - 0.0) < 0.01
        no_errors(cs)

    def test_volt_mid(self, cs):
        cs.settings.voltage = 25.0
        assert abs(cs.settings.voltage - 25.0) < 0.01
        no_errors(cs)

    def test_volt_max(self, cs):
        cs.settings.voltage = 50.0
        assert abs(cs.settings.voltage - 50.0) < 0.01
        no_errors(cs)

    def test_volt_over_max(self, cs):
        cs.send("VOLT 51")
        assert cs.status.last_execution_error == 1  # illegal value

    def test_volt_below_min(self, cs):
        cs.send("VOLT -1")
        assert cs.status.last_execution_error == 1  # illegal value

    def test_volt_bad_float(self, cs):
        cs.send("VOLT BADVAL")
        assert cs.status.last_command_error != 0  # LCME 9 or 14


# ── TestSetup ─────────────────────────────────────────────────────────────────

class TestSetup:
    """Tests for the ALRM command."""

    @pytest.fixture(autouse=True)
    def clean_errors(self, cs):
        clear_errors(cs)
        yield
        clear_errors(cs)

    def test_alarms_on(self, cs):
        cs.setup.alarms = True
        assert cs.setup.alarms is True
        no_errors(cs)

    def test_alarms_off(self, cs):
        cs.setup.alarms = False
        assert cs.setup.alarms is False
        no_errors(cs)

    def test_alarms_token_on(self, cs):
        cs.send("ALRM ON")
        assert cs.setup.alarms is True
        no_errors(cs)

    def test_alarms_token_off(self, cs):
        cs.send("ALRM OFF")
        assert cs.setup.alarms is False
        no_errors(cs)

    def test_alarms_bad_token(self, cs):
        cs.send("ALRM MAYBE")
        assert cs.status.last_command_error == 14  # unknown token


# ── TestInterface ─────────────────────────────────────────────────────────────

class TestInterface:
    """Tests for id_string, token_mode, and operation_complete."""

    @pytest.fixture(autouse=True)
    def restore_token_mode(self, cs):
        clear_errors(cs)
        yield
        cs.interface.token_mode = False  # always restore integer mode
        clear_errors(cs)

    # ── id_string ─────────────────────────────────────────────────────────────

    def test_id_string_format(self, cs):
        idn = cs.interface.id_string
        pattern = r"Stanford.Research.Systems,CS580,s/n\d{6},ver\d+\.\d+"
        assert re.match(pattern, idn), f"Unexpected IDN format: '{idn}'"

    def test_id_string_read_only(self, cs):
        """*IDN without '?' is an illegal set → LCME 4."""
        cs.send("*IDN FOOBAR")
        assert cs.status.last_command_error == 4  # illegal set

    # ── token_mode ────────────────────────────────────────────────────────────

    def test_token_mode_on_returns_keywords(self, cs):
        cs.interface.token_mode = True
        raw = cs.query_text("RESP?")
        assert not raw.strip().isdigit(), (
            f"With TOKN ON, expected a keyword response, got '{raw}'"
        )

    def test_token_mode_off_returns_integers(self, cs):
        cs.interface.token_mode = False
        raw = cs.query_text("RESP?")
        assert raw.strip().isdigit(), (
            f"With TOKN OFF, expected an integer response, got '{raw}'"
        )

    def test_token_mode_restored_dictcommand_works(self, cs):
        cs.interface.token_mode = False
        speed = cs.config.speed
        assert speed in (Keys.Fast, Keys.Slow)
        no_errors(cs)

    # ── operation_complete ────────────────────────────────────────────────────

    def test_opc_query_returns_1(self, cs):
        assert cs.interface.operation_complete == 1

    def test_opc_set_sets_esr_opc_bit(self, cs):
        """The set form (*OPC) sets bit 0 (OPC) of the ESR."""
        cs.status.clear()
        cs.send("*OPC")
        assert cs.status.get_esr(0) == 1  # OPC bit (bit 0, weight 1)


# ── TestStatus ────────────────────────────────────────────────────────────────

class TestStatus:
    """
    Tests for overload, error registers, status registers, and all Status
    component methods.
    """

    @pytest.fixture(autouse=True)
    def clean_state(self, cs):
        cs.status.clear()
        _ = cs.status.last_execution_error
        _ = cs.status.last_command_error
        yield
        cs.status.clear()

    # ── overload ──────────────────────────────────────────────────────────────

    def test_overload_zero_with_no_load(self, cs):
        assert cs.status.overload == 0

    def test_overload_read_only(self, cs):
        cs.send("OVLD 0")
        assert cs.status.last_command_error == 4  # illegal set

    # ── last_execution_error / last_command_error ─────────────────────────────

    def test_lexe_triggers_and_self_clears(self, cs):
        cs.send("CURR 99")
        error = cs.status.last_execution_error
        assert error != 0, "Expected a non-zero LEXE after CURR 99"
        assert cs.status.last_execution_error == 0  # clears on read

    def test_lcme_triggers_and_self_clears(self, cs):
        cs.send("*IDN")  # missing '?' → illegal set
        error = cs.status.last_command_error
        assert error != 0, "Expected a non-zero LCME after '*IDN' (no '?')"
        assert cs.status.last_command_error == 0  # clears on read

    # ── clear() / *CLS ────────────────────────────────────────────────────────

    def test_clear_clears_esr(self, cs):
        cs.send("*IDN")        # trigger CME → sets ESR bit 5
        cs.status.clear()
        assert cs.status.get_esr() == 0

    # ── get_esr() / *ESR? ─────────────────────────────────────────────────────

    def test_get_esr_zero_after_clear(self, cs):
        assert cs.status.get_esr() == 0

    def test_get_esr_cme_bit_set_on_bad_command(self, cs):
        cs.send("*IDN")        # trigger CME (bit 5, weight 32)
        esr = cs.status.get_esr()
        assert esr & 32 == 32, f"Expected ESR CME bit (32) set, got {esr}"

    def test_get_esr_auto_clears_on_read(self, cs):
        cs.send("*IDN")        # trigger CME
        cs.status.get_esr()    # first read clears it
        assert cs.status.get_esr() == 0

    def test_get_esr_bit_specific_cme(self, cs):
        cs.send("*IDN")        # trigger CME (bit 5)
        assert cs.status.get_esr(5) == 1
        assert cs.status.get_esr(5) == 0  # cleared after single-bit read

    def test_get_esr_exe_bit_set_on_bad_value(self, cs):
        cs.send("CURR 99")     # trigger EXE (bit 4, weight 16)
        _ = cs.status.last_execution_error  # clear LEXE (independent of ESR)
        esr = cs.status.get_esr()
        assert esr & 16 == 16, f"Expected ESR EXE bit (16) set, got {esr}"

    # ── get_sre() / set_sre() / *SRE ─────────────────────────────────────────

    def test_set_get_sre_bit(self, cs):
        cs.status.set_sre(5, 1)
        assert cs.status.get_sre(5) == 1
        assert cs.status.get_sre() & 32 == 32
        cs.status.set_sre(5, 0)
        assert cs.status.get_sre(5) == 0

    # ── get_ese() / set_ese() / *ESE ─────────────────────────────────────────

    def test_set_get_ese_bit(self, cs):
        cs.status.set_ese(4, 1)
        assert cs.status.get_ese(4) == 1
        assert cs.status.get_ese() & 16 == 16
        cs.status.set_ese(4, 0)
        assert cs.status.get_ese(4) == 0

    # ── get_status_byte() / *STB? ─────────────────────────────────────────────

    def test_get_status_byte_returns_int(self, cs):
        stb = cs.status.get_status_byte()
        assert isinstance(stb, int)
        assert 0 <= stb <= 255

    def test_get_status_byte_bit_returns_int(self, cs):
        """*STB? with optional bit index."""
        bit = cs.status.get_status_byte(6)  # MSS bit (bit 6)
        assert isinstance(bit, int)

    # ── get_status_text() ─────────────────────────────────────────────────────

    def test_get_status_text_is_nonempty_string(self, cs):
        text = cs.status.get_status_text()
        assert isinstance(text, str)
        assert len(text) > 0

    def test_get_status_text_contains_expected_fields(self, cs):
        text = cs.status.get_status_text()
        for field in ("Overload", "Status byte", "execution error"):
            assert field.lower() in text.lower(), (
                f"Expected '{field}' in get_status_text() output"
            )


# ── TestInstrumentBaseMethods ─────────────────────────────────────────────────

class TestInstrumentBaseMethods:
    """
    Tests for methods inherited from srsgui.Instrument, exercised against
    the live CS580: is_connected, get/set_term_char, send, query_text,
    query_int, query_float, check_id, get_info, handle_command, and
    connect_with_parameter_string.
    """

    @pytest.fixture(autouse=True)
    def clean_errors(self, cs):
        clear_errors(cs)
        yield
        clear_errors(cs)

    def test_is_connected_true(self, cs):
        assert cs.is_connected() is True

    def test_get_term_char_default(self, cs):
        assert cs.get_term_char() == b"\n"

    def test_set_get_term_char_roundtrip(self, cs):
        original = cs.get_term_char()
        cs.set_term_char(b"\r")
        assert cs.get_term_char() == b"\r"
        cs.set_term_char(original)
        assert cs.get_term_char() == original

    def test_send_does_not_raise(self, cs):
        cs.send("*CLS")  # should complete silently
        no_errors(cs)

    def test_query_text_returns_string(self, cs):
        reply = cs.query_text("*IDN?")
        assert isinstance(reply, str)
        assert "CS580" in reply

    def test_query_int_returns_int(self, cs):
        result = cs.query_int("*OPC?")
        assert isinstance(result, int)
        assert result == 1

    def test_query_float_returns_float(self, cs):
        result = cs.query_float("VOLT?")
        assert isinstance(result, float)

    def test_check_id_returns_tuple(self, cs):
        model, serial, firmware = cs.check_id()
        assert model is not None and "CS580" in model
        assert serial is not None
        assert firmware is not None

    def test_get_info_returns_expected_keys(self, cs):
        info = cs.get_info()
        assert isinstance(info, dict)
        assert info.get("baud_rate") == 9600
        assert info.get("type") == "serial"
        assert "CS580" in (info.get("model_name") or "")
        assert info.get("serial_number") is not None
        assert info.get("firmware_version") is not None

    def test_handle_command_query(self, cs):
        reply = cs.handle_command("*IDN?")
        assert isinstance(reply, str)
        assert "CS580" in reply

    def test_handle_command_set_returns_empty_string(self, cs):
        reply = cs.handle_command("*CLS")
        assert reply == ""

    def test_connect_with_parameter_string(self, cs):
        """Disconnect, then reconnect using a colon-separated parameter string."""
        port = cs.comm.get_info()["port"]
        cs.disconnect()
        try:
            cs.connect_with_parameter_string(f"serial:{port}:9600")
            assert cs.is_connected()
        except Exception:
            # Fallback: ensure we are reconnected even if the test fails
            if not cs.is_connected():
                cs.connect("serial", port)
            raise


# ── TestInstrumentMethods ─────────────────────────────────────────────────────

class TestInstrumentMethods:
    """Tests for CS580-specific methods: reset() and get_status()."""

    def test_reset_restores_defaults(self, cs):
        cs.settings.current = 0.001
        cs.settings.voltage = 30.0
        cs.reset()
        assert abs(cs.settings.current - 0.0) < 1e-9
        assert abs(cs.settings.voltage - 10.0) < 0.01

    def test_get_status_is_nonempty_string(self, cs):
        text = cs.get_status()
        assert isinstance(text, str)
        assert len(text) > 0

    def test_get_status_contains_expected_fields(self, cs):
        text = cs.get_status()
        for field in ("Output", "Gain", "DC current", "Compliance"):
            assert field in text, f"Expected '{field}' in get_status() output"
