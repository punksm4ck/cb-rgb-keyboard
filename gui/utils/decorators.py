#!/usr/bin/env python3
"""Enhanced Decorators for RGB Controller with comprehensive error handling and performance monitoring"""

import functools
import time
import threading
import logging
from typing import Callable, Any, Optional, Dict
import traceback

from ..core.exceptions import (
    RGBControllerError, HardwareError, TimeoutError, CriticalError,
    log_error_context, should_retry_operation
)


def safe_execute(max_attempts: int = 3, severity: str = "error",
                timeout: Optional[float] = None,
                exceptions_to_catch: tuple = (Exception,),
                exceptions_to_ignore: tuple = (),
                fallback_return: Any = None):
    """
    Enhanced decorator for safe execution with retry logic and comprehensive error handling

    Args:
        max_attempts: Maximum retry attempts
        severity: Error severity level ("debug", "info", "warning", "error", "critical")
        timeout: Operation timeout in seconds
        exceptions_to_catch: Exceptions that should be caught and handled
        exceptions_to_ignore: Exceptions that should be ignored (not logged)
        fallback_return: Default return value on failure
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(f"safe_execute.{func.__module__}.{func.__name__}")
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    # Apply timeout if specified
                    if timeout:
                        return _execute_with_timeout(func, args, kwargs, timeout)
                    else:
                        return func(*args, **kwargs)

                except exceptions_to_ignore:
                    # Silently ignore specified exceptions
                    return fallback_return

                except exceptions_to_catch as e:
                    last_exception = e

                    # Log the error with context
                    if not isinstance(e, exceptions_to_ignore):
                        log_error_context(logger, e, f"{func.__name__} (attempt {attempt + 1})")

                    # Check if we should retry
                    if attempt < max_attempts - 1 and should_retry_operation(e, attempt, max_attempts):
                        # Exponential backoff for retries
                        retry_delay = 2 ** attempt * 0.1
                        logger.debug(f"Retrying {func.__name__} in {retry_delay:.2f}s")
                        time.sleep(retry_delay)
                        continue
                    else:
                        break

            # All attempts failed, handle based on severity
            if last_exception:
                severity_level = getattr(logging, severity.upper(), logging.ERROR)
                logger.log(severity_level, f"Function {func.__name__} failed after {max_attempts} attempts")

                # Critical errors should be re-raised
                if severity == "critical" or isinstance(last_exception, CriticalError):
                    raise last_exception

            return fallback_return

        return wrapper
    return decorator


def _execute_with_timeout(func: Callable, args: tuple, kwargs: dict, timeout: float):
    """Execute function with timeout using threading"""
    result = [None]
    exception = [None]

    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        raise TimeoutError(f"Function {func.__name__} timed out after {timeout}s")

    if exception[0]:
        raise exception[0]

    return result[0]


def performance_monitor(log_performance: bool = True,
                       performance_threshold: float = 1.0,
                       memory_threshold: Optional[int] = None):
    """
    Decorator to monitor function performance and resource usage

    Args:
        log_performance: Whether to log performance metrics
        performance_threshold: Log warning if execution exceeds this time (seconds)
        memory_threshold: Log warning if memory usage exceeds this (MB)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(f"performance.{func.__module__}.{func.__name__}")

            # Record start metrics
            start_time = time.time()
            start_memory = _get_memory_usage() if memory_threshold else None

            try:
                result = func(*args, **kwargs)

                # Record end metrics
                end_time = time.time()
                execution_time = end_time - start_time

                # Log performance if enabled
                if log_performance:
                    logger.debug(f"Function {func.__name__} executed in {execution_time:.4f}s")

                # Check performance threshold
                if execution_time > performance_threshold:
                    logger.warning(f"Function {func.__name__} exceeded performance threshold: {execution_time:.4f}s > {performance_threshold}s")

                # Check memory threshold
                if memory_threshold and start_memory:
                    end_memory = _get_memory_usage()
                    memory_delta = end_memory - start_memory
                    if memory_delta > memory_threshold:
                        logger.warning(f"Function {func.__name__} exceeded memory threshold: +{memory_delta}MB")

                return result

            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                logger.error(f"Function {func.__name__} failed after {execution_time:.4f}s")
                raise

        return wrapper
    return decorator


def _get_memory_usage() -> int:
    """Get current memory usage in MB"""
    try:
        import psutil
        process = psutil.Process()
        return int(process.memory_info().rss / 1024 / 1024)
    except ImportError:
        return 0


def thread_safe(lock: Optional[threading.Lock] = None):
    """
    Decorator to make functions thread-safe

    Args:
        lock: Optional specific lock to use, otherwise creates a new one
    """
    if lock is None:
        lock = threading.RLock()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_hardware_state(check_operational: bool = True,
                           check_brightness_range: bool = False,
                           required_method: Optional[str] = None):
    """
    Decorator to validate hardware state before function execution

    Args:
        check_operational: Check if hardware is operational
        check_brightness_range: Validate brightness parameter is in range
        required_method: Require specific hardware method
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Find hardware controller instance (assume it's 'self' or in args)
            hardware = None
            if args and hasattr(args[0], 'hardware'):
                hardware = args[0].hardware
            elif args and hasattr(args[0], 'is_operational'):
                hardware = args[0]

            if hardware is None:
                raise HardwareError("Hardware controller not found for validation")

            # Check if hardware is operational
            if check_operational and not hardware.is_operational():
                raise HardwareError("Hardware is not operational",
                                  hardware_method=getattr(hardware, 'active_control_method', 'unknown'))

            # Check required method
            if required_method and getattr(hardware, 'active_control_method', '') != required_method:
                raise HardwareError(f"Required hardware method '{required_method}' not active",
                                  hardware_method=getattr(hardware, 'active_control_method', 'unknown'))

            # Validate brightness range if requested
            if check_brightness_range:
                brightness_arg = None
                if 'brightness' in kwargs:
                    brightness_arg = kwargs['brightness']
                elif len(args) > 1 and isinstance(args[1], (int, float)):
                    brightness_arg = args[1]

                if brightness_arg is not None:
                    if not (0 <= brightness_arg <= 100):
                        raise ValueError(f"Brightness must be between 0-100, got {brightness_arg}")

            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_function_calls(log_level: str = "debug",
                      log_args: bool = False,
                      log_result: bool = False,
                      sensitive_args: tuple = ()):
    """
    Decorator to log function calls for debugging

    Args:
        log_level: Logging level for the calls
        log_args: Whether to log function arguments
        log_result: Whether to log function return value
        sensitive_args: Argument names to exclude from logging
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(f"function_calls.{func.__module__}.{func.__name__}")
            level = getattr(logging, log_level.upper(), logging.DEBUG)

            # Build call info
            call_info = f"Calling {func.__name__}"

            if log_args:
                # Filter out sensitive arguments
                safe_kwargs = {k: v for k, v in kwargs.items() if k not in sensitive_args}
                if safe_kwargs or args:
                    call_info += f" with args={args[:3]}{'...' if len(args) > 3 else ''}, kwargs={safe_kwargs}"

            logger.log(level, call_info)

            try:
                result = func(*args, **kwargs)

                if log_result and result is not None:
                    # Truncate large results
                    result_str = str(result)
                    if len(result_str) > 200:
                        result_str = result_str[:200] + "..."
                    logger.log(level, f"{func.__name__} returned: {result_str}")

                return result

            except Exception as e:
                logger.log(level, f"{func.__name__} raised {type(e).__name__}: {e}")
                raise

        return wrapper
    return decorator


def cache_result(ttl: float = 300.0, max_size: int = 128):
    """
    Decorator to cache function results with TTL

    Args:
        ttl: Time to live for cached results (seconds)
        max_size: Maximum cache size
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_times = {}
        access_order = []
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()

            with lock:
                # Check if we have a valid cached result
                if key in cache and (current_time - cache_times[key]) < ttl:
                    # Move to end of access order
                    if key in access_order:
                        access_order.remove(key)
                    access_order.append(key)
                    return cache[key]

                # Compute new result
                result = func(*args, **kwargs)

                # Store in cache
                cache[key] = result
                cache_times[key] = current_time

                if key in access_order:
                    access_order.remove(key)
                access_order.append(key)

                # Enforce cache size limit
                while len(cache) > max_size:
                    oldest_key = access_order.pop(0)
                    cache.pop(oldest_key, None)
                    cache_times.pop(oldest_key, None)

                return result

        # Add cache management methods
        def clear_cache():
            with lock:
                cache.clear()
                cache_times.clear()
                access_order.clear()

        def cache_info():
            with lock:
                return {
                    'cache_size': len(cache),
                    'max_size': max_size,
                    'ttl': ttl,
                    'hit_keys': list(cache.keys())
                }

        wrapper.clear_cache = clear_cache
        wrapper.cache_info = cache_info

        return wrapper
    return decorator


def osiris_hardware_optimized(fallback_method: Optional[str] = None):
    """
    Decorator to optimize functions for OSIRIS hardware

    Args:
        fallback_method: Fallback method if OSIRIS optimization fails
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if we're running on OSIRIS hardware
            hardware = None
            if args and hasattr(args[0], 'hardware'):
                hardware = args[0].hardware
            elif args and hasattr(args[0], 'is_osiris_hardware'):
                hardware = args[0]

            is_osiris = getattr(hardware, 'is_osiris_hardware', False)

            if is_osiris:
                # Apply OSIRIS-specific optimizations
                logger = logging.getLogger(f"osiris_optimization.{func.__name__}")
                logger.debug(f"Applying OSIRIS optimizations for {func.__name__}")

                # For OSIRIS single-zone hardware, we can optimize certain operations
                if 'colors' in kwargs and isinstance(kwargs['colors'], list):
                    # Convert multiple colors to single optimal brightness
                    from ..core.rgb_color import get_optimal_osiris_brightness
                    colors = kwargs['colors']
                    if len(colors) > 1:
                        kwargs['osiris_optimized'] = True
                        logger.debug(f"OSIRIS optimization: Converting {len(colors)} colors to optimal brightness")

            try:
                return func(*args, **kwargs)
            except Exception as e:
                if fallback_method and is_osiris:
                    logger.warning(f"OSIRIS optimization failed for {func.__name__}, trying fallback")
                    # Could implement fallback logic here
                raise

        return wrapper
    return decorator


def deprecated(reason: str, version: str = "future",
               alternative: Optional[str] = None):
    """
    Decorator to mark functions as deprecated

    Args:
        reason: Reason for deprecation
        version: Version when it will be removed
        alternative: Suggested alternative function/method
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(f"deprecated.{func.__module__}.{func.__name__}")

            warning_msg = f"Function {func.__name__} is deprecated: {reason}"
            if version != "future":
                warning_msg += f" (will be removed in version {version})"
            if alternative:
                warning_msg += f". Use {alternative} instead."

            logger.warning(warning_msg)
            return func(*args, **kwargs)

        return wrapper
    return decorator


# Global decorator instances for common use cases
hardware_safe = safe_execute(
    max_attempts=2,
    exceptions_to_catch=(HardwareError, TimeoutError),
    severity="error"
)

config_safe = safe_execute(
    max_attempts=1,
    exceptions_to_catch=(ValueError, KeyError, TypeError),
    severity="warning",
    fallback_return=None
)

ui_safe = safe_execute(
    max_attempts=1,
    exceptions_to_catch=(Exception,),
    severity="error",
    fallback_return=False
)

critical_operation = safe_execute(
    max_attempts=3,
    severity="critical",
    timeout=30.0
)
