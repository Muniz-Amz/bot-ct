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
    print(f"[INFO] Token lido corretamente: {DISCORD_TOKEN[:5]}***")

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
print("[INFO] Keep-alive iniciado.")

# =========================
# Bot Discord
# =========================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

# Evento de debug para ver se o bot está recebendo mensagens
@bot.event
async def on_message(message):
    print(f"[DEBUG] Mensagem recebida: {message.content} de {message.author}")
    await bot.process_commands(message)

# =========================
# Comando PNG/JPG → GIF
# =========================
@bot.command()
async def img2gif(ctx):
    if not ctx.message.attachments:
        await ctx.send("❌ Envie um arquivo PNG ou JPG/JPEG junto com o comando `!img2gif`")
        return

    attachment = ctx.message.attachments[0]
    filename_lower = attachment.filename.lower()
    if not (filename_lower.endswith(".png") or filename_lower.endswith(".jpg") or filename_lower.endswith(".jpeg")):
        await ctx.send("❌ O arquivo precisa ser PNG ou JPG/JPEG")
        return

    os.makedirs("temp", exist_ok=True)

    file_id = str(uuid.uuid4())
    input_path = os.path.join("temp", f"{file_id}_{attachment.filename}")
    gif_path = os.path.join("temp", f"{file_id}.gif")

    try:
        await attachment.save(input_path)
        print(f"[INFO] Arquivo recebido: {attachment.filename} → {input_path}")

        img = Image.open(input_path)
        img.save(gif_path, format="GIF")
        print(f"[INFO] GIF criado: {gif_path}")

        await ctx.send("✅ GIF criado com sucesso:", file=discord.File(gif_path))
    finally:
        # Limpeza de arquivos temporários
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(gif_path):
            os.remove(gif_path)
        print(f"[INFO] Arquivos temporários removidos: {input_path}, {gif_path}")

# =========================
# Rodar bot
# =========================
try:
    bot.run(DISCORD_TOKEN)
except discord.LoginFailure:
    print("[ERROR] Falha no login! Verifique seu DISCORD_TOKEN.")
except Exception as e:
    print(f"[ERROR] Ocorreu um erro: {e}")
