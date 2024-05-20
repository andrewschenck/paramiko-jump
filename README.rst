
The Problem
___________
"How do I use paramiko to SSH to a remote host while proxying through a jump host? Also, my jump host requires two-factor authentication!"

This seems to be a surprisingly common problem with a lot of not-very-working solutions. I figured I'd share my attempt with the world.


The Solution
------------
A simple class, ``SSHJumpClient``, which derives from ``paramiko.SSHClient`` and implements two additional features:

1) Easy chaining of SSH connections, supported through object injection. This enables the programmer to build a 'stack' of proxied SSH sessions, and tunnel commands through infrastructure as-needed.

2) Easy authentication scheme override, forcing a keyboard-interactive authentication approach to be used. This should support most 2FA / MFA infrastructure approaches to SSH authentication. The keyboard-interactive authentication handler is injected, permitting easy integration with more advanced use cases.


Usage Example 1: Connect to a single target through a Jump Host
---------------------------------------------------------------
In this example, we use keyboard-interactive authentication on the Jump Host, and we tell Paramiko to 'auto add' (and accept) unknown Host Keys. (What could possibly go wrong?)

.. code-block:: python

    import paramiko
    from paramiko_jump import SSHJumpClient, simple_auth_handler

    # My Jump Host requires keyboard-interactive multi-factor
    # authentication, so I use auth_handler=. Otherwise, I could
    # use paramiko.SSHClient here.
    with SSHJumpClient(auth_handler=simple_auth_handler) as jumper:
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
        _, stdout, _ = target.exec_command('sh ip int br')
        print(stdout.read().decode())
        target.close()


Usage Example 2: Open one Jump Channel, connect to multiple targets
--------------------------------------------------------------------

.. code-block:: python

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
        _, stdout, _ = target1.exec_command('sh ver')
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
        print(stdout.read().decode())
        target2.close()


Usage Example 3: Multiple-Hop SSH "Virtual Circuit"
---------------------------------------------------

.. code-block:: python

    circuit = []

    hop1 = SSHJumpClient()
    hop1.connect('host')
    circuit.append(hop1)

    hop2 = SSHJumpClient(jump_session=hop1)
    hop2.connect('host')
    circuit.append(hop2)

    hop3 = SSHJumpClient(jump_session=hop2)
    hop3.connect('host')
    circuit.append(hop3)

    hop4 = SSHJumpClient(jump_session=hop3)
    hop4.connect('host')
    circuit.append(hop4)

    target = SSHJumpClient(jump_session=hop4)
    target.connect('host')
    circuit.append(target)

    target.exec_command('uptime')

    for session in reversed(circuit):
        session.close()


A Note on Authentication
------------------------

In order to successfully authenticate with infrastructure requiring keyboard-interactive multi-factor authentication, you will probably want to explicitly pass in auth_handler= during client construction. A basic handler callable is included, and should work for most use cases:

``from paramiko_jump import simple_auth_handler``

When troubleshooting authentication failures, remember that Paramiko will be authenticating as a client on each 'hop', and that it has strong preferences over which authentication scheme it will be using. You can control authentication behavior by passing various parameters to the ```connect()``` call. Read ```paramiko.SSHClient._auth``` for more insight into how this works.

A Note on Fabric
----------------

If using with ``fabric``, the best means to do this is to create a ``fabric.connection.Connection`` object, and then replace the ``Connection.client`` with an instance of ``SSHJumpClient`` targeting the ``Connection.host``.

.. code-block:: python

    from fabric.connection import Connection
    from paramiko_jump import SSHJumpClient, simple_auth_handler

    # Create Fabric Connection
    conn: Connection = Connection("hostname_target")
    
    # Create SSHJumpClient for the target jumphost
    jumphost_client: SSHJumpClient = SSHJumpClient(auth_handler=simple_auth_handler)
    jumphost_client.connect("jumphost_target")

    # Create SSHJumpClient to replace internal SSHClient representation in Fabric
    new_client: SSHJumpClient = SSHJumpClient(jump_session=jumphost_client, auth_handler=simple_auth_handler)
    new_client.connect(conn.host)

    # Add the client to the conn.client
    conn.client = new_client

