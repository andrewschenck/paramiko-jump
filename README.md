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

2) Easy authentication scheme override, allowing for keyboard-interactive authentication as well as
fully-automated authentication through 2FA / MFA infrastructure. This package includes 
authentication handlers which can handle either use case, and more.


## Installing paramiko-jump
Paramiko-jump is available on PyPI, so you can readily install it with pip:

```bash
pip install paramiko-jump
```


**********************


# Usage Examples

## You Can Authenticate However You Want

Within this document are numerous examples of how to use paramiko-jump to authenticate to a remote
host as well as how to use it to proxy SSH sessions, but not all possible permutations are
documented here. It's important to know that **you can use any authentication scheme demonstrated
in these examples, with or without the proxying feature, as long as your SSH infrastructure 
supports it.**


## Quick Start: I need to solve MFA but I don't need SSH Proxying features

If you don't need the Jump Host features but DO need to handle multi-factor authentication,
these next examples are for you. 

You can use the ```simple_auth_handler``` or ```MultiFactorAuthHandler``` to handle your 
authentication to a single host without ever proxying another SSH session through it ('jumping'.)
Just pick an authentication approach and go.


## Authentication Handlers 

In order to successfully authenticate with infrastructure requiring keyboard-interactive and/or
multi-factor authentication, you will probably want to explicitly pass in auth_handler= during 
client construction. You can use the included handlers, or you can write your own.


### Authentication Handler Example 1: Keyboard-Interactive (Any Authentication Scheme)

A basic handler callable is included, and should work for most keyboard-interactive use cases. In
this example, we supply a username and will be prompted for any passwords/tokens that are needed in
order to authenticate.

If you choose to use the ```simple_auth_handler```, paramiko will prompt you for any passwords or
tokens that are required for authentication, and will ignore other authentication methods (such as
SSH keys) even if you pass in authentication-related parameters. It will even ignore any
password value you pass in, because it's expecting to get it via the handler.

#### Keyboard-Interactive Authentication using the simple_auth_handler
```python
from paramiko_jump import SSHJumpClient, simple_auth_handler

with SSHJumpClient(auth_handler=simple_auth_handler) as jumper:
    jumper.connect(
        hostname='somehost.example.com',
        username='username',
        look_for_keys=False,
    )
stdin, stdout, stderr = jumper.exec_command('uptime')
output = stdout.readlines()
print(output)
```


### Authentication Handler Example 2: MultiFactor Authentication using the MultiFactorAuthHandler

The ```MultiFactorAuthHandler``` class is a more advanced handler that can be used to accomplish 
complex authentication sessions with automation -- even through MFA infrastructure. This is
accomplished by seeding the handler with a sequence of responses which will be required during
the authentication session, such as a password and OTP.

It goes without saying that, you must figure out what your MFA infrastructure is expecting and
provide the correct responses in the correct order. This is a powerful tool, but it can take a bit
of tinkering to get it right for your environment.

In this next example, my MFA infrastucture is first going to require that I authenticate with my 
password, and then I have to enter '1' to instruct the infrastructure to push an authentication
request to my mobile authenticator.

#### Multi-Factor Authentication using the MultiFactorAuthHandler
```python
from paramiko_jump import SSHJumpClient, MultiFactorAuthHandler

handler = MultiFactorAuthHandler()
handler.add('password')  # Just add strings to the handler in the order they are needed
handler.add('1')

with SSHJumpClient(auth_handler=handler) as jumper:
    jumper.connect(
        hostname='somehost.example.com',
        username='username',
        look_for_keys=False,
    )
    stdin, stdout, stderr = jumper.exec_command('uptime')
    output = stdout.readlines()
    print(output)
```


## Simpler Authentication Schemes

In general, unless you want keyboard interactive authentication (See: ```simple_auth_handler```),
or you want to authenticate through 2FA/MFA infrastructure (See: ```MultiFactorAuthHandler```),
you probably want to authenticate to a host in one of the following ways:


### Simple Authentication Example 1: Use an SSH key with ssh-agent

If you have an SSH key, you can use it to authenticate instead of using keyboard-interactive
authentication.

By default, paramiko will even use your ssh-agent, if one is running.

In this example, the private key is managed by ssh-agent, but you can add a passphrase=
parameter to the connect() call if you have a passphrase-protected key and aren't using
ssh-agent.

#### SSH Key Authentication using ssh-agent
```python
from paramiko_jump import SSHJumpClient

with SSHJumpClient() as jumper:
    jumper.connect(
        hostname='somehost.example.com',
        username='username',
        look_for_keys=True,
    )
```


### Simple Authentication Example 2: Use an SSH key with a passhphrase

In this example, we have an SSH key, and we have a passphrase to unlock it, that we've somehow
fetched from a secure secrets store and exposed to Python in a secure manner.

#### SSH Key Authentication using a passphrase-protected key, ssh-agent ignored
```python
from paramiko_jump import SSHJumpClient

with SSHJumpClient() as jumper:
    jumper.connect(
        hostname='somehost.example.com',
        username='username',
        passphrase='mykeypassphrase',
        look_for_keys=True,
        allow_agent=False,
    )
```


### Simple Authentication Example 3: Ignore SSH keys, use Username/Password authentication

