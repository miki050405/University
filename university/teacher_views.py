from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import (
    Teacher,
    Lecture,
    Schedule,
    Enrollment,
    ProgressInStudy,
    GradeControl,
    Stream,
    TimeSlot,
)


def teacher_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not hasattr(request.user, "userprofile") or request.user.userprofile.role != "teacher":
            return redirect("role_redirect")
        return view_func(request, *args, **kwargs)
    return wrapper


def build_teacher_schedule_grid(teacher):
    day_headers = [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
    ]
    day_numbers = [1, 2, 3, 4, 5, 6]

    schedules = Schedule.objects.filter(
        stream__lecture__teacher=teacher
    ).select_related(
        "stream__lecture__subject",
        "timeslot",
    ).prefetch_related(
        "stream__group"
    ).order_by("timeslot__number", "day_of_week")

    timeslots = TimeSlot.objects.all().order_by("number")

    schedule_map = {}

    for item in schedules:
        key = (item.timeslot_id, item.day_of_week)

        group_names = ", ".join(group.name for group in item.stream.group.all())

        type_short_map = {
            "lecture": "Лек",
            "practice": "Пр",
            "lab": "Лаб",
        }

        week_short_map = {
            "every": "",
            "numerator": "Числ",
            "denominator": "Знам",
        }

        lesson_data = {
            "subject": item.stream.lecture.subject.name,
            "type_short": type_short_map.get(item.stream.lecture.type, ""),
            "week_short": week_short_map.get(item.week_type, ""),
            "room": f"{item.building} {item.room}",
            "groups": group_names,
            "subgroup": item.stream.get_subgroup_display(),
        }

        schedule_map.setdefault(key, []).append(lesson_data)

    schedule_rows = []
    for timeslot in timeslots:
        row = {
            "timeslot": timeslot,
            "cells": []
        }

        for day in day_numbers:
            lessons = schedule_map.get((timeslot.id, day), [])
            row["cells"].append({
                "lessons": lessons
            })

        schedule_rows.append(row)

    return day_headers, schedule_rows


@login_required
@teacher_required
def teacher_dashboard(request):
    teacher = get_object_or_404(
        Teacher.objects.select_related("user", "position"),
        user=request.user
    )

    day_headers, schedule_rows = build_teacher_schedule_grid(teacher)

    context = {
        "teacher": teacher,
        "day_headers": day_headers,
        "schedule_rows": schedule_rows,
    }
    return render(request, "teachers/dashboard.html", context)


@login_required
@teacher_required
def teacher_journal_list(request):
    teacher = get_object_or_404(
        Teacher.objects.select_related("user", "position"),
        user=request.user
    )

    teacher_lectures = Lecture.objects.filter(
        teacher=teacher
    ).select_related(
        "subject",
        "term"
    ).order_by("subject__name", "term__start_date")

    type_priority = {
        "lecture": 1,
        "practice": 2,
        "lab": 3,
    }

    main_lectures_map = {}

    for lecture in teacher_lectures:
        key = (lecture.subject_id, lecture.term_id)

        if key not in main_lectures_map:
            main_lectures_map[key] = lecture
        else:
            current_main = main_lectures_map[key]
            if type_priority.get(lecture.type, 99) < type_priority.get(current_main.type, 99):
                main_lectures_map[key] = lecture

    lectures = list(main_lectures_map.values())
    lectures.sort(key=lambda x: (x.subject.name, x.term.start_date))

    context = {
        "teacher": teacher,
        "lectures": lectures,
    }
    return render(request, "teachers/lectures.html", context)


@login_required
@teacher_required
def teacher_journal_streams(request, lecture_id):
    teacher = get_object_or_404(
        Teacher.objects.select_related("user", "position"),
        user=request.user
    )

    lecture = get_object_or_404(
        Lecture.objects.select_related("subject", "term"),
        id=lecture_id,
        teacher=teacher
    )

    streams = Stream.objects.filter(
        lecture=lecture
    ).prefetch_related("group").order_by("subgroup", "id")

    context = {
        "teacher": teacher,
        "lecture": lecture,
        "streams": streams,
    }
    return render(request, "teachers/lecture_detail.html", context)


@login_required
@teacher_required
def teacher_gradebook(request, stream_id):
    teacher = get_object_or_404(
        Teacher.objects.select_related("user", "position"),
        user=request.user
    )

    stream = get_object_or_404(
        Stream.objects.select_related(
            "lecture__subject",
            "lecture__term",
            "lecture__teacher"
        ).prefetch_related("group"),
        id=stream_id,
        lecture__teacher=teacher
    )

    lecture = stream.lecture
    subject = lecture.subject
    term = lecture.term

    grade_control, _ = GradeControl.objects.get_or_create(
        subject=subject,
        term=term,
        defaults={
            "has_module1": True,
            "has_module2": True,
            "has_final_exam": True,
            "has_extra": False,
            "module1_active": False,
            "module2_active": False,
            "final_exam_active": False,
            "extra_active": False,
        }
    )

    enrollments = Enrollment.objects.filter(
        stream=stream,
        status="registered"
    ).select_related(
        "student__user",
        "student__group"
    ).order_by(
        "student__user__last_name",
        "student__user__first_name"
    )

    students = [enrollment.student for enrollment in enrollments]

    progress_map = {}
    for student in students:
        progress, _ = ProgressInStudy.objects.get_or_create(
            student=student,
            subject=subject,
            term=term
        )
        progress_map[student.id] = progress

    if request.method == "POST":
        def get_int_value(field_name, student_id):
            value = request.POST.get(f"{field_name}_{student_id}", "").strip()
            if value == "":
                return None
            try:
                return int(value)
            except ValueError:
                return None

        for student in students:
            progress = progress_map[student.id]

            if grade_control.has_module1 and grade_control.module1_active:
                progress.module1 = get_int_value("module1", student.id)

            if grade_control.has_module2 and grade_control.module2_active:
                progress.module2 = get_int_value("module2", student.id)

            if grade_control.has_final_exam and grade_control.final_exam_active:
                progress.final_exam = get_int_value("final_exam", student.id)

            if grade_control.has_extra and grade_control.extra_active:
                progress.extra = get_int_value("extra", student.id)

            total = 0

            if grade_control.has_module1 and progress.module1 is not None:
                total += progress.module1
            if grade_control.has_module2 and progress.module2 is not None:
                total += progress.module2
            if grade_control.has_final_exam and progress.final_exam is not None:
                total += progress.final_exam
            if grade_control.has_extra and progress.extra is not None:
                total += progress.extra

            progress.final_grade = min(total, 100)
            progress.save()

        messages.success(request, "Оценки успешно сохранены.")
        return redirect("teacher_gradebook", stream_id=stream.id)

    student_rows = []
    for student in students:
        student_rows.append({
            "student": student,
            "progress": progress_map[student.id],
        })

    context = {
        "teacher": teacher,
        "stream": stream,
        "lecture": lecture,
        "grade_control": grade_control,
        "student_rows": student_rows,
    }
    return render(request, "teachers/gradebook.html", context)