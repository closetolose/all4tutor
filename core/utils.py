import requests
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode

from .models import Notification


def notify_user(user, message, link=None, notification_type='info', send_telegram=False):
    """
    Создать in-app уведомление для пользователя.
    user — экземпляр User (AUTH_USER_MODEL).
    link — строка или None (сохраняется как '' в БД).
    notification_type — 'info' или 'warning' (Notification.TYPE_CHOICES).
    send_telegram — при True отправить дубликат в Telegram, если у user есть profile.telegram_id.
    """
    Notification.objects.create(
        user=user,
        message=message[:255],
        link=link or '',
        type=notification_type,
    )
    if send_telegram:
        profile = getattr(user, 'profile', None)
        if profile and getattr(profile, 'telegram_id', None):
            send_telegram_notification(profile, message)


def send_telegram_notification(user_profile, message):
    if not user_profile.telegram_id:
        return False

    token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    data = {
        "chat_id": user_profile.telegram_id,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, data=data)
        return response.ok
    except Exception:
        return False


def send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    domain = get_current_site(request).domain

    subject = "Активация аккаунта All4Tutors 🚀"

    html_content = render_to_string('core/email_verification.html', {
        'user': user,
        'domain': domain,
        'uid': uid,
        'token': token,
    })

    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=f"All4Tutors <{settings.EMAIL_HOST_USER}>",
        to=[user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()
