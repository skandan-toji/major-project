"""
session_manager.py -- Session Management for Control Center

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

Manages all active and expired sessions on the Control Center side.
Tracks session state, expiry, sequence numbers, and blacklists
expired session IDs to prevent reuse.

Session Parameters:
    Session ID       : 16 bytes (os.urandom)
    Session Lifetime : 900 seconds (15 minutes)
    Sequence Number  : 32-bit unsigned int, starts at 0
"""

import time
import os


class Session:
    """
    Represents one active secure session between a Smart Meter
    and the Control Center.

    Attributes:
        session_id (bytes):           16-byte unique session identifier.
        meter_id (str):               Smart meter identifier e.g. "SM_001".
        aes_key (bytes):              32-byte AES-256 session key.
        nonce (bytes):                12-byte AES-GCM nonce for this session.
        created_at (float):           Unix timestamp when session was created.
        expiry_time (float):          created_at + 900 seconds.
        last_sequence_number (int):   Last valid sequence number seen.
        active (bool):                True if session is still valid.
    """

    SESSION_LIFETIME = 900  # 15 minutes

    def __init__(self, session_id, meter_id, aes_key, nonce):
        """
        Initialize a new session with all attributes.

        Args:
            session_id (bytes): 16-byte unique session identifier.
            meter_id (str):     Smart meter identifier.
            aes_key (bytes):    32-byte AES-256 session key.
            nonce (bytes):      12-byte AES-GCM nonce.
        """
        self.session_id = session_id
        self.meter_id = meter_id
        self.aes_key = aes_key
        self.nonce = nonce
        self.created_at = time.time()
        self.expiry_time = self.created_at + self.SESSION_LIFETIME
        self.last_sequence_number = 0
        self.active = True

    def is_expired(self) -> bool:
        """
        Returns True if the current time exceeds the session expiry_time.

        Returns:
            bool: True if expired, False if still within lifetime.
        """
        return time.time() > self.expiry_time

    def is_valid(self) -> bool:
        """
        Returns True if the session is both active and not expired.

        Returns:
            bool: True if session can still accept packets.
        """
        return self.active and not self.is_expired()

    def increment_sequence(self) -> int:
        """
        Increments last_sequence_number by 1 and returns the new value.

        Returns:
            int: The new (incremented) sequence number.
        """
        self.last_sequence_number += 1
        return self.last_sequence_number

    def expected_sequence(self) -> int:
        """
        Returns the next expected sequence number.

        Returns:
            int: last_sequence_number + 1
        """
        return self.last_sequence_number + 1

    def time_remaining(self) -> float:
        """
        Returns the number of seconds until session expiry.

        Returns:
            float: Seconds remaining. 0.0 if already expired.
        """
        remaining = self.expiry_time - time.time()
        return max(0.0, remaining)

    def to_dict(self) -> dict:
        """
        Returns session info as a dictionary for logging and API responses.
        Converts session_id to hex string. Does NOT include aes_key.

        Returns:
            dict: Session information:
                {
                    "session_id": str (hex),
                    "meter_id": str,
                    "created_at": float,
                    "expiry_time": float,
                    "last_sequence_number": int,
                    "active": bool,
                    "time_remaining": float
                }
        """
        return {
            "session_id": self.session_id.hex(),
            "meter_id": self.meter_id,
            "created_at": self.created_at,
            "expiry_time": self.expiry_time,
            "last_sequence_number": self.last_sequence_number,
            "active": self.active,
            "time_remaining": self.time_remaining(),
        }


class SessionManager:
    """
    Manages all active and expired sessions on the Control Center.

    Internal storage:
        active_sessions (dict):  session_id(bytes) -> Session object
        meter_sessions (dict):   meter_id(str) -> session_id(bytes)
        expired_sessions (dict): session_id(bytes) -> expired_at(float)
    """

    BLACKLIST_TTL = 86400  # 24 hours in seconds

    def __init__(self):
        """
        Initialize the SessionManager with empty session stores.
        """
        self.active_sessions = {}
        self.meter_sessions = {}
        self.expired_sessions = {}

    def create_session(self, meter_id: str,
                       aes_key: bytes,
                       nonce: bytes) -> Session:
        """
        Creates a new session for a meter.

        Steps:
            1. Generate session_id = os.urandom(16)
            2. If meter already has an active session, end it first
            3. Create Session object
            4. Store in active_sessions[session_id]
            5. Store in meter_sessions[meter_id] = session_id
            6. Return the Session object

        Args:
            meter_id (str):  Smart meter identifier e.g. "SM_001".
            aes_key (bytes): 32-byte AES-256 session key.
            nonce (bytes):   12-byte AES-GCM nonce.

        Returns:
            Session: The newly created Session object.
        """
        session_id = os.urandom(16)

        # End existing session for this meter if one exists
        if meter_id in self.meter_sessions:
            old_session_id = self.meter_sessions[meter_id]
            if old_session_id in self.active_sessions:
                self.end_session(old_session_id)

        session = Session(session_id, meter_id, aes_key, nonce)
        self.active_sessions[session_id] = session
        self.meter_sessions[meter_id] = session_id
        return session

    def get_session(self, session_id: bytes):
        """
        Retrieves a session by its session_id.

        Steps:
            1. Look up in active_sessions
            2. If not found: return None
            3. If found but expired: call end_session(), return None
            4. If found and valid: return Session object

        Args:
            session_id (bytes): The 16-byte session identifier.

        Returns:
            Session or None: The session if active and valid, else None.
        """
        session = self.active_sessions.get(session_id)
        if session is None:
            return None
        if session.is_expired():
            self.end_session(session_id)
            return None
        return session

    def get_session_by_hex(self, session_id_hex: str):
        """
        Retrieves a session by hex-encoded session_id string.

        Args:
            session_id_hex (str): Hex string of the 16-byte session ID.

        Returns:
            Session or None: The session if active and valid, else None.
        """
        try:
            session_id = bytes.fromhex(session_id_hex)
            return self.get_session(session_id)
        except (ValueError, TypeError):
            return None

    def get_meter_session(self, meter_id: str):
        """
        Gets the current active session for a specific meter.

        Args:
            meter_id (str): Smart meter identifier.

        Returns:
            Session or None: The active session, or None if no active session.
        """
        session_id = self.meter_sessions.get(meter_id)
        if session_id is None:
            return None
        return self.get_session(session_id)

    def end_session(self, session_id: bytes):
        """
        Ends a session and moves it to expired_sessions blacklist.

        Steps:
            1. Get session from active_sessions
            2. Set session.active = False
            3. Add to expired_sessions[session_id] = time.time()
            4. Remove from active_sessions
            5. Remove from meter_sessions if present

        Args:
            session_id (bytes): The 16-byte session identifier to end.
        """
        session = self.active_sessions.get(session_id)
        if session is None:
            return

        session.active = False
        self.expired_sessions[session_id] = time.time()
        del self.active_sessions[session_id]

        # Remove from meter_sessions if this is the current session
        if (session.meter_id in self.meter_sessions and
                self.meter_sessions[session.meter_id] == session_id):
            del self.meter_sessions[session.meter_id]

    def is_session_blacklisted(self, session_id: bytes) -> bool:
        """
        Checks if session_id exists in expired_sessions blacklist.

        Args:
            session_id (bytes): The 16-byte session identifier.

        Returns:
            bool: True if session was previously ended/expired.
        """
        return session_id in self.expired_sessions

    def cleanup_expired(self):
        """
        Removes entries from expired_sessions older than 24 hours.
        Prevents unbounded memory growth from blacklist accumulation.
        Call this periodically in long-running simulations.
        """
        cutoff = time.time() - self.BLACKLIST_TTL
        to_remove = [
            sid for sid, expired_at in self.expired_sessions.items()
            if expired_at < cutoff
        ]
        for sid in to_remove:
            del self.expired_sessions[sid]

    def expire_all_timed_out(self):
        """
        Checks all active sessions and ends any that have expired.
        Call this periodically in the simulation loop to keep
        active_sessions clean.
        """
        expired_ids = [
            sid for sid, session in self.active_sessions.items()
            if session.is_expired()
        ]
        for sid in expired_ids:
            self.end_session(sid)

    def list_active_sessions(self) -> list:
        """
        Returns a list of to_dict() for all active sessions.
        Calls expire_all_timed_out() first to clean stale ones.

        Returns:
            list: List of session info dicts.
        """
        self.expire_all_timed_out()
        return [
            session.to_dict()
            for session in self.active_sessions.values()
        ]

    def get_stats(self) -> dict:
        """
        Returns overall session manager statistics.

        Returns:
            dict:
                {
                    "total_active": int,
                    "total_expired": int,
                    "meters_online": list of meter_ids with active sessions
                }
        """
        self.expire_all_timed_out()
        return {
            "total_active": len(self.active_sessions),
            "total_expired": len(self.expired_sessions),
            "meters_online": list(self.meter_sessions.keys()),
        }


print("[MODULE LOADED] session_manager.py ready")
