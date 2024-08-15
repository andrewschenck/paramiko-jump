# paramiko-jump -- Multi-Factor Authentication and SSH Proxying with Paramiko

## The Problem

"How do I use paramiko to SSH to a remote host while proxying through a jump host? Also, my jump 
host requires two-factor authentication!"

This seems to be a surprisingly common problem with a lot of not-very-working solutions. I figured 
I'd share my attempt with the world.



## The Solution

A simple class, ``SSHJumpClient``, which derives from ``paramiko.SSHClient`` and implements two
additional features:

1) Easy chaining of SSH connections, supported through object injection. This enables the
programmer to build a 'stack' of proxied SSH sessions, and tunnel commands through infrastructure
as-needed.

2) Easy authentication scheme override, forcing a keyboard-interactive authentication approach to be
used. This should support most 2FA / MFA infrastructure approaches to SSH authentication. The 
keyboard-interactive authentication handler is injected, permitting easy integration with more 
advanced use cases.

Additionally, this package includes a special object which can provide Paramiko with everything it 
needs to successfully authenticate with a remote system using MFA infrastructure and single-use 
tokens.



## Installing paramiko-jump
    pip install paramiko_jump




## Usage Examples


### Quick Start: I don't need Jump Host / SSH Proxying features

If you don't need the Jump Host features but DO need to handle multi-factor authentication,
see the section on **Authentication Handlers**. You can use the ```simple_auth_handler``` or
```MagicAuthHandler``` to handle your authentication to a single host without ever proxying
another SSH session through it ('jumping').


### SSH Proxying Usage Example 1a: Connect to a single target through a Jump Host

In this most basic example, we connect to a Jump Host, then connect to a Target Host through it.
We are using keyboard-interactive authentication on the Jump Host by way of 
```auth_handler=simple_auth_handler``` and we are passing pre-determined username and password
credentials to the Target Host.


    from paramiko_jump import SSHJumpClient, simple_auth_handler

    ##
    # This Jump Host requires keyboard-interactive multi-factor
    # authentication, so I use auth_handler=. Otherwise, I could
    # use paramiko.SSHClient here.
    ##
    with SSHJumpClient(auth_handler=simple_auth_handler) as jumper:
        jumper.connect(
            hostname='jump-host',
            username='jump-user',
        )

        ##
        # Now I instantiate a session for the Jump Host <-> Target
        # Host connection, and inject the jump_session to use for
        # proxying.
        ##
        with SSHJumpClient(jump_session=jumper) as target:
            target.connect(
                hostname='target-host',
                username='target-user',
                password='target-password',
                look_for_keys=False,
                allow_agent=False,
            )
            stdin, stdout, stderr = target.exec_command('sh ip int br')
            output = stdout.readlines()
            print(output)


### SSH Proxying Usage Example 1b: Connect to a single target through a Jump Host

This example is functionally equivalent to Example 1a, with two key changes:

1) It doesn't use the context manager.
2) It applies paramiko.AutoAddPolicy() as the missing host key policy to the Jump Host and 
Target Host connections -- this tells the SSH processes to 'auto accept' the host key if it's not 
already known (be cautious!)


    import paramiko
    from paramiko_jump import SSHJumpClient, simple_auth_handler

    jumper = SSHJumpClient(auth_handler=simple_auth_handler)
    jumper.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jumper.connect(
        hostname='jump-host',
        username='jump-user',
    )

    # Now I instantiate a session for the Jump Host <-> Target
    # Host connection, and inject the jump_session to use for
    # proxying.
    target = SSHJumpClient(jump_session=jumper)
    target.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    target.connect(
        hostname='target-host',
        username='target-user',
        password='target-password',
        look_for_keys=False,
        allow_agent=False,
    )
    stdin, stdout, stderr = target.exec_command('sh ip int br')
    output = stdout.readlines()
    print(output)
    target.close()


### SSH Proxying Example 2: Open one Jump Channel, connect to multiple targets


    from getpass import getpass

    import paramiko
    from paramiko_jump import SSHJumpClient, simple_auth_handler

    with SSHJumpClient(auth_handler=simple_auth_handler) as jumper:
        jumper.connect(
            hostname='jump-host',
            username='jump-user',
        )

        target1 = SSHJumpClient(jump_session=jumper)
        target1.connect(
            hostname='target-host1',
            username='username',
            password='password',
            look_for_keys=False,
            allow_agent=False,
        )
        stdin, stdout, stderr = target1.exec_command('sh ver')
        print(stdout.read().decode())
        target1.close()

        target2 = SSHJumpClient(jump_session=jumper)
        target2.connect(
            hostname='target-host2',
            username='username',
            password='password',
            look_for_keys=False,
            allow_agent=False,
        )
        _, stdout, _ = target2.exec_command('sh ip int br')
        output = stdout.readlines()
        print(output)
        target2.close()


