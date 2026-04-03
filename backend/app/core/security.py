"""Security utilities for authentication and authorization."""

from __future__ import annotations

import hashlib
import secrets
from collections import defaultdict, deque
from datetime import datetime, timedelta
from threading import Lock
from time import monotonic
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Argon2id for password hashing (more secure than bcrypt)
ph = PasswordHasher(
    time_cost=3,  # Number of iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,  # Number of threads
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash."""
    try:
        ph.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False


def generate_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Hash a token for storage (SHA256)."""
    return hashlib.sha256(token.encode()).hexdigest()


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Validate password strength.
    
    Returns (is_valid, list_of_violations).
    """
    violations = []
    
    if len(password) < 8:
        violations.append("Password must be at least 8 characters long")
    
    if len(password) > 128:
        violations.append("Password must be less than 128 characters")
    
    if not any(c.isupper() for c in password):
        violations.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        violations.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        violations.append("Password must contain at least one digit")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        violations.append("Password must contain at least one special character")
    
    return len(violations) == 0, violations


class InMemoryRateLimiter:
    """Rate limiter using sliding window algorithm."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = monotonic()
        with self._lock:
            queue = self._events[key]
            threshold = now - self.window_seconds
            while queue and queue[0] < threshold:
                queue.popleft()

            if len(queue) >= self.max_requests:
                return False

            queue.append(now)
            return True

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key."""
        now = monotonic()
        with self._lock:
            queue = self._events[key]
            threshold = now - self.window_seconds
            while queue and queue[0] < threshold:
                queue.popleft()
            return max(0, self.max_requests - len(queue))


class BruteForceProtection:
    """Brute force protection for login attempts."""

    def __init__(
        self,
        max_attempts: int = 5,
        lockout_minutes: int = 15,
        incremental_lockout: bool = True,
    ) -> None:
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes
        self.incremental_lockout = incremental_lockout
        self._attempts: dict[str, int] = defaultdict(int)
        self._lockouts: dict[str, datetime] = {}
        self._lock = Lock()

    def record_failure(self, key: str) -> tuple[bool, int]:
        """Record a failed login attempt.
        
        Returns (is_locked, remaining_attempts).
        """
        with self._lock:
            self._attempts[key] += 1
            remaining = self.max_attempts - self._attempts[key]
            
            if remaining <= 0:
                # Lock the account
                lockout_duration = self.lockout_minutes
                if self.incremental_lockout:
                    # Incremental lockout: 15, 30, 60, 120, 240 minutes
                    multiplier = 2 ** min(self._attempts[key] // self.max_attempts - 1, 4)
                    lockout_duration = self.lockout_minutes * multiplier
                
                self._lockouts[key] = datetime.utcnow() + timedelta(minutes=lockout_duration)
                return True, 0
            
            return False, remaining

    def is_locked(self, key: str) -> tuple[bool, datetime | None]:
        """Check if a key is locked out."""
        with self._lock:
            if key not in self._lockouts:
                return False, None
            
            if datetime.utcnow() > self._lockouts[key]:
                # Lockout expired, reset
                del self._lockouts[key]
                self._attempts[key] = 0
                return False, None
            
            return True, self._lockouts[key]

    def reset(self, key: str) -> None:
        """Reset attempts for a key (after successful login)."""
        with self._lock:
            self._attempts[key] = 0
            if key in self._lockouts:
                del self._lockouts[key]


# Global instances
rate_limiter = InMemoryRateLimiter(max_requests=180, window_seconds=60)
brute_force_protection = BruteForceProtection(max_attempts=5, lockout_minutes=15)