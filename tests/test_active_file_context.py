import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from telegram.ext import ConversationHandler

from handlers.modules import modules_panel


class ActiveFileContextTests(unittest.IsolatedAsyncioTestCase):

    async def test_modules_panel_remembers_selected_file_from_callback(self):
        query = SimpleNamespace(
            data="modules_panel|demo.py",
            answer=AsyncMock(),
        )
        update = SimpleNamespace(callback_query=query)
        context = SimpleNamespace(user_data={})

        with patch(
            "handlers.modules.modules_menu",
            new_callable=AsyncMock,
            return_value=ConversationHandler.END,
        ) as menu_mock:
            result = await modules_panel(update, context)

        self.assertEqual(result, ConversationHandler.END)
        self.assertEqual(context.user_data.get("active_file"), "demo.py")
        menu_mock.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
