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


__all__ = (
    'MagicAuthHandler',
    'MultiFactorAuthHandler',
    'simple_auth_handler',
)


import logging

from getpass import getpass
from typing import (
    List,
    Optional,
    Sequence,
    Tuple,
)


_LOG = logging.getLogger(__name__)


def simple_auth_handler(
        title: str,
        instructions: str,
        prompt_list: Sequence[Tuple[str, bool]],
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
        answers.append(input_(prompt))  # type: ignore[operator]
    return answers


class MagicAuthHandler:
    """
    Stateful auth handler for paramiko that will return an auth parameter
    for each CLI prompt. This is useful for multi-factor authentication
    where the auth parameters change with each prompt (e.g. password
    followed by OTP).

    Example
    -------
        >>> from paramiko_jump import MagicAuthHandler
        >>> handler = MagicAuthHandler(['password'], ['1234'])
        >>> handler()
        ['password']
        >>> handler()
        ['1234']


    This class is deprecated by the ``MultiFactorAuthHandler``; use that
    class instead for new use cases.
    """

    def __init__(self, *items):
        """
        :param items:
            Auth responses to be returned by the handler. Each should be a
            List.
        """
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


class MultiFactorAuthHandler:
    """
    Stateful auth handler for paramiko that will return an auth parameter
    for each CLI prompt. This is useful for multi-factor authentication
    where the auth parameters change with each prompt (e.g. password
    followed by OTP).

    This class is a more flexible and feature-rich replacement for the
    deprecated ``MagicAuthHandler``.

    Example
    -------
        >>> from paramiko_jump import MultiFactorAuthHandler
        >>> handler = MultiFactorAuthHandler()
        >>> handler.add('password')
        >>> handler.add('1234')
        >>> handler()
        ['password']
        >>> handler()
        ['1234']

    Backwards-compatibility Example
    -------------------------------
        >>> from paramiko_jump import MultiFactorAuthHandler
        >>> handler = MultiFactorAuthHandler(['password'], ['1234'])
        >>> handler()
        ['password']
        >>> handler()
        ['1234']
    """

    def __init__(
            self,
            *auth_responses: List,
            show_title: bool = False,
            show_instructions: bool = False,
            show_prompts: bool = False,

    ):
        """
        :param auth_responses:
            Optional auth responses to be returned by the handler.
            Each item should be a List. This interface is backwards-
            compatible with the ``MagicAuthHandler``

            Alternatively, see the .add() method for an easier
            approach to adding auth responses after instantiation,
            without needing to pack them into Lists.
        :param show_title:
            If True, the title will be displayed.
        :param show_instructions:
            If True, the instructions will be displayed.
        :param show_prompts:
            If True, the authentication prompts will be displayed.
        """
        self._auth_responses = [*auth_responses]
        self._show_title = show_title
        self._show_instructions = show_instructions
        self._show_prompts = show_prompts

        self._iterator = None

    def __call__(
            self,
            title: Optional[str] = None,
            instructions: Optional[str] = None,
            prompt_list: Optional[List] = None,
    ):
        if self._show_title:
            _LOG.info(title)
        if self._show_instructions:
            _LOG.info(instructions)
        if self._show_prompts and prompt_list:
            for prompt, _ in prompt_list:
                _LOG.info(prompt)
        try:
            return next(self)
        except StopIteration:
            return []

    def __iter__(self):
        return self

    def __next__(self):
        if self._iterator is None:
            self._iterator = iter(self._auth_responses)

        return next(self._iterator)

    def add(self, auth_response: str) -> None:
        """
        Add an auth response to the handler.
        """
        # Pack it into a list as this is how Paramiko expects it.
        self._auth_responses.append([auth_response])
