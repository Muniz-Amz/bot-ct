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
import random  # Necessário para o sorteio dos times
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
    return "🛡️ Celestial Bot - Sistema de Guerra Online!"

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
# SISTEMA DE GUERRA (Botões e Sorteio)
# =========================
class GuerraView(discord.ui.View):
    def __init__(self, imagem_url):
        super().__init__(timeout=None) # O botão nunca expira
        self.participantes = []
        self.imagem_url = imagem_url

    @discord.ui.button(label="⚔️ Participar (0/12)", style=discord.ButtonStyle.green, custom_id="btn_guerra_entrar")
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. Verifica se a pessoa já clicou
        if interaction.user in self.participantes:
            return await interaction.response.send_message("❌ Você já está na lista!", ephemeral=True)
        
        # 2. Verifica se já lotou
        if len(self.participantes) >= 12:
            return await interaction.response.send_message("❌ A guerra já está cheia!", ephemeral=True)

        # 3. Adiciona a pessoa
        self.participantes.append(interaction.user)
        
        # 4. Atualiza o texto do botão (Ex: "Participar (5/12)")
        button.label = f"⚔️ Participar ({len(self.participantes)}/12)"
        
        # 5. Se completou 12 pessoas, faz o sorteio
        if len(self.participantes) == 12:
            random.shuffle(self.participantes) # Mistura a lista
            time_a = self.participantes[:6]    # Pega os 6 primeiros
            time_b = self.participantes[6:]    # Pega os 6 últimos
            
            # Cria o Embed com o resultado
            embed_times = discord.Embed(title="🔥 TIMES SORTEADOS!", color=discord.Color.dark_red())
            embed_times.description = "A guerra vai começar! Organizem-se nos canais de voz."
            
            # Lista Time A
            lista_a = "\n".join([f"👤 {u.mention}" for u in time_a])
            embed_times.add_field(name="🔵 TIME A", value=lista_a, inline=True)
            
            # Lista Time B
            lista_b = "\n".join([f"👤 {u.mention}" for u in time_b])
            embed_times.add_field(name="🔴 TIME B", value=lista_b, inline=True)
            
            if self.imagem_url:
                embed_times.set_image(url=self.imagem_url)
            
            # Tranca o botão
            button.disabled = True
            button.label = "⛔ INSCRIÇÕES ENCERRADAS"
            button.style = discord.ButtonStyle.grey
            
            # Atualiza a mensagem original e manda o aviso
            await interaction.response.edit_message(view=self)
            await interaction.channel.send(content=f"🚨 **ATENÇÃO GUERREIROS! TIMES DEFINIDOS!**", embed=embed_times)
        else:
            # Se ainda não deu 12, só atualiza o botão
            await interaction.response.edit_message(view=self)

# =========================
# Funções de Processamento
# =========================
def converter_imagem_sync(input_path, output_path):
    with Image.open(input_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, format="GIF")

def extrair_audio_sync(video_path, audio_path):
    with VideoFileClip(video_path, target_resolution=(120, None)) as video:
        video.audio.write_audiofile(audio_path, logger=None, bitrate="64k")

def converter_video_gif_sync(video_path, gif_path):
    with VideoFileClip(video_path, audio=False, target_resolution=(300, None), fps_source="fps") as clip:
        duracao = min(clip.duration, 5)
        final = clip.subclip(0, duracao)
        final.write_gif(gif_path, fps=10, logger=None, colors=128, opt="OptimizePlus")

# =========================
# Eventos
# =========================
@bot.event
async def on_ready():
    print(f"✅ Bot logado como {bot.user}")
    print("👉 Use !deploy para atualizar.")

@bot.event
async def on_member_join(member):
    try:
        embed = discord.Embed(title=f"⚔️ Bem-vindo(a), {member.name}!", color=discord.Color.gold())
        embed.description = "Entre no grupo do Roblox para participar das guerras!"
        embed.add_field(name="🔗 Grupo", value="[Clique Aqui](https://www.roblox.com/pt/communities/34214394/Celestial-Trindade)")
        embed.set_thumbnail(url=member.display_avatar.url)
        await member.send(embed=embed)
    except:
        pass

# =========================
# Comandos
# =========================
@bot.command()
@commands.has_permissions(administrator=True)
async def deploy(ctx):
    await bot.tree.sync()
    await ctx.send("✅ Comandos sincronizados!")

@bot.tree.command(name="agendar_guerra", description="Agenda guerra e sorteia 2 times quando atingir 12 pessoas")
@app_commands.describe(data="Dia (ex: Hoje)", horario="Hora (ex: 20h)", imagem="Link da imagem (URL)")
async def agendar_guerra(interaction: Interaction, data: str, horario: str, imagem: str):
    embed = discord.Embed(
        title="⚔️ CONVOCAÇÃO DE GUERRA",
        description=f"**Data:** {data}\n**Horário:** {horario}\n\nClique abaixo para entrar na fila.\n**Precisa de 12 jogadores para sortear os times.**",
        color=discord.Color.gold()
    )
    embed.set_image(url=imagem)
    
    view = GuerraView(imagem_url=imagem)
    await interaction.response.send_message(embed=embed, view=view)

# --- Comandos de Mídia ---
@bot.tree.command(name="videogif")
async def videogif(interaction: Interaction, arquivo: discord.Attachment):
    if not arquivo.content_type.startswith("video"): return await interaction.response.send_message("❌ Envie um vídeo!")
    await interaction.response.defer()
    v_path, g_path = f"v_{uuid.uuid4()}.mp4", f"g_{uuid.uuid4()}.gif"
    try:
        await arquivo.save(v_path)
        await asyncio.to_thread(converter_video_gif_sync, v_path, g_path)
        await interaction.followup.send(file=discord.File(g_path))
    except Exception as e:
        await interaction.followup.send("❌ Erro ao converter.")
    finally:
        for p in (v_path, g_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="videoaudio")
async def videoaudio(interaction: Interaction, arquivo: discord.Attachment):
    await interaction.response.defer()
    v_path, a_path = f"v_{uuid.uuid4()}.mp4", f"a_{uuid.uuid4()}.mp3"
    try:
        await arquivo.save(v_path)
        await asyncio.to_thread(extrair_audio_sync, v_path, a_path)
        await interaction.followup.send(file=discord.File(a_path))
    except:
        await interaction.followup.send("❌ Erro.")
    finally:
        for p in (v_path, a_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="gifct")
async def gifct(interaction: Interaction, arquivo: discord.Attachment):
    await interaction.response.defer()
    i_path, o_path = f"i_{uuid.uuid4()}.png", f"o_{uuid.uuid4()}.gif"
    try:
        await arquivo.save(i_path)
        await asyncio.to_thread(converter_imagem_sync, i_path, o_path)
        await interaction.followup.send(file=discord.File(o_path))
    except:
        await interaction.followup.send("❌ Erro.")
    finally:
        for p in (i_path, o_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="ping")
async def ping(interaction: Interaction):
    await interaction.response.send_message(f"🏓 Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="logo")
async def logo(interaction: Interaction):
    embed = discord.Embed(title="🛡️ Celestial Trindade", color=discord.Color.gold())
    embed.set_image(url="https://tr.rbxcdn.com/180DAY-8a0ac9f112f6761f919be4fe156a9cb5/420/420/Image/Webp/noFilter")
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)