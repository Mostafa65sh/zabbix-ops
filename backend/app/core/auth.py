from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


class User(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    roles: List[str] = Field(default_factory=lambda: ["viewer"])
    permissions: List[str] = Field(default_factory=list)


class TokenData(BaseModel):
    sub: str
    username: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    exp: Optional[datetime] = None


class BaseAuthProvider:
    """
    Abstract interface for authentication providers (Local DB, LDAP, Active Directory, SSO/OAuth2/OIDC).
    """
    async def authenticate(self, credentials: dict) -> Optional[User]:
        raise NotImplementedError

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        raise NotImplementedError


class LocalDevAuthProvider(BaseAuthProvider):
    """
    Default provider for development and testing.
    """
    async def authenticate(self, credentials: dict) -> Optional[User]:
        username = credentials.get("username", "admin")
        return User(
            id="usr_001",
            username=username,
            email=f"{username}@ops.local",
            is_active=True,
            is_superuser=True,
            roles=["admin"],
            permissions=["*"]
        )

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        return User(
            id=user_id,
            username="admin",
            email="admin@ops.local",
            is_active=True,
            is_superuser=True,
            roles=["admin"],
            permissions=["*"]
        )


security_scheme = HTTPBearer(auto_error=False)
_auth_provider: BaseAuthProvider = LocalDevAuthProvider()


def get_auth_provider() -> BaseAuthProvider:
    return _auth_provider


def set_auth_provider(provider: BaseAuthProvider) -> None:
    global _auth_provider
    _auth_provider = provider


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)
) -> User:
    """
    Core authentication dependency. Returns the active user context.
    In local development without auth tokens, returns the development admin user.
    """
    # In production, validate JWT signature, expiration, and user state
    return await _auth_provider.get_user_by_id("usr_001")


def has_permission(user: User, permission: str) -> bool:
    """Check if user has a specific permission or superuser/wildcard."""
    if user.is_superuser:
        return True
    if "*" in user.permissions:
        return True
    if permission in user.permissions:
        return True
    # Check wildcard prefixes e.g. module.overview.*
    prefix = permission.rsplit(".", 1)[0] + ".*"
    return prefix in user.permissions


def require_permission(permission: str):
    """FastAPI dependency to require a specific permission."""
    from fastapi import Depends

    async def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission}' required"
            )
        return current_user

    return _dependency

