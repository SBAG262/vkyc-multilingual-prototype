"""
RAG layer for the VKYC prototype.

Three stages:
  1. RETRIEVE  - find the policy passages most relevant to the question
  2. AUGMENT   - hand those passages to the AI as its only source
  3. GENERATE  - the AI answers from them, and cites the section

Retrieval here is keyword-based scoring, which works well on a small,
focused knowledge base. Production would use embeddings so that
"ID proof" matches "identity document" even with no shared words.
"""

import os
import re
from sarvamai import SarvamAI

KNOWLEDGE_FILE = "kyc_policy.md"

# Words too common to be useful for matching.
STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "of", "to", "in", "for", "on", "at", "by", "with", "from", "as", "and",
    "or", "but", "if", "it", "its", "this", "that", "these", "those",
    "can", "could", "should", "would", "may", "might", "must", "do", "does",
    "did", "have", "has", "had", "i", "we", "you", "he", "she", "they",
    "what", "which", "who", "when", "where", "how", "why", "not", "no",
}


def _words(text: str) -> set:
    """Break text into meaningful lowercase words."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) > 2}


def load_sections() -> list:
    """
    Read the knowledge base and split it into sections.
    Each '## Heading' starts a new section.
    """
    if not os.path.exists(KNOWLEDGE_FILE):
        raise RuntimeError(f"{KNOWLEDGE_FILE} not found")

    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        raw = f.read()

    sections = []
    title = "Introduction"
    body = []

    for line in raw.split("\n"):
        if line.startswith("## "):
            if body:
                sections.append({"title": title, "text": "\n".join(body).strip()})
            title = line[3:].strip()
            body = []
        else:
            body.append(line)

    if body:
        sections.append({"title": title, "text": "\n".join(body).strip()})

    return [s for s in sections if s["text"]]


def retrieve(question: str, top_k: int = 3) -> list:
    """STAGE 1: score every section against the question, return the best."""
    q_words = _words(question)
    scored = []

    for sec in load_sections():
        sec_words = _words(sec["title"] + " " + sec["text"])
        overlap = len(q_words & sec_words)
        # A match in the heading counts double - headings are topic labels.
        heading_bonus = len(q_words & _words(sec["title"])) * 2
        score = overlap + heading_bonus
        if score > 0:
            scored.append({"score": score, **sec})

    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored[:top_k]


def answer_question(question: str) -> dict:
    """STAGES 2 and 3: give the AI the passages, let it answer from them only."""
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY not set - add it to your .env file")

    passages = retrieve(question)

    if not passages:
        return {
            "answer": "That is not covered in the policy knowledge base. "
                      "Please check with your compliance team.",
            "sources": [],
        }

    context = "\n\n".join(
        f"SECTION: {p['title']}\n{p['text']}" for p in passages
    )

    system_prompt = (
        "You are a compliance assistant for bank officers conducting video KYC. "
        "Answer ONLY from the policy sections provided below. "
        "If the answer is not in those sections, say that it is not covered in "
        "the policy and that the officer should check with compliance. "
        "Never guess or draw on outside knowledge. "
        "Keep the answer under 60 words and state the rule plainly. "
        "End with the section name you used, in the form: [Source: section name]"
        "\n\nPOLICY SECTIONS:\n" + context
    )

    client = SarvamAI(api_subscription_key=api_key)
    resp = client.chat.completions(
        model="sarvam-105b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.1,   # low = stick to the facts, don't get creative
    )

    # Pull the reply text out of the response object.
    try:
        answer = resp.choices[0].message.content
    except AttributeError:
        answer = resp["choices"][0]["message"]["content"]

    return {
        "answer": answer,
        "sources": [p["title"] for p in passages],
    }