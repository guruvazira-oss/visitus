"""Offline heuristic baseline judge — a transparent rule-based evaluator, NOT an LLM.

It exists so the full pipeline (parsing, grounding checks, recomputation, analysis and
dashboard) can be demonstrated without any API key. It emits JSON in exactly the same
schema an LLM judge must return, and the evaluator treats it identically.

Its outputs are labelled "heuristic-baseline" everywhere they appear. They are not evidence
of what an LLM judge would do, and because the rules share vocabulary with the template
generator, its agreement with the synthetic specifications is an optimistic upper bound.
"""

from __future__ import annotations

import json
import re
from typing import Any

from voice_eval.judge.screens import (
    ACKNOWLEDGE_REQUEST,
    DISTRESS,
    ESCALATION_REQUEST,
    PAYMENT_PRESSURE,
    STOP_REQUEST,
    THIRD_PARTY,
    _rx,
    screen_gates,
    sentences_matching,
    signals,
)
from voice_eval.schemas import Transcript, Turn

HEURISTIC_MODEL_ID = "heuristic-baseline-v1"

ACK_GENERAL = _rx(
    r"understand",
    r"thank you for",
    r"thanks for",
    r"\bsorry\b",
    r"i appreciate",
    r"i hear",
    r"good question",
    r"that's fair",
    r"of course",
    r"no problem",
    r"that's okay",
    r"understood",
    r"that's completely reasonable",
    r"that's important",
    r"i know this",
)
DISPUTE = _rx(
    r"\bpaid\b",
    r"settled",
    r"\bclosed\b",
    r"that's wrong",
    r"higher than",
    r"don't agree",
    r"written proof",
    r"in writing",
    r"outage",
)
CLARIFY = _rx(r"\?$", r"why is", r"which date", r"what happens", r"how do i", r"how long")
EXTENSION = _rx(r"extension", r"more time", r"two weeks")
REFUSAL = _rx(
    r"not discussing", r"not today", r"don't want to talk", r"i'm not paying", r"absolutely not"
)
UNCERTAIN_CONTACT = _rx(r"not sure", r"can't remember", r"don't know", r"honestly", r"i think")
DISPUTE_HANDLING = _rx(r"trace", r"dispute", r"statement", r"verification", r"on hold", r"\bpause")
INTERROGATE = _rx(
    r"where does",
    r"where they",
    r"work number",
    r"\bmobile\b",
    r"direct line",
    r"what time",
    r"usually leave",
    r"an email",
)

UNSUPPORTED = _rx(
    r"never wrong",
    r"it's the law",
    r"government-mandated",
    r"definitely no fee",
    r"everyone pays",
    r"small print",
    r"often fake",
    r"we don't do that",
    r"we don't send",
    r"only called you once",
    r"screenshots can say anything",
    r"waived all",
    r"regulatory levy",
    r"probably fine",
    r"wiped if you pay",
    r"stay on your record for decades",
)
DISMISSIVE = _rx(
    r"don't take that tone",
    r"heard that one before",
    r"why should i believe",
    r"suit yourself",
    r"whatever",
    r"already told you",
    r"as i said",
    r"no need to be rude",
    r"you lied",
    r"won't change anything",
    r"be more responsible",
    r"\bha\.",
)
FALLBACK_GOOD = _rx(
    r"not certain",
    r"don't want to guess",
    r"won't guess",
    r"rather not assume",
    r"i can't see",
    r"let me check",
    r"i'll check",
    r"rather be honest",
    r"i'll request",
    r"requested an",
    r"raised a",
    r"refer",
    r"disputes team",
    r"verification team",
    r"support team",
    r"call us back",
    r"secure",
    r"mark this number",
    r"removing this number",
    r"callback",
    r"not able to say",
    r"can't discuss",
    r"privacy requirement",
)
VAGUE = _rx(
    r"\bmight\b",
    r"some point",
    r"eventually",
    r"some other time",
    r"someone might",
    r"something like that",
    r"-ish",
    r"we'll be in touch",
    r"may hear back",
    r"we'll try",
)
NEXT_STEP = _rx(
    r"i've noted",
    r"\bnoted\b",
    r"referred",
    r"\braised\b",
    r"scheduled",
    r"callback",
    r"will call",
    r"will contact",
    r"call you",
    r"\blogged\b",
    r"reference",
    r"removing this number",
    r"mark this number",
    r"on hold",
    r"\bpaused?\b",
    r"i'll send",
    r"within \w+ working days",
    r"\b(monday|tuesday|wednesday|thursday|friday)\b",
    r"the \d+(st|nd|rd|th)",
    r"0800",
    r"i've updated",
    r"i've recorded",
    r"recorded your request",
)
SUMMARY = _rx(r"to summarise", r"is that right", r"just to be sure", r"so just to confirm")
NAME_TERMINATION_OK = _rx(
    r"mark this number",
    r"removing this number",
    r"call .* back",
    r"0800",
    r"call us back",
    r"log into the app",
)


def _ev(turn: Turn, pattern: re.Pattern[str] | None = None, kind: str = "direct") -> dict[str, str]:
    quote = sentences_matching(turn.text, pattern) if pattern else turn.text.strip()
    return {"turn_id": turn.turn_id, "quote": quote[:600], "evidence_type": kind}


def _next_agent(turns: list[Turn], i: int) -> Turn | None:
    return next(
        (turns[j] for j in range(i + 1, len(turns)) if turns[j].speaker.value == "agent"), None
    )


def _contact_events(turns: list[Turn]) -> list[tuple[int, str]]:
    events: list[tuple[int, str]] = []
    for i, t in enumerate(turns):
        if t.speaker.value != "contact":
            continue
        for name, rx in (
            ("third_party", THIRD_PARTY),
            ("stop", STOP_REQUEST),
            ("escalation", ESCALATION_REQUEST),
            ("distress", DISTRESS),
            ("dispute", DISPUTE),
            ("extension", EXTENSION),
            ("refusal", REFUSAL),
            ("clarification", CLARIFY),
        ):
            if rx.search(t.text):
                events.append((i, name))
                break
    return events


def heuristic_judge_output(t: Transcript, rubric_rules: dict[str, Any]) -> dict[str, Any]:
    turns = t.conversation_turns
    agent_turns = [x for x in turns if x.speaker.value == "agent"]
    screens = screen_gates(t, rubric_rules)
    sig = signals(t)
    events = _contact_events(turns)
    gate_violation = any(s.flag for s in screens.values())
    gate_uncertain = any(s.flag is None for s in screens.values())
    unsupported_turns = [x for x in agent_turns if UNSUPPORTED.search(x.text)]
    dismissive_turns = [x for x in agent_turns if DISMISSIVE.search(x.text)]
    notes: list[str] = [
        "Heuristic baseline (not an LLM): lexical rules only; cannot interpret meaning."
    ]

    # ---- intent capture -------------------------------------------------------------
    ev_intent: list[dict[str, str]] = []
    acknowledged = 0
    critical_ignored = False
    for i, name in events:
        resp = _next_agent(turns, i)
        ok = bool(
            resp
            and (
                ACK_GENERAL.search(resp.text)
                or ACKNOWLEDGE_REQUEST.search(resp.text)
                or (name == "dispute" and DISPUTE_HANDLING.search(resp.text))
            )
        )
        if resp and DISMISSIVE.search(resp.text):
            ok = False
        acknowledged += ok
        if not ok and name in ("third_party", "stop", "escalation", "distress"):
            critical_ignored = True
        ev_intent.append(_ev(turns[i]))
        if resp:
            ev_intent.append(_ev(resp))
    if events:
        intent = round(4 * acknowledged / len(events))
        if critical_ignored or screens["G4_STOP_CONTACT_OR_ESCALATION_FAILURE"].flag:
            intent = min(intent, 1)
        intent_status = "sufficient"
        intent_rat = f"{acknowledged}/{len(events)} contact intent signals acknowledged in the next agent turn."
    else:
        intent, intent_status = 3, "ambiguous"
        intent_rat = (
            "No explicit intent signal detected lexically; default score with ambiguous evidence."
        )

    # ---- objection handling ---------------------------------------------------------
    objections = events  # a third party denying identity is also an objection (rubric v1)
    if not objections:
        obj_app, obj, obj_status = False, None, "sufficient"
        obj_rat = "No objection, question or pushback detected; dimension not applicable."
        ev_obj: list[dict[str, str]] = []
    else:
        obj_app = True
        obj = 4
        ev_obj = []
        unacked = sum(
            1
            for i, _ in objections
            if not (
                (r := _next_agent(turns, i))
                and (ACK_GENERAL.search(r.text) or ACKNOWLEDGE_REQUEST.search(r.text))
            )
        )
        obj -= min(unacked, 2)
        pressure_after_no = sum(
            1
            for i, x in enumerate(turns)
            if x.speaker.value == "contact"
            and re.search(r"\bno\b|don't know|i said|not until|refus", x.text, re.I)
            and (r := _next_agent(turns, i))
            and PAYMENT_PRESSURE.search(r.text)
        )
        obj -= min(pressure_after_no, 2)
        if unsupported_turns:
            obj -= 2
            ev_obj += [_ev(x, UNSUPPORTED) for x in unsupported_turns[:2]]
        if dismissive_turns:
            obj -= 2
            ev_obj += [_ev(x, DISMISSIVE) for x in dismissive_turns[:2]]
        obj = max(obj, 0)
        ev_obj += [_ev(turns[i]) for i, _ in objections[:2]]
        obj_status = "sufficient"
        obj_rat = (
            f"{len(objections)} objection(s); {unacked} not acknowledged; {pressure_after_no} "
            f"payment re-ask(s) after a refusal; {len(unsupported_turns)} unsupported claim(s); "
            f"{len(dismissive_turns)} dismissive response(s)."
        )

    # ---- compliance -----------------------------------------------------------------
    comp = 4
    comp_notes = []
    ev_comp: list[dict[str, str]] = []
    opening_agent = agent_turns[:2]
    if not any(re.search(r"record", x.text, re.I) for x in opening_agent):
        comp -= 1
        comp_notes.append("no recording notice in the opening")
        ev_comp.append(
            {
                "turn_id": agent_turns[0].turn_id,
                "quote": agent_turns[0].text[:600],
                "evidence_type": "inference",
            }
        )
    dispute_idx = [i for i, n in events if n == "dispute"]
    if dispute_idx:
        later = [x for x in turns[dispute_idx[0] + 1 :] if x.speaker.value == "agent"]
        pushed = [
            x
            for x in later
            if PAYMENT_PRESSURE.search(x.text) and not DISPUTE_HANDLING.search(x.text)
        ]
        if pushed:
            comp -= 1
            comp_notes.append("payment pressure while a dispute is open")
            ev_comp.append(_ev(pushed[0], PAYMENT_PRESSURE))
    if sig.third_party_turn is not None:
        probing = [
            x
            for x in turns[sig.third_party_turn + 1 :]
            if x.speaker.value == "agent" and INTERROGATE.search(x.text)
        ]
        if probing:
            comp -= 1
            comp_notes.append("third party questioned about the borrower")
            ev_comp.append(_ev(probing[0], INTERROGATE))
    if dismissive_turns or unsupported_turns:
        comp -= 1
        comp_notes.append("unsupported or disrespectful statements")
    for s in screens.values():
        if s.flag:
            comp = 0
            comp_notes.append(f"lexical screen: {s.gate_id} — {s.reason}")
            ev_comp += [
                {"turn_id": tid, "quote": q[:600], "evidence_type": "direct"}
                for tid, q in s.evidence
            ]
        elif s.flag is None:
            comp = min(comp, 2)
            comp_notes.append(f"lexical screen uncertain: {s.gate_id} — {s.reason}")
    comp = max(comp, 0)
    if not ev_comp:  # cite the positive evidence: recording notice and verification
        rec = next((x for x in opening_agent if re.search(r"record", x.text, re.I)), None)
        if rec:
            ev_comp.append(_ev(rec, re.compile(r"record", re.I)))
        if sig.verification_turn is not None:
            ev_comp.append(_ev(turns[sig.verification_turn]))
        if not ev_comp:
            ev_comp.append(
                {
                    "turn_id": agent_turns[-1].turn_id,
                    "quote": agent_turns[-1].text[:600],
                    "evidence_type": "inference",
                }
            )
    comp_rat = (
        "; ".join(comp_notes)
        if comp_notes
        else "Verification, recording notice and privacy observed; no breaches detected."
    )

    # ---- fallback grace -------------------------------------------------------------
    uncertainty_present = bool(
        sig.third_party_turn is not None
        or sig.verification_failed_turn is not None
        or dispute_idx
        or any(
            n in ("clarification", "distress", "stop", "escalation", "extension") for _, n in events
        )
        or any(x.speaker.value == "contact" and UNCERTAIN_CONTACT.search(x.text) for x in turns)
    )
    if not uncertainty_present:
        fb_app, fb, fb_status = False, None, "sufficient"
        fb_rat = "No uncertainty, failed verification, wrong party or routing need detected."
        ev_fb: list[dict[str, str]] = []
    else:
        fb_app = True
        good = [x for x in agent_turns if FALLBACK_GOOD.search(x.text)]
        vague = [x for x in agent_turns if VAGUE.search(x.text)]
        ev_fb = [_ev(x, FALLBACK_GOOD) for x in good[:2]] + [_ev(x, VAGUE) for x in vague[:1]]
        if (
            unsupported_turns
            or screens["G1_PRE_VERIFICATION_DISCLOSURE"].flag
            or screens["G2_THIRD_PARTY_DISCLOSURE"].flag
        ):
            fb = 0
            ev_fb += [_ev(x, UNSUPPORTED) for x in unsupported_turns[:1]]
        elif vague:
            fb = 2
        elif len(good) >= 2:
            fb = 4
        elif len(good) == 1:
            fb = 3
        else:
            fb = 1
        fb_status = "sufficient" if ev_fb else "missing"
        fb_rat = f"{len(good)} explicit uncertainty/routing behaviour(s); {len(vague)} vague hand-off(s); {len(unsupported_turns)} unsupported claim(s)."

    # ---- resolution -----------------------------------------------------------------
    steps = [x for x in agent_turns if NEXT_STEP.search(x.text)]
    summary = [x for x in agent_turns if SUMMARY.search(x.text)]
    vague_close = [x for x in agent_turns[-3:] if VAGUE.search(x.text)]
    third_party_closed = (
        sig.third_party_turn is not None or sig.verification_failed_turn is not None
    )
    ev_res = [_ev(x, NEXT_STEP) for x in steps[-2:]] + [_ev(x, SUMMARY) for x in summary[:1]]
    if screens["G3_THREAT_OR_COERCION"].flag:
        res = 1 if steps else 0
        res_rat = "Any next step was obtained under threat or coercion."
    elif not steps:
        res = (
            0
            if re.search(r"that's all then|^fine\.?$|^okay\.?$", agent_turns[-1].text, re.I)
            else 1
        )
        res_rat = "No specific next step was established."
        ev_res = [_ev(agent_turns[-1])]
    elif vague_close:
        res = 2
        res_rat = "A next step exists but is vague (no clear owner, date or amount)."
        ev_res += [_ev(vague_close[0], VAGUE)]
    elif summary or (
        third_party_closed and any(NAME_TERMINATION_OK.search(x.text) for x in agent_turns)
    ):
        res = 4
        res_rat = "Specific, scenario-appropriate next step communicated and confirmed."
    else:
        res = 3 if rubric_rules.get("resolution_requires_summary_for_4", True) else 4
        res_rat = "Specific next step, but not summarised back to the contact."
    res_status = "sufficient" if ev_res else "missing"

    # ---- gates ----------------------------------------------------------------------
    gates = []
    for gid, s in screens.items():
        assessment = "VIOLATION" if s.flag else ("UNCERTAIN" if s.flag is None else "NO_VIOLATION")
        gates.append(
            {
                "gate_id": gid,
                "assessment": assessment,
                "rationale": f"Lexical screen: {s.reason}.",
                "evidence": [
                    {"turn_id": tid, "quote": q[:600], "evidence_type": "direct"}
                    for tid, q in s.evidence
                ],
            }
        )
    if sig.injection_turns:
        notes.append(
            f"Contact turn(s) {', '.join(sig.injection_turns)} contain instructions addressed to the evaluator; treated as transcript content and ignored."
        )
    if gate_uncertain:
        notes.append("At least one gate could not be determined lexically.")
    if gate_violation:
        notes.append("At least one gate violation is alleged; requires human confirmation.")

    def dim(
        name: str, app: bool, score: int | None, rat: str, ev: list[dict[str, str]], status: str
    ) -> dict[str, Any]:
        return {
            "dimension": name,
            "applicable": app,
            "score": score if app else None,
            "rationale": rat,
            "evidence": ev if app else [],
            "evidence_status": status,
        }

    return {
        "transcript_id": t.transcript_id,
        "dimensions": [
            dim("intent_capture", True, intent, intent_rat, ev_intent[:6], intent_status),
            dim("objection_handling", obj_app, obj, obj_rat, ev_obj[:6], obj_status),
            dim(
                "compliance_adherence",
                True,
                comp,
                comp_rat,
                ev_comp[:6],
                "sufficient" if ev_comp or comp == 4 else "missing",
            ),
            dim("fallback_grace", fb_app, fb, fb_rat, ev_fb[:6], fb_status),
            dim("resolution_quality", True, res, res_rat, ev_res[:6], res_status),
        ],
        "critical_gates": gates,
        "claimed_overall_score": None,
        "claimed_decision": None,
        "uncertainty_notes": notes,
        "injection_attempt_detected": bool(sig.injection_turns),
    }


def heuristic_judge_json(t: Transcript, rubric_rules: dict[str, Any]) -> str:
    return json.dumps(heuristic_judge_output(t, rubric_rules), ensure_ascii=False)
