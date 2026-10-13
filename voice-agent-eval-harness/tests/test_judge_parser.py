import pytest

from voice_eval.judge.response_parser import MalformedJudgeResponse, parse_judge_response


def test_parses_clean_json(tiny_transcript, rubric_v1, judge_output_factory):
    import json

    raw = json.dumps(judge_output_factory("BFSI-A-001"))
    out = parse_judge_response(raw, tiny_transcript, rubric_v1)
    assert out.transcript_id == "BFSI-A-001"


def test_extracts_from_code_fence(tiny_transcript, rubric_v1, judge_output_factory):
    import json

    raw = (
        "Here is the result:\n```json\n" + json.dumps(judge_output_factory("BFSI-A-001")) + "\n```"
    )
    assert parse_judge_response(raw, tiny_transcript, rubric_v1).transcript_id == "BFSI-A-001"


def test_empty_raises(tiny_transcript, rubric_v1):
    with pytest.raises(MalformedJudgeResponse):
        parse_judge_response("", tiny_transcript, rubric_v1)


def test_invalid_json_raises(tiny_transcript, rubric_v1):
    with pytest.raises(MalformedJudgeResponse):
        parse_judge_response("{not json", tiny_transcript, rubric_v1)


def test_out_of_range_score_raises(tiny_transcript, rubric_v1, judge_output_factory):
    import json

    data = judge_output_factory("BFSI-A-001")
    data["dimensions"][0]["score"] = 9
    with pytest.raises(MalformedJudgeResponse):
        parse_judge_response(json.dumps(data), tiny_transcript, rubric_v1)


def test_transcript_id_mismatch_raises(tiny_transcript, rubric_v1, judge_output_factory):
    import json

    with pytest.raises(MalformedJudgeResponse):
        parse_judge_response(
            json.dumps(judge_output_factory("BFSI-Z-999")), tiny_transcript, rubric_v1
        )


def test_always_applicable_na_rejected(tiny_transcript, rubric_v1, judge_output_factory):
    import json

    data = judge_output_factory(
        "BFSI-A-001",
        applicable={
            "intent_capture": False,
            "objection_handling": True,
            "compliance_adherence": True,
            "fallback_grace": True,
            "resolution_quality": True,
        },
    )
    with pytest.raises(MalformedJudgeResponse):
        parse_judge_response(json.dumps(data), tiny_transcript, rubric_v1)


def test_unicode_escaping_in_tool_input(tiny_transcript, rubric_v1, judge_output_factory):
    import json

    data = judge_output_factory("BFSI-A-001")
    data["dimensions"][0]["rationale"] = "slash \\/ and quote “test”"
    raw = json.dumps(data)
    assert parse_judge_response(raw, tiny_transcript, rubric_v1).dimensions[0].rationale
