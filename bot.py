import discord
from discord.ext import commands
from PIL import Image
import os
import uuid
from flask import Flask
from threading import Thread
import sys

# =========================
# Token do Discord (ENV)
# =========================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    print("[ERROR] DISCORD_TOKEN não encontrado nas variáveis de ambiente!")
    sys.exit(1)
else:
    print(f"[INFO] Token detectado: {DISCORD_TOKEN[:5]}***")

# =========================
# Keep Alive (Render)
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot online!"

def run_flask():
    print("[INFO] Keep-alive rodando na porta 8080")
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

@bot.event
async def on_connect():
    print("[INFO] Conexão estabelecida com Discord...")

@bot.event
async def on_disconnect():
    print("[WARNING] Bot desconectado do Discord!")

# =========================
# Comando PNG/JPG → GIF
# =========================
@bot.command()
async def img2gif(ctx):
    if not ctx.message.attachments:
        await ctx.send("❌ Envie um arquivo PNG ou JPG junto com o comando `!img2gif`")
        print("[WARNING] Nenhum arquivo enviado")
        return

    attachment = ctx.message.attachments[0]
    filename_lower = attachment.filename.lower()

    if not (filename_lower.endswith(".png") or filename_lower.endswith(".jpg") or filename_lower.endswith(".jpeg")):
        await ctx.send("❌ O arquivo precisa ser PNG ou JPG")
        print(f"[WARNING] Arquivo inválido: {attachment.filename}")
        return

    os.makedirs("temp", exist_ok=True)

    file_id = str(uuid.uuid4())
    ext = ".png" if filename_lower.endswith(".png") else ".jpg"
    img_path = os.path.join("temp", f"{file_id}{ext}")
    gif_path = os.path.join("temp", f"{file_id}.gif")

    await attachment.save(img_path)
    print(f"[INFO] Imagem recebida: {attachment.filename} → {img_path}")

    img = Image.open(img_path)
    img.save(gif_path, format="GIF")
    print(f"[INFO] GIF criado: {gif_path}")

    await ctx.send(
        "✅ GIF criado com sucesso:",
        file=discord.File(gif_path)
    )

    os.remove(img_path)
    os.remove(gif_path)
    print(f"[INFO] Arquivos temporários removidos: {img_path}, {gif_path}")

# =========================
# Rodar bot
# =========================
try:
    bot.run(DISCORD_TOKEN)
except discord.LoginFailure:
    print("[ERROR] Falha no login! Verifique seu DISCORD_TOKEN.")
except Exception as e:
    print(f"[ERROR] Ocorreu um erro: {e}")
