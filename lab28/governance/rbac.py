"""
Layer 5 — Governance: Role-Based Access Control (RBAC)
Simple in-memory RBAC for demo purposes.
In production: use OPA, Casbin, or cloud IAM.
"""
from enum import Enum
from dataclasses import dataclass, field
import time
from typing import Optional


class Permission(str, Enum):
    CHAT = "chat"
    SEARCH = "search"
    INGEST = "ingest"
    ADMIN = "admin"
    METRICS = "metrics"


@dataclass
class Role:
    name: str
    permissions: set[Permission]
    rate_limit_per_min: int = 60

@dataclass
class APIKey:
    key_hash: str
    role: str
    created_at: float = field(default_factory=time.time)
    last_used: float = 0.0
    enabled: bool = True


class RBACManager:
    """Simple RBAC manager with rate limiting"""

    def __init__(self):
        self._roles: dict[str, Role] = {
            "admin": Role(
                name="admin",
                permissions={
                    Permission.CHAT, Permission.SEARCH,
                    Permission.INGEST, Permission.ADMIN,
                    Permission.METRICS
                },
                rate_limit_per_min=120,
            ),
            "developer": Role(
                name="developer",
                permissions={
                    Permission.CHAT, Permission.SEARCH,
                    Permission.INGEST, Permission.METRICS,
                },
                rate_limit_per_min=60,
            ),
            "viewer": Role(
                name="viewer",
                permissions={Permission.CHAT, Permission.SEARCH},
                rate_limit_per_min=20,
            ),
        }
        self._api_keys: dict[str, APIKey] = {}
        self._usage: dict[str, list[float]] = {}

    def register_key(self, key: str, role: str) -> None:
        import hashlib
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        if role not in self._roles:
            raise ValueError(f"Unknown role: {role}")
        self._api_keys[key_hash] = APIKey(key_hash=key_hash, role=role)
        self._usage[key_hash] = []

    def check_permission(self, api_key: str, permission: Permission) -> bool:
        import hashlib
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        apikey = self._api_keys.get(key_hash)
        if not apikey or not apikey.enabled:
            return False
        apikey.last_used = time.time()
        role = self._roles.get(apikey.role)
        if not role:
            return False
        return permission in role.permissions

    def check_rate_limit(self, api_key: str) -> bool:
        import hashlib
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        apikey = self._api_keys.get(key_hash)
        if not apikey:
            return False
        role = self._roles.get(apikey.role)
        if not role:
            return False
        now = time.time()
        window = self._usage.setdefault(key_hash, [])
        window[:] = [t for t in window if now - t < 60]
        if len(window) >= role.rate_limit_per_min:
            return False
        window.append(now)
        return True

    def disable_key(self, api_key: str) -> None:
        import hashlib
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        if key_hash in self._api_keys:
            self._api_keys[key_hash].enabled = False

    def enable_key(self, api_key: str) -> None:
        import hashlib
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        if key_hash in self._api_keys:
            self._api_keys[key_hash].enabled = True


# Global instance
rbac_manager = RBACManager()
