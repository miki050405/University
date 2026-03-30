from django import forms
from .models import Lecture, Teacher, Subject, Group, Stream

class LoginForm(forms.Form):
    username = forms.CharField(
        label="Логин",
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Введите логин"
        })
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            "class": "form-input",
            "placeholder": "Введите пароль"
        })
    )

class LectureForm(forms.ModelForm):
    class Meta:
        model = Lecture
        fields = [
            "subject",
            "teacher",
            "term",
            "type",
            "hours",
            "credits",
            "syllabus_url",
            "is_elective",
        ]

    def __init__(self, *args, **kwargs):
        chair = kwargs.pop("chair", None)
        super().__init__(*args, **kwargs)

        if chair:
            self.fields["teacher"].queryset = Teacher.objects.filter(chair=chair)
            self.fields["subject"].queryset = Subject.objects.filter(chair=chair)
        else:
            self.fields["teacher"].queryset = Teacher.objects.none()
            self.fields["subject"].queryset = Subject.objects.none()

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name"]
    
class StreamForm(forms.ModelForm):
    class Meta:
        model = Stream
        fields = [
            "lecture",
            "group",
            "subgroup",
            "max_budget",
            "max_contract",
        ]
        widgets = {
            "group": forms.CheckboxSelectMultiple
        }

    def __init__(self, *args, **kwargs):
        chair = kwargs.pop("chair", None)
        super().__init__(*args, **kwargs)

        if chair:
            self.fields["lecture"].queryset = Lecture.objects.filter(
                subject__chair=chair
            ).select_related(
                "subject",
                "teacher__user"
            ).order_by("subject__name")

            self.fields["lecture"].label_from_instance = self.lecture_label

            self.fields["group"].queryset = Group.objects.filter(
                specialty__chair=chair
            ).order_by("name")
        else:
            self.fields["lecture"].queryset = Lecture.objects.none()
            self.fields["group"].queryset = Group.objects.none()

    def lecture_label(self, lecture):
        teacher = lecture.teacher

        if teacher and teacher.user.get_full_name():
            teacher_name = teacher.user.get_full_name()
        elif teacher:
            teacher_name = teacher.user.username
        else:
            teacher_name = "Без преподавателя"

        return f"{lecture.subject.name} ({lecture.get_type_display()}) — {teacher_name}"