"""Staff API package."""

from fastapi import APIRouter

from .audit import (
    router as audit_router,
)
from .device_pairing import (
    router as device_pairing_router,
)
from .devices import (
    router as devices_router,
)
from .schemas import (
    AssignDeviceRequest,
    AssignDeviceResponse,
    AuditLogsResponse,
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserResponse,
    DeviceItem,
    DeviceListResponse,
    DeviceMessageResponse,
    RecoverUserRequest,
    RecoverUserResponse,
    RegisterDeviceRequest,
    ResetPinResponse,
    UserListResponse,
)
from .user_delete import (
    router as user_delete_router,
)
from .user_recover import (
    router as user_recover_router,
)
from .user_reset_pin import (
    router as user_reset_pin_router,
)
from .users import (
    router as users_router,
)

router = APIRouter()
router.include_router(users_router)
router.include_router(user_reset_pin_router)
router.include_router(user_delete_router)
router.include_router(user_recover_router)
router.include_router(audit_router)
router.include_router(devices_router)
router.include_router(device_pairing_router)

__all__ = [
    "AssignDeviceRequest",
    "AssignDeviceResponse",
    "AuditLogsResponse",
    "CreateUserRequest",
    "CreateUserResponse",
    "DeleteUserResponse",
    "DeviceItem",
    "DeviceListResponse",
    "DeviceMessageResponse",
    "RecoverUserRequest",
    "RecoverUserResponse",
    "RegisterDeviceRequest",
    "ResetPinResponse",
    "UserListResponse",
    "audit_router",
    "device_pairing_router",
    "devices_router",
    "router",
    "user_delete_router",
    "user_recover_router",
    "user_reset_pin_router",
    "users_router",
]
