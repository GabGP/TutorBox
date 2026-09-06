"""Pydantic schemas for user and profile endpoints."""

from pydantic import BaseModel

from core.security import PinField, UsernameField


class SignupRequest(BaseModel):
    username: UsernameField
    pin: PinField


class SignupResponse(BaseModel):
    username: str
    role: str


class UserProfileResponse(BaseModel):
    user_id: int
    username: str
    role: str
    must_change_pin: bool


class ChangeUsernameRequest(BaseModel):
    current_pin: PinField
    new_username: UsernameField


class ChangePinRequest(BaseModel):
    current_pin: PinField
    new_pin: PinField


class CredentialChangeResponse(BaseModel):
    detail: str = "Credentials updated. Please sign in again."
