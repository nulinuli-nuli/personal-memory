"""SDK event handler adapter for Feishu bot."""
import json
import lark_oapi as lark
from sqlalchemy.orm import Session, sessionmaker
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

from src.feishu.handlers import FeishuEventHandler
from src.core.database import engine


def create_event_handler(db: Session):
    """Create SDK event handler with message receive callback.

    Args:
        db: Database session (not used in async mode, each thread creates its own)

    Returns:
        EventDispatcherHandler instance
    """

    # Create thread-safe session factory for async processing
    # Each thread will get its own database session
    SessionLocal = sessionmaker(bind=engine)

    # Create thread pool for async processing
    # Use max_workers=4 to handle concurrent message processing
    executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="feishu_event")

    def process_message_async(sender_id: str, text: str, message_id: str):
        """Process message in background thread with isolated database session.

        Each thread gets its own database session to ensure thread safety.

        Args:
            sender_id: Feishu user ID
            text: Message text
            message_id: Unique message ID
        """
        # Create thread-local database session
        thread_db = SessionLocal()
        try:
            print(f"🔄 [ASYNC] 开始处理消息 {message_id}", flush=True)

            # Create handler with thread-local session
            thread_handler = FeishuEventHandler(thread_db)

            # Handle message (delegates to business logic)
            response_text = thread_handler.handle_message_by_text(
                sender_id=sender_id,
                text=text
            )

            # Send reply (only if not duplicate)
            if response_text is None:
                print(f"⚠️ [ASYNC] 重复消息，跳过回复", flush=True)
            elif response_text:
                print(f"📫 [ASYNC] 发送到飞书...", flush=True)
                # Import here to avoid circular import
                from src.feishu.client import LarkAPIClient
                success = LarkAPIClient.send_text_message(sender_id, response_text)
                if not success:
                    print(f"❌ [ASYNC] 发送回复失败", flush=True)
                else:
                    print(f"✓ [ASYNC] 回复发送成功", flush=True)
            else:
                print(f"⚠️ [ASYNC] 无回复内容（可能已处理）", flush=True)

        except Exception as e:
            print(f"❌ [ASYNC] 处理消息失败: {e}", flush=True)
            import traceback
            traceback.print_exc()

            # Try to send error message
            try:
                from src.feishu.client import LarkAPIClient
                LarkAPIClient.send_text_message(
                    sender_id,
                    f"❌ 处理失败: {str(e)}"
                )
            except Exception:
                pass
        finally:
            # Always close the thread-local session
            thread_db.close()

    def on_message_received(data: lark.im.v1.P2ImMessageReceiveV1):
        """Handle received message event (async - returns immediately).

        This function extracts message data and submits processing to a thread pool,
        ensuring the event handler returns within Feishu's 3-second timeout requirement.

        Args:
            data: Message event data from SDK
        """
        print(f"🔍 [DEBUG] Event received, type: {type(data).__name__}", flush=True)

        try:
            # Access through data.event (not data directly)
            event_data = data.event
            message_id = data.event.message.message_id
            print(f"🔍 [DEBUG] Message ID: {message_id}", flush=True)

            # Extract message information
            # Try user_id first, fall back to open_id
            sender_id = event_data.sender.sender_id.user_id or event_data.sender.sender_id.open_id

            # Log for debugging
            print(f"🔍 [DEBUG] user_id: {event_data.sender.sender_id.user_id}", flush=True)
            print(f"🔍 [DEBUG] open_id: {event_data.sender.sender_id.open_id}", flush=True)
            print(f"🔍 [DEBUG] Using sender_id: {sender_id}", flush=True)

            if not sender_id:
                print("❌ 无法获取发送者 ID", flush=True)
                return

            message_content = event_data.message.content

            print(f"🔍 [DEBUG] Sender ID: {sender_id}", flush=True)
            print(f"🔍 [DEBUG] Message content: {message_content}", flush=True)

            # Parse JSON content
            content = json.loads(message_content)
            text = content.get("text", "").strip()

            print(f"🔍 [DEBUG] Extracted text: {text}", flush=True)

            if not text:
                print("⚠️ 收到空消息，忽略", flush=True)
                return

            print(f"📩 收到消息: {text}", flush=True)
            print(f"⏱️ [ASYNC] 提交到后台线程处理...", flush=True)

            # Submit to thread pool for async processing
            # This returns immediately, avoiding Feishu's 3-second timeout
            executor.submit(process_message_async, sender_id, text, message_id)
            print(f"✅ [ASYNC] 事件处理函数立即返回 (<0.1s)", flush=True)

        except Exception as e:
            print(f"❌ 事件处理失败: {e}", flush=True)
            import traceback
            traceback.print_exc()

    def on_message_read(data: lark.im.v1.P2ImMessageMessageReadV1):
        """Handle message read event (ignore it).

        Args:
            data: Message read event data from SDK
        """
        print(f"📖 [DEBUG] Message read event received (ignoring), type: {type(data).__name__}", flush=True)
        # Simply ignore message read events - we don't need to process them
        return

    # Build and return event dispatcher handler
    # Note: APP_ID and APP_SECRET are set in ws.Client, not here
    return lark.EventDispatcherHandler.builder(
        "", ""  # Empty strings - credentials are in ws.Client
    ).register_p2_im_message_receive_v1(on_message_received) \
     .register_p2_im_message_message_read_v1(on_message_read) \
     .build()
