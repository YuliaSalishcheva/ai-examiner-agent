
import json
import random
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
STUDENTS = BASE / "students.json"
RESULTS = BASE / "results.json"

TOPICS = [
    "Tokenization and BPE",
    "Word embeddings",
    "Transformers and attention",
    "Language models",
    "Text classification",
    "Evaluation metrics in NLP"
]


class ExamTools:
    def __init__(self):
        self.topics = []
        self.index = 0
        self.email = None
        self.current_topic = None
        self.completed_topics = []
        self.correct_answers = 0

    def start_exam(self, email: str, name: str) -> list[str]:
        students = json.loads(
            STUDENTS.read_text(encoding="utf-8")
        )

        matched = any(
            s["email"].casefold() == email.strip().casefold()
            and s["name"].strip().casefold() == name.strip().casefold()
            for s in students
        )

        if not matched:
            raise ValueError(
                "Student not found. Ask the student to check their name and email."
            )

        self.email = email.strip()
        self.topics = random.sample(
            TOPICS,
            k=random.choice([2, 3])
        )

        self.index = 0
        self.current_topic = None
        self.completed_topics = []
        self.correct_answers = 0

        return self.topics.copy()

    def get_next_topic(self) -> str:
        if not self.topics:
            raise ValueError("Exam has not started.")

        if self.current_topic is not None:
            raise ValueError(
                "The current topic has not been completed yet."
            )

        if self.index >= len(self.topics):
            return "NO_MORE_TOPICS"

        topic = self.topics[self.index]
        self.index += 1
        self.current_topic = topic

        return topic

    def record_topic_result(self, topic: str, correct: bool) -> dict:
        if self.current_topic is None:
            raise ValueError("There is no active topic.")

        if topic != self.current_topic:
            raise ValueError(
                "Cannot evaluate a topic that is not currently active."
            )

        if topic in self.completed_topics:
            raise ValueError("This topic has already been evaluated.")

        if not isinstance(correct, bool):
            raise ValueError("The result must be True or False.")

        self.completed_topics.append(topic)

        if correct:
            self.correct_answers += 1

        self.current_topic = None

        return {
            "topic": topic,
            "correct": correct,
            "completed": len(self.completed_topics),
            "total": len(self.topics),
            "score": self.calculate_score()
        }

    def calculate_score(self) -> float:
        if not self.topics:
            return 0.0

        score = (
            self.correct_answers / len(self.topics)
        ) * 10

        return round(score, 2)

    def end_exam(
        self,
        email: str,
        score: float,
        history: list[dict]
    ) -> None:

        if self.email is None:
            raise ValueError("Exam has not started.")

        if email.casefold() != self.email.casefold():
            raise ValueError("Email does not match active exam.")

        if self.current_topic is not None:
            raise ValueError("The current topic has not been completed.")

        if len(self.completed_topics) != len(self.topics):
            raise ValueError("Not all topics were covered.")

        score = self.calculate_score()

        entry = {
            "email": email,
            "score": score,
            "correct_answers": self.correct_answers,
            "total_topics": len(self.topics),
            "topics": self.topics.copy(),
            "history": history,
            "finished_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

        old = (
            json.loads(RESULTS.read_text(encoding="utf-8"))
            if RESULTS.exists()
            else []
        )

        old.append(entry)

        RESULTS.write_text(
            json.dumps(old, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
