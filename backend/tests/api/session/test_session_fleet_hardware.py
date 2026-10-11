"""Week 7 fleet acceptance: 15 simulated ESP32 clickers vote through the real endpoints.

Clickers and phones share each match. A clicker logs in with its device secret and
votes with the bearer token that login issued, so the server labels its votes as
hardware. Counts and results come from the API; the stored vote rows are read only for
what the API does not report: which student and which transport each vote has.
"""

from tests.api.session.fleet_support import (
    CLICKER_USERNAME_PREFIX,
    CORRECT_OPTION,
    DISTRACTOR_OPTION,
    FLEET_SIZE,
    OPTIONS,
    TEACHER_USERNAME,
    advance_to_next_round,
    assign_device,
    authenticate_clicker,
    ballots_for,
    bearer,
    cast_vote,
    clicker_device_id,
    interleave,
    provision_clicker,
    provision_fleet,
    reveal_current_round,
    seed_students,
    set_up_arena,
    start_match,
    stored_votes,
    submit_votes_concurrently,
    unassign_device,
    votes_cast_in_current_round,
)
from tests.conftest import auth_headers

ROUND_COUNT = 5
UNASSIGNED_DEVICE_DETAIL = "Device is not assigned to any student."


def test_15_clickers_and_15_phones_play_5_rounds_with_zero_lost_votes(staff_db, client):
    _, conn = staff_db
    arena = set_up_arena(client, conn)
    session_id = start_match(
        client, conn, arena.teacher_headers, question_count=ROUND_COUNT
    )
    voters = interleave(arena.clickers, arena.phones)

    for round_index in range(ROUND_COUNT):
        if round_index > 0:
            advance_to_next_round(client, session_id, arena.teacher_headers)
        ballots = [
            (voter.headers, OPTIONS[(position + round_index) % len(OPTIONS)])
            for position, voter in enumerate(voters)
        ]

        statuses = submit_votes_concurrently(client, session_id, ballots)

        assert statuses == [200] * 30
        assert votes_cast_in_current_round(client, session_id) == 30
        reveal = reveal_current_round(client, session_id, arena.teacher_headers)
        assert reveal["tally"]["total_votes"] == 30

    votes = stored_votes(conn, session_id)
    hardware_votes = [vote for vote in votes if vote["transport_type"] == "hardware"]
    web_votes = [vote for vote in votes if vote["transport_type"] == "web"]
    device_by_student = {
        clicker.student_id: clicker.device_id for clicker in arena.clickers
    }
    assert len(votes) == 150
    assert len(hardware_votes) == 75
    assert len(web_votes) == 75
    assert {vote["student_id"] for vote in hardware_votes} == set(device_by_student)
    assert all(
        device_by_student.get(vote["student_id"]) == vote["device_id"]
        for vote in hardware_votes
    )
    assert all(vote["device_id"] is None for vote in web_votes)
    assert len({(vote["round_id"], vote["student_id"]) for vote in votes}) == 150


def test_15_clickers_pressing_twice_at_once_store_one_vote_each(staff_db, client):
    _, conn = staff_db
    teacher = auth_headers(client, TEACHER_USERNAME)
    clickers = provision_fleet(
        client, teacher, seed_students(conn, CLICKER_USERNAME_PREFIX, FLEET_SIZE)
    )
    session_id = start_match(client, conn, teacher, question_count=1)
    ballots = [
        (clicker.headers, option)
        for clicker in clickers
        for option in (CORRECT_OPTION, DISTRACTOR_OPTION)
    ]

    statuses = submit_votes_concurrently(client, session_id, ballots)

    assert statuses.count(200) == FLEET_SIZE
    assert statuses.count(409) == FLEET_SIZE
    pairs = [statuses[index : index + 2] for index in range(0, len(statuses), 2)]
    assert all(sorted(pair) == [200, 409] for pair in pairs)
    votes = stored_votes(conn, session_id)
    assert sorted(vote["student_id"] for vote in votes) == sorted(
        clicker.student_id for clicker in clickers
    )
    assert all(vote["transport_type"] == "hardware" for vote in votes)


def test_an_unassigned_clicker_stops_voting_while_the_fleet_continues(staff_db, client):
    _, conn = staff_db
    teacher = auth_headers(client, TEACHER_USERNAME)
    clickers = provision_fleet(
        client, teacher, seed_students(conn, CLICKER_USERNAME_PREFIX, FLEET_SIZE)
    )
    session_id = start_match(client, conn, teacher, question_count=2)
    round_one = submit_votes_concurrently(
        client, session_id, ballots_for(clickers, CORRECT_OPTION)
    )
    assert round_one == [200] * FLEET_SIZE
    first_reveal = reveal_current_round(client, session_id, teacher)
    assert first_reveal["tally"]["total_votes"] == FLEET_SIZE
    advance_to_next_round(client, session_id, teacher)

    unassigned = clickers[0]
    unassigned_response = unassign_device(client, teacher, unassigned.device_id)
    assert unassigned_response.status_code == 200
    reauthentication = authenticate_clicker(
        client, unassigned.device_id, unassigned.secret
    )
    assert reauthentication.status_code == 403
    assert reauthentication.json()["detail"] == UNASSIGNED_DEVICE_DETAIL

    round_two = submit_votes_concurrently(
        client, session_id, ballots_for(clickers, CORRECT_OPTION)
    )
    assert round_two == [401] + [200] * (FLEET_SIZE - 1)
    assert votes_cast_in_current_round(client, session_id) == FLEET_SIZE - 1
    second_reveal = reveal_current_round(client, session_id, teacher)
    assert second_reveal["tally"]["total_votes"] == FLEET_SIZE - 1


def test_a_reassigned_clicker_votes_as_its_new_student_after_reauthenticating(
    staff_db, client
):
    _, conn = staff_db
    teacher = auth_headers(client, TEACHER_USERNAME)
    old_student = seed_students(conn, CLICKER_USERNAME_PREFIX, 1)[0]
    new_student = seed_students(conn, "fleet_spare", 1)[0]
    clicker = provision_clicker(client, teacher, old_student, clicker_device_id(1))
    session_id = start_match(client, conn, teacher, question_count=1)

    reassigned = assign_device(
        client, teacher, clicker.device_id, new_student.student_id
    )
    assert reassigned.status_code == 200
    stale_vote = cast_vote(client, session_id, clicker.headers, CORRECT_OPTION)
    assert stale_vote.status_code == 401

    reauthentication = authenticate_clicker(client, clicker.device_id, clicker.secret)
    assert reauthentication.status_code == 200
    assert reauthentication.json()["username"] == new_student.username
    vote = cast_vote(
        client,
        session_id,
        bearer(reauthentication.json()["session_id"]),
        CORRECT_OPTION,
    )
    assert vote.status_code == 200
    assert vote.json()["student_id"] == new_student.student_id
    stored = [
        (row["student_id"], row["transport_type"], row["device_id"])
        for row in stored_votes(conn, session_id)
    ]
    assert stored == [(new_student.student_id, "hardware", clicker.device_id)]


def test_one_distractor_above_51_percent_speaks_whatever_the_transport(
    staff_db, client
):
    _, conn = staff_db
    arena = set_up_arena(client, conn)
    session_id = start_match(client, conn, arena.teacher_headers, question_count=1)
    wrong_pickers = arena.clickers[:8] + arena.phones[:8]  # 16 of 30 votes
    right_pickers = arena.clickers[8:] + arena.phones[8:]  # 14 of 30 votes
    ballots = ballots_for(wrong_pickers, DISTRACTOR_OPTION) + ballots_for(
        right_pickers, CORRECT_OPTION
    )

    assert submit_votes_concurrently(client, session_id, ballots) == [200] * 30
    reveal = reveal_current_round(client, session_id, arena.teacher_headers)

    assert reveal["tally"]["total_votes"] == 30
    assert reveal["tally"]["counts"][DISTRACTOR_OPTION] == 16
    decision = reveal["decision"]
    assert decision["should_speak"] is True
    assert decision["reason"] == "dominant_distractor_exceeded_threshold"
    assert decision["dominant_distractor"] == DISTRACTOR_OPTION
    assert decision["dominant_percentage"] == 53.33
    assert decision["explanation"] == "Sumaste 1 de mas."


def test_exactly_half_on_one_distractor_stays_silent_whatever_the_transport(
    staff_db, client
):
    _, conn = staff_db
    arena = set_up_arena(client, conn)
    session_id = start_match(client, conn, arena.teacher_headers, question_count=1)
    wrong_pickers = arena.clickers[:8] + arena.phones[:7]  # 15 of 30 votes
    right_pickers = arena.clickers[8:] + arena.phones[7:]  # 15 of 30 votes
    ballots = ballots_for(wrong_pickers, DISTRACTOR_OPTION) + ballots_for(
        right_pickers, CORRECT_OPTION
    )

    assert submit_votes_concurrently(client, session_id, ballots) == [200] * 30
    reveal = reveal_current_round(client, session_id, arena.teacher_headers)

    assert reveal["tally"]["total_votes"] == 30
    assert reveal["tally"]["counts"][DISTRACTOR_OPTION] == 15
    decision = reveal["decision"]
    assert decision["should_speak"] is False
    assert decision["reason"] == "threshold_not_reached"
    assert decision["dominant_percentage"] == 50.0
