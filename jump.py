"""

A simple recipe for an easy approach to using paramiko to SSH
through a "Jump Host", with support for keyboard-interactive
multi-factor-authentication.

<aschenck@gmail.com>
"""

from getpass import getpass, getuser
from typing import (
    AnyStr,
    Callable,
    Optional,
    Tuple,
    Union,
)

import paramiko

Host = Union[AnyStr, Tuple[AnyStr, int]]


class SSHJumpClient(paramiko.SSHClient):
    """
    Manage an SSH session which is being proxied through a "Jump Host".
    """

    def __init__(
            self,
            jump_host: Host,
            jump_user: Optional[AnyStr] = None,
            auth_handler: Optional[Callable] = None,
    ):
        """
        Construct a new instance of :class:`SSHJumpClient`

        :param jump_host: A ('host', port) or 'host' representation
            of the "Jump Host".
        :param jump_user: If specified, used as the username during
            "Jump Host" authentication.
        :param auth_handler: If specified, used as the auth handler
            callback during interactive authentication.
        """
        super().__init__()

        if isinstance(jump_host, str):
            jump_host = (jump_host, 22)
        self._jump_host = jump_host
        self._jump_user = jump_user or getuser()

        if auth_handler:
            self._auth_handler = auth_handler
        else:
            def _default_auth_handler(title, instructions, prompt_list):
                # This is the auth handler callback, for MFA sessions
                answers = []
                if title:
                    print(title.strip())
                if instructions:
                    print(instructions.strip())
                for prompt, show_input in prompt_list:
                    input_ = input if show_input else getpass
                    print(prompt.strip(), end=' ')
                    answers.append(input_())
                return answers
            self._auth_handler = _default_auth_handler

        self._jump_channel = None

    def _connect_jump_channel(self, target_host: Host) -> paramiko.Channel:
        """
        Given a :class:`paramiko.SSHClient` instance,

        - Create, connect, and authenticate a "Jump Host" proxy
          session for the client instance.
        - Create a command channel from the authenticated "Jump Host"
          proxy session.

        :param target_host: A ('host', port) representation of the
            target host.
        :return: A :class`paramiko.Channel` for the "Jump Host".
        """

        # This constructor is incorrectly annotated in paramiko
        transport = paramiko.Transport(self._jump_host)
        transport.start_client()

        # Authenticate using interactive mode
        transport.auth_interactive(
            username=self._jump_user,
            handler=self._auth_handler,
        )

        # Snag a channel from this now-authenticated session...
        self._jump_channel = transport.open_channel(
            kind='direct-tcpip',
            dest_addr=target_host,
            src_addr=self._jump_host,
        )

        return self._jump_channel

    def connect(self, **kwargs) -> None:
        target_host = kwargs.pop('hostname', None)
        if not target_host:
            raise ValueError('hostname= required')
        target_host_port = kwargs.pop('port', 22)

        self._connect_jump_channel((target_host, target_host_port))
        super().connect(
            hostname=target_host,
            port=target_host_port,
            sock=self._jump_channel,  # Inject the Jump Host channel
            **kwargs,
        )

    def close(self) -> None:
        super().close()
        if self._jump_channel.active:
            self._jump_channel.close()
