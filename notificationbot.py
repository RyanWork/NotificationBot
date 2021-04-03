from discord.ext import commands
from notificationCog import NotificationCog
from dotenv import load_dotenv
import os

load_dotenv()
bot = commands.Bot(command_prefix='!')
bot.add_cog(NotificationCog(bot))
bot.run(os.environ.get('BOT_TOKEN'))
