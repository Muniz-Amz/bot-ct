import discord
from discord.ext import commands
from PIL import Image
import os
from flask import Flask
from threading import Thread

# =========================
# Token do Discord (ENV)
# =========================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    print("[ERROR] DISCORD_TOKEN não encontrado nas variáveis de ambiente.")
    exit(1)

# =========================
# Keep Alive (Render)
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot online!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

keep_alive()

# =========================
# Bot Discord
# =========================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

# =========================
# Comando PNG → GIF
# =========================
@bot.command()
async def png2gif(ctx):
    if not ctx.message.attachments:
        await ctx.send("❌ Envie um arquivo PNG junto com o comando `!png2gif`")
        return

    attachment = ctx.message.attachments[0]

    if not attachment.filename.lower().endswith(".png"):
        await ctx.send("❌ O arquivo precisa ser PNG")
        return

    os.makedirs("temp", exist_ok=True)

    png_path = os.path.join("temp", attachment.filename)
    gif_path = png_path.replace(".png", ".gif")

    await attachment.save(png_path)

    img = Image.open(png_path)
    img.save(gif_path, format="GIF")

    await ctx.send(
        "✅ GIF criado com sucesso:",
        file=discord.File(gif_path)
    )

    os.remove(png_path)
    os.remove(gif_path)

# =========================
# Iniciar bot
# =========================
bot.run(DISCORD_TOKEN)
