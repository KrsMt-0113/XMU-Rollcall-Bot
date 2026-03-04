"""Push-based automatic rollcall listener.

This example uses FCM/OneSignal to receive rollcall push notifications
instead of polling. Works automatically within seconds of the teacher
starting a rollcall.

Three channels run concurrently:
  - FCM/MCS    → NUMBER, RADAR, QRCODE rollcalls
  - Socket.IO  → SELF_REGISTRATION rollcalls
  - ntf WS     → generic notifications
"""

import asyncio
from tronclass import TronClassClient
from tronclass.auth import XMULogin

# Authenticate
client = TronClassClient(
    "https://lnt.xmu.edu.cn",
    XMULogin("your_xmu_username", "your_xmu_password"),
)

# Create listener
listener = client.push_listener()


@listener.on_rollcall
def handle_rollcall(rollcall):
    """Auto-answer any incoming rollcall."""
    print(f"[Rollcall] {rollcall.rollcall_type} — {rollcall.course_title}")
    try:
        result = client.rollcall.auto_answer(rollcall)
        print(f"  Answered: {result}")
    except Exception as e:
        print(f"  Failed: {e}")


@listener.on_notification
def handle_notification(msg):
    """Print all other push notifications."""
    print(f"[Notification] {msg}")


# Run forever
if __name__ == "__main__":
    print("Listening for rollcall pushes... (Ctrl+C to stop)")
    asyncio.run(listener.listen())
