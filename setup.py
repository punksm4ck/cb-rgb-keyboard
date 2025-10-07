#!/usr/bin/env python3
"""Enhanced setup script for RGB Controller with comprehensive environment preparation"""

import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project information
PROJECT_NAME = "Enhanced RGB Keyboard Controller"
PROJECT_VERSION = "3.0.0-OSIRIS"
REQUIRED_PYTHON = (3, 8)

# Required system packages and their alternatives
SYSTEM_PACKAGES = {
    'debian': ['python3-tk', 'python3-pip', 'python3-dev'],
    'arch': ['tk', 'python-pip'],
    'fedora': ['python3-tkinter', 'python3-pip', 'python3-devel'],
    'generic': ['python3-tkinter', 'python3-pip']
}

# Python packages (no external dependencies for core functionality)
PYTHON_PACKAGES = []  # Core functionality uses only standard library

class SetupManager:
    """Enhanced setup manager for comprehensive environment preparation"""

    def __init__(self):
        """Initialize setup manager"""
        self.logger = self._setup_logging()
        self.project_root = Path(__file__).parent
        self.errors = []
        self.warnings = []

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for setup process"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s: %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        return logging.getLogger('Setup')

    def run_complete_setup(self) -> bool:
        """
        Run complete setup process

        Returns:
            bool: True if setup completed successfully
        """
        self.logger.info(f"=== {PROJECT_NAME} v{PROJECT_VERSION} Setup ===")

        try:
            # Check Python version
            if not self._check_python_version():
                return False

            # Check system compatibility
            if not self._check_system_compatibility():
                return False

            # Create directory structure
            self._create_directory_structure()

            # Check and install system dependencies
            self._check_system_dependencies()

            # Check Python dependencies
            self._check_python_dependencies()

            # Setup permissions
            self._setup_permissions()

            # Create configuration files
            self._create_config_files()

            # Run system tests
            self._run_system_tests()

            # Display summary
            self._display_setup_summary()

            return len(self.errors) == 0

        except Exception as e:
            self.logger.error(f"Setup failed with exception: {e}")
            return False

    def _check_python_version(self) -> bool:
        """Check Python version compatibility"""
        current_version = sys.version_info[:2]

        if current_version < REQUIRED_PYTHON:
            self.errors.append(
                f"Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ required, "
                f"but {current_version[0]}.{current_version[1]} found"
            )
            return False

        self.logger.info(f"✓ Python {current_version[0]}.{current_version[1]} compatible")
        return True

    def _check_system_compatibility(self) -> bool:
        """Check system compatibility"""
        system = self._detect_system()

        if system['platform'] != 'Linux':
            self.warnings.append(
                f"This application is optimized for Linux. "
                f"Current platform: {system['platform']}"
            )

        if system.get('is_chromeos'):
            self.logger.info("✓ ChromeOS detected - optimal compatibility")
        elif system.get('is_osiris'):
            self.logger.info("✓ OSIRIS hardware detected - full compatibility")
        else:
            self.warnings.append(
                "RGB keyboard hardware not detected. "
                "Application will run but hardware features may be limited."
            )

        return True

    def _detect_system(self) -> Dict[str, Any]:
        """Detect system information"""
        try:
            import platform

            system_info = {
                'platform': platform.system(),
                'distribution': None,
                'is_chromeos': False,
                'is_osiris': False
            }

            # Check for ChromeOS
            chromeos_indicators = [
                Path('/etc/lsb-release'),
                Path('/opt/google/chrome/chrome'),
                Path('/usr/share/chromeos-assets')
            ]
            system_info['is_chromeos'] = any(path.exists() for path in chromeos_indicators)

            # Check for OSIRIS hardware
            dmi_paths = [
                '/sys/devices/virtual/dmi/id/product_name',
                '/sys/devices/virtual/dmi/id/sys_vendor',
                '/sys/devices/virtual/dmi/id/board_name'
            ]

            dmi_info = []
            for dmi_path in dmi_paths:
                try:
                    with open(dmi_path, 'r') as f:
                        dmi_info.append(f.read().strip().lower())
                except:
                    continue

            dmi_text = ' '.join(dmi_info)
            system_info['is_osiris'] = any(
                identifier in dmi_text
                for identifier in ['osiris', 'acer chromebook plus 516 ge', 'brya']
            )

            # Detect Linux distribution
            if system_info['platform'] == 'Linux':
                system_info['distribution'] = self._detect_linux_distribution()

            return system_info

        except Exception as e:
            self.logger.warning(f"Could not detect system information: {e}")
            return {'platform': platform.system()}

    def _detect_linux_distribution(self) -> str:
        """Detect Linux distribution"""
        try:
            # Try os-release file
            os_release_path = Path('/etc/os-release')
            if os_release_path.exists():
                with open(os_release_path, 'r') as f:
                    for line in f:
                        if line.startswith('ID='):
                            dist_id = line.split('=')[1].strip().strip('"')
                            if dist_id in ['ubuntu', 'debian']:
                                return 'debian'
                            elif dist_id in ['fedora', 'rhel', 'centos']:
                                return 'fedora'
                            elif dist_id in ['arch', 'manjaro']:
                                return 'arch'
                            else:
                                return dist_id

            # Fallback methods
            if Path('/etc/debian_version').exists():
                return 'debian'
            elif Path('/etc/fedora-release').exists():
                return 'fedora'
            elif Path('/etc/arch-release').exists():
                return 'arch'
            else:
                return 'generic'

        except Exception:
            return 'generic'

    def _create_directory_structure(self):
        """Create necessary directory structure"""
        directories = [
            'gui/core',
            'gui/effects',
            'gui/hardware',
            'gui/utils',
            'logs',
            'backups',
            'exports'
        ]

        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)

            # Create __init__.py files for Python packages
            if directory.startswith('gui'):
                init_file = dir_path / '__init__.py'
                if not init_file.exists():
                    init_file.write_text('# Package marker\n')

        self.logger.info("✓ Directory structure created")

    def _check_system_dependencies(self):
        """Check and suggest system dependencies"""
        system = self._detect_system()
        distribution = system.get('distribution', 'generic')

        packages = SYSTEM_PACKAGES.get(distribution, SYSTEM_PACKAGES['generic'])

        self.logger.info("Checking system dependencies...")

        # Check if packages are installed
        missing_packages = []
        for package in packages:
            if not self._is_package_installed(package, distribution):
                missing_packages.append(package)

        if missing_packages:
            install_cmd = self._get_install_command(distribution, missing_packages)
            self.warnings.append(
                f"Missing system packages: {', '.join(missing_packages)}\n"
                f"Install with: {install_cmd}"
            )
        else:
            self.logger.info("✓ All system dependencies satisfied")

    def _is_package_installed(self, package: str, distribution: str) -> bool:
        """Check if system package is installed"""
        try:
            if distribution in ['debian', 'ubuntu']:
                result = subprocess.run(['dpkg', '-l', package],
                                      capture_output=True, text=True)
                return result.returncode == 0
            elif distribution in ['fedora', 'rhel', 'centos']:
                result = subprocess.run(['rpm', '-q', package],
                                      capture_output=True, text=True)
                return result.returncode == 0
            elif distribution == 'arch':
                result = subprocess.run(['pacman', '-Q', package],
                                      capture_output=True, text=True)
                return result.returncode == 0
            else:
                # Generic check - just assume it might be there
                return True

        except Exception:
            return False

    def _get_install_command(self, distribution: str, packages: List[str]) -> str:
        """Get package installation command"""
        if distribution in ['debian', 'ubuntu']:
            return f"sudo apt install {' '.join(packages)}"
        elif distribution in ['fedora', 'rhel', 'centos']:
            return f"sudo dnf install {' '.join(packages)}"
        elif distribution == 'arch':
            return f"sudo pacman -S {' '.join(packages)}"
        else:
            return f"Install packages: {' '.join(packages)}"

    def _check_python_dependencies(self):
        """Check Python dependencies"""
        if not PYTHON_PACKAGES:
            self.logger.info("✓ No external Python dependencies required")
            return

        missing = []
        for package in PYTHON_PACKAGES:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)

        if missing:
            self.warnings.append(
                f"Missing Python packages: {', '.join(missing)}\n"
                f"Install with: pip3 install {' '.join(missing)}"
            )
        else:
            self.logger.info("✓ All Python dependencies satisfied")

    def _setup_permissions(self):
        """Setup necessary permissions"""
        current_user = os.environ.get('USER', 'unknown')

        # Check hardware access permissions
        hw_paths = [
            '/sys/class/leds',
            '/sys/class/backlight',
            '/dev/input'
        ]

        accessible_paths = []
        inaccessible_paths = []

        for hw_path in hw_paths:
            if Path(hw_path).exists():
                if os.access(hw_path, os.R_OK):
                    accessible_paths.append(hw_path)
                else:
                    inaccessible_paths.append(hw_path)

        if inaccessible_paths:
            self.warnings.append(
                f"Some hardware paths require elevated privileges: {', '.join(inaccessible_paths)}\n"
                "The application will attempt to use sudo when needed."
            )

        if accessible_paths:
            self.logger.info(f"✓ Hardware access available: {', '.join(accessible_paths)}")

    def _create_config_files(self):
        """Create configuration files"""
        # Create basic gitignore if it doesn't exist
        gitignore_path = self.project_root / '.gitignore'
        if not gitignore_path.exists():
            gitignore_content = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Logs
