from discord.ext import commands
from notificationCog import NotificationCog


bot = commands.Bot(command_prefix='!')
bot.add_cog(NotificationCog(bot))
bot.run('ODI3MDMxMTIwODg4NDYzMzcw.YGVGwA.R7Q_VkZttU-2RSXxKiW4Cjb27TI')
