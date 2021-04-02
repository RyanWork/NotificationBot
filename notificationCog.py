from datetime import datetime, timedelta
from discord.ext import commands, tasks
import asyncio

check_reminder_interval = 1.0


class NotificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lastRunTime = None
        self.ctx = None
        self.notification_text = None
        self.notification_link = None
        self.runInterval = 0
        self.ctxLock = asyncio.BoundedSemaphore()
        self.textLock = asyncio.BoundedSemaphore()
        self.linkLock = asyncio.BoundedSemaphore()
        self.runIntervalLock = asyncio.BoundedSemaphore()
        self.started = False

    @tasks.loop(seconds=check_reminder_interval)
    async def check_reminder(self):
        async with self.runIntervalLock:
            async with self.textLock:
                if (self.lastRunTime is None or self.lastRunTime + timedelta(seconds=self.runInterval) < datetime.now()) \
                        and self.notification_text is not None:
                    await self.send_reminder(self.notification_text)

    @commands.command()
    async def link(self, _, arg):
        async with self.linkLock:
            self.notification_link = arg

    @commands.command()
    async def text(self, _, arg):
        async with self.textLock:
            self.notification_text = arg

    @commands.command()
    async def interval(self, _, arg):
        try:
            parsed_int = int(arg)
            if parsed_int > check_reminder_interval:
                async with self.runIntervalLock:
                    self.runInterval = parsed_int
            else:
                await self.send("Value must be > {0}".format(check_reminder_interval))
        except ValueError:
            await self.send("Invalid value.")

    @commands.command()
    async def start(self, ctx):
        async with self.ctxLock:
            self.ctx = ctx

        if self.started is False:
            self.check_reminder.start()
            self.started = True

    @commands.command()
    async def stop(self, _):
        self.check_reminder.cancel()
        self.started = False

    @commands.command(name='set')
    async def set_text_and_link(self, _, *args):
        if len(args) < 0 or len(args) > 2:
            await self.send('Please provide two parameters.\r\n Ex: !set "Some kind of text" https://google.com')
            return

        self.notification_text = args[0]
        self.notification_link = args[1]

    @check_reminder.before_loop
    async def before_check_reminder_loop(self):
        await self.bot.wait_until_ready()

    async def send(self, message):
        async with self.ctxLock:
            await self.ctx.send(message)

    async def send_reminder(self, notification):
        self.lastRunTime = datetime.now()
        if notification is not None:
            async with self.linkLock:
                await self.send('{0}\n{1}'.format(notification,
                                                  self.notification_link if
                                                  self.notification_link is not None
                                                  else ""))
