import discord

client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run('ODI3MDMxMTIwODg4NDYzMzcw.YGVGwA.R7Q_VkZttU-2RSXxKiW4Cjb27TI')