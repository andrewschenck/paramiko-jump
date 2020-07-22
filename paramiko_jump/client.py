"""

A simple recipe for an easy approach to using paramiko to SSH
through a "Jump Host", with support for keyboard-interactive
multi-factor-authentication.

"""


from getpass import getpass, getuser
from typing import (
    Any,
    AnyStr,
    Callable,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import paramiko


SSH_PORT = 22


Host = Union[AnyStr, Tuple[AnyStr, int]]
Prompt = Tuple[AnyStr, bool]


def default_auth_handler(
        title: AnyStr,
        instructions: AnyStr,
        prompt_list: Sequence[Prompt],
):
    """
    Authentication handler callback, for interactive
    authentication.
    """
    answers = []
    if title:
        print(title)
    if instructions:
        print(instructions)
    for prompt, show_input in prompt_list:
        input_ = input if show_input else getpass
        print(prompt, end=' ')
        answers.append(input_())
    return answers


class SSHJumpClient(paramiko.SSHClient):
    """
    Manage an SSH session which is optionally being proxied
    through a Jump Host.
    """

    def __init__(
            self,
            *,
            jump_host: Optional[Host] = None,
            jump_user: Optional[AnyStr] = None,
            auth_handler: Optional[Callable] = default_auth_handler,
            close_jump_channel: bool = True,
    ):
        """
        Construct a new instance of :class:`SSHJumpClient`

        :param jump_host: A ('host', port) or 'host' representation
            of the Jump Host.
        :param jump_user: Used as the username during Jump Host
            authentication.
        :param auth_handler: Used as the auth handler callback during
            interactive authentication of the Jump Channel. Set to
            None to use paramiko's default authentication algorithm
            instead of forcing interactive authentication.
        :param close_jump_channel: If set, calling this class's
            close() method with no additional arguments will close
            the Jump Channel in addition to closing the current SSH
            connection. If unset, the Jump Channel must be closed
            manually. This argument has no effect on the context
            manager, which will always close the Jump Channel on exit.
        """
        super().__init__()

        if isinstance(jump_host, (str, bytes)):
            jump_host = (jump_host, SSH_PORT)
        self._jump_host = jump_host
        self._jump_user = jump_user or getuser()
        self._auth_handler = auth_handler
        self._close_jump_channel = close_jump_channel
        self._jump_transport: Optional[paramiko.Transport] = None

    def __enter__(self):
        if self._jump_host:
            self._connect_jump_host()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close(close_jump_channel=True)
        super().__exit__(exc_type, exc_val, exc_tb)

    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'jump_host={self._jump_host!r}, '
                f'jump_user={self._jump_user!r}, '
                f'auth_handler={self._auth_handler!r}, '
                f'close_jump_channel={self._close_jump_channel})')

    def __str__(self):
        return self.__class__.__name__

    def _disconnect_jump_host(self) -> None:
        if self._jump_transport and self._jump_transport.active:
            self._jump_transport.close()

    def _connect_jump_host(self) -> None:
        """
        Given a :class:`paramiko.SSHClient` instance,

        - Create, connect, and authenticate a Jump Host proxy
          session for the client instance.
        - Create a command channel from the authenticated Jump Host
          proxy session.

        :return: A :class`paramiko.Channel` for the Jump Host.
        """
        # This constructor is incorrectly annotated in paramiko
        # noinspection PyTypeChecker
        self._jump_transport = paramiko.Transport(self._jump_host)
        self._jump_transport.start_client()

        # Authenticate using interactive mode
        if callable(self._auth_handler):
            self._jump_transport.auth_interactive(
                username=self._jump_user,
                handler=self._auth_handler,
            )
        else:
            # Authenticate using default paramiko algorithm
            self._jump_transport.connect(username=self._jump_user)

    # pylint: disable=R0913,R0914
    def connect(
            self,
            hostname: AnyStr,
            port: int = SSH_PORT,
            username: AnyStr = None,
            password: AnyStr = None,
            pkey: Any = None,
            key_filename: AnyStr = None,
            timeout: float = None,
            allow_agent: bool = True,
            look_for_keys: bool = True,
            compress: bool = False,
            sock=None,
            gss_auth: bool = False,
            gss_kex: bool = False,
            gss_deleg_creds: bool = True,
            gss_host: AnyStr = None,
            banner_timeout: float = None,
            auth_timeout: float = None,
            gss_trust_dns: bool = True,
            passphrase: AnyStr = None,
            disabled_algorithms: dict = None,
    ) -> None:
        # Matching the parent signature in order to satisfy Liskov

        if self._jump_host and not self._jump_transport:
            # We're in Jump Host mode but don't have a Jump Channel
            self._connect_jump_host()
            sock = self._jump_transport.open_channel(
                kind='direct-tcpip',
                dest_addr=(hostname, port),
                src_addr=self._jump_host,
            )

        super().connect(
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
        )

    # pylint: disable=W0221
    def close(self, *, close_jump_channel: bool = False) -> None:
        if self._close_jump_channel or close_jump_channel:
            self._disconnect_jump_host()
        super().close()
