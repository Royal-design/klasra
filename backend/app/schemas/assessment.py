import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.normalizers import normalize_enum_str, normalize_required_text

AssessmentType = Literal["quiz", "test", "exam"]
AssessmentStatus = Literal["draft", "published", "closed"]
QuestionType = Literal["single_choice", "true_false", "multi_select", "short_answer"]


class QuestionOptionInput(BaseModel):
    key: str = Field(min_length=1, max_length=20)
    label: str = Field(min_length=1, max_length=500)

    @field_validator("key")
    @classmethod
    def clean_key(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("label")
    @classmethod
    def clean_label(cls, value: str) -> str:
        return normalize_required_text(value)


class AssessmentQuestionCreateRequest(BaseModel):
    question_type: QuestionType
    prompt: str = Field(min_length=2, max_length=5000)
    options: list[QuestionOptionInput] | None = None
    correct_answers: list[str] | None = None
    points: float = Field(default=1.0, gt=0, le=1000)
    display_order: int = Field(default=0, ge=0, le=1000)

    @field_validator("question_type", mode="before")
    @classmethod
    def clean_type(cls, value: object) -> object:
        return normalize_enum_str(value)

    @model_validator(mode="after")
    def validate_question_structure(self) -> "AssessmentQuestionCreateRequest":
        if self.question_type == "short_answer":
            self.options = None
            self.correct_answers = None
            return self

        if not self.options or len(self.options) < 2:
            raise ValueError("Objective questions require at least 2 options.")
        option_keys = {opt.key for opt in self.options}
        if len(option_keys) != len(self.options):
            raise ValueError("Option keys must be unique.")
        if not self.correct_answers or len(self.correct_answers) == 0:
            raise ValueError("Objective questions require at least one correct answer key.")

        normalized_correct = [c.strip().upper() for c in self.correct_answers if c.strip()]
        if self.question_type in {"single_choice", "true_false"} and len(normalized_correct) != 1:
            raise ValueError(
                f"{self.question_type} questions must have exactly 1 correct answer key."
            )
        if not set(normalized_correct).issubset(option_keys):
            raise ValueError("All correct_answers must match defined option keys.")
        self.correct_answers = sorted(set(normalized_correct))
        return self


class AssessmentCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    instructions: str | None = Field(default=None, max_length=20000)
    assessment_type: AssessmentType = "quiz"
    status: AssessmentStatus = "draft"
    available_from: datetime | None = None
    available_until: datetime | None = None
    time_limit_minutes: int | None = Field(default=None, ge=1, le=600)
    max_attempts: int = Field(default=1, ge=1, le=20)
    shuffle_questions: bool = False
    shuffle_options: bool = False
    show_results_immediately: bool = False

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        return normalize_required_text(value)

    @field_validator("assessment_type", "status", mode="before")
    @classmethod
    def clean_enums(cls, value: object) -> object:
        return normalize_enum_str(value)

    @model_validator(mode="after")
    def validate_window(self) -> "AssessmentCreateRequest":
        if (
            self.available_from is not None
            and self.available_until is not None
            and self.available_until <= self.available_from
        ):
            raise ValueError("available_until must be after available_from.")
        return self


class AssessmentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    instructions: str | None = Field(default=None, max_length=20000)
    assessment_type: AssessmentType | None = None
    status: AssessmentStatus | None = None
    available_from: datetime | None = None
    available_until: datetime | None = None
    time_limit_minutes: int | None = Field(default=None, ge=1, le=600)
    max_attempts: int | None = Field(default=None, ge=1, le=20)
    shuffle_questions: bool | None = None
    shuffle_options: bool | None = None
    show_results_immediately: bool | None = None

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str | None) -> str | None:
        return normalize_required_text(value) if value is not None else None

    @field_validator("assessment_type", "status", mode="before")
    @classmethod
    def clean_enums(cls, value: object) -> object:
        return normalize_enum_str(value)


class AssessmentQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_type: str
    prompt: str
    options: list[dict[str, str]] | None = None
    # Hidden (None) for students unless results are published
    correct_answers: list[str] | None = None
    points: float
    display_order: int


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    subject_offering_id: uuid.UUID
    created_by_user_id: uuid.UUID | None
    author_full_name: str | None = None
    title: str
    instructions: str | None
    assessment_type: str
    status: str
    available_from: datetime | None
    available_until: datetime | None
    time_limit_minutes: int | None
    max_attempts: int
    shuffle_questions: bool
    shuffle_options: bool
    show_results_immediately: bool
    total_points: float
    question_count: int = 0
    questions: list[AssessmentQuestionResponse] = []
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AttemptAnswerInput(BaseModel):
    question_id: uuid.UUID
    selected_options: list[str] | None = None
    text_answer: str | None = Field(default=None, max_length=20000)


class SubmitAttemptRequest(BaseModel):
    answers: list[AttemptAnswerInput] = Field(default_factory=list)


class GradeAnswerInput(BaseModel):
    question_id: uuid.UUID
    points_awarded: float = Field(ge=0)
    feedback: str | None = Field(default=None, max_length=2000)


class GradeAttemptRequest(BaseModel):
    answer_grades: list[GradeAnswerInput] = Field(default_factory=list)
    teacher_feedback: str | None = Field(default=None, max_length=5000)
    is_published: bool = True


class AssessmentAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    selected_options: list[str] | None
    text_answer: str | None
    is_correct: bool | None
    points_awarded: float
    feedback: str | None


class AssessmentAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    school_name: str | None = None
    assessment_id: uuid.UUID
    assessment_title: str | None = None
    assessment_type: str | None = None
    subject_name: str | None = None
    subject_code: str | None = None
    student_user_id: uuid.UUID
    student_full_name: str | None = None
    attempt_number: int
    status: str
    started_at: datetime
    deadline_at: datetime | None
    submitted_at: datetime | None
    auto_score: float | None
    manual_score: float | None
    total_score: float | None
    max_score: float
    teacher_feedback: str | None
    is_published: bool
    published_at: datetime | None
    answers: list[AssessmentAnswerResponse] = []
    created_at: datetime
    updated_at: datetime
