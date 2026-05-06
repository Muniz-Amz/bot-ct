
import discord
from discord import app_commands, Interaction
from discord.ext import commands, tasks
from PIL import Image
import os
import uuid
import asyncio
import logging
import random
import time
import aiohttp
import io
from flask import Flask
from threading import Thread
import moviepy.editor as mp
from moviepy.editor import VideoFileClip
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify
from flask_cors import CORS
# ... (Configurações de Log, Token e Ranks PVP) ...

# =========================
# CONFIGURAÇÕES DE LOG E TOKEN
# =========================
logging.basicConfig(level=logging.INFO)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


# Dicionário de Ranks para consulta do Bot

# ==========================
# SISTEMA KEEP ALIVE (FLASK)
# ==========================
app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return "🛡️ Souls Bot - Sistema de Guerra Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

keep_alive()

# =========================
# CONFIGURAÇÃO DO BOT
# =========================
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True          
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


# --- VIEW PARA O MENU PEROXIDE ---
class PeroxideView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Selecione o que deseja consultar...",
        options=[
            discord.SelectOption(label="🌐 Servidores Oficiais (DC)", description="Gotei 13, Wandenreich, Las Noches...", emoji="🔗"),
            discord.SelectOption(label="🏟️ Arenas Privadas", description="Lista de códigos para arenas", emoji="⚔️"),
            discord.SelectOption(label="💰 Tabela de Valores (Trade)", description="Valores de troca de itens", emoji="📉"),
            discord.SelectOption(label="📚 Wiki & Trello", description="Links para guias e informações", emoji="📖")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        escolha = select.values[0]
        embed = discord.Embed(color=discord.Color.blue())

        if escolha == "🌐 Servidores Oficiais (DC)":
            embed.title = "🌐 Servidores Oficiais do Peroxide"
            embed.description = (
                "**Gotei 13:** [Entrar](https://discord.gg/pEFDJke57G)\n"
                "**Wandenreich:** [Entrar](https://discord.gg/g2g7YJzeva)\n"
                "**✕cution:** [Entrar](https://discord.gg/QUJ3z28Bx7)\n"
                "**Las Noches:** [Entrar](https://discord.gg/8dqU9rWqGw)\n\n"
                "**Servidor Oficial Peroxide:** [Clique Aqui](https://discord.gg/WkS4UvmtFH)\n"
                "**Peroxide Support:** [Clique Aqui](https://discord.gg/9RFa6k7ra)\n"
            )

        elif escolha == "🏟️ Arenas Privadas":
            embed.title = "🏟️ Códigos de Arenas Privadas"
            embed.description = (
                "Copie e cole os códigos abaixo no jogo:\n\n"
                "`YzP20tx2ioNU`\n`OsF8EVLjtvuv`\n`uCKibt4s4ODq`\n"
                "`3HSbTOgt0MoB`\n`bFiQTRvskV6B`\n`WAFW0KpaanL2`"
            )
            embed.set_footer(text="Use com sabedoria para treinar!")

        elif escolha == "💰 Tabela de Valores (Trade)":
            embed.title = "💰 Lista de Valor de Troca"
            embed.description = (
                "Confira os valores atualizados dos itens para trocas:\n\n"
                "🔗 [Planilha de Valores (Google Docs)](https://docs.google.com/spreadsheets/d/1-yzMInes6bUe35qenH1XGSnqCn9kDp62Bg9iYtfuOUs/edit?gid=0#gid=0)"
            )

        elif escolha == "📚 Wiki & Trello":
            embed.title = "📚 Guias e Enciclopédias"
            embed.add_field(name="📋 Trello Oficial", value="[Acessar Trello](https://trello.com/b/S9Uu73kt/peroxide-trello)", inline=False)
            embed.add_field(name="📖 Wiki Fandom", value="[Acessar Wiki](https://peroxide-roblox.fandom.com/wiki/Peroxide_Wiki)", inline=False)

        await interaction.response.edit_message(embed=embed, view=self)

def converter_imagem_sync(input_path, output_path):
    with Image.open(input_path) as img:
        # 1. Converte para RGBA para ler a imagem original com perfeição
        img = img.convert("RGBA")
        
        # 2. Cria um fundo sólido (BRANCO) do mesmo tamanho da imagem
        # Isso remove qualquer "sujeira" ou marcação fantasma por baixo
        fundo = Image.new("RGB", img.size, (255, 255, 255))
        
        # 3. Cola a imagem sobre o fundo usando a própria imagem como máscara
        # Isso garante que as bordas fiquem idênticas à PNG original
        fundo.paste(img, (0, 0), mask=img)
        
        # 4. Converte para o modo de cores do GIF (P) de forma ADAPTATIVA
        # O modo ADAPTIVE escolhe as melhores cores para não perder qualidade
        final = fundo.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
        
        # 5. Salva como GIF de quadro único
        final.save(
            output_path, 
            format="GIF", 
            optimize=True
        )

def extrair_audio_sync(video_path, audio_path):
    with VideoFileClip(video_path, target_resolution=(120, None)) as video:
        video.audio.write_audiofile(audio_path, logger=None, bitrate="64k")

def converter_video_gif_sync(video_path, gif_path):
    with VideoFileClip(video_path, audio=False, target_resolution=(300, None)) as clip:
        duracao = min(clip.duration, 5)
        final = clip.subclip(0, duracao)
        final.write_gif(gif_path, fps=12, logger=None, colors=128, opt="OptimizePlus")

# --- COMANDO SLASH ---
@bot.tree.command(name="peroxide", description="Informações úteis sobre o jogo Peroxide")
async def peroxide(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ Central de Informações Lost Souls - Peroxide",
        description="Escolha uma opção no menu abaixo para acessar links, códigos de arena e tabelas.",
        color=discord.Color.from_rgb(0, 0, 0)
    )
    # Espaço invisível para organizar o layout se precisar
    embed.add_field(name="\u3164", value="Acesse o conteúdo oficial abaixo:", inline=False)
    
    await interaction.response.send_message(embed=embed, view=PeroxideView())
# =========================
# EVENTOS DO BOT
# =========================

        
@bot.event
async def on_ready():
    print(f"✅ Bot logado como {bot.user}")
    print("👉 Use !deploy no Discord para atualizar os comandos Slash.")

@bot.event
async def on_member_join(member):
    try:
        embed = discord.Embed(
            title=f" Bem-vindo(a) à o Servidor, {member.name}!",
            description="É uma honra ter você conosco! Sejá bem vindo e fortaleça nossa Comunidade.",
            color=discord.Color.gold()
        )
        
        await member.send(embed=embed)
    except discord.Forbidden:
        print(f"❌ DM fechada para {member.name}.")
    except Exception as e:
        print(f"❌ Erro no on_member_join: {e}")

# =========================
# COMANDOS SLASH (/)
# =========================

@bot.tree.command(name="help", description="Mostra a lista completa de comandos e como usá-los")
async def help_cmd(interaction: discord.Interaction):
    link_logo = "https://cdn.discordapp.com/attachments/1478901345963479131/1501375280508567583/Gemini_Generated_Image_s6lv1ps6lv1ps6lv.png?ex=69fbd831&is=69fa86b1&hm=880567f0b71a7d0bee9c39da567d7d314cf29939df3ff486a18b584fc9495854&"
    
    embed = discord.Embed(
        title="📚 Central de Ajuda - AMZ Bot",
        description="Veja os Comandos da **Society** com nossos comandos oficiais.",
        color=discord.Color.blue()
    )

    # --- GESTÃO DE GUILDA ---
    embed.add_field(
        name="🛡️ Gestão de Guilda", 
        value=(
          
            "`/peroxide` - Central de links, arenas e guia de trade.\n"
          
        ), 
        inline=False
    )

    # --- FERRAMENTAS DE MÍDIA ---
    embed.add_field(
        name="🎬 Ferramentas de Mídia", 
        value=(
            "`/videogif` - Converte vídeos curtos em GIF.\n"
            "`/videoaudio` - Extrai o áudio (MP3) de vídeos.\n"
            "`/gifs` - Converte PNG para GIF nítido (HQ)."
        ), 
        inline=False
    )

    # --- SISTEMA ---
    embed.add_field(
        name="🔧 Sistema", 
        value="`/ping` - Latência do bot.\n`!deploy` - Sincroniza comandos (Admin).", 
        inline=False
    )


    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="Verifica a latência atual do bot")
