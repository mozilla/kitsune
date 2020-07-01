from django.core.validators import RegexValidator


TwitterValidator = RegexValidator(
    r"^[\w]+$", message="Please enter correct Twitter Handle", code="Invalid name"
)
