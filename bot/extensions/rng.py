from json import load as json_load

from arithmetic_dice_roller.roller import Roller, RollerError

from discord import Embed
from discord.ext import commands

with open('bot/extensions/rng_config.json', 'r', encoding='utf-8') as f:
    rng_config = json_load(f)


class RNG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embeds_color = int(rng_config['embeds_color'], 16)

    @commands.command(aliases=['r', 'rolldice', 'rolld', 'rdice', 'rd'],
                      brief=rng_config['roll_brief'],
                      description=rng_config['roll_description'])
    async def roll(self, ctx, expression, *label):
        roller = Roller(expression, ' '.join(label))
        try:
            roller.roll()
        except RollerError as error:
            pass


def setup(bot):
    bot.add_cog(RNG(bot))


def teardown(bot):
    bot.remove_cog(RNG(bot))