logs/
*.log

# Settings and user data
settings.json
backups/
exports/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
            gitignore_path.write_text(gitignore_content.strip())
            self.logger.info("✓ Created .gitignore")

        self.logger.info("✓ Configuration files ready")

    def _run_system_tests(self):
        """Run basic system tests"""
        self.logger.info("Running system tests...")

        # Test Python imports
        try:
            import tkinter
            self.logger.info("✓ Tkinter GUI available")
        except ImportError:
            self.errors.append("Tkinter not available - GUI will not work")

        # Test hardware paths
        osiris_path = Path('/sys/class/leds/chromeos::kbd_backlight')
        if osiris_path.exists():
            self.logger.info("✓ OSIRIS keyboard backlight detected")

        # Test ectool availability
        try:
            result = subprocess.run(['which', 'ectool'], capture_output=True)
            if result.returncode == 0:
                self.logger.info("✓ ectool found in system PATH")
            else:
                self.warnings.append("ectool not found - some features may be limited")
        except Exception:
            self.warnings.append("Could not check ectool availability")

    def _display_setup_summary(self):
        """Display setup summary"""
        print("\n" + "="*50)
        print(f"{PROJECT_NAME} v{PROJECT_VERSION}")
        print("Setup Summary")
        print("="*50)

        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.errors:
            print("\n✅ Setup completed successfully!")
            print("\nNext steps:")
            print("1. Run the application:")
            print("   python3 -m gui")
            print("\n2. For CLI mode:")
            print("   python3 -m gui --help")
            print("\n3. Test hardware:")
            print("   python3 -m gui --test")
        else:
            print("\n❌ Setup failed - please resolve errors above")

        print("="*50)

    def create_desktop_entry(self) -> bool:
        """
        Create desktop entry for GUI launcher

        Returns:
            bool: True if created successfully
        """
        try:
            desktop_dir = Path.home() / '.local' / 'share' / 'applications'
            desktop_dir.mkdir(parents=True, exist_ok=True)

            desktop_file = desktop_dir / 'enhanced-rgb-controller.desktop'

            desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={PROJECT_NAME}
