import discord
from datetime import date
from discord.ext import commands

client = commands.Bot(command_prefix='!')
lastRunTime = None
notificationLink = None
notificationText = None


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.command()
async def link(ctx, arg):
    global notificationLink
    notificationLink = arg
    await ctx.send('Set: {0}'.format(arg))
    return


@client.command()
async def text(ctx, arg):
    global notificationText
    notificationText = arg
    await ctx.send('Set: {0}'.format(arg))
    return


@client.command(name='set')
async def set_text_and_link(ctx, *args):
    if len(args) != 2:
        await ctx.send('Please provide two parameters.\r\n Ex: !set "Some kind of text" https://google.com')
        return

    global notificationText, notificationLink
    notificationText = args[0]
    notificationLink = args[1]
    await ctx.send('Set: {0} and {1}'.format(args[0], args[1]))
    return


@client.event
async def on_message(message):
    global lastRunTime, notificationText
    if message.author == client.user:
        return

    await client.process_commands(message)

    if (lastRunTime is None or lastRunTime < date.today()) and notificationText is not None:
        await send_reminder(message, notificationText)

    await message.channel.send('lastRunTime is: {0}'.format(lastRunTime))


async def send_reminder(message, notification):
    global lastRunTime
    if notification is not None:
        await message.channel.send('{0}\n{1}'.format(notification, notificationLink))

    lastRunTime = date.today()


client.run('ODI3MDMxMTIwODg4NDYzMzcw.YGVGwA.R7Q_VkZttU-2RSXxKiW4Cjb27TI')