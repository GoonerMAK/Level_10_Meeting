import enum


class UserRole(enum.StrEnum):
    ADMIN = "admin"
    TEAM_MEMBER = "team_member"
    OBSERVER = "observer"


class GoalType(enum.StrEnum):
    AT_LEAST = "at_least"
    AT_MOST = "at_most"
    BETWEEN = "between"
    EXACTLY = "exactly"


class RockStatus(enum.StrEnum):
    ON_TRACK = "on_track"
    OFF_TRACK = "off_track"
    COMPLETE = "complete"


class MeetingSection(enum.StrEnum):
    SCORECARD = "scorecard"
    IDS = "ids"
    CONCLUDE = "conclude"


class AuditEntity(enum.StrEnum):
    SCORE = "score"
    ISSUE = "issue"
    TODO = "todo"
    MEETING = "meeting"
    MEETING_RATING = "meeting_rating"


class AuditAction(enum.StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    SOLVED = "solved"
