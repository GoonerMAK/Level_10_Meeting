from dataclasses import dataclass
from http import HTTPStatus

FIELD_MESSAGES = {
    "title": "Title is required, up to 200 characters",
    "priority": "Priority must be 1 to 5",
    "resolution_note": "A note is required to solve an Issue, up to 2,000 characters",
    "value": "Score must be a number up to 11 digits, with up to 4 decimal places",
    "week_start": "Week must be a date, like 2026-11-02",
    "rating": "Rating must be 1 to 10",
    "owner_id": "Choose an owner",
    "user_id": "Choose a user to sign in as",
    "status": "Status must be open or solved",
}


@dataclass(frozen=True)
class DataRule:
    status: HTTPStatus
    message: str
    field: str | None = None


def bad_value(message: str, field: str | None = None) -> DataRule:
    return DataRule(HTTPStatus.UNPROCESSABLE_CONTENT, message, field)


def clash(message: str) -> DataRule:
    return DataRule(HTTPStatus.CONFLICT, message)


NAME_REQUIRED = bad_value("Name is required", "name")
TITLE_REQUIRED = bad_value(FIELD_MESSAGES["title"], "title")
WEEK_IS_MONDAY = bad_value("A week must start on a Monday", "week_start")

DATA_RULES = {
    "ck_companies_name_not_blank": NAME_REQUIRED,
    "ck_teams_name_not_blank": NAME_REQUIRED,
    "ck_users_name_not_blank": NAME_REQUIRED,
    "ck_measurables_name_not_blank": NAME_REQUIRED,
    "ck_users_email_format": bad_value("Email must be lowercase and contain @", "email"),
    "uq_users_email": clash("This email is already in use"),
    "ck_measurables_goal_shape": bad_value("A goal needs one value, or a min no bigger than its max for 'between'"),
    "ck_rocks_quarter_format": bad_value("Quarter must look like 2026-Q4", "quarter"),
    "ck_rocks_title_not_blank": TITLE_REQUIRED,
    "ck_milestones_title_not_blank": TITLE_REQUIRED,
    "ck_issues_title_not_blank": TITLE_REQUIRED,
    "ck_todos_title_not_blank": TITLE_REQUIRED,
    "ck_issues_priority_range": bad_value(FIELD_MESSAGES["priority"], "priority"),
    "ck_issues_solved_requires_note": bad_value("A solved Issue needs a note, and an open one has none", "resolution_note"),
    "ck_issues_solved_after_created": bad_value("An Issue can't be solved before it was created"),
    "ck_issues_source_complete": bad_value("An Issue's source needs both a Measurable and a week"),
    "ck_issues_source_week_is_monday": WEEK_IS_MONDAY,
    "ck_scores_week_start_is_monday": WEEK_IS_MONDAY,
    "uq_issues_open_source": clash("This score already has an unsolved Issue"),
    "ck_meetings_ended_after_started": bad_value("A meeting can't end before it starts"),
    "ck_meetings_active_has_section": clash("A running meeting must be in a section, and an ended one in none"),
    "uq_meetings_one_active_per_team": clash("This team already has a meeting running"),
    "ck_meeting_ratings_rating_range": bad_value(FIELD_MESSAGES["rating"], "rating"),
    "fk_meeting_ratings_attendee": clash("Only people attending the meeting can rate it"),
    "fk_todos_owner_id_users": bad_value("Owner must be a Team Member of this team or an Admin", "owner_id"),
    "fk_todos_source_issue_id_issues": bad_value("Issue not found", "source_issue_id"),
    "fk_issues_owner_id_users": bad_value("Owner not found", "owner_id"),
    "fk_scores_measurable_id_measurables": bad_value("Measurable not found", "measurable_id"),
    "ck_activity_logs_changes_is_array": bad_value("An activity entry must list its changes", "changes"),
    "ck_activity_logs_entity_label_not_blank": bad_value("An activity entry needs a label", "entity_label"),
}

UNKNOWN_LINK = bad_value("Something this change points to doesn't exist")
UNKNOWN_RULE = clash("This change breaks a data rule")
