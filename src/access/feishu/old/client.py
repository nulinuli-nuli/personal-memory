"""Feishu SDK client (WebSocket long-connection and API)."""
import lark_oapi as lark
from sqlalchemy.orm import Session
from typing import Any

from src.config import settings
from src.feishu.event_handler import create_event_handler


class LarkWSClient:
    """Feishu WebSocket long-connection client.

    This client uses the official Lark SDK to establish a persistent
    WebSocket connection for receiving events in real-time.

    Advantages over webhook mode:
    - No public URL required
    - Works in local development
    - Simpler authentication
    - Auto-reconnection
    """

    def __init__(self):
        """Initialize the WebSocket client."""
        self.db: Session | None = None
        self.event_handler = None
        self.client = None

    def start(self):
        """Start the WebSocket connection (blocking).

        This method will block until the connection is closed.
        """
        from src.core.database import get_db

        # Get database session (use context manager properly)
        self.db_context = get_db()
        self.db = self.db_context.__enter__()

        # Create event handler
        self.event_handler = create_event_handler(self.db)

        # Create WebSocket client
        self.client = lark.ws.Client(
            settings.feishu_app_id,
            settings.feishu_app_secret,
            event_handler=self.event_handler,
            log_level=lark.LogLevel.INFO,
        )

        print("✅ 飞书长连接已建立")
        print("📩 等待消息... (按 Ctrl+C 停止)")

        # Start connection (blocking)
        try:
            self.client.start()
        finally:
            # Clean up database session
            self.db_context.__exit__(None, None, None)

    def start_in_thread(self):
        """Start the WebSocket connection in a background thread (non-blocking).

        Returns:
            Thread object
        """
        import threading

        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        return thread

    def stop(self):
        """Stop the WebSocket connection."""
        if self.client:
            self.client.stop()
            print("🔌 飞书长连接已断开")


class LarkAPIClient:
    """Feishu API client for sending messages and calling APIs.

    This is a singleton wrapper around the Lark SDK client.
    """

    _instance = None
    _client = None

    @classmethod
    def get_client(cls):
        """Get the SDK API client (singleton).

        Returns:
            Lark SDK client instance
        """
        if cls._client is None:
            cls._client = lark.Client.builder() \
                .app_id(settings.feishu_app_id) \
                .app_secret(settings.feishu_app_secret) \
                .log_level(lark.LogLevel.INFO) \
                .build()
        return cls._client

    @classmethod
    def send_text_message(cls, receive_id: str, text: str) -> bool:
        """Send a text message to a user.

        Args:
            receive_id: User ID to send to
            text: Message text

        Returns:
            True if successful, False otherwise
        """
        import json

        client = cls.get_client()

        # Build message content
        content = json.dumps({"text": text}, ensure_ascii=False)

        # Build request
        request = lark.im.v1.CreateMessageRequest.builder() \
            .receive_id_type("user_id") \
            .request_body(
                lark.im.v1.CreateMessageRequestBody.builder()
                    .receive_id(receive_id)
                    .msg_type("text")
                    .content(content)
                    .build()
            ).build()

        # Send message
        response = client.im.v1.message.create(request)

        if not response.success():
            print(f"❌ 发送消息失败: {response.code} - {response.msg}")
            return False

        return True

    @classmethod
    def send_rich_text_message(cls, receive_id: str, text: str) -> bool:
        """Send a rich text message to a user.

        Args:
            receive_id: User ID to send to
            text: Message text (supports markdown-style formatting)

        Returns:
            True if successful, False otherwise
        """
        import json

        client = cls.get_client()

        # Build rich text content
        content = json.dumps([{
            "tag": "text",
            "text": text
        }], ensure_ascii=False)

        # Build request
        request = lark.im.v1.CreateMessageRequest.builder() \
            .receive_id_type("user_id") \
            .request_body(
                lark.im.v1.CreateMessageRequestBody.builder()
                    .receive_id(receive_id)
                    .msg_type("text")
                    .content(content)
                    .build()
            ).build()

        # Send message
        response = client.im.v1.message.create(request)

        if not response.success():
            print(f"❌ 发送消息失败: {response.code} - {response.msg}")
            return False

        return True
