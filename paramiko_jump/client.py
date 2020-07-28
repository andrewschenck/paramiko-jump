"""

A simple recipe for an easy approach to using paramiko to SSH
through a "Jump Host", with support for keyboard-interactive
multi-factor-authentication.

"""

from getpass import getpass
from typing import (
    AnyStr,
    Callable,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from paramiko.client import SSH_PORT, SSHClient


Host = Union[AnyStr, Tuple[AnyStr, int]]
Prompt = Tuple[AnyStr, bool]


def simple_auth_handler(
        title: AnyStr,
        instructions: AnyStr,
        prompt_list: Sequence[Prompt],
) -> List[AnyStr]:
    """
    Authentication callback, for keyboard-interactive
    authentication.

    :param title:
        Displayed to the end user before anything else.
    :param instructions:
        Displayed to the end user. Typically contains text explaining
        the authentication scheme and / or legal disclaimers.
    :param prompt_list:
        A Sequence of (AnyStr, bool). Each string element is
        displayed as an end-user input prompt. The corresponding
        boolean element indicates whether the user input should
        be 'echoed' back to the terminal during the interaction.
    """
    answers = []
    if title:
        print(title)
    if instructions:
        print(instructions)

    for prompt, show_input in prompt_list:
        input_ = input if show_input else getpass
        answers.append(input_(prompt))
    return answers

def duo_handler(
        title: AnyStr,
        instructions: AnyStr,
        prompt_list: Sequence[Prompt],
) -> List[AnyStr]:
    """
    The purpose of this handler is to automate auth handlers that use duo. This removes prompting the user to
    enter password and duo auth mode so that auth can be handled programmatically without user input at run time.

    Authentication callback, for keyboard-interactive
    authentication that uses DUO Auth.

    Example:
        # set the duo_handler password that will be entered to console
        duo_handler.password = password
        with SSHJumpClient(auth_handler=duo_handler) as jumper:
            jumper.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jumper.connect(
                hostname=jump_host,
                username=jump_user,
            )
            # Now I instantiate a session for the Jump Host <-> Target
            # Host connection, and inject the jump_session to use for
            # proxying.
            target = SSHJumpClient(jump_session=jumper)
            target.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            target.connect(
                hostname=target_host,
                username=username,
                password=password,
                look_for_keys=False,
                allow_agent=False,
            )
            _, stdout, _ = target.exec_command('sh ip int br')
            print(stdout.read().decode())
            target.close()

    :param title:
        Displayed to the end user before anything else.
    :param instructions:
        Displayed to the end user. Typically contains text explaining
        the authentication scheme and / or legal disclaimers.
    :param prompt_list:
        A Sequence of (AnyStr, bool). Each string element is
        displayed as an end-user input prompt. The corresponding
        boolean element indicates whether the user input should
        be 'echoed' back to the terminal during the interaction.
    """
    answers = []
    if title:
        print(title)
    if instructions:
        print(instructions)
    for prompt, show_input in prompt_list:

        if 'password' in prompt.lower() and duo_handler.password:
            input_ = duo_handler.password
            answers.append(input_)
        elif 'duo' in prompt.lower():
            print("Approve Duo Mobile Login Request On Your Device ")
            answers.append("1")
        else:
            input_ = input if show_input else getpass
            answers.append(input_(prompt))
    return answers

class SSHJumpClient(SSHClient):
    """
    Manage an SSH session which is optionally being proxied
    through a Jump Host.
    """

    def __init__(
            self,
            *,
            jump_session: SSHClient = None,
            auth_handler: Optional[Callable] = None,
    ):
        """
        :param jump_session:
            If provided, proxy SSH connections through the another
            instance of SSHClient. The underlying Transport object
            will be used to initiate a 'direct-tcpip' mode tunneling
            session.
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
    ):  # pylint: disable=R0913
        if callable(self._auth_handler):
            return self._transport.auth_interactive(
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
            gss_trust_dns=True,
            passphrase=None,
            disabled_algorithms=None,
    ):  # pylint: disable=R0913,R0914
        if self._jump_session is not None:
            if sock is not None:
                raise ValueError('jump_session= and sock= are mutually '
                                 'exclusive')
            transport = self._jump_session._transport  # pylint: disable=W0212
            sock = transport.open_channel(
                kind='direct-tcpip',
                dest_addr=(hostname, port),
                src_addr=transport.getpeername(),
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
        )
