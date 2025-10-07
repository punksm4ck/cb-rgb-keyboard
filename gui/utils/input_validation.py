#!/usr/bin/env python3
"""Enhanced Input Validation utilities for RGB Controller with OSIRIS optimization"""

import re
import json
from typing import Any, Union, List, Dict, Optional, Tuple
from pathlib import Path

from ..core.rgb_color import RGBColor, Colors, parse_color_string
from ..core.exceptions import ValidationError, ColorError


class SafeInputValidation:
    """
    Comprehensive input validation with enhanced security and type checking

    Provides validation methods for all types of user input in the RGB Controller,
    with special attention to OSIRIS hardware constraints and security considerations.
    """

    # Validation patterns
    HEX_COLOR_PATTERN = re.compile(r'^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
    FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')
    SETTING_KEY_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')

    # Safe ranges
    BRIGHTNESS_RANGE = (0, 100)
    SPEED_RANGE = (1, 10)
    ZONE_COUNT_RANGE = (1, 16)

    # Maximum string lengths to prevent DoS
    MAX_STRING_LENGTH = 1000
    MAX_FILENAME_LENGTH = 255
    MAX_JSON_SIZE = 10 * 1024 * 1024  # 10MB

    @classmethod
    def validate_integer(cls, value: Any, min_val: int = None, max_val: int = None,
                        default: Optional[int] = None) -> Optional[int]:
        """
        Validate and convert value to integer within specified range

        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            default: Default value if validation fails

        Returns:
            Optional[int]: Validated integer or default

        Raises:
            ValidationError: If validation fails and no default provided
        """
        try:
            if value is None:
                if default is not None:
                    return default
                raise ValidationError("Value cannot be None", field_name="integer_value")

            # Convert to int
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    if default is not None:
                        return default
                    raise ValidationError("Empty string cannot be converted to integer")

            int_value = int(value)

            # Check range
            if min_val is not None and int_value < min_val:
                if default is not None:
                    return default
                raise ValidationError(f"Value {int_value} is below minimum {min_val}",
                                    field_name="integer_value", invalid_value=int_value)

            if max_val is not None and int_value > max_val:
                if default is not None:
                    return default
                raise ValidationError(f"Value {int_value} is above maximum {max_val}",
                                    field_name="integer_value", invalid_value=int_value)

            return int_value

        except (ValueError, TypeError) as e:
            if default is not None:
                return default
            raise ValidationError(f"Cannot convert to integer: {e}",
                                field_name="integer_value", invalid_value=value)

    @classmethod
    def validate_float(cls, value: Any, min_val: float = None, max_val: float = None,
                      default: Optional[float] = None) -> Optional[float]:
        """
        Validate and convert value to float within specified range

        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            default: Default value if validation fails

        Returns:
            Optional[float]: Validated float or default
        """
        try:
            if value is None:
                if default is not None:
                    return default
                raise ValidationError("Value cannot be None", field_name="float_value")

            # Convert to float
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    if default is not None:
                        return default
                    raise ValidationError("Empty string cannot be converted to float")

            float_value = float(value)

            # Check for special values
            if not isinstance(float_value, (int, float)) or float_value != float_value:  # NaN check
                if default is not None:
                    return default
                raise ValidationError("Invalid float value (NaN)")

            # Check range
            if min_val is not None and float_value < min_val:
                if default is not None:
                    return default
                raise ValidationError(f"Value {float_value} is below minimum {min_val}",
                                    field_name="float_value", invalid_value=float_value)

            if max_val is not None and float_value > max_val:
                if default is not None:
                    return default
                raise ValidationError(f"Value {float_value} is above maximum {max_val}",
                                    field_name="float_value", invalid_value=float_value)

            return float_value

        except (ValueError, TypeError) as e:
            if default is not None:
                return default
            raise ValidationError(f"Cannot convert to float: {e}",
                                field_name="float_value", invalid_value=value)

    @classmethod
    def validate_string(cls, value: Any, max_length: int = None, min_length: int = 0,
                       pattern: Optional[re.Pattern] = None, allowed_chars: Optional[str] = None,
                       default: Optional[str] = None) -> Optional[str]:
        """
        Validate string with comprehensive security checks

        Args:
            value: Value to validate
            max_length: Maximum string length
            min_length: Minimum string length
            pattern: Regex pattern to match
            allowed_chars: Set of allowed characters
            default: Default value if validation fails

        Returns:
            Optional[str]: Validated string or default
        """
        try:
            if value is None:
                if default is not None:
                    return default
                raise ValidationError("Value cannot be None", field_name="string_value")

            # Convert to string and apply security limits
            str_value = str(value)

            if len(str_value) > (max_length or cls.MAX_STRING_LENGTH):
                if default is not None:
                    return default
                raise ValidationError(f"String too long: {len(str_value)} > {max_length or cls.MAX_STRING_LENGTH}",
                                    field_name="string_value", invalid_value=f"{str_value[:50]}...")

            if len(str_value) < min_length:
                if default is not None:
                    return default
                raise ValidationError(f"String too short: {len(str_value)} < {min_length}",
                                    field_name="string_value", invalid_value=str_value)

            # Pattern validation
            if pattern and not pattern.match(str_value):
                if default is not None:
                    return default
                raise ValidationError(f"String does not match required pattern",
                                    field_name="string_value", invalid_value=str_value)

            # Character whitelist validation
            if allowed_chars:
                invalid_chars = set(str_value) - set(allowed_chars)
                if invalid_chars:
                    if default is not None:
                        return default
                    raise ValidationError(f"String contains invalid characters: {invalid_chars}",
                                        field_name="string_value", invalid_value=str_value)

            return str_value

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            if default is not None:
                return default
            raise ValidationError(f"String validation failed: {e}",
                                field_name="string_value", invalid_value=value)

    @classmethod
    def validate_color(cls, value: Any, default: Optional[RGBColor] = None) -> Optional[RGBColor]:
        """
        Validate color input in various formats

        Args:
            value: Color value (hex string, RGB dict, tuple, RGBColor instance)
            default: Default color if validation fails

        Returns:
            Optional[RGBColor]: Validated color or default

        Raises:
            ColorError: If validation fails and no default provided
        """
        try:
            if value is None:
                if default is not None:
                    return default
                raise ColorError("Color value cannot be None", color_data=value)

            # Handle different input types
            if isinstance(value, RGBColor):
                if not value.is_valid():
                    if default is not None:
                        return default
                    raise ColorError("Invalid RGBColor instance", color_data=value)
                return value

            elif isinstance(value, str):
                # Validate hex color format
                if not cls.HEX_COLOR_PATTERN.match(value):
                    if default is not None:
                        return default
                    raise ColorError("Invalid hex color format", color_data=value, color_format="hex")
                return RGBColor.from_hex(value)

            elif isinstance(value, dict):
                return RGBColor.from_dict(value)

            elif isinstance(value, (tuple, list)):
                if len(value) != 3:
                    if default is not None:
                        return default
                    raise ColorError("RGB tuple must have exactly 3 values", color_data=value)
                return RGBColor.from_tuple(value)

            else:
                # Try parsing as color name or other format
                try:
                    return parse_color_string(str(value))
                except Exception:
                    if default is not None:
                        return default
                    raise ColorError("Unsupported color format", color_data=value)

        except ColorError:
            raise
        except Exception as e:
            if default is not None:
                return default
            raise ColorError(f"Color validation failed: {e}", color_data=value)

    @classmethod
    def validate_brightness(cls, value: Any, default: Optional[int] = None) -> Optional[int]:
        """
        Validate brightness value (0-100)

        Args:
            value: Brightness value to validate
            default: Default value if validation fails

        Returns:
            Optional[int]: Validated brightness or default
        """
        return cls.validate_integer(value, *cls.BRIGHTNESS_RANGE, default=default)

    @classmethod
    def validate_speed(cls, value: Any, default: Optional[int] = None) -> Optional[int]:
        """
        Validate speed value (1-10)

        Args:
            value: Speed value to validate
            default: Default value if validation fails

        Returns:
            Optional[int]: Validated speed or default
        """
        return cls.validate_integer(value, *cls.SPEED_RANGE, default=default)

    @classmethod
    def validate_filename(cls, value: Any, allow_path: bool = False,
                         default: Optional[str] = None) -> Optional[str]:
        """
        Validate filename with security considerations

        Args:
            value: Filename to validate
            allow_path: Whether to allow path separators
            default: Default value if validation fails

        Returns:
            Optional[str]: Validated filename or default
        """
        try:
            if value is None:
                if default is not None:
                    return default
                raise ValidationError("Filename cannot be None", field_name="filename")

            filename = str(value).strip()

            # Basic security checks
            if not filename:
                if default is not None:
                    return default
                raise ValidationError("Filename cannot be empty", field_name="filename")

            if len(filename) > cls.MAX_FILENAME_LENGTH:
                if default is not None:
                    return default
                raise ValidationError(f"Filename too long: {len(filename)} > {cls.MAX_FILENAME_LENGTH}",
                                    field_name="filename", invalid_value=filename)

            # Security: prevent directory traversal
            if not allow_path:
                if '..' in filename or '/' in filename or '\\' in filename:
                    if default is not None:
                        return default
                    raise ValidationError("Filename contains path separators",
                                        field_name="filename", invalid_value=filename)

            # Character validation
            if not allow_path and not cls.FILENAME_PATTERN.match(filename):
                if default is not None:
                    return default
                raise ValidationError("Filename contains invalid characters",
                                    field_name="filename", invalid_value=filename)

            # Prevent dangerous filenames
            dangerous_names = ['con', 'prn', 'aux', 'nul'] + [f'com{i}' for i in range(1,10)] + [f'lpt{i}' for i in range(1,10)]
            if filename.lower().split('.')[0] in dangerous_names:
                if default is not None:
                    return default
                raise ValidationError("Filename is a reserved system name",
                                    field_name="filename", invalid_value=filename)

            return filename

        except ValidationError:
            raise
        except Exception as e:
            if default is not None:
                return default
            raise ValidationError(f"Filename validation failed: {e}",
                                field_name="filename", invalid_value=value)

    @classmethod
    def validate_json_data(cls, value: Any, max_size: int = None,
                          expected_keys: Optional[List[str]] = None,
                          default: Optional[Dict] = None) -> Optional[Dict]:
        """
        Validate JSON data with size and structure checks

        Args:
            value: JSON data (string or dict)
            max_size: Maximum JSON size in bytes
            expected_keys: List of required keys
            default: Default value if validation fails

        Returns:
            Optional[Dict]: Validated JSON data or default
        """
        try:
            if value is None:
                if default is not None:
                    return default
                raise ValidationError("JSON data cannot be None", field_name="json_data")

            # Convert to dict if string
            if isinstance(value, str):
                # Size check
                if len(value.encode('utf-8')) > (max_size or cls.MAX_JSON_SIZE):
                    if default is not None:
                        return default
                    raise ValidationError("JSON data too large", field_name="json_data")

                try:
                    data = json.loads(value)
                except json.JSONDecodeError as e:
                    if default is not None:
                        return default
                    raise ValidationError(f"Invalid JSON format: {e}", field_name="json_data")

            elif isinstance(value, dict):
                data = value
                # Size check for dict
                try:
                    json_str = json.dumps(data)
                    if len(json_str.encode('utf-8')) > (max_size or cls.MAX_JSON_SIZE):
                        if default is not None:
                            return default
                        raise ValidationError("JSON data too large", field_name="json_data")
                except (TypeError, ValueError) as e:
                    if default is not None:
                        return default
                    raise ValidationError(f"Cannot serialize to JSON: {e}", field_name="json_data")

            else:
                if default is not None:
                    return default
                raise ValidationError("JSON data must be string or dict", field_name="json_data")

            # Structure validation
            if expected_keys:
                missing_keys = set(expected_keys) - set(data.keys())
                if missing_keys:
                    if default is not None:
                        return default
                    raise ValidationError(f"Missing required keys: {missing_keys}",
                                        field_name="json_data")

            return data

        except ValidationError:
            raise
        except Exception as e:
            if default is not None:
                return default
            raise ValidationError(f"JSON validation failed: {e}",
                                field_name="json_data", invalid_value=value)

    @classmethod
    def validate_path(cls, value: Any, must_exist: bool = False, must_be_file: bool = False,
                     must_be_dir: bool = False, create_dirs: bool = False,
                     default: Optional[Path] = None) -> Optional[Path]:
        """
        Validate file/directory path with security checks

        Args:
            value: Path to validate
            must_exist: Whether path must exist
            must_be_file: Whether path must be a file
            must_be_dir: Whether path must be a directory
            create_dirs: Whether to create parent directories
            default: Default value if validation fails

        Returns:
            Optional[Path]: Validated path or default
        """
        try:
            if value is None:
                if default is not None:
                    return default
                raise ValidationError("Path cannot be None", field_name="path")

            path = Path(value).resolve()

            # Security: prevent access outside allowed areas (basic check)
            path_str = str(path)
            if '..' in path_str:
                # Allow if it resolves to a safe location
                try:
                    path = path.resolve(strict=False)
                except Exception:
                    if default is not None:
                        return default
                    raise ValidationError("Invalid path with directory traversal",
                                        field_name="path", invalid_value=value)

            # Existence checks
            if must_exist and not path.exists():
                if default is not None:
                    return default
                raise ValidationError("Path does not exist", field_name="path", invalid_value=str(path))

            if must_be_file and path.exists() and not path.is_file():
                if default is not None:
                    return default
                raise ValidationError("Path is not a file", field_name="path", invalid_value=str(path))

            if must_be_dir and path.exists() and not path.is_dir():
                if default is not None:
                    return default
                raise ValidationError("Path is not a directory", field_name="path", invalid_value=str(path))

            # Create parent directories if requested
            if create_dirs and not path.parent.exists():
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    if default is not None:
                        return default
                    raise ValidationError(f"Cannot create parent directories: {e}",
                                        field_name="path", invalid_value=str(path))

            return path

        except ValidationError:
            raise
        except Exception as e:
            if default is not None:
                return default
            raise ValidationError(f"Path validation failed: {e}",
                                field_name="path", invalid_value=value)

    @classmethod
    def validate_color_list(cls, colors: Any, min_count: int = 1, max_count: int = None,
                           default: Optional[List[RGBColor]] = None) -> Optional[List[RGBColor]]:
        """
        Validate list of colors

        Args:
            colors: List of color values
            min_count: Minimum number of colors required
            max_count: Maximum number of colors allowed
            default: Default value if validation fails

        Returns:
            Optional[List[RGBColor]]: Validated color list or default
        """
        try:
            if colors is None:
                if default is not None:
                    return default
                raise ValidationError("Color list cannot be None", field_name="color_list")

            if not isinstance(colors, (list, tuple)):
                if default is not None:
                    return default
                raise ValidationError("Colors must be a list or tuple", field_name="color_list")

            if len(colors) < min_count:
                if default is not None:
                    return default
                raise ValidationError(f"Not enough colors: {len(colors)} < {min_count}",
                                    field_name="color_list")

            if max_count and len(colors) > max_count:
                if default is not None:
                    return default
                raise ValidationError(f"Too many colors: {len(colors)} > {max_count}",
                                    field_name="color_list")

            validated_colors = []
            for i, color in enumerate(colors):
                try:
                    validated_color = cls.validate_color(color)
                    if validated_color is None:
                        raise ColorError(f"Invalid color at index {i}")
                    validated_colors.append(validated_color)
                except Exception as e:
                    if default is not None:
                        return default
                    raise ValidationError(f"Invalid color at index {i}: {e}",
                                        field_name="color_list", invalid_value=color)

            return validated_colors

        except ValidationError:
            raise
        except Exception as e:
            if default is not None:
                return default
            raise ValidationError(f"Color list validation failed: {e}",
                                field_name="color_list", invalid_value=colors)

    @classmethod
    def sanitize_input_for_display(cls, value: Any, max_display_length: int = 100) -> str:
        """
        Sanitize input for safe display in logs and error messages

        Args:
            value: Value to sanitize
            max_display_length: Maximum length for display

        Returns:
            str: Sanitized string safe for display
        """
        try:
            if value is None:
                return "<None>"

            # Convert to string
            str_value = str(value)

            # Truncate if too long
            if len(str_value) > max_display_length:
                str_value = str_value[:max_display_length] + "..."

            # Remove potentially dangerous characters for display
            # Replace control characters and other problematic chars
            safe_chars = []
            for char in str_value:
                if ord(char) < 32 or ord(char) > 126:
                    if char in ['\n', '\t', '\r']:
                        safe_chars.append(' ')  # Replace with space
                    else:
                        safe_chars.append('?')  # Replace with question mark
                else:
                    safe_chars.append(char)

            return ''.join(safe_chars)

        except Exception:
            return "<Error displaying value>"

    @classmethod
    def validate_setting_key(cls, key: Any, default: Optional[str] = None) -> Optional[str]:
        """
        Validate setting key name

        Args:
            key: Setting key to validate
            default: Default value if validation fails

        Returns:
            Optional[str]: Validated setting key or default
        """
        try:
            if key is None:
                if default is not None:
                    return default
                raise ValidationError("Setting key cannot be None", field_name="setting_key")

            key_str = str(key).strip()

            if not key_str:
                if default is not None:
                    return default
                raise ValidationError("Setting key cannot be empty", field_name="setting_key")

            if not cls.SETTING_KEY_PATTERN.match(key_str):
                if default is not None:
                    return default
                raise ValidationError("Invalid setting key format (must be alphanumeric with underscores)",
                                    field_name="setting_key", invalid_value=key_str)

            return key_str

        except ValidationError:
            raise
        except Exception as e:
            if default is not None:
                return default
            raise ValidationError(f"Setting key validation failed: {e}",
                                field_name="setting_key", invalid_value=key)

    @classmethod
    def validate_osiris_specific(cls, operation: str, value: Any, **kwargs) -> Any:
        """
        OSIRIS-specific validation for single-zone white backlight constraints

        Args:
            operation: Type of operation being validated
            value: Value to validate
            **kwargs: Additional validation parameters

        Returns:
            Any: Validated value optimized for OSIRIS hardware
        """
        try:
            if operation == "brightness_conversion":
                # For OSIRIS, ensure brightness is optimized for white backlight
                if isinstance(value, (list, tuple)) and len(value) > 1:
                    # Multiple colors - convert to optimal brightness
                    from ..core.rgb_color import get_optimal_osiris_brightness
                    colors = cls.validate_color_list(value)
                    if colors:
                        optimal_brightness = get_optimal_osiris_brightness(colors)
                        return optimal_brightness

                return cls.validate_brightness(value)

            elif operation == "zone_colors":
                # For OSIRIS single-zone, validate but prepare for brightness conversion
                colors = cls.validate_color_list(value)
                if colors and len(colors) > 1:
                    # Log that multiple colors will be averaged for OSIRIS
                    import logging
                    logger = logging.getLogger("osiris_validation")
                    logger.info(f"OSIRIS: {len(colors)} zone colors will be averaged for single-zone hardware")

                return colors

            elif operation == "effect_parameters":
                # Validate effect parameters with OSIRIS constraints
                if 'color' in kwargs:
                    kwargs['color'] = cls.validate_color(kwargs['color'])
                if 'brightness' in kwargs:
                    kwargs['brightness'] = cls.validate_brightness(kwargs['brightness'])
                if 'speed' in kwargs:
                    kwargs['speed'] = cls.validate_speed(kwargs['speed'])

                return kwargs

            else:
                # Standard validation for other operations
                return value

        except Exception as e:
            raise ValidationError(f"OSIRIS-specific validation failed for {operation}: {e}",
                                field_name=operation, invalid_value=value)

    @classmethod
    def validate_hardware_method(cls, method: str, default: Optional[str] = None) -> Optional[str]:
        """
        Validate hardware control method

        Args:
            method: Hardware method to validate
            default: Default method if validation fails

        Returns:
            Optional[str]: Validated method or default
        """
        valid_methods = ['ec_direct', 'ectool', 'none']

        try:
            if method is None:
                if default is not None:
                    return default
                raise ValidationError("Hardware method cannot be None", field_name="hardware_method")

            method_str = str(method).lower().strip()

            if method_str not in valid_methods:
                if default is not None:
                    return default
                raise ValidationError(f"Invalid hardware method: {method_str}. Must be one of: {valid_methods}",
                                    field_name="hardware_method", invalid_value=method_str)

            return method_str

        except ValidationError:
            raise
        except Exception as e:
            if default is not None:
                return default
            raise ValidationError(f"Hardware method validation failed: {e}",
                                field_name="hardware_method", invalid_value=method)

    @classmethod
    def validate_effect_name(cls, name: str, available_effects: Optional[List[str]] = None,
                           default: Optional[str] = None) -> Optional[str]:
        """
        Validate effect name

        Args:
            name: Effect name to validate
            available_effects: List of available effect names
            default: Default effect name if validation fails

        Returns:
            Optional[str]: Validated effect name or default
        """
        try:
            if name is None:
                if default is not None:
                    return default
                raise ValidationError("Effect name cannot be None", field_name="effect_name")

            name_str = cls.validate_string(name, max_length=100)

            if available_effects and name_str not in available_effects:
                if default is not None:
                    return default
                raise ValidationError(f"Effect '{name_str}' is not available. Available effects: {available_effects}",
                                    field_name="effect_name", invalid_value=name_str)

            return name_str

        except ValidationError:
            raise
        except Exception as e:
            if default is not None:
                return default
            raise ValidationError(f"Effect name validation failed: {e}",
                                field_name="effect_name", invalid_value=name)


# Convenience validation functions with safe defaults
def validate_brightness_safe(value: Any) -> int:
    """Safe brightness validation with default fallback (100%)"""
    return SafeInputValidation.validate_brightness(value, default=100)


def validate_color_safe(value: Any) -> RGBColor:
    """Safe color validation with default fallback (white)"""
    return SafeInputValidation.validate_color(value, default=RGBColor(255, 255, 255))


def validate_string_safe(value: Any, max_length: int = 1000) -> str:
    """Safe string validation with default fallback (empty string)"""
    return SafeInputValidation.validate_string(value, max_length=max_length, default="")


def validate_integer_safe(value: Any, min_val: int = None, max_val: int = None, fallback: int = 0) -> int:
    """Safe integer validation with fallback"""
    return SafeInputValidation.validate_integer(value, min_val, max_val, default=fallback)


def validate_filename_safe(value: Any) -> str:
    """Safe filename validation with timestamp fallback"""
    import time
    fallback_name = f"untitled_{int(time.time())}"
    return SafeInputValidation.validate_filename(value, default=fallback_name)


def validate_json_safe(value: Any) -> Dict[str, Any]:
    """Safe JSON validation with empty dict fallback"""
    return SafeInputValidation.validate_json_data(value, default={})


def validate_color_list_safe(colors: Any, min_count: int = 1) -> List[RGBColor]:
    """Safe color list validation with white color fallback"""
    fallback_colors = [RGBColor(255, 255, 255)] * min_count
    return SafeInputValidation.validate_color_list(colors, min_count=min_count, default=fallback_colors)


def sanitize_for_logging(value: Any, max_length: int = 200) -> str:
    """Sanitize value for safe logging"""
    return SafeInputValidation.sanitize_input_for_display(value, max_length)


def is_valid_hex_color(color_str: str) -> bool:
    """Quick check if string is valid hex color"""
    try:
        return bool(SafeInputValidation.HEX_COLOR_PATTERN.match(str(color_str)))
    except:
        return False


def is_valid_brightness(value: Any) -> bool:
    """Quick check if value is valid brightness"""
    try:
        brightness = SafeInputValidation.validate_brightness(value)
        return brightness is not None
    except:
        return False


def is_safe_filename(filename: str) -> bool:
    """Quick check if filename is safe"""
    try:
        validated = SafeInputValidation.validate_filename(filename)
        return validated is not None
    except:
        return False


# OSIRIS-specific validation shortcuts
def validate_osiris_brightness_conversion(colors: List[Any]) -> int:
    """Convert multiple colors to OSIRIS-optimal brightness"""
    return SafeInputValidation.validate_osiris_specific("brightness_conversion", colors)


def validate_osiris_zone_colors(colors: List[Any]) -> List[RGBColor]:
    """Validate zone colors for OSIRIS single-zone hardware"""
    return SafeInputValidation.validate_osiris_specific("zone_colors", colors)


# Security validation helpers
def validate_user_input_secure(value: Any, input_type: str = "string", **kwargs) -> Any:
    """
    Secure validation dispatcher for user inputs

    Args:
        value: Value to validate
        input_type: Type of input expected
        **kwargs: Additional validation parameters

    Returns:
        Any: Validated value with security checks applied
    """
    if input_type == "string":
        return SafeInputValidation.validate_string(value, **kwargs)
    elif input_type == "integer":
        return SafeInputValidation.validate_integer(value, **kwargs)
    elif input_type == "float":
        return SafeInputValidation.validate_float(value, **kwargs)
    elif input_type == "color":
        return SafeInputValidation.validate_color(value, **kwargs)
    elif input_type == "filename":
        return SafeInputValidation.validate_filename(value, **kwargs)
    elif input_type == "json":
        return SafeInputValidation.validate_json_data(value, **kwargs)
    elif input_type == "path":
        return SafeInputValidation.validate_path(value, **kwargs)
    else:
        raise ValidationError(f"Unknown input type for validation: {input_type}")


# Export all validation utilities
__all__ = [
    'SafeInputValidation',
    'validate_brightness_safe',
    'validate_color_safe',
    'validate_string_safe',
    'validate_integer_safe',
    'validate_filename_safe',
    'validate_json_safe',
    'validate_color_list_safe',
    'sanitize_for_logging',
    'is_valid_hex_color',
    'is_valid_brightness',
    'is_safe_filename',
    'validate_osiris_brightness_conversion',
    'validate_osiris_zone_colors',
    'validate_user_input_secure'
]
