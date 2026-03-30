from django.contrib import admin
from django.contrib import messages
from django import forms
from django.contrib.auth.models import User
from .models import (
    Nationality,
    Region,
    StudyForm,
    Faculty,
    Chair,
    Specialty,
    Group,
    UserProfile,
    Student,
    TeacherPosition,
    Teacher,
    Subject,
    Term,
    Lecture,
    Stream,
    Enrollment,
    ProgressInStudy,
    GradeControl,
    Schedule,
    TimeSlot,
)


admin.site.register(Nationality)
admin.site.register(Region)
admin.site.register(StudyForm)
admin.site.register(Faculty)
@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "faculty", "chair")
    list_filter = ("faculty", "chair")
    search_fields = ("name", "faculty__name", "chair__name")
admin.site.register(Group)
admin.site.register(UserProfile)
class StudentAdminForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        used_user_ids = Student.objects.exclude(pk=self.instance.pk).values_list("user_id", flat=True)

        self.fields["user"].queryset = User.objects.filter(
            userprofile__role="student"
        ).exclude(
            id__in=used_user_ids
        )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentAdminForm
    list_display = ("id", "user", "group", "course", "study_form")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    list_filter = ("course", "study_form", "group")

admin.site.register(TeacherPosition)
class TeacherAdminForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        used_user_ids = Teacher.objects.exclude(pk=self.instance.pk).values_list("user_id", flat=True)

        self.fields["user"].queryset = User.objects.filter(
            userprofile__role="teacher"
        ).exclude(
            id__in=used_user_ids
        )


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    form = TeacherAdminForm
    list_display = ("id", "user", "faculty", "position", "phone")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    list_filter = ("faculty", "position")

admin.site.register(Subject)
admin.site.register(Term)
admin.site.register(Lecture)

@admin.action(description="Закрыть регистрацию для выбранных потоков")
def close_stream_registration(modeladmin, request, queryset):
    updated = queryset.update(status="closed")
    modeladmin.message_user(
        request,
        f"Закрыта регистрация для {updated} потоков.",
        messages.SUCCESS
    )


@admin.action(description="Открыть регистрацию для выбранных потоков")
def open_stream_registration(modeladmin, request, queryset):
    count = 0
    for stream in queryset:
        stream.status = "open"
        stream.save(update_fields=["status"])
        stream.refresh_status()
        count += 1

    modeladmin.message_user(
        request,
        f"Регистрация открыта для {count} потоков.",
        messages.SUCCESS
    )

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ("id", "lecture", "subgroup", "max_budget", "max_contract", "status")
    list_filter = ("status", "subgroup", "lecture__subject__chair", "lecture__term")
    search_fields = ("lecture__subject__name",)
    actions = [close_stream_registration, open_stream_registration]

admin.site.register(Enrollment)
admin.site.register(ProgressInStudy)
admin.site.register(GradeControl)
admin.site.register(Schedule)
admin.site.register(TimeSlot)
@admin.register(Chair)
class ChairAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "faculty")
    list_filter = ("faculty",)
    search_fields = ("name", "faculty__name")

