"""Feishu bot client using the new architecture."""
import asyncio
import json
import lark_oapi as lark
from sqlalchemy.orm import Session, sessionmaker
from concurrent.futures import ThreadPoolExecutor
import threading

from src.shared.config import settings
from src.shared.database import SessionLocal, engine
from src.access.feishu.adapter import FeishuAdapter
from src.access.base import AccessRequest


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
            print(f"❌ 发送消息失败: {response.code} - {response.msg}", flush=True)
            return False

        return True

    @classmethod
    def send_markdown_message(cls, receive_id: str, text: str, title: str = "查询结果") -> bool:
        """Send a Markdown message to a user.

        Args:
            receive_id: User ID to send to
            text: Message text in Markdown format
            title: Card title

        Returns:
            True if successful, False otherwise
        """
        client = cls.get_client()

        # Build card with Markdown content
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "content": title,
                    "tag": "plain_text"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": text
                    }
                }
            ]
        }

        content = json.dumps(card, ensure_ascii=False)

        # Build request
        request = lark.im.v1.CreateMessageRequest.builder() \
            .receive_id_type("user_id") \
            .request_body(
                lark.im.v1.CreateMessageRequestBody.builder()
                    .receive_id(receive_id)
                    .msg_type("interactive")
                    .content(content)
                    .build()
            ).build()

        # Send message
        response = client.im.v1.message.create(request)

        if not response.success():
            print(f"❌ 发送Markdown消息失败: {response.code} - {response.msg}", flush=True)
            return False

        return True


class LarkBotClient:
    """Feishu bot client using the new adapter architecture.

    This client uses the official Lark SDK to establish a persistent
    WebSocket connection for receiving events in real-time.
    """

    def __init__(self):
        """Initialize the bot client."""
        self.adapter = None
        self.client = None
        self.executor = None

    def start(self):
        """Start the WebSocket connection (blocking)."""
        # Initialize adapter
        db = SessionLocal()
        try:
            self.adapter = FeishuAdapter(db)
            asyncio.run(self.adapter.initialize_plugins())
            print(f"✅ 已加载 {len(self.adapter.plugin_manager.plugins)} 个插件")

            # Create thread pool for async processing
            self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="feishu_event")

            # Create event handler
            event_handler = self._create_event_handler()

            # Create WebSocket client
            self.client = lark.ws.Client(
                settings.feishu_app_id,
                settings.feishu_app_secret,
                event_handler=event_handler,
                log_level=lark.LogLevel.INFO,
            )

            print("✅ 飞书机器人已启动")
            print("📩 等待消息... (按 Ctrl+C 停止)")

            # Start connection (blocking)
            self.client.start()

        finally:
            if db:
                db.close()

    def stop(self):
        """Stop the WebSocket connection."""
        if self.client:
            self.client.stop()
            print("🔌 飞书机器人已停止")

    def _create_event_handler(self):
        """Create SDK event handler with message receive callback.

        Returns:
            EventDispatcherHandler instance
        """

        def process_message_async(sender_id: str, text: str, message_id: str, feishu_user_id: str):
            """Process message in background thread with isolated database session.

            Args:
                sender_id: Internal user ID (always "1")
                text: Message text
                message_id: Unique message ID
                feishu_user_id: Original Feishu user ID for sending replies
            """
            # Create thread-local database session
            thread_db = SessionLocal()
            try:
                print(f"🔄 [ASYNC] 开始处理消息 {message_id}", flush=True)

                # Create adapter with thread-local session
                thread_adapter = FeishuAdapter(thread_db)
                asyncio.run(thread_adapter.initialize_plugins())

                # Create request with default user ID
                request = AccessRequest(
                    user_id=sender_id,
                    input_text=text,
                    channel="feishu",
                    context={},
                    metadata={}
                )

                # Process request
                response = asyncio.run(thread_adapter.process_request(request))
                formatted = thread_adapter.format_response(response)

                # Send reply
                if response.success:
                    print(f"📫 [ASYNC] 发送到飞书...", flush=True)

                    # Check if response contains markdown
                    msg_type = formatted.get('msg_type', 'text')
                    if msg_type == 'interactive' and response.metadata and 'markdown' in response.metadata:
                        # Send as Markdown card
                        markdown_text = response.metadata['markdown']
                        summary = response.message or ''
                        if summary:
                            # Add summary as plain text before markdown
                            full_content = f"{summary}\n\n{markdown_text}"
                        else:
                            full_content = markdown_text
                        success = LarkAPIClient.send_markdown_message(feishu_user_id, full_content)
                    else:
                        # Send as plain text
                        message_text = formatted.get('content', {}).get('text', '')
                        success = LarkAPIClient.send_text_message(feishu_user_id, message_text)

                    if success:
                        print(f"✓ [ASYNC] 回复发送成功", flush=True)
                    else:
                        print(f"❌ [ASYNC] 发送回复失败", flush=True)
                else:
                    print(f"⚠️ [ASYNC] 处理失败: {response.error}", flush=True)

            except Exception as e:
                print(f"❌ [ASYNC] 处理消息失败: {e}", flush=True)
                import traceback
                traceback.print_exc()
            finally:
                # Always close the thread-local session
                thread_db.close()

        def on_message_received(data: lark.im.v1.P2ImMessageReceiveV1):
            """Handle received message event (async - returns immediately).

            Args:
                data: Message event data from SDK
            """
            try:
                event_data = data.event
                message_id = event_data.message.message_id

                # Extract sender ID
                feishu_user_id = event_data.sender.sender_id.user_id or event_data.sender.sender_id.open_id

                if not feishu_user_id:
                    print("❌ 无法获取发送者 ID", flush=True)
                    return

                # Parse message content
                message_content = event_data.message.content
                content = json.loads(message_content)
                text = content.get("text", "").strip()

                if not text:
                    print("⚠️ 收到空消息，忽略", flush=True)
                    return

                print(f"\n📨 收到消息 [飞书用户: {feishu_user_id}]:")
                print(f"   {text}", flush=True)

                # Use default user ID (1) for all Feishu users, but pass original Feishu ID for replies
                default_user_id = "1"

                # Submit to thread pool for async processing
                self.executor.submit(process_message_async, default_user_id, text, message_id, feishu_user_id)

            except Exception as e:
                print(f"❌ 事件处理失败: {e}", flush=True)
                import traceback
                traceback.print_exc()

        def on_message_read(data: lark.im.v1.P2ImMessageMessageReadV1):
            """Handle message read event (ignore it).

            Args:
                data: Message read event data from SDK
            """
            # Ignore message read events
            return

        # Build and return event dispatcher handler
        return lark.EventDispatcherHandler.builder(
            "", ""  # Empty strings - credentials are in ws.Client
        ).register_p2_im_message_receive_v1(on_message_received) \
         .register_p2_im_message_message_read_v1(on_message_read) \
         .build()

    def _send_text_message(self, user_id: str, text: str) -> bool:
        """Send text message to user.

        Args:
            user_id: User ID (Feishu user_id)
            text: Message text

        Returns:
            True if successful
        """
        return LarkAPIClient.send_text_message(user_id, text)
