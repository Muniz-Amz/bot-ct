import discord
from discord import app_commands
from PIL import Image
import os
import uuid
from flask import Flask
from threading import Thread
import sys
import traceback

# =========================
# Token do Discord (ENV)
# =========================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    print("[ERROR] DISCORD_TOKEN não encontrado nas variáveis de ambiente!")
    sys.exit(1)

# =========================
# Keep Alive (Render)
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    print(f"[INFO] Keep-alive rodando na porta {port}")
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask).start()

# =========================
# Bot Discord (Slash)
# =========================
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f"✅ Bot online como {client.user}")
    try:
        synced = await tree.sync()
        print(f"🔄 Slash commands sincronizados: {len(synced)}")
    except Exception as e:
        print(f"[ERROR] Falha ao sincronizar comandos: {e}")

# =========================
# Slash Command /gif
# =========================
@tree.command(
    name="gif",
    description="Converter PNG ou JPG em GIF"
)
@app_commands.describe(imagem="Envie uma imagem PNG ou JPG")
async def gif(interaction: discord.Interaction, imagem: discord.Attachment):

    img_path = None
    gif_path = None

    await interaction.response.defer(thinking=True)

    try:
        if not imagem.filename.lower().endswith((".png", ".jpg", ".jpeg")):
            await interaction.followup.send("❌ O arquivo precisa ser PNG ou JPG")
            return

        os.makedirs("temp", exist_ok=True)

        file_id = str(uuid.uuid4())
        ext = ".png" if imagem.filename.lower().endswith(".png") else ".jpg"
        img_path = os.path.join("temp", f"{file_id}{ext}")
        gif_path = os.path.join("temp", f"{file_id}.gif")

        await imagem.save(img_path)
        print(f"[INFO] Imagem salva em {img_path}")

        img = Image.open(img_path)
        img.save(gif_path, format="GIF")

        await interaction.followup.send(
            content="✅ GIF criado com sucesso:",
            file=discord.File(gif_path)
        )

    except Exception as e:
        print(f"[ERROR] {e}")
        traceback.print_exc()
        await interaction.followup.send("❌ Ocorreu um erro ao processar a imagem.")

    finally:
        for path in (img_path, gif_path):
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except:
                pass

# =========================
# Rodar bot
# =========================
client.run(DISCORD_TOKEN)
