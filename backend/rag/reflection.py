"""
Reflection Agent (Agent C).

Receives both agent responses, judges them against pramāṇa/Advaita/register,
loads imprints, can trigger up to 2 retry rounds on whichever agent failed,
then outputs the final response + reasoning.
"""

import os
import json
from dataclasses import dataclass
from typing import List, Optional

from backend.rag.groq_client import get_client, chat as groq_chat
from backend.rag.imprints import load_imprints

REFLECTION_SYSTEM = """You are the Reflection Agent for SankaRĀGamana.

You are an auditor, not a philosopher. You do not judge what is Advaitic.
You do not judge doctrinal correctness. The corpus is the only pramāṇa.
Your job is purely mechanical: audit both responses on three observable criteria,
pick the better one, output JSON.

SEEKER PROFILE:
{seeker_profile_formatted}

RETRIEVED CHUNKS — AGENT A used:
{agent_a_chunks_full}

RETRIEVED CHUNKS — AGENT B used:
{agent_b_chunks_full}

AGENT A RESPONSE (Sanskrit path, Sanskrit query: {sanskrit_query}):
{agent_a_response}

AGENT B RESPONSE (Original language path):
{agent_b_response}

LEARNED IMPRINTS (distilled from past feedback):
Positive principles (what works): {positive_imprints}
Negative principles (what fails): {negative_imprints}

YOUR THREE AUDIT CRITERIA — apply mechanically, not philosophically:

1. PRAMĀṆA SCORE (0.0 to 1.0)
   Read each sentence in the response.
   Count: how many sentences are traceable to a retrieved chunk above?
   Score = sentences_grounded / total_sentences
   A sentence is grounded if its content appears in the chunks above.
   A sentence is NOT grounded if it adds information not in any chunk.
   Do NOT judge whether the information is philosophically correct —
   only whether it appears in the retrieved chunks.

2. REGISTER FIT (0 or 1)
   Does the tone obviously match the seeker profile?
   beginner or distressed → should be simple and warm (not dense or technical)
   scholar or advanced → should be precise and technical (not simplified)
   Score 1 if appropriate, 0 if obviously mismatched.
   Only score 0 for clear mismatch. When in doubt, score 1.

3. CHUNK COVERAGE (0.0 to 1.0)
   How many of the retrieved chunks contributed at least one sentence to the response?
   Score = chunks_used_in_response / total_chunks_retrieved
   Higher is better — it means the response makes full use of available pramāṇa.

SCORING:
combined_score = (pramana_score * 0.5) + (register_fit * 0.3) + (chunk_coverage * 0.2)

Pick the response with higher combined_score as winner.
If scores are equal or within 0.05 — prefer Agent A (Sanskrit path),
because the corpus is Sanskrit and the Sanskrit query retrieves closer matches.

CORRECTION LOGIC:
Only flag correction_for_a or correction_for_b if pramāṇa_score < 0.6.
The correction must be specific: name which sentences are ungrounded.
Do not correct register or coverage — those are not worth a retry.

OUTPUT — valid JSON only, no markdown, no explanation outside the JSON:
{{
  "agent_a_pramana": <float>,
  "agent_a_register": <0 or 1>,
  "agent_a_coverage": <float>,
  "agent_a_score": <float>,
  "agent_b_pramana": <float>,
  "agent_b_register": <0 or 1>,
  "agent_b_coverage": <float>,
  "agent_b_score": <float>,
  "winner": "a" or "b",
  "final_response": "<synthesized response — rules: (1) Take the winning agent's Sanskrit passages and citations as the authoritative pramāṇa base. (2) Pull the translation and explanation from Agent B wherever it clarifies meaning — do not discard it just because A won. (3) If the seeker's language is English: present the Sanskrit verse first, then its translation, then the meaning for the seeker — all in English prose. (4) If the seeker's language is Hindi: same structure but explanation in Hindi. (5) If the seeker's language is Sanskrit: full Sanskrit throughout, no translation needed. (6) If the seeker's language is Kannada: explanation in Kannada, Sanskrit verses cited with translation. (7) Remove all duplicate sentences. (8) Do NOT copy either agent verbatim — synthesize into one clean, unified response that reads naturally in the seeker's language.>",
  "reasoning": "<one sentence: which score was higher and why>",
  "correction_for_a": "<specific sentence-level correction or null>",
  "correction_for_b": "<specific sentence-level correction or null>"
}}"""

RETRY_SYSTEM = """You are SankaRĀGamana. Regenerate your previous response with this correction applied.

Original query: {query}
Your previous response: {previous_response}
Correction required: {correction}
Retrieved chunks (same as before): {chunks_formatted}

Apply the correction strictly. Do not change what was already correct.
Respond only with the corrected response, no preamble."""


@dataclass
class ReflectionResult:
    final_response: str
    reasoning: str
    winner: str
    chunks_used: List[dict]
    agent_a_response: str
    agent_b_response: str


def _fmt_chunks(chunks: list) -> str:
    if not chunks:
        return "none"
    return " | ".join(
        f"{c.get('text_name','?')} v.{c.get('verse_number','?')} (sim={c.get('similarity',0):.3f})"
        for c in chunks
    )


def _fmt_imprints(imprints: list) -> str:
    if not imprints:
        return "none yet"
    return "\n".join(
        f"- [{i['confidence']:.2f}] {i['principle']}" for i in imprints
    )


def _fmt_profile(profile: dict) -> str:
    return (
        f"level={profile.get('level')} intent={profile.get('intent')} "
        f"tone={profile.get('emotional_tone')} language={profile.get('language')}"
    )


def _fmt_chunks_full(chunks: list) -> str:
    if not chunks:
        return "No passages retrieved."
    return "\n\n".join(
        f"[{i+1}] {c.get('text_name','?')}, v.{c.get('verse_number','?')}\n{c.get('content','')}"
        for i, c in enumerate(chunks)
    )


def _dedupe_repeated_half(text: str) -> str:
    """If text is the same content concatenated twice, return one copy.
    Handles the case where the model emits 'X. X.' with X repeated."""
    t = text.strip()
    n = len(t)
    if n < 40:
        return t
    half = n // 2
    # Check exact halves (with optional whitespace in the middle)
    first = t[:half].strip()
    second = t[half:].strip()
    if first and first == second:
        return first
    # Check if the second half starts by repeating the first sentence verbatim
    first_sentence = t.split(".")[0].strip()
    if first_sentence and len(first_sentence) > 25:
        idx = t.find(first_sentence, len(first_sentence))
        if idx != -1:
            candidate = t[:idx].strip()
            if candidate:
                return candidate
    return t


def _is_clean_prose(text: str) -> bool:
    """True if text is a real prose response, not leaked JSON/profile/error markers."""
    if not text or not text.strip():
        return False
    t = text.strip()
    # Reject anything that looks like a JSON object/array or contains audit keys
    if t.startswith("{") or t.startswith("["):
        return False
    leaks = (
        '"final_response"', '"winner"', '"agent_a_pramana"', '"reasoning"',
        "reflection error", "jsondecodeerror", "level=", "intent=",
        "emotional_tone", "retrieval_strategy",
    )
    low = t.lower()
    if any(marker in low for marker in leaks):
        return False
    return True


def _extract_field(text: str, key: str) -> Optional[str]:
    """Pull a single string field out of malformed/truncated JSON by regex.
    Used as a last resort when json.loads fails (e.g. truncated at max_tokens)."""
    import re
    # Match "key": "...." allowing escaped quotes inside
    m = re.search(rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
    if m:
        try:
            return json.loads('"' + m.group(1) + '"')  # unescape
        except Exception:
            return m.group(1)
    return None


def _parse_reflection(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # Truncated or malformed JSON — salvage the prose fields by regex so
        # we still get a usable synthesis instead of falling back to raw text.
        final_resp = _extract_field(text, "final_response")
        if not final_resp:
            raise  # nothing salvageable — let caller use fallback
        result = {
            "final_response": final_resp,
            "winner": (_extract_field(text, "winner") or "b").strip().lower()[-1:] or "b",
            "reasoning": _extract_field(text, "reasoning") or "",
            "correction_for_a": None,
            "correction_for_b": None,
        }

    # Repair final_response spacing — normalize whitespace within paragraphs
    # but preserve paragraph breaks for markdown rendering. Also dedupe.
    if "final_response" in result and result["final_response"]:
        resp = result["final_response"]
        # Split on paragraph breaks, normalize each paragraph internally
        paragraphs = resp.split("\n\n")
        cleaned = []
        seen = set()
        for para in paragraphs:
            # Within a paragraph, collapse multiple spaces/newlines to single space
            para = " ".join(para.split())
            if not para:
                continue
            # Drop exact-duplicate paragraphs (model sometimes repeats the whole block)
            key = para.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(para)
        joined = "\n\n".join(cleaned)
        # Catch whole-text duplication: text repeated back-to-back with no break
        joined = _dedupe_repeated_half(joined)
        result["final_response"] = joined

    return result


async def _retry_agent(
    query: str,
    previous_response: str,
    correction: str,
    chunks: list,
    model: str,
) -> str:
    try:
        resp = groq_chat(
            model=model,
            messages=[
                {"role": "system", "content": RETRY_SYSTEM.format(
                    query=query,
                    previous_response=previous_response,
                    correction=correction,
                    chunks_formatted=_fmt_chunks_full(chunks),
                )},
                {"role": "user", "content": query},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[reflection] retry failed: {e}")
        return previous_response


async def run_reflection_agent(
    query: str,
    seeker_profile: dict,
    agent_a,   # AgentResult from agent_a
    agent_b,   # AgentResult from agent_b
) -> ReflectionResult:
    imprints = load_imprints()

    a_response = agent_a.response
    b_response = agent_b.response
    a_chunks = agent_a.chunks
    b_chunks = agent_b.chunks

    for _round in range(2):  # max 2 retry rounds
        try:
            raw = groq_chat(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": REFLECTION_SYSTEM.format(
                        seeker_profile_formatted=_fmt_profile(seeker_profile),
                        sanskrit_query=getattr(agent_a, "sanskrit_query", ""),
                        agent_a_chunks_full=_fmt_chunks_full(a_chunks),
                        agent_a_response=a_response,
                        agent_b_chunks_full=_fmt_chunks_full(b_chunks),
                        agent_b_response=b_response,
                        positive_imprints=_fmt_imprints(imprints["positive"]),
                        negative_imprints=_fmt_imprints(imprints["negative"]),
                    )},
                    {"role": "user", "content": f"Audit these two responses for: {query}"},
                ],
                temperature=0.1,
                max_tokens=1024,
            )
            judgment = _parse_reflection(raw.choices[0].message.content)
        except Exception as e:
            print(f"[reflection] judgment failed (round {_round}): {e}")
            # Use better of the two responses as fallback, deduped + spacing normalized
            fallback = b_response or a_response or ""
            fallback = " ".join(fallback.split())  # normalize whitespace
            fallback = _dedupe_repeated_half(fallback)  # kill any doubled text
            return ReflectionResult(
                final_response=fallback,
                reasoning=f"Reflection error ({type(e).__name__}) — using Agent B response.",
                winner="b",
                chunks_used=b_chunks,
                agent_a_response=a_response,
                agent_b_response=b_response,
            )

        correction_a = judgment.get("correction_for_a")
        correction_b = judgment.get("correction_for_b")

        # Only retry if pramāṇa is critically low (< 0.6) and we have a correction
        a_needs_retry = correction_a and judgment.get("agent_a_pramana", 1.0) < 0.6
        b_needs_retry = correction_b and judgment.get("agent_b_pramana", 1.0) < 0.6

        if (not a_needs_retry and not b_needs_retry) or _round == 1:
            break

        if a_needs_retry:
            a_response = await _retry_agent(
                query, a_response, correction_a, a_chunks, "llama-3.3-70b-versatile"
            )
        if b_needs_retry:
            b_response = await _retry_agent(
                query, b_response, correction_b, b_chunks, "llama-3.3-70b-versatile"
            )

    winner = judgment.get("winner", "b")
    chunks_used = a_chunks if winner == "a" else b_chunks

    # Guarantee final_response is clean prose — never JSON, never an error marker.
    final_resp = judgment.get("final_response") or ""
    if not _is_clean_prose(final_resp):
        # The model returned something that looks like JSON/profile/garbage —
        # fall back to the winning agent's actual response.
        final_resp = (b_response if winner == "b" else a_response) or b_response or a_response or ""
        final_resp = " ".join(final_resp.split())

    return ReflectionResult(
        final_response=final_resp,
        reasoning=judgment.get("reasoning", ""),
        winner=winner,
        chunks_used=chunks_used,
        agent_a_response=a_response,
        agent_b_response=b_response,
    )
