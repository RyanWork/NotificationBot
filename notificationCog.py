from datetime import datetime, timedelta
from discord.ext import commands, tasks
import asyncio

check_reminder_interval = 1.0
interval_lookup = {
    "second": 1,
    "minute": 60,
    "hour": 3600,
    "day": 86400,
    "week": 604800,
    "month": 2419200
}


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
        """
        Process if any reminders need to be sent
        Loops every check_reminder_interval to check if any reminders need to be sent.
        Compares if the last time the message has been sent has elapsed the requested interval.
        """
        async with self.runIntervalLock:
            async with self.textLock:
                if (self.lastRunTime is None
                    or self.lastRunTime + timedelta(seconds=self.runInterval) < datetime.now()) \
                        and self.notification_text is not None:
                    await self.send_reminder(self.notification_text)

    @commands.command()
    async def create(self, ctx, arg):
        """
        Create a new reminder.
        :param ctx: The context from which a message was received.
        :param arg:
        """
        return

    @commands.command()
    async def link(self, _, arg):
        """
        Attach a link to a reminder
        :param arg:
        :param _:
        :return:
        """
        async with self.linkLock:
            self.notification_link = arg

    @commands.command()
    async def text(self, _, arg):
        async with self.textLock:
            self.notification_text = arg

    @commands.command()
    async def interval(self, _, *args):
        """
        Set the interval for how often the reminder should be sent.
        If no time unit is specified, assume seconds.
        :param args: list of arguments passed to the interval method
        :param _:
        :return:
        """
        if len(args) < 0:
            await self.send("Ex. !interval 10 days")

        time_factor = 1
        if args[1] is not None:
            time_unit = args[1].lower().rstrip('s')
            if time_unit in interval_lookup:
                time_factor = interval_lookup[time_unit]

        try:
            parsed_int = int(args[0])
            if parsed_int * time_factor > check_reminder_interval:
                async with self.runIntervalLock:
                    self.runInterval = parsed_int * time_factor
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
