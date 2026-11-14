# AI NLP Examiner

An LLM agent that examines students on 2–3 random NLP topics using real function calls.

## Local setup

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Enter your OpenAI API key in the sidebar (or set `OPENAI_API_KEY`). Use the demo student `Юлія`, `test@example.com`.

## Tools

- `start_exam(email, name)`: validates student and selects topics.
- `get_next_topic()`: moves to the next topic.
- `end_exam(email, score, history)`: saves results to `results.json`.

The application passes the real history from the session to `end_exam` rather than trusting model-provided history. Student data is for demonstration only. Do not commit API keys or private exam records.

## Deployment

Deploy to Streamlit Community Cloud or another Python hosting service. Set `OPENAI_API_KEY` as a secret, or enter it in the sidebar. Note that local `results.json` storage may not persist on ephemeral hosting; use durable storage for production.
