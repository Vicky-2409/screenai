from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import EmploymentType, JobStatus


class JobBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    department: str | None = None
    location: str | None = None
    experience: str | None = None
    min_experience_years: float = 0
    salary: str | None = None
    employment_type: EmploymentType = EmploymentType.full_time
    description: str | None = None
    responsibilities: str | None = None
    qualifications: str | None = None
    skills: list[str] = Field(default_factory=list)


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: str | None = None
    department: str | None = None
    location: str | None = None
    experience: str | None = None
    min_experience_years: float | None = None
    salary: str | None = None
    employment_type: EmploymentType | None = None
    status: JobStatus | None = None
    description: str | None = None
    responsibilities: str | None = None
    qualifications: str | None = None
    skills: list[str] | None = None


class JobOut(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    status: JobStatus
    created_at: datetime
    updated_at: datetime


class JobWithStats(JobOut):
    resume_count: int = 0
    scored_count: int = 0
    average_score: float = 0
