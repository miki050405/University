from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import LectureForm, SubjectForm, StreamForm
from .models import Lecture, Subject, Stream, Student, Group, Specialty


@login_required
def chair_dashboard(request):
    profile = request.user.userprofile

    if profile.role != "chair":
        return redirect("role_redirect")

    return render(request, "chair_dashboard.html")


@login_required
def create_lecture(request):
    profile = request.user.userprofile

    if profile.role != "chair":
        return redirect("role_redirect")

    if not profile.chair:
        messages.error(request, "У вашего профиля не указана кафедра.")
        return redirect("role_redirect")

    if request.method == "POST":
        form = LectureForm(request.POST, chair=profile.chair)
        if form.is_valid():
            form.save()
            messages.success(request, "Лекция успешно создана.")
            return redirect("create_lecture")
    else:
        form = LectureForm(chair=profile.chair)

    return render(request, "create_lecture.html", {
        "form": form
    })


@login_required
def lecture_list(request):
    profile = request.user.userprofile

    if profile.role != "chair":
        return redirect("role_redirect")

    if not profile.chair:
        messages.error(request, "У вашего профиля не указана кафедра.")
        return redirect("role_redirect")

    lectures = Lecture.objects.filter(
        subject__chair=profile.chair
    ).select_related(
        "subject",
        "subject__chair",
        "teacher__user",
        "term"
    ).order_by("subject__name")

    return render(request, "lecture_list.html", {
        "lectures": lectures
    })


@login_required
def edit_lecture(request, lecture_id):
    profile = request.user.userprofile

    if profile.role != "chair":
        return redirect("role_redirect")

    if not profile.chair:
        messages.error(request, "У вашего профиля не указана кафедра.")
        return redirect("role_redirect")

    lecture = get_object_or_404(
        Lecture,
        id=lecture_id,
        subject__chair=profile.chair
    )

    if request.method == "POST":
        form = LectureForm(request.POST, instance=lecture, chair=profile.chair)
        if form.is_valid():
            form.save()
            messages.success(request, "Занятие успешно обновлено.")
            return redirect("lecture_list")
    else:
        form = LectureForm(instance=lecture, chair=profile.chair)

    return render(request, "edit_lecture.html", {
        "form": form,
        "lecture": lecture
    })


@login_required
def delete_lecture(request, lecture_id):
    profile = request.user.userprofile

    if profile.role != "chair":
        return redirect("role_redirect")

    if not profile.chair:
        messages.error(request, "У вашего профиля не указана кафедра.")
        return redirect("role_redirect")

    lecture = get_object_or_404(
        Lecture,
        id=lecture_id,
        subject__chair=profile.chair
    )

    if request.method == "POST":
        lecture.delete()
        messages.success(request, "Занятие удалено.")
        return redirect("lecture_list")

    return render(request, "delete_lecture.html", {
        "lecture": lecture
    })

@login_required
def subject_list(request):
    profile = request.user.userprofile

    if profile.role != "chair":
        return redirect("role_redirect")

    if not profile.chair:
        messages.error(request, "У вашего профиля не указана кафедра.")
        return redirect("role_redirect")

    subjects = Subject.objects.filter(
        chair=profile.chair
    ).order_by("name")

    return render(request, "subject_list.html", {
        "subjects": subjects
    })


@login_required
def create_subject(request):
    profile = request.user.userprofile

    if profile.role != "chair":
        return redirect("role_redirect")

    if not profile.chair:
        messages.error(request, "У вашего профиля не указана кафедра.")
        return redirect("role_redirect")

    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.chair = profile.chair
            subject.save()
            messages.success(request, "Дисциплина успешно создана.")
            return redirect("subject_list")
    else:
        form = SubjectForm()

    return render(request, "create_subject.html", {
        "form": form
    })


@login_required
def edit_subject(request, subject_id):
    profile = request.user.userprofile

    if profile.role != "chair":
        return redirect("role_redirect")

    if not profile.chair:
        messages.error(request, "У вашего профиля не указана кафедра.")
        return redirect("role_redirect")

    subject = get_object_or_404(
        Subject,
        id=subject_id,
        chair=profile.chair
    )

    if request.method == "POST":
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            edited_subject = form.save(commit=False)
            edited_subject.chair = profile.chair
            edited_subject.save()
            messages.success(request, "Дисциплина успешно обновлена.")
            return redirect("subject_list")
    else:
        form = SubjectForm(instance=subject)

    return render(request, "edit_subject.html", {
        "form": form,
        "subject": subject
    })


@login_required
def delete_subject(request, subject_id):
    profile = request.user.userprofile

    if profile.role != "chair":
        return redirect("role_redirect")

    if not profile.chair:
        messages.error(request, "У вашего профиля не указана кафедра.")
        return redirect("role_redirect")

    subject = get_object_or_404(
        Subject,
        id=subject_id,
        chair=profile.chair
    )

    if request.method == "POST":
        subject.delete()
        messages.success(request, "Дисциплина удалена.")
        return redirect("subject_list")

    return render(request, "delete_subject.html", {
        "subject": subject
    })

@login_required
def stream_list(request):
    profile = request.user.userprofile

    if profile.role != "chair":
        return redirect("role_redirect")

    if not profile.chair:
        messages.error(request, "У вашего профиля не указана кафедра.")
        return redirect("role_redirect")

    streams = Stream.objects.filter(
        lecture__subject__chair=profile.chair
    ).select_related(
        "lecture",
        "lecture__subject",
        "lecture__term"
    ).prefetch_related("group").order_by("lecture__subject__name")

    lectures = Lecture.objects.filter(
        subject__chair=profile.chair
    ).select_related("subject", "term").order_by("subject__name", "type")

    groups = Group.objects.filter(
        specialty__chair=profile.chair
    ).order_by("name")

    lecture_id = request.GET.get("lecture")
    group_id = request.GET.get("group")

    if lecture_id:
        streams = streams.filter(lecture_id=lecture_id)

    if group_id:
        streams = streams.filter(group__id=group_id)

    return render(request, "streams/stream_list.html", {
        "streams": streams.distinct(),
        "lectures": lectures,
        "groups": groups,
        "selected_lecture": lecture_id,
        "selected_group": group_id,
    })


@login_required
def create_stream(request):
    profile = request.user.userprofile

    if profile.role != "chair":
        return redirect("role_redirect")

    if request.method == "POST":
        form = StreamForm(request.POST, chair=profile.chair)
        if form.is_valid():
            form.save()
            messages.success(request, "Поток успешно создан.")
            return redirect("stream_list")
    else:
        form = StreamForm(chair=profile.chair)

    return render(request, "streams/create_stream.html", {
        "form": form
    })

@login_required
def edit_stream(request, stream_id):
    profile = request.user.userprofile

    if profile.role != "chair":
        return redirect("role_redirect")

    stream = get_object_or_404(
        Stream,
        id=stream_id,
        lecture__subject__chair=profile.chair
    )

    if request.method == "POST":
        form = StreamForm(request.POST, instance=stream, chair=profile.chair)
        if form.is_valid():
            form.save()
            messages.success(request, "Поток обновлён.")
            return redirect("stream_list")
    else:
        form = StreamForm(instance=stream, chair=profile.chair)

    return render(request, "streams/edit_stream.html", {
        "form": form,
        "stream": stream
    })

@login_required
def delete_stream(request, stream_id):
    profile = request.user.userprofile

    if profile.role != "chair":
        return redirect("role_redirect")

    stream = get_object_or_404(
        Stream,
        id=stream_id,
        lecture__subject__chair=profile.chair
    )

    if request.method == "POST":
        stream.delete()
        messages.success(request, "Поток удалён.")
        return redirect("stream_list")

    return render(request, "streams/delete_stream.html", {
        "stream": stream
    })

@login_required
def chair_groups(request):
    if request.user.userprofile.role != "chair":
        return redirect("role_redirect")

    chair = request.user.userprofile.chair

    specialties = Specialty.objects.filter(
        chair=chair
    ).order_by("name")

    specialty_id = request.GET.get("specialty")

    groups = Group.objects.filter(
        specialty__chair=chair
    ).select_related(
        "specialty",
        "specialty__faculty",
        "specialty__chair"
    )

    selected_specialty = None

    if specialty_id:
        try:
            specialty_id = int(specialty_id)
            groups = groups.filter(specialty_id=specialty_id)
            selected_specialty = specialties.filter(id=specialty_id).first()
        except ValueError:
            specialty_id = None

    groups = groups.order_by("specialty__name", "name")

    context = {
        "groups": groups,
        "chair": chair,
        "specialties": specialties,
        "selected_specialty": selected_specialty,
    }
    return render(request, "chair/groups.html", context)

@login_required
def chair_group_students(request, group_id):
    if request.user.userprofile.role != "chair":
        return redirect("role_redirect")

    chair = request.user.userprofile.chair

    group = get_object_or_404(
        Group.objects.select_related(
            "specialty",
            "specialty__faculty",
            "specialty__chair"
        ),
        id=group_id,
        specialty__chair=chair
    )

    students = Student.objects.filter(
        group=group
    ).select_related(
        "user",
        "nationality",
        "region",
        "study_form"
    ).order_by(
        "user__last_name",
        "user__first_name"
    )

    context = {
        "group": group,
        "students": students,
        "chair": chair,
    }
    return render(request, "chair/group_students.html", context)