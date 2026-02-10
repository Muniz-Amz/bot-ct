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
import time

# =========================
# CONFIGURAÇÕES DE LOG E TOKEN
# =========================
logging.basicConfig(level=logging.INFO)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# =========================
# SISTEMA KEEP ALIVE (FLASK)
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
# CONFIGURAÇÃO DO BOT
# =========================
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True          
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# =========================
# SISTEMA DE GUERRA (LOGICA ATUALIZADA)
# =========================
class GuerraView(discord.ui.View):
    def __init__(self, imagem_url):
        super().__init__(timeout=None)
        self.participantes = []
        self.imagem_url = imagem_url

    # --- BOTÃO ENTRAR ---
    @discord.ui.button(label="⚔️ Participar (0/12)", style=discord.ButtonStyle.green, custom_id="btn_guerra_entrar")
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verifica se já está na lista
        if interaction.user in self.participantes:
            return await interaction.response.send_message("❌ Você já está na lista!", ephemeral=True)
        
        # Verifica se está cheio
        if len(self.participantes) >= 12:
            return await interaction.response.send_message("❌ A guerra já está cheia!", ephemeral=True)

        # Adiciona o usuário
        self.participantes.append(interaction.user)
        
        # Atualiza o texto do botão
        button.label = f"⚔️ Participar ({len(self.participantes)}/12)"
        
        # Lógica de Sorteio (quando bater 12)
        if len(self.participantes) == 12:
            random.shuffle(self.participantes)
            time_a = self.participantes[:6]
            time_b = self.participantes[6:]
            
            embed_times = discord.Embed(title="🔥 TIMES SORTEADOS!", color=discord.Color.dark_red())
            embed_times.description = "A guerra vai começar! Organizem-se nos canais de voz."
            
            lista_a = "\n".join([f"👤 {u.mention}" for u in time_a])
            embed_times.add_field(name="🔵 TIME ALPHA", value=lista_a, inline=True)
            
            lista_b = "\n".join([f"👤 {u.mention}" for u in time_b])
            embed_times.add_field(name="🔴 TIME OMEGA", value=lista_b, inline=True)
            
            if self.imagem_url:
                embed_times.set_image(url=self.imagem_url)
            
            # Tranca TODOS os botões
            for child in self.children:
                child.disabled = True
            
            button.label = "⛔ INSCRIÇÕES ENCERRADAS"
            button.style = discord.ButtonStyle.grey
            
            await interaction.response.edit_message(view=self)
            await interaction.channel.send(content="🚨 **ATENÇÃO GUERREIROS! TIMES DEFINIDOS!**", embed=embed_times)
        else:
            # Se não lotou, apenas atualiza a mensagem e manda o aviso de punição no privado
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("✅ **Inscrição Confirmada!**\n⚠️ **ATENÇÃO:** Se você não aparecer no horário marcado, receberá **MUTE**. Em caso de reincidência, será aplicado **WARN**.", ephemeral=True)

    # --- BOTÃO SAIR / CANCELAR ---
    @discord.ui.button(label="✖️ Sair da Fila", style=discord.ButtonStyle.red, custom_id="btn_guerra_sair")
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participantes:
            return await interaction.response.send_message("❌ Você não está na lista de inscrição.", ephemeral=True)
        
        # Remove o usuário
        self.participantes.remove(interaction.user)
        
        # Atualiza o botão de contagem (o primeiro botão da lista)
        botao_participar = self.children[0] # Pega o botão verde pelo índice
        botao_participar.label = f"⚔️ Participar ({len(self.participantes)}/12)"
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("🗑️ Você cancelou sua inscrição.", ephemeral=True)

