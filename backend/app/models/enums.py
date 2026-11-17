from enum import StrEnum


class Period(StrEnum):
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(StrEnum):
    HOME = "home"
    OFFICE = "office"
    SELF = "self"
    MISC = "misc"


class EntryKind(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"


class EntryStatus(StrEnum):
    PLANNED = "planned"
    PAID = "paid"
