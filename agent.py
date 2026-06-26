"""Persian local ERP agent with Ollama and a rich terminal interface."""
import json
from typing import Any, List, Tuple

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

import ollama

from config import MAX_TOOL_STEPS, MODEL_NAME, OLLAMA_HOST
from mcp_server import ERPServer


class LocalERPAgent:
    def __init__(self, server: ERPServer | None = None, model_name: str | None = None, ollama_host: str | None = None) -> None:
        self.server = server or ERPServer()
        self.model_name = model_name or MODEL_NAME
        self.ollama_host = ollama_host or OLLAMA_HOST
        self.console = Console()
        self.client = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            self.client = ollama.Client(host=self.ollama_host)
        except Exception as exc:  # pragma: no cover - runtime dependency
            self.client = None
            self.last_error = str(exc)

    def _build_system_prompt(self) -> str:
        tools = self.server.get_tools_definition()
        schema_instruction = (
            "Available tables are: `products` (id, name, price, stock), "
            "`customers` (id, name, city, phone, email), and "
            "`orders` (id, customer_id, product_id, quantity). "
            "You must use these exact table names when calling tools."
        )
        return (
            "شما یک دستیار ERP محلی و فارسی‌زبان هستید. "
            "برای هر پرسش مربوط به داده‌های ERP، محصولات، مشتریان، سفارش‌ها یا گزارش‌ها، حتماً از ابزارهای دیتابیس استفاده کن. "
            "وقتی نیاز به خواندن داده دارید، باید فوراً ابزار را فراخوانی کنید و فقط JSON ابزار را در خروجی بدهید، بدون متن اضافی. "
            "پس از دریافت داده‌های خام از پایگاه داده، هرگز خروجی خام JSON یا متن انگلیسی نده. "
            "پاسخ نهایی باید فقط به صورت لیست ساده و فارسی باشد. "
            "از قالب زیر استفاده کن: - نام محصول: [نام] | قیمت: [قیمت] | موجودی: [موجودی] "
            "اگر داده‌ها مربوط به مشتریان باشند، از قالب: - نام مشتری: [نام] | شهر: [شهر] | تلفن: [تلفن] استفاده کن. "
            "همه‌ی عناوین و توضیحات باید به فارسی باشند و از جدول‌های پیچیده یا متن انگلیسی پرهیز کن. "
            "هرگز از حدس یا اطلاعات خارج از داده‌های واقعی استفاده نکن. "
            f"{schema_instruction} "
            f"ابزارهای در دسترس: {json.dumps(tools, ensure_ascii=False)}"
        )

    def _render_dashboard(self, title: str, history: List[Tuple[str, str]], final_text: str | None = None) -> Group:
        lines: List[Text] = []
        for role, item in history[-6:]:
            prefix = "🛠️" if role == "tool" else "🧠"
            style = "bold cyan" if role == "tool" else "bold magenta"
            lines.append(Text(f"{prefix} {item}", style=style))
        if final_text:
            lines.append(Text("\n✅ پاسخ نهایی", style="bold green"))
            lines.append(Text(final_text, style="white"))

        body = Group(*lines) if lines else Group(Text("در حال آماده‌سازی...", style="italic dim"))
        spinner = Spinner("dots", text=Text(title, style="bold cyan"))
        panel = Panel(body, title="[bold gold1]عامل ERP محلی[/bold gold1]", subtitle="Ollama + SQLite", border_style="bright_cyan")
        return Group(spinner, panel)

    def run(self, user_question: str) -> str:
        if self.client is None:
            return (
                "اتصال به Ollama برقرار نشد. لطفاً سرویس Ollama را روی localhost:11434 اجرا کنید "
                "و دوباره تلاش کنید."
            )

        system_prompt = self._build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question},
        ]
        history: List[Tuple[str, str]] = []

        for _ in range(MAX_TOOL_STEPS):
            with Live(self._render_dashboard("در حال تحلیل سوال...", history), console=self.console, refresh_per_second=8) as live:
                try:
                    response = self.client.chat(
                        model=self.model_name,
                        messages=messages,
                        tools=self.server.get_tools_definition(),
                        stream=False,
                    )
                except Exception as exc:
                    return f"خطا در ارتباط با Ollama: {exc}"

                assistant_message = response.get("message", {})
                assistant_content = assistant_message.get("content", "") or ""
                tool_calls = assistant_message.get("tool_calls", []) or []

                if not tool_calls:
                    final_answer = assistant_content.strip() or "پاسخ کوتاهی دریافت نشد."
                    history.append(("assistant", final_answer))
                    live.update(self._render_dashboard("پاسخ آماده شد", history, final_answer))
                    return final_answer

                tool_call_message = {
                    "role": "assistant",
                    "content": assistant_content,
                    "tool_calls": tool_calls,
                }
                messages.append(tool_call_message)

                for tool_call in tool_calls:
                    function = tool_call.get("function", {})
                    tool_name = function.get("name")
                    arguments_raw = function.get("arguments", "{}")
                    try:
                        arguments = json.loads(arguments_raw) if isinstance(arguments_raw, str) else arguments_raw
                    except (TypeError, json.JSONDecodeError):
                        arguments = {}

                    if tool_name is None:
                        continue

                    try:
                        result = self.server.handle_tool_call(tool_name, arguments)
                    except Exception as exc:
                        result = {"error": str(exc)}

                    messages.append(
                        {
                            "role": "tool",
                            "name": tool_name,
                            "content": json.dumps(result, ensure_ascii=False, default=str),
                        }
                    )
                    history.append(("tool", f"{tool_name}: {json.dumps(arguments, ensure_ascii=False)}"))
                    live.update(self._render_dashboard("در حال استفاده از ابزار...", history))

        return "تعداد مراحل تحلیل بیش از حد شد. لطفاً سؤال را ساده‌تر کنید."

    def close(self) -> None:
        self.server.close()


if __name__ == "__main__":
    agent = LocalERPAgent()
    agent.console.print(
        Panel(
            "سلام! من دستیار ERP محلی شما هستم. در مورد محصولات، مشتریان و سفارش‌ها بپرسید.",
            title="[bold green]AI Agent محلی[/bold green]",
            border_style="green",
        )
    )
    while True:
        try:
            user_question = input("سوال شما: ").strip()
        except KeyboardInterrupt:
            print("\nخروج از برنامه...")
            break

        if not user_question:
            continue
        if user_question.lower() in {"exit", "quit", "خروج", "بbye", "bye"}:
            print("خروج از برنامه...")
            break

        answer = agent.run(user_question)
        agent.console.print(Panel(answer, title="[bold yellow]پاسخ نهایی[/bold yellow]", border_style="yellow"))

    agent.close()