# =========================
# FUNÇÕES DE PROCESSAMENTO
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
            title=f"⚔️ Bem-vindo(a) à Celestial Trindade, {member.name}!",
            description="É uma honra ter você conosco! Prepare-se para as batalhas e fortaleça nossa guilda.",
            color=discord.Color.gold()
        )
        
        link_grupo = "https://www.roblox.com/pt/communities/34214394/Celestial-Trindade#!/about"
        link_logo = "https://tr.rbxcdn.com/180DAY-8a0ac9f112f6761f919be4fe156a9cb5/420/420/Image/Webp/noFilter"

        # Instrução do comando /solicitar
        embed.add_field(
            name="📝 Como entrar no Grupo", 
            value="1. Entre no link do grupo abaixo e peça para entrar.\n2. Volte aqui no servidor e digite o comando `/solicitar`.", 
            inline=False
        )
        
        embed.add_field(name="🛡️ Grupo no Roblox", value=f"[ENTRAR NO GRUPO]({link_grupo})", inline=False)
        embed.add_field(name="📢 Aviso", value="Certifique-se de estar no grupo para participar dos eventos e ganhar cargos!", inline=False)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=link_logo)
        embed.set_footer(text="Celestial Trindade - A serviço da honra.")

        await member.send(embed=embed)
    except discord.Forbidden:
        print(f"❌ DM fechada para {member.name}.")
    except Exception as e:
        print(f"❌ Erro no on_member_join: {e}")

# =========================
# COMANDOS ADMINISTRATIVOS
# =========================
@bot.command()
@commands.has_permissions(administrator=True)
async def deploy(ctx):
    await bot.tree.sync()
    await ctx.send("✅ **Comandos Slash sincronizados com sucesso!**")

# =========================
# COMANDOS SLASH (/)
# =========================

@bot.tree.command(name="help", description="Mostra a lista completa de comandos e como usá-los")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Central de Ajuda - Celestial Bot",
        description="Aqui estão todos os comandos disponíveis para os membros da guilda:",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="⚔️ EVENTOS E GUILDA", 
        value="`/agendar_guerra` - Cria um painel de inscrição para 12 pessoas.\n`/logo` - Informações e link oficial do grupo.\n`/regras` - Exibe as leis do servidor.\n`/solicitar` - Pede aprovação no grupo do Roblox.", 
        inline=False
    )
    
    embed.add_field(
        name="🎬 FERRAMENTAS DE MÍDIA", 
        value="`/videogif` - Converte vídeo para GIF nítido.\n`/videoaudio` - Extrai MP3 de um vídeo.\n`/gifct` - Converte imagem para GIF.", 
        inline=False
    )
    
    embed.add_field(
        name="🔧 SISTEMA", 
        value="`/ping` - Verifica a latência do bot.\n`!deploy` - Sincroniza comandos (Admin).", 
        inline=False
    )
    
    embed.set_footer(text="🛡️ Celestial Trindade", icon_url="https://tr.rbxcdn.com/180DAY-8a0ac9f112f6761f919be4fe156a9cb5/420/420/Image/Webp/noFilter")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="Verifica a latência atual do bot")
async def ping(interaction: Interaction):
    await interaction.response.send_message(f"🏓 **Pong!** `{round(bot.latency * 1000)}ms`")

