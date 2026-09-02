"""
Account and Authentication Validators.
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_username_format(value: str):
    """
    Ensures username contains only alphanumeric characters, underscores, or hyphens,
    and is between 3 and 30 characters.
    """
    if not re.match(r'^[a-zA-Z0-9_-]{3,30}$', value):
        raise ValidationError(
            _('Username must be 3-30 characters long and contain only letters, numbers, underscores, or hyphens.')
        )


def validate_phone_number(value: str):
    """
    Validates international E.164 phone format.
    """
    if value and not re.match(r'^\+?[1-9]\d{1,14}$', value):
        raise ValidationError(_('Please enter a valid international phone number in format +1234567890.'))


def validate_image_file_extension(value):
    """
    Checks if uploaded avatar or banner is an allowed image format.
    """
    import os
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if ext not in valid_extensions:
        raise ValidationError(_(f'Unsupported image file extension. Allowed extensions are: {", ".join(valid_extensions)}'))


def validate_image_file_size(value):
    """
    Ensures image does not exceed 5 MB.
    """
    limit = 5 * 1024 * 1024  # 5 MB
    if value.size > limit:
        raise ValidationError(_('File size exceeds the 5 MB limit.'))


class ComplexPasswordValidator:
    """
    Enforces minimum 8 characters, at least 1 uppercase letter, 1 lowercase letter,
    1 digit, and 1 special symbol.
    """
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(_('Password must be at least 8 characters long.'), code='password_too_short')
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_('Password must contain at least one uppercase letter.'), code='password_no_upper')
        if not re.search(r'[a-z]', password):
            raise ValidationError(_('Password must contain at least one lowercase letter.'), code='password_no_lower')
        if not re.search(r'\d', password):
            raise ValidationError(_('Password must contain at least one digit.'), code='password_no_digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(_('Password must contain at least one special character (!@#$%^&*).'), code='password_no_symbol')

    def get_help_text(self):
        return _(
            'Your password must contain at least 8 characters, including uppercase, lowercase, numbers, and special characters.'
        )
