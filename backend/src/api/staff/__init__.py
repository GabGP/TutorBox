"""Staff API package."""

from fastapi import APIRouter

from .audit import (
    AuditLogsResponse,
)
from .audit import (
    router as audit_router,
)
from .delete import (
    DeleteUserResponse,
)
from .delete import (
    router as delete_router,
)
from .device_pairing import (
    AssignDeviceRequest,
    AssignDeviceResponse,
)
from .device_pairing import (
    router as device_pairing_router,
)
from .devices import (
    DeviceItem,
    DeviceListResponse,
    DeviceMessageResponse,
    RegisterDeviceRequest,
)
from .devices import (
    router as devices_router,
)
from .recover import (
    RecoverUserRequest,
    RecoverUserResponse,
)
from .recover import (
    router as recover_router,
)
from .reset_pin import (
    ResetPinResponse,
)
from .reset_pin import (
    router as reset_pin_router,
)
from .users import (
    CreateUserRequest,
    CreateUserResponse,
    UserListResponse,
)
from .users import (
    router as users_router,
)

router = APIRouter()
router.include_router(users_router)
router.include_router(reset_pin_router)
router.include_router(delete_router)
router.include_router(recover_router)
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
    "delete_router",
    "device_pairing_router",
    "devices_router",
    "recover_router",
    "reset_pin_router",
    "router",
    "users_router",
]
