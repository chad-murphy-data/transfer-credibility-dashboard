"""
llm_structurer_resumable.py

This script processes Fabrizio Romano tweets into structured JSON using OpenAI's GPT.
- `llm_tweet_structurer.py`: Use for quick, clean runs
- `llm_structurer_resumable.py`: Use for long runs with checkpointing

Required:
- Set your OpenAI API key as an environment variable named OPENAI_API_KEY.
"""

import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

import re
import json
import time
import openai
import pandas as pd
from tqdm import tqdm
import os

# Set your OpenAI API key here

CHECKPOINT_FILE = "checkpoint_fabrizio_v1_4.csv"
OUTPUT_FILE = "fabrizio_may_to_june_structured.csv"

def tag_looks_like_move(tweet_text: str) -> bool:
    move_keywords = [
        r'\bdeal\b', r'\bcontacted\b', r'\bin talks\b', r'\boffer\b',
        r'\bagreement\b', r'\bhere we go\b', r'\bmedical\b', r'\blinked\b',
        r'\bset to join\b', r'\bclose to\b', r'\badvanced talks\b',
        r'\brejected\b', r'\bnegotiations\b', r'\bproposal\b', r'\brelease clause\b'
    ]
    pattern = re.compile("|".join(move_keywords), flags=re.IGNORECASE)
    return bool(pattern.search(tweet_text))

def llm_extract_entities(tweet_text: str) -> dict:
    prompt = f"""
You're a football transfer analyst. Your job is to extract structured data from a tweet and assess whether a specific player transfer is likely to happen.

Tweet:
'''{tweet_text}'''

Follow these rules carefully:
[...TRUNCATED FOR SPACE: same rules as before...]
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You extract structured football transfer info from tweets."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        content = response.choices[0].message["content"].strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group())
    except Exception as e:
        print("❌ LLM error:", e)

    return {
        "Player": None,
        "From_Club": None,
        "To_Club": None,
        "Status": None,
        "Certainty_Score": 0.0,
        "LooksLikeMove_LLM": False,
        "From_Club_Guess": "Unknown",
        "To_Club_Guess": "Unknown"
    }

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        return pd.read_csv(CHECKPOINT_FILE)
    else:
        return pd.DataFrame()

def save_checkpoint(results):
    df = pd.DataFrame(results)
    df.to_csv(CHECKPOINT_FILE, index=False)

def process_all_tweets(input_csv_path):
    df = pd.read_csv(input_csv_path)
    print("DEBUG: Columns are", df.columns.tolist())
    df["LooksLikeMove"] = df["Tweet_Content"].apply(tag_looks_like_move)

    done_df = load_checkpoint()
    done_ids = set(done_df["Tweet_ID"]) if not done_df.empty else set()

    results = done_df.to_dict(orient="records") if not done_df.empty else []

    for i, row in tqdm(df.iterrows(), total=len(df)):
        tweet_id = row["Tweet_ID"]
        if tweet_id in done_ids:
            continue

        tweet = row["Tweet_Content"]
        extracted = llm_extract_entities(tweet)
        result = {
            "Tweet_ID": tweet_id,
            "Raw_Tweet": tweet,
            "LooksLikeMove": row["LooksLikeMove"],
            **extracted
        }
        results.append(result)

        if len(results) % 100 == 0:
            save_checkpoint(results)

        time.sleep(1)

    pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Full dataset saved to {OUTPUT_FILE}")

process_all_tweets("fabrizio may to june.csv")
