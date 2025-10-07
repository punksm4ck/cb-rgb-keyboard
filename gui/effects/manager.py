#!/usr/bin/env python3
"""Enhanced Effects Manager with OSIRIS optimization and comprehensive effect management"""

import threading
import time
import logging
from typing import Dict, Any, Optional, List, Callable
import queue

from ..core.rgb_color import RGBColor, Colors
from ..core.constants import NUM_ZONES, ANIMATION_FRAME_DELAY
from ..core.exceptions import EffectError, HardwareError
from ..utils.decorators import safe_execute, thread_safe, performance_monitor
from ..utils.input_validation import SafeInputValidation
from .library import BaseEffect, EffectLibrary, effect_library


class EffectManager:
    """
    Enhanced Effects Manager with hardware integration and OSIRIS optimization

    Manages effect execution, transitions, and hardware communication with
    thread-safe operations and comprehensive error handling.
    """

    def __init__(self, hardware_controller=None, parent_logger=None):
        """
        Initialize effect manager

        Args:
            hardware_controller: Hardware controller instance
            parent_logger: Parent logger instance
        """
        self.logger = (parent_logger.getChild('EffectManager')
                      if parent_logger else logging.getLogger('EffectManager'))

        self.hardware = hardware_controller
        self._lock = threading.RLock()

        # Effect management
        self.current_effect: Optional[BaseEffect] = None
        self.effect_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()

        # Frame management
        self._frame_queue = queue.Queue(maxsize=60)  # Buffer for 60 frames
        self._frame_counter = 0
        self._effect_start_time = 0.0

        # Performance tracking
        self._frame_times = []
        self._max_frame_time_samples = 100

        # OSIRIS optimization
        self.osiris_mode = False
        self.single_zone_hardware = False

        # State management
        self.is_running = False
        self.last_colors = [Colors.BLACK] * NUM_ZONES

        self.logger.info("Effect Manager initialized")

    def set_hardware_controller(self, hardware_controller):
        """Set or update hardware controller"""
        with self._lock:
            self.hardware = hardware_controller

            # Detect OSIRIS hardware
            if hasattr(self.hardware, 'is_osiris_hardware'):
                self.osiris_mode = getattr(self.hardware, 'is_osiris_hardware', False)
                self.single_zone_hardware = self.osiris_mode

                if self.osiris_mode:
                    self.logger.info("OSIRIS hardware detected - enabling optimizations")

    @safe_execute(max_attempts=2, severity="error")
    def start_effect(self, effect_name: str, **kwargs) -> bool:
        """
        Start a lighting effect

        Args:
            effect_name: Name of effect to start
            **kwargs: Effect parameters

        Returns:
            bool: True if effect started successfully
        """
        with self._lock:
            try:
                # Stop current effect if running
                if self.is_running:
                    self.stop_effect()

                # Create new effect
                if self.osiris_mode:
                    kwargs['osiris_optimized'] = True
                    kwargs['single_zone_hardware'] = True

                self.current_effect = effect_library.create_effect(effect_name, **kwargs)

                # Reset state
                self._stop_event.clear()
                self._pause_event.clear()
                self._frame_counter = 0
                self._effect_start_time = time.time()

                # Start effect execution thread
                self.effect_thread = threading.Thread(
                    target=self._effect_loop,
                    name=f"Effect-{effect_name}",
                    daemon=True
                )

                self.current_effect.start()
                self.effect_thread.start()
                self.is_running = True

                self.logger.info(f"Started effect: {effect_name}")
                return True

            except Exception as e:
                self.logger.error(f"Failed to start effect '{effect_name}': {e}")
                self.current_effect = None
                return False

    @safe_execute(max_attempts=1, severity="warning")
    def stop_effect(self) -> bool:
        """
        Stop the current effect

        Returns:
            bool: True if stopped successfully
        """
        with self._lock:
            if not self.is_running:
                return True

            try:
                # Signal stop
                self._stop_event.set()
                self.is_running = False

                # Stop current effect
                if self.current_effect:
                    self.current_effect.stop()

                # Wait for thread to finish
                if self.effect_thread and self.effect_thread.is_alive():
                    self.effect_thread.join(timeout=2.0)
                    if self.effect_thread.is_alive():
                        self.logger.warning("Effect thread did not stop gracefully")

                # Clear hardware
                if self.hardware and self.hardware.is_operational():
                    self.hardware.clear_all_leds()

                self.current_effect = None
                self.effect_thread = None
                self.last_colors = [Colors.BLACK] * NUM_ZONES

                self.logger.info("Effect stopped")
                return True

            except Exception as e:
                self.logger.error(f"Error stopping effect: {e}")
                return False

    def pause_effect(self) -> bool:
        """Pause the current effect"""
        with self._lock:
            if self.current_effect and self.is_running:
                self._pause_event.set()
                self.current_effect.pause()
                self.logger.info("Effect paused")
                return True
            return False

    def resume_effect(self) -> bool:
        """Resume the paused effect"""
        with self._lock:
            if self.current_effect and self.is_running:
                self._pause_event.clear()
                self.current_effect.resume()
                self.logger.info("Effect resumed")
                return True
            return False

    @performance_monitor(log_performance=False, performance_threshold=0.1)
    def _effect_loop(self):
        """Main effect execution loop"""
        try:
            while not self._stop_event.is_set() and self.current_effect:
                loop_start = time.time()

                # Check if paused
                if self._pause_event.is_set():
                    time.sleep(0.1)
                    continue

                try:
                    # Generate frame
                    frame_colors = self.current_effect.generate_frame(self._frame_counter)

                    if frame_colors:
                        # Apply OSIRIS optimizations if needed
                        if self.osiris_mode:
                            frame_colors = self._optimize_for_osiris(frame_colors)

                        # Send to hardware
                        success = self._send_colors_to_hardware(frame_colors)

                        if success:
                            self.last_colors = frame_colors.copy()

                    self._frame_counter += 1

                    # Calculate timing
                    loop_time = time.time() - loop_start
                    self._track_performance(loop_time)

                    # Sleep for appropriate delay
                    delay = self.current_effect.get_delay()
                    remaining_time = delay - loop_time
                    if remaining_time > 0:
                        time.sleep(remaining_time)

                except Exception as e:
                    self.logger.error(f"Error in effect loop: {e}")
                    time.sleep(0.1)  # Prevent tight error loop

        except Exception as e:
            self.logger.error(f"Critical error in effect loop: {e}")

        finally:
            self.logger.debug("Effect loop terminated")

    def _optimize_for_osiris(self, colors: List[RGBColor]) -> List[RGBColor]:
        """
        Optimize colors for OSIRIS single-zone hardware

        Args:
            colors: List of zone colors

        Returns:
            List[RGBColor]: Optimized colors
        """
        if not colors:
            return colors

        if len(colors) == 1:
            return colors

        # For OSIRIS, convert multiple colors to optimal single color
        from ..core.rgb_color import get_optimal_osiris_brightness

        # Calculate optimal brightness
        optimal_brightness = get_optimal_osiris_brightness(colors, method="weighted_average")

        # Create equivalent white color at optimal brightness
        optimized_color = RGBColor.from_brightness(optimal_brightness, "neutral")

        # Return single color for all zones
        return [optimized_color] * NUM_ZONES

    @safe_execute(max_attempts=2, severity="warning", fallback_return=False)
    def _send_colors_to_hardware(self, colors: List[RGBColor]) -> bool:
        """
        Send colors to hardware with error handling

        Args:
            colors: List of colors to send

        Returns:
            bool: True if successful
        """
        if not self.hardware or not self.hardware.is_operational():
            return False

        try:
            if len(colors) == 1:
                # Single color for all zones
                return self.hardware.set_all_leds_color(colors[0])
            else:
                # Multiple zone colors
                return self.hardware.set_zone_colors(colors)

        except HardwareError as e:
            self.logger.warning(f"Hardware error sending colors: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending colors: {e}")
            return False

    def _track_performance(self, frame_time: float):
        """Track performance metrics"""
        self._frame_times.append(frame_time)

        # Keep only recent samples
        if len(self._frame_times) > self._max_frame_time_samples:
            self._frame_times.pop(0)

        # Log performance warnings
        if frame_time > 0.1:  # 100ms is too slow
            self.logger.warning(f"Slow frame render: {frame_time:.3f}s")

    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        if not self._frame_times:
            return {}

        return {
            'avg_frame_time': sum(self._frame_times) / len(self._frame_times),
            'max_frame_time': max(self._frame_times),
            'min_frame_time': min(self._frame_times),
            'frame_count': len(self._frame_times),
            'estimated_fps': 1.0 / (sum(self._frame_times) / len(self._frame_times))
        }

    def get_current_effect_info(self) -> Optional[Dict[str, Any]]:
        """Get information about current effect"""
        with self._lock:
            if self.current_effect:
                info = self.current_effect.get_info()
                info.update({
                    'manager_frame_counter': self._frame_counter,
                    'runtime': time.time() - self._effect_start_time,
                    'is_paused': self._pause_event.is_set(),
                    'performance_stats': self.get_performance_stats()
                })
                return info
            return None

    def set_static_color(self, color: RGBColor) -> bool:
        """
        Set static color (shortcut method)

        Args:
            color: Color to set

        Returns:
            bool: True if successful
        """
        return self.start_effect("Static Color", color=color)

    def set_static_brightness(self, brightness: int) -> bool:
        """
        Set static brightness (OSIRIS optimized)

        Args:
            brightness: Brightness level (0-100)

        Returns:
            bool: True if successful
        """
        if not self.hardware or not self.hardware.is_operational():
            return False

        try:
            return self.hardware.set_brightness(brightness)
        except Exception as e:
            self.logger.error(f"Failed to set brightness: {e}")
            return False

    def trigger_reactive(self, zone: int = 0):
        """
        Trigger reactive effect on specific zone

        Args:
            zone: Zone to trigger (0-based)
        """
        with self._lock:
            if (self.current_effect and
                hasattr(self.current_effect, 'trigger_zone') and
                self.current_effect.name == "Reactive"):

                self.current_effect.trigger_zone(zone)
                self.logger.debug(f"Triggered reactive effect on zone {zone}")

    def apply_instant_color(self, colors: List[RGBColor], duration: float = 0.0) -> bool:
        """
        Apply colors instantly without starting an effect

        Args:
            colors: Colors to apply
            duration: Duration to show colors (0 for permanent)

        Returns:
            bool: True if successful
        """
        if not self.hardware or not self.hardware.is_operational():
            return False

        try:
            # Apply OSIRIS optimization if needed
            if self.osiris_mode:
                colors = self._optimize_for_osiris(colors)

            success = self._send_colors_to_hardware(colors)

            if success and duration > 0:
                # Schedule return to previous state
                def restore_previous():
                    time.sleep(duration)
                    self._send_colors_to_hardware(self.last_colors)

                restore_thread = threading.Thread(target=restore_previous, daemon=True)
                restore_thread.start()

            return success

        except Exception as e:
            self.logger.error(f"Failed to apply instant color: {e}")
            return False

    def get_available_effects(self) -> List[str]:
        """Get list of available effects"""
        effects = effect_library.get_available_effects()

        # Filter for OSIRIS if needed
        if self.osiris_mode:
            from .library import get_osiris_recommended_effects
            recommended = get_osiris_recommended_effects()
            return [effect for effect in effects if effect in recommended] + \
                   [effect for effect in effects if effect not in recommended]

        return effects

    def cleanup(self):
        """Cleanup effect manager resources"""
        self.logger.info("Cleaning up Effect Manager...")

        try:
            self.stop_effect()

            # Clear any remaining frame queue
            while not self._frame_queue.empty():
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    break

            self.logger.info("Effect Manager cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during Effect Manager cleanup: {e}")

    def __del__(self):
        """Destructor"""
        try:
            self.cleanup()
        except:
            pass


# Convenience functions for common operations
def create_effect_manager(hardware_controller=None, logger=None) -> EffectManager:
    """Create effect manager instance"""
    return EffectManager(hardware_controller, logger)


def get_recommended_effects_for_hardware(is_osiris: bool = False) -> List[str]:
    """Get recommended effects for specific hardware"""
    if is_osiris:
        from .library import get_osiris_recommended_effects
        return get_osiris_recommended_effects()
    else:
        return effect_library.get_available_effects()


def validate_effect_parameters(effect_name: str, **kwargs) -> Dict[str, Any]:
    """Validate effect parameters"""
    validated = {}

    # Common parameter validation
    if 'speed' in kwargs:
        validated['speed'] = SafeInputValidation.validate_speed(kwargs['speed'], default=5)

    if 'brightness' in kwargs:
        validated['brightness'] = SafeInputValidation.validate_brightness(kwargs['brightness'], default=100)

    if 'color' in kwargs:
        validated['color'] = SafeInputValidation.validate_color(kwargs['color'], default=Colors.WHITE)

    if 'colors' in kwargs:
        validated['colors'] = SafeInputValidation.validate_color_list(kwargs['colors'])

    # Add other parameters as-is
    for key, value in kwargs.items():
        if key not in validated:
            validated[key] = value

    return validated
