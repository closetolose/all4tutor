from django.utils import timezone
from .models import Lessons


def next_lesson_processor(request):
    if request.user.is_authenticated:
        try:
            next_lesson = Lessons.objects.filter(
                tutor=request.user.profile,
                start_time__gt=timezone.now()
            ).order_by('start_time').first()
            return {'next_lesson': next_lesson}
        except:
            return {'next_lesson': None}
    return {'next_lesson': None}