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
import asyncio

# =========================
# Configurações e Token
# =========================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# =========================
# Keep Alive Render (Flask)
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot vivo!"

def run_flask():
    # Render usa a porta 10000 por padrão em muitos casos
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

keep_alive()

# =========================
# Configuração do Bot
# =========================
intents = discord.Intents.default()
intents.message_content = True # Necessário para o comando !deploy
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# =========================
# Eventos
# =========================
@bot.event
async def on_ready():
    print(f"✅ Logado como {bot.user}")
    print("⚠️ Slash commands não sincronizados automaticamente para evitar Erro 429.")
    print("👉 Digite !deploy no seu servidor para ativar os comandos /")

# =========================
# Comando de Sincronização Manual (Evita Rate Limit)
# =========================
@bot.command()
@commands.is_owner() # Só você (dono do bot) pode usar isso
async def deploy(ctx):
    await ctx.send("Sincronizando comandos... aguarde.")
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Sucesso! {len(synced)} comandos sincronizados.")
    except Exception as e:
        await ctx.send(f"❌ Erro: {e}")

# =========================
# Processamento de Imagem (Seguro)
# =========================
def converter_imagem_sync(input_path, output_path):
    with Image.open(input_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, format="GIF")

# =========================
# Slash Command: /gifct
# =========================
@bot.tree.command(name="gifct", description="Converte PNG/JPG em GIF")
async def gifct(interaction: Interaction, file: discord.Attachment):
    # Cooldown de 10 segundos
    now = time.time()
    if not hasattr(bot, 'last_uses'): bot.last_uses = {}
    last = bot.last_uses.get(interaction.user.id, 0)
    
    if now - last < 10:
        await interaction.response.send_message(f"⏳ Aguarde {int(10-(now-last))}s", ephemeral=True)
        return
    
    bot.last_uses[interaction.user.id] = now

    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        await interaction.response.send_message("❌ Envie PNG ou JPG", ephemeral=True)
        return

    await interaction.response.defer()

    img_path = f"temp_{uuid.uuid4()}.png"
    gif_path = f"res_{uuid.uuid4()}.gif"

    try:
        await file.save(img_path)
        await asyncio.to_thread(converter_imagem_sync, img_path, gif_path)
        
        await interaction.followup.send(file=discord.File(gif_path))

    except Exception as e:
        print(f"Erro: {e}")
        await interaction.followup.send("❌ Erro ao converter.")
    
    finally:
        await asyncio.sleep(2) # Espera o envio terminar
        for p in (img_path, gif_path):
            if os.path.exists(p): os.remove(p)

# =========================
# Início
# =========================
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ ERRO: DISCORD_TOKEN não configurado no Render!")
    else:
        try:
            bot.run(DISCORD_TOKEN)
        except discord.errors.HTTPException as e:
            if e.status == 429:
                print("❌ BLOQUEIO TEMPORÁRIO (429). Desligue o bot por 20 min.")
            else:
                print(f"❌ Erro HTTP: {e}")