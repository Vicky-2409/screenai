from app.services.ai.local_provider import LocalProvider


def test_local_analysis_recommendation_thresholds():
    provider = LocalProvider()
    high = provider.analyze_candidate(
        "job", "resume",
        {"overall_score": 85, "matching_skills": ["python"], "missing_skills": [],
         "total_experience_years": 6, "min_experience_years": 5, "name": "Jane"},
    )
    assert "recommend" in high.recommendation.lower()
    assert high.strengths
    assert len(high.interview_questions) >= 3

    low = provider.analyze_candidate(
        "job", "resume",
        {"overall_score": 30, "matching_skills": [], "missing_skills": ["python", "aws"],
         "total_experience_years": 1, "min_experience_years": 5, "name": "Bob"},
    )
    assert "not recommended" in low.recommendation.lower()
    assert low.weaknesses