async def ping(interaction: Interaction):
    await interaction.response.send_message(f"🏓 **Pong!** `{round(bot.latency * 1000)}ms`")


# --- Comandos de Mídia ---

@bot.tree.command(name="videogif", description="Converte um vídeo para GIF (máximo 5 segundos)")
async def videogif(interaction: Interaction, arquivo: discord.Attachment):
    if not arquivo.content_type.startswith("video"): 
        return await interaction.response.send_message("❌ Por favor, envie um arquivo de vídeo!", ephemeral=True)
    
    await interaction.response.defer()
    v_path, g_path = f"v_{uuid.uuid4()}.mp4", f"g_{uuid.uuid4()}.gif"
    try:
        await arquivo.save(v_path)
        # O uso do asyncio.to_thread é essencial para o Render não travar
        await asyncio.to_thread(converter_video_gif_sync, v_path, g_path)
        
        # CORREÇÃO: filename="resultado.gif" força o Discord a mostrar a imagem aberta
        await interaction.followup.send(file=discord.File(g_path, filename="resultado.gif"))
    except Exception as e:
        print(f"Erro videogif: {e}")
        await interaction.followup.send("❌ Erro ao converter o vídeo.")
    finally:
        for p in (v_path, g_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="videoaudio", description="Converte um vídeo para arquivo de áudio MP3")
