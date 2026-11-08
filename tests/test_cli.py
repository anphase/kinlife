import io
from pathlib import Path

import pytest

from multicell import __version__
from multicell.cli import main
from multicell.engine import Simulation, parse_seed
from multicell.render import frame, population_text, run_plain
from multicell.slate import main as slate_main
from multicell.ui import MAX_INTERVAL, MIN_INTERVAL, Session, _wrap_words


@pytest.fixture
def seed(tmp_path: Path) -> Path:
    path = tmp_path / "seed.txt"
    path.write_text("...\n.A.\n...\n")
    return path


def test_run_plain_prints_frames(
    seed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([str(seed), "--plain", "-n", "2", "-p", "0"]) == 0
    out = capsys.readouterr().out
    assert out.count("Generation") == 3
    assert "Generation 0  A=1" in out
    assert "Generation 1  extinct" in out


def test_wrap_and_rng_seed_flags(
    seed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = [str(seed), "--plain", "-n", "3", "--wrap", "--rng-seed", "3"]
    assert main(args) == 0
    first = capsys.readouterr().out
    assert main(args) == 0
    assert capsys.readouterr().out == first


def test_rule_flag_runs_brians_brain(
    seed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([str(seed), "--plain", "-n", "2", "-p", "0", "--rule", "brain"]) == 0
    out = capsys.readouterr().out
    # The live cell becomes dying (no species counted), then empty.
    assert "Generation 1  extinct" in out
    assert "|.~.|" not in out  # empty cells print as spaces
    assert "| ~ |" in out


def test_unknown_rule_rejected(seed: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        main([str(seed), "--rule", "nope"])
    assert exc.value.code == 2


@pytest.mark.parametrize(
    "args",
    [["-p", "-1"], ["-t", "-1"], ["-n", "-1"]],
)
def test_negative_options_rejected(
    seed: Path, args: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([str(seed), "--plain", *args]) == 2
    assert "must not be negative" in capsys.readouterr().err


def test_missing_seed_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(tmp_path / "nope.txt")]) == 2
    assert "cannot read" in capsys.readouterr().err


def test_non_rectangular_seed_reports_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bad.txt"
    bad.write_text("A.\nB..\n")
    assert main([str(bad), "--plain"]) == 2
    assert "not rectangular" in capsys.readouterr().err


def test_non_utf8_seed_reports_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bad.txt"
    bad.write_bytes(b"A.\n\xff.\n")
    assert main([str(bad), "--plain"]) == 2
    assert "not UTF-8" in capsys.readouterr().err


def test_utf8_bom_is_ignored(seed: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed.write_bytes(b"\xef\xbb\xbf...\n.A.\n...\n")
    assert main([str(seed), "--plain", "-n", "0", "-p", "0"]) == 0
    assert "Generation 0  A=1" in capsys.readouterr().out


def test_ctrl_c_in_plain_mode_exits_quietly(
    seed: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def interrupt(*_args: object, **_kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("multicell.cli.run_plain", interrupt)
    assert main([str(seed), "--plain"]) == 130


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["--version"])
    assert __version__ in capsys.readouterr().out


def test_live_plain_clears_between_frames() -> None:
    out = io.StringIO()
    sim = Simulation(parse_seed("A.\n.."))
    run_plain(sim, 1, 0.0, out, live=True)
    assert out.getvalue().count("\x1b[H\x1b[J") == 2


def test_frame_and_population_text() -> None:
    assert frame(("A.", "..")) == "+--+\n|A |\n|  |\n+--+"
    assert frame(()) == "++\n++"
    assert population_text(Simulation(parse_seed("AAB")).population) == "A=2 B=1"


# --- slate -----------------------------------------------------------------


def test_slate_writes_blank_seed(tmp_path: Path) -> None:
    out = tmp_path / "s.txt"
    assert slate_main(["-o", str(out), "-r", "2", "-c", "3"]) == 0
    assert out.read_text() == "...\n...\n"


def test_slate_rejects_negative(tmp_path: Path) -> None:
    assert slate_main(["-o", str(tmp_path / "s.txt"), "-r", "-1"]) == 2


def test_slate_overwrite_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "s.txt"
    out.write_text("old")
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    assert slate_main(["-o", str(out), "-r", "1", "-c", "1"]) == 1
    assert out.read_text() == "old"
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    assert slate_main(["-o", str(out), "-r", "1", "-c", "1"]) == 0
    assert out.read_text() == ".\n"


def test_slate_overwrite_without_tty_declines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "s.txt"
    out.write_text("old")

    def eof(_prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert slate_main(["-o", str(out)]) == 1
    assert slate_main(["-o", str(out), "-f", "-r", "1", "-c", "1"]) == 0


def test_slate_write_failure_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert slate_main(["-o", str(tmp_path / "missing" / "s.txt"), "-f"]) == 1
    assert "cannot write" in capsys.readouterr().err


# --- session ---------------------------------------------------------------


def make_session() -> Session:
    return Session(lambda: Simulation(parse_seed(".....\n.AAA.\n.....")), 0.05)


def test_session_pause_and_step() -> None:
    s = make_session()
    s.tick()
    assert s.sim.generation == 1
    s.handle(" ")
    assert s.paused
    s.tick()
    assert s.sim.generation == 1
    s.handle("s")
    assert s.sim.generation == 2
    s.handle("p")
    assert not s.paused


def test_session_step_pauses() -> None:
    s = make_session()
    s.handle("s")
    assert s.paused
    assert s.sim.generation == 1


def test_session_speed_is_clamped() -> None:
    s = make_session()
    for _ in range(50):
        s.handle("+")
    assert s.interval == MIN_INTERVAL
    for _ in range(50):
        s.handle("-")
    assert s.interval == MAX_INTERVAL


def test_session_restart_toggle_wrap_quit() -> None:
    s = make_session()
    s.tick()
    s.handle("r")
    assert s.sim.generation == 0
    assert not s.sim.wrap
    s.handle("w")
    assert s.sim.wrap
    assert "wrap" in s.status()
    assert not s.quit
    s.handle("q")
    assert s.quit


def test_session_restart_keeps_current_wrap_setting() -> None:
    s = make_session()
    s.handle("w")
    assert s.sim.wrap
    s.handle("r")
    assert s.sim.generation == 0
    assert s.sim.wrap
    s.handle("w")
    s.handle("r")
    assert not s.sim.wrap


def test_session_unknown_key_ignored_and_text() -> None:
    s = make_session()
    s.handle("z")
    assert not s.paused
    assert s.status().startswith("Generation 0  running")
    assert population_text(s.sim.population) == "A=3"


def test_session_interval_initial_clamp() -> None:
    assert Session(lambda: Simulation(("A",)), 0).interval == MIN_INTERVAL


def test_wrap_words_wraps_to_width() -> None:
    assert _wrap_words(["aa", "bb", "cc"], 100) == ["aa  bb  cc"]
    assert _wrap_words(["aa", "bb", "cc"], 5) == ["aa", "bb", "cc"]


def test_python_dash_m_entry_point(seed: Path) -> None:
    import runpy
    import sys

    argv = sys.argv
    sys.argv = ["multicell", str(seed), "--plain", "-n", "0"]
    try:
        with pytest.raises(SystemExit) as exit_info:
            runpy.run_module("multicell", run_name="__main__")
    finally:
        sys.argv = argv
    assert exit_info.value.code == 0
