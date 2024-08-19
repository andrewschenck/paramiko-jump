import unittest
from unittest.mock import call, patch
from paramiko_jump.handler import (
    MagicAuthHandler,
    MultiFactorAuthHandler,
    simple_auth_handler,
)


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


class TestMultiFactorAuthHandler(unittest.TestCase):

    def test_init_with_auth_responses(self):
        handler = MultiFactorAuthHandler(['password'], ['1234'])
        self.assertEqual(handler._auth_responses, [['password'], ['1234']])

    def test_init_without_auth_responses(self):
        handler = MultiFactorAuthHandler()
        self.assertEqual(handler._auth_responses, [])

    def test_call_with_auth_responses(self):
        handler = MultiFactorAuthHandler(['password'], ['1234'])
        self.assertEqual(handler(), ['password'])
        self.assertEqual(handler(), ['1234'])
        self.assertEqual(handler(), [])

    def test_call_with_title_instructions_prompts(self):
        handler = MultiFactorAuthHandler(show_title=True, show_instructions=True, show_prompts=True)
        with patch('paramiko_jump.handler._LOG.info') as mock_log_info:
            handler('Title', 'Instructions', [('Prompt', True)])
            mock_log_info.assert_has_calls([
                call('Title'),
                call('Instructions'),
                call('Prompt')
            ])

    def test_add_auth_response(self):
        handler = MultiFactorAuthHandler()
        handler.add('password')
        self.assertEqual(handler._auth_responses, [['password']])

    def test_iter(self):
        handler = MultiFactorAuthHandler(['password'], ['1234'])
        iterator = iter(handler)
        self.assertEqual(next(iterator), ['password'])
        self.assertEqual(next(iterator), ['1234'])
        with self.assertRaises(StopIteration):
            next(iterator)

    def test_next(self):
        handler = MultiFactorAuthHandler(['password'], ['1234'])
        self.assertEqual(next(handler), ['password'])
        self.assertEqual(next(handler), ['1234'])
        with self.assertRaises(StopIteration):
            next(handler)


if __name__ == '__main__':
    unittest.main()
