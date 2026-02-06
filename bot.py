import discord
from discord import app_commands, Interaction
from discord.ext import commands
from PIL import Image
import os, uuid, asyncio, logging, random, time, threading
from flask import Flask

# =========================
# CONFIGURAÇÕES E KEEPALIVE
# =========================
logging.basicConfig(level=logging.INFO)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

app = Flask(__name__)
@app.route("/")
def home(): return "🛡️ Celestial Bot Online!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_flask, daemon=True).start()

# =========================
# SETUP DO BOT
# =========================
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True          
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# =========================
# SISTEMA DE GUERRA (A PARTE MAIS BONITA)
# =========================
class GuerraView(discord.ui.View):
    def __init__(self, imagem_url):
        super().__init__(timeout=None)
        self.participantes = []
        self.imagem_url = imagem_url

    @discord.ui.button(label="⚔️ Participar (0/12)", style=discord.ButtonStyle.green, custom_id="war_join")
    async def participar(self, it: Interaction, btn: discord.ui.Button):
        if it.user in self.participantes:
            return await it.response.send_message("❌ Você já está na lista!", ephemeral=True)
        if len(self.participantes) >= 12:
            return await it.response.send_message("❌ A guerra já está cheia!", ephemeral=True)

        self.participantes.append(it.user)
        btn.label = f"⚔️ Participar ({len(self.participantes)}/12)"
        
        if len(self.participantes) == 12:
            random.shuffle(self.participantes)
            a, b = self.participantes[:6], self.participantes[6:]
            em = discord.Embed(title="🔥 TIMES SORTEADOS!", color=0x990000)
            em.description = "🛡️ **A guerra vai começar! Organizem-se nos canais de voz.**"
            em.add_field(name="🔵 TIME ALPHA", value="\n".join([f"👤 {u.mention}" for u in a]), inline=True)
            em.add_field(name="🔴 TIME OMEGA", value="\n".join([f"👤 {u.mention}" for u in b]), inline=True)
            if self.imagem_url: em.set_image(url=self.imagem_url)
            for child in self.children: child.disabled = True
            await it.response.edit_message(view=self)
            await it.channel.send(content="🚨 **ATENÇÃO GUERREIROS! TIMES DEFINIDOS!**", embed=em)
        else:
            await it.response.edit_message(view=self)
            await it.followup.send("✅ **Inscrição Confirmada!**\n⚠️ **Atenção:** Ausência sem aviso gera MUTE ou WARN.", ephemeral=True)

    @discord.ui.button(label="✖️ Sair da Fila", style=discord.ButtonStyle.red, custom_id="war_leave")
    async def sair(self, it: Interaction, btn: discord.ui.Button):
        if it.user not in self.participantes:
            return await it.response.send_message("❌ Você não está inscrito.", ephemeral=True)
        self.participantes.remove(it.user)
        self.children[0].label = f"⚔️ Participar ({len(self.participantes)}/12)"
        await it.response.edit_message(view=self)

# =========================
# COMANDOS SLASH (ESTILIZADOS)
# =========================

@bot.tree.command(name="regras", description="Exibe as leis fundamentais da Celestial Trindade")
async def regras(it: Interaction):
    logo = "https://tr.rbxcdn.com/180DAY-8a0ac9f112f6761f919be4fe156a9cb5/420/420/Image/Webp/noFilter"
    
    e1 = discord.Embed(title="📜 Regras do Servidor", color=0xFFD700) # Dourado
    e1.add_field(name="⚖️ Conduta", value="1. Respeito mútuo.\n2. Sem Spam/Flood.\n3. Proibido conteúdo +18.", inline=False)
    e1.set_thumbnail(url=logo)

    e2 = discord.Embed(title="⚔️ Regras de Jogo (Peroxide)", color=0x000000) # Preto
    e2.add_field(name="🛡️ Identidade", value="1. Obrigatório usar a Logo.\n2. Proibido matar aliados ou Allys.", inline=False)
    
    e3 = discord.Embed(title="⚠️ Sistema de WARNs", color=0xFF0000) # Vermelho
    e3.add_field(name="Punições", value="`3-4 WARNs`: Suspensão.\n`7 WARNs`: **EXPULSÃO IMEDIATA.**", inline=False)
    e3.set_footer(text="Celestial Trindade - A honra acima de tudo.")

    await it.response.send_message(embeds=[e1, e2, e3])

@bot.tree.command(name="solicitar", description="Pede aprovação no grupo do Roblox")
async def solicitar(it: Interaction, nick: str):
    cargos = [1395092778614132777, 1458811065583403323] # Seus cargos de ADM
    mencoes = " ".join([f"<@&{c}>" for c in cargos])
    
    em = discord.Embed(title="📝 Nova Solicitação de Entrada", color=0x0000FF)
    em.add_field(name="👤 Nick no Roblox", value=f"`{nick}`", inline=True)
    em.add_field(name="🔗 Perfil", value=f"[Abrir Perfil](https://www.roblox.com/users/profile?username={nick})", inline=True)
    em.set_thumbnail(url=it.user.display_avatar.url)
    em.set_footer(text="Celestial Trindade - Sistema de Recrutamento")

    await it.response.send_message(content=f"🔔 {mencoes}, novo guerreiro aguardando!", embed=em)

@bot.tree.command(name="videogif", description="Converte vídeo para GIF (Max 5s)")
async def videogif(it: Interaction, arquivo: discord.Attachment):
    if not arquivo.content_type.startswith("video"): return await it.response.send_message("❌ Isso não é um vídeo!")
    await it.response.defer()
    
    from moviepy.editor import VideoFileClip # Import pesado fica escondido aqui
    v_path, g_path = f"{uuid.uuid4()}.mp4", f"{uuid.uuid4()}.gif"
    try:
        await arquivo.save(v_path)
        with VideoFileClip(v_path, audio=False, target_resolution=(240, None)) as clip:
            clip.subclip(0, min(clip.duration, 5)).write_gif(g_path, fps=10, logger=None)
        await it.followup.send(file=discord.File(g_path))
    except Exception as e: await it.followup.send(f"❌ Erro: {e}")
    finally:
        for p in (v_path, g_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="agendar_guerra", description="Inicia chamada para guerra")
async def agendar(it: Interaction, data: str, hora: str, imagem: str, regras: str):
    em = discord.Embed(title="⚔️ CONVOCAÇÃO DE GUERRA", color=0xFFD700)
    em.add_field(name="📅 Data", value=data, inline=True)
    em.add_field(name="⏰ Horário", value=hora, inline=True)
    em.add_field(name="📜 Regras", value=f"```\n{regras}\n```", inline=False)
    em.set_image(url=imagem)
    em.set_footer(text="Celestial Trindade - Sistema Automático")
    await it.response.send_message(embed=em, view=GuerraView(imagem))

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ {bot.user} ONLINE!")

if __name__ == "__main__":
    if DISCORD_TOKEN: bot.run(DISCORD_TOKEN)