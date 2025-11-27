"""
Validator implementations for schema validation.

Provides concrete validator classes for different validation types.
"""

import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import EmailStr, HttpUrl, validate_email


class BaseValidator(ABC):
    """Base class for all validators."""

    def __init__(self, error_message: str | None = None) -> None:
        """
        Initialize validator.

        Args:
            error_message: Custom error message
        """
        self.error_message = error_message

    @abstractmethod
    def validate(self, value: Any) -> tuple[bool, str | None]:
        """
        Validate a value.

        Args:
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """

    def __call__(self, value: Any) -> Any:
        """
        Call validator as a function.

        Args:
            value: Value to validate

        Returns:
            The value if valid

        Raises:
            ValueError: If validation fails
        """
        is_valid, error = self.validate(value)
        if not is_valid:
            raise ValueError(error or "Validation failed")
        return value


class LengthValidator(BaseValidator):
    """Validator for string/list length constraints."""

    def __init__(
        self,
        min_length: int | None = None,
        max_length: int | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Initialize length validator.

        Args:
            min_length: Minimum length (inclusive)
            max_length: Maximum length (inclusive)
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value: Any) -> tuple[bool, str | None]:
        """Validate length of value."""
        if not hasattr(value, "__len__"):
            return False, f"Value must have length (got {type(value).__name__})"

        length = len(value)

        if self.min_length is not None and length < self.min_length:
            error = (
                self.error_message
                or f"Length must be at least {self.min_length} (got {length})"
            )
            return False, error

        if self.max_length is not None and length > self.max_length:
            error = (
                self.error_message
                or f"Length must be at most {self.max_length} (got {length})"
            )
            return False, error

        return True, None


class RangeValidator(BaseValidator):
    """Validator for numeric range constraints."""

    def __init__(
        self,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Initialize range validator.

        Args:
            min_value: Minimum value (inclusive)
            max_value: Maximum value (inclusive)
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: Any) -> tuple[bool, str | None]:
        """Validate numeric range."""
        if not isinstance(value, (int, float)):
            return False, f"Value must be numeric (got {type(value).__name__})"

        if self.min_value is not None and value < self.min_value:
            error = (
                self.error_message
                or f"Value must be at least {self.min_value} (got {value})"
            )
            return False, error

        if self.max_value is not None and value > self.max_value:
            error = (
                self.error_message
                or f"Value must be at most {self.max_value} (got {value})"
            )
            return False, error

        return True, None


class RegexValidator(BaseValidator):
    """Validator for regex pattern matching."""

    def __init__(self, pattern: str, error_message: str | None = None) -> None:
        """
        Initialize regex validator.

        Args:
            pattern: Regex pattern to match
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.pattern = pattern
        self._compiled = re.compile(pattern)

    def validate(self, value: Any) -> tuple[bool, str | None]:
        """Validate regex match."""
        if not isinstance(value, str):
            return False, f"Value must be string (got {type(value).__name__})"

        if not self._compiled.match(value):
            error = self.error_message or f"Value must match pattern: {self.pattern}"
            return False, error

        return True, None


class EnumValidator(BaseValidator):
    """Validator for enum/choice constraints."""

    def __init__(
        self,
        allowed_values: list[Any],
        error_message: str | None = None,
    ) -> None:
        """
        Initialize enum validator.

        Args:
            allowed_values: List of allowed values
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.allowed_values = allowed_values

    def validate(self, value: Any) -> tuple[bool, str | None]:
        """Validate value is in allowed list."""
        if value not in self.allowed_values:
            error = (
                self.error_message
                or f"Value must be one of {self.allowed_values} (got {value!r})"
            )
            return False, error

        return True, None


class EmailValidator(BaseValidator):
    """Validator for email addresses."""

    def validate(self, value: Any) -> tuple[bool, str | None]:
        """Validate email address."""
        if not isinstance(value, str):
            return False, f"Email must be string (got {type(value).__name__})"

        try:
            # Use Pydantic's email validation function instead of private method
            validate_email(value)
            return True, None
        except ValueError as e:
            error = self.error_message or f"Invalid email address: {e}"
            return False, error


class URLValidator(BaseValidator):
    """Validator for URLs."""

    def validate(self, value: Any) -> tuple[bool, str | None]:
        """Validate URL."""
        if not isinstance(value, str):
            return False, f"URL must be string (got {type(value).__name__})"

        try:
            # Use Pydantic's URL validation
            HttpUrl(value)
            return True, None
        except ValueError as e:
            error = self.error_message or f"Invalid URL: {e}"
            return False, error


class UUIDValidator(BaseValidator):
    """Validator for UUIDs."""

    def validate(self, value: Any) -> tuple[bool, str | None]:
        """Validate UUID."""
        if isinstance(value, UUID):
            return True, None

        if not isinstance(value, str):
            return False, f"UUID must be string or UUID (got {type(value).__name__})"

        try:
            UUID(value)
            return True, None
        except ValueError as e:
            error = self.error_message or f"Invalid UUID: {e}"
            return False, error


class DateValidator(BaseValidator):
    """Validator for dates."""

    def __init__(
        self,
        format: str = "%Y-%m-%d",
        error_message: str | None = None,
    ) -> None:
        """
        Initialize date validator.

        Args:
            format: Expected date format (default: ISO 8601)
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.format = format

    def validate(self, value: Any) -> tuple[bool, str | None]:
        """Validate date."""
        if isinstance(value, date):
            return True, None

        if not isinstance(value, str):
            return False, f"Date must be string or date (got {type(value).__name__})"

        try:
            datetime.strptime(value, self.format)
            return True, None
        except ValueError as e:
            error = self.error_message or f"Invalid date format (expected {self.format}): {e}"
            return False, error


class DateTimeValidator(BaseValidator):
    """Validator for datetimes."""

    def __init__(
        self,
        format: str = "%Y-%m-%dT%H:%M:%S",
        error_message: str | None = None,
    ) -> None:
        """
        Initialize datetime validator.

        Args:
            format: Expected datetime format (default: ISO 8601)
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.format = format

    def validate(self, value: Any) -> tuple[bool, str | None]:
        """Validate datetime."""
        if isinstance(value, datetime):
            return True, None

        if not isinstance(value, str):
            return False, f"DateTime must be string or datetime (got {type(value).__name__})"

        try:
            datetime.strptime(value, self.format)
            return True, None
        except ValueError as e:
            error = (
                self.error_message or f"Invalid datetime format (expected {self.format}): {e}"
            )
            return False, error


class CustomValidator(BaseValidator):
    """Validator that uses a custom function."""

    def __init__(
        self,
        validator_func: Callable[[Any], bool],
        error_message: str | None = None,
    ) -> None:
        """
        Initialize custom validator.

        Args:
            validator_func: Function that takes value and returns bool
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.validator_func = validator_func

    def validate(self, value: Any) -> tuple[bool, str | None]:
        """Validate using custom function."""
        try:
            result = self.validator_func(value)
        except Exception as e:
            # Validation function raised an exception
            error = self.error_message or f"Validation error: {e}"
            return False, error

        # Check return type
        if not isinstance(result, bool):
            error = f"Validator function must return bool (got {type(result).__name__})"  # type: ignore[unreachable]
            return False, error

        if not result:
            error = self.error_message or "Custom validation failed"
            return False, error

        return True, None


# Factory for creating validators from schema definitions
class ValidatorFactory:
    """Factory for creating validator instances from schema definitions."""

    @staticmethod
    def create_validator(validator_config: dict[str, Any]) -> BaseValidator:
        """
        Create a validator from configuration.

        Args:
            validator_config: Validator configuration dict

        Returns:
            Validator instance

        Raises:
            ValueError: If validator type is unknown
        """
        validator_type = validator_config.get("type")
        error_message = validator_config.get("error_message")

        if validator_type in ("min_length", "max_length"):
            return LengthValidator(
                min_length=validator_config.get("min_value"),
                max_length=validator_config.get("max_value"),
                error_message=error_message,
            )

        if validator_type in ("min_value", "max_value", "range"):
            return RangeValidator(
                min_value=validator_config.get("min_value"),
                max_value=validator_config.get("max_value"),
                error_message=error_message,
            )

        if validator_type == "regex":
            pattern = validator_config.get("pattern")
            if not pattern:
                msg = "Regex validator requires 'pattern' parameter"
                raise ValueError(msg)
            return RegexValidator(pattern=pattern, error_message=error_message)

        if validator_type == "enum":
            allowed_values = validator_config.get("allowed_values")
            if not allowed_values:
                msg = "Enum validator requires 'allowed_values' parameter"
                raise ValueError(msg)
            return EnumValidator(allowed_values=allowed_values, error_message=error_message)

        if validator_type == "email":
            return EmailValidator(error_message=error_message)

        if validator_type == "url":
            return URLValidator(error_message=error_message)

        if validator_type == "uuid":
            return UUIDValidator(error_message=error_message)

        if validator_type == "date":
            date_format = validator_config.get("format", "%Y-%m-%d")
            return DateValidator(format=date_format, error_message=error_message)

        if validator_type == "datetime":
            datetime_format = validator_config.get("format", "%Y-%m-%dT%H:%M:%S")
            return DateTimeValidator(format=datetime_format, error_message=error_message)

        msg = f"Unknown validator type: {validator_type}"
        raise ValueError(msg)
