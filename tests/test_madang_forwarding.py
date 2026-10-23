"""Exercise forwarding boundaries without importing Telethon or reading secrets."""
import ast
from pathlib import Path
import types
import unittest
from unittest.mock import AsyncMock, Mock


SOURCE_PATH = Path(__file__).resolve().parents[1] / "forwarder.py"
TREE = ast.parse(SOURCE_PATH.read_text())
LEGACY_SOURCES = [
    "WalletvKR",
    "squid_kor_update",
    "YellowKorea_ann",
    "Origintrailkr",
    "babylonBTC",
]


def extracted_forwarder(client, logger):
    """Compile only the async function: no module imports, clients, or config."""
    node = next(
        node for node in TREE.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_forward_messages"
    )
    module = ast.Module(body=[node], type_ignores=[])
    namespace = {
        "client": client,
        "logger": logger,
        "DESTINATION": "coiniseasy",
    }
    exec(compile(module, str(SOURCE_PATH), "exec"), namespace)
    return namespace["_forward_messages"]


def message(message_id, *, text="Madang announcement", media=None):
    return types.SimpleNamespace(
        id=message_id,
        text=text,
        media=media,
        get_input_chat=AsyncMock(return_value="verified-madang-peer"),
    )


class MadangForwardingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = types.SimpleNamespace(
            forward_messages=AsyncMock(),
            send_message=AsyncMock(),
            send_file=AsyncMock(),
        )
        self.logger = Mock()
        self.forward = extracted_forwarder(self.client, self.logger)

    async def test_new_madang_message_is_forwarded_once_to_coineasy(self):
        post = message(123)
        await self.forward([post], "madangfunann")
        self.client.forward_messages.assert_awaited_once_with(
            entity="coiniseasy", messages=[post], from_peer="verified-madang-peer"
        )
        self.client.send_message.assert_not_awaited()
        self.client.send_file.assert_not_awaited()

    async def test_madang_album_is_forwarded_once_in_message_order(self):
        first, second = message(123, media="photo-1"), message(124, media="photo-2")
        await self.forward([second, first], "madangfunann")
        self.client.forward_messages.assert_awaited_once_with(
            entity="coiniseasy", messages=[first, second], from_peer="verified-madang-peer"
        )
        first.get_input_chat.assert_awaited_once()
        second.get_input_chat.assert_not_awaited()
        self.client.send_message.assert_not_awaited()
        self.client.send_file.assert_not_awaited()

    async def test_madang_unknown_or_failed_delivery_never_copies(self):
        for posts in ([message(123)], [message(123, media="a"), message(124, media="b")]):
            for exception_type in (TimeoutError, RuntimeError):
                with self.subTest(album=len(posts) > 1, exception=exception_type.__name__):
                    self.setUp()
                    error = exception_type("sensitive-provider-detail")
                    self.client.forward_messages.side_effect = error
                    with self.assertRaises(exception_type) as raised:
                        await self.forward(posts, "MadangFunAnn")
                    self.assertIs(raised.exception, error)
                    self.client.forward_messages.assert_awaited_once()
                    self.client.send_message.assert_not_awaited()
                    self.client.send_file.assert_not_awaited()
                    self.logger.error.assert_called_once_with(
                        "Madang forward delivery unknown/review required; no copy fallback"
                    )
                    self.logger.warning.assert_not_called()

    async def test_legacy_message_fallback_is_retained(self):
        post = message(222, text="Legacy announcement", media="photo")
        self.client.forward_messages.side_effect = RuntimeError("failed")
        await self.forward([post], "babylonBTC")
        self.client.forward_messages.assert_awaited_once()
        self.client.send_message.assert_awaited_once_with(
            entity="coiniseasy", message="[babylonBTC]\nLegacy announcement", file="photo"
        )
        self.client.send_file.assert_not_awaited()

    async def test_legacy_album_fallback_is_retained(self):
        posts = [message(222, text="Legacy album", media="a"), message(223, media="b")]
        self.client.forward_messages.side_effect = RuntimeError("failed")
        await self.forward(posts, "Origintrailkr")
        self.client.forward_messages.assert_awaited_once()
        self.client.send_file.assert_awaited_once_with(
            entity="coiniseasy", file=["a", "b"], caption="[Origintrailkr]\nLegacy album"
        )
        self.client.send_message.assert_not_awaited()

    def test_new_message_allowlist_only_adds_madang_announcement(self):
        assignment = next(
            node for node in TREE.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "SOURCE_CHANNELS"
                    for target in node.targets)
        )
        self.assertEqual(ast.literal_eval(assignment.value), LEGACY_SOURCES + ["madangfunann"])
        handler = next(
            node for node in TREE.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "handler"
        )
        self.assertEqual(len(handler.decorator_list), 1)
        event_filter = handler.decorator_list[0].args[0]
        self.assertEqual(ast.unparse(event_filter), "events.NewMessage(chats=SOURCE_CHANNELS)")


if __name__ == "__main__":
    unittest.main()
