# Multilingual VKYC Interpretation Layer

A working prototype of a real-time interpretation layer for video KYC, built so that
an English/Hindi-speaking verification officer can conduct a V-CIP session with a
customer speaking any of 10+ Indian languages — without the bank hiring a separate
agent pool per language.

Includes a grounded policy assistant (RAG) that answers officer questions from a KYC
knowledge base and refuses to answer from anything else.

---

## The problem

A bank's credit-card VKYC team conducts video KYC only in English and Hindi. Customers
across South and East India either drop off or get routed to branch KYC.

The usual fix is **skill-based routing** — send a Tamil customer to a Tamil-speaking
agent. That forces the bank to hire an agent pool per language. Low-volume pools sit
idle, high-volume pools queue, and every new language means new headcount.

## The approach

Insert an interpretation layer between officer and customer instead:

- Customer speaks Tamil → ASR + translation → officer reads English
- Officer speaks English → translation + TTS → customer hears Tamil

Any officer can now take any call, so N language pools collapse into one. Utilisation
rises, queues even out, and adding a language is a config change rather than a hire.
**That is the mechanism that holds team size flat.**

## The compliance position (important)

RBI's Master Direction on KYC requires V-CIP to be conducted by a trained official of
the regulated entity, who performs the liveness check, varies questions to prove the
session is live, matches the OVD photograph to the live feed, and rejects the session
on observing prompting or coaching.

**This system is an assistive interpreter, not the verifier.** The human officer
conducts the session and makes every legally significant judgment. The design reflects
that deliberately:

- The officer's transcribed speech is shown **editable** before it is sent, so a
  mis-heard word ("PAN card" → "pen card") is caught by the officer, not discovered later.
- The policy assistant is **pull, not push** — it answers when asked and never injects
  unrequested guidance into a live session.
- Every turn is logged to a session transcript, standing in for the audit trail.

---

## What's built

| Component | What it does |
|---|---|
| Customer leg | Records customer speech, auto-detects the language, returns English text |
| Officer leg | Records officer's English, shows it editable, translates and speaks it to the customer |
| Policy assistant | Retrieval-augmented answers from a KYC knowledge base, with the source section cited |
| Session transcript | Logs every turn with a timestamp |

### Architecture

```
Browser (press-to-talk)
        │
        ▼
FastAPI backend ──── translator.py ──── Sarvam AI (ASR / MT / TTS)
        │
        └─────────── rag.py ─────────── retrieval + grounded answer
                         │
                    kyc_policy.md
```

All provider calls are isolated in `translator.py` and `rag.py`. Swapping Sarvam for
Bhashini, or for self-hosted AI4Bharat models, means changing those files only.

### Files
| File | Purpose |
|---|---|
| `main.py` | FastAPI backend and routes |
| `translator.py` | All speech and translation calls |
| `rag.py` | Retrieval and grounded answering |
| `kyc_policy.md` | The policy knowledge base (sample content — replace with real internal policy) |
| `static/index.html` | The interface |
| `requirements.txt` | Python dependencies |
| `Project_Note_VKYC.md` | One-page business note for leadership |
| `.env` | Your API key (never committed) |

---

## Running it locally

**Prerequisites:** Python 3.9+, and a Sarvam AI API key from https://dashboard.sarvam.ai

```bash
# 1. Clone and enter the project
git clone https://github.com/SBAG262/vkyc-multilingual-prototype.git
cd vkyc-multilingual-prototype

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your key — create a file named .env containing:
#    SARVAM_API_KEY=your_key_here

# 5. Run
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000

Note: microphone access requires either `localhost` or HTTPS. A deployed version must
be served over HTTPS.

---

## Honest limitations

These are design choices and gaps worth stating plainly rather than discovering in a demo.

**Press-to-talk, not streaming.** The officer and customer hold a button to speak. True
live captioning — words appearing as they are spoken — needs Sarvam's streaming
WebSocket API. Press-to-talk was chosen to get a working end-to-end loop first.

**Keyword retrieval, not embeddings.** The RAG layer scores policy sections by keyword
overlap. Production RAG uses embeddings so that "ID proof" matches "identity document"
with no shared words. Keyword matching works well on a small, focused knowledge base;
it degrades as the base grows.

**Sample knowledge base.** `kyc_policy.md` contains illustrative content based on
publicly available RBI V-CIP norms. It is not the bank's internal policy and must be
replaced before any real use.

**No video, liveness, or face-match.** The prototype demonstrates the interpretation
layer only. Liveness detection, OVD photo matching, geo-tagging and session recording
already exist in the bank's VKYC platform; integrating with them is a separate task.

**Public cloud inference.** Calls go to Sarvam's hosted API. RBI requires V-CIP
infrastructure to sit within the regulated entity's secured network, with data
residency in India. A production deployment would use self-hosted models inside the
bank VPC (see below) or a contracted enterprise tier.

**No authentication or rate limiting.** Anyone with the URL can use it and consume API
credits. Fine for a controlled demo; not for an open link.

---

## Production path

The prototype uses Sarvam AI because it offers immediate self-serve access. For a
production deployment, two routes:

1. **Bhashini** (government-backed, MeitY) — appropriate for a public-sector-aligned
   stack, with an enterprise tier and data-handling agreement.
2. **Self-hosted open models in the bank VPC** — the underlying models are MIT-licensed
   and available from AI4Bharat: IndicConformer (ASR), IndicTrans2 (translation),
   Indic-TTS. This satisfies data localisation cleanly, removes the external dependency,
   and allows fine-tuning on BFSI and KYC vocabulary where generic models stumble.

Further production work, in rough priority order:

- **Golden strings.** Consent statements, declarations and the fixed KYC question set
  should be pre-translated once and human-verified, then played verbatim — bounding
  mistranslation risk to non-binding conversation only.
- **Confidence gating.** Flag low-confidence transcription or translation to the officer
  rather than passing it through silently.
- **Streaming ASR** for live captions.
- **Alteration-proof audit storage** of source audio, transcript, translation,
  confidence scores, timestamps and officer ID per turn.

---

## Credits

Built as a prototype by Soumen Bag. Speech, translation and LLM services by
[Sarvam AI](https://www.sarvam.ai/).
