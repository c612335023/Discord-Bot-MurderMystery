import discord
from discord.ext import commands
import time
import random
import asyncio

token = "YOUR_TOKEN_HERE"

bot = commands.Bot(
    command_prefix='!',
    case_insensitive=True,
    help_command=None,
    activity=discord.Game("Murder Mystery"),
    intents=discord.Intents.all()
)

@bot.event
async def on_ready():
    print('ログインしました')

@bot.command()
async def help(ctx):
    await ctx.send(f"<@{ctx.author.id}>")
    await ctx.send("!ping : botの応答速度を測定")
    await ctx.send("!dice [number] [face] : [number]d[face]を行う（[face]面ダイスを[number]個振ります）")
    await ctx.send("!setup [scenario] [players] [channels] :\n[scenario] : カテゴリ名\n[players] : プレイ人数\n[channels] : 密談VC数")

@bot.command()
async def ping(ctx):
    await ctx.send(f'<@{ctx.author.id}> {round(bot.latency*1000)}ms')

@bot.command()
async def dice(ctx, number=1, face=100):
    n = [0]*number
    s = ""
    for i in range(number):
        n[i] = random.randint(1, face)
        s += str(n[i])
        s += "," if i != number-1 else ""
    await ctx.send(f'<@{ctx.author.id}> {number}d{face} → [{s}] → {sum(n)}')

@bot.command()
async def setup(ctx, scenario="マーダーミステリー", players=4, channels=1):
    message = await ctx.send('作成中...')
    # ロール作成
    await ctx.guild.create_role(name = f"{scenario}_GM")
    await ctx.guild.create_role(name = f"{scenario}_PL")
    await ctx.guild.create_role(name = f"{scenario}_観戦")
    for i in range(1,players+1):
        await ctx.guild.create_role(name = f"{scenario}_PL{i}")

    # カテゴリ作成
    category = await ctx.guild.create_category(name = scenario)
    # テキストチャンネル作成
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
        discord.utils.get(ctx.guild.roles, name = f"{scenario}_GM"): discord.PermissionOverwrite(read_messages=True, send_messages=True),
        discord.utils.get(ctx.guild.roles, name = f"{scenario}_PL"): discord.PermissionOverwrite(read_messages=True, send_messages=False),
        discord.utils.get(ctx.guild.roles, name = f"{scenario}_観戦"): discord.PermissionOverwrite(read_messages=True, send_messages=False)
    }
    await category.create_text_channel(name = "共通情報", overwrites=overwrites)
    await category.create_text_channel(name = "共通ルール", overwrites=overwrites)
    await category.create_text_channel(name = "タイマー", overwrites=overwrites)

    for i in range(1,players+1):
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
            discord.utils.get(ctx.guild.roles, name = f"{scenario}_GM"): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            discord.utils.get(ctx.guild.roles, name = f"{scenario}_PL"): discord.PermissionOverwrite(read_messages=False, send_messages=False),
            discord.utils.get(ctx.guild.roles, name = f"{scenario}_PL{i}"): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            discord.utils.get(ctx.guild.roles, name = f"{scenario}_観戦"): discord.PermissionOverwrite(read_messages=True, send_messages=False)
        }
        await category.create_text_channel(name = f"PL{i}", overwrites=overwrites)
    
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
        discord.utils.get(ctx.guild.roles, name = f"{scenario}_GM"): discord.PermissionOverwrite(read_messages=True, send_messages=True),
        discord.utils.get(ctx.guild.roles, name = f"{scenario}_PL"): discord.PermissionOverwrite(read_messages=False, send_messages=False),
        discord.utils.get(ctx.guild.roles, name = f"{scenario}_観戦"): discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    await category.create_text_channel(name = "実況（暇があれば）", overwrites=overwrites)
    
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
        discord.utils.get(ctx.guild.roles, name = f"{scenario}_GM"): discord.PermissionOverwrite(read_messages=True, send_messages=True),
        discord.utils.get(ctx.guild.roles, name = f"{scenario}_PL"): discord.PermissionOverwrite(read_messages=False, send_messages=False),
        discord.utils.get(ctx.guild.roles, name = f"{scenario}_観戦"): discord.PermissionOverwrite(read_messages=True, send_messages=False)
    }
    await category.create_text_channel(name = "解説", overwrites=overwrites)

    # ボイスチャンネル作成
    await category.create_voice_channel(name = "全体会議")
    for i in range(1,channels+1):
        await category.create_voice_channel(name = f"密談{i}")
    
    await message.edit(content=f"<@{ctx.author.id}> ")

@bot.command()
async def timer(ctx, minutes=5, seconds=0):
    # フラグ作成
    flags = {
        10: True,
        5: True,
        3: True,
        1: True,
        30: True
    }
    if seconds == 0:
        if minutes in flags:
            flags[minutes] = False
    elif seconds == 30:
        flags[30] = False

    # bot VC参加
    if ctx.author.voice is None:
        await ctx.send("あなたはボイスチャンネルに参加していません")
        return
    if ctx.guild.voice_client is None:
        await ctx.author.voice.channel.connect()
    
    # 時間設定
    message = await ctx.send(f'```{minutes}分{seconds}秒```')
    time_start = time.perf_counter()
    while minutes*60+seconds > 0:
        if time.perf_counter() - time_start > 10:
            time_start = time.perf_counter()
            seconds -= 10
            if seconds < 0:
                minutes -= 1
                seconds += 60
            await message.edit(content=f'```{minutes}分{seconds}秒```')
        if minutes == 10 and seconds == 0 and flags[10]:
            ctx.guild.voice_client.play(
                discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio("voice\\001_ずんだもん（ノーマル）_残り10分です。.wav"),
                    volume=0.5
                )
            )
            await asyncio.sleep(2)
            flags[10] = False
        if minutes == 5 and seconds == 0 and flags[5]:
            ctx.guild.voice_client.play(
                discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio("voice\\002_ずんだもん（ノーマル）_残り5分です。.wav"),
                    volume=0.5
                )
            )
            await asyncio.sleep(2)
            flags[5] = False
        if minutes == 3 and seconds == 0 and flags[3]:
            ctx.guild.voice_client.play(
                discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio("voice\\003_ずんだもん（ノーマル）_残り3分です。.wav"),
                    volume=0.5
                )
            )
            await asyncio.sleep(2)
            flags[3] = False
        if minutes == 1 and seconds == 0 and flags[1]:
            ctx.guild.voice_client.play(
                discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio("voice\\004_ずんだもん（ノーマル）_残り1分です。.wav"),
                    volume=0.5
                )
            )
            await asyncio.sleep(2)
            flags[1] = False
        if minutes == 0 and seconds == 30 and flags[30]:
            ctx.guild.voice_client.play(
                discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio("voice\\005_ずんだもん（ノーマル）_残り30秒です。.wav"),
                    volume=1
                )
            )
            await asyncio.sleep(2)
            flags[30] = False
        if minutes == 0 and seconds == 0:
            members = [i.id for i in ctx.author.voice.channel.members]
            await message.edit(content="```タイマーが終了しました```")
            s = ""
            for member in members:
                s += f"<@{member}> "
            await ctx.send(s)
            await ctx.guild.voice_client.disconnect()

bot.run(token)