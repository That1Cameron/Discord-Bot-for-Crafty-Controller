import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import requests
import ast
import urllib3
from mc import *
# this is a small discord bot for managing a minecraft server running on crafty controller
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# discord bot init
discordToken = os.getenv("DISCORD_TOKEN")
description = ''' bot for managing mc server '''
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', description=description, intents=intents, help_command=None)
mcInterface = None
verifySSL = False


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    global mcInterface
    mcInterface = MC()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print("Failed to sync commands:", e)

    try:
        mcInterface.prepCraftyToken()
        print(f"Obtained Crafty Controller Token")
    except Exception as e:
        print("Failed to fetch crafty token:", e)


# Bots help command
@bot.tree.command(name="help", description="Show help menu for Minecraft server bot")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ServerManager",
        description="This is a custom bot to allow players to query, monitor, and lightly manager a privatly hosted server\nAll my commands are prefixed by `/`. Refer to the list below for full functionality!",
        color=0xd61c1c
    )

    # Commands list
    commands_list = [
        ("/help ", "returns this menu"),
        (":pick: Minecraft commands:", "━━━━━━━━━━━━━━━━━━━━"),
        ("    /mc-servers", "gets the list of created minecraft servers"),
        ("    /mc-status <server name>", "gets the status of specified server"),
        ("    /mc-whitelist <player name> <server id>", "whitelists a player on a server"),
        ("    /mc-metrics <server name>", "gets the metrics of specified server"),
        ("    /mc-start <server name>", "(WIP)"),
        ("    /mc-restart <server name>", "(WIP)"),
        ("    /mc-voteKick <player name>", "(WIP)"),
        ("\u200b", "\u200b"),
        (":t_rex: Ark Commands:", "━━━━━━━━━━━━━━━━━━━━"),
        ("    /ark-status <server name>", "gets the status of specified Ark server")
    ]

    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)

    await interaction.response.send_message(embed=embed)


# bot command /servers lists minecraft servers
@bot.tree.command(name="mc-servers", description="List all Minecraft servers")
async def mcServers(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Servers:",
        description="",
        color=0xd61c1c
    )

    serversResp = mcInterface.getServers()
    for server in serversResp:
        embed.add_field(name=server[0], value=server[1], inline=False)
    await interaction.response.send_message(embed=embed)


# autocomplete server names based on getServers response
# returns list of server names (not IDs)
async def msServerAutocomplete(interaction: discord.Interaction, current: str):
    serversResp = mcInterface.getServers()
    return [
       discord.app_commands.Choice(name=name, value=name)
       for name, _id in serversResp
       if current.lower() in name.lower()
   ][:25]


@bot.tree.command(name="mc-whitelist", description="Whitelist a player on a server")
@discord.app_commands.describe(player="Player to whitelist", server="Select the server")
@discord.app_commands.autocomplete(server=msServerAutocomplete)
async def mcWhitelist(interaction: discord.Interaction, player: str, server: str):
    embed = discord.Embed(
        title=f"Whitelist of {player}",
        description="",
        color=0xd61c1c
    )
    try:
        serverID = mcInterface.getServerID(server)
        mcInterface.whitelistPlayer(serverID, player)
    except Exception as e:
        print(e)
        embed.add_field(name="Error", value="Ensure to use a server ID like 'ee4caf2e-cd2d-4d1c-a792-886f2da8bc31'", inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        embed.add_field(name=f"Whitelisting player {player} on server {server}",
                        value="if you have any issues reach out to server a maintainer", inline=False)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="mc-status", description="Get status of a server")
@discord.app_commands.describe(server="Select the server")
@discord.app_commands.autocomplete(server=msServerAutocomplete)
async def status(interaction: discord.Interaction, server: str):
    embed = discord.Embed(
        title=f"{server} status:",
        description="",
        color=0xd61c1c
    )

    stats = mcInterface.getStatus(server)
    print(stats)
    if not stats:
        embed.add_field(name="Error", value="Server not found, try `/servers`.", inline=False)
        await interaction.response.send_message(embed=embed)
        return

    if stats[3] != "False":
        playerList = ast.literal_eval(stats[3])
        players = ' | '.join(playerList)
    else:
        players = "None"

    embed.add_field(name="Server Name:", value=stats[0], inline=False)
    embed.add_field(name="Server Running:", value=('✅' if stats[1] else '❌'), inline=False)
    embed.add_field(name="Server Description:", value=stats[2], inline=False)
    embed.add_field(name="Current Players:", value=(players if players != "" else "None online"), inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="mc-metrics", description="Get metrics of a server")
@discord.app_commands.describe(server="Select the server")
@discord.app_commands.autocomplete(server=msServerAutocomplete)
async def metrics(interaction: discord.Interaction, server: str):
    embed = discord.Embed(
        title=f"{server} metrics:",
        description="",
        color=0xd61c1c
    )

    metric = mcInterface.getMetrics(server)
    if not metric:
        embed.add_field(name="Error", value="Server not found, try `/servers`.", inline=False)
        await interaction.response.send_message(embed=embed)
        return

    embed.add_field(name="Server Name:", value=metric[0], inline=False)
    embed.add_field(name="Server CPU percent:", value=(metric[1]), inline=False)
    embed.add_field(name="Server Memory:", value=metric[2], inline=False)
    embed.add_field(name="Current Mem Percent:", value=(metric[3]), inline=False)
    await interaction.response.send_message(embed=embed)


bot.run(discordToken)