"""Security utilities for password hashing and brute force protection."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic

from argon2 import PasswordHasher

from app.core.config import get_settings

# Argon2id password hasher - more secure than bcrypt
ph = PasswordHasher(
    time_cost=2,  # Number of iterations
    memory_cost=65536,  # 64 MB
    parallelism=2,  # Number of threads
    hash_len=32,  # Hash length
    salt_len=16,  # Salt length
)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash."""
    try:
        ph.verify(password_hash, password)
        return True
    except Exception:
        return False


def hash_token(token: str) -> str:
    """Hash a token using SHA256."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Validate password meets minimum security requirements."""
    settings = get_settings()
    violations: list[str] = []

    if len(password) < settings.password_min_length:
        violations.append(f"minimum_length<{settings.password_min_length}")

    if settings.password_require_uppercase and not any(c.isupper() for c in password):
        violations.append("missing_uppercase")

    if settings.password_require_lowercase and not any(c.islower() for c in password):
        violations.append("missing_lowercase")

    if settings.password_require_digit and not any(c.isdigit() for c in password):
        violations.append("missing_digit")

    if settings.password_require_special and not any(
        (not c.isalnum()) and (not c.isspace()) for c in password
    ):
        violations.append("missing_special_char")

    return len(violations) == 0, violations


@dataclass
class FailedAttempt:
    """Track failed login attempts for an identifier."""

    count: int = 0
    first_attempt: float = field(default_factory=monotonic)
    locked_until: float | None = None


@dataclass
class BruteForceProtection:
    """Brute force protection for login attempts."""

    max_attempts: int = 5
    lockout_duration: float = 900.0  # 15 minutes in seconds
    cleanup_interval: float = 3600.0  # 1 hour in seconds
    _attempts: dict[str, FailedAttempt] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)
    _last_cleanup: float = field(default_factory=monotonic)

    def record_failure(self, identifier: str) -> None:
        """Record a failed login attempt."""
        with self._lock:
            now = monotonic()

            # Cleanup old entries periodically
            if now - self._last_cleanup > self.cleanup_interval:
                self._cleanup(now)
                self._last_cleanup = now

            attempt = self._attempts.get(identifier)
            if attempt is None:
                attempt = FailedAttempt()
                self._attempts[identifier] = attempt

            attempt.count += 1

            # Lock the account if max attempts reached
            if attempt.count >= self.max_attempts:
                attempt.locked_until = now + self.lockout_duration

    def is_locked(self, identifier: str) -> bool:
        """Check if an identifier is locked out."""
        with self._lock:
            attempt = self._attempts.get(identifier)
            if attempt is None:
                return False

            if attempt.locked_until is None:
                return False

            # Check if lockout period has passed
            if monotonic() > attempt.locked_until:
                # Reset after lockout expires
                del self._attempts[identifier]
                return False

            return True

    def reset(self, identifier: str) -> None:
        """Reset failed attempts for an identifier."""
        with self._lock:
            self._attempts.pop(identifier, None)

    def _cleanup(self, now: float) -> None:
        """Remove expired entries."""
        expired = [
            identifier
            for identifier, attempt in self._attempts.items()
            if attempt.locked_until and now > attempt.locked_until
        ]
        for identifier in expired:
            del self._attempts[identifier]


# Global brute force protection instance
brute_force_protection = BruteForceProtection()


@dataclass
class InMemoryRateLimiter:
    """Simple in-memory rate limiter."""

    max_requests: int = 100
    window_seconds: float = 60.0
    _requests: dict[str, list[float]] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def allow(self, key: str) -> bool:
        """Check if a request is allowed for the given key."""
        with self._lock:
            now = monotonic()
            cutoff = now - self.window_seconds

            # Get or create request list
            if key not in self._requests:
                self._requests[key] = []

            # Remove old requests outside the window
            self._requests[key] = [
                ts for ts in self._requests[key] if ts > cutoff
            ]

            # Check if under limit
            if len(self._requests[key]) >= self.max_requests:
                return False

            # Record this request
            self._requests[key].append(now)
            return True