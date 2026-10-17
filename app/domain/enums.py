from enum import StrEnum


class DocType(StrEnum):
    INVOICE = "invoice"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    BANK = "bank"
    LAW = "law"


class Category(StrEnum):
    SOFTWARE = "software"
    HOSTING = "hosting"
    OFFICE = "office"
    TRAVEL = "travel"
    UTILITIES = "utilities"
    PRIVATE = "private"
    OTHER = "other"