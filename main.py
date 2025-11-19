import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import requests
import ast

# this is a small discord bot for managing a minecraft server running on crafty controller

load_dotenv()

# discord bot init
discordToken = os.getenv("DISCORD_TOKEN")
description = ''' bot for managing mc server '''
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', description=description, intents=intents, help_command=None)


# crafty controller init
ccAccUname = os.getenv("CC_USERNAME")
ccAccPass = os.getenv("CC_PASSWORD")
ccToken = None  # to store token from crafty controller when started
baseURL = os.getenv("BASE_URL")
verifySSL = False


def getToken():
    global ccToken
    loginUrl = f"{baseURL}/auth/login"
    loginPayload = {
        "username": f"{ccAccUname}",
        "password": f"{ccAccPass}"
    }

    loginResp = requests.post(loginUrl, json=loginPayload, verify=verifySSL)
    loginResp.raise_for_status()

    ccToken = loginResp.json()["data"]["token"]
    print("Token:", ccToken)

# gets the status of a crafty controller server by name
# response data includes server name, running status, description, and player count
def getServers():
    global ccToken
    headers = {
        "Authorization": f"Bearer {ccToken}"
    }
    resp = requests.get(f"{baseURL}/servers/", headers=headers, verify=verifySSL)
    resp.raise_for_status()

    data = resp.json()["data"]  # list of servers
    return [(server["server_name"], server["server_id"])for server in data]


# get the status of a crafty controller server by name
# response data includes server name, running status, description, and player count
def getStatus(serverName):
    global ccToken
    url = f"{baseURL}/servers/"
    headers = {
        "Authorization": f"Bearer {ccToken}"
    }
    resp = requests.get(url, headers=headers, verify=verifySSL)
    resp.raise_for_status()

    data = resp.json()["data"]

    for server in data:
        worldName = server["server_name"]
        if serverName == worldName:
            serverID = server["server_id"]
            statsURL = f"{baseURL}/servers/{serverID}/stats"
            statsResp = requests.get(statsURL, headers=headers, verify=verifySSL)
            statsResp.raise_for_status()
            stats = statsResp.json()["data"]

            return [
                serverName,  # name
                stats["running"],  # running boolean
                stats["desc"],  # description
                stats["players"],  # players list/string
            ]

    return None


# get the metrics of a crafty controller server by name
# response data includes server name, cpu utilization, memory utilization, memory percentage
def getMetrics(serverName):
    global ccToken
    url = f"{baseURL}/servers/"
    headers = {
        "Authorization": f"Bearer {ccToken}"
    }
    resp = requests.get(url, headers=headers, verify=verifySSL)
    resp.raise_for_status()

    data = resp.json()["data"]

    for server in data:
        worldName = server["server_name"]
        if serverName == worldName:
            serverID = server["server_id"]
            statsURL = f"{baseURL}/servers/{serverID}/stats"
            statsResp = requests.get(statsURL, headers=headers, verify=verifySSL)
            statsResp.raise_for_status()
            stats = statsResp.json()["data"]

            return [
                serverName,
                stats["cpu"],
                stats["mem"],
                stats["mem_percent"],
            ]

    return None


# autocomplete server names based on getServers response
# returns list of server names (not IDs)
async def serverAutocomplete(interaction: discord.Interaction, current: str):
    serversResp = getServers()
    return [
       discord.app_commands.Choice(name=name, value=name)
       for name, _id in serversResp
       if current.lower() in name.lower()
   ][:25]


# whitelist a player on crafty controller server by player name and server ID
# returns true if able to send command to server
def whitelistPlayer(serverID, playerName):
    global ccToken
    url = f"{baseURL}/servers/{serverID}/stdin"
    headers = {
        "Authorization": f"Bearer {ccToken}"
    }

    resp = requests.post(url, headers=headers, data=f"/whitelist add {playerName}", verify=verifySSL)
    resp.raise_for_status()

    return resp.status_code == 200


@bot.tree.command(name="help", description="Show help menu for Minecraft server bot")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="mcServerManager",
        description="This is a custom bot to allow players to query, monitor, and lightly manager a privatly hosted server\nAll my commands are prefixed by `/`. Refer to the list below for full functionality!",
        color=0xd61c1c
    )

    # Commands list
    commands_list = [
        ("/help ", "returns this menu"),
        ("/servers", "gets the list of created minecraft servers"),
        ("/status <server name>", "gets the status of specified server"),
        ("/whitelist <player name> <server id>", "whitelists a player on a server"),
        ("/metrics <server name>", "gets the metrics of specified server"),
        ("/start <server name>", "(WIP)"),
        ("/restart <server name>", "(WIP)"),
        ("/voteKick <player name>", "(WIP)"),
    ]

    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="servers", description="List all Minecraft servers")
async def servers(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Servers:",
        description="",
        color=0xd61c1c
    )

    serversResp = getServers()
    for server in serversResp:
        embed.add_field(name=server[0], value=server[1], inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="status", description="Get status of a server")
@discord.app_commands.describe(server="Select the server")
@discord.app_commands.autocomplete(server=serverAutocomplete)
async def status(interaction: discord.Interaction, server: str):
    embed = discord.Embed(
        title=f"{server} status:",
        description="",
        color=0xd61c1c
    )

    stats = getStatus(server)
    if not stats:
        embed.add_field(name="Error", value="Server not found, try `/servers`.", inline=False)
        await interaction.response.send_message(embed=embed)
        return

    playerList = ast.literal_eval(stats[3])
    players = ' | '.join(playerList)

    embed.add_field(name="Server Name:", value=stats[0], inline=False)
    embed.add_field(name="Server Running:", value=('✅' if stats[1] else '❌'), inline=False)
    embed.add_field(name="Server Description:", value=stats[2], inline=False)
    embed.add_field(name="Current Players:", value=(players if players != "" else "None online"), inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="metrics", description="Get metrics of a server")
@discord.app_commands.describe(server="Select the server")
@discord.app_commands.autocomplete(server=serverAutocomplete)
async def metrics(interaction: discord.Interaction, server: str):
    embed = discord.Embed(
        title=f"{server} metrics:",
        description="",
        color=0xd61c1c
    )

    metric = getMetrics(server)
    if not metric:
        embed.add_field(name="Error", value="Server not found, try `/servers`.", inline=False)
        await interaction.response.send_message(embed=embed)
        return

    embed.add_field(name="Server Name:", value=metric[0], inline=False)
    embed.add_field(name="Server CPU percent:", value=(metric[1]), inline=False)
    embed.add_field(name="Server Memory:", value=metric[2], inline=False)
    embed.add_field(name="Current Mem Percent:", value=(metric[3]), inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="start", description="Start a Minecraft server")
@discord.app_commands.describe(server="Select the server")
@discord.app_commands.autocomplete(server=serverAutocomplete)
async def start(interaction: discord.Interaction, server: str):
    await interaction.response.send_message(f"Starting server: {server} (WIP)")


@bot.tree.command(name="whitelist", description="Whitelist a player on a server")
@discord.app_commands.describe(player="Player to whitelist", server="Select the server")
async def whitelist(interaction: discord.Interaction, player: str, server: str):
    embed = discord.Embed(
        title=f"Whitelist of {player}",
        description="",
        color=0xd61c1c
    )
    try:
        resp = whitelistPlayer(server, player)
    except Exception as e:
        print(e)
        embed.add_field(name="Error", value="Ensure to use a server ID like 'ee4caf2e-cd2d-4d1c-a792-886f2da8bc31'", inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        embed.add_field(name=f"Whitelisting player {player} on server {server}",
                        value="if you have any issues reach out to server a maintainer", inline=False)
        await interaction.response.send_message(embed=embed)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print("Failed to sync commands:", e)

    getToken()


bot.run(discordToken)