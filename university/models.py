from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# models 

class Nationality(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class StudyForm(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class Faculty(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name
    
class Chair(models.Model):
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name="chairs"
    )
    name = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["faculty", "name"],
                name="unique_chair_per_faculty"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.faculty.name})"
    
class Specialty(models.Model):
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name="specialties"
    )

    chair = models.ForeignKey(
        Chair,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="specialties"
    )

    name = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["faculty", "name"],
                name="unique_specialty_per_faculty"
            )
        ]

    def __str__(self):
        return self.name   

class Group(models.Model):
    name = models.CharField(max_length=50, unique=True)

    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.CASCADE,
        related_name="groups"
    )

    def __str__(self):
        return self.name
    
class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    ROLE_CHOICES = [
        ("student", "Студент"),
        ("teacher", "Преподаватель"),
        ("chair", "Кафедра"),
        ("admin", "Администратор"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    chair = models.ForeignKey(
        Chair,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profiles"
    )
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

class Student(models.Model):
    GENDER_CHOICES = [
        ("male", "Мужской"),
        ("female", "Женский"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    nationality = models.ForeignKey(
        Nationality,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    study_form = models.ForeignKey(
        StudyForm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField()
    course = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)]
    )
    def __str__(self):
        full_name = self.user.get_full_name().strip()
        return full_name if full_name else self.user.username
    
class TeacherPosition(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Должность преподавателя"
        verbose_name_plural = "Должности преподавателей"

    def __str__(self):
        return self.name
     
class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    chair = models.ForeignKey(
        Chair,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teachers"
    )
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    position = models.ForeignKey(
        TeacherPosition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teachers"
    )

    def __str__(self):
        full_name = self.user.get_full_name().strip()
        return full_name if full_name else self.user.username
    
class Subject(models.Model):
    chair = models.ForeignKey(
        Chair,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subjects"
    )
    name = models.CharField("Название дисциплины",max_length=200, unique=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["chair", "name"],
                name="unique_subject_per_chair"
            )
        ]
    def __str__(self):
        return self.name
    
class Term(models.Model):
    name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name
    
class Lecture(models.Model):

    TYPE_CHOICES = [
        ("lecture", "Лекция"),
        ("practice", "Практика"),
        ("lab", "Лабораторная"),
    ]

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        verbose_name="Дисциплина"
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Преподаватель"
    )

    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        verbose_name="Семестр"
    )

    type = models.CharField("Тип занятия", max_length=20, choices=TYPE_CHOICES)
    hours = models.PositiveIntegerField("Количество часов")
    credits = models.PositiveIntegerField("Количество кредитов")
    syllabus_url = models.URLField(blank=True, null=True)
    is_elective = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.subject} ({self.get_type_display()})"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subject", "teacher", "term", "type"],
                name="unique_lecture_per_subject_teacher_term_type"
            )
        ]
    
class Stream(models.Model):
    STATUS_CHOICES = [
        ("open", "Открыт"),
        ("closed", "Закрыт"),
        ("full", "Заполнен"),
    ]

    SUBGROUP_CHOICES = [
        (0, "Вся группа"),
        (1, "Подгруппа 1"),
        (2, "Подгруппа 2"),
    ]

    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        verbose_name="Занятие"
    )

    group = models.ManyToManyField(
        Group,
        related_name="streams",
        verbose_name="Группы"
    )
    subgroup = models.IntegerField("Подгруппа",choices=SUBGROUP_CHOICES, default=0)

    max_budget = models.PositiveIntegerField("Мест (бюджет)",null=True, blank=True)
    max_contract = models.PositiveIntegerField("Мест (контракт)",null=True, blank=True)

    status = models.CharField("Статус",max_length=20, choices=STATUS_CHOICES, default="closed")

    def __str__(self):
        return f"{self.lecture} | {self.get_subgroup_display()}"
    

    def get_registered_budget_count(self):
        return Enrollment.objects.filter(
            stream=self,
            status="registered",
            student__study_form__name__iexact="Бюджет"
        ).count()

    def get_registered_contract_count(self):
        return Enrollment.objects.filter(
            stream=self,
            status="registered",
            student__study_form__name__iexact="Контракт"
        ).count()

    def is_full_for_student(self, student):
        if not student.study_form:
            return True

        study_form_name = student.study_form.name.strip().lower()

        if study_form_name == "бюджет":
            if self.max_budget is None:
                return False
            return self.get_registered_budget_count() >= self.max_budget

        if study_form_name == "контракт":
            if self.max_contract is None:
                return False
            return self.get_registered_contract_count() >= self.max_contract

        return True

    def refresh_status(self):
        if self.status == "closed":
            return

        budget_full = (
            self.max_budget is not None and
            self.get_registered_budget_count() >= self.max_budget
        )
        contract_full = (
            self.max_contract is not None and
            self.get_registered_contract_count() >= self.max_contract
        )

        budget_exists = self.max_budget not in (None, 0)
        contract_exists = self.max_contract not in (None, 0)

        if budget_exists and contract_exists:
            self.status = "full" if budget_full and contract_full else "open"
        elif budget_exists:
            self.status = "full" if budget_full else "open"
        elif contract_exists:
            self.status = "full" if contract_full else "open"
        else:
            self.status = "open"

        self.save(update_fields=["status"])
    
class Enrollment(models.Model):
    STATUS_CHOICES = [
        ("registered", "Зарегистрирован"),
        ("cancelled", "Отменена")
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    stream = models.ForeignKey(
        Stream,
        on_delete=models.CASCADE
    )

    date = models.DateField(auto_now_add=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="registered")

    def __str__(self):
        return f"{self.student} -> {self.stream}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "stream"],
                name="unique_student_stream_enrollment"
            )
        ]
    
class ProgressInStudy(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    module1 = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(30)]
    )
    module2 = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(30)]
    )
    final_exam = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(40)]
    )
    extra = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    final_grade = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    def __str__(self):
        return f"{self.student} - {self.subject} ({self.term})"
    

class GradeControl(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="grade_controls",
        null=True,
        blank=True
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="grade_controls",
        null=True,
        blank=True
    )
    has_module1 = models.BooleanField(default=True)
    has_module2 = models.BooleanField(default=True)
    has_final_exam = models.BooleanField(default=True)
    has_extra = models.BooleanField(default=False)

    module1_active = models.BooleanField(default=False)
    module2_active = models.BooleanField(default=False)
    final_exam_active = models.BooleanField(default=False)
    extra_active = models.BooleanField(default=False)

    def __str__(self):
        return f"Настройки оценивания: {self.subject} ({self.term})"
    
class TimeSlot(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number} пара ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

class Schedule(models.Model):

    WEEK_TYPE_CHOICES = [
        ("every", "Каждую неделю"),
        ("numerator", "Числитель"),
        ("denominator", "Знаменатель"),
    ]
        
    DAY_CHOICES = [
        (1, "Понедельник"),
        (2, "Вторник"),
        (3, "Среда"),
        (4, "Четверг"),
        (5, "Пятница"),
        (6, "Суббота"),
    ]

    stream = models.ForeignKey(
        Stream,
        on_delete=models.CASCADE
    )
    week_type = models.CharField(
        max_length=20,
        choices=WEEK_TYPE_CHOICES,
        default="every"
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    timeslot = models.ForeignKey(
        TimeSlot,
        on_delete=models.PROTECT,
        related_name="schedules",
        null=True,
        blank=True,
    )
    building = models.CharField(max_length=50)
    room = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.stream} | {self.get_day_of_week_display()} | {self.timeslot}"
    