from datetime import datetime, timedelta
from discord.ext import commands, tasks
import asyncio

check_reminder_interval = 1.0


class NotificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.lastRunTime = None
        self.notificationText = None
        self.notificationLink = None
        self.runInterval = 0
        self.ctx = None
        self.ctxLock = asyncio.BoundedSemaphore()
        self.started = False

    @tasks.loop(seconds=check_reminder_interval)
    async def check_reminder(self):
        if (self.lastRunTime is None or self.lastRunTime + timedelta(seconds=self.runInterval) < datetime.now()) \
                and self.notificationText is not None:
            await self.send_reminder(self.ctx, self.notificationText)

    @commands.command()
    async def link(self, _, arg):
        self.notificationLink = arg

    @commands.command()
    async def text(self, _, arg):
        self.notificationText = arg

    @commands.command()
    async def interval(self, ctx, arg):
        try:
            parsed_int = int(arg)
            if parsed_int > check_reminder_interval:
                self.runInterval = parsed_int
            else:
                await ctx.send("Value must be > {0}".format(check_reminder_interval))
        except ValueError:
            await ctx.send("Invalid value.")

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
    async def set_text_and_link(self, ctx, *args):
        if len(args) < 0 or len(args) > 2:
            await ctx.send('Please provide two parameters.\r\n Ex: !set "Some kind of text" https://google.com')
            return

        self.notificationText = args[0]
        self.notificationLink = args[1]

    @check_reminder.before_loop
    async def before_check_reminder_loop(self):
        await self.bot.wait_until_ready()

    async def send_reminder(self, ctx, notification):
        if notification is not None:
            async with self.ctxLock:
                await ctx.send('{0}\n{1}'.format(notification,
                                                 self.notificationLink if
                                                 self.notificationLink is not None
                                                 else ""))
        self.lastRunTime = datetime.now()
