"""

Jump Host / Multi-Factor Authentication / Virtual Circuit Support for
the Paramiko SSH Client.

This package extends the Paramiko SSH client to easily support Multi-
Factor-Authentication use-cases, Jump Host support, and Virtual
Circuits.

See the README for usage examples.

"""


__all__ = (
    'SSHJumpClient',
)

from typing import Callable, Optional

from paramiko.client import SSHClient
from paramiko.config import SSH_PORT


class SSHJumpClient(SSHClient):
    """
    Manage an SSH session which is optionally being proxied
    through a Jump Host.
    """

    def __init__(
            self,
            *,
            jump_session: Optional[SSHClient] = None,
            auth_handler: Optional[Callable] = None,
    ):
        """
        :param jump_session:
            If provided, proxy SSH connections through the another
            instance of SSHClient.
        :param auth_handler:
            If provided, keyboard-interactive authentication will be
            implemented, using this handler as the callback. If this
            is set to None, use Paramiko's default authentication
            algorithm instead of forcing keyboard-interactive
            authentication.
        """
        super().__init__()

        j = self._jump_session = jump_session
        if j is not None and not hasattr(j, '_transport'):
            raise TypeError(f'bad jump_session: {j}')
        self._auth_handler = auth_handler

    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'jump_session={self._jump_session!r}, '
                f'auth_handler={self._auth_handler!r})')

    def __str__(self):
        return self.__class__.__name__

    def _auth(
            self,
            username,
            password,
            pkey,
            key_filenames,
            allow_agent,
            look_for_keys,
            gss_auth,
            gss_kex,
            gss_deleg_creds,
            gss_host,
            passphrase,
    ):  # pylint: disable=too-many-arguments

        # pylint: disable=protected-access
        if callable(self._auth_handler):
            return self._transport.auth_interactive_dumb(
                username=username,
                handler=self._auth_handler,
            )

        return super()._auth(
            username=username,
            password=password,
            pkey=pkey,
            key_filenames=key_filenames,
            allow_agent=allow_agent,
            look_for_keys=look_for_keys,
            gss_auth=gss_auth,
            gss_kex=gss_kex,
            gss_deleg_creds=gss_deleg_creds,
            gss_host=gss_host,
            passphrase=passphrase,
        )

    def connect(
            self,
            hostname,
            port=SSH_PORT,
            username=None,
            password=None,
            pkey=None,
            key_filename=None,
            timeout=None,
            allow_agent=True,
            look_for_keys=True,
            compress=False,
            sock=None,
            gss_auth=False,
            gss_kex=False,
            gss_deleg_creds=True,
            gss_host=None,
            banner_timeout=None,
            auth_timeout=None,
            channel_timeout=None,
            gss_trust_dns=True,
            passphrase=None,
            disabled_algorithms=None,
            transport_factory=None,
            auth_strategy=None,
    ):  # pylint: disable=too-many-arguments, too-many-locals

        # pylint: disable=protected-access
        if self._jump_session is not None:
            if sock is not None:
                raise ValueError('jump_session= and sock= are mutually '
                                 'exclusive')
            transport = self._jump_session._transport
            sock = transport.open_channel(
                kind='direct-tcpip',
                dest_addr=(hostname, port),
                src_addr=transport.getpeername(),
                timeout=timeout,
            )

        return super().connect(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            pkey=pkey,
            key_filename=key_filename,
            timeout=timeout,
            allow_agent=allow_agent,
            look_for_keys=look_for_keys,
            compress=compress,
            sock=sock,
            gss_auth=gss_auth,
            gss_kex=gss_kex,
            gss_deleg_creds=gss_deleg_creds,
            gss_host=gss_host,
            banner_timeout=banner_timeout,
            auth_timeout=auth_timeout,
            gss_trust_dns=gss_trust_dns,
            passphrase=passphrase,
            disabled_algorithms=disabled_algorithms,
            transport_factory=transport_factory,
            auth_strategy=auth_strategy,
        )
