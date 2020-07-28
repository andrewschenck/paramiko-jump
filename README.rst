
The Problem
___________
"How do I use paramiko to SSH to a remote host while proxying through a jump host? Also, my jump host requires two-factor authentication!"

This seems to be a surprisingly common problem with a lot of not-very-working solutions. I figured I'd share my attempt with the world.


The Solution
------------
A simple class, ``SSHJumpClient``, which derives from ``paramiko.SSHClient`` and implements two additional features:

1) Easy chaining of SSH connections, supported through object injection. This enables the programmer to build a 'stack' of proxied SSH sessions, and tunnel commands through Jump Host infrastructure as-needed.

2) Easy authentication scheme override, forcing a keyboard-interactive authentication approach to be used. This should support most 2FA / MFA infrastructure approaches to SSH authentication.


Usage Example 1: Connect to a single target through a Jump Host
---------------------------------------------------------------

In this example, we disable SSH key-based authentication
between the Jump Host and the Target Host.

.. code-block::

    import paramiko
    from paramiko_jump import SSHJumpClient, simple_auth_handler

    jump_host = 'network-tools'
    target_host = 'some-switch-gw1'

    jump_user = input(f'{jump_host} Username: ')
    username = input(f'{target_host1} Username: ')
    password = getpass(f'{target_host1} Password: ')

    # My Jump Host requires keyboard-interactive multi-factor
    # authentication, so I use auth_handler=. Otherwise, I could
    # use paramiko.SSHClient here.
    with SSHJumpClient(auth_handler=simple_auth_handler) as jumper:
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


Example 2a: Open one Jump Channel, connect to multiple targets
--------------------------------------------------------------

In this example, we allow Paramiko to authenticate using its normal algorithm; if we have an SSH key on the Jump Host, Paramiko will use it to authenticate our session between the Jump Host and the Target Hosts.

.. code-block::

    from getpass import getpass

    import paramiko
    from paramiko_jump import SSHJumpClient, simple_auth_handler

    jump_host = 'network-tools'
    target_host1 = 'some-host-1'
    target_host2 = 'some-host-2'

    jump_user = input(f'{jump_host} Username: ')
    username1 = input(f'{target_host1} Username: ')
    password1 = getpass(f'{target_host1} Password: ')
    username2 = input(f'{target_host2} Username: ')
    password2 = getpass(f'{target_host2} Password: ')

    with SSHJumpClient(auth_handler=simple_auth_handler) as jumper:
        jumper.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jumper.connect(
            hostname=jump_host,
            username=jump_user,
        )

        target1 = SSHJumpClient(jump_session=jumper)
        target1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        target1.connect(
            hostname=target_host1,
            username=username1,
            password=password1,
            look_for_keys=False,
            allow_agent=False,
        )
        _, stdout, _ = target1.exec_command('sh ver')
        print(stdout.read().decode())
        target1.close()

        target2 = SSHJumpClient(jump_session=jumper)
        target2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        target2.connect(
            hostname=target_host1,
            username=username2,
            password=password2,
            look_for_keys=False,
            allow_agent=False,
        )
        _, stdout, _ = target2.exec_command('sh ip int br')
        print(stdout.read().decode())
        target2.close()


Example 2b: Same as 2a, no context manager (Just for fun)
---------------------------------------------------------

.. code-block::

    jumper = SSHJumpClient(auth_handler=simple_auth_handler)
    jumper.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jumper.connect(
        hostname=jump_host,
        username=jump_user,
    )

    target1 = SSHJumpClient(jump_session=jumper)
    target1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    target1.connect(
        hostname=target_host1,
        username=username1,
        password=password1,
        look_for_keys=False,
        allow_agent=False,
    )
    _, stdout, _ = target1.exec_command('sh ver')
    print(stdout.read().decode())
    target1.close()

    target2 = SSHJumpClient(jump_session=jumper)
    target2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    target2.connect(
        hostname=target_host2,
        username=username2,
        password=password2,
        look_for_keys=False,
        allow_agent=False,
    )
    _, stdout, _ = target2.exec_command('sh ip int br')
    print(stdout.read().decode())
    target2.close()

    jumper.close()


A Note on Authentication
------------------------

You must think about how you're authenticating from the Client to the Jump Host, as well as from the Jump Host to the Target Host. When connecting to the Target Host, be sure to pass authentication-related parameters into the connect() call. If you have an SSH key on the Jump Host, Paramiko will try to use it for authentication unless you override its behavior.

In order to successfully authenticate with infrastructure requiring keyboard-interactive multi-factor authentication, you will probably need to explicitly pass in auth_handler= during client construction. A basic handler callable is included, and should work for most use cases:

``from paramiko_jump import simple_auth_handler``

