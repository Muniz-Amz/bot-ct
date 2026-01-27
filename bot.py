import discord
from discord import app_commands, Interaction
from discord.ext import commands
from PIL import Image
import os
import uuid
from flask import Flask
from threading import Thread
import sys
import traceback
import time

# =========================
# Token do Discord
# =========================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    print("[ERROR] DISCORD_TOKEN não encontrado!")
    sys.exit(1)
else:
    print(f"[INFO] Token detectado: {DISCORD_TOKEN[:5]}***")

# =========================
# Keep Alive Render
# =========================
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    print(f"[INFO] Keep-alive rodando na porta {port}")
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

keep_alive()

# =========================
# Bot Discord
# =========================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# =========================
# Eventos
# =========================
@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")
    await bot.tree.sync()  # Registra slash commands
    print("[INFO] Slash commands sincronizados!")

@bot.event
async def on_connect():
    print("[INFO] Conectado ao Discord")

@bot.event
async def on_disconnect():
    print("[WARNING] Desconectado do Discord")

# =========================
# Cooldown simples
# =========================
user_cooldowns = {}

def check_cooldown(user_id):
    now = time.time()
    last = user_cooldowns.get(user_id, 0)
    if now - last < 15:
        return int(15 - (now - last))
    user_cooldowns[user_id] = now
    return 0

# =========================
# Slash command /gifct
# =========================
@bot.tree.command(name="gifct", description="Converte PNG/JPG em GIF")
async def gifct(interaction: Interaction, file: discord.Attachment):
    cd = check_cooldown(interaction.user.id)
    if cd > 0:
        await interaction.response.send_message(f"⏳ Aguarde {cd}s antes de usar novamente.", ephemeral=True)
        return

    img_path = None
    gif_path = None

    try:
        filename_lower = file.filename.lower()
        if not filename_lower.endswith((".png", ".jpg", ".jpeg")):
            await interaction.response.send_message("❌ O arquivo precisa ser PNG ou JPG", ephemeral=True)
            return

        os.makedirs("temp", exist_ok=True)
        file_id = str(uuid.uuid4())
        ext = ".png" if filename_lower.endswith(".png") else ".jpg"
        img_path = os.path.join("temp", f"{file_id}{ext}")
        gif_path = os.path.join("temp", f"{file_id}.gif")

        await file.save(img_path)
        print(f"[INFO] Imagem salva: {img_path}")

        img = Image.open(img_path)
        img.save(gif_path, format="GIF")
        print(f"[INFO] GIF criado: {gif_path}")

        await interaction.response.send_message(
            "✅ GIF criado com sucesso:",
            file=discord.File(gif_path)
        )

    except Exception as e:
        await interaction.response.send_message("❌ Erro ao processar a imagem.", ephemeral=True)
        print(f"[ERROR] {e}")
        traceback.print_exc()

    finally:
        for path in (img_path, gif_path):
            try:
                if path and os.path.exists(path):
                    os.remove(path)
                    print(f"[INFO] Arquivo removido: {path}")
            except Exception as ex:
                print(f"[WARNING] Falha ao remover {path}: {ex}")

# =========================
# Rodar bot
# =========================
try:
    bot.run(DISCORD_TOKEN)
except discord.LoginFailure:
    print("[ERROR] Token inválido!")
except Exception as e:
    print(f"[ERROR] Erro crítico: {e}")
    traceback.print_exc()
