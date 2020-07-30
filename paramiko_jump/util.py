"""
Utility functions and classes designed to help simplify paramiko jump as well as add extra features.

"""
from getpass import getpass

from contextlib import contextmanager
from typing import (
    AnyStr,
    Tuple,
    Iterator,
    Sequence,
    Optional,
    Callable,
)
from paramiko_jump.client import SSHJumpClient

import paramiko


Prompt = Tuple[AnyStr, bool]
Optional[Callable] = None


class DummyAuthHandler:
    """Stateful auth handler for paramiko that will return a list of auth
     parameters for every CLI prompt

    Example
    -------
        >>> from paramiko_jump.util import DummyAuthHandler
        >>> handler = DummyAuthHandler(['password'],['1'])
        >>> handler()
        ['password']
        >>> handler()
        ['1']

    Attributes
    ----------
    _iterator: Iterator
        Iterator to iterate through all the objects in an iteratable object
    """

    def __init__(self, *items: Sequence):
        self._iterator = iter(items)

    def __call__(self, *args: Sequence, **kwargs: Sequence):
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
    auth_handler=None,
    look_for_keys=True,
):
    """
    Context manager for SSHJumpClient to further simplify the SSHJumpClient Context
    Manger by handling connecting and closing to the jump host

    Example
    -------
    >>> from getpass import getpass
    >>> import paramiko
    >>> from paramiko_jump import SSHJumpClient, simple_auth_handler
    >>> jump_hostname = 'network-tools'
    >>> jump_user = input(f'{jump_host} Username: ')
    >>> target_host1 = 'some-host-1'
    >>> password1 = getpass(f'{target_host1} Password: ')
    >>> with jump_host(hostname=jump_hostname,username=jump_user,password=password) as jump:
    >>>     target1 = SSHJumpClient(jump_session=jumper)
    >>>     target1.connect(
    >>>         hostname=target_host1,
    >>>         username=jump_user,
    >>>         password=password1,
    >>>         look_for_keys=False,
    >>>         allow_agent=False,
    >>>     )
    >>>     _, stdout, _ = target1.exec_command('sh ver')
    >>>     print(stdout.read().decode())
    >>>     target1.close()


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
        Gives Paramiko permission to look around in our ~/.ssh folder to discover
        SSH keys on its own (Default False)
    :return:
        Connected SSHJumpClient
    """
    jumper = SSHJumpClient(auth_handler=auth_handler)
    if not look_for_keys:
        jumper.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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
