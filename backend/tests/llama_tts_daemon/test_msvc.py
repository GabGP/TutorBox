"""Unit tests for the Visual Studio vcvars64.bat lookup (tools/llama_tts_daemon/build_llama/msvc.py)."""

from tools.llama_tts_daemon.build_llama import msvc


def test_find_vcvars64_returns_none_when_vcinstalldir_is_set(tmp_path, monkeypatch):
    """Verifies find_vcvars64 returns None when MSVC is already initialized, even if a candidate exists."""
    existing_candidate = tmp_path / "vcvars64.bat"
    existing_candidate.write_text("", encoding="utf-8")
    monkeypatch.setattr(msvc, "VCVARS64_CANDIDATES", [existing_candidate])
    monkeypatch.setenv("VCINSTALLDIR", "C:/VS/VC/")

    assert msvc.find_vcvars64() is None


def test_find_vcvars64_returns_first_existing_candidate(tmp_path, monkeypatch):
    """Verifies find_vcvars64 returns the first candidate in list order that is an existing file."""
    missing_candidate = tmp_path / "first" / "vcvars64.bat"
    second_candidate = tmp_path / "second" / "vcvars64.bat"
    third_candidate = tmp_path / "third" / "vcvars64.bat"
    second_candidate.parent.mkdir(parents=True)
    third_candidate.parent.mkdir(parents=True)
    second_candidate.write_text("", encoding="utf-8")
    third_candidate.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        msvc,
        "VCVARS64_CANDIDATES",
        [missing_candidate, second_candidate, third_candidate],
    )
    monkeypatch.delenv("VCINSTALLDIR", raising=False)

    assert msvc.find_vcvars64() == str(second_candidate)


def test_find_vcvars64_returns_none_when_no_candidate_exists(tmp_path, monkeypatch):
    """Verifies find_vcvars64 returns None when no Visual Studio installation provides vcvars64.bat."""
    missing_candidate = tmp_path / "missing" / "vcvars64.bat"
    monkeypatch.setattr(msvc, "VCVARS64_CANDIDATES", [missing_candidate])
    monkeypatch.delenv("VCINSTALLDIR", raising=False)

    assert msvc.find_vcvars64() is None


def test_vcvars64_candidates_list_known_visual_studio_installs_in_order():
    """Verifies the built-in candidate list covers VS 2022 then VS 2019 installs in the documented order."""
    candidate_posix_paths = [
        candidate.as_posix() for candidate in msvc.VCVARS64_CANDIDATES
    ]

    assert candidate_posix_paths == [
        "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars64.bat",
        "C:/Program Files/Microsoft Visual Studio/2022/Professional/VC/Auxiliary/Build/vcvars64.bat",
        "C:/Program Files/Microsoft Visual Studio/2022/Enterprise/VC/Auxiliary/Build/vcvars64.bat",
        "C:/Program Files/Microsoft Visual Studio/2022/BuildTools/VC/Auxiliary/Build/vcvars64.bat",
        "C:/Program Files (x86)/Microsoft Visual Studio/2019/Community/VC/Auxiliary/Build/vcvars64.bat",
        "C:/Program Files (x86)/Microsoft Visual Studio/2019/BuildTools/VC/Auxiliary/Build/vcvars64.bat",
    ]
