"""ORM models. Importing this package registers all tables on the metadata."""
from app.models.activity_log import ActivityLog
from app.models.candidate import Candidate
from app.models.candidate_score import CandidateScore
from app.models.embedding import Embedding
from app.models.job import Job
from app.models.notification import Notification
from app.models.refresh_token import RefreshToken
from app.models.report import Report
from app.models.resume import Resume
from app.models.skill import CandidateSkill, Skill
from app.models.user import User

__all__ = [
    "ActivityLog",
    "Candidate",
    "CandidateScore",
    "Embedding",
    "Job",
    "Notification",
    "RefreshToken",
    "Report",
    "Resume",
    "Skill",
    "CandidateSkill",
    "User",
]
