import asyncio
import inspect
import logging
from typing import Any, Callable, Coroutine, Dict, Optional
from apps.api.app.core.config import settings

logger = logging.getLogger("modelops.tasks")

class TaskRunner:
    @staticmethod
    def run_task(coro_or_func: Callable[..., Any], *args, **kwargs):
        """
        Dispatches background job asynchronously.
        If a coroutine is provided, runs as asyncio task in event loop.
        If synchronous function is provided, runs in thread pool.
        """
        try:
            loop = asyncio.get_running_loop()
            if inspect.iscoroutinefunction(coro_or_func):
                loop.create_task(coro_or_func(*args, **kwargs))
            else:
                loop.run_in_executor(None, lambda: coro_or_func(*args, **kwargs))
        except RuntimeError:
            # No running event loop (e.g. background worker thread)
            if inspect.iscoroutinefunction(coro_or_func):
                asyncio.run(coro_or_func(*args, **kwargs))
            else:
                coro_or_func(*args, **kwargs)

task_runner = TaskRunner()
