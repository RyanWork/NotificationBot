from datetime import datetime, timedelta
from discord.ext import commands, tasks
import asyncio


class NotificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.lastRunTime = None
        self.notificationText = None
        self.notificationLink = None
        self.runInterval = 0
        self.ctx = None
        self.ctxLock = asyncio.Lock()
        self.started = False

    @tasks.loop(seconds=10.0)
    async def check_reminder(self):
        if (self.lastRunTime is None or self.lastRunTime + timedelta(seconds=self.runInterval) < datetime.now()) \
                and self.notificationText is not None:
            await self.send_reminder(self.ctx, self.notificationText)

        await self.ctx.send('lastRunTime is: {0}'.format(self.lastRunTime))

    @check_reminder.after_loop
    async def on_check_remind_cancel(self):
        print("done")
        return

    @commands.command()
    async def link(self, _, arg):
        self.notificationLink = arg
        return

    @commands.command()
    async def text(self, _, arg):
        self.notificationText = arg
        return

    @commands.command()
    async def interval(self, _, arg):
        self.runInterval = arg
        return

    @commands.command()
    async def start(self, ctx):
        async with self.ctxLock:
            self.ctx = ctx

        if self.started is False:
            self.check_reminder.start()

        return

    @commands.command(name='set')
    async def set_text_and_link(self, ctx, *args):
        if len(args) < 0 or len(args) > 2:
            await ctx.send('Please provide two parameters.\r\n Ex: !set "Some kind of text" https://google.com')
            return

        self.notificationText = args[0]
        self.notificationLink = args[1]
        await ctx.send('Set: {0} and {1}'.format(args[0], args[1]))
        return

    @check_reminder.before_loop
    async def before_check_reminder_loop(self):
        await self.bot.wait_until_ready()

    async def send_reminder(self, ctx, notification):
        if notification is not None:
            await ctx.send('{0}\n{1}'.format(notification,
                                             self.notificationLink if
                                             self.notificationLink is not None
                                             else ""))
        self.lastRunTime = datetime.now()
