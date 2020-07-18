"""

A simple recipe for an easy approach to using paramiko to SSH
through a "Jump Host", with support for keyboard-interactive
multi-factor-authentication.

"""

from getpass import getpass, getuser
from typing import AnyStr, Optional, Tuple, Union

import paramiko


Host = Union[AnyStr, Tuple[AnyStr, int]]


class SSHJumpClient(paramiko.SSHClient):
    """
    Manage an SSH session which is being proxied through a "Jump Host".
    """

    def __init__(self, jump_host: Host, jump_user: Optional[AnyStr] = None):
        """
        Construct a new instance of :class:`SSHJumpClient`

        :param jump_host: A ('host', port) or 'host' representation
            of the "Jump Host".
        :param jump_user: If specified, used as the username during
            "Jump Host" authentication.
        """
        super().__init__()

        if isinstance(jump_host, str):
            jump_host = (jump_host, 22)
        self._jump_host = jump_host
        self._jump_user = jump_user or getuser()
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
        def auth_handler(title, instructions, prompt_list):
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

        # This constructor is incorrectly annotated in paramiko
        transport = paramiko.Transport(self._jump_host)
        transport.start_client()

        transport.auth_interactive(
            username=self._jump_user,
            handler=auth_handler,
        )

        # Snag a channel from this now-authenticated session...
        self._jump_channel = transport.open_channel(
            kind='direct-tcpip',
            dest_addr=target_host,
            src_addr=self._jump_host,
        )

        return self._jump_channel

    def connect(self, **kwargs) -> None:
        target_host = kwargs.pop('hostname')
        if isinstance(target_host, str):
            target_host = (target_host, 22)

        self._connect_jump_channel(target_host)
        super().connect(
            hostname=target_host[0],
            port=target_host[1],
            sock=self._jump_channel, # Inject the Jump Host channel
            **kwargs,
        )

    def close(self) -> None:
        super().close()
        if self._jump_channel.active:
            self._jump_channel.close()
##
# Test
##
if __name__ == '__main__':
    jump_host_example = 'jump-host-hostname'
    target_host_example = 'target-host-hostname'

    username = input(f'{target_host_example} Username: ')
    password = getpass(f'{target_host_example} Password: ')

    ssh = SSHJumpClient(jump_host=jump_host_example)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=target_host_example,
        username=username,
        password=password,
    )

    stdin, stdout, stderr = ssh.exec_command('show version')
    print(stdout.read())
