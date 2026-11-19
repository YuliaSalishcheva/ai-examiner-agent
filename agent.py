
import json
from datetime import datetime, timezone
from openai import OpenAI
from tools import ExamTools

SYSTEM = """
Ти екзаменатор з NLP. Спілкуйся українською, коротко та зрозуміло.

1. Запитай ім'я та email, перевір через start_exam.
2. Отримуй теми через get_next_topic.
3. Став по одному основному запитанню на тему.
4. За потреби постав до двох уточнювальних запитань.
5. Після завершення теми один раз виклич record_topic_result.
6. Правильна відповідь — correct=true, неправильна або
   "не знаю" після уточнень — correct=false.
7. Не повторюй завершені теми та не переходь далі,
   поки не записаний результат поточної теми.
8. Коли теми закінчаться, отримай оцінку з Python,
   поясни результат і дай рекомендації.
9. Виклич end_exam для збереження результату.

Не вигадуй відповіді та оцінки. Підсумковий бал обчислює Python.
"""

SCHEMAS = [
    {"type": "function", "function": {
        "name": "start_exam",
        "description": "Перевірити студента та вибрати теми",
        "parameters": {"type": "object", "properties": {
            "email": {"type": "string"},
            "name": {"type": "string"}
        }, "required": ["email", "name"]}
    }},
    {"type": "function", "function": {
        "name": "get_next_topic",
        "description": "Отримати наступну тему",
        "parameters": {"type": "object", "properties": {}}
    }},
    {"type": "function", "function": {
        "name": "record_topic_result",
        "description": "Записати результат теми",
        "parameters": {"type": "object", "properties": {
            "topic": {"type": "string"},
            "correct": {"type": "boolean"}
        }, "required": ["topic", "correct"]}
    }},
    {"type": "function", "function": {
        "name": "end_exam",
        "description": "Зберегти результат іспиту",
        "parameters": {"type": "object", "properties": {
            "email": {"type": "string"},
            "score": {"type": "number"}
        }, "required": ["email", "score"]}
    }}
]


class ExaminerAgent:
    def __init__(self, api_key: str, model="llama-3.3-70b-versatile"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = model
        self.tools = ExamTools()
        self.messages = [{"role": "system", "content": SYSTEM}]
        self.history = []
        self.finished = False

    def _record(self, role, content):
        self.history.append({
            "role": role,
            "content": str(content),
            "datetime": datetime.now(timezone.utc).isoformat()
        })

    def respond(self, user_text: str) -> str:
        if self.finished:
            return "Іспит завершено. Почніть новий іспит."

        self.messages.append({"role": "user", "content": user_text})
        self._record("user", user_text)

        for _ in range(12):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=SCHEMAS,
                tool_choice="auto",
                temperature=0.3
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

                    elif name == "record_topic_result":
                        result = self.tools.record_topic_result(**args)

                    elif name == "end_exam":
                        score = self.tools.calculate_score()
                        self.tools.end_exam(
                            args["email"], score, self.history.copy()
                        )
                        self.finished = True
                        result = {"status": "success", "score": score}

                    else:
                        result = {"error": "Невідомий інструмент"}

                except Exception as exc:
                    result = {"error": str(exc)}

                self._record("tool_call", f"{name}: {result}")

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })

        raise RuntimeError("Забагато викликів інструментів. Спробуйте ще раз.")
