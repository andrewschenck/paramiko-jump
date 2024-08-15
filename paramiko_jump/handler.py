"""

Authentication Handlers

Authentication handlers are callbacks that we pass into
Paramiko.SSHClient, enabling us to have more fine-grained control
over the authentication process.

This module provides two authentication handlers:
    - simple_auth_handler, for simple keyboard-interactive use-cases
    - MagicAuthHandler, for mimicking keyboard-interactive authentication
      using pre-defined responses.


"""


from getpass import getpass
from typing import List, Sequence, Tuple


__all__ = (
    'MagicAuthHandler',
    'simple_auth_handler',
)


_Prompt = Tuple[str, bool]


def simple_auth_handler(
        title: str,
        instructions: str,
        prompt_list: Sequence[_Prompt],
) -> List[str]:
    """
    Authentication callback, for keyboard-interactive
    authentication.

    :param title:
        Displayed to the end user before anything else.
    :param instructions:
        Displayed to the end user. Typically contains text explaining
        the authentication scheme and / or legal disclaimers.
    :param prompt_list:
        A Sequence of (str, bool). Each string element is
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
        answers.append(input_(prompt))  # type: ignore
    return answers


class MagicAuthHandler:
    """
    Stateful auth handler for paramiko that will return a list of
    auth parameters for every CLI prompt. This is useful for multi-
    factor authentication where the auth parameters change with each
    prompt (e.g. password followed by OTP).

    Example
    -------
        >>> from paramiko_jump import MagicAuthHandler
        >>> handler = MagicAuthHandler(['password'], ['1234'])
        >>> handler()
        ['password']
        >>> handler()
        ['1234']


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
