
import json
import random
import os
import base64
import urllib.request
import urllib.error

from datetime import datetime, timezone
from pathlib import Path


BASE = Path(__file__).resolve().parent
STUDENTS = BASE / "students.json"

GITHUB_REPO = "YuliaSalishcheva/ai-examiner-agent"
GITHUB_BRANCH = "main"
GITHUB_FILE = "results.json"

TOPICS = [
    "Tokenization and BPE",
    "Word embeddings",
    "Transformers and attention",
    "Language models",
    "Text classification",
    "Evaluation metrics in NLP"
]


def get_github_token():
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        try:
            import streamlit as st
            token = st.secrets.get("GITHUB_TOKEN")
        except Exception:
            token = None

    if not token:
        raise RuntimeError(
            "GitHub token not found. Add GITHUB_TOKEN to Streamlit Secrets."
        )

    return token


class ExamTools:

    def __init__(self):
        self.topics = []
        self.index = 0
        self.email = None

    def start_exam(self, email: str, name: str) -> list[str]:
        students = json.loads(STUDENTS.read_text(encoding="utf-8"))

        matched = any(
            s["email"].strip().casefold() == email.strip().casefold()
            and s["name"].strip().casefold() == name.strip().casefold()
            for s in students
        )

        if not matched:
            raise ValueError(
                "Student not found. Ask the student to check their name and email."
            )

        self.email = email.strip()
        self.topics = random.sample(TOPICS, k=random.choice([2, 3]))
        self.index = 0

        return self.topics.copy()

    def get_next_topic(self) -> str:
        if not self.topics:
            raise ValueError("Exam has not started.")

        if self.index >= len(self.topics):
            return "NO_MORE_TOPICS"

        topic = self.topics[self.index]
        self.index += 1

        return topic

    def end_exam(self, email: str, score: float, history: list[dict]) -> None:
        if (
            self.email is None
            or email.strip().casefold() != self.email.casefold()
        ):
            raise ValueError("Email does not match active exam.")

        if self.index < len(self.topics):
            raise ValueError("Not all topics were covered.")

        score = float(score)

        if not 0 <= score <= 10:
            raise ValueError("Score must be from 0 to 10.")

        entry = {
            "email": email.strip(),
            "score": score,
            "topics": self.topics.copy(),
            "history": history,
            "finished_at": datetime.now(timezone.utc).isoformat()
        }

        self._save_to_github(entry)

    def _save_to_github(self, entry: dict) -> None:
        token = get_github_token()

        url = (
            f"https://api.github.com/repos/{GITHUB_REPO}"
            f"/contents/{GITHUB_FILE}"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AI-NLP-Examiner"
        }

        sha = None

        try:
            request = urllib.request.Request(
                f"{url}?ref={GITHUB_BRANCH}",
                headers=headers
            )

            with urllib.request.urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))

            sha = data["sha"]
            old = json.loads(
                base64.b64decode(data["content"]).decode("utf-8")
            )

        except urllib.error.HTTPError as error:
            if error.code == 404:
                old = []
            else:
                details = error.read().decode("utf-8")
                raise RuntimeError(
                    f"GitHub read error {error.code}: {details}"
                ) from error

        old.append(entry)

        content = base64.b64encode(
            json.dumps(old, ensure_ascii=False, indent=2).encode("utf-8")
        ).decode("utf-8")

        payload = {
            "message": f"Save exam results for {entry['email']}",
            "content": content,
            "branch": GITHUB_BRANCH
        }

        if sha:
            payload["sha"] = sha

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="PUT"
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status not in (200, 201):
                    raise RuntimeError("Could not save results to GitHub.")

        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8")
            raise RuntimeError(
                f"GitHub save error {error.code}: {details}"
            ) from error
