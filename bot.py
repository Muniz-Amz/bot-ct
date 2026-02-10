# ============================================================
#             SISTEMA SUPREMO CELESTIAL TRINDADE
# ============================================================
# Versão: 2.0 - Expandida e Detalhada
# Objetivo: Gestão de Guerra, Recrutamento e Mídia
# ============================================================

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
import random
from moviepy.editor import VideoFileClip
import datetime
import time

# --- CONFIGURAÇÃO DE LOGS (Essencial para depuração) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CelestialBot')

# --- CONFIGURAÇÕES DE IDENTIDADE ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LINK_LOGO = "https://tr.rbxcdn.com/180DAY-8a0ac9f112f6761f919be4fe156a9cb5/420/420/Image/Webp/noFilter"
LINK_GRUPO = "https://www.roblox.com/pt/communities/34214394/Celestial-Trindade#!/about"

# IDs da Staff (Para notificações privadas e menções)
IDS_ADMINS = [840997758202413093, 1041870714124382258, 1129212119213146136, 845105032449884161]
CARGOS_STAFF = [1395092778614132777, 1458811065583403323, 1425983765053837402, 1467634329214652486]

# ============================================================
#             SISTEMA KEEP ALIVE (WEB SERVER)
# ============================================================
app = Flask(__name__)

@app.route("/")
def index():
    return "🛡️ Celestial Bot está Online e Operacional!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Iniciando servidor Flask na porta {port}")
    app.run(host="0.0.0.0", port=port)

# Iniciando a thread de manutenção para o bot não dormir
Thread(target=run_server, daemon=True).start()

# ============================================================
#             CORE DO BOT E INTENTS
# ============================================================
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True          

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ============================================================
#             FUNÇÕES TÉCNICAS (PROCESSAMENTO)
# ============================================================

def converter_imagem_sync(input_path, output_path):
    """Transforma imagens estáticas em GIF compatível."""
    try:
        with Image.open(input_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_path, format="GIF")
        return True
    except Exception as e:
        logger.error(f"Erro na conversão de imagem: {e}")
        return False

def extrair_audio_sync(video_path, audio_path):
    """Extrai áudio MP3 de vídeos MP4."""
    try:
        with VideoFileClip(video_path) as video:
            video.audio.write_audiofile(audio_path, logger=None, bitrate="64k")
        return True
    except Exception as e:
        logger.error(f"Erro na extração de áudio: {e}")
        return False

def converter_video_gif_sync(video_path, gif_path):
    """Converte trecho de vídeo em GIF animado."""
    try:
        with VideoFileClip(video_path, audio=False) as clip:
            # Limita a 5 segundos para não pesar o Discord
            duracao = min(clip.duration, 5)
            clip_final = clip.subclip(0, duracao)
            clip_final.write_gif(gif_path, fps=10, logger=None, colors=128, opt="OptimizePlus")
        return True
    except Exception as e:
        logger.error(f"Erro na conversão de vídeo para GIF: {e}")
        return False

# ============================================================
#             SISTEMA DE GUERRA (INTERFACE)
# ============================================================

class GuerraView(discord.ui.View):
    def __init__(self, imagem_url):
        super().__init__(timeout=None)
        self.participantes = []
        self.imagem_url = imagem_url

    @discord.ui.button(label="⚔️ ALISTAR-SE (0/12)", style=discord.ButtonStyle.green, custom_id="btn_entrar")
    async def entrar_guerra(self, interaction: Interaction, button: discord.ui.Button):
        if interaction.user in self.participantes:
            return await interaction.response.send_message("❌ Você já está inscrito!", ephemeral=True)
        
        if len(self.participantes) >= 12:
            return await interaction.response.send_message("❌ Pelotão lotado!", ephemeral=True)

        self.participantes.append(interaction.user)
        button.label = f"⚔️ ALISTAR-SE ({len(self.participantes)}/12)"
        
        if len(self.participantes) == 12:
            # Sorteio de times Alpha e Omega
            random.shuffle(self.participantes)
            time_a = self.participantes[:6]
            time_b = self.participantes[6:]
            
            embed = discord.Embed(title="🔥 GUERRA DECLARADA - TIMES DEFINIDOS", color=0xFF0000)
            embed.add_field(name="🔵 ALPHA", value="\n".join([u.mention for u in time_a]), inline=True)
            embed.add_field(name="🔴 OMEGA", value="\n".join([u.mention for u in time_b]), inline=True)
            embed.set_image(url=self.imagem_url)
            
            for item in self.children: item.disabled = True
            button.label = "🚫 INSCRIÇÕES FECHADAS"
            
            await interaction.response.edit_message(view=self)
            await interaction.channel.send(content="🚨 **ATENÇÃO! TIMES SORTEADOS!**", embed=embed)
        else:
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="✖️ SAIR", style=discord.ButtonStyle.red, custom_id="btn_sair")
    async def sair_guerra(self, interaction: Interaction, button: discord.ui.Button):
        if interaction.user not in self.participantes:
            return await interaction.response.send_message("❌ Você não está na lista.", ephemeral=True)
        
        self.participantes.remove(interaction.user)
        self.children[0].label = f"⚔️ ALISTAR-SE ({len(self.participantes)}/12)"
        await interaction.response.edit_message(view=self)

# ============================================================
#             COMANDOS SLASH (DETALHADOS)
# ============================================================

@bot.tree.command(name="solicitar", description="Pede aprovação no grupo e avisa a Staff")
async def solicitar(it: Interaction, nick_roblox: str):
    # Lógica de menção extensa
    mencoes = ""
    for cid in CARGOS_STAFF:
        mencoes += f"<@&{cid}> "
    
    embed = discord.Embed(title="📝 PEDIDO DE RECRUTAMENTO", color=0x00AAFF)
    embed.add_field(name="👤 Usuário", value=it.user.mention, inline=True)
    embed.add_field(name="🆔 Nick", value=f"`{nick_roblox}`", inline=True)
    embed.set_footer(text="Celestial Trindade - Sistema Automático")
    
    await it.response.send_message(content=f"🔔 {mencoes}", embed=embed)
    
    # Notificação via DM para cada Admin
    for aid in IDS_ADMINS:
        try:
            admin = await bot.fetch_user(aid)
            await admin.send(embed=embed)
        except:
            continue

# (Aqui continuariam os comandos /regras, /videogif, etc. mantendo este mesmo padrão)

@bot.event
async def on_ready():
    logger.info(f"Bot logado como {bot.user}")
    await bot.tree.sync()

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)