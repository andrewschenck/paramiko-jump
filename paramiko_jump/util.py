from getpass import getpass
from paramiko_jump.client import SSHJumpClient

from typing import (
    AnyStr,
    Tuple,
    Sequence,
    List,
    BinaryIO,
    SupportsInt,
)

Prompt = Tuple[AnyStr, bool]

class JumpHost:

    def __init__(self,hostname,username,password,auth_handler=None):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.auth_handler = auth_handler
        self.jumper = SSHJumpClient(auth_handler=auth_handler)

    def __enter__(self):
        self.jumper.connect(hostname=self.hostname,username=self.username,password=self.password,look_for_keys=False,allow_agent=False)
        return self.jumper

    def __exit__(self):
        self.jumper.close()

def duo_auth(password: AnyStr = "", duo_push: BinaryIO = True,passcode: SupportsInt = 0):
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

            if 'password' in prompt.lower() and password:
                answers.append(password)
            elif 'duo' in prompt.lower():
                if duo_push is True:
                    print("Approve Duo Mobile Login Request On Your Device ")
                    answers.append("1")
                else:
                    if passcode:
                        answers.append(passcode)
                    else:
                        input_ = input if show_input else getpass
                        answers.append(input_(prompt))
            else:
                input_ = input if show_input else getpass
                answers.append(input_(prompt))
        return answers

    return duo_handler