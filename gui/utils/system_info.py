#!/usr/bin/env python3
"""Enhanced System Information utilities with OSIRIS hardware detection"""

import os
import platform
import subprocess
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from ..core.exceptions import ResourceError, ValidationError
from .decorators import safe_execute, performance_monitor
from .safe_subprocess import run_command


class SystemInfo:
    """
    Enhanced system information collector with OSIRIS-specific detection

    Provides comprehensive system information gathering with special focus
    on ChromeOS hardware detection and OSIRIS device identification.
    """

    def __init__(self):
        """Initialize system information collector"""
        self.logger = logging.getLogger(f"{__name__}.SystemInfo")
        self._cache = {}
        self._cache_valid = False

    @safe_execute(max_attempts=1, severity="warning", fallback_return={})
    @performance_monitor(log_performance=False)
    def get_system_info(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive system information

        Args:
            force_refresh: Force refresh of cached data

        Returns:
            Dict[str, Any]: System information dictionary
        """
        if self._cache_valid and not force_refresh:
            return self._cache.copy()

        try:
            info = {
                'platform': self._get_platform_info(),
                'hardware': self._get_hardware_info(),
                'chromeos': self._get_chromeos_info(),
                'osiris': self._get_osiris_info(),
                'environment': self._get_environment_info(),
                'permissions': self._get_permission_info(),
                'display': self._get_display_info(),
                'system_paths': self._get_system_paths(),
                'keyboard_devices': self._get_keyboard_devices()
            }

            self._cache = info
            self._cache_valid = True

            return info.copy()

        except Exception as e:
            self.logger.error(f"Failed to gather system information: {e}")
            return {}

    def _get_platform_info(self) -> Dict[str, str]:
        """Get basic platform information"""
        try:
            return {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'architecture': platform.architecture()[0],
                'python_version': platform.python_version(),
                'platform_string': platform.platform()
            }
        except Exception as e:
            self.logger.warning(f"Failed to get platform info: {e}")
            return {}

    def _get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information from various sources"""
        info = {}

        try:
            # CPU information
            info['cpu'] = self._get_cpu_info()

            # Memory information
            info['memory'] = self._get_memory_info()

            # DMI information
            info['dmi'] = self._get_dmi_info()

            # PCI devices
            info['pci_devices'] = self._get_pci_devices()

            # USB devices
            info['usb_devices'] = self._get_usb_devices()

        except Exception as e:
            self.logger.warning(f"Failed to get hardware info: {e}")

        return info

    def _get_cpu_info(self) -> Dict[str, str]:
        """Get CPU information"""
        cpu_info = {}

        try:
            # Try /proc/cpuinfo first (Linux)
            cpuinfo_path = Path('/proc/cpuinfo')
            if cpuinfo_path.exists():
                with open(cpuinfo_path, 'r') as f:
                    content = f.read()

                # Extract key information
                lines = content.split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        value = value.strip()

                        if key in ['model_name', 'vendor_id', 'cpu_family', 'model', 'stepping']:
                            cpu_info[key] = value
                            if key == 'model_name':
                                break  # We have the main info

        except Exception as e:
            self.logger.debug(f"Failed to read /proc/cpuinfo: {e}")

        # Fallback to platform module
        if not cpu_info:
            cpu_info['processor'] = platform.processor()

        return cpu_info

    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory information"""
        memory_info = {}

        try:
            # Try /proc/meminfo (Linux)
            meminfo_path = Path('/proc/meminfo')
            if meminfo_path.exists():
                with open(meminfo_path, 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            # Convert kB to MB
                            total_kb = int(line.split()[1])
                            memory_info['total_mb'] = total_kb // 1024
                            break

        except Exception as e:
            self.logger.debug(f"Failed to read /proc/meminfo: {e}")

        # Try alternative methods
        if not memory_info:
            try:
                import psutil
                memory_info['total_mb'] = psutil.virtual_memory().total // (1024 * 1024)
            except ImportError:
                pass

        return memory_info

    def _get_dmi_info(self) -> Dict[str, str]:
        """Get DMI (Desktop Management Interface) information"""
        dmi_info = {}
        dmi_files = {
            'sys_vendor': '/sys/devices/virtual/dmi/id/sys_vendor',
            'product_name': '/sys/devices/virtual/dmi/id/product_name',
            'product_version': '/sys/devices/virtual/dmi/id/product_version',
            'board_name': '/sys/devices/virtual/dmi/id/board_name',
            'board_vendor': '/sys/devices/virtual/dmi/id/board_vendor',
            'bios_vendor': '/sys/devices/virtual/dmi/id/bios_vendor',
            'bios_version': '/sys/devices/virtual/dmi/id/bios_version',
            'chassis_type': '/sys/devices/virtual/dmi/id/chassis_type'
        }

        for key, path in dmi_files.items():
            try:
                dmi_path = Path(path)
                if dmi_path.exists():
                    with open(dmi_path, 'r') as f:
                        value = f.read().strip()
                        if value and value != 'Unknown':
                            dmi_info[key] = value
            except Exception as e:
                self.logger.debug(f"Failed to read DMI {key}: {e}")

        return dmi_info

    def _get_chromeos_info(self) -> Dict[str, Any]:
        """Get ChromeOS-specific information"""
        chromeos_info = {
            'is_chromeos': False,
            'version': None,
            'board': None,
            'channel': None
        }

        try:
            # Check for ChromeOS indicators
            chromeos_indicators = [
                Path('/etc/lsb-release'),
                Path('/opt/google/chrome/chrome'),
                Path('/usr/share/chromeos-assets'),
                Path('/run/chromeos-config')
            ]

            chromeos_found = any(indicator.exists() for indicator in chromeos_indicators)

            if chromeos_found:
                chromeos_info['is_chromeos'] = True

                # Try to get version from lsb-release
                lsb_release = Path('/etc/lsb-release')
                if lsb_release.exists():
                    with open(lsb_release, 'r') as f:
                        for line in f:
                            if line.startswith('CHROMEOS_RELEASE_VERSION='):
                                chromeos_info['version'] = line.split('=', 1)[1].strip()
                            elif line.startswith('CHROMEOS_RELEASE_BOARD='):
                                chromeos_info['board'] = line.split('=', 1)[1].strip()
                            elif line.startswith('CHROMEOS_RELEASE_TRACK='):
                                chromeos_info['channel'] = line.split('=', 1)[1].strip()

                # Check for developer mode
                crossystem_path = Path('/usr/bin/crossystem')
                if crossystem_path.exists():
                    try:
                        result = run_command([str(crossystem_path), 'cros_debug'], timeout=5.0)
                        if result.returncode == 0 and result.stdout:
                            chromeos_info['developer_mode'] = result.stdout.strip() == '1'
                    except Exception:
                        pass

        except Exception as e:
            self.logger.warning(f"Failed to detect ChromeOS info: {e}")

        return chromeos_info

    def _get_osiris_info(self) -> Dict[str, Any]:
        """Get OSIRIS-specific hardware information"""
        osiris_info = {
            'is_osiris': False,
            'model': None,
            'keyboard_backlight_path': None,
            'supported_methods': []
        }

        try:
            # Check DMI information for OSIRIS identifiers
            dmi_info = self._get_dmi_info()
            dmi_text = ' '.join(dmi_info.values()).lower()

            osiris_identifiers = ['osiris', 'acer chromebook plus 516 ge', 'brya']
            is_osiris = any(identifier in dmi_text for identifier in osiris_identifiers)

            if is_osiris:
                osiris_info['is_osiris'] = True
                osiris_info['model'] = 'Acer Chromebook Plus 516 GE (Osiris)'

                # Check for keyboard backlight paths
                backlight_paths = [
                    '/sys/class/leds/chromeos::kbd_backlight',
                    '/sys/class/backlight/chromeos-keyboard-backlight',
                    '/sys/devices/platform/chromeos-keyboard-backlight'
                ]

                for path in backlight_paths:
                    if Path(path).exists():
                        osiris_info['keyboard_backlight_path'] = path
                        break

                # Check supported control methods
                if osiris_info['keyboard_backlight_path']:
                    osiris_info['supported_methods'].append('ec_direct')

                # Check for ectool
                ectool_paths = ['/usr/local/bin/ectool', '/usr/bin/ectool']
                for ectool_path in ectool_paths:
                    if Path(ectool_path).exists():
                        osiris_info['supported_methods'].append('ectool')
                        break
                else:
                    # Check if ectool is in PATH
                    try:
                        result = run_command(['which', 'ectool'], timeout=2.0)
                        if result.returncode == 0:
                            osiris_info['supported_methods'].append('ectool')
                    except Exception:
                        pass

        except Exception as e:
            self.logger.warning(f"Failed to detect OSIRIS info: {e}")

        return osiris_info

    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information"""
        env_info = {}

        try:
            # Desktop environment
            desktop_vars = ['XDG_CURRENT_DESKTOP', 'DESKTOP_SESSION', 'GDMSESSION']
            for var in desktop_vars:
                value = os.environ.get(var)
                if value:
                    env_info['desktop_environment'] = value
                    break

            # Display server
            if os.environ.get('WAYLAND_DISPLAY'):
                env_info['display_server'] = 'wayland'
            elif os.environ.get('DISPLAY'):
                env_info['display_server'] = 'x11'

            # Session type
            env_info['session_type'] = os.environ.get('XDG_SESSION_TYPE', 'unknown')

            # User information
            env_info['user'] = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
            env_info['home'] = os.environ.get('HOME', os.environ.get('USERPROFILE', 'unknown'))

            # PATH information
            path_env = os.environ.get('PATH', '')
            env_info['path_count'] = len(path_env.split(os.pathsep)) if path_env else 0

        except Exception as e:
            self.logger.warning(f"Failed to get environment info: {e}")

        return env_info

    def _get_permission_info(self) -> Dict[str, bool]:
        """Get permission and privilege information"""
        perm_info = {}

        try:
            # Check if running as root/administrator
            perm_info['is_root'] = os.geteuid() == 0 if hasattr(os, 'geteuid') else False

            # Check sudo availability
            try:
                result = run_command(['sudo', '-n', 'true'], timeout=2.0)
                perm_info['sudo_available'] = result.returncode == 0
            except Exception:
                perm_info['sudo_available'] = False

            # Check write access to common system directories
            test_paths = ['/sys', '/dev', '/proc', '/tmp']
            for path in test_paths:
                path_obj = Path(path)
                if path_obj.exists():
                    perm_info[f'write_access_{path.replace("/", "_")}'] = os.access(path_obj, os.W_OK)

            # Check specific hardware access
            hw_paths = [
                '/sys/class/leds',
                '/sys/class/backlight',
                '/dev/input'
            ]

            for hw_path in hw_paths:
                hw_path_obj = Path(hw_path)
                if hw_path_obj.exists():
                    key = f'hw_access_{hw_path.split("/")[-1]}'
                    perm_info[key] = os.access(hw_path_obj, os.R_OK)

        except Exception as e:
            self.logger.warning(f"Failed to get permission info: {e}")

        return perm_info

    def _get_display_info(self) -> Dict[str, Any]:
        """Get display and GUI information"""
        display_info = {}

        try:
            # Screen resolution (if available)
            if os.environ.get('DISPLAY'):
                try:
                    result = run_command(['xdpyinfo'], timeout=3.0)
                    if result.returncode == 0 and result.stdout:
                        for line in result.stdout.split('\n'):
                            if 'dimensions:' in line:
                                dimensions = line.split('dimensions:')[1].split()[0]
                                display_info['resolution'] = dimensions
                                break
                except Exception:
                    pass

            # GTK/Qt availability
            try:
                import tkinter
                display_info['tkinter_available'] = True
            except ImportError:
                display_info['tkinter_available'] = False

            # Check for accessibility features
            if os.environ.get('XDG_CURRENT_DESKTOP'):
                display_info['accessibility_bus'] = bool(os.environ.get('AT_SPI_BUS'))

        except Exception as e:
            self.logger.warning(f"Failed to get display info: {e}")

        return display_info

    def _get_system_paths(self) -> Dict[str, Any]:
        """Get important system paths"""
        paths_info = {}

        try:
            # Executable paths
            executables = ['python3', 'ectool', 'sudo', 'which']
            for exe in executables:
                try:
                    result = run_command(['which', exe], timeout=2.0)
                    if result.returncode == 0:
                        paths_info[f'{exe}_path'] = result.stdout.strip()
                except Exception:
                    paths_info[f'{exe}_path'] = None

            # System directories
            system_dirs = ['/sys/class/leds', '/sys/class/backlight', '/dev/input', '/proc']
            for sys_dir in system_dirs:
                dir_path = Path(sys_dir)
                paths_info[f'{sys_dir.replace("/", "_")}_exists'] = dir_path.exists()

        except Exception as e:
            self.logger.warning(f"Failed to get system paths: {e}")

        return paths_info

    def _get_keyboard_devices(self) -> List[Dict[str, str]]:
        """Get information about keyboard devices"""
        devices = []

        try:
            # Check /proc/bus/input/devices
            devices_path = Path('/proc/bus/input/devices')
            if devices_path.exists():
                with open(devices_path, 'r') as f:
                    content = f.read()

                # Parse device information
                device_blocks = content.split('\n\n')
                for block in device_blocks:
                    if 'keyboard' in block.lower() or 'EV=120013' in block:
                        device = {}
                        for line in block.split('\n'):
                            if line.startswith('N: Name='):
                                device['name'] = line.split('Name=')[1].strip().strip('"')
                            elif line.startswith('P: Phys='):
                                device['physical'] = line.split('Phys=')[1].strip()
                            elif line.startswith('H: Handlers='):
                                device['handlers'] = line.split('Handlers=')[1].strip()

                        if device:
                            devices.append(device)

        except Exception as e:
            self.logger.warning(f"Failed to get keyboard devices: {e}")

        return devices

    def _get_pci_devices(self) -> List[Dict[str, str]]:
        """Get PCI device information"""
        devices = []

        try:
            result = run_command(['lspci', '-v'], timeout=10.0)
            if result.returncode == 0 and result.stdout:
                device = {}
                for line in result.stdout.split('\n'):
                    if line and not line.startswith('\t'):
                        # New device
                        if device:
                            devices.append(device)
                        device = {'description': line.strip()}
                    elif line.startswith('\tSubsystem:'):
                        device['subsystem'] = line.strip().replace('\tSubsystem: ', '')

                if device:
                    devices.append(device)

        except Exception as e:
            self.logger.debug(f"Failed to get PCI devices: {e}")

        return devices[:20]  # Limit to first 20 devices

    def _get_usb_devices(self) -> List[Dict[str, str]]:
        """Get USB device information"""
        devices = []

        try:
            result = run_command(['lsusb'], timeout=5.0)
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        devices.append({'description': line.strip()})

        except Exception as e:
            self.logger.debug(f"Failed to get USB devices: {e}")

        return devices[:20]  # Limit to first 20 devices

    def is_chromeos(self) -> bool:
        """Quick check if running on ChromeOS"""
        return self.get_system_info().get('chromeos', {}).get('is_chromeos', False)

    def is_osiris_hardware(self) -> bool:
        """Quick check if running on OSIRIS hardware"""
        return self.get_system_info().get('osiris', {}).get('is_osiris', False)

    def get_supported_hardware_methods(self) -> List[str]:
        """Get list of supported hardware control methods"""
        return self.get_system_info().get('osiris', {}).get('supported_methods', [])

    def get_keyboard_backlight_path(self) -> Optional[str]:
        """Get keyboard backlight control path if available"""
        return self.get_system_info().get('osiris', {}).get('keyboard_backlight_path')

    def has_root_access(self) -> bool:
        """Check if the application has root access"""
        return self.get_system_info().get('permissions', {}).get('is_root', False)

    def has_sudo_access(self) -> bool:
        """Check if sudo is available"""
        return self.get_system_info().get('permissions', {}).get('sudo_available', False)

    def clear_cache(self):
        """Clear cached system information"""
        self._cache.clear()
        self._cache_valid = False
        self.logger.debug("System information cache cleared")


# Global instance for convenience
system_info = SystemInfo()

# Convenience functions
def get_system_summary() -> Dict[str, str]:
    """Get a brief system summary"""
    info = system_info.get_system_info()
    return {
        'platform': f"{info.get('platform', {}).get('system', 'Unknown')} {info.get('platform', {}).get('release', '')}".strip(),
        'hardware': info.get('hardware', {}).get('dmi', {}).get('product_name', 'Unknown'),
        'chromeos': 'Yes' if info.get('chromeos', {}).get('is_chromeos') else 'No',
        'osiris': 'Yes' if info.get('osiris', {}).get('is_osiris') else 'No',
        'desktop': info.get('environment', {}).get('desktop_environment', 'Unknown'),
        'permissions': 'Root' if info.get('permissions', {}).get('is_root') else 'User'
    }

def is_compatible_system() -> bool:
    """Check if the system is compatible with RGB keyboard control"""
    info = system_info.get_system_info()

    # Must be Linux-based
    if info.get('platform', {}).get('system') != 'Linux':
        return False

    # Must have some form of hardware control available
    methods = info.get('osiris', {}).get('supported_methods', [])
    return len(methods) > 0

def get_recommended_hardware_method() -> Optional[str]:
    """Get recommended hardware control method for this system"""
    methods = system_info.get_supported_hardware_methods()

    # Prefer EC Direct for OSIRIS hardware
    if system_info.is_osiris_hardware() and 'ec_direct' in methods:
        return 'ec_direct'
    elif 'ectool' in methods:
        return 'ectool'
    elif methods:
        return methods[0]
    else:
        return None

def log_system_info(logger: logging.Logger):
    """Log comprehensive system information for debugging"""
    logger.info("=== System Information ===")

    summary = get_system_summary()
    for key, value in summary.items():
        logger.info(f"  {key.title()}: {value}")

    if system_info.is_osiris_hardware():
        logger.info("  OSIRIS-specific:")
        osiris_info = system_info.get_system_info().get('osiris', {})
        logger.info(f"    Model: {osiris_info.get('model', 'Unknown')}")
        logger.info(f"    Backlight Path: {osiris_info.get('keyboard_backlight_path', 'Not found')}")
        logger.info(f"    Supported Methods: {', '.join(osiris_info.get('supported_methods', ['None']))}")

    logger.info("==========================")
