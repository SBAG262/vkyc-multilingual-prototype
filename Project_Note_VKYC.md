# Multilingual VKYC — Project Note

**Prepared by:** Soumen Bag
**Status:** Working prototype, demonstrable
**Date:** October 2026

---

## The problem

The credit-card VKYC team conducts video KYC in English and Hindi only. Customers
across South and East India who are not comfortable in either language drop off at the
V-CIP stage or get diverted to branch KYC — adding cost, delay and abandonment to what
should be a same-day digital journey.

## Why the obvious fix doesn't scale

The standard answer is skill-based routing: send a Tamil customer to a Tamil-speaking
officer. That requires hiring an agent pool per language. The result is predictable —
low-volume language pools sit idle while high-volume pools queue, and every additional
language is a recruitment, training and attrition problem of its own.

## The proposal

Insert a real-time interpretation layer between the officer and the customer, rather
than matching them by language.

- The customer speaks their own language; the officer reads English.
- The officer speaks English; the customer hears their own language.

Because any officer can now handle any call, the separate language pools collapse into
a single shared pool. Utilisation rises, queues even out, and **adding a language
becomes a configuration change rather than a hire.** That is the mechanism that delivers
pan-India coverage without increasing team size.

## Compliance position

This is the part that determines whether the idea is viable at all.

RBI's Master Direction requires V-CIP to be conducted by a trained official of the bank,
who performs the liveness check, varies questions to establish the session is live,
matches the OVD photograph against the live feed, and rejects the session if the
customer appears to be prompted or coached.

**The system is an assistive interpreter. It is not the verifier.** The officer conducts
the session and makes every verification decision. Three design choices enforce this:

| Design choice | Why |
|---|---|
| Officer's transcribed speech shown **editable** before sending | A mis-heard word is caught by the officer, not discovered in an audit |
| Policy assistant answers **only when asked** | No unrequested guidance injected into a live, legally significant conversation |
| Every turn logged with timestamp | Supports the audit-trail requirement |

The distinction between "AI interprets, officer decides" and "AI conducts KYC" is the
difference between a compliant enhancement and an unapprovable system.

## What has been built

A working prototype, demonstrable end to end:

1. **Customer leg** — customer speaks; the language is auto-detected; the officer reads English.
2. **Officer leg** — officer speaks English; the words appear editable; on confirmation they are translated and spoken to the customer in their language.
3. **Policy assistant** — the officer asks a KYC policy question and receives an answer drawn only from the bank's policy knowledge base, with the source section cited. Asked something outside the policy, it says so rather than inventing an answer. For a regulated process, that refusal is the feature.
4. **Session transcript** — every turn logged.

Currently supports Tamil, Telugu, Bengali, Kannada, Malayalam, Marathi, Gujarati,
Punjabi, Odia and Hindi.

## What this prototype is not

Stated plainly, so expectations are set correctly:

- It demonstrates the **interpretation layer only** — no video, liveness, face-match or geo-tagging. Those already exist in the production VKYC platform.
- It runs on a **public cloud AI service**, which is appropriate for a demo and not for live customer data.
- The knowledge base contains **sample policy content**, not the bank's internal policy.
- Speech is **press-to-talk**, not live streaming captions.

## Production considerations

**Data residency.** RBI requires V-CIP infrastructure to sit within the bank's secured
network with data held in India. Production would run self-hosted open models
(IndicConformer, IndicTrans2, Indic-TTS — all MIT-licensed, from AI4Bharat) inside the
bank VPC, or use Bhashini's enterprise tier under a data-handling agreement. The
prototype's AI layer is deliberately isolated so this swap touches two files.

**Bounded translation risk.** Consent statements, declarations and the fixed KYC
question set should be pre-translated once and human-verified, then played verbatim.
Live machine translation would then apply only to non-binding conversation.

**Domain vocabulary.** Generic models stumble on BFSI terms. Fine-tuning on KYC
vocabulary — PAN, OVD, product names — is a known and solvable gap.

## Suggested next steps

1. **Demonstration** to VKYC operations and compliance leadership — 15 minutes, live.
2. **Controlled pilot** on the two highest-drop-off language pools, using self-hosted
   models, with concurrent maker-checker review on every pilot session.
3. **Measure the thesis.** The number that matters: approvals per officer per day
   should hold or rise as language coverage expands, with no net new VKYC headcount.

---

*This prototype was built independently to test feasibility. It uses no bank systems,
no customer data and no internal documents.*
