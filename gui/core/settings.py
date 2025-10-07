#!/usr/bin/env python3
"""Enhanced Settings Manager with OSIRIS optimization and comprehensive validation"""

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from datetime import datetime

from .constants import default_settings, SETTINGS_FILE, BACKUP_DIR
from .exceptions import ConfigurationError
from .rgb_color import RGBColor


class SettingsManager:
    """
    Enhanced Settings Manager with thread-safe operations, validation, and backup support

    Provides comprehensive settings management for the Enhanced RGB Controller with
    OSIRIS-specific optimizations, automatic backup, and validation.
    """

    def __init__(self, settings_file: Optional[Path] = None):
        """
        Initialize the Settings Manager

        Args:
            settings_file: Optional custom settings file path
        """
        self.settings_file = settings_file or SETTINGS_FILE
        self.backup_dir = BACKUP_DIR
        self._lock = threading.RLock()
        self._settings: Dict[str, Any] = {}
        self._dirty = False
        self._last_save_time = 0.0
        self._auto_save_delay = 2.0  # Auto-save delay in seconds
        self._auto_save_timer: Optional[threading.Timer] = None

        # Setup logging
        self.logger = logging.getLogger(f"SettingsManager")

        # Ensure directories exist
        self._ensure_directories()

        # Load settings
        self._load_settings()

        # Track session state
        self._session_start_time = time.time()
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def _ensure_directories(self):
        """Ensure settings and backup directories exist"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to create settings directories: {e}")
            raise ConfigurationError(f"Cannot create settings directories: {e}")

    def _load_settings(self):
        """Load settings from file with validation and error recovery"""
        with self._lock:
            try:
                if self.settings_file.exists():
                    with open(self.settings_file, 'r', encoding='utf-8') as f:
                        loaded_settings = json.load(f)

                    if not isinstance(loaded_settings, dict):
                        raise ValueError("Settings file contains invalid data structure")

                    # Validate and merge with defaults
                    self._settings = self._validate_and_merge_settings(loaded_settings)
                    self.logger.info(f"Settings loaded from {self.settings_file}")

                else:
                    # Use defaults for new installation
                    self._settings = default_settings.copy()
                    self.logger.info("Using default settings for new installation")
                    self._save_settings_immediate()

            except Exception as e:
                self.logger.error(f"Failed to load settings: {e}")

                # Attempt to restore from backup
                if self._restore_from_backup():
                    self.logger.info("Settings restored from backup")
                else:
                    # Fallback to defaults
                    self.logger.warning("Using default settings due to load failure")
                    self._settings = default_settings.copy()
                    self._save_settings_immediate()

    def _validate_and_merge_settings(self, loaded_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate loaded settings and merge with defaults

        Args:
            loaded_settings: Settings loaded from file

        Returns:
            Dict[str, Any]: Validated and merged settings
        """
        validated_settings = default_settings.copy()

        for key, value in loaded_settings.items():
            if key in default_settings:
                try:
                    # Validate specific setting types
                    if key == "zone_colors":
                        validated_settings[key] = self._validate_zone_colors(value)
                    elif key == "current_color":
                        validated_settings[key] = self._validate_color_dict(value)
                    elif key in ["brightness", "effect_speed"]:
                        validated_settings[key] = self._validate_numeric_range(value, key)
                    elif key in ["effect_color", "gradient_start_color", "gradient_end_color"]:
                        validated_settings[key] = self._validate_hex_color(value)
                    elif isinstance(value, type(default_settings[key])):
                        validated_settings[key] = value
                    else:
                        self.logger.warning(f"Invalid type for setting '{key}': {type(value)}, using default")

                except Exception as e:
                    self.logger.warning(f"Validation failed for setting '{key}': {e}, using default")
            else:
                self.logger.debug(f"Unknown setting '{key}' ignored")

        return validated_settings

    def _validate_zone_colors(self, zone_colors: Any) -> List[Dict[str, int]]:
        """Validate zone colors setting"""
        if not isinstance(zone_colors, list):
            raise ValueError("zone_colors must be a list")

        validated_colors = []
        for i, color_data in enumerate(zone_colors):
            try:
                if isinstance(color_data, dict):
                    # Validate as RGBColor dictionary
                    rgb_color = RGBColor.from_dict(color_data)
                    validated_colors.append(rgb_color.to_dict())
                else:
                    raise ValueError(f"Invalid color data type at index {i}")
            except Exception as e:
                self.logger.warning(f"Invalid zone color at index {i}: {e}, using default")
                default_color = default_settings["zone_colors"][i % len(default_settings["zone_colors"])]
                validated_colors.append(default_color)

        return validated_colors

    def _validate_color_dict(self, color_data: Any) -> Dict[str, int]:
        """Validate color dictionary"""
        try:
            rgb_color = RGBColor.from_dict(color_data)
            return rgb_color.to_dict()
        except Exception:
            return default_settings["current_color"]

    def _validate_numeric_range(self, value: Any, setting_name: str) -> Union[int, float]:
        """Validate numeric settings with appropriate ranges"""
        try:
            if setting_name == "brightness":
                return max(0, min(100, int(value)))
            elif setting_name == "effect_speed":
                return max(1, min(10, int(value)))
            else:
                return value
        except (ValueError, TypeError):
            return default_settings[setting_name]

    def _validate_hex_color(self, value: Any) -> str:
        """Validate hex color string"""
        try:
            if isinstance(value, str):
                # Validate by creating RGBColor
                RGBColor.from_hex(value)
                return value
            else:
                raise ValueError("Hex color must be string")
        except Exception:
            # Return appropriate default
            if "gradient_start" in str(value):
                return default_settings["gradient_start_color"]
            elif "gradient_end" in str(value):
                return default_settings["gradient_end_color"]
            else:
                return default_settings["effect_color"]

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Any: Setting value or default
        """
        with self._lock:
            return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """
        Set a setting value with validation

        Args:
            key: Setting key
            value: Setting value

        Returns:
            bool: True if setting was updated
        """
        with self._lock:
            try:
                # Validate the setting
                if key == "zone_colors" and isinstance(value, list):
                    validated_value = self._validate_zone_colors(value)
                elif key == "current_color" and isinstance(value, dict):
                    validated_value = self._validate_color_dict(value)
                elif key in ["brightness", "effect_speed"]:
                    validated_value = self._validate_numeric_range(value, key)
                elif key in ["effect_color", "gradient_start_color", "gradient_end_color"]:
                    validated_value = self._validate_hex_color(value)
                else:
                    validated_value = value

                # Check if value actually changed
                if self._settings.get(key) != validated_value:
                    self._settings[key] = validated_value
                    self._dirty = True
                    self._schedule_auto_save()
                    self.logger.debug(f"Setting '{key}' updated")
                    return True

                return False

            except Exception as e:
                self.logger.error(f"Failed to set setting '{key}': {e}")
                return False

    def update(self, settings_dict: Dict[str, Any]) -> int:
        """
        Update multiple settings

        Args:
            settings_dict: Dictionary of settings to update

        Returns:
            int: Number of settings actually updated
        """
        updated_count = 0
        with self._lock:
            for key, value in settings_dict.items():
                if self.set(key, value):
                    updated_count += 1

        if updated_count > 0:
            self.logger.info(f"Updated {updated_count} settings")

        return updated_count

    def _schedule_auto_save(self):
        """Schedule automatic save with delay to batch multiple changes"""
        if self._auto_save_timer:
            self._auto_save_timer.cancel()

        self._auto_save_timer = threading.Timer(self._auto_save_delay, self._auto_save_callback)
        self._auto_save_timer.daemon = True
        self._auto_save_timer.start()

    def _auto_save_callback(self):
        """Auto-save callback"""
        try:
            self.save_settings()
        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")

    def save_settings(self) -> bool:
        """
        Save settings to file

        Returns:
            bool: True if save was successful
        """
        with self._lock:
            if not self._dirty:
                return True  # No changes to save

            return self._save_settings_immediate()

    def _save_settings_immediate(self) -> bool:
        """Immediate save without checking dirty flag"""
        try:
            # Create backup before saving
            self._create_backup()

            # Add metadata
            settings_with_metadata = self._settings.copy()
            settings_with_metadata['_metadata'] = {
                'version': '3.0.0-OSIRIS',
                'saved_at': datetime.now().isoformat(),
                'session_id': self._session_id,
                'session_duration': time.time() - self._session_start_time
            }

            # Atomic write using temporary file
            temp_file = self.settings_file.with_suffix('.tmp')

            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(settings_with_metadata, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_file.replace(self.settings_file)

            self._dirty = False
            self._last_save_time = time.time()
            self.logger.debug(f"Settings saved to {self.settings_file}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            return False

    def _create_backup(self):
        """Create backup of current settings"""
        try:
            if self.settings_file.exists():
                backup_file = self.backup_dir / f"settings_backup_{self._session_id}.json"

                # Copy current settings to backup
                with open(self.settings_file, 'r', encoding='utf-8') as src:
                    with open(backup_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())

                # Cleanup old backups (keep last 10)
                self._cleanup_old_backups()

        except Exception as e:
            self.logger.warning(f"Failed to create settings backup: {e}")

    def _cleanup_old_backups(self):
        """Cleanup old backup files"""
        try:
            backup_files = list(self.backup_dir.glob("settings_backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Keep only the 10 most recent backups
            for old_backup in backup_files[10:]:
                old_backup.unlink()

        except Exception as e:
            self.logger.warning(f"Failed to cleanup old backups: {e}")

    def _restore_from_backup(self) -> bool:
        """Attempt to restore settings from backup"""
        try:
            backup_files = list(self.backup_dir.glob("settings_backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            for backup_file in backup_files:
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_settings = json.load(f)

                    # Remove metadata if present
                    backup_settings.pop('_metadata', None)

                    # Validate and use backup
                    self._settings = self._validate_and_merge_settings(backup_settings)
                    self.logger.info(f"Restored settings from backup: {backup_file}")
                    return True

                except Exception as e:
                    self.logger.warning(f"Failed to restore from backup {backup_file}: {e}")
                    continue

            return False

        except Exception as e:
            self.logger.error(f"Backup restore failed: {e}")
            return False

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        with self._lock:
            self._settings = default_settings.copy()
            self._dirty = True
            self.save_settings()
            self.logger.info("Settings reset to defaults")

    def export_settings(self, export_file: Path) -> bool:
        """
        Export settings to file

        Args:
            export_file: Export file path

        Returns:
            bool: True if export was successful
        """
        try:
            export_data = {
                'settings': self._settings.copy(),
                'export_info': {
                    'exported_at': datetime.now().isoformat(),
                    'version': '3.0.0-OSIRIS',
                    'exported_from': str(self.settings_file)
                }
            }

            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Settings exported to {export_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            return False

    def import_settings(self, import_file: Path) -> bool:
        """
        Import settings from file

        Args:
            import_file: Import file path

        Returns:
            bool: True if import was successful
        """
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # Extract settings from export format or use direct format
            if 'settings' in import_data:
                imported_settings = import_data['settings']
            else:
                imported_settings = import_data

            # Validate and merge
            validated_settings = self._validate_and_merge_settings(imported_settings)

            with self._lock:
                self._settings = validated_settings
                self._dirty = True
                self.save_settings()

            self.logger.info(f"Settings imported from {import_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            return False

    def was_previous_session_clean(self) -> bool:
        """
        Check if the previous session ended cleanly

        Returns:
            bool: True if previous session was clean
        """
        return self.get('clean_shutdown', False)

    def mark_clean_shutdown(self):
        """Mark the current session as ending cleanly"""
        self.set('clean_shutdown', True)
        self.save_settings()

    def mark_unclean_shutdown(self):
        """Mark the current session as ending uncleanly"""
        self.set('clean_shutdown', False)
        # Don't auto-save here to avoid overwriting during crash

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all settings as a dictionary copy

        Returns:
            Dict[str, Any]: All settings
        """
        with self._lock:
            return self._settings.copy()

    def has_setting(self, key: str) -> bool:
        """
        Check if a setting exists

        Args:
            key: Setting key

        Returns:
            bool: True if setting exists
        """
        with self._lock:
            return key in self._settings

    def get_settings_info(self) -> Dict[str, Any]:
        """
        Get settings manager information

        Returns:
            Dict[str, Any]: Settings manager info
        """
        return {
            'settings_file': str(self.settings_file),
            'backup_dir': str(self.backup_dir),
            'last_save_time': self._last_save_time,
            'dirty': self._dirty,
            'session_start_time': self._session_start_time,
            'session_id': self._session_id,
            'session_duration': time.time() - self._session_start_time,
            'total_settings': len(self._settings),
            'file_exists': self.settings_file.exists(),
            'file_size': self.settings_file.stat().st_size if self.settings_file.exists() else 0
        }

    def cleanup(self):
        """Cleanup resources"""
        if self._auto_save_timer:
            self._auto_save_timer.cancel()
            self._auto_save_timer = None

        if self._dirty:
            self.save_settings()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
