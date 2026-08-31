from typing import Literal

from pydantic import BaseModel, Field, model_validator

OptionKey = Literal["A", "B", "C", "D"]
VALID_OPTIONS: set[str] = {"A", "B", "C", "D"}


class DistractorDetail(BaseModel):
    misconception: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Slug of the diagnosed misconception",
    )
    explanation: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Primary-school friendly explanation",
    )


class QuestionOptions(BaseModel):
    A: str = Field(..., min_length=1)
    B: str = Field(..., min_length=1)
    C: str = Field(..., min_length=1)
    D: str = Field(..., min_length=1)

    def as_dict(self) -> dict[str, str]:
        return {"A": self.A, "B": self.B, "C": self.C, "D": self.D}


class QuizQuestionBase(BaseModel):
    topic: str = Field(..., min_length=2, max_length=64)
    subconcept: str = Field(..., min_length=2, max_length=64)
    question_text: str = Field(..., min_length=5, max_length=500)
    options: dict[str, str]
    correct_option: OptionKey
    distractors: dict[str, DistractorDetail]

    @model_validator(mode="after")
    def validate_diagnostic_structure(self) -> "QuizQuestionBase":
        option_keys = set(self.options.keys())
        if option_keys != VALID_OPTIONS:
            raise ValueError(
                f"Options must contain exactly keys A, B, C, D; got {sorted(option_keys)}"
            )

        for option_key, option_text in self.options.items():
            if not str(option_text).strip():
                raise ValueError(f"Option {option_key} text cannot be empty")

        expected_distractors = VALID_OPTIONS - {self.correct_option}
        distractor_keys = set(self.distractors.keys())
        if distractor_keys != expected_distractors:
            raise ValueError(
                f"Distractors must match non-correct options {sorted(expected_distractors)}; "
                f"got {sorted(distractor_keys)}"
            )
        return self


class QuizQuestionCreate(QuizQuestionBase):
    id: str | None = None


class QuizQuestion(QuizQuestionBase):
    id: str = Field(..., min_length=1, max_length=64)


class QuizQuestionResponse(QuizQuestion):
    source: str = "llm"
    sympy_verified: bool = False
    created_at: str | None = None


class GenerateQuestionRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=64)
    subconcept: str | None = Field(default=None, max_length=64)
    save_to_bank: bool = False


class ValidateQuestionRequest(BaseModel):
    question: QuizQuestion


class MathValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    details: dict[str, str] = Field(default_factory=dict)


class QuestionListResponse(BaseModel):
    questions: list[QuizQuestionResponse]
    total: int


class QuizDeleteResponse(BaseModel):
    detail: str = "Question deleted."
