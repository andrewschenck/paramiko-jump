from getpass import getpass
from typing import AnyStr, Sequence, List

from paramiko_jump.client import Prompt


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
