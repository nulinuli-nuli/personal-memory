"""SDK event handler adapter for Feishu bot."""
import json
import lark_oapi as lark
from sqlalchemy.orm import Session

from src.feishu.handlers import FeishuEventHandler


def create_event_handler(db: Session):
    """Create SDK event handler with message receive callback.

    Args:
        db: Database session

    Returns:
        EventDispatcherHandler instance
    """

    # Create business logic handler
    handler = FeishuEventHandler(db)

    def on_message_received(data: lark.im.v1.P2ImMessageReceiveV1):
        """Handle received message event.

        Args:
            data: Message event data from SDK
        """
        print(f"🔍 [DEBUG] Event received, type: {type(data).__name__}", flush=True)
        try:
            # Access through data.event (not data directly)
            event_data = data.event

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

            # Handle message (delegates to business logic)
            response_text = handler.handle_message_by_text(
                sender_id=sender_id,
                text=text
            )

            # Send reply (only if not duplicate)
            if response_text is None:
                print(f"⚠️ 重复消息，跳过回复", flush=True)
            elif response_text:
                print(f"📫 [发送回复] 发送到飞书...", flush=True)
                # Import here to avoid circular import
                from src.feishu.client import LarkAPIClient
                success = LarkAPIClient.send_text_message(sender_id, response_text)
                if not success:
                    print(f"❌ 发送回复失败", flush=True)
                else:
                    print(f"✓ 回复发送成功", flush=True)
            else:
                print(f"⚠️ 无回复内容（可能已处理）", flush=True)

        except Exception as e:
            print(f"❌ 处理消息失败: {e}")
            import traceback
            traceback.print_exc()

            # Try to send error message
            try:
                if 'sender_id' in locals():
                    from src.feishu.client import LarkAPIClient
                    LarkAPIClient.send_text_message(
                        sender_id,
                        f"❌ 处理失败: {str(e)}"
                    )
            except Exception:
                pass

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
