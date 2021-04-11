import asyncio
from dataclasses import dataclass
from datetime import datetime


@dataclass
class notification:
    ctx = None
    runInterval = 0
    notification_text = None
    notification_link = None
    started = False
    ctxLock = asyncio.BoundedSemaphore()
    textLock = asyncio.BoundedSemaphore()
    linkLock = asyncio.BoundedSemaphore()
    runIntervalLock = asyncio.BoundedSemaphore()
    startLock = asyncio.BoundedSemaphore()
    lastRunTime = None

    async def set_link(self, link):
        async with self.linkLock:
            self.notification_link = link
        return self.notification_link

    async def set_text(self, text):
        async with self.textLock:
            self.notification_text = text
        return self.notification_text

    async def set_interval(self, interval):
        async with self.runIntervalLock:
            self.runInterval = interval
        return self.runInterval

    async def set_started(self, running_state):
        async with self.startLock:
            self.started = running_state
        return self.started

    async def set_ctx(self, ctx):
        async with self.ctxLock:
            self.ctx = ctx
        return self.ctx

    async def send(self, message):
        async with self.ctxLock:
            await self.ctx.send(message)

    async def send_reminder(self):
        self.lastRunTime = datetime.now()
        if self.notification_text is not None:
            async with self.textLock:
                async with self.linkLock:
                    await self.send('{0}\n{1}'.format(self.notification_text,
                                                      self.notification_link if
                                                      self.notification_link is not None
                                                      else ""))