async def videoaudio(interaction: Interaction, arquivo: discord.Attachment):
    if not arquivo.content_type.startswith("video"):
        return await interaction.response.send_message("❌ Envie um arquivo de vídeo!", ephemeral=True)

    await interaction.response.defer()
    v_path, a_path = f"v_{uuid.uuid4()}.mp4", f"a_{uuid.uuid4()}.mp3"
    try:
        await arquivo.save(v_path)
        # Isso resolve o erro "extrair_audio_sync is not defined" se a função estiver acima
        await asyncio.to_thread(extrair_audio_sync, v_path, a_path)
        
        # CORREÇÃO: filename="audio.mp3" permite ouvir direto no player do Discord
        await interaction.followup.send(file=discord.File(a_path, filename="audio.mp3"))
    except Exception as e:
        print(f"Erro videoaudio: {e}")
        await interaction.followup.send("❌ Erro ao extrair áudio.")
    finally:
        for p in (v_path, a_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="gifs", description="Converte PNG para um GIF idêntico e nítido")
async def gifct(interaction: discord.Interaction, arquivo: discord.Attachment):
    await interaction.response.defer()
    
    i_path = f"input_{uuid.uuid4()}.png"
    o_path = f"output_{uuid.uuid4()}.gif"
    
    try:
        await arquivo.save(i_path)
        # Usando to_thread para manter consistência com os outros comandos
        await asyncio.to_thread(converter_imagem_sync, i_path, o_path)
        
        # CORREÇÃO: filename="imagem.gif" resolve o problema do link azul (print image_5f3ce1.png)
        await interaction.followup.send(file=discord.File(o_path, filename="resultado.gif"))
        
    except Exception as e:
        print(f"Erro no GIF: {e}")
        await interaction.followup.send("❌ Erro ao converter para GIF.")
    finally:
        for p in (i_path, o_path):
            if os.path.exists(p): 
                os.remove(p)



@bot.command()
@commands.has_permissions(administrator=True)
async def deploy(ctx):
    try:
        await bot.tree.sync()
        await ctx.send("✅ **Comandos Slash sincronizados com sucesso!**")
    except Exception as e:
        await ctx.send(f"❌ Erro ao sincronizar: {e}")
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)