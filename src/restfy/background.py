import asyncio


class BackgroundTask:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    async def run(self):
        if asyncio.iscoroutinefunction(self.func):
            await self.func(*self.args, **self.kwargs)
        else:
            await asyncio.to_thread(self.func, *self.args, **self.kwargs)


class BackgroundTasks:
    def __init__(self):
        self._tasks: list[BackgroundTask] = []

    def add(self, func, *args, **kwargs):
        self._tasks.append(BackgroundTask(func, *args, **kwargs))

    async def run(self):
        for task in self._tasks:
            try:
                await task.run()
            except Exception as exc:
                print(f'Background task {task.func.__name__!r} raised: {exc}')

    def __bool__(self):
        return bool(self._tasks)
