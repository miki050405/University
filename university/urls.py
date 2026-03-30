from django.urls import path

from .views import (
    authorization_view,
    logout_view,
    role_redirect_view,
    student_dashboard,
    student_subjects,
    student_grades,
)
from .chair_views import (
    chair_dashboard,
    create_lecture,
    lecture_list,
    edit_lecture,
    delete_lecture,
    subject_list,
    create_subject,
    edit_subject,
    delete_subject,
    stream_list,
    create_stream,
    edit_stream,
    delete_stream,
    chair_groups,
    chair_group_students,
)
from .student_registration_views import (
    student_registration_list,
    registration_step,
    register_stream,
    cancel_registration,
)

from .teacher_views import (
    teacher_dashboard,
    teacher_journal_list,
    teacher_journal_streams,
    teacher_gradebook,
)


urlpatterns = [
    path("", authorization_view, name="authorization"),
    path("logout/", logout_view, name="logout"),
    path("redirect/", role_redirect_view, name="role_redirect"),

    path("student/", student_dashboard, name="student_dashboard"),
    path("student/subjects/", student_subjects, name="student_subjects"),
    
    path("teacher/", teacher_dashboard, name="teacher_dashboard"),

    path("chair/", chair_dashboard, name="chair_dashboard"),
    path("chair/lectures/", lecture_list, name="lecture_list"),
    path("chair/lectures/create/", create_lecture, name="create_lecture"),
    path("chair/lectures/<int:lecture_id>/edit/", edit_lecture, name="edit_lecture"),
    path("chair/lectures/<int:lecture_id>/delete/", delete_lecture, name="delete_lecture"),
    path("chair/subjects/", subject_list, name="subject_list"),
    path("chair/subjects/create/", create_subject, name="create_subject"),
    path("chair/subjects/<int:subject_id>/edit/", edit_subject, name="edit_subject"),
    path("chair/subjects/<int:subject_id>/delete/", delete_subject, name="delete_subject"),
    path("chair/streams/", stream_list, name="stream_list"),
    path("chair/streams/create/", create_stream, name="create_stream"),
    path("chair/streams/<int:stream_id>/edit/", edit_stream, name="edit_stream"),
    path("chair/streams/<int:stream_id>/delete/", delete_stream, name="delete_stream"),
    path("chair/groups/", chair_groups, name="chair_groups"),
    path("chair/groups/<int:group_id>/", chair_group_students, name="chair_group_students"),

    path("student/registration/", student_registration_list, name="student_registration_list"),
    path(
        "student/registration/<int:subject_id>/<str:lecture_type>/",
        registration_step,
        name="registration_step"
    ),
    path("student/registration/register/<int:stream_id>/", register_stream, name="register_stream"),
    path("student/registration/cancel/<int:enrollment_id>/", cancel_registration, name="cancel_registration"),
    path("student/grades/", student_grades, name="student_grades"),

    path("teacher/", teacher_dashboard, name="teacher_dashboard"),
    path("teacher/journal/", teacher_journal_list, name="teacher_journal_list"),
    path("teacher/journal/<int:lecture_id>/streams/", teacher_journal_streams, name="teacher_journal_streams"),
    path("teacher/journal/stream/<int:stream_id>/", teacher_gradebook, name="teacher_gradebook"),
]