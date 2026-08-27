import logging
import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from db.database import get_db
from security.auth import hash_pin
from security.session import AuthContext, require_roles
from security.validation import (
    PIN_MAX_LENGTH,
    PIN_MIN_LENGTH,
    PIN_PATTERN,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_PATTERN,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateUserRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        pattern=USERNAME_PATTERN,
        examples=["student3"],
    )
    pin: str = Field(
        ...,
        min_length=PIN_MIN_LENGTH,
        max_length=PIN_MAX_LENGTH,
        pattern=PIN_PATTERN,
        examples=["1234"],
    )
    role: str = Field("student", pattern="^(student|teacher|admin)$")


class CreateUserResponse(BaseModel):
    username: str
    role: str


class UserListResponse(BaseModel):
    users: list[dict[str, Any]]


@router.get("/users", response_model=UserListResponse)
def list_users(
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    include_deleted: bool = False,
):
    """
    Roster view. Lists active users, or minimal metadata for deleted accounts when include_deleted=True.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        if include_deleted:
            cursor.execute(
                "SELECT id, role, former_username, deleted_at FROM users "
                "WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC LIMIT 1000"
            )
            return UserListResponse(
                users=[
                    {
                        "id": r["id"],
                        "role": r["role"],
                        "former_username": r["former_username"],
                        "deleted_at": r["deleted_at"],
                    }
                    for r in cursor.fetchall()
                ]
            )

        cursor.execute(
            "SELECT id, username, role, created_at, must_change_pin "
            "FROM users WHERE deleted_at IS NULL "
            "ORDER BY username LIMIT 1000"
        )
        rows = cursor.fetchall()

    return UserListResponse(
        users=[
            {
                "id": r["id"],
                "username": r["username"],
                "role": r["role"],
                "created_at": r["created_at"],
                "must_change_pin": bool(r["must_change_pin"]),
            }
            for r in rows
        ]
    )


@router.post(
    "/users",
    response_model=CreateUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: CreateUserRequest,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
):
    """
    Staff user creation. Teachers can create student and teacher accounts. Admins can create any account.
    """
    # teachers create students AND teachers; only admins create admins.
    if ctx.role == "teacher" and payload.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins may create admin accounts.",
        )

    logger.info(
        "User creation attempt by '%s' (role: %s) for new user '%s' (role: %s).",
        ctx.username,
        ctx.role,
        payload.username,
        payload.role,
    )

    hashed = hash_pin(payload.pin)

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, hashed_pin, role) VALUES (?, ?, ?)",
                (payload.username, hashed, payload.role),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        logger.warning(
            "User creation conflict: Username '%s' already exists.",
            payload.username,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken.",
        )

    logger.info(
        "User '%s' (role: %s) created successfully by '%s'.",
        payload.username,
        payload.role,
        ctx.username,
    )
    return CreateUserResponse(username=payload.username, role=payload.role)
