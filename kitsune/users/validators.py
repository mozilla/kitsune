from django.core.validators import RegexValidator

UsernameValidator = RegexValidator(
    r"^[\w]+$",
    message="Please enter a valid username (letters, numbers, and underscores only)",
    code="Invalid username",
)
