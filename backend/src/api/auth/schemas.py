"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel

from core.security import PinField, UsernameField


class LoginRequest(BaseModel):
    username: UsernameField
    pin: PinField


class LoginResponse(BaseModel):
    session_id: str
    username: str
    status: str = "authenticated"
    must_change_pin: bool = False


class LogoutResponse(BaseModel):
    detail: str = "Logged out."
