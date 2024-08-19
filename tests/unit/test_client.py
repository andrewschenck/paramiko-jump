import unittest
from unittest.mock import patch, MagicMock
from paramiko import SSHClient
from paramiko_jump import (
    MagicAuthHandler,
    SSHJumpClient,
    simple_auth_handler,
)


class TestSSHJumpClientUnit(unittest.TestCase):

    @patch('paramiko_jump.client.SSHJumpClient.connect')
    @patch('paramiko_jump.client.SSHJumpClient.exec_command')
    def test_connect_and_exec_command(self, mock_exec_command, mock_connect):
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = ['output']
        mock_exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

        client = SSHJumpClient()
        client.connect(hostname='somehost.example.com', username='username')
        stdin, stdout, stderr = client.exec_command('uptime')
        self.assertEqual(stdout.readlines(), ['output'])

    @patch('paramiko_jump.client.SSHJumpClient.connect')
    def test_connect_failure(self, mock_connect):
        mock_connect.side_effect = Exception("Connection failed")

        client = SSHJumpClient()
        with self.assertRaises(Exception) as context:
            client.connect(hostname='invalid-host', username='username')
        self.assertEqual(str(context.exception), "Connection failed")

    @patch('paramiko_jump.client.SSHJumpClient.exec_command')
    def test_exec_command_failure(self, mock_exec_command):
        mock_exec_command.side_effect = Exception("Command failed")

        client = SSHJumpClient()
        client.connect = MagicMock()  # Mock connect to avoid real connection
        with self.assertRaises(Exception) as context:
            client.exec_command('invalid-command')
        self.assertEqual(str(context.exception), "Command failed")

    @patch('paramiko_jump.client.SSHJumpClient.connect')
    def test_simple_auth_handler(self, mock_connect):
        client = SSHJumpClient(auth_handler=simple_auth_handler)
        client.connect(hostname='somehost.example.com', username='username')
        mock_connect.assert_called_with(hostname='somehost.example.com', username='username')

    @patch('paramiko_jump.client.SSHJumpClient.connect')
    def test_magic_auth_handler(self, mock_connect):
        handler = MagicAuthHandler(['password'], ['1'])
        client = SSHJumpClient(auth_handler=handler)
        client.connect(hostname='somehost.example.com', username='username')
        mock_connect.assert_called_with(hostname='somehost.example.com', username='username')

    @patch('paramiko_jump.client.SSHJumpClient.connect')
    def test_password_auth(self, mock_connect):
        client = SSHJumpClient()
        client.connect(hostname='somehost.example.com', username='ubuntu', password='password')
        mock_connect.assert_called_with(hostname='somehost.example.com', username='ubuntu', password='password')

    @patch('paramiko_jump.client.SSHJumpClient.connect')
    def test_ssh_key_auth(self, mock_connect):
        client = SSHJumpClient()
        client.connect(hostname='somehost.example.com', username='username', look_for_keys=True)
        mock_connect.assert_called_with(hostname='somehost.example.com', username='username', look_for_keys=True)

    def test_repr(self):
        client = SSHJumpClient()
        self.assertEqual(repr(client), "SSHJumpClient(jump_session=None, auth_handler=None)")

    def test_str(self):
        client = SSHJumpClient()
        self.assertEqual(str(client), "SSHJumpClient")

    # @patch('paramiko_jump.client.SSHJumpClient._auth')
    @patch('paramiko.client.SSHClient._auth')
    def test_auth_with_handler(self, mock_auth):
        handler = MagicMock()
        client = SSHJumpClient(auth_handler=handler)
        client._transport = MagicMock()
        client._auth('username', None, None, None, None, None, None, None, None, None, None)
        # mock_auth.assert_called()

    # @patch('paramiko_jump.client.SSHJumpClient._auth')
    @patch('paramiko.client.SSHClient._auth')
    def test_auth_without_handler(self, mock_auth):
        client = SSHJumpClient()
        client._transport = MagicMock()
        client._auth('username', None, None, None, None, None, None, None, None, None, None)
        # mock_auth.assert_called()

    @patch('paramiko_jump.client.SSHJumpClient._auth')
    def test_auth_with_handler_again(self, mock_auth):
        handler = MagicMock()
        client = SSHJumpClient(auth_handler=handler)
        client._transport = MagicMock()
        client._auth('username', None, None, None, None, None, None, None, None, None, None)
        mock_auth.assert_called()

    @patch('paramiko_jump.client.SSHJumpClient._auth')
    def test_auth_without_handler_again(self, mock_auth):
        client = SSHJumpClient()
        client._transport = MagicMock()
        client._auth('username', None, None, None, None, None, None, None, None, None, None)
        mock_auth.assert_called()

    # @patch('paramiko_jump.client.SSHJumpClient._transport')
    # @patch('paramiko_jump.client.SSHJumpClient._auth')
    # def test_connect_with_jump_session(self, mock_auth, mock_transport):
    #     jump_client = MagicMock()
    #     jump_client._transport = mock_transport
    #     client = SSHJumpClient(jump_session=jump_client)
    #     client.connect(hostname='somehost.example.com', username='username')
    #     mock_transport.open_channel.assert_called()

    # def test_invalid_jump_session(self):
    #     with self.assertRaises(TypeError):
    #         SSHJumpClient(jump_session="invalid_session")

    # @patch('paramiko_jump.client.SSHJumpClient.connect')
    # def test_connect_with_transport_factory(self, mock_transport):
    #     mock_transport_instance = mock_transport.return_value
    #     client = SSHJumpClient()
    #     client.connect(hostname='somehost.example.com', transport_factory=mock_transport)
    #     mock_transport.assert_called()
    #     mock_transport_instance.start_client.assert_called()

    # @patch('paramiko_jump.client.SSHJumpClient.connect')
    # def test_connect_with_disabled_algorithms(self, mock_transport):
    #     client = SSHJumpClient()
    #     client.connect(hostname='somehost.example.com', disabled_algorithms={'kex': ['diffie-hellman-group1-sha1']})
    #     mock_transport.set_disabled_algorithms.assert_called_with({'kex': ['diffie-hellman-group1-sha1']})


class TestSSHJumpClientJumpSession(unittest.TestCase):

    @patch('paramiko_jump.client.SSHClient.connect')
    def test_connect_with_jump_session(self, mock_connect):
        jump_client = MagicMock(spec=SSHClient)
        jump_client._transport = MagicMock()
        client = SSHJumpClient(jump_session=jump_client)
        client.connect(hostname='somehost.example.com', username='username')
        jump_client._transport.open_channel.assert_called()

    def test_invalid_jump_session(self):
        with self.assertRaises(TypeError):
            SSHJumpClient(jump_session="invalid_session")

    @patch('paramiko_jump.client.SSHClient.connect')
    def test_connect_with_jump_session_and_sock(self, mock_connect):
        jump_client = MagicMock(spec=SSHClient)
        jump_client._transport = MagicMock()
        client = SSHJumpClient(jump_session=jump_client)
        with self.assertRaises(ValueError):
            client.connect(hostname='somehost.example.com', username='username', sock=MagicMock())


if __name__ == '__main__':
    unittest.main()
