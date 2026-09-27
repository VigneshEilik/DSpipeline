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
        Dispatches background job asynchronously in-process.
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
            if inspect.iscoroutinefunction(coro_or_func):
                asyncio.run(coro_or_func(*args, **kwargs))
            else:
                coro_or_func(*args, **kwargs)

    @classmethod
    def dispatch(
        cls,
        celery_task: Optional[Any],
        async_coro_func: Callable[..., Any],
        *args,
        **kwargs
    ):
        """
        Production-hardened dual-dispatch:
        - If USE_IN_PROCESS_WORKER is False and celery_task is provided, dispatches to Celery broker.
        - If Celery fails or USE_IN_PROCESS_WORKER is True, falls back to in-process execution safely.
        """
        if not settings.USE_IN_PROCESS_WORKER and celery_task is not None:
            try:
                res = celery_task.delay(*args, **kwargs)
                logger.info("Task dispatched to Celery worker: task_id=%s", res.id)
                return str(res.id)
            except Exception as e:
                logger.warning(
                    "Celery dispatch failed (%s). Falling back to in-process worker.",
                    str(e),
                )

        cls.run_task(async_coro_func, *args, **kwargs)
        return "in-process"

task_runner = TaskRunner()
