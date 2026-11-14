
import json
from datetime import datetime, timezone
from openai import OpenAI
from tools import ExamTools

SYSTEM = """
Ти екзаменатор з NLP. Спілкуйся українською, коротко та зрозуміло.
Спочатку запитай ім'я та email студента. Перевір їх через `start_exam`. Якщо студент не знайдений, попроси правильні дані.
Отримуй теми через `get_next_topic`. Став по одному запитанню та чекай відповіді. Якщо потрібно, постав до двох уточнювальних запитань. Не повторюйся і не переходь до наступної теми без відповіді студента, якщо він не відмовився відповідати.
Після всіх тем вистав оцінку від 0 до 10, коротко поясни її та дай рекомендації.
Виклич `end_exam`, щоб зберегти результат та історію іспиту.
Не вигадуй відповіді студента.
"""

SCHEMAS = [
    {"type": "function", "function": {
        "name": "start_exam",
        "description": "Перевірити студента та вибрати теми",
        "parameters": {"type": "object", "properties": {
            "email": {"type": "string"}, "name": {"type": "string"}
        }, "required": ["email", "name"]}
    }},
    {"type": "function", "function": {
        "name": "get_next_topic",
        "description": "Отримати наступну тему або NO_MORE_TOPICS",
        "parameters": {"type": "object", "properties": {}}
    }},
    {"type": "function", "function": {
        "name": "end_exam",
        "description": "Зберегти оцінку та історію іспиту",
        "parameters": {"type": "object", "properties": {
            "email": {"type": "string"},
            "score": {"type": "number"},
            "history": {"type": "array", "items": {"type": "object"}}
        }, "required": ["email", "score", "history"]}
    }}
]

class ExaminerAgent:
    def __init__(self, api_key: str, model="llama-3.3-70b-versatile"):
        self.client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        self.model = model
        self.tools = ExamTools()
        self.messages = [{"role": "system", "content": SYSTEM}]
        self.history = []
        self.finished = False

    def _record(self, role, content):
        self.history.append({
            "role": role, "content": str(content),
            "datetime": datetime.now(timezone.utc).isoformat()
        })

    def respond(self, user_text: str) -> str:
        if self.finished:
            return "Іспит завершено. Почніть новий іспит."

        self.messages.append({"role": "user", "content": user_text})
        self._record("user", user_text)

        for _ in range(12):
            response = self.client.chat.completions.create(
                model=self.model, messages=self.messages,
                tools=SCHEMAS, tool_choice="auto", temperature=0.3
            )
            msg = response.choices[0].message
            self.messages.append(msg.model_dump(exclude_none=True))

            if not msg.tool_calls:
                answer = msg.content or ""
                self._record("assistant", answer)
                return answer

            for call in msg.tool_calls:
                name = call.function.name
                try:
                    args = json.loads(call.function.arguments)
                    if name == "start_exam":
                        result = self.tools.start_exam(**args)
                    elif name == "get_next_topic":
                        result = self.tools.get_next_topic()
                    elif name == "end_exam":
                        score = float(args["score"])
                        if not 0 <= score <= 10:
                            raise ValueError("Оцінка має бути від 0 до 10")
                        self._record("tool_call", "end_exam")
                        self.tools.end_exam(args["email"], score, self.history.copy())
                        self.finished = True
                        result = "Іспит успішно збережено"
                    else:
                        result = {"error": "Невідомий інструмент"}
                except Exception as exc:
                    result = {"error": str(exc)}

                if name != "end_exam":
                    self._record("tool_call", f"{name}: {result}")

                self.messages.append({
                    "role": "tool", "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })

        raise RuntimeError("Забагато викликів інструментів. Спробуйте ще раз.")
