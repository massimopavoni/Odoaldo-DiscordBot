from io import StringIO
from json import load as json_load
from logging import getLogger
from os.path import join as path_join

from arithmetic_dice_roller.roller import Roller as ArithmeticDiceRoller, RollerError as ArithmeticDiceRollerError
from discord import Embed as DiscordEmbed, File as DiscordFile
from discord.ext import commands as discord_commands

# Setting up extension logger
logger = getLogger(__name__.split('.', 1)[-1])

# Get extension level config
with open(path_join('bot', 'src', 'extensions', 'games.json'), 'r', encoding='utf-8') as f:
    _config = json_load(f)


class Games(discord_commands.Cog):
    """
    Games bot extension.
    """

    def __init__(self, bot):
        self.bot = bot
        self.description = _config['extension_description']
        self.__embeds_color = int(_config['embeds_color'], 16)

    @discord_commands.command(aliases=['r', 'rolldice', 'rolld', 'rdice', 'rd'],
                              brief=_config['roll_brief'],
                              description=_config['roll_description'])
    async def roll(self, ctx: discord_commands.Context,
                   expression: str = discord_commands.parameter(description=_config['roll_expression']),
                   *,
                   label: str = discord_commands.parameter(default=None, description=_config['roll_label'])):
        # Create roller for expression
        roller = ArithmeticDiceRoller(expression, label)
        try:
            roller.roll()
            # Compose embed with roll information
            embed_msg = DiscordEmbed(title=roller.label if roller.label else "No label roll", color=self.__embeds_color)
            embed_msg.add_field(name="Requested by", value=ctx.author.mention)
            embed_msg.add_field(name="Original expression", value=f"```{roller.expression}```", inline=False)
            # And create text file with full roll breakdown
            file_roll_info = StringIO()
            file_roll_info.write(f"Original expression:\n{roller.expression}\n\n"
                                 f"Expanded expression:\n{roller.no_nx_expression}\n\n"
                                 f"Rolls:\n" + '\n'.join(f" - {roll[0]} = {roll[1]} {roll[2]}" for roll in roller.rolls)
                                 + "\n\n" + f"Evaluated expression:\n{roller.no_dice_expression}\n\n"
                                            f"Final result: {roller.final_result}")
            file_roll_info.seek(0)
            embed_msg.add_field(name="Final result", value=f"```{roller.final_result}```")
            # Send both message and text file
            await ctx.send(embed=embed_msg)
            await ctx.send(file=DiscordFile(file_roll_info, 'rollinfo.txt'))
        except ArithmeticDiceRollerError as error:
            raise discord_commands.CommandInvokeError(error)


async def setup(bot):
    await bot.add_cog(Games(bot))


async def teardown(bot):
    await bot.remove_cog(Games(bot))
