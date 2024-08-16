import unittest
from unittest.mock import patch, MagicMock
from paramiko_jump.handler import simple_auth_handler, MagicAuthHandler


class TestSimpleAuthHandler(unittest.TestCase):

    @patch('paramiko_jump.handler.getpass')
    @patch('paramiko_jump.handler.input')
    def test_simple_auth_handler(self, mock_input, mock_getpass):
        mock_input.side_effect = ['user_input']
        mock_getpass.side_effect = ['hidden_input']

        title = "Title"
        instructions = "Instructions"
        prompt_list = [("Enter username: ", True), ("Enter password: ", False)]

        result = simple_auth_handler(title, instructions, prompt_list)
        self.assertEqual(result, ['user_input', 'hidden_input'])
        mock_input.assert_called_once_with("Enter username: ")
        mock_getpass.assert_called_once_with("Enter password: ")

    @patch('paramiko_jump.handler.getpass')
    @patch('paramiko_jump.handler.input')
    def test_simple_auth_handler_no_title_instructions(self, mock_input, mock_getpass):
        mock_input.side_effect = ['user_input']
        mock_getpass.side_effect = ['hidden_input']

        title = ""
        instructions = ""
        prompt_list = [("Enter username: ", True), ("Enter password: ", False)]

        result = simple_auth_handler(title, instructions, prompt_list)
        self.assertEqual(result, ['user_input', 'hidden_input'])
        mock_input.assert_called_once_with("Enter username: ")
        mock_getpass.assert_called_once_with("Enter password: ")

class TestMagicAuthHandler(unittest.TestCase):

    def test_magic_auth_handler(self):
        handler = MagicAuthHandler(['password'], ['1234'])
        self.assertEqual(handler(), ['password'])
        self.assertEqual(handler(), ['1234'])
        self.assertEqual(handler(), [])

    def test_magic_auth_handler_iteration(self):
        handler = MagicAuthHandler(['password'], ['1234'])
        iterator = iter(handler)
        self.assertEqual(next(iterator), ['password'])
        self.assertEqual(next(iterator), ['1234'])
        with self.assertRaises(StopIteration):
            next(iterator)


if __name__ == '__main__':
    unittest.main()
