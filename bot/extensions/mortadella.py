from discord import Embed
from discord.ext import commands
from json import load as load_json

with open('bot/extensions/mortadella_config.json', 'r', encoding='utf-8') as f:
    mortadella_config = load_json(f)


class Mortadella(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embeds_color = int(mortadella_config['embeds_color'], 16)

    @commands.command(aliases=['morta', 'della', 'mortade'],
                      brief=mortadella_config['mortadella_brief'],
                      description=mortadella_config['mortadella_description'])
    async def mortadella(self, ctx):
        embed_msg = Embed(title=mortadella_config['mortadella'], color=self.embeds_color)
        await ctx.send(embed=embed_msg)


def setup(bot):
    bot.add_cog(Mortadella(bot))


def teardown(bot):
    bot.remove_cog(Mortadella(bot))
