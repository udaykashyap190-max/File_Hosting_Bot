import unittest
from unittest.mock import MagicMock, patch

import bot


class ModuleConversationRegistrationTests(unittest.IsolatedAsyncioTestCase):

    async def test_main_registers_module_conversation_handler(self):
        builder = MagicMock()
        builder.token.return_value = builder
        app = MagicMock()
        builder.build.return_value = app

        with patch("bot.init_database"), \
             patch("bot.Application.builder", return_value=builder), \
             patch("bot.get_module_conversation_handler", return_value=object()) as conversation_handler:
            await bot.main()

        registered_handlers = [call.args[0] for call in app.add_handler.call_args_list]
        self.assertIn(conversation_handler.return_value, registered_handlers)


if __name__ == "__main__":
    unittest.main()
