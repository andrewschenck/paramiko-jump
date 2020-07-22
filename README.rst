
The Problem
___________
"How do I use paramiko to SSH to a remote host while proxying through a jump host? Also, my jump host requires multi-factor authentication!"

This seems to be a surprisingly common problem with a lot of not-very-working solutions. I figured I'd share my attempt with the world.


A little setup:

.. code-block::

    if __name__ == '__main__':
        from getpass import getpass

        import paramiko
        from paramiko_jump import SSHJumpClient

        jump_host = 'jump-host'
        target_host1 = 'target_host1'
        target_host2 = 'target_host2'


Example 1: Connect to a single target through a Jump Host
---------------------------------------------------------

In this example, we disable SSH key-based authentication
between the Jump Host and the Target Host.

.. code-block::

        username = input(f'{target_host1} Username: ')
        password = getpass(f'{target_host1} Password: ')

        with SSHJumpClient(jump_host=jump_host) as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=target_host1,
                username=username,
                password=password,
                look_for_keys=False,
            )

            _, stdout, _ = ssh.exec_command('sh ip int br')
            print(stdout.read().decode())
            ssh.close()


Example 2: Open one Jump Channel, connect to multiple targets
-------------------------------------------------------------

In this example, we allow Paramiko to authenticate using its normal algorithm; if we have an SSH key on the Jump Host, Paramiko will use it to authenticate our session between the Jump Host and the Target Hosts.

.. code-block::

        with SSHJumpClient(jump_host=jump_host, close_jump_channel=False) as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh.connect(
                hostname=target_host1,
                username=username,
                password=password,
            )
            _, stdout, _ = ssh.exec_command('sh ip int br')
            print(stdout.read().decode())
            ssh.close()

            ssh.connect(
                hostname=target_host2,
                username=username,
                password=password,
            )
            _, stdout, _ = ssh.exec_command('sh ver')
            print(stdout.read().decode())
            ssh.close()


Example 3: Same behavior as Example 1
-------------------------------------

.. code-block::

        ssh = SSHJumpClient(jump_host=jump_host)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(
            hostname=target_host1,
            username=username,
            password=password,
            look_for_keys=False,
        )
        _, stdout, _ = ssh.exec_command('sh ip int br')
        print(stdout.read().decode())
        ssh.close()


Example 4: Same behavior as Example 2
-------------------------------------

.. code-block::

        ssh = SSHJumpClient(jump_host=jump_host, close_jump_channel=False)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(
            hostname=target_host1,
            username=username,
            password=password,
        )
        _, stdout, _ = ssh.exec_command('sh ip int br')
        print(stdout.read().decode())
        ssh.close()

        ssh.connect(
            hostname=target_host2,
            username=username,
            password=password,
        )
        _, stdout, _ = ssh.exec_command('sh ver')
        print(stdout.read().decode())

        # We're also done with the Jump Channel
        ssh.close(close_jump_channel=True)



A Note on Authentication
------------------------

You must think about how you're authenticating from the client to the Jump Host, as well as from the Jump Host to the Target Host. When connecting to the Target Host, be sure to pass authentication-related parameters into the connect() call. If you have an SSH key on the Jump Host, Paramiko will try to use it for authentication unless you override its behavior.

