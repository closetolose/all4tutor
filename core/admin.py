from django.contrib import admin
from .models import Users,  Subjects, StudyGroups, Lessons, StudentBalances, Transaction, TutorSubjects,ConnectionRequest


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'role', 'contact')
    list_filter = ('role',)
    search_fields = ('last_name', 'contact')

@admin.register(Lessons)
class LessonsAdmin(admin.ModelAdmin):
    list_display = ('tutor', 'subject', 'start_time', 'format', 'is_paid')
    list_filter = ('format', 'is_paid', 'subject')

@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
    # Эти колонки будут видны в списке всех заявок
    list_display = ('tutor', 'student', 'status', 'created_at')
    # Можно будет фильтровать по статусу
    list_filter = ('status',)

admin.site.register(Subjects)
admin.site.register(StudyGroups)
admin.site.register(StudentBalances)
admin.site.register(Transaction)
admin.site.register(TutorSubjects)