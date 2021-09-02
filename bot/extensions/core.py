from json import load as load_json

from discord import Embed
from discord.ext import commands

with open('bot/bot_config.json', 'r', encoding='utf-8') as f:
    bot_config = load_json(f)
with open('bot/extensions/core_config.json', 'r', encoding='utf-8') as f:
    core_config = load_json(f)


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embeds_color = int(core_config['embeds_color'], 16)

    @commands.command(brief=core_config['clear_brief'],
                      description=core_config['clear_description'])
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx, amount=3):
        await ctx.channel.purge(limit=amount)

    @commands.command(aliases=['odoaldo'],
                      brief=core_config['info_brief'],
                      description=core_config['info_description'])
    async def info(self, ctx):
        embed_msg = Embed(title=bot_config['name'], color=self.embeds_color)
        embed_msg.add_field(name='Version', value=f"`{bot_config['version']}`")
        embed_msg.add_field(name='Source', value=f"[GitHub repository]({bot_config['url']})", inline=True)
        embed_msg.add_field(name='\u200b', value='\u200b', inline=True)
        embed_msg.add_field(name='License', value=bot_config['license'])
        embed_msg.add_field(name='Author', value=bot_config['author'], inline=True)
        embed_msg.add_field(name='\u200b', value='\u200b', inline=True)
        embed_msg.add_field(name='\u200b', value=core_config['info'], inline=False)
        await ctx.send(embed=embed_msg)

    @commands.command(aliases=['marco'],
                      brief=core_config['ping_brief'],
                      description=core_config['ping_description'])
    async def ping(self, ctx):
        embed_msg = Embed(
            description=f":ping_pong: {'Polo' if ctx.message.content.lower() == '.marco' else 'Pong'}! "
                        f"with {str(round(self.bot.latency * 1000))}ms",
            color=self.embeds_color)
        await ctx.send(embed=embed_msg)

    @commands.command(aliases=['chisono'],
                      brief=core_config['whoami_brief'],
                      description=core_config['whoami_description'])
    async def whoami(self, ctx):
        embed_msg = Embed(description=f"You are {ctx.message.author.mention}", color=self.embeds_color)
        await ctx.send(embed=embed_msg)


def setup(bot):
    bot.add_cog(Core(bot))


def teardown(bot):
    bot.remove_cog(Core(bot))
