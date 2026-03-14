from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.db import transaction

from .models import (
    Users, Subjects, StudyGroups, Lessons, StudentBalance, Transaction,
    TutorSubjects, ConnectionRequest, UnlinkRequest, UserGroupColor, FileTag, FilesLibrary,
    PaymentReceipt, TestResult, Notification, ChatMessage, BotChatMessage,
)


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
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
    list_filter = ('format', 'is_paid', 'subject')

@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
    list_display = ('tutor', 'student', 'status', 'color_hex', 'tutor_color_hex', 'created_at')
    list_filter = ('status',)


@admin.register(UnlinkRequest)
class UnlinkRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'tutor', 'status', 'reason_short', 'created_at', 'reviewed_at', 'reviewed_by')
    list_filter = ('status',)
    search_fields = ('student__first_name', 'student__last_name', 'tutor__first_name', 'tutor__last_name')
    actions = ['approve_unlink', 'reject_unlink']
    list_per_page = 25

    @admin.display(description='Причина')
    def reason_short(self, obj):
        return (obj.reason[:50] + '…') if obj.reason and len(obj.reason) > 50 else (obj.reason or '—')

    @admin.action(description='Одобрить заявки на открепление')
    def approve_unlink(self, request, queryset):
        pending = list(queryset.filter(status='pending'))
        archived = 0
        with transaction.atomic():
            for req in pending:
                req.status = 'approved'
                req.reviewed_at = timezone.now()
                req.reviewed_by = request.user
                req.save()
                conn = ConnectionRequest.objects.filter(
                    student=req.student, tutor=req.tutor, status='confirmed'
                ).first()
                if conn:
                    conn.status = 'archived'
                    conn.save()
                    archived += 1
        self.message_user(request, 'Одобрено заявок: %d; связей переведено в архив: %d.' % (len(pending), archived))

    @admin.action(description='Отклонить заявки на открепление')
    def reject_unlink(self, request, queryset):
        pending = list(queryset.filter(status='pending'))
        for req in pending:
            req.status = 'rejected'
            req.reviewed_at = timezone.now()
            req.reviewed_by = request.user
            req.save()
        self.message_user(request, 'Отклонено заявок: %d.' % len(pending))


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
    list_display = ('student', 'tutor', 'subject', 'score', 'max_score', 'date', 'comment')
    list_filter = ('tutor', 'subject', 'date')
    search_fields = ('student__first_name', 'student__last_name')


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


@admin.register(BotChatMessage)
class BotChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'content_preview', 'created_at')
    list_filter = ('role',)
    search_fields = ('content', 'user__username')

    def content_preview(self, obj):
        return (obj.content[:50] + '...') if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Текст'


admin.site.register(Subjects)
admin.site.register(StudyGroups)
admin.site.register(StudentBalance)
admin.site.register(Transaction)
admin.site.register(TutorSubjects)

# Скрыть стандартные модели User и Group в /admin/ (кастомная панель — /dashboard/admin/)
admin.site.unregister(User)
admin.site.unregister(Group)