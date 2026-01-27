import discord
from discord import app_commands, Interaction
from discord.ext import commands
from PIL import Image
import os
import uuid
from flask import Flask
from threading import Thread
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
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# =========================
# Eventos
# =========================
@bot.event
async def on_ready():
    print(f"✅ Logado como {bot.user}")
    print("👉 Digite !deploy no seu servidor para ativar os comandos /")

# =========================
# Comando de Sincronização
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
# Funções de Imagem
# =========================
def converter_imagem_sync(input_path, output_path):
    with Image.open(input_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, format="GIF")

# =========================
# Slash Commands (/)
# =========================

@bot.tree.command(name="gifct", description="Converte PNG/JPG em GIF")
async def gifct(interaction: Interaction, file: discord.Attachment):
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
        await interaction.followup.send("❌ Erro ao converter.")
    finally:
        await asyncio.sleep(2)
        for p in (img_path, gif_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="ping", description="Verifica a latência do bot")
async def ping(interaction: Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 **Pong!** Latência: {latency}ms")

@bot.tree.command(name="help", description="Mostra como usar o bot")
async def help(interaction: Interaction):
    embed = discord.Embed(
        title="🤖 Central de Ajuda - Bot de GIFs",
        description="Eu transformo suas imagens estáticas em GIFs animados!",
        color=discord.Color.blue()
    )
    embed.add_field(name="/gifct", value="Anexe uma imagem (PNG/JPG) para converter.", inline=False)
    embed.add_field(name="/ping", value="Mostra a velocidade do bot.", inline=False)
    embed.set_footer(text="Desenvolvido com ❤️")
    await interaction.response.send_message(embed=embed)
# =========================
# Evento: Boas-vindas (Privado)
# =========================
@bot.event
async def on_member_join(member):
    try:
        embed = discord.Embed(
            title=f"Bem-vindo(a) à Celestial Trindade, {member.name}! ⚔️",
            description="É uma honra ter você conosco! Para fazer parte oficialmente, siga os dois passos abaixo:",
            color=discord.Color.from_rgb(255, 215, 0)
        )
        
        # Link do Grupo do Roblox
        link_grupo = "https://www.roblox.com/pt/communities/34214394/Celestial-Trindade#!/about"
        # Link da Imagem da Logo
        link_logo = "https://tr.rbxcdn.com/180DAY-8a0ac9f112f6761f919be4fe156a9cb5/420/420/Image/Webp/noFilter"

        embed.add_field(name="1️⃣ Entre no Grupo do Roblox", value=f"[CLIQUE AQUI PARA ENTRAR]({link_grupo})", inline=False)
        embed.add_field(name="2️⃣ Use a Logo no Perfil", value="Baixe a imagem abaixo e coloque-a na sua foto do Discord.", inline=False)
        
        embed.set_image(url=link_logo)
        embed.set_footer(text="A Trindade te espera no campo de batalha!")

        await member.send(embed=embed)
        print(f"✅ Convite e Logo enviados para {member.name}")
    except discord.Forbidden:
        print(f"❌ Privado fechado de {member.name}")

# =========================
# Comando: /logo (Manual)
# =========================
@bot.tree.command(name="logo", description="Envia o link do grupo e a logo da Celestial Trindade")
async def logo(interaction: discord.Interaction):
    link_grupo = "https://www.roblox.com/pt/communities/34214394/Celestial-Trindade#!/about"
    link_logo = "https://tr.rbxcdn.com/180DAY-8a0ac9f112f6761f919be4fe156a9cb5/420/420/Image/Webp/noFilter"

    embed = discord.Embed(
        title="🛡️ Identidade e Grupo - Celestial Trindade",
        description="Aqui estão as informações oficiais da guilda:",
        color=discord.Color.from_rgb(255, 215, 0)
    )
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