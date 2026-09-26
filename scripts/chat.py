"""
Script tương tác hỏi đáp trực tiếp (Interactive Chat CLI) với các Agent trong Lab 11:
- Blue Agent: Trợ lý VinBank có Guardrails (CP2 & CP3).
- Red Default: Trợ lý VinBank không phòng thủ (CP4).
- Red Advance: Trợ lý VinBank có Guardrails tham chiếu (CP4).
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Cấu hình đường dẫn và encoding UTF-8 cho console
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from agents.agent import create_blue_agent, create_red_agent_default
from agents.guards_agent import create_red_agent_advance
from assignment.pipeline import build_production_plugins
from core.config import (
    blue_provider_label,
    red_provider_label,
    setup_api_key,
)
from core.utils import chat_with_agent, format_api_error


def print_banner():
    print("=" * 60)
    print(" VINBANK AGENT INTERACTIVE CHAT — LAB 11")
    print("=" * 60)


def choose_agent():
    print("\nChọn Agent để chat thử nghiệm:")
    print("  [1] Blue Agent        — Có Guardrails đầy đủ (Input + Output)")
    print("                          Model: " + blue_provider_label())
    print("  [2] Red Default       — KHÔNG Guardrails (Unsafe)")
    print("                          Model: " + red_provider_label("default"))
    print("  [3] Red Advance       — Guardrails mạnh (Advanced defense)")
    print("                          Model: " + red_provider_label("advance"))
    print("  [0] Thoát")

    while True:
        choice = input("\nNhập lựa chọn (1/2/3/0): ").strip()
        if choice in {"0", "1", "2", "3"}:
            return choice
        print("Lựa chọn không hợp lệ, vui lòng nhập lại.")


def init_agent(choice: str):
    if choice == "1":
        print("\n--> Khởi tạo Blue Agent (kèm Input/Output Guardrails)...")
        plugins = build_production_plugins(use_llm_judge=False)
        agent, runner = create_blue_agent(plugins=plugins)
        name = "Blue Agent (Protected)"
    elif choice == "2":
        print("\n--> Khởi tạo Red Default (Không có Guardrails)...")
        agent, runner = create_red_agent_default()
        name = "Red Default (Unsafe)"
    elif choice == "3":
        print("\n--> Khởi tạo Red Advance (Guardrails mạnh)...")
        agent, runner = create_red_agent_advance()
        name = "Red Advance (Guarded)"
    else:
        return None, None, None
    return agent, runner, name


async def chat_loop():
    print_banner()
    try:
        setup_api_key()
    except Exception as e:
        print(f"Lưu ý API Key: {e}")

    while True:
        choice = choose_agent()
        if choice == "0":
            print("\nTạm biệt!")
            break

        agent, runner, name = init_agent(choice)
        if not agent:
            break

        print("\n" + "-" * 60)
        print(f"Đang trò chuyện với: {name}")
        print("Lệnh đặc biệt: gõ 'switch' để đổi Agent, 'exit' để thoát.")
        print("-" * 60)

        while True:
            try:
                user_msg = input("\nBạn: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n")
                break

            if not user_msg:
                continue

            cmd = user_msg.lower()
            if cmd in {"exit", "quit", "q"}:
                print("\nTạm biệt!")
                return
            if cmd in {"switch", "change", "back"}:
                break

            try:
                response, _ = await chat_with_agent(agent, runner, user_msg)
                print(f"\n{name}:\n{response}")
            except Exception as e:
                print(f"\n>>> LỖI: {format_api_error(e)}")


def main():
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        print("\nĐã dừng chương trình.")


if __name__ == "__main__":
    main()