### SSH Proxying Example 3: Multiple-Hop SSH "Virtual Circuit"

You can build a 'virtual circuit' out of multiple SSH connections, each one proxying through 
the previous.

    from paramiko_jump import SSHJumpClient

    circuit = []

    hop1 = SSHJumpClient()
    hop1.connect('host1')
    circuit.append(hop1)

    hop2 = SSHJumpClient(jump_session=hop1)
    hop2.connect('host2')
    circuit.append(hop2)

    hop3 = SSHJumpClient(jump_session=hop2)
    hop3.connect('host3')
    circuit.append(hop3)

    hop4 = SSHJumpClient(jump_session=hop3)
    hop4.connect('host4')
    circuit.append(hop4)

    target = SSHJumpClient(jump_session=hop4)
    target.connect('target')
    circuit.append(target)

    stdin, stdout, stderr = target.exec_command('uptime')

    for session in reversed(circuit):
        session.close()



**********************

## Authentication Handlers

In order to successfully authenticate with infrastructure requiring keyboard-interactive 
multi-factor authentication, you will probably want to explicitly pass in auth_handler= during 
client construction.


### simple_auth_handler

 A basic handler callable is included, and should work for most keyboard-interactive use cases:

    ##
    # Keyboard-Interactive Authentication using simple_auth_handler
    ##

    from paramiko_jump import SSHJumpClient, simple_auth_handler

    with SSHJumpClient(auth_handler=simple_auth_handler) as jumper:
        jumper.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jumper.connect(
            hostname='somehost.example.com',
            username='username',
            look_for_keys=False,
        )
    stdin, stdout, stderr = jumper.exec_command('uptime')
    output = stdout.readlines()
    print(output)


### MagicAuthHandler

The ```MagicAuthHandler``` class is a more advanced handler that can be used to accomplish complex 
authentication sessions with automation -- even through MFA infrastructure. This is accomplished by
feeding the handler a sequence of responses which will be required during the authentication 
session, such as a password and OTP. Each item in the sequence should be a Python list.

    ##
    # Multi-Factor Authentication using the MagicAuthHandler
    ##

    from paramiko_jump import SSHJumpClient, MagicAuthHandler

    handler = MagicAuthHandler(['password'], ['1'])


    # First call to handler will return ['password']
    # Second call to handler will return ['1']

    with SSHJumpClient(auth_handler=handler) as jumper:
        jumper.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jumper.connect(
            hostname='somehost.example.com',
            username='username',
            look_for_keys=False,
        )
        stdin, stdout, stderr = jumper.exec_command('uptime')
        output = stdout.readlines()
        print(output)


### Password-Only Authentication

### SSH Key-Based Authentication

    ##
    # SSH key-based authentication
    ##

    # If I have an SSH key, I can use it to authenticate instead of using keyboard-interactive
    # authentication.
    #
    # In this example, my private key is managed by ssh-agent, but you can add a passphrase=
    # parameter to the connect() call if you have a passphrase-protected key and aren't using
    # ssh-agent.

    from paramiko_jump import SSHJumpClient
    with SSHJumpClient() as jumper:
        jumper.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jumper.connect(
            hostname='somehost.example.com',
            username='username,
            look_for_keys=True,
        )
        stdin, stdout, stderr = jumper.exec_command('uptime')
        output = stdout.readlines()
        print(output)


### User/Password Authentication
        
    ##
    # User/Password Authentication
    ##
    with SSHJumpClient() as jumper:
        jumper.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jumper.connect(
            hostname='somehost.example.com',
            username='ubuntu',
            password='password',
            look_for_keys=False,
        )
        _, stdout, _ = jumper.exec_command('ls')
        output = stdout.readlines()
        print(output)



## Troubleshooting


### Authentication Failures
When troubleshooting authentication failures, remember that Paramiko will be authenticating as a
client on each 'hop', and that it has strong preferences over which authentication scheme it will
be using. You can control authentication behavior by passing various parameters to the
```connect()``` call. Read ```paramiko.SSHClient._auth``` for more insight into how this works.


### "Missing Host Key" Errors
See Usage Example 1b for an example of how to use ```paramiko.AutoAddPolicy()``` to automatically
accept unknown host keys. This is a dangerous practice, but it can be useful for testing and
development.
