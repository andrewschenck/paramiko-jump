"""

Objects provided by this module:

    :class:`SSHJumpClient`
    :class:`DummyAuthHandler`
    :func:`jump_host`
    :func:`simple_auth_handler`

"""

from contextlib import contextmanager
from getpass import getpass

from socket import socket

from typing import (
    AnyStr,
    Callable,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    Any,
    Dict,
    Iterator,
)

from paramiko import AutoAddPolicy, PKey
from paramiko.client import SSHClient
from paramiko.config import SSH_PORT


_Host = Union[AnyStr, Tuple[AnyStr, int]]
_Prompt = Tuple[AnyStr, bool]


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
    ) -> None:
        """
        SSHJumpClient constructor, which is a subclass of
        paramiko.client.SSHClient.
        
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
        self._jump_session: Optional[SSHClient] = jump_session
        j: Optional[SSHClient] = self._jump_session
        if j is not None and not hasattr(j, '_transport'):
            raise TypeError(f'bad jump_session: {j}')
        self._auth_handler: Optional[Callable[..., Any]] = auth_handler

    def __repr__(self) -> str:
        """Return repr(self).

        :return: The class name and the jump session and auth handler.
        """
        return (f'{self.__class__.__name__}('
                f'jump_session={self._jump_session!r}, '
                f'auth_handler={self._auth_handler!r})')

    def __str__(self) -> str:
        """String representation of the object.

        :return: The class name.
        """
        return self.__class__.__name__

    def _auth(
            self,
            username: AnyStr,
            password: Optional[AnyStr] = None,
            pkey: Optional[PKey] = None,
            key_filenames: Optional[AnyStr] = None,
            allow_agent: bool = True,
            look_for_keys: bool = True,
            gss_auth: bool = False,
            gss_kex: bool = False,
            gss_deleg_creds: bool = True,
            gss_host: Optional[AnyStr] = None,
            passphrase: Optional[AnyStr] = None,
    ) -> None:  # pylint: disable=R0913
        """
        Authenticate to the server.
        
        :param username: 
            Username to authenticate with.
        :param password: 
            Password to authenticate with, defaults to None
        :param pkey:
            Private key file to use for authentication, defaults to None
        :param key_filenames:
            Private key filenames to use for authentication, defaults to None
        :param allow_agent:
            Allow local SSH Agent to provide private key files, defaults to True
        :param look_for_keys:
            Look for keys in default locations, defaults to True
        :param gss_auth:
            Allow GSS-API authentication, defaults to False
        :param gss_kex:
            Allow GSS-API key exchange, defaults to False
        :param gss_deleg_creds:
            Delegate GSS-API credentials from client to server, defaults to True
        :param gss_host:
            Hostname to use in GSS-API authentication, defaults to None
        :param passphrase:
            Passphrase to use for private key, defaults to None
        :return: None
        """
        if callable(self._auth_handler):
            # Ignore type issues here, as the super class does
            # not share _transport information (which is private)
            return self._transport.auth_interactive( # type: ignore
                username=username,
                handler=self._auth_handler,
            )

        return super()._auth( # type: ignore
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
            hostname: AnyStr,
            port: int = SSH_PORT,
            username: Optional[AnyStr] = None,
            password: Optional[AnyStr] = None,
            pkey: Optional[PKey] = None,
            key_filename: Optional[AnyStr] = None,
            timeout: Optional[int] = None,
            allow_agent: bool = True,
            look_for_keys: bool = True,
            compress: bool = False,
            sock: Optional[socket] = None,
            gss_auth: bool = False,
            gss_kex: bool = False,
            gss_deleg_creds: bool = True,
            gss_host: Optional[str] = None,
            banner_timeout: Optional[int] = None,
            auth_timeout: Optional[int] = None,
            gss_trust_dns: bool = True,
            passphrase: Optional[AnyStr] = None,
            disabled_algorithms: Optional[Dict[AnyStr, List[AnyStr]]] = None,
    ) -> None:  # pylint: disable=R0913,R0914
        """
        Connect to an SSH server and authenticate to it.

        :param hostname: 
            Hostname or IP address of the remote host.
        :param port:
            Port number of the remote host, defaults to SSH_PORT (22)
        :param username:
            Username to authenticate as, defaults to None
        :param password:
            Password to authenticate with, defaults to None
        :param pkey:
            PKey object for private key, defaults to None
        :param key_filename:
            Filename of the private key file, defaults to None
        :param timeout:
            Timeout for the TCP connect, defaults to None
        :param allow_agent:
            Set to False to disable connecting to the SSH agent, defaults to True
        :param look_for_keys:
            Set to False to disable searching for discoverable private key files, defaults to True
        :param compress:
            Set to True to turn on compression, defaults to False
        :param sock:
            Existing socket to use for connection, defaults to None
        :param gss_auth:
            Set to True to allow GSS-API authentication, defaults to False
        :param gss_kex:
            Set to True to allow GSS-API key exchange, defaults to False
        :param gss_deleg_creds:
            Set to True to delegate GSS-API credentials from client to server, defaults to True
        :param gss_host:
            Hostname to use in GSS-API authentication, defaults to None
        :param banner_timeout:
            Timeout for the banner message, defaults to None
        :param auth_timeout:
            Timeout for authentication, defaults to None
        :param gss_trust_dns:
            Set to False to disable DNS lookups for GSS-API, defaults to True
        :param passphrase:
            Passphrase to use for private key, defaults to None
        :param disabled_algorithms:
            A dictionary of disabled algorithms, defaults to None
        :raises ValueError:
            If jump_session and sock are both provided as arguments; 
            they are mutually exclusive
        :return: None
        """
        if self._jump_session is not None:
            if sock is not None:
                raise ValueError('jump_session= and sock= are mutually '
                                 'exclusive')
            transport = self._jump_session._transport  # pylint: disable=W0212 # type: ignore
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
        )


class DummyAuthHandler:
    """Stateful auth handler for paramiko that will return a list of
     auth parameters for every CLI prompt

    Example
    -------
        >>> from paramiko_jump import DummyAuthHandler
        >>> handler = DummyAuthHandler(['password'], ['1'])
        >>> handler()
        ['password']
        >>> handler()
        ['1']

    """

    def __init__(self, *items):
        self._iterator = iter(items)

    def __call__(self, *args, **kwargs):
        try:
            return next(self)
        except StopIteration:
            return []

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._iterator)


@contextmanager
def jump_host(
        hostname: AnyStr,
        username: AnyStr,
        password: AnyStr,
        auth_handler: Optional[Callable[..., Any]] = None,
        look_for_keys: bool = True,
        auto_add_missing_key_policy: bool = False,
) -> Iterator:  # pylint: disable=R0913
    """

    Example
    -------
    >>> from paramiko_jump import SSHJumpClient, simple_auth_handler
    >>> with jump_host(
    >>>         hostname='jump-host',
    >>>         username='username') as jump:
    >>>     target = SSHJumpClient(jump_session=jumper)
    >>>     target.connect(hostname='target-host', username='target-user')
    >>>     _, stdout, _ = target.exec_command('sh ver')
    >>>     print(stdout.read().decode())
    >>>     target.close()


    :param hostname:
        The hostname of the jump host.
    :param username:
        The username used to authenticate with the jump host.
    :param password:
        Password used to authenticate with the jump host.
    :param auth_handler:
        If provided, keyboard-interactive authentication will be
        implemented, using this handler as the callback. If this
        is set to None, use Paramiko's default authentication
        algorithm instead of forcing keyboard-interactive
        authentication.
    :param look_for_keys:
        Gives Paramiko permission to look around in our ~/.ssh
        folder to discover SSH keys on its own (Default False)
    :param auto_add_missing_key_policy:
        If set to True, setting the missing host key policy on the jump is set
        to auto add policy. (Default False)
    :return:
        Connected SSHJumpClient instance context.
    """
    jumper = SSHJumpClient(auth_handler=auth_handler)
    if auto_add_missing_key_policy:
        jumper.set_missing_host_key_policy(AutoAddPolicy())
    try:

        jumper.connect(
            hostname=hostname,
            username=username,
            password=password,
            look_for_keys=look_for_keys,
            allow_agent=False,
        )
        yield jumper
    finally:
        jumper.close()


def simple_auth_handler(
        title: AnyStr,
        instructions: AnyStr,
        prompt_list: Sequence[_Prompt],
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
    :return:
        A list of user input, in the order that the prompts were
        presented.
    """
    answers = []
    if title:
        print(title)
    if instructions:
        print(instructions)

    for prompt, show_input in prompt_list:
        input_ = input if show_input else getpass
        answers.append(input_(prompt)) # type: ignore
    return answers
