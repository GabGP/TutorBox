from pydantic import BaseModel, Field

CURRICULUM_TAXONOMY: dict[str, dict[str, list[str]]] = {
    "arithmetic": {
        "addition_subtraction": [
            "sign_error",
            "borrowing_error",
            "alignment_error",
            "added_instead_of_subtracted",
        ],
        "multiplication_division": [
            "table_lookup_error",
            "remainder_ignored",
            "inverted_division",
            "forgot_carry",
        ],
        "order_of_operations": [
            "left_to_right_precedence",
            "addition_before_multiplication",
            "ignored_parentheses",
        ],
    },
    "fractions": {
        "addition_subtraction": [
            "added_denominators",
            "ignored_common_denominator",
            "subtracted_denominators",
        ],
        "multiplication_division": [
            "cross_multiplied_for_product",
            "forgot_to_invert_divisor",
            "multiplied_only_numerators",
        ],
        "simplification": [
            "divided_only_numerator",
            "subtracted_to_reduce",
            "partial_factor_division",
        ],
    },
    "pre_algebra": {
        "one_step_equations": [
            "sign_flip_error",
            "wrong_inverse_operation",
            "applied_op_to_one_side_only",
        ],
        "two_step_equations": [
            "divided_before_subtracting",
            "forgot_division",
            "subtracted_instead_of_divided",
            "sign_inversion_error",
        ],
    },
    "decimals_percentages": {
        "decimal_operations": [
            "misplaced_decimal_point",
            "ignored_decimal_places",
            "added_without_aligning_decimal",
        ],
        "percentages": [
            "multiplied_by_percentage_directly",
            "confused_fraction_with_percent",
            "subtracted_percentage_as_raw_number",
        ],
    },
}


class SubconceptInfo(BaseModel):
    name: str
    misconceptions: list[str] = Field(default_factory=list)


class TopicInfo(BaseModel):
    name: str
    subconcepts: list[SubconceptInfo] = Field(default_factory=list)


def get_available_topics() -> list[TopicInfo]:
    result: list[TopicInfo] = []
    for topic_name, subconcepts in CURRICULUM_TAXONOMY.items():
        sub_list = [
            SubconceptInfo(name=sub_name, misconceptions=miscs)
            for sub_name, miscs in subconcepts.items()
        ]
        result.append(TopicInfo(name=topic_name, subconcepts=sub_list))
    return result


def is_valid_topic(topic: str) -> bool:
    return topic in CURRICULUM_TAXONOMY


def is_valid_subconcept(topic: str, subconcept: str) -> bool:
    return topic in CURRICULUM_TAXONOMY and subconcept in CURRICULUM_TAXONOMY[topic]
