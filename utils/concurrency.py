import asyncio
from threading import Thread
from framework.logger.providers import get_logger

logger = get_logger(__name__)


class DeferredTasks:
    def __init__(self, *args):
        self._tasks = args or []

    def add_task(self, coroutine):
        self._tasks.append(coroutine)
        return self

    def add_tasks(self, *args):
        self._tasks.extend(args)
        return self

    async def run(self):
        if any(self._tasks):
            return await asyncio.gather(*self._tasks)


class AsyncHelper:
    MaxThreadWorkers = 12
    Semaphore = asyncio.Semaphore(MaxThreadWorkers)

    @classmethod
    async def run_async(cls, coroutine):
        await coroutine

    @classmethod
    def threaded_event_loop(cls, coroutine):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(coroutine, loop)

    @classmethod
    def run_threaded_async(cls, coroutine):
        thread = Thread(
            target=cls.threaded_event_loop,
            args=(coroutine,))
        return thread


class SemaphoreProviderFactory:
    def create_provider(
        self,
        value: int,
        name: str
    ) -> 'SemaphoreProviderFactory':

        self.__name = name
        self.__semaphore = asyncio.Semaphore(value)

        return self

    async def __aenter__(self):
        logger.info(f'Acquire: {self.__name}')

        await self.__semaphore.acquire()

    async def __aexit__(
        self,
        *args
    ) -> None:
        '''
        Release semaphore on async exit
        '''

        logger.info(f'Release: {self.__name}')

        self.__semaphore.release()
