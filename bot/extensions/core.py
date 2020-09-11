from discord.ext import commands
from json import load as load_json


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('bot\\extensions\\core_config.json', 'r') as f:
            self.core_config = load_json(f)

    @commands.command(aliases=['odoaldo'])
    async def info(self, ctx):
        await ctx.send(self.core_config['odoaldo_info'])

    @commands.command(aliases=['chisono'])
    async def whoami(self, ctx):
        await ctx.send(f"You are {ctx.message.author.name}")

    @commands.command(aliases=['marco'])
    async def ping(self, ctx):
        await ctx.send(f"🏓 {'Polo' if ctx.message.content.lower() == '.marco' else 'Pong'}! "
                       f"with {str(round(self.bot.latency * 1000))}ms")

    @commands.command(aliases=['morta', 'della', 'mortade'])
    async def mortadella(self, ctx):
        await ctx.send("**Inhales deeply**\n\n*Dove? Dimmelo.*")

    @commands.command()
    async def clear(self, ctx, amount=3):
        await ctx.channel.purge(limit=amount)


def setup(bot):
    bot.add_cog(Core(bot))