In this example, we may have an SSH key configured, but in order to succesfully authenticate with
the remote host, we need to use a username and password. We explicitly tell paramiko to ignore any
keys it finds, because we don't want it to try to use them as the keys will fail to authenticate.

#### Basic (Username/Password) Authentication
```python
from paramiko_jump import SSHJumpClient

with SSHJumpClient() as jumper:
    jumper.connect(
        hostname='somehost.example.com',
        username='username',
        password='password',
        look_for_keys=False,
    )
```


## SSH Proxying / "Jump Host" Support

If you need to proxy your SSH session through a Jump Host, this is how to do it. Note that the
following examples are primarily using the ```simple_auth_handler``` for authentication, but 
you can use any authentication scheme you like for either Jump Host or Target Host, as long as
your SSH infrastructure supports it.


### SSH Proxying Example 1a: Connect to a single Target Host through a Jump Host

In this example, we connect to a Jump Host, then connect to a Target Host through it.
We are using keyboard-interactive authentication on the Jump Host by way of
```auth_handler=simple_auth_handler``` and we are passing pre-determined username and password
credentials to the Target Host.

#### Keyboard-Interactive Authentication on the Jump Host, Basic Authentication on the Target Host
```python
from paramiko_jump import SSHJumpClient, simple_auth_handler

##
# Because I'm passing in ```simple_auth_handler```, I will be prompted for any passwords or
# tokens that are required for authentication. This is how to do keyboard-interactive SSH
# authentication.
##
with SSHJumpClient(auth_handler=simple_auth_handler) as jumper:
    jumper.connect(
        hostname='jump-host',
        username='jump-user',
        look_for_keys=False,
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
```


### SSH Proxying Example 1b: Connect to a single Target Host through a Jump Host

This example is functionally equivalent to Example 1a, with two key changes:

1) It doesn't use the context manager.
2) It applies paramiko.AutoAddPolicy() as the missing host key policy to the Jump Host and
   Target Host connections -- this tells the SSH processes to 'auto accept' the host key if it's not
   already known (be cautious!)


#### Keyboard-Interactive Authentication on the Jump Host, Basic Authentication on the Target Host
```python
import paramiko
from paramiko_jump import SSHJumpClient, simple_auth_handler


jumper = SSHJumpClient(auth_handler=simple_auth_handler)
jumper.set_missing_host_key_policy(paramiko.AutoAddPolicy())
jumper.connect(
    hostname='jump-host',
    username='jump-user',
    look_for_keys=False,
)

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
```


### SSH Proxying Example 2: Open one jump channel, connect to multiple Target Hosts


#### MFA on the Jump Host, Basic Authentication on the Target Hosts
```python
import os
from paramiko_jump import SSHJumpClient, MultiFactorAuthHandler

password = os.getenv('JUMP_HOST_PASSWORD')
handler = MultiFactorAuthHandler()
handler.add(password)
handler.add('1')

with SSHJumpClient(auth_handler=handler) as jumper:
    jumper.connect(
        hostname='jump-host',
        username='username',
        look_for_keys=False,
    )

    with SSHJumpClient(jump_session=jumper) as target1:
        target1.connect(
            hostname='target-host1',
            username='username',
            password='password',
            look_for_keys=False,
        )
        _, stdout, _ = target1.exec_command('uptime')
        output = stdout.readlines()
        print(output)

    with SSHJumpClient(jump_session=jumper) as target2:
        target2.connect(
            hostname='target-host2',
            username='username',
            password='password',
            look_for_keys=False,
        )
        _, stdout, _ = target2.exec_command('uptime')
        output = stdout.readlines()
        print(output)

    with SSHJumpClient(jump_session=jumper) as target3:
        target2.connect(
            hostname='target-host3',
            username='username',
            password='password',
            look_for_keys=False,
        )
        _, stdout, _ = target2.exec_command('uptime')
        output = stdout.readlines()
        print(output)
```


### SSH Proxying Example 3: Multiple-Hop SSH "Virtual Circuit"

You can build a 'virtual circuit' out of multiple SSH connections, each one proxying through
the previous.

#### This example lacks authentication parameters, and exists to illustrate the concept.
```python
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
```


# Troubleshooting

## Authentication Issues

* Remember to use the Authentication Handlers (or make your own) to help manage your more complex
use cases. Injecting the correct handler can make all the difference in the world.

* If you have injected an authentication handler, Paramiko will use that to handle the
  authentication process, and it will take precedence over other authentication parameters you pass
  in.

* When troubleshooting authentication failures, remember that Paramiko will be authenticating as
a client on each 'hop', and that it has strong preferences over which authentication scheme it
will be using. You can control authentication behavior by passing various parameters to the
```connect()``` call. Read ```paramiko.SSHClient._auth``` for more insight into how this works.

* If you aren't using key-based authentication, it's safest to explicitly set
```look_for_keys=False```. This will prevent Paramiko from trying to use any keys it finds, which
can take it down the wrong code path.

## Missing Host Key Errors

See **SSH Proxying Example 1b** for an example of how to use ```paramiko.AutoAddPolicy()``` to 
automatically accept unknown host keys. This is a dangerous practice, but it can be useful 
for testing and development.
