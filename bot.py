import discord
from discord.ext import tasks

import requests
import json
import random
from discord import FFmpegPCMAudio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

client = discord.Client(intents=intents)

# channels for the cat facts
channels = []
# channels for sending typing messages
typingChannels = []
# add words separated by a comma for each of these
high_naughty = []
medium_naughty = []
low_naughty = []
# TODO - read/write to a file
naughty_points = {}

# returns a cat fact from API
def get_fact():
  response = requests.get('https://catfact.ninja/fact?max_length=140')
  json_data = json.loads(response.text)
  return("```" + "Fact: " + json_data["fact"] + "```")

# user = Discord user id, 
# points = int value of either {1,3,5}
# TODO - make naughty points channel to list every time someone gains one
def add_naughty(user, points):
    global naughty_points
    # if the user is already in list, add to existing key. Else create new key
    if user in naughty_points:
        total_points = naughty_points[user]
        total_points += points
        naughty_points[user] = total_points
    else:
        naughty_points[user] = points

# user is the username, must convert to ID
# needs the channel to send it to
async def get_naughty(user, channel):
    global naughty_points
    print(user)
    print (channel.guild.members)
    member = discord.utils.get(channel.guild.members, name=user)
    if member == None:
        await channel.send("User " + user + " is not in the guild")
    elif member.id in naughty_points:
        total_points = naughty_points[member.id]
        await channel.send("User " + user + " has " + str(total_points) + " naughty points")
    else:
        await channel.send("User " + user + " does not have any naughty points yet")

@client.event
async def on_ready():
    # starts the automated cat facts for all servers
    print(f'We have logged in as {client.user}')
    for channel in client.get_all_channels():
        global channels
        if channel.name == "catfacts":
            channels.append(channel)    
            print('Cat Fact timer has been added to channel list for server ' + str(channel.guild))
        if channel.name == "typing-channel":
            typingChannels.append(channel)
            print('Typing channel has been added to channel list for server ' + str(channel.guild))
    # starts timer for list of channels
    automated_cat_fact.start()



@client.event
async def on_message(message):
    if message.author == client.user:
        return
        # REDACTED - if bot sends an on_typing message, delete it after some time
        # if message.content.startswith('I see you are typing '):
        #     await message.delete(delay = 3)

    if message.content.startswith('!catfact'):
        fact = get_fact()
        await message.channel.send(fact)
    
    if message.content.startswith('!np') or message.content.startswith('!naughtypoints'):
        msg = message.content.split()
        if len(msg) == 1:
            msg.append(message.author.name)
        await get_naughty(msg[1], message.channel)

    # add high naughty points
    for word in high_naughty:
        if word in message.content:
            add_naughty(message.author.id, 5)

    # add medium naughty points
    for word in medium_naughty:
        if word in message.content:
            add_naughty(message.author.id, 3)

    # add low naughty points
    for word in low_naughty:
        if word in message.content:
            add_naughty(message.author.id, 1)

# TODO - make it so that it sends to specific channel
@client.event
async def on_typing(channel, user, when):
    typing_message = "I see you are typing " + str(user) + " in channel " + str(channel)
    await typingChannels[0].send(typing_message)

@client.event
async def on_guild_join(guild):
    print('joined guild ' + str(guild.id))
    global isCatfactsChannel
    isCatfactsChannel = False
    global isTypingChannel
    isTypingChannel = False
    # checking to see if there is a catfacts channel
    for channel in guild.channels:
        if channel.name == "catfacts":
            isCatfactsChannel = True
        if channel.name == "typing-status":
            isTypingChannel = True
    # if there is no catfacts channel, create one
    if isCatfactsChannel == False:
        channel = await guild.create_text_channel('catfacts') #then, in the channel_create method it will start the timer
    if isTypingChannel == False:
        channel = await guild.create_text_channel('typing-channel')
    # create the role for random mute, mute of shame
    # await guild.create_role(name="Mute of Shame", colour=discord.Colour(0x800000))


# FIXME - this only handles for one server, with one voice channel at a time
@client.event
async def on_voice_state_update(member, before, after):
    # if someone is joining
    if before.channel == None and member != client.user:
        # if this is first joiner, start timer
        if len(after.channel.members) <= 1 and random_voice_channel.is_running() == False:
            random_voice_channel.start(after.channel)
    # if someone is leaving
    if after.channel == None:
        if len(before.channel.members) == 0 and random_voice_channel.is_running() == True:
            random_voice_channel.stop()


        
# when people create a channel called catfacts, it will add it to the list
@client.event
async def on_guild_channel_create(channel):
    if channel.name == "catfacts":
        global channels
        channels.append(channel)

# if people delete catfacts channel
@client.event
async def on_guild_channel_delete(channel):
    global channels
    if channel in channels:
        channels.remove(channel)

# TODO - add mute!
# @tasks.loop(hours=12.0)
# async def mute_random_user(guild):
#     num_members = guild.member_count
#     random_value = random.randint(0,num_members - 1)
#     member = guild.members[random_value]
#     role = discord.utils.get(guild.roles, name="Mute of Shame")
#     await member.add_roles(role)
    # TODO - mute the user, and then unmute the previous user


@tasks.loop(minutes=2.0)
async def random_voice_channel(channel):
    voice = discord.utils.get(client.voice_clients, guild=channel.guild)
    if (random.randint(1,10) == 5 and voice == None):
        # play rick roll lol
        voiceChannel = await channel.connect()
        source = FFmpegPCMAudio('rickroll.mp3')
        player = voiceChannel.play(source)
        # set a task to disconnect
        global loop
        loop = 0
        end_rick_roll.start(channel)

        # disconnect
        print ("LOL scream here")

@tasks.loop(seconds=5.0)
async def end_rick_roll(voiceChannel):
    global loop
    print (loop)
    if client.user in voiceChannel.members and loop == 1:
        await voiceChannel.guild.voice_client.disconnect()
        end_rick_roll.stop()
    loop += 1

# TODO - make it so that it finds the cat facts channel and if it isnt there then it doesnt send anything
@tasks.loop(minutes=5.0)
async def automated_cat_fact():
    # TODO, if you want it to get different fact for every server, have it fetch inside for loop
    # leaving it this way for now to minimize calls to API
    global channels
    fact = get_fact()
    print (len(channels))
    for channel in channels:
        await channel.send(fact)

client.run('BOT ID IS HERE, YOU WILL NOT FIND IT!')
