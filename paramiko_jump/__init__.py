"""

paramiko_jump: Paramiko + Jump Host + Multi-Factor Authentication

A simple recipe for an easy approach to using paramiko to SSH
through a "Jump Host", with support for keyboard-interactive
multi-factor-authentication.

"""

import logging

from paramiko_jump.client import SSHJumpClient
from paramiko_jump.handler import (
    MagicAuthHandler,
    MultiFactorAuthHandler,
    simple_auth_handler,
)


logging.getLogger(__name__).addHandler(logging.NullHandler())


__all__ = (
    'MagicAuthHandler',
    'MultiFactorAuthHandler',
    'SSHJumpClient',
    'simple_auth_handler',
)
