# Transfer Credibility Dashboard

A Streamlit-based tool for tracking and analyzing football transfer rumors, with structured data extracted from tweets (mainly Fabrizio Romano) using OpenAI.

## 📊 What It Does

- Filters and displays transfer rumors by:
  - Status category
  - Club (origin or destination)
  - Certainty score
- Visualizes the most credible rumors
- Provides a downloadable CSV of filtered results
- Supports LLM-based structuring of raw tweet data

## 🧠 LLM Processing (OpenAI)

Structured data is generated using `gpt-3.5-turbo` via scripts in `/scripts/`:

- `llm_tweet_structurer.py` – quick single-run processor
- `llm_structurer_resumable.py` – safe for long jobs with checkpointing

Set your OpenAI key as an environment variable:
```bash
export OPENAI_API_KEY=sk-...
