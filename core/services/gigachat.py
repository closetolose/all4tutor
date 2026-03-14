"""
Сервис для работы с GigaChat API.
Требует: pip install gigachat
Настройки: GIGACHAT_CREDENTIALS в .env (авторизационный ключ из личного кабинета GigaChat)
"""
import logging
import os

logger = logging.getLogger(__name__)

# Fallback: если env/.env пусты или не доходят — используется этот ключ.
_FALLBACK_CREDS = 'MDE5Y2VkMmEtN2I1Yy03NzFiLThlMDYtZDJiYTZiYmUxODkyOmVlOTNlYjM5LTQ2NmEtNDQxNi1iOWRmLTAyNjI5OTAyMGE1Yg=='


def _find_env_paths():
    """Все возможные пути к .env (Docker, локально, разные cwd)."""
    paths = []
    try:
        from django.conf import settings
        base = getattr(settings, 'BASE_DIR', None)
        if base:
            paths.append(os.path.join(str(base), '.env'))
    except Exception:
        pass
    # Путь от core/services/gigachat.py вверх к корню проекта
    this_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(this_file)))
    paths.append(os.path.join(project_root, '.env'))
    paths.append(os.path.join(os.getcwd(), '.env'))
    return paths


def _load_creds_from_env_file():
    """Читает GIGACHAT_CREDENTIALS напрямую из .env (fallback для Docker/Gunicorn)."""
    for env_path in _find_env_paths():
        try:
            if env_path and os.path.isfile(env_path):
                with open(env_path, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        line = line.strip().strip('\r')
                        if line.startswith('GIGACHAT_CREDENTIALS='):
                            val = line.split('=', 1)[1].strip().strip('"').strip("'")
                            if val:
                                return val
        except Exception as e:
            logger.debug("Could not read %s: %s", env_path, e)
    return None

SYSTEM_PROMPT = (
    "Ты — полезный AI-помощник платформы All4Tutors для репетиторов и учеников. "
    "Отвечай кратко и по делу. Помогай с вопросами об учёбе, подготовке к экзаменам, "
    "организации занятий и общими вопросами по платформе."
)


def get_giga_response(messages: list[dict], credentials: str = None) -> str:
    """
    Отправляет сообщения в GigaChat и возвращает ответ модели.
    messages: список {"role": "user"|"assistant"|"system", "content": "..."}
    credentials: ключ авторизации (если None — берётся из settings)
    """
    try:
        from gigachat import GigaChat
        from gigachat.models import Chat, Messages, MessagesRole
    except ImportError:
        logger.error("gigachat package not installed. Run: pip install gigachat")
        return "Ошибка: пакет gigachat не установлен. Обратитесь к администратору."

    from django.conf import settings
    def _non_empty(s):
        return (s and str(s).strip()) or None

    creds = (
        _non_empty(credentials)
        or _non_empty(getattr(settings, 'GIGACHAT_CREDENTIALS', None))
        or _non_empty(os.environ.get('GIGACHAT_CREDENTIALS'))
        or _non_empty(_load_creds_from_env_file())
        or _FALLBACK_CREDS
    )
    if not creds:
        logger.error("GIGACHAT_CREDENTIALS not configured")
        return "Ошибка: GigaChat не настроен. Обратитесь к администратору."

    # Формируем сообщения: system + история (последние 20) + новый запрос
    role_map = {"system": MessagesRole.SYSTEM, "user": MessagesRole.USER, "assistant": MessagesRole.ASSISTANT}
    api_messages = [Messages(role=MessagesRole.SYSTEM, content=SYSTEM_PROMPT)]
    for m in messages[-20:]:  # ограничиваем контекст
        role = role_map.get(m["role"], MessagesRole.USER)
        api_messages.append(Messages(role=role, content=m["content"][:8000]))

    try:
        with GigaChat(credentials=creds, verify_ssl_certs=False) as giga:
            response = giga.chat(Chat(model="GigaChat", messages=api_messages))
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            return "Не удалось получить ответ от модели."
    except Exception as e:
        logger.exception("GigaChat API error: %s", e)
        return f"Ошибка при обращении к нейросети: {str(e)}"
