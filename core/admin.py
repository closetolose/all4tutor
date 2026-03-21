from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.db import transaction

from .models import (
    Profile, Subjects, StudyGroups, Lessons, Transaction,
    ConnectionRequest, UserGroupColor, FileTag, FilesLibrary,
    PaymentReceipt, TestResult, Notification, ChatMessage,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'role', 'contact', '_is_active')
    list_filter = ('role',)
    search_fields = ('last_name', 'first_name', 'contact')
    list_editable = ('role',)
    actions = ['block_users', 'unblock_users']

    @admin.display(boolean=True, description='Активен')
    def _is_active(self, obj):
        return obj.user.is_active if obj.user_id else False

    @admin.action(description='Заблокировать выбранных')
    def block_users(self, request, queryset):
        updated = 0
        for profile in queryset:
            if profile.user_id and profile.user.is_active:
                profile.user.is_active = False
                profile.user.save(update_fields=['is_active'])
                updated += 1
        self.message_user(request, 'Заблокировано пользователей: %d.' % updated)

    @admin.action(description='Разблокировать выбранных')
    def unblock_users(self, request, queryset):
        updated = 0
        for profile in queryset:
            if profile.user_id and not profile.user.is_active:
                profile.user.is_active = True
                profile.user.save(update_fields=['is_active'])
                updated += 1
        self.message_user(request, 'Разблокировано пользователей: %d.' % updated)

@admin.register(Lessons)
class LessonsAdmin(admin.ModelAdmin):
    list_display = ('tutor', 'subject', 'start_time', 'format', 'is_paid')
    list_filter = ('format', 'subject')

@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
    list_display = ('tutor', 'student', 'status', 'color_hex', 'tutor_color_hex', 'created_at')
    list_filter = ('status',)


@admin.register(UserGroupColor)
class UserGroupColorAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'color_hex')

@admin.register(FileTag)
class FileTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'tutor')
    list_filter = ('tutor',)


@admin.register(FilesLibrary)
class FilesLibraryAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'tutor', 'upload_date')
    list_filter = ('tutor',)
    filter_horizontal = ('tags',)


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = ('student', 'tutor', 'amount', 'receipt_date', 'status', 'created_at', 'reviewed_at')
    list_filter = ('status', 'tutor')


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'get_tutor', 'subject', 'score', 'max_score', 'date', 'comment')
    list_filter = ('subject__tutor', 'subject', 'date')
    search_fields = ('student__first_name', 'student__last_name')

    @admin.display(description='Репетитор')
    def get_tutor(self, obj):
        return obj.subject.tutor if obj.subject_id else '—'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')
    search_fields = ('user__username', 'message')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('connection', 'sender', 'text_preview', 'file_name', 'is_read', 'created_at')
    list_filter = ('connection', 'is_read')
    search_fields = ('text', 'sender__first_name', 'sender__last_name')
    readonly_fields = ('connection', 'sender', 'text', 'created_at')

    def text_preview(self, obj):
        return (obj.text[:50] + '...') if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Текст'


admin.site.register(Subjects)
admin.site.register(StudyGroups)
admin.site.register(Transaction)

# Скрыть стандартные модели User и Group в /admin/ (кастомная панель — /dashboard/admin/)
admin.site.unregister(User)
admin.site.unregister(Group)