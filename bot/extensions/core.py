from discord.ext import commands
from json import load as load_json

with open('bot/extensions/core_config.json', 'r', encoding='utf-8') as f:
    core_config = load_json(f)


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief=core_config['clear_brief'],
                      description=core_config['clear_description']
                      if (core_config['clear_description'] != '') else core_config['clear_brief'])
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx, amount=3):
        await ctx.channel.purge(limit=amount)

    @commands.command(aliases=['odoaldo'],
                      brief=core_config['info_brief'],
                      description=core_config['info_description']
                      if (core_config['info_description'] != '') else core_config['info_brief'])
    async def info(self, ctx):
        await ctx.send(core_config['info'])

    @commands.command(aliases=['marco'],
                      brief=core_config['ping_brief'],
                      description=core_config['ping_description']
                      if (core_config['ping_description'] != '') else core_config['ping_brief'])
    async def ping(self, ctx):
        await ctx.send(f":ping_pong: {'Polo' if ctx.message.content.lower() == '.marco' else 'Pong'}! "
                       f"with {str(round(self.bot.latency * 1000))}ms")

    @commands.command(aliases=['chisono'],
                      brief=core_config['whoami_brief'],
                      description=core_config['whoami_description']
                      if (core_config['whoami_description'] != '') else core_config['whoami_brief'])
    async def whoami(self, ctx):
        await ctx.send(f"You are {ctx.message.author.mention}")


def setup(bot):
    bot.add_cog(Core(bot))
