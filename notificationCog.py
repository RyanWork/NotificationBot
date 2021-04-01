from datetime import date
from discord.ext import commands


class NotificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.lastRunTime = None
        self.notificationText = None
        self.notificationLink = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if (self.lastRunTime is None or self.lastRunTime < date.today()) and self.notificationText is not None:
            await self.send_reminder(message, self.notificationText)

        await message.channel.send('lastRunTime is: {0}'.format(self.lastRunTime))

    @commands.command()
    async def link(self, ctx, arg):
        self.notificationLink = arg
        await ctx.send('Set: {0}'.format(arg))
        return

    @commands.command()
    async def text(self, ctx, arg):
        self.notificationText = arg
        await ctx.send('Set: {0}'.format(arg))
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

    async def send_reminder(self, message, notification):
        if notification is not None:
            await message.channel.send('{0}\n{1}'.format(notification,
                                                         self.notificationLink if
                                                         self.notificationLink is not None
                                                         else ""))
        self.lastRunTime = date.today()