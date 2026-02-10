import pytz
from django.utils import timezone
import re


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            tzname = request.user.profile.timezone
            if tzname:
                # ПРАВИЛЬНО: передаем просто название 'Europe/Moscow' или 'Asia/Krasnoyarsk'
                timezone.activate(tzname)
            else:
                timezone.deactivate()
        return self.get_response(request)


class MobileDiscoveryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Простая регулярка для поиска мобильных девайсов в User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Список признаков мобильного устройства
        mobile_re = re.compile(
            r".*(iphone|android|mobile|up.browser|up.link|mmp|symbian|smartphone|midp|wap|phone|iemobile|kindle|silk).*",
            re.IGNORECASE)

        request.is_mobile = bool(mobile_re.match(user_agent))

        return self.get_response(request)