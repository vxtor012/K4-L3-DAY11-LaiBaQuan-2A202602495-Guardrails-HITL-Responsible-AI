"""
Lab 11 — Helper Utilities
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.config import get_llm_provider, PROVIDER_OPENROUTER  # noqa: F401
from core.openai_runtime import OpenAIRunner


async def chat_with_agent(agent, runner, user_message: str, session_id=None):
    """Send a message to the agent and get the response.

    Works with OpenAIRunner (OpenAI Red / OpenRouter Blue) and Google ADK (Gemini Red).
    """
    provider = getattr(runner, "provider", None)
    if isinstance(runner, OpenAIRunner) or provider in ("openrouter", "openai"):
        text = await runner.chat(agent, user_message)
        return text, None

    from google.genai import types

    user_id = "student"
    app_name = runner.app_name

    session = None
    if session_id is not None:
        try:
            session = await runner.session_service.get_session(
                app_name=app_name, user_id=user_id, session_id=session_id
            )
        except (ValueError, KeyError):
            pass

    if session is None:
        try:
            session = await runner.session_service.create_session(
                app_name=app_name, user_id=user_id
            )
        except Exception:
            session = await runner.session_service.create_session(
                app_name=app_name, user_id=user_id
            )

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)],
    )

    final_response = ""
    async for event in runner.run_async(
        user_id=user_id, session_id=session.id, new_message=content
    ):
        if hasattr(event, "content") and event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    final_response += part.text

    return final_response, session


def format_api_error(e: Exception) -> str:
    """Format raw API exceptions into clean, human-readable console messages."""
    msg = str(e)
    msg_lower = msg.lower()
    if "503" in msg or "unavailable" in msg_lower or "high demand" in msg_lower:
        return (
            "[503 UNAVAILABLE] Model đang quá tải tạm thời (High demand spikes). "
            "Vui lòng thử lại sau vài giây hoặc ít phút."
        )
    if "429" in msg or "resource_exhausted" in msg_lower or "quota" in msg_lower:
        return (
            "[429 RESOURCE EXHAUSTED] Đã vượt giới hạn quota hoặc rate limit (RPM/RPD). "
            "Hãy tăng REQUEST_DELAY_SECONDS trong .env hoặc kiểm tra lại quota API key."
        )
    if "401" in msg or "403" in msg or "unauthenticated" in msg_lower or "permission" in msg_lower:
        return "[AUTH ERROR] API key không hợp lệ hoặc thiếu quyền truy cập."
    first_line = msg.strip().split("\n")[0]
    return f"[{type(e).__name__}] {first_line[:160]}"

