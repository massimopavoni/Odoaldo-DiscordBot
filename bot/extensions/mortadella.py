from json import load as json_load
from random import choice as random_choice

from discord import Embed as DiscordEmbed
from discord.ext import commands as discord_commands

with open('bot/extensions/mortadella_config.json', 'r', encoding='utf-8') as f:
    mortadella_config = json_load(f)
with open('bot/extensions/mortadella_bad_food_jokes.json', 'r', encoding='utf-8') as f:
    bad_food_jokes = json_load(f)['bad_food_jokes']


class Mortadella(discord_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embeds_color = int(mortadella_config['embeds_color'], 16)

    @discord_commands.command(aliases=['morta', 'della', 'mortade'],
                              brief=mortadella_config['mortadella_brief'],
                              description=mortadella_config['mortadella_description'])
    async def mortadella(self, ctx):
        embed_msg = DiscordEmbed(title=mortadella_config['mortadella_message'], color=self.embeds_color)
        await ctx.send(embed=embed_msg)

    @discord_commands.command(aliases=['foodjoke', 'badjoke', 'joke'],
                              brief=mortadella_config['badfoodjoke_brief'],
                              description=mortadella_config['badfoodjoke_description'])
    async def badfoodjoke(self, ctx):
        embed_msg = DiscordEmbed(description=random_choice(bad_food_jokes), color=self.embeds_color)
        await ctx.send(embed=embed_msg)


def setup(bot):
    bot.add_cog(Mortadella(bot))


def teardown(bot):
    bot.remove_cog(Mortadella(bot))
