import requests
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

def send_telegram_notification(user_profile, message):
    """
    Отправляет сообщение пользователю, если у него привязан Telegram
    """
    if not user_profile.telegram_id:
        return False  # Уведомление не отправлено, нет ID

    token = "8505922369:AAHAv595sVcvPL5dRwuOcBhP_R_kW2jFgJk"
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    data = {
        "chat_id": user_profile.telegram_id,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, data=data)
        return response.ok
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False


def send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    domain = get_current_site(request).domain

    subject = "Активация аккаунта All4Tutors 🚀"

    # 1. Генерируем HTML контент из шаблона
    html_content = render_to_string('core/email_verification.html', {
        'user': user,
        'domain': domain,
        'uid': uid,
        'token': token,
    })

    # 2. Создаем текстовую версию (на случай, если HTML не поддерживается)
    text_content = strip_tags(html_content)

    # 3. Собираем письмо
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=f"All4Tutors <{settings.EMAIL_HOST_USER}>",
        to=[user.email]
    )

    # Прикрепляем HTML версию
    email.attach_alternative(html_content, "text/html")

    # 4. Погнали!
    email.send()