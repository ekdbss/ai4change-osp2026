def validate_complaint(title: str, text: str) -> list[str]:
    errors = []

    if not title.strip():
        errors.append("제목을 입력해주세요.")
    if not text.strip():
        errors.append("민원 내용을 입력해주세요.")
    if len(text.strip()) < 10:
        errors.append("민원 내용은 최소 10자 이상 입력해주세요.")
    if len(text) > 2000:
        errors.append("민원 내용은 2000자 이하로 입력해주세요.")

    return errors

