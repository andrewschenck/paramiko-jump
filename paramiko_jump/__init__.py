"""

paramiko_jump: Paramiko + Jump Host + Multi-Factor Authentication

A simple recipe for an easy approach to using paramiko to SSH
through a "Jump Host", with support for keyboard-interactive
multi-factor-authentication.

"""

from paramiko_jump.client import SSHJumpClient
from paramiko_jump.handler import MagicAuthHandler, simple_auth_handler

__all__ = (
    'MagicAuthHandler',
    'SSHJumpClient',
    'simple_auth_handler',
)
