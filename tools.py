import json
import random
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
STUDENTS = BASE / 'students.json'
RESULTS = BASE / 'results.json'
TOPICS = ['Tokenization and BPE', 'Word embeddings', 'Transformers and attention', 'Language models', 'Text classification', 'Evaluation metrics in NLP']

class ExamTools:
    def __init__(self):
        self.topics = []
        self.index = 0
        self.email = None

    def start_exam(self, email: str, name: str) -> list[str]:
        students = json.loads(STUDENTS.read_text(encoding='utf-8'))
        matched = any(s['email'].casefold() == email.strip().casefold() and s['name'].strip().casefold() == name.strip().casefold() for s in students)
        if not matched:
            raise ValueError('Student not found. Ask the student to check their name and email.')
        self.email = email.strip()
        self.topics = random.sample(TOPICS, k=random.choice([2, 3]))
        self.index = 0
        return self.topics.copy()

    def get_next_topic(self) -> str:
        if not self.topics:
            raise ValueError('Exam has not started.')
        if self.index >= len(self.topics):
            return 'NO_MORE_TOPICS'
        topic = self.topics[self.index]
        self.index += 1
        return topic

    def end_exam(self, email: str, score: float, history: list[dict]) -> None:
        if self.email is None or email.casefold() != self.email.casefold():
            raise ValueError('Email does not match active exam.')
        if self.index < len(self.topics):
            raise ValueError('Not all topics were covered.')
        score = float(score)
        if not 0 <= score <= 10:
            raise ValueError('Score must be from 0 to 10.')
        entry = {'email': email, 'score': score, 'topics': self.topics, 'history': history, 'finished_at': datetime.now(timezone.utc).isoformat()}
        old = json.loads(RESULTS.read_text(encoding='utf-8')) if RESULTS.exists() else []
        old.append(entry)
        RESULTS.write_text(json.dumps(old, ensure_ascii=False, indent=2), encoding='utf-8')