@bot.tree.command(name="logo", description="Mostra a identidade visual e o link da Celestial Trindade")
async def logo(interaction: Interaction):
    link_grupo = "https://www.roblox.com/pt/communities/34214394/Celestial-Trindade#!/about"
    link_logo = "https://tr.rbxcdn.com/180DAY-8a0ac9f112f6761f919be4fe156a9cb5/420/420/Image/Webp/noFilter"
    
    embed = discord.Embed(
        title="🛡️ Celestial Trindade - Oficial",
        description="Unidos pela força, guiados pela honra.",
        color=discord.Color.gold()
    )
    embed.add_field(name="🔗 Link do Grupo", value=f"[CLIQUE PARA ENTRAR]({link_grupo})", inline=False)
    embed.add_field(name="⚔️ Status", value="Recrutamento Aberto", inline=True)
    embed.add_field(name="📜 Requisito", value="Usar logo no Peroxide", inline=True)
    embed.set_image(url=link_logo)
    embed.set_footer(text=f"Solicitado por {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="agendar_guerra", description="Inicia uma chamada para guerra com sorteio de times e regras")
@app_commands.describe(data="Ex: Hoje", horario="Ex: 20:00", imagem="Link da imagem (URL)", limitacoes="Regras de build/nível (Ex: Sem Bankai, Apenas Shikai)")
async def agendar_guerra(interaction: Interaction, data: str, horario: str, imagem: str, limitacoes: str):
    embed = discord.Embed(
        title="⚔️ CONVOCAÇÃO DE GUERRA",
        description=f"Preparem-se guerreiros! A batalha foi anunciada.\n**Precisa de 12 jogadores para sortear os times.**",
        color=discord.Color.gold()
    )
    
    # Detalhes do Evento
    embed.add_field(name="📅 Data", value=data, inline=True)
    embed.add_field(name="⏰ Horário", value=horario, inline=True)
    
    # Campo de Regras e Limitações
    embed.add_field(name="📜 Regras / Limitações", value=f"```\n{limitacoes}\n```", inline=False)
    
    # Aviso de Punição
    embed.add_field(
        name="🚨 PUNIÇÃO POR AUSÊNCIA", 
        value="**Não comparecer no horário marcado = MUTE.**\n**Reincidência = WARN.**\n*Cancele sua inscrição se não puder ir.*", 
        inline=False
    )

    embed.set_image(url=imagem)
    embed.set_footer(text="Celestial Trindade - Sistema Automático de Guerra")
    
    view = GuerraView(imagem_url=imagem)
    await interaction.response.send_message(embed=embed, view=view)

# --- Comandos de Mídia ---

@bot.tree.command(name="videogif", description="Converte um vídeo para GIF (máximo 5 segundos)")
async def videogif(interaction: Interaction, arquivo: discord.Attachment):
    if not arquivo.content_type.startswith("video"): 
        return await interaction.response.send_message("❌ Por favor, envie um arquivo de vídeo!")
    
    await interaction.response.defer()
    v_path, g_path = f"v_{uuid.uuid4()}.mp4", f"g_{uuid.uuid4()}.gif"
    try:
        await arquivo.save(v_path)
        await asyncio.to_thread(converter_video_gif_sync, v_path, g_path)
        await interaction.followup.send(file=discord.File(g_path))
    except Exception:
        await interaction.followup.send("❌ Erro ao converter o vídeo.")
    finally:
        for p in (v_path, g_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="videoaudio", description="Converte um vídeo para arquivo de áudio MP3")
async def videoaudio(interaction: Interaction, arquivo: discord.Attachment):
    await interaction.response.defer()
    v_path, a_path = f"v_{uuid.uuid4()}.mp4", f"a_{uuid.uuid4()}.mp3"
    try:
        await arquivo.save(v_path)
        await asyncio.to_thread(extrair_audio_sync, v_path, a_path)
        await interaction.followup.send(file=discord.File(a_path))
    except Exception:
        await interaction.followup.send("❌ Erro ao extrair áudio.")
    finally:
        for p in (v_path, a_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="gifct", description="Transforma uma imagem em formato GIF")
async def gifct(interaction: Interaction, arquivo: discord.Attachment):
    await interaction.response.defer()
    i_path, o_path = f"i_{uuid.uuid4()}.png", f"o_{uuid.uuid4()}.gif"
    try:
        await arquivo.save(i_path)
        await asyncio.to_thread(converter_imagem_sync, i_path, o_path)
        await interaction.followup.send(file=discord.File(o_path))
    except Exception:
        await interaction.followup.send("❌ Erro ao processar imagem.")
    finally:
        for p in (i_path, o_path):
            if os.path.exists(p): os.remove(p)

@bot.tree.command(name="regras", description="Exibe as leis fundamentais da Celestial Trindade (Servidor e Jogo)")
async def regras(interaction: discord.Interaction):
    link_logo = "https://tr.rbxcdn.com/180DAY-8a0ac9f112f6761f919be4fe156a9cb5/420/420/Image/Webp/noFilter"
    
    # --- EMBED 1: REGRAS DO SERVIDOR ---
    embed1 = discord.Embed(
        title="📜 Regras do Servidor - Celestial Trindade",
        description="O descumprimento destas normas resultará em punições imediatas.",
        color=discord.Color.gold()
    )
    embed1.add_field(name="⚖️ Conduta Básica", value="**1.** Respeito mútuo acima de tudo.\n**2.** Proibido qualquer tipo de Discriminação/Racismo/Homofobia.\n**3.** Proibido Spam de mensagens repetitivas.", inline=False)
    embed1.add_field(name="🚫 Proibições", value="**4.** Conteúdo +18 (Pornografia/Gifs) é proibido.\n**5.** Proibido divulgar outros servidores/canais sem permissão.\n**6.** Proibido vazar informações internas da guilda.\n**7.** Proibido mendigar cargo ou promoções.", inline=False)
    embed1.add_field(name="👥 Outros", value="**8.** Evite intrigas por religião ou política.\n**9.** Idade mínima: 13 anos.", inline=False)
    embed1.set_thumbnail(url=link_logo)

    # --- EMBED 2: REGRAS DO JOGO (PEROXIDE) ---
    embed2 = discord.Embed(
        title="⚔️ Regras do Jogo - Peroxide",
        description="Normas de combate e comportamento in-game.",
        color=discord.Color.dark_red()
    )
    embed2.add_field(name="🛡️ Identidade", value="**1.** É obrigatório o uso da Logo da Guilda.\n**2.** Proibido lutar contra membros da guilda sem logo.", inline=False)
    embed2.add_field(name="🚫 Combate e Traição", value="**3.** Proibido Grips/Mortes não justificadas contra membros ou Allys.\n**4.** Proibido deixar aliados morrerem na sua presença.\n**5.** Proibido usar o nome da guilda para causar má reputação.", inline=False)
    embed2.add_field(name="⚠️ Observação", value="A guilda não protege membros que ajudam jogadores sem logo ou de guildas inimigas.", inline=False)

    # --- EMBED 3: SISTEMA DE WARNS ---
    embed3 = discord.Embed(
        title="⚠️ Sistema de Punições (WARNs)",
        description="A contagem de infrações leva à expulsão definitiva.",
        color=discord.Color.red()
    )
    embed3.add_field(name="Fase Inicial", value="`1-2 WARNs`: Advertência verbal e aviso público.", inline=True)
    embed3.add_field(name="Fase Grave", value="`3-4 WARNs`: Suspensão de eventos e rebaixamento.", inline=True)
    embed3.add_field(name="Fase Final", value="`5-6 WARNs`: Última chance e avaliação da liderança.\n`7 WARNs`: **EXPULSÃO IMEDIATA.**", inline=False)
    embed3.set_footer(text="A liderança reserva o direito de punir atos maliciosos não listados.")

    # Enviando tudo de uma vez
    await interaction.response.send_message(embeds=[embed1, embed2, embed3])

@bot.tree.command(name="solicitar", description="Envia uma solicitação para a liderança aceitar seu pedido no grupo do Roblox")
@app_commands.describe(nick_roblox="Seu nome de usuário (Username) no Roblox")
async def solicitar(interaction: discord.Interaction, nick_roblox: str):
    # IDs dos administradores que receberão a DM
    adms_ids = [845105032449884161, 1041870714124382258, 1129212119213146136]
    
    # IDs dos cargos para a menção no canal (os que você já tinha)
    cargos_id = [1395092778614132777, 1458811065583403323, 1425983765053837402, 1467634329214652486]
    mencoes = " ".join([f"<@&{id_cargo}>" for id_cargo in cargos_id])
    
    link_grupo = "https://www.roblox.com/pt/communities/34214394/Celestial-Trindade#!/about"
    
    # Criando o Embed
    embed = discord.Embed(
        title="📝 Nova Solicitação de Entrada",
        description=f"O membro {interaction.user.mention} solicitou aprovação no grupo do Roblox.",
        color=discord.Color.blue()
    )
    embed.add_field(name="👤 Nick no Roblox", value=f"`{nick_roblox}`", inline=True)
    embed.add_field(name="🔗 Perfil", value=f"[Abrir Perfil](https://www.roblox.com/users/profile?username={nick_roblox})", inline=True)
    embed.add_field(name="🛡️ Grupo", value=f"[Verificar Pedidos]({link_grupo})", inline=False)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text="Celestial Trindade - Sistema de Recrutamento")

    # 1. Responde no canal primeiro para confirmar ao usuário
    await interaction.response.send_message(
        content=f"🔔 {mencoes}, novo guerreiro aguardando aprovação!", 
        embed=embed
    )

    # 2. Envio das DMs para os líderes
    for adm_id in adms_ids:
        try:
            admin = await bot.fetch_user(adm_id) # Busca o usuário pelo ID
            if admin:
                # Cria um embed simplificado para a DM ou usa o mesmo
                await admin.send(f"⚠️ **Alerta de Recrutamento:** {interaction.user.name} pediu para entrar no grupo!", embed=embed)
                # Pequena pausa para não ser banido por spam (Rate Limit)
                await asyncio.sleep(1) 
        except Exception as e:
            print(f"❌ Não consegui enviar DM para o ID {adm_id}: {e}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)