import re

import pytz
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import logout


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            tzname = request.user.profile.timezone
            if tzname:
                timezone.activate(tzname)
            else:
                timezone.deactivate()
        return self.get_response(request)


class MobileDiscoveryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        mobile_re = re.compile(
            r".*(iphone|android|mobile|up.browser|up.link|mmp|symbian|"
            r"smartphone|midp|wap|phone|iemobile|kindle|silk).*",
            re.IGNORECASE,
        )
        request.is_mobile = bool(mobile_re.match(user_agent))
        return self.get_response(request)


class ProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            allowed_urls = [
                reverse('edit_profile'),
                reverse('logout'),
            ]

            if not hasattr(request.user, 'profile') or not request.user.profile.first_name:
                if request.path not in allowed_urls and not request.path.startswith('/admin/'):
                    return redirect('edit_profile')

        response = self.get_response(request)
        return response


class SessionCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # ПРОВЕРКА: Если у пользователя нет профиля (как у твоего админа)
            # или если это суперпользователь, которого мы не хотим ограничивать
            if not hasattr(request.user, 'profile') or request.user.is_superuser:
                return self.get_response(request)

            user_session_key = request.session.get('user_session_key')
            # Теперь эта строка не упадет, так как мы проверили наличие профиля выше
            actual_key = str(request.user.profile.session_key)

            if not user_session_key:
                request.session['user_session_key'] = actual_key
            elif user_session_key != actual_key:
                logout(request)
                return redirect('login')

        return self.get_response(request)
