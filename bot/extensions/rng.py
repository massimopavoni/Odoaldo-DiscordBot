from io import StringIO
from json import load as json_load

from arithmetic_dice_roller.roller import Roller as ArithmeticDiceRoller, RollerError as ArithmeticDiceRollerError
from discord import Embed as DiscordEmbed, File as DiscordFile
from discord.ext import commands as discord_commands

with open('bot/extensions/rng_config.json', 'r', encoding='utf-8') as f:
    rng_config = json_load(f)


class RNG(discord_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embeds_color = int(rng_config['embeds_color'], 16)

    @discord_commands.command(aliases=['r', 'rolldice', 'rolld', 'rdice', 'rd'],
                              brief=rng_config['roll_brief'],
                              description=rng_config['roll_description'])
    async def roll(self, ctx, expression, *label):
        roller = ArithmeticDiceRoller(expression, ' '.join(label))
        try:
            roller.roll()
            embed_msg = DiscordEmbed(title=roller.label if roller.label else "No label roll", color=self.embeds_color)
            embed_msg.add_field(name="Requested by", value=ctx.message.author.mention)
            embed_msg.add_field(name="Original expression", value=f"```{roller.expression}```", inline=False)
            file_roll_info = StringIO()
            file_roll_info.write(f"Original expression:\n{roller.expression}\n\n"
                                 f"Expanded expression:\n{roller.no_nx_expression}\n\n"
                                 f"Rolls:\n" + '\n'.join(f" - {roll[0]} = {roll[1]} {roll[2]}" for roll in roller.rolls)
                                 + "\n\n" + f"Evaluated expression:\n{roller.no_dice_expression}\n\n"
                                            f"Final result: {roller.final_result}")
            file_roll_info.seek(0)
            embed_msg.add_field(name="Final result", value=f"```{roller.final_result}```")
            await ctx.send(embed=embed_msg)
            await ctx.send(file=DiscordFile(file_roll_info, 'rollinfo.txt'))
        except ArithmeticDiceRollerError as error:
            embed_msg = DiscordEmbed(
                description=f"Expression roll requested by {ctx.message.author.mention}\n{error.message}",
                color=self.embeds_color)
            await ctx.send(embed=embed_msg)


def setup(bot):
    bot.add_cog(RNG(bot))


def teardown(bot):
    bot.remove_cog(RNG(bot))
