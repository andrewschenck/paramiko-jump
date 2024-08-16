import unittest
from unittest.mock import patch, MagicMock

from paramiko_jump import SSHJumpClient, simple_auth_handler, MagicAuthHandler


class TestSSHJumpClientFunctional(unittest.TestCase):

    @patch('paramiko_jump.SSHJumpClient.connect')
    @patch('paramiko_jump.SSHJumpClient.exec_command')
    def test_proxying_example_1a(self, mock_exec_command, mock_connect):
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = ['output']
        mock_exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

        with SSHJumpClient(auth_handler=simple_auth_handler) as jumper:
            jumper.connect(hostname='jump-host', username='jump-user')
            with SSHJumpClient(jump_session=jumper) as target:
                target.connect(hostname='target-host', username='target-user',
                               password='target-password', look_for_keys=False,
                               allow_agent=False)
                stdin, stdout, stderr = target.exec_command('sh ip int br')
                output = stdout.readlines()
                self.assertEqual(output, ['output'])

    @patch('paramiko_jump.SSHJumpClient.connect')
    @patch('paramiko_jump.SSHJumpClient.exec_command')
    def test_proxying_example_1b(self, mock_exec_command, mock_connect):
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = ['output']
        mock_exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

        jumper = SSHJumpClient(auth_handler=simple_auth_handler)
        jumper.set_missing_host_key_policy(MagicMock())
        jumper.connect(hostname='jump-host', username='jump-user')

        target = SSHJumpClient(jump_session=jumper)
        target.set_missing_host_key_policy(MagicMock())
        target.connect(hostname='target-host', username='target-user',
                       password='target-password', look_for_keys=False,
                       allow_agent=False)
        stdin, stdout, stderr = target.exec_command('sh ip int br')
        output = stdout.readlines()
        self.assertEqual(output, ['output'])
        target.close()

    @patch('paramiko_jump.SSHJumpClient.connect')
    @patch('paramiko_jump.SSHJumpClient.exec_command')
    def test_proxying_example_2(self, mock_exec_command, mock_connect):
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = ['output']
        mock_exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

        with SSHJumpClient(auth_handler=simple_auth_handler) as jumper:
            jumper.connect(hostname='jump-host', username='jump-user')

            target1 = SSHJumpClient(jump_session=jumper)
            target1.connect(hostname='target-host1', username='username',
                            password='password', look_for_keys=False,
                            allow_agent=False)
            stdin, stdout, stderr = target1.exec_command('sh ver')
            self.assertEqual(stdout.readlines(), ['output'])
            target1.close()

            target2 = SSHJumpClient(jump_session=jumper)
            target2.connect(hostname='target-host2', username='username',
                            password='password', look_for_keys=False,
                            allow_agent=False)
            stdin, stdout, stderr = target2.exec_command('sh ip int br')
            self.assertEqual(stdout.readlines(), ['output'])
            target2.close()

    @patch('paramiko_jump.SSHJumpClient.connect')
    @patch('paramiko_jump.SSHJumpClient.exec_command')
    def test_proxying_example_3(self, mock_exec_command, mock_connect):
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = 'output'
        mock_exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

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
        self.assertEqual(stdout.read(), 'output')

        for session in reversed(circuit):
            session.close()

    @patch('paramiko_jump.SSHJumpClient.connect')
    @patch('paramiko_jump.SSHJumpClient.exec_command')
    def test_simple_auth_handler(self, mock_exec_command, mock_connect):
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = ['output']
        mock_exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

        with SSHJumpClient(auth_handler=simple_auth_handler) as jumper:
            jumper.connect(hostname='somehost.example.com', username='username',
                           look_for_keys=False)
            stdin, stdout, stderr = jumper.exec_command('uptime')
            self.assertEqual(stdout.readlines(), ['output'])

    @patch('paramiko_jump.SSHJumpClient.connect')
    @patch('paramiko_jump.SSHJumpClient.exec_command')
    def test_magic_auth_handler(self, mock_exec_command, mock_connect):
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = ['output']
        mock_exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

        handler = MagicAuthHandler(['password'], ['1'])

        with SSHJumpClient(auth_handler=handler) as jumper:
            jumper.connect(hostname='somehost.example.com', username='username',
                           look_for_keys=False)
            stdin, stdout, stderr = jumper.exec_command('uptime')
            self.assertEqual(stdout.readlines(), ['output'])

    @patch('paramiko_jump.SSHJumpClient.connect')
    @patch('paramiko_jump.SSHJumpClient.exec_command')
    def test_password_auth(self, mock_exec_command, mock_connect):
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = ['output']
        mock_exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

        with SSHJumpClient() as jumper:
            jumper.connect(hostname='somehost.example.com', username='ubuntu',
                           password='password', look_for_keys=False)
            stdin, stdout, stderr = jumper.exec_command('ls')
            self.assertEqual(stdout.readlines(), ['output'])

    @patch('paramiko_jump.SSHJumpClient.connect')
    @patch('paramiko_jump.SSHJumpClient.exec_command')
    def test_ssh_key_auth(self, mock_exec_command, mock_connect):
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = ['output']
        mock_exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

        with SSHJumpClient() as jumper:
            jumper.connect(hostname='somehost.example.com', username='username',
                           look_for_keys=True)
            stdin, stdout, stderr = jumper.exec_command('uptime')
            self.assertEqual(stdout.readlines(), ['output'])

    @patch('paramiko_jump.SSHJumpClient.connect')
    def test_connection_failure(self, mock_connect):
        mock_connect.side_effect = Exception("Connection failed")

        with self.assertRaises(Exception) as context:
            with SSHJumpClient() as jumper:
                jumper.connect(hostname='invalid-host', username='username')
        self.assertEqual(str(context.exception), "Connection failed")

    @patch('paramiko_jump.SSHJumpClient.connect')
    @patch('paramiko_jump.SSHJumpClient.exec_command')
    def test_command_failure(self, mock_connect, mock_exec_command):
        mock_exec_command.side_effect = Exception("Command failed")

        with self.assertRaises(Exception) as context:
            with SSHJumpClient() as jumper:
                jumper.connect(hostname='somehost.example.com', username='username')
                jumper.exec_command('invalid-command')
        self.assertEqual(str(context.exception), "Command failed")


if __name__ == '__main__':
    unittest.main()
