"""voice_release: unload every loaded voice, unless a live quiz game keeps them."""

from core.system_health.voice_release import release_voices


class FakeVoiceRouter:
    def __init__(self, engines: list[str], failing: set[str] | None = None) -> None:
        self.engines = engines
        self.failing = failing or set()
        self.unloaded: list[str] = []
        self.engines_error: Exception | None = None

    def loaded_engines(self) -> list[str]:
        if self.engines_error is not None:
            raise self.engines_error
        return list(self.engines)

    def unload(self, engine: str | None = None) -> str:
        if engine in self.failing:
            raise OSError(f"{engine} is busy")
        self.unloaded.append(engine or "")
        return engine or ""


def no_game() -> bool:
    return False


def test_no_loaded_voice_gives_no_actions():
    assert release_voices(FakeVoiceRouter([]), no_game) == []


def test_each_idle_voice_is_unloaded():
    router = FakeVoiceRouter(["piper", "qwen3-tts"])

    actions = release_voices(router, no_game)

    assert router.unloaded == ["piper", "qwen3-tts"]
    assert [(action.target, action.kind, action.action) for action in actions] == [
        ("voz piper", "voice", "unloaded"),
        ("voz qwen3-tts", "voice", "unloaded"),
    ]


def test_a_live_quiz_game_keeps_every_voice():
    router = FakeVoiceRouter(["piper", "qwen3-tts"])

    actions = release_voices(router, lambda: True)

    assert router.unloaded == []
    assert {action.action for action in actions} == {"kept"}
    assert actions[0].detail == "a quiz game is running"


def test_an_unknown_game_state_keeps_the_voices_and_says_why():
    router = FakeVoiceRouter(["piper"])

    def broken_game_check() -> bool:
        raise RuntimeError("database is locked")

    actions = release_voices(router, broken_game_check)

    assert router.unloaded == []
    assert actions[0].action == "kept"
    assert "database is locked" in (actions[0].detail or "")


def test_a_voice_that_cannot_unload_fails_and_the_others_still_go():
    router = FakeVoiceRouter(["piper", "qwen3-tts"], failing={"piper"})

    actions = release_voices(router, no_game)

    assert router.unloaded == ["qwen3-tts"]
    assert (actions[0].target, actions[0].action) == ("voz piper", "failed")
    assert actions[0].detail == "piper is busy"
    assert actions[1].action == "unloaded"


def test_loaded_voices_that_cannot_be_listed_fail_as_one_action():
    router = FakeVoiceRouter([])
    router.engines_error = RuntimeError("registry broken")

    actions = release_voices(router, no_game)

    assert len(actions) == 1
    assert (actions[0].target, actions[0].action) == ("voces", "failed")
    assert router.unloaded == []


def test_espeak_keeps_nothing_in_memory_so_it_is_neither_listed_nor_unloaded():
    router = FakeVoiceRouter(["espeak", "piper"])

    actions = release_voices(router, no_game)

    assert router.unloaded == ["piper"]
    assert [action.target for action in actions] == ["voz piper"]
