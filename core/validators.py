from django.core.exceptions import ValidationError

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def validate_file_size(value):
    if value.size > MAX_FILE_SIZE:
        raise ValidationError("Максимальный размер файла — 10 МБ.")


def validate_receipt_file(value):
    if value.size > MAX_FILE_SIZE:
        raise ValidationError("Максимальный размер файла — 10 МБ.")
    ext = (value.name or '').lower().split('.')[-1]
    if ext not in ('pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp'):
        raise ValidationError("Допустимы только изображения (jpg, png, gif, webp) или PDF.")


CHAT_FILE_EXTS = (
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp',  # изображения
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'rtf', 'odt', 'ods',  # документы
)


def validate_chat_file(value):
    if value.size > MAX_FILE_SIZE:
        raise ValidationError("Максимальный размер файла — 10 МБ.")
    ext = (value.name or '').lower().split('.')[-1]
    if ext not in CHAT_FILE_EXTS:
        raise ValidationError(
            "Допустимы изображения (jpg, png, gif, webp) и документы (pdf, doc, docx, xls, xlsx, txt)."
        )