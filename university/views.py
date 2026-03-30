"""
Модуль views для обработки запросов пользователей
и отображения страниц веб-приложения университета.
"""
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import LoginForm
from .models import Student, Enrollment, ProgressInStudy, Schedule, TimeSlot, GradeControl


def authorization_view(request):
    
    if request.user.is_authenticated:
        return redirect("role_redirect")

    form = LoginForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect("role_redirect")
            messages.error(request, "Неверный логин или пароль.")

    return render(request, "authorization.html", {"form": form})

@login_required
def logout_view(request):
    logout(request)
    return redirect("authorization")


@login_required
def role_redirect_view(request):
    profile = getattr(request.user, "userprofile", None)

    if profile is None:
        messages.error(request, "Для пользователя не назначен профиль.")
        logout(request)
        return redirect("authorization")

    if profile.role == "student":
        return redirect("student_dashboard")
    if request.user.userprofile.role == "teacher":
        return redirect("teacher_dashboard")
    if profile.role == "chair":
        return redirect("chair_dashboard")
    if profile.role == "admin":
        return redirect("/admin/")

    messages.error(request, "Неизвестная роль пользователя.")
    logout(request)
    return redirect("authorization")


@login_required
def student_dashboard(request):
    if request.user.userprofile.role != "student":
        return redirect("role_redirect")

    try:
        student = Student.objects.select_related(
            "user", "group", "group__specialty", "group__specialty__faculty",
            "nationality", "region", "study_form"
        ).get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Данные студента не найдены.")
        return redirect("logout")

    enrollments = Enrollment.objects.filter(
        student=student,
        status="registered"
    ).select_related(
        "stream",
        "stream__lecture",
        "stream__lecture__subject",
        "stream__lecture__teacher",
        "stream__lecture__teacher__user",
        "stream__lecture__term",
    ).prefetch_related(
        "stream__group"
    )

    # progress_list = ProgressInStudy.objects.filter(
    #     student=student
    # ).select_related(
    #     "lecture",
    #     "lecture__subject",
    #     "lecture__teacher",
    #     "lecture__teacher__user",
    #     "lecture__term"
    # )

    schedules = Schedule.objects.filter(
        stream__enrollment__student=student,
        stream__enrollment__status="registered"
    ).select_related(
        "stream",
        "stream__lecture",
        "stream__lecture__subject",
        "stream__lecture__teacher",
        "stream__lecture__teacher__user",
        "timeslot",
    ).prefetch_related(
        "stream__group"
    ).distinct().order_by("day_of_week", "timeslot__number")
    day_names = {
        1: "Понедельник",
        2: "Вторник",
        3: "Среда",
        4: "Четверг",
        5: "Пятница",
        6: "Суббота",
    }

    lecture_type_map = {
        "lecture": "Лек",
        "practice": "Пр",
        "lab": "Лаб",
    }

    week_type_map = {
        "every": "",
        "numerator": "Чис",
        "denominator": "Знам",
        None: "",
        "": "",
    }
    def teacher_name_short(teacher):
        if not teacher:
            return "—"

        user = teacher.user
        last_name = user.last_name or user.username
        first_initial = f"{user.first_name[0]}." if user.first_name else ""
        last_initial = f"{user.last_name[0]}." if user.last_name else ""

        if first_initial:
            if user.first_name and user.last_name:
                return f"{last_name} {first_initial}"
            return last_name

        full_name = user.get_full_name().strip()
        return full_name if full_name else user.username

    timeslots = list(
        TimeSlot.objects.all().order_by("number")
    )

    schedule_map = defaultdict(list)
    for item in schedules:
        key = (item.timeslot_id, item.day_of_week)
        schedule_map[key].append(item)

    schedule_rows = []
    for slot in timeslots:
        row = {
            "timeslot": slot,
            "cells": []
        }

        for day in range(1, 7):
            lessons = []
            for item in schedule_map.get((slot.id, day), []):
                lessons.append({
                    "subject": item.stream.lecture.subject.name,
                    "type_short": lecture_type_map.get(
                        item.stream.lecture.type, 
                        item.stream.lecture.type,
                    ),
                    "week_short": week_type_map.get(item.week_type, ""),
                    "room": f"{item.building} {item.room}",
                    "teacher": teacher_name_short(item.stream.lecture.teacher),
                })

            row["cells"].append({
                "day": day,
                "lessons": lessons
            })

        schedule_rows.append(row)

    context = {
        "student": student,
        "schedule_rows": schedule_rows,
        "day_headers": [day_names[i] for i in range(1, 7)],
    }
    return render(request, "student_dashboard.html", context)

@login_required
def student_subjects(request):
    if request.user.userprofile.role != "student":
        return redirect("role_redirect")

    try:
        student = Student.objects.select_related(
            "user", "group", "group__specialty", "group__specialty__faculty",
            "nationality", "region", "study_form"
        ).get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Данные студента не найдены.")
        return redirect("logout")

    enrollments = Enrollment.objects.filter(
        student=student,
        status="registered"
    ).select_related(
        "stream",
        "stream__lecture",
        "stream__lecture__subject",
        "stream__lecture__teacher",
        "stream__lecture__teacher__user",
        "stream__lecture__term",
    ).prefetch_related(
        "stream__group"
    ).distinct()

    type_map = {
        "lecture": "Лекция",
        "practice": "Практика",
        "lab": "Лабораторная",
    }

    def teacher_full_name(user):
        full_name = user.get_full_name().strip()
        return full_name if full_name else user.username

    grouped_subjects = {}

    for enrollment in enrollments:
        lecture_obj = enrollment.stream.lecture
        subject = lecture_obj.subject
        subject_id = subject.id

        if subject_id not in grouped_subjects:
            grouped_subjects[subject_id] = {
                "subject_name": subject.name,
                "term": lecture_obj.term.name if lecture_obj.term else "—",
                "credits": None,
                "types": [],
                "teachers_by_type": [],
                "lecture_credits": None,
                "fallback_credits": None,
            }

        item = grouped_subjects[subject_id]

        lesson_type_code = lecture_obj.type
        lesson_type_display = type_map.get(lesson_type_code, lesson_type_code)

        if lesson_type_display not in item["types"]:
            item["types"].append(lesson_type_display)

        teacher_name = "—"
        if lecture_obj.teacher:
            teacher_name = teacher_full_name(lecture_obj.teacher.user)

        teacher_entry = {
            "type": lesson_type_display,
            "teacher": teacher_name,
        }

        if teacher_entry not in item["teachers_by_type"]:
            item["teachers_by_type"].append(teacher_entry)

        if lesson_type_code == "lecture":
            item["lecture_credits"] = lecture_obj.credits

        if item["fallback_credits"] is None:
            item["fallback_credits"] = lecture_obj.credits

    subjects_list = []
    for item in grouped_subjects.values():
        if item["lecture_credits"] is not None:
            item["credits"] = item["lecture_credits"]
        else:
            item["credits"] = item["fallback_credits"]

        subjects_list.append(item)

    subjects_list.sort(key=lambda x: x["subject_name"].lower())

    context = {
        "student": student,
        "subjects_list": subjects_list,
    }
    return render(request, "student_subjects.html", context)

@login_required
def student_grades(request):
    if request.user.userprofile.role != "student":
        return redirect("role_redirect")

    try:
        student = Student.objects.select_related(
            "user", "group", "group__specialty", "group__specialty__faculty",
            "nationality", "region", "study_form"
        ).get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Данные студента не найдены.")
        return redirect("logout")

    enrollments = Enrollment.objects.filter(
        student=student,
        status="registered"
    ).select_related(
        "stream__lecture__subject",
        "stream__lecture__teacher__user",
        "stream__lecture__term",
    ).prefetch_related(
        "stream__group"
    ).distinct()

    type_map = {
        "lecture": "Лекция",
        "practice": "Практика",
        "lab": "Лабораторная",
    }

    def teacher_full_name(user):
        full_name = user.get_full_name().strip()
        return full_name if full_name else user.username

    grouped_subjects = {}

    for enrollment in enrollments:
        lecture_obj = enrollment.stream.lecture
        subject = lecture_obj.subject
        term = lecture_obj.term

        key = (subject.id, term.id)

        if key not in grouped_subjects:
            grouped_subjects[key] = {
                "subject_id": subject.id,
                "term_id": term.id,
                "subject_name": subject.name,
                "term": term.name if term else "—",
                "credits": None,
                "types": [],
                "teachers_by_type": [],
                "lecture_credits": None,
                "fallback_credits": None,
            }

        item = grouped_subjects[key]

        lesson_type_code = lecture_obj.type
        lesson_type_display = type_map.get(lesson_type_code, lesson_type_code)

        if lesson_type_display not in item["types"]:
            item["types"].append(lesson_type_display)

        teacher_name = "—"
        if lecture_obj.teacher:
            teacher_name = teacher_full_name(lecture_obj.teacher.user)

        teacher_entry = {
            "type": lesson_type_display,
            "teacher": teacher_name,
        }

        if teacher_entry not in item["teachers_by_type"]:
            item["teachers_by_type"].append(teacher_entry)

        if lesson_type_code == "lecture":
            item["lecture_credits"] = lecture_obj.credits

        if item["fallback_credits"] is None:
            item["fallback_credits"] = lecture_obj.credits

    subjects_list = []
    for item in grouped_subjects.values():
        if item["lecture_credits"] is not None:
            item["credits"] = item["lecture_credits"]
        else:
            item["credits"] = item["fallback_credits"]

        subjects_list.append(item)

    subjects_list.sort(key=lambda x: (x["subject_name"].lower(), x["term"]))

    selected_subject_id = request.GET.get("subject")
    selected_term_id = request.GET.get("term")

    selected_subject = None
    selected_progress = None
    selected_grade_control = None

    if selected_subject_id and selected_term_id:
        try:
            selected_subject_id = int(selected_subject_id)
            selected_term_id = int(selected_term_id)

            selected_subject = next(
                (
                    item for item in subjects_list
                    if item["subject_id"] == selected_subject_id and item["term_id"] == selected_term_id
                ),
                None
            )

            if selected_subject:
                selected_progress = ProgressInStudy.objects.filter(
                    student=student,
                    subject_id=selected_subject_id,
                    term_id=selected_term_id
                ).select_related(
                    "subject",
                    "term"
                ).first()

                selected_grade_control = GradeControl.objects.filter(
                    subject_id=selected_subject_id,
                    term_id=selected_term_id
                ).first()

        except ValueError:
            selected_subject = None

    context = {
        "student": student,
        "subjects_list": subjects_list,
        "selected_subject": selected_subject,
        "selected_progress": selected_progress,
        "selected_grade_control": selected_grade_control,
    }
    return render(request, "student_grades.html", context)