Comment=Enhanced RGB Keyboard Controller for ChromeOS
Exec=python3 -m gui
Icon=input-keyboard
Terminal=false
Categories=System;Settings;HardwareSettings;
Keywords=keyboard;rgb;lighting;chromebook;
StartupNotify=true
"""

            desktop_file.write_text(desktop_content)

            # Make executable
            os.chmod(desktop_file, 0o755)

            self.logger.info("✓ Desktop entry created")
            return True

        except Exception as e:
            self.warnings.append(f"Could not create desktop entry: {e}")
            return False

    def setup_udev_rules(self) -> bool:
        """
        Setup udev rules for hardware access (optional)

        Returns:
            bool: True if setup attempted
        """
        try:
            udev_rules_content = '''# RGB Keyboard Controller - Enhanced access rules
# Allow users to control keyboard backlighting without sudo

# ChromeOS keyboard backlight
SUBSYSTEM=="leds", KERNEL=="chromeos::kbd_backlight", MODE="0666"

# Generic keyboard backlight devices
SUBSYSTEM=="leds", KERNEL=="*kbd_backlight*", MODE="0666"
SUBSYSTEM=="backlight", KERNEL=="*keyboard*", MODE="0666"

# Input devices for reactive effects
SUBSYSTEM=="input", GROUP="input", MODE="0664"
'''

            rules_file = Path('/tmp/90-rgb-keyboard-controller.rules')
            rules_file.write_text(udev_rules_content)

            self.warnings.append(
                "Optional: For enhanced hardware access without sudo, copy udev rules:\n"
                f"sudo cp {rules_file} /etc/udev/rules.d/ && sudo udevadm control --reload-rules"
            )

            return True

        except Exception as e:
            self.logger.debug(f"Could not setup udev rules: {e}")
            return False


def main():
    """Main setup function"""
    setup_manager = SetupManager()

    print(f"Setting up {PROJECT_NAME} v{PROJECT_VERSION}...")
    print("This will check dependencies and prepare the environment.\n")

    success = setup_manager.run_complete_setup()

    if success:
        # Optional enhancements
        setup_manager.create_desktop_entry()
        setup_manager.setup_udev_rules()

        return 0
    else:
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
