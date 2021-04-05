import asyncio
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
special_interval_dictionary = {
    "daily": 86400,
    "weekly": 604800,
    "monthly": 2419200,
    "annually": 29030400
}


class NotificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notificationList = {}
        self.notificationListLock = asyncio.BoundedSemaphore()
        self.check_reminder.start()

    @tasks.loop(seconds=check_reminder_interval)
    async def check_reminder(self):
        """
        Process if any reminders need to be sent.
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
        :param args: passed list of arguments to the create method.
        :return: The reminder object that was created.
        """
        if len(args) < 1:
            await ctx.send("Invalid number of arguments.")
            return -1

        async with self.notificationListLock:
            if args[0] is not None and args[0] in self.notificationList:
                await ctx.send("Reminder _{0}_ already exists".format(args[0]))
                return -1

        interval = parse_interval(args[1], args[2] if len(args) >= 3 else None) if len(args) >= 2 else 0
        if interval < 0:
            await ctx.send("Invalid interval provided")
            return -1

        reminder = notification()
        reminder.ctx = ctx
        reminder.runInterval = interval
        reminder.notification_text = None if len(args) <= 3 else args[3]
        reminder.notification_link = None if len(args) <= 4 else args[4]
        async with self.notificationListLock:
            self.notificationList[args[0]] = reminder
        await ctx.send("Reminder _{0}_ was successfully created.".format(args[0]))
        return reminder

    @commands.command()
    async def delete(self, ctx, arg):
        """
        Delete a reminder that was created.
        :param ctx: The context from where the message was sent.
        :param arg: The key of the reminder to delete.
        """
        if await self.is_key_valid(ctx, arg):
            async with self.notificationListLock:
                del self.notificationList[arg]
            await ctx.send("Reminder _{0}_ was successfully deleted.".format(arg))

    @commands.command()
    async def list(self, ctx):
        """
        List all reminders that have been created.
        :param ctx: The context from where the message was sent..
        """
        if len(self.notificationList) > 0:
            async with self.notificationListLock:
                await ctx.send(
                    wrap_code_block(
                        "\n".join("{0}\t\t{1}".format(i + 1, key) for i, key in enumerate(self.notificationList))))

    @commands.command()
    async def status(self, ctx, arg):
        """
        Retrieve the current status of the specified reminder.
        :param ctx: the context of where the command was received.
        :param arg: the key of the notification to get the status of.
        """
        if await self.is_key_valid(ctx, arg):
            reminder = await self.get_reminder(arg)
            interval_unit = get_time_unit(reminder.runInterval)
            await ctx.send(wrap_code_block(
                "Name: {0}\r\n"
                "Current Text: {1}\r\n"
                "Current Link: {2}\r\n"
                "Running Interval: {3} {4}(s)\r\n"
                "Running: {5}\r\n"
                "Last Ran: {6}".format(arg,
                                       reminder.notification_text if reminder.notification_text is not None else "N/A",
                                       reminder.notification_link if reminder.notification_link is not None else "N/A",
                                       round(reminder.runInterval / interval_lookup[interval_unit], 2),
                                       interval_unit,
                                       reminder.started,
                                       reminder.lastRunTime if reminder.lastRunTime is not None else "N/A")))

    @commands.command()
    async def start(self, ctx, arg):
        """
        Start sending notifications for the specified key.
        Ex: !Start "some_key"
        :param ctx: the context of where the command was received.
        :param arg: the key of the notification to start.
        :return: a boolean indicating if the notification was successfully started.
        """
        if await self.is_key_valid(ctx, arg):
            reminder = await self.get_reminder(arg)
            if reminder.notification_text is None:
                await ctx.send("You must set a notification text for _{0}_\r\n"
                               "Ex. !text {0} \"Hello World\"".format(arg))
                return False
            elif reminder.runInterval is None or reminder.runInterval <= 0:
                await ctx.send("You must set a valid run interval for _{0}_\r\n"
                               "Ex. !interval {0} 10 seconds".format(arg))
                return False
            else:
                await reminder.set_started(True)
                await ctx.send("Reminder _{0}_ was started.".format(arg))
                return True

        return False

    @commands.command()
    async def stop(self, ctx, arg):
        """
        Stop sending notifications for the specified key.
        Ex. !stop "some_key"
        :param ctx: the context of where the command was received.
        :param arg: the key of the notification to stop.
        :return: a boolean indicating if the notification was successfully stopped.
        """
        if await self.is_key_valid(ctx, arg):
            reminder = await self.get_reminder(arg)
            await reminder.set_started(False)
            await ctx.send("Reminder _{0}_ was stopped.".format(arg))
            return True

        return False

    @commands.command()
    async def link(self, ctx, *args):
        """
        Set the link at the specified notification.
        Ex. !link "some_key" "https://google.com".
        :param ctx: the context of where the command was received.
        :param args: the key of the notification to set the link.
        :return: a boolean indicating if the notification link was successfully set.
        """
        if await self.is_key_valid(ctx, args[0]):
            reminder = await self.get_reminder(args[0])
            await reminder.set_link(args[1])
            await ctx.send("Updated link for _{0}_.".format(args[0]))
            return True

        return False

    @commands.command()
    async def text(self, ctx, *args):
        """
        Set the text at the specified notification.
        Ex. !link "some_key" "some_text"
        :param ctx: The context of where the command was received.
        :param args: The key of the notification to set the text.
        :return: a boolean indicating if the notification text was successfully set.
        """
        if await self.is_key_valid(ctx, args[0]):
            reminder = await self.get_reminder(args[0])
            await reminder.set_text(args[1])
            await ctx.send("Updated text for _{0}_.".format(args[0]))
            return True

        return False

    @commands.command()
    async def interval(self, ctx, *args):
        """
        Set the interval of the specified reminder.
        :param ctx: The context of where the command was received.
        :param args: The arguments containing the key to update and the specified interval to set it to.
        :return: The interval that it was set to.
        """
        if await self.is_key_valid(ctx, args[0]):
            interval = parse_interval(args[1], args[2]) if len(args) >= 3 else -1
            if interval < 0:
                await ctx.send("Invalid interval provided\r\n"
                               "Ex. !interval 10 seconds")
                return -1

            reminder = await self.get_reminder(args[0])
            await reminder.set_interval(interval)
            await ctx.send("Interval for {0} updated.".format(args[0]))
            return interval

    @check_reminder.before_loop
    async def before_check_reminder_loop(self):
        """
        Ensure that the bot is ready before we begin looping
        """
        await self.bot.wait_until_ready()

    async def is_key_valid(self, ctx, key):
        """
        Check if a key already exists and send a message if it does not.
        :param ctx: The context of where to send the message.
        :param key: The requested key to check if it exists/does not exist.
        :return: A boolean indicating if a the key is valid or not.
        """
        async with self.notificationListLock:
            if key in self.notificationList:
                return True
            else:
                await ctx.send("Reminder _{0}_ does not exist.".format(key))
                return False

    async def get_reminder(self, key):
        """
        Get the reminder at the specified key.
        :param key: The key to search in the dictionary.
        :return: The reminder object at the specified key.
        """
        async with self.notificationListLock:
            return self.notificationList[key]


def parse_interval(interval, interval_unit):
    """
    Parses a provided interval to see if it is valid.
    Also returns the associated unit that is formatted correctly.
    :param interval: The interval string that was entered.
    :param interval_unit: The unit of time provided for the interval.
    :return: The actual interval based off the time factor.
    """
    if interval in special_interval_dictionary:
        return special_interval_dictionary[interval]

    time_factor = 1
    if interval_unit is not None:
        time_unit = interval_unit.lower().rstrip('s')
        if time_unit in interval_lookup:
            time_factor = interval_lookup[time_unit]
    try:
        parsed_interval = float(interval)
        if parsed_interval * time_factor > check_reminder_interval:
            return parsed_interval * time_factor
        else:
            return -1
    except ValueError:
        return -1


def wrap_code_block(message):
    """
    Wrap a message in a discord code block
    :param message: The message to wrap
    :return: A message wrapped in a code block
    """
    return "```\r\n{0}\r\n```".format(message)


def get_time_unit(interval):
    """
    Get the associated time unit that fits the interval best
    :param interval: The interval in seconds
    :return: The unit of time that best fits
    """
    for key in reversed(interval_lookup):
        if interval / interval_lookup[key] >= 1:
            return key

    return "second"
