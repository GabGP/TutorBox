"""Tells a live clicker token from a revoked one the only way a clicker can: by voting."""

from fastapi.testclient import TestClient

VOTE_ON_A_MISSING_MATCH_URL = "/api/v1/session/no-such-match/vote"


def clicker_token_is_live(client: TestClient, headers: dict[str, str]) -> bool:
    """Votes on a match that does not exist: 404 once the token is accepted, 401 if not."""
    response = client.post(
        VOTE_ON_A_MISSING_MATCH_URL, json={"selected_option": "A"}, headers=headers
    )
    assert response.status_code in (401, 404), response.text
    return response.status_code == 404
