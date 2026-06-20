import re


PHONE_PATTERN = re.compile(r"(01[016789])[-.\s]?(\d{3,4})[-.\s]?(\d{4})")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def mask_sensitive_info(text: str) -> str:
    masked = PHONE_PATTERN.sub(r"\1-****-\3", text)
    masked = EMAIL_PATTERN.sub("[이메일 마스킹]", masked)
    return masked

