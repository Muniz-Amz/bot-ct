import discord
from discord import app_commands, Interaction
from discord.ext import commands
from PIL import Image
import os
import uuid
from flask import Flask
from threading import Thread
import asyncio
import logging
from moviepy.editor import VideoFileClip

# =========================
# Configurações de Log
# =========================
logging.basicConfig(level=logging.INFO)

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
    return "🛡️ Celestial Bot Online e Operacional!"

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
# Funções de Processamento (Otimizadas para 512MB RAM)
# =========================

def converter_imagem_sync(input_path, output_path):
    with Image.open(input_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, format="GIF")

def extrair_audio_sync(video_path, audio_path):
    # Usamos target_resolution baixo apenas para ler o áudio sem gastar RAM
    with VideoFileClip(video_path, target_resolution=(120, None)) as video:
        video.audio.write_audiofile(audio_path, logger=None, bitrate="64k")

def converter_video_gif_sync(video_path, gif_path):
    # audio=False é vital. target_resolution=(200, None) evita crash no Render
    with VideoFileClip(video_path, audio=False, target_resolution=(200, None), fps_source="fps") as clip:
        # Pega apenas os primeiros 5 segundos (Auto-corte)
        duracao = min(clip.duration, 5)
        final = clip.subclip(0, duracao)
        # fps=7 e cores=32 garantem que o arquivo final seja leve
        final.write_gif(gif_path, fps=7, logger=None, colors=32, opt="OptimizePlus")

# =========================
# Eventos Principais
# =========================

@bot.event
async def on_ready():
    print(f"✅ Bot logado como {bot.user}")
    print("👉 Digite !deploy no chat para ativar os comandos /")

@bot.event
async def on_member_join(member):
    try:
        embed = discord.Embed(
            title=f"⚔️ Bem-vindo(a), {member.name}!",
            description="Você entrou na **Celestial Trindade**! Siga os passos abaixo:",
            color=discord.Color.gold()
        )
        link_grupo = "https://www.roblox.com/pt/communities/34214394/Celestial-Trindade#!/about"
        embed.add_field(name="1️⃣ Grupo Roblox", value=f"[Clique para entrar]({link_grupo})", inline=False)
        embed.add_field(name="2️⃣ Identidade", value="Use nossa logo oficial no Peroxide.", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await member.send(embed=embed)
    except discord.Forbidden:
        print(f"❌ Não consegui enviar DM para {member.name} (Privado fechado)")

# =========================
# Comando de Sincronização
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def deploy(ctx):
    await ctx.send("📡 Sincronizando comandos Slash... aguarde.")
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Sucesso! {len(synced)} comandos sincronizados.")
    except Exception as e:
        await ctx.send(f"❌ Erro: {e}")

# =========================
# Slash Commands (/)
# =========================

@bot.tree.command(name="help", description="Lista todos os comandos do bot")
async def help_cmd(interaction: Interaction):
    embed = discord.Embed(title="🤖 Central de Ajuda - Celestial", color=discord.Color.blue())
    embed.add_field(name="/videogif", value="Converte vídeo em GIF (Corte auto 5s)", inline=False)
    embed.add_field(name="/videoaudio", value="Extrai o MP3 de um vídeo", inline=False)
    embed.add_field(name="/gifct", value="Converte Imagem em GIF", inline=False)
    embed.add_field(name="/logo", value="Mostra a logo e link da guilda", inline=False)
    embed.add_field(name="/ping", value="Verifica a conexão do bot", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="Verifica a latência do bot")
async def ping(interaction: Interaction):
    await interaction.response.send_message(f"🏓 Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="logo", description="Envia a logo e o link da Celestial Trindade")
async def logo(interaction: Interaction):
    link_grupo = "https://www.roblox.com/pt/communities/34214394/Celestial-Trindade#!/about"
    link_logo = "https://tr.rbxcdn.com/180DAY-8a0ac9f112f6761f919be4fe156a9cb5/420/420/Image/Webp/noFilter"
    embed = discord.Embed(title="🛡️ Celestial Trindade - Roblox", color=discord.Color.gold())
    embed.add_field(name="🔗 Nosso Grupo", value=f"[CLIQUE PARA ENTRAR]({link_grupo})")
    embed.set_image(url=link_logo)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="videogif", description="Converte vídeo para GIF animado (Máx 5s)")
async def videogif(interaction: Interaction, arquivo: discord.Attachment):
    if not arquivo.content_type or not arquivo.content_type.startswith("video"):
        return await interaction.response.send_message("❌ Isso não parece ser um vídeo!")

    await interaction.response.defer()
    v_path, g_path = f"v_{uuid.uuid4()}.mp4", f"g_{uuid.uuid4()}.gif"
    
    try:
        await arquivo.save(v_path)
        await asyncio.to_thread(converter_video_gif_sync, v_path, g_path)
        await interaction.followup.send(file=discord.File(g_path))
    except Exception as e:
        logging.error(f"ERRO VIDEOGIF: {e}")
        await interaction.followup.send("❌ Erro: Vídeo muito pesado ou formato incompatível.")
    finally:
        for p in (v_path, g_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="videoaudio", description="Converte vídeo em áudio MP3")
async def videoaudio(interaction: Interaction, arquivo: discord.Attachment):
    await interaction.response.defer()
    v_path, a_path = f"v_{uuid.uuid4()}.mp4", f"a_{uuid.uuid4()}.mp3"
    
    try:
        await arquivo.save(v_path)
        await asyncio.to_thread(extrair_audio_sync, v_path, a_path)
        await interaction.followup.send(file=discord.File(a_path))
    except Exception as e:
        logging.error(f"ERRO AUDIO: {e}")
        await interaction.followup.send("❌ Falha ao extrair áudio.")
    finally:
        for p in (v_path, a_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="gifct", description="Transforma imagem em GIF")
async def gifct(interaction: Interaction, arquivo: discord.Attachment):
    await interaction.response.defer()
    i_path, o_path = f"i_{uuid.uuid4()}.png", f"o_{uuid.uuid4()}.gif"
    try:
        await arquivo.save(i_path)
        await asyncio.to_thread(converter_imagem_sync, i_path, o_path)
        await interaction.followup.send(file=discord.File(o_path))
    except Exception as e:
        await interaction.followup.send("❌ Erro ao processar imagem.")
    finally:
        for p in (i_path, o_path):
            if os.path.exists(p): os.remove(p)

# =========================
# Inicialização Final
# =========================
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ Variável DISCORD_TOKEN não encontrada!")
    else:
        bot.run(DISCORD_TOKEN)