from .models import Student, Teacher


def user_role_data(request):

    if not request.user.is_authenticated:
        return {}

    data = {}

    try:
        data["student"] = Student.objects.select_related("group").get(user=request.user)
    except Student.DoesNotExist:
        pass

    try:
        data["teacher"] = Teacher.objects.select_related("position").get(user=request.user)
    except Teacher.DoesNotExist:
        pass

    return data