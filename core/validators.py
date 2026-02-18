from django.core.exceptions import ValidationError

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def validate_file_size(value):
    if value.size > MAX_FILE_SIZE:
        raise ValidationError("Максимальный размер файла — 10 МБ.")