#!/usr/bin/env python3
"""Enhanced RGB Color class with OSIRIS optimization and comprehensive validation"""

import re
import colorsys
import math
from typing import Union, Tuple, Dict, Any, Optional, List
import json


class RGBColor:
    """
    Enhanced RGB Color class with OSIRIS hardware optimization and comprehensive validation

    Supports multiple color formats, validation, conversion utilities, and OSIRIS-specific
    brightness calculation for single-zone white backlight hardware.
    """

    # Color validation constants
    MIN_VALUE = 0
    MAX_VALUE = 255
    HEX_PATTERN = re.compile(r'^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')

    # OSIRIS luminance coefficients (ITU-R BT.709 standard)
    LUMINANCE_RED = 0.2126
    LUMINANCE_GREEN = 0.7152
    LUMINANCE_BLUE = 0.0722

    # Alternative luminance coefficients (NTSC standard - more perceptual)
    NTSC_LUMINANCE_RED = 0.299
    NTSC_LUMINANCE_GREEN = 0.587
    NTSC_LUMINANCE_BLUE = 0.114

    def __init__(self, r: int = 0, g: int = 0, b: int = 0):
        """
        Initialize RGB color with validation

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)

        Raises:
            ValueError: If color values are invalid
        """
        self._r = self._validate_component(r, "red")
        self._g = self._validate_component(g, "green")
        self._b = self._validate_component(b, "blue")

    @property
    def r(self) -> int:
        """Red component (0-255)"""
        return self._r

    @r.setter
    def r(self, value: int):
        """Set red component with validation"""
        self._r = self._validate_component(value, "red")

    @property
    def g(self) -> int:
        """Green component (0-255)"""
        return self._g

    @g.setter
    def g(self, value: int):
        """Set green component with validation"""
        self._g = self._validate_component(value, "green")

    @property
    def b(self) -> int:
        """Blue component (0-255)"""
        return self._b

    @b.setter
    def b(self, value: int):
        """Set blue component with validation"""
        self._b = self._validate_component(value, "blue")

    def _validate_component(self, value: Union[int, float], component_name: str = "component") -> int:
        """
        Validate a single color component

        Args:
            value: Component value to validate
            component_name: Name of component for error messages

        Returns:
            int: Validated component value

        Raises:
            ValueError: If component value is invalid
        """
        try:
            # Convert to int if float
            if isinstance(value, float):
                value = int(round(value))

            # Type validation
            if not isinstance(value, int):
                raise TypeError(f"{component_name} must be numeric")

            # Range validation
            if not (self.MIN_VALUE <= value <= self.MAX_VALUE):
                raise ValueError(f"{component_name} must be between {self.MIN_VALUE} and {self.MAX_VALUE}")

            return value

        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid {component_name} component: {e}")

    def is_valid(self) -> bool:
        """
        Check if the current color is valid

        Returns:
            bool: True if color is valid
        """
        try:
            return (
                self.MIN_VALUE <= self._r <= self.MAX_VALUE and
                self.MIN_VALUE <= self._g <= self.MAX_VALUE and
                self.MIN_VALUE <= self._b <= self.MAX_VALUE
            )
        except:
            return False

    def to_hex(self) -> str:
        """
        Convert to hexadecimal color string

        Returns:
            str: Hex color string (e.g., "#FF0000")
        """
        return f"#{self._r:02X}{self._g:02X}{self._b:02X}"

    def to_tuple(self) -> Tuple[int, int, int]:
        """
        Convert to RGB tuple

        Returns:
            Tuple[int, int, int]: RGB tuple
        """
        return (self._r, self._g, self._b)

    def to_dict(self) -> Dict[str, int]:
        """
        Convert to dictionary representation

        Returns:
            Dict[str, int]: Dictionary with r, g, b keys
        """
        return {"r": self._r, "g": self._g, "b": self._b}

    def to_normalized(self) -> Tuple[float, float, float]:
        """
        Convert to normalized RGB values (0.0-1.0)

        Returns:
            Tuple[float, float, float]: Normalized RGB tuple
        """
        return (self._r / 255.0, self._g / 255.0, self._b / 255.0)

    def to_hsv(self) -> Tuple[float, float, float]:
        """
        Convert to HSV color space

        Returns:
            Tuple[float, float, float]: HSV tuple (H: 0-360, S: 0-1, V: 0-1)
        """
        r_norm, g_norm, b_norm = self.to_normalized()
        h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
        return (h * 360, s, v)  # Convert hue to degrees

    def to_hsl(self) -> Tuple[float, float, float]:
        """
        Convert to HSL color space

        Returns:
            Tuple[float, float, float]: HSL tuple (H: 0-360, S: 0-1, L: 0-1)
        """
        r_norm, g_norm, b_norm = self.to_normalized()
        h, l, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)  # FIXED: was l_norm, s_norm
        return (h * 360, s, l)  # Convert hue to degrees

    def to_osiris_brightness(self, method: str = "ntsc") -> int:
        """
        Convert RGB to perceived brightness for OSIRIS single-zone white backlight

        Uses perceptual luminance formulas to convert RGB colors to appropriate
        brightness levels for white-only backlights.

        Args:
            method: Luminance calculation method ("ntsc", "itu", "average", "max")

        Returns:
            int: Brightness level (0-100)
        """
        if method == "ntsc":
            # NTSC standard - more perceptually accurate
            luminance = (
                self.NTSC_LUMINANCE_RED * self._r +
                self.NTSC_LUMINANCE_GREEN * self._g +
                self.NTSC_LUMINANCE_BLUE * self._b
            )
        elif method == "itu":
            # ITU-R BT.709 standard
            luminance = (
                self.LUMINANCE_RED * self._r +
                self.LUMINANCE_GREEN * self._g +
                self.LUMINANCE_BLUE * self._b
            )
        elif method == "average":
            # Simple average
            luminance = (self._r + self._g + self._b) / 3
        elif method == "max":
            # Maximum component
            luminance = max(self._r, self._g, self._b)
        else:
            # Default to NTSC
            luminance = (
                self.NTSC_LUMINANCE_RED * self._r +
                self.NTSC_LUMINANCE_GREEN * self._g +
                self.NTSC_LUMINANCE_BLUE * self._b
            )

        # Convert to percentage (0-100)
        brightness = int(round(luminance / 2.55))

        # Ensure very dim colors don't become 0 (unless they are actually black)
        if brightness == 0 and (self._r > 0 or self._g > 0 or self._b > 0):
            brightness = 1

        return max(0, min(100, brightness))

    def get_perceived_brightness(self) -> float:
        """
        Get perceived brightness using NTSC luminance formula

        Returns:
            float: Perceived brightness (0.0-1.0)
        """
        return (
            self.NTSC_LUMINANCE_RED * (self._r / 255.0) +
            self.NTSC_LUMINANCE_GREEN * (self._g / 255.0) +
            self.NTSC_LUMINANCE_BLUE * (self._b / 255.0)
        )

    def is_dark(self, threshold: float = 0.3) -> bool:
        """
        Check if color is considered dark

        Args:
            threshold: Brightness threshold (0.0-1.0)

        Returns:
            bool: True if color is dark
        """
        return self.get_perceived_brightness() < threshold

    def is_light(self, threshold: float = 0.7) -> bool:
        """
        Check if color is considered light

        Args:
            threshold: Brightness threshold (0.0-1.0)

        Returns:
            bool: True if color is light
        """
        return self.get_perceived_brightness() > threshold

    def darken(self, factor: float = 0.8) -> 'RGBColor':
        """
        Create a darker version of this color

        Args:
            factor: Darkening factor (0.0-1.0, where 0 is black)

        Returns:
            RGBColor: Darkened color
        """
        factor = max(0.0, min(1.0, factor))
        return RGBColor(
            int(self._r * factor),
            int(self._g * factor),
            int(self._b * factor)
        )

    def lighten(self, factor: float = 0.2) -> 'RGBColor':
        """
        Create a lighter version of this color

        Args:
            factor: Lightening factor (0.0-1.0, where 1 adds maximum brightness)

        Returns:
            RGBColor: Lightened color
        """
        factor = max(0.0, min(1.0, factor))
        return RGBColor(
            min(255, int(self._r + (255 - self._r) * factor)),
            min(255, int(self._g + (255 - self._g) * factor)),
            min(255, int(self._b + (255 - self._b) * factor))
        )

    def adjust_brightness(self, brightness: float) -> 'RGBColor':
        """
        Adjust color brightness while preserving hue and saturation

        Args:
            brightness: Target brightness (0.0-1.0)

        Returns:
            RGBColor: Brightness-adjusted color
        """
        h, s, v = self.to_hsv()
        brightness = max(0.0, min(1.0, brightness))

        # Convert back to RGB
        r_norm, g_norm, b_norm = colorsys.hsv_to_rgb(h / 360.0, s, brightness)

        return RGBColor(
            int(round(r_norm * 255)),
            int(round(g_norm * 255)),
            int(round(b_norm * 255))
        )

    def blend_with(self, other: 'RGBColor', ratio: float = 0.5) -> 'RGBColor':
        """
        Blend this color with another color

        Args:
            other: Color to blend with
            ratio: Blend ratio (0.0 = this color, 1.0 = other color)

        Returns:
            RGBColor: Blended color
        """
        if not isinstance(other, RGBColor):
            raise TypeError("Can only blend with another RGBColor")

        ratio = max(0.0, min(1.0, ratio))
        inv_ratio = 1.0 - ratio

        return RGBColor(
            int(round(self._r * inv_ratio + other._r * ratio)),
            int(round(self._g * inv_ratio + other._g * ratio)),
            int(round(self._b * inv_ratio + other._b * ratio))
        )

    def distance_to(self, other: 'RGBColor') -> float:
        """
        Calculate Euclidean distance to another color

        Args:
            other: Color to measure distance to

        Returns:
            float: Color distance (0.0-441.67)
        """
        if not isinstance(other, RGBColor):
            raise TypeError("Can only calculate distance to another RGBColor")

        return math.sqrt(
            (self._r - other._r) ** 2 +
            (self._g - other._g) ** 2 +
            (self._b - other._b) ** 2
        )

    def is_similar_to(self, other: 'RGBColor', tolerance: float = 20.0) -> bool:
        """
        Check if this color is similar to another color

        Args:
            other: Color to compare with
            tolerance: Maximum distance for colors to be considered similar

        Returns:
            bool: True if colors are similar
        """
        return self.distance_to(other) <= tolerance

    def get_complementary(self) -> 'RGBColor':
        """
        Get complementary color (opposite on color wheel)

        Returns:
            RGBColor: Complementary color
        """
        return RGBColor(255 - self._r, 255 - self._g, 255 - self._b)

    def get_contrasting_color(self) -> 'RGBColor':
        """
        Get a color that contrasts well with this color (black or white)

        Returns:
            RGBColor: Contrasting color (black or white)
        """
        if self.is_light():
            return RGBColor(0, 0, 0)  # Black for light colors
        else:
            return RGBColor(255, 255, 255)  # White for dark colors

    @classmethod
    def from_hex(cls, hex_color: str) -> 'RGBColor':
        """
        Create RGBColor from hexadecimal string

        Args:
            hex_color: Hex color string (e.g., "#FF0000" or "FF0000" or "#F00")

        Returns:
            RGBColor: Color object

        Raises:
            ValueError: If hex string is invalid
        """
        if not isinstance(hex_color, str):
            raise ValueError("Hex color must be a string")

        hex_color = hex_color.strip()

        if not cls.HEX_PATTERN.match(hex_color):
            raise ValueError(f"Invalid hex color format: {hex_color}")

        # Remove # if present
        hex_color = hex_color.lstrip('#')

        # Expand 3-character hex to 6-character
        if len(hex_color) == 3:
            hex_color = ''.join(c * 2 for c in hex_color)

        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return cls(r, g, b)
        except ValueError as e:
            raise ValueError(f"Invalid hex color: {hex_color}") from e

    @classmethod
    def from_dict(cls, color_dict: Dict[str, Union[int, float]]) -> 'RGBColor':
        """
        Create RGBColor from dictionary

        Args:
            color_dict: Dictionary with 'r', 'g', 'b' keys

        Returns:
            RGBColor: Color object

        Raises:
            ValueError: If dictionary is invalid
        """
        if not isinstance(color_dict, dict):
            raise ValueError("Color data must be a dictionary")

        required_keys = {'r', 'g', 'b'}
        if not required_keys.issubset(color_dict.keys()):
            raise ValueError(f"Color dictionary must contain keys: {required_keys}")

        try:
            return cls(
                int(color_dict['r']),
                int(color_dict['g']),
                int(color_dict['b'])
            )
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid color dictionary values: {e}")

    @classmethod
    def from_tuple(cls, rgb_tuple: Tuple[Union[int, float], Union[int, float], Union[int, float]]) -> 'RGBColor':
        """
        Create RGBColor from RGB tuple

        Args:
            rgb_tuple: RGB tuple (r, g, b)

        Returns:
            RGBColor: Color object

        Raises:
            ValueError: If tuple is invalid
        """
        if not isinstance(rgb_tuple, (tuple, list)) or len(rgb_tuple) != 3:
            raise ValueError("RGB tuple must contain exactly 3 values")

        return cls(rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])

    @classmethod
    def from_hsv(cls, h: float, s: float, v: float) -> 'RGBColor':
        """
        Create RGBColor from HSV values

        Args:
            h: Hue (0-360 degrees)
            s: Saturation (0.0-1.0)
            v: Value/Brightness (0.0-1.0)

        Returns:
            RGBColor: Color object
        """
        # Normalize hue to 0-1 range
        h_norm = (h % 360) / 360.0
        s = max(0.0, min(1.0, s))
        v = max(0.0, min(1.0, v))

        r_norm, g_norm, b_norm = colorsys.hsv_to_rgb(h_norm, s, v)

        return cls(
            int(round(r_norm * 255)),
            int(round(g_norm * 255)),
            int(round(b_norm * 255))
        )

    @classmethod
    def from_brightness(cls, brightness: int, color_temperature: str = "warm") -> 'RGBColor':
        """
        Create RGBColor representing white light at specified brightness
        Useful for OSIRIS hardware brightness conversion

        Args:
            brightness: Brightness level (0-100)
            color_temperature: "warm", "neutral", or "cool"

        Returns:
            RGBColor: White color at specified brightness
        """
        brightness = max(0, min(100, brightness))
        value = int(round(brightness * 2.55))  # Convert 0-100 to 0-255

        # Color temperature adjustments
        if color_temperature == "warm":
            return cls(value, int(value * 0.9), int(value * 0.7))  # Warm white
        elif color_temperature == "cool":
            return cls(int(value * 0.8), int(value * 0.9), value)  # Cool white
        else:  # neutral
            return cls(value, value, value)  # Pure white

    @classmethod
    def interpolate(cls, color1: 'RGBColor', color2: 'RGBColor', steps: int) -> List['RGBColor']:
        """
        Generate interpolated colors between two colors

        Args:
            color1: Starting color
            color2: Ending color
            steps: Number of interpolation steps

        Returns:
            List[RGBColor]: List of interpolated colors
        """
        if steps < 2:
            raise ValueError("Steps must be at least 2")

        colors = []
        for i in range(steps):
            ratio = i / (steps - 1)
            interpolated = color1.blend_with(color2, ratio)
            colors.append(interpolated)

        return colors

    def __str__(self) -> str:
        """String representation"""
        return f"RGBColor(r={self._r}, g={self._g}, b={self._b})"

    def __repr__(self) -> str:
        """Developer representation"""
        return f"RGBColor({self._r}, {self._g}, {self._b})"

    def __eq__(self, other) -> bool:
        """Equality comparison"""
        if not isinstance(other, RGBColor):
            return False
        return self._r == other._r and self._g == other._g and self._b == other._b

    def __ne__(self, other) -> bool:
        """Inequality comparison"""
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Hash for use in sets/dictionaries"""
        return hash((self._r, self._g, self._b))

    def __add__(self, other) -> 'RGBColor':
        """Add colors (with clamping)"""
        if not isinstance(other, RGBColor):
            raise TypeError("Can only add RGBColor to RGBColor")

        return RGBColor(
            min(255, self._r + other._r),
            min(255, self._g + other._g),
            min(255, self._b + other._b)
        )

    def __sub__(self, other) -> 'RGBColor':
        """Subtract colors (with clamping)"""
        if not isinstance(other, RGBColor):
            raise TypeError("Can only subtract RGBColor from RGBColor")

        return RGBColor(
            max(0, self._r - other._r),
            max(0, self._g - other._g),
            max(0, self._b - other._b)
        )

    def __mul__(self, factor) -> 'RGBColor':
        """Multiply color by scalar factor (with clamping)"""
        if not isinstance(factor, (int, float)):
            raise TypeError("Can only multiply RGBColor by numeric factor")

        return RGBColor(
            min(255, max(0, int(self._r * factor))),
            min(255, max(0, int(self._g * factor))),
            min(255, max(0, int(self._b * factor)))
        )

    def __rmul__(self, factor) -> 'RGBColor':
        """Right multiply (factor * color)"""
        return self.__mul__(factor)

    def __truediv__(self, divisor) -> 'RGBColor':
        """Divide color by scalar divisor (with clamping)"""
        if not isinstance(divisor, (int, float)):
            raise TypeError("Can only divide RGBColor by numeric divisor")

        if divisor == 0:
            raise ZeroDivisionError("Cannot divide color by zero")

        return RGBColor(
            min(255, max(0, int(self._r / divisor))),
            min(255, max(0, int(self._g / divisor))),
            min(255, max(0, int(self._b / divisor)))
        )

    def copy(self) -> 'RGBColor':
        """Create a copy of this color"""
        return RGBColor(self._r, self._g, self._b)

    def to_json(self) -> str:
        """Convert color to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'RGBColor':
        """Create RGBColor from JSON string"""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid JSON color data: {e}")


# Predefined color constants for convenience
class Colors:
    """Predefined RGB color constants"""

    # Basic colors
    BLACK = RGBColor(0, 0, 0)
    WHITE = RGBColor(255, 255, 255)
    RED = RGBColor(255, 0, 0)
    GREEN = RGBColor(0, 255, 0)
    BLUE = RGBColor(0, 0, 255)
    YELLOW = RGBColor(255, 255, 0)
    CYAN = RGBColor(0, 255, 255)
    MAGENTA = RGBColor(255, 0, 255)

    # Extended colors
    ORANGE = RGBColor(255, 165, 0)
    PURPLE = RGBColor(128, 0, 128)
    PINK = RGBColor(255, 192, 203)
    BROWN = RGBColor(165, 42, 42)
    GRAY = RGBColor(128, 128, 128)
    DARK_GRAY = RGBColor(64, 64, 64)
    LIGHT_GRAY = RGBColor(192, 192, 192)

    # Warm colors for OSIRIS (good for single-zone white backlight)
    WARM_WHITE = RGBColor(255, 230, 180)
    COOL_WHITE = RGBColor(200, 220, 255)
    SOFT_WHITE = RGBColor(255, 245, 220)

    # Popular gaming colors
    GAMING_RED = RGBColor(220, 20, 60)
    GAMING_BLUE = RGBColor(30, 144, 255)
    GAMING_GREEN = RGBColor(50, 205, 50)
    GAMING_PURPLE = RGBColor(138, 43, 226)

    @classmethod
    def get_all_colors(cls) -> Dict[str, RGBColor]:
        """Get all predefined colors as a dictionary"""
        colors = {}
        for name in dir(cls):
            if not name.startswith('_') and name != 'get_all_colors':
                value = getattr(cls, name)
                if isinstance(value, RGBColor):
                    colors[name] = value
        return colors

    @classmethod
    def get_color_by_name(cls, name: str) -> Optional[RGBColor]:
        """Get a predefined color by name (case-insensitive)"""
        name = name.upper()
        return getattr(cls, name, None)


# Utility functions for color operations
def create_gradient(start_color: RGBColor, end_color: RGBColor, steps: int) -> List[RGBColor]:
    """
    Create a gradient between two colors

    Args:
        start_color: Starting color
        end_color: Ending color
        steps: Number of steps in gradient

    Returns:
        List[RGBColor]: Gradient colors
    """
    return RGBColor.interpolate(start_color, end_color, steps)


def create_rainbow_gradient(steps: int, saturation: float = 1.0, value: float = 1.0) -> List[RGBColor]:
    """
    Create a rainbow gradient

    Args:
        steps: Number of colors in rainbow
        saturation: Color saturation (0.0-1.0)
        value: Color brightness (0.0-1.0)

    Returns:
        List[RGBColor]: Rainbow colors
    """
    colors = []
    for i in range(steps):
        hue = (i / steps) * 360
        color = RGBColor.from_hsv(hue, saturation, value)
        colors.append(color)
    return colors


def parse_color_string(color_str: str) -> RGBColor:
    """
    Parse various color string formats

    Args:
        color_str: Color string (hex, name, rgb tuple as string)

    Returns:
        RGBColor: Parsed color

    Raises:
        ValueError: If color string cannot be parsed
    """
    color_str = color_str.strip()

    # Try hex format first
    if color_str.startswith('#') or all(c in '0123456789ABCDEFabcdef' for c in color_str):
        return RGBColor.from_hex(color_str)

    # Try predefined color name
    predefined = Colors.get_color_by_name(color_str)
    if predefined:
        return predefined

    # Try RGB tuple format: "rgb(255,0,0)" or "(255,0,0)"
    rgb_match = re.match(r'(?:rgb)?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_str, re.IGNORECASE)
    if rgb_match:
        r, g, b = map(int, rgb_match.groups())
        return RGBColor(r, g, b)

    raise ValueError(f"Cannot parse color string: {color_str}")


def validate_color_list(colors: List[Any]) -> List[RGBColor]:
    """
    Validate and convert a list of color representations to RGBColor objects

    Args:
        colors: List of color representations (hex, dict, tuple, RGBColor)

    Returns:
        List[RGBColor]: Validated color list

    Raises:
        ValueError: If any color is invalid
    """
    validated_colors = []

    for i, color in enumerate(colors):
        try:
            if isinstance(color, RGBColor):
                if not color.is_valid():
                    raise ValueError(f"Invalid RGBColor at index {i}")
                validated_colors.append(color)
            elif isinstance(color, str):
                validated_colors.append(parse_color_string(color))
            elif isinstance(color, dict):
                validated_colors.append(RGBColor.from_dict(color))
            elif isinstance(color, (tuple, list)):
                validated_colors.append(RGBColor.from_tuple(color))
            else:
                raise ValueError(f"Unsupported color type: {type(color)}")
        except Exception as e:
            raise ValueError(f"Invalid color at index {i}: {e}")

    return validated_colors


def get_optimal_osiris_brightness(rgb_colors: List[RGBColor], method: str = "weighted_average") -> int:
    """
    Calculate optimal brightness for OSIRIS hardware from multiple RGB colors

    Args:
        rgb_colors: List of RGB colors to convert
        method: Conversion method ("weighted_average", "max", "average")

    Returns:
        int: Optimal brightness level (0-100)
    """
    if not rgb_colors:
        return 0

    if method == "max":
        # Use the brightest color
        brightnesses = [color.to_osiris_brightness() for color in rgb_colors]
        return max(brightnesses)

    elif method == "average":
        # Simple average
        brightnesses = [color.to_osiris_brightness() for color in rgb_colors]
        return int(sum(brightnesses) / len(brightnesses))

    else:  # weighted_average (default)
        # Weight by perceived brightness
        total_weight = 0
        weighted_brightness = 0

        for color in rgb_colors:
            brightness = color.to_osiris_brightness()
            weight = max(1, brightness)  # Prevent zero weight
            weighted_brightness += brightness * weight
            total_weight += weight

        if total_weight > 0:
            return int(weighted_brightness / total_weight)
        else:
            return 0
