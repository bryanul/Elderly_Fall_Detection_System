"""Person tracking and identity management."""

import time
from typing import Dict, Optional


class PersonTracker:
    """Manages person tracking and identity assignment."""

    def __init__(self, max_attempts: int = 5, attempt_timeout: float = 1.0):
        """
        Initialize person tracker.

        Args:
            max_attempts: Maximum identification attempts before marking as 'no id'
            attempt_timeout: Time window for counting attempts
        """
        self.track_id_to_identity: Dict[int, str] = {}
        self.track_id_attempts: Dict[int, int] = {}
        self.track_id_last_attempt: Dict[int, float] = {}
        self.max_attempts = max_attempts
        self.attempt_timeout = attempt_timeout

    def get_identity(self, track_id: int) -> Optional[str]:
        """Get the identity for a track ID."""
        return self.track_id_to_identity.get(track_id)

    def has_identity(self, track_id: int) -> bool:
        """Check if track ID has an assigned identity."""
        return track_id in self.track_id_to_identity

    def set_identity(self, track_id: int, identity: str) -> None:
        """Set identity for a track ID and reset attempt counter."""
        self.track_id_to_identity[track_id] = identity
        self.track_id_attempts.pop(track_id, None)

    def should_attempt_identification(self, track_id: int) -> bool:
        """
        Check if we should attempt identification for this track ID.

        Returns:
            True if should attempt, False if max attempts reached
        """
        now = time.time()
        last = self.track_id_last_attempt.get(track_id, 0)

        # Reset attempts if timeout exceeded
        if now - last > self.attempt_timeout:
            self.track_id_attempts[track_id] = 0

        self.track_id_last_attempt[track_id] = now

        # Check if max attempts reached
        attempts = self.track_id_attempts.get(track_id, 0)
        if attempts >= self.max_attempts:
            self.track_id_to_identity[track_id] = "no id"
            return False

        return True

    def increment_attempt(self, track_id: int) -> None:
        """Increment identification attempt counter for track ID."""
        self.track_id_attempts[track_id] = self.track_id_attempts.get(track_id, 0) + 1
