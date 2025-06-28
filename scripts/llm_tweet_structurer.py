"""
llm_tweet_structurer.py

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

# Set your OpenAI API key here
##SET
# Tag tweets using regex to create LooksLikeMove
def tag_looks_like_move(tweet_text: str) -> bool:
    move_keywords = [
        r'\bdeal\b', r'\bcontacted\b', r'\bin talks\b', r'\boffer\b',
        r'\bagreement\b', r'\bhere we go\b', r'\bmedical\b', r'\blinked\b',
        r'\bset to join\b', r'\bclose to\b', r'\badvanced talks\b',
        r'\brejected\b', r'\bnegotiations\b', r'\bproposal\b'
    ]
    pattern = re.compile("|".join(move_keywords), flags=re.IGNORECASE)
    return bool(pattern.search(tweet_text))

# LLM extraction with robust JSON handling and LooksLikeMove_LLM tag

def llm_extract_entities(tweet_text: str) -> dict:
    prompt = f"""
You're a football transfer analyst. Your job is to extract structured data from a tweet and assess whether a specific player transfer is likely to happen.

Tweet:
'''{tweet_text}'''

Follow these rules carefully:

1. If the tweet is about a **coach or manager** appointment (e.g. "X joins Sevilla as new head coach"), do NOT extract any data. Return all fields as null or false. Set LooksLikeMove_LLM to false.

2. Use the following examples as calibration:

[
  {{
    "Tweet": "Manchester City have contacted Benfica for João Neves.",
    "Status": "Contact",
    "Certainty_Score": 0.5
  }},
  {{
    "Tweet": "Chelsea are in advanced talks with Brighton for Caicedo.",
    "Status": "Agreement",
    "Certainty_Score": 0.7
  }},
  {{
    "Tweet": "Here we go! Declan Rice joins Arsenal — £105m deal agreed.",
    "Status": "Here we go",
    "Certainty_Score": 1.0
  }},
  {{
    "Tweet": "Tottenham appreciate Conor Gallagher but no talks yet.",
    "Status": "Link",
    "Certainty_Score": 0.3
  }},
  {{
    "Tweet": "Liverpool want João Palhinha, deal depends on outgoings.",
    "Status": "Link",
    "Certainty_Score": 0.4
  }},
  {{
    "Tweet": "PSG have submitted a bid for Kvaratskhelia.",
    "Status": "Bid",
    "Certainty_Score": 0.6
  }},
  {{
    "Tweet": "Barça president Laporta: 'We want Ansu Fati back but it’s up to the coach.'",
    "Status": "Link",
    "Certainty_Score": 0.3
  }}
]

3. Calibrate scores carefully:
- Certainty_Score should reflect the **likelihood that the specific transfer will happen**, based on this tweet alone.
- Only ~15–25% of all transfer rumors lead to completed moves. Use this prior when assigning scores.
- Do not base scores solely on tweet phrasing or tone. Focus on substance.

4. Club guessing guidance:
- If the tweet does not name a From_Club or To_Club but one can be **reasonably inferred**, you must guess it.
- Always fill From_Club_Guess and To_Club_Guess using public football knowledge, even if unsure.
- If truly impossible to guess, return "Unknown" (not null), but this should be rare.

Examples of guessing behavior:

{{
  "Tweet": "Pep Guardiola on Mohamed Salah: 'He’s a top player, and of course he’d improve any team.'",
  "Status": "Link",
  "From_Club": "Liverpool",
  "To_Club": null,
  "From_Club_Guess": "Liverpool",
  "To_Club_Guess": "Manchester City",
  "Certainty_Score": 0.3
}},
{{
  "Tweet": "Barcelona have made contact with João Cancelo, but no talks yet with Man City.",
  "Status": "Contact",
  "From_Club": "Manchester City",
  "To_Club": "Barcelona",
  "From_Club_Guess": "Manchester City",
  "To_Club_Guess": "Barcelona",
  "Certainty_Score": 0.5
}}

Return ONLY valid JSON with these fields:
- Player: Full name of the player, or null
- From_Club: Exact club stated in the tweet, or null
- To_Club: Exact club stated in the tweet, or null
- Status: One of ["Link", "Contact", "Bid", "Agreement", "Here we go", "Deal off", null]
- Certainty_Score: float from 0.0 to 1.0 based on calibrated judgment
- LooksLikeMove_LLM: true if this tweet is plausibly about a player transfer, false otherwise
- From_Club_Guess: best guess at origin club, or "Unknown"
- To_Club_Guess: best guess at destination club, or "Unknown"

Only respond with the JSON object. No explanation or commentary.
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
        "LooksLikeMove_LLM": False
    }

# Sample 10 rumors + 10 non-rumors for balanced LLM test
def sample_mixed_tweets(df, rumor_count=10, non_rumor_count=10):
    rumors = df[df["LooksLikeMove"] == True].sample(n=rumor_count, random_state=42)
    non_rumors = df[df["LooksLikeMove"] == False].sample(n=non_rumor_count, random_state=42)
    return pd.concat([rumors, non_rumors]).reset_index(drop=True)

# Main processing pipeline
def process_tweets(input_csv_path, output_csv_path):
    df = pd.read_csv(input_csv_path)
    print("DEBUG: Columns are", df.columns.tolist())

    # First pass to tag with regex
    df["LooksLikeMove"] = df["Tweet_Content"].apply(tag_looks_like_move)

    # Sample for LLM processing
    sample_df = sample_mixed_tweets(df, rumor_count=10, non_rumor_count=10)

    results = []

    for _, row in tqdm(sample_df.iterrows(), total=len(sample_df)):
        tweet = row["Tweet_Content"]
        extracted = llm_extract_entities(tweet)

        result = {
            "Tweet_ID": row.get("Tweet_ID", None),
            "Raw_Tweet": tweet,
            "LooksLikeMove": row["LooksLikeMove"],
            **extracted
        }

        results.append(result)
        time.sleep(1)

    output_df = pd.DataFrame(results)
    output_df.to_csv(output_csv_path, index=False)
    print(f"✅ Saved structured data to {output_csv_path}")

# Run the pipeline
process_tweets("fabrizio may to june.csv", "fabrizio_may_to_june_structured.csv")
