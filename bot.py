import discord
from discord import app_commands, Interaction
from discord.ext import commands
from PIL import Image
import os
import uuid
from flask import Flask
from threading import Thread
import asyncio
from moviepy.editor import VideoFileClip

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
intents.message_content = True 
intents.members = True          
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# =========================
# Funções de Processamento (Otimizadas para RAM Baixa)
# =========================
def converter_imagem_sync(input_path, output_path):
    with Image.open(input_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, format="GIF")

def extrair_audio_sync(video_path, audio_path):
    with VideoFileClip(video_path) as video:
        video.audio.write_audiofile(audio_path, logger=None)

def converter_video_gif_sync(video_path, gif_path):
    # Usamos o contexto 'with' para garantir que a memória seja liberada
    with VideoFileClip(video_path) as clip:
        # Reduzimos para 240px (essencial para o plano free do Render)
        # Pegamos apenas os primeiros 5 segundos
        duracao = min(clip.duration, 5)
        final = clip.resize(width=240).subclip(0, duracao)
        
        # 'colors=128' e 'fps=8' reduzem drasticamente o uso de CPU e RAM
        final.write_gif(gif_path, fps=8, logger=None, colors=128, opt="OptimizePlus")

# =========================
# Eventos
# =========================
@bot.event
async def on_ready():
    print(f"✅ Logado como {bot.user}")
    print("👉 Digite !deploy no seu servidor para ativar os comandos /")

@bot.event
async def on_member_join(member):
    try:
        embed = discord.Embed(
            title=f"Bem-vindo(a) à Celestial Trindade, {member.name}! ⚔️",
            description="É uma honra ter você conosco!",
            color=discord.Color.from_rgb(255, 215, 0)
        )
        embed.set_image(url="https://tr.rbxcdn.com/180DAY-8a0ac9f112f6761f919be4fe156a9cb5/420/420/Image/Webp/noFilter")
        await member.send(embed=embed)
    except discord.Forbidden:
        print(f"❌ Privado fechado de {member.name}")

# =========================
# Comandos de Admin
# =========================
@bot.command()
async def deploy(ctx):
    await ctx.send("Sincronizando comandos... aguarde.")
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Sucesso! {len(synced)} comandos sincronizados.")
    except Exception as e:
        await ctx.send(f"❌ Erro: {e}")

# =========================
# Slash Commands (/)
# =========================

@bot.tree.command(name="gifct", description="Converte PNG/JPG em GIF")
async def gifct(interaction: Interaction, file: discord.Attachment):
    await interaction.response.defer()
    img_path, gif_path = f"t_{uuid.uuid4()}.png", f"r_{uuid.uuid4()}.gif"
    try:
        await file.save(img_path)
        await asyncio.to_thread(converter_imagem_sync, img_path, gif_path)
        await interaction.followup.send(file=discord.File(gif_path))
    except Exception as e:
        print(f"❌ Erro GIFCT: {e}")
        await interaction.followup.send("❌ Erro ao converter imagem.")
    finally:
        for p in (img_path, gif_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="videoaudio", description="Extrai o áudio de um vídeo (MP3)")
async def videoaudio(interaction: Interaction, file: discord.Attachment):
    if file.size > 8000000: # Reduzi para 8MB para segurança
        return await interaction.response.send_message("❌ Vídeo muito grande para o servidor free! Máximo 8MB.")
    
    await interaction.response.defer()
    v_path, a_path = f"v_{uuid.uuid4()}.mp4", f"a_{uuid.uuid4()}.mp3"
    try:
        await file.save(v_path)
        await asyncio.to_thread(extrair_audio_sync, v_path, a_path)
        await interaction.followup.send(file=discord.File(a_path))
    except Exception as e:
        print(f"❌ Erro AUDIO: {e}")
        await interaction.followup.send("❌ Erro ao extrair áudio.")
    finally:
        for p in (v_path, a_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="videogif", description="Converte vídeo em GIF (Máx 5 segundos)")
async def videogif(interaction: Interaction, file: discord.Attachment):
    if file.size > 8000000:
        return await interaction.response.send_message("❌ Vídeo muito grande! Use arquivos menores que 8MB.")

    await interaction.response.defer()
    v_path, g_path = f"v_{uuid.uuid4()}.mp4", f"g_{uuid.uuid4()}.gif"
    try:
        await file.save(v_path)
        # Processamento em thread para não travar o bot
        await asyncio.to_thread(converter_video_gif_sync, v_path, g_path)
        await interaction.followup.send(file=discord.File(g_path))
    except Exception as e:
        # AGORA O ERRO APARECE NO LOG DO RENDER
        print(f"❌ ERRO TÉCNICO VIDEOGIF: {e}")
        await interaction.followup.send("❌ Erro ao gerar GIF. O vídeo pode ser pesado demais ou incompatível.")
    finally:
        for p in (v_path, g_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="ping", description="Verifica a latência")
async def ping(interaction: Interaction):
    await interaction.response.send_message(f"🏓 Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="logo", description="Envia o link do grupo e a logo da Celestial Trindade")
async def logo(interaction: discord.Interaction):
    link_grupo = "https://www.roblox.com/pt/communities/34214394/Celestial-Trindade#!/about"
    link_logo = "https://tr.rbxcdn.com/180DAY-8a0ac9f112f6761f919be4fe156a9cb5/420/420/Image/Webp/noFilter"
    embed = discord.Embed(title="🛡️ Identidade - Celestial Trindade", color=discord.Color.from_rgb(255, 215, 0))
    embed.add_field(name="🔗 Grupo no Roblox", value=f"[ENTRAR NO GRUPO]({link_grupo})", inline=False)
    embed.set_image(url=link_logo)
    await interaction.response.send_message(embed=embed)

# =========================
# Início
# =========================
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ ERRO: DISCORD_TOKEN não configurado!")
    else:
        bot.run(DISCORD_TOKEN)