from datetime import datetime, timedelta
from discord.ext import commands, tasks
from notification import notification

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
        self.notificationList = {}
        self.check_reminder.start()

    @tasks.loop(seconds=check_reminder_interval)
    async def check_reminder(self):
        """
        Process if any reminders need to be sent
        Loops every check_reminder_interval to check if any reminders need to be sent.
        Compares if the last time the message has been sent has elapsed the requested interval.
        """
        for _, reminder in self.notificationList.items():
            if reminder.started and (reminder.lastRunTime is None
                                     or reminder.lastRunTime + timedelta(seconds=reminder.runInterval)
                                     < datetime.now()):
                await reminder.send_reminder()

    @commands.command()
    async def create(self, ctx, *args):
        """
        Create a new reminder.
        Ex. !create "some_key" 5 minutes "some_text" "some_link (OPTIONAL)"
        :param ctx: The context from which a message was received.
        :param args: passed list of arguments to the create method
        """
        if len(args) < 4:
            await ctx.send("Invalid number of arguments.")
            return -1
        if args[0] in self.notificationList:
            await ctx.send("Reminder {0} already exists.".format(args[0]))
            return -1

        interval = parse_interval(args[1], args[2])
        if interval < 0:
            await ctx.send("Invalid interval provided")

        reminder = notification()
        reminder.ctx = ctx
        reminder.runInterval = interval
        reminder.notification_text = args[3]
        reminder.notification_link = args[4]
        self.notificationList[args[0]] = reminder
        await ctx.send("{0} was successfully created.".format(args[0]))
        return reminder

    @commands.command()
    async def list(self, ctx):
        """
        List all reminders that have been created
        :param ctx:
        :return:
        """
        if len(self.notificationList) > 0:
            await ctx.send(
                wrap_code_block(
                    "\n".join("{0}\t\t{1}".format(i + 1, key) for i, key in enumerate(self.notificationList))))

    @commands.command()
    async def status(self, ctx, arg):
        """
        Retrieve the current status of the specified reminder
        :param ctx: the context of where the command was received
        :param arg: the key of the notification to get the status of
        :return:
        """
        if await self.is_key_valid(ctx, arg):
            reminder = self.notificationList[arg]
            interval_unit = get_time_unit(reminder.runInterval)
            await ctx.send(wrap_code_block(
                "Name: {0}\r\n"
                "Current Text: {1}\r\n"
                "Current Link: {2}\r\n"
                "Running Interval: {3} {4}(s)\r\n"
                "Running: {5}\r\n"
                "Last Ran: {6}".format(arg,
                                       reminder.notification_text,
                                       reminder.notification_link,
                                       round(reminder.runInterval / interval_lookup[interval_unit], 2),
                                       interval_unit,
                                       reminder.started,
                                       reminder.lastRunTime)))

    @commands.command()
    async def start(self, ctx, arg):
        """
        Start sending notifications for the specified key
        Ex: !Start "some_key"
        :param ctx: the context of where the command was received
        :param arg: the key of the notification to start
        :return: a boolean indicating if the notification was successfully started
        """
        if await self.is_key_valid(ctx, arg):
            await self.notificationList[arg].set_started(True)
            return True

        return False

    @commands.command()
    async def stop(self, ctx, arg):
        """
        Stop sending notifications for the specified key
        Ex. !stop "some_key"
        :param ctx: the context of where the command was received
        :param arg: the key of the notification to stop
        :return: a boolean indicating if the notification was successfully stopped
        """
        if await self.is_key_valid(ctx, arg):
            await self.notificationList[arg].set_started(False)
            return True

        return False

    @commands.command()
    async def link(self, ctx, *args):
        """
        Set the link at the specified notification
        Ex. !link "some_key" "https://google.com"
        :param ctx: the context of where the command was received
        :param args: the key of the notification to set the link
        :return: a boolean indicating if the notification link was successfully set
        """
        if await self.is_key_valid(ctx, args[0]):
            await self.notificationList[args[0]].set_link(args[1])
            return True

        return False

    @commands.command()
    async def text(self, ctx, *args):
        """
        Set the text at the specified notification
        Ex. !link "some_key" "some_text"
        :param ctx: the context of where the command was received
        :param args: the key of the notification to set the text
        :return: a boolean indicating if the notification text was successfully set
        """
        if await self.is_key_valid(ctx, args[0]):
            await self.notificationList[args[0]].set_text(args[1])
            return True

        return False

    @check_reminder.before_loop
    async def before_check_reminder_loop(self):
        await self.bot.wait_until_ready()

    async def is_key_valid(self, ctx, key):
        """
        Check if a key already exists and send a message if it does not
        :param ctx: The context of where to send the message
        :param key: The requested key to check if it exists/does not exist
        :return: A boolean indicating if a the key is valid or not
        """
        if key in self.notificationList:
            return True
        else:
            await ctx.send("Reminder {0} does not exist.".format(key))
            return False


def parse_interval(interval, interval_unit):
    """
    Parses a provided interval to see if it is valid.
    Also returns the associated unit that is formatted correctly.
    :param interval: The interval string that was entered.
    :param interval_unit: The unit of time provided for the interval.
    :return: The actual interval based off the time factor.
    """
    time_factor = 1
    if interval_unit is not None:
        time_unit = interval_unit.lower().rstrip('s')
        if time_unit in interval_lookup:
            time_factor = interval_lookup[time_unit]
    try:
        parsed_interval = int(interval)
        if parsed_interval * time_factor > check_reminder_interval:
            return parsed_interval * time_factor
        else:
            return -1
    except ValueError:
        return -1


def wrap_code_block(message):
    return "```\r\n{0}\r\n```".format(message)


def get_time_unit(interval):
    for key in reversed(interval_lookup):
        if interval / interval_lookup[key] >= 1:
            return key
