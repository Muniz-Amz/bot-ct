import discord
from discord.ext import commands
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
    port = int(os.environ.get("PORT", 8080))  # Porta do Render
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
@bot.command(aliases=["png2gif", "jpg2gif", "image2gif"])
async def img2gif(ctx):
    try:
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

    except Exception as e:
        await ctx.send("❌ Ocorreu um erro ao processar a imagem.")
        print(f"[ERROR] Erro em img2gif: {e}")
        traceback.print_exc()

    finally:
        for path in [img_path, gif_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"[INFO] Arquivo temporário removido: {path}")
            except Exception as ex:
                print(f"[WARNING] Não foi possível remover {path}: {ex}")

# =========================
# Rodar bot
# =========================
try:
    bot.run(DISCORD_TOKEN)
except discord.LoginFailure:
    print("[ERROR] Falha no login! Verifique seu DISCORD_TOKEN.")
except Exception as e:
    print(f"[ERROR] Ocorreu um erro crítico: {e}")
    traceback.print_exc()
