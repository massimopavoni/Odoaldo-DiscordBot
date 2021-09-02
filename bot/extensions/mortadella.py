import random
from json import load as load_json

from discord import Embed
from discord.ext import commands

with open('bot/extensions/mortadella_config.json', 'r', encoding='utf-8') as f:
    mortadella_config = load_json(f)
with open('bot/extensions/mortadella_bad_food_jokes.json', 'r', encoding='utf-8') as f:
    bad_food_jokes = load_json(f)['bad_food_jokes']


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

    @commands.command(aliases=['foodjoke', 'badjoke', 'joke'],
                      brief=mortadella_config['badfoodjoke_brief'],
                      description=mortadella_config['badfoodjoke_description'])
    async def badfoodjoke(self, ctx):
        embed_msg = Embed(description=random.choice(bad_food_jokes), color=self.embeds_color)
        await ctx.send(embed=embed_msg)


def setup(bot):
    bot.add_cog(Mortadella(bot))


def teardown(bot):
    bot.remove_cog(Mortadella(bot))
