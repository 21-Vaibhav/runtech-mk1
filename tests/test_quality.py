from app.ingestion.quality import assess_stream_quality


def test_quality_flags_missing_streams():
    result = assess_stream_quality({"time": {"data": [0, 1, 2]}})
    assert result.score < 1.0
    assert result.flags["missing_streams"] is True
