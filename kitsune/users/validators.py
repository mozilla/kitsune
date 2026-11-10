from django.core.validators import RegexValidator

UsernameValidator = RegexValidator(
    r"^[\w]+$",
    message="Please enter a valid username (letters, numbers, and underscores only)",
    code="Invalid username",
)

XUsernameValidator = RegexValidator(
    r"^(?:[\w]+|i/user/[0-9]+)$",
    message="Please enter a valid X username or profile permalink",
    code="Invalid username",
)
