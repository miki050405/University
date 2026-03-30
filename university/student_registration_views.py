from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Student, Stream, Enrollment


@login_required
def student_registration_list(request):
    if request.user.userprofile.role != "student":
        return redirect("role_redirect")

    student = get_object_or_404(Student, user=request.user)

    streams = Stream.objects.filter(
        group=student.group
    ).select_related(
        "lecture",
        "lecture__subject",
        "lecture__teacher__user",
        "lecture__term"
    ).prefetch_related("group").distinct()

    current_enrollments = Enrollment.objects.filter(
        student=student,
        status="registered"
    ).select_related(
        "stream",
        "stream__lecture",
        "stream__lecture__subject",
        "stream__lecture__teacher__user",
        "stream__lecture__term"
    ).prefetch_related("stream__group")

    enrollment_map = {
        (enrollment.stream.lecture.subject_id, enrollment.stream.lecture.type): enrollment
        for enrollment in current_enrollments
    }

    options = {}

    for stream in streams:
        key = (stream.lecture.subject_id, stream.lecture.type)

        if key not in options:
            options[key] = {
                "subject_id": stream.lecture.subject_id,
                "subject_name": stream.lecture.subject.name,
                "lecture_type": stream.lecture.type,
                "lecture_type_display": stream.lecture.get_type_display(),
                "credits": stream.lecture.credits,
                "is_elective": stream.lecture.is_elective,
                "enrollment": enrollment_map.get(key),
            }

    registration_options = sorted(
        options.values(),
        key=lambda item: (item["subject_name"].lower(), item["lecture_type_display"].lower())
    )

    return render(request, "student_registration_list.html", {
        "student": student,
        "registration_options": registration_options,
    })


@login_required
def registration_step(request, subject_id, lecture_type):
    if request.user.userprofile.role != "student":
        return redirect("role_redirect")

    student = get_object_or_404(Student, user=request.user)

    streams = Stream.objects.filter(
        group=student.group,
        lecture__subject_id=subject_id,
        lecture__type=lecture_type
    ).select_related(
        "lecture",
        "lecture__subject",
        "lecture__teacher__user",
        "lecture__term"
    ).prefetch_related("group").distinct()

    if not streams.exists():
        messages.error(request, "Подходящие потоки не найдены.")
        return redirect("student_registration_list")

    first_stream = streams.first()

    current_enrollment = Enrollment.objects.filter(
        student=student,
        status="registered",
        stream__lecture__subject_id=subject_id,
        stream__lecture__type=lecture_type
    ).select_related(
        "stream",
        "stream__lecture",
        "stream__lecture__subject",
        "stream__lecture__teacher__user",
        "stream__lecture__term"
    ).prefetch_related("stream__group").first()

    teacher_map = {}
    for stream in streams:
        if stream.lecture.teacher:
            teacher_map[stream.lecture.teacher.id] = stream.lecture.teacher

    teachers = sorted(
        teacher_map.values(),
        key=lambda teacher: (
            teacher.user.get_full_name().strip().lower()
            if teacher.user.get_full_name().strip()
            else teacher.user.username.lower()
        )
    )

    selected_teacher_id = request.GET.get("teacher")
    filtered_streams = []

    if len(teachers) == 1 and not selected_teacher_id:
        selected_teacher_id = str(teachers[0].id)

    if selected_teacher_id:
        filtered_streams = streams.filter(
            lecture__teacher_id=selected_teacher_id
        )

    return render(request, "student_registration_step.html", {
        "student": student,
        "subject": first_stream.lecture.subject,
        "lecture_type": first_stream.lecture.type,
        "lecture_type_display": first_stream.lecture.get_type_display(),
        "is_elective": first_stream.lecture.is_elective,
        "credits": first_stream.lecture.credits,
        "teachers": teachers,
        "selected_teacher_id": selected_teacher_id,
        "filtered_streams": filtered_streams,
        "current_enrollment": current_enrollment,
    })


@login_required
def register_stream(request, stream_id):
    if request.user.userprofile.role != "student":
        return redirect("role_redirect")

    student = get_object_or_404(Student, user=request.user)

    stream = get_object_or_404(
        Stream.objects.select_related(
            "lecture",
            "lecture__subject",
            "lecture__teacher__user",
        ).prefetch_related("group"),
        id=stream_id
    )

    if student.group not in stream.group.all():
        messages.error(request, "Вы не можете зарегистрироваться в этот поток.")
        return redirect("student_registration_list")

    if stream.status == "closed":
        messages.error(request, "Регистрация на этот поток закрыта.")
        return redirect("student_registration_list")

    if stream.status == "full":
        messages.error(request, "Поток заполнен.")
        return redirect("student_registration_list")

    if stream.is_full_for_student(student):
        stream.refresh_status()
        messages.error(request, "Свободных мест для вашей формы обучения нет.")
        return redirect("student_registration_list")

    same_option_enrollments = Enrollment.objects.filter(
        student=student,
        status="registered",
        stream__lecture__subject=stream.lecture.subject,
        stream__lecture__type=stream.lecture.type
    ).select_related("stream")

    for old_enrollment in same_option_enrollments:
        if old_enrollment.stream_id == stream.id:
            messages.warning(request, "Вы уже зарегистрированы в этот поток.")
            return redirect(
                "registration_step",
                subject_id=stream.lecture.subject_id,
                lecture_type=stream.lecture.type
            )

    for old_enrollment in same_option_enrollments:
        old_stream = old_enrollment.stream
        old_enrollment.status = "cancelled"
        old_enrollment.save(update_fields=["status"])
        old_stream.refresh_status()

    enrollment, created = Enrollment.objects.get_or_create(
        student=student,
        stream=stream,
        defaults={"status": "registered"}
    )

    if not created:
        enrollment.status = "registered"
        enrollment.save(update_fields=["status"])

    stream.refresh_status()
    messages.success(request, "Вы успешно зарегистрировались.")
    return redirect(
        "registration_step",
        subject_id=stream.lecture.subject_id,
        lecture_type=stream.lecture.type
    )

@login_required
def cancel_registration(request, enrollment_id):
    if request.user.userprofile.role != "student":
        return redirect("role_redirect")

    student = get_object_or_404(Student, user=request.user)

    enrollment = get_object_or_404(
        Enrollment.objects.select_related(
            "stream",
            "stream__lecture",
            "stream__lecture__subject"
        ),
        id=enrollment_id,
        student=student,
        status="registered"
    )

    if enrollment.stream.status == "closed":
        messages.error(request, "Регистрация закрыта. Отменить запись нельзя.")
        return redirect("student_registration_list")

    enrollment.status = "cancelled"
    enrollment.save(update_fields=["status"])

    enrollment.stream.refresh_status()

    messages.success(request, "Регистрация отменена.")
    return redirect(
        "registration_step",
        subject_id=enrollment.stream.lecture.subject_id,
        lecture_type=enrollment.stream.lecture.type
    )