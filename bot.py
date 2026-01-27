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

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

@bot.event
async def on_connect():
    print("[INFO] Conectado ao Discord")

@bot.event
async def on_disconnect():
    print("[WARNING] Desconectado do Discord")

# =========================
# Comando PNG/JPG → GIF
# =========================
@bot.command(aliases=["png2gif", "jpg2gif", "image2gif"])
@commands.cooldown(1, 15, commands.BucketType.user)  # evita rate limit
async def img2gif(ctx):
    img_path = None
    gif_path = None

    try:
        if not ctx.message.attachments:
            await ctx.send("❌ Envie um arquivo PNG ou JPG junto com o comando `!img2gif`")
            return

        attachment = ctx.message.attachments[0]
        filename_lower = attachment.filename.lower()

        if not filename_lower.endswith((".png", ".jpg", ".jpeg")):
            await ctx.send("❌ O arquivo precisa ser PNG ou JPG")
            return

        os.makedirs("temp", exist_ok=True)

        file_id = str(uuid.uuid4())
        ext = ".png" if filename_lower.endswith(".png") else ".jpg"
        img_path = os.path.join("temp", f"{file_id}{ext}")
        gif_path = os.path.join("temp", f"{file_id}.gif")

        await attachment.save(img_path)
        print(f"[INFO] Imagem salva em {img_path}")

        img = Image.open(img_path)
        img.save(gif_path, format="GIF")

        await ctx.send(
            "✅ GIF criado com sucesso:",
            file=discord.File(gif_path)
        )

    except commands.CommandOnCooldown as e:
        await ctx.send(f"⏳ Aguarde `{int(e.retry_after)}` segundos antes de usar novamente.")

    except Exception as e:
        await ctx.send("❌ Ocorreu um erro ao processar a imagem.")
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
