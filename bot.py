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
from datetime import datetime, timezone
import aiohttp

# =========================
# CONFIGURAÇÕES DE LOG E TOKEN
# =========================
logging.basicConfig(level=logging.INFO)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ID_CANAL_LOG_AVALIACAO = 1475890030135476387

# Dicionário de Ranks para consulta do Bot
RANKS_PVP = {
    "ARCANJO": 1434373467104481300,
    "SERAFIM": 1299983374047252560,
    "QUERUBIM": 1317543532910612541,
    "DIVINDADE": 1314695358294790244,
    "ANJO": 1317557856077348905,
    "HEREGE": 1434428766435938416
}
# ==========================
# SISTEMA KEEP ALIVE (FLASK)
# ==========================
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

# Travas independentes
agendados_recentemente = set()
avaliados_recentemente = set()

# ------------------------------------------
# MODAL 1: APENAS PARA AGENDAR A LUTA
# ------------------------------------------
class AgendarModal(discord.ui.Modal, title='Agendar Arena'):
    def __init__(self, candidato_id: int):
        super().__init__()
        self.candidato_id = candidato_id

    data_hora = discord.ui.TextInput(
        label='Data e Horário',
        placeholder='Ex: Hoje às 18:00',
        style=discord.TextStyle.short,
        required=True
    )

    codigo_arena = discord.ui.TextInput(
        label='Código da Arena (PS)',
        placeholder='Ex: ARENA-XYZ',
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        ID_DO_SERVIDOR = 1295495463595802765
        guild = interaction.client.get_guild(ID_DO_SERVIDOR)
        
        if not guild:
            return await interaction.response.send_message("❌ Erro: Servidor não encontrado.", ephemeral=True)

        try:
            membro = guild.get_member(self.candidato_id) or await guild.fetch_member(self.candidato_id)
        except:
            return await interaction.response.send_message("❌ Membro não encontrado no servidor.", ephemeral=True)

        # Log de Agendamento
        canal_log = interaction.client.get_channel(ID_CANAL_LOG_AVALIACAO)
        if canal_log:
            embed_log = discord.Embed(title="📅 Log de Agendamento PvP", color=discord.Color.blue(), timestamp=datetime.now())
            embed_log.add_field(name="👤 Candidato", value=f"{membro.mention}", inline=True)
            embed_log.add_field(name="🛡️ Avaliador", value=f"{interaction.user.mention}", inline=True)
            embed_log.add_field(name="⏰ Marcado para", value=f"`{self.data_hora.value}`", inline=False)
            embed_log.add_field(name="🔑 Arena", value=f"`{self.codigo_arena.value}`", inline=False)
            await canal_log.send(embed=embed_log)

        # DM para o Jogador
        try:
            embed_jogador = discord.Embed(title="⚔️ Teste PvP Agendado!", color=discord.Color.blue())
            embed_jogador.description = f"Seu teste foi marcado pelo avaliador {interaction.user.mention}."
            embed_jogador.add_field(name="📅 Horário", value=f"`{self.data_hora.value}`", inline=False)
            embed_jogador.add_field(name="🎮 Arena", value=f"`{self.codigo_arena.value}`", inline=False)
            embed_jogador.set_footer(text="Prepare-se para a batalha!")
            await membro.send(embed=embed_jogador)
            
            agendados_recentemente.add(self.candidato_id)
            await interaction.response.send_message(f"✅ Arena marcada e enviada para {membro.name}.", ephemeral=True)
            
            # Desativa apenas o botão de agendar na DM do avaliador
            if interaction.message:
                view = discord.ui.View.from_message(interaction.message)
                view.children[0].disabled = True # Desativa o 1º botão
                await interaction.message.edit(view=view)
        except:
            await interaction.response.send_message(f"✅ Agendado, mas a DM do membro está fechada.", ephemeral=True)


# ------------------------------------------
# MODAL 2: APENAS PARA DAR O RESULTADO/CARGO
# ------------------------------------------
class ResultadoModal(discord.ui.Modal, title='Definir Resultado'):
    def __init__(self, candidato_id: int):
        super().__init__()
        self.candidato_id = candidato_id

    rank_conquistado = discord.ui.TextInput(
        label='Rank Conquistado',
        placeholder='Ex: Anjo, Serafim, Querubim...',
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        ID_DO_SERVIDOR = 1295495463595802765
        guild = interaction.client.get_guild(ID_DO_SERVIDOR)
        
        try:
            membro = guild.get_member(self.candidato_id) or await guild.fetch_member(self.candidato_id)
        except:
            return await interaction.response.send_message("❌ Membro não encontrado no servidor.", ephemeral=True)

        rank_texto = self.rank_conquistado.value.upper().strip()
        cargo_nome_log = "Rank Inválido"

        if rank_texto in RANKS_PVP:
            id_cargo = RANKS_PVP[rank_texto]
            cargo_obj = guild.get_role(id_cargo)
            if cargo_obj:
                cargos_atuais = [guild.get_role(rid) for rname, rid in RANKS_PVP.items() if guild.get_role(rid) in membro.roles]
                if cargos_atuais:
                    await membro.remove_roles(*cargos_atuais)
                await membro.add_roles(cargo_obj)
                cargo_nome_log = cargo_obj.name
        else:
            return await interaction.response.send_message("❌ Nome de Rank não reconhecido. Use: Anjo, Serafim, etc.", ephemeral=True)

        # Log Final
        canal_log = interaction.client.get_channel(ID_CANAL_LOG_AVALIACAO)
        if canal_log:
            embed_log = discord.Embed(title="🏆 Log de Resultado PvP", color=discord.Color.green(), timestamp=datetime.now())
            embed_log.add_field(name="👤 Jogador", value=f"{membro.mention}", inline=True)
            embed_log.add_field(name="🛡️ Avaliado por", value=f"{interaction.user.mention}", inline=True)
            embed_log.add_field(name="📈 Novo Rank", value=f"**{cargo_nome_log}**", inline=False)
            await canal_log.send(embed=embed_log)

        # DM Final para o Jogador
        try:
            embed_jogador = discord.Embed(title="🏆 Resultado da Avaliação PvP", color=discord.Color.green())
            embed_jogador.description = f"Parabéns! O avaliador {interaction.user.mention} definiu seu novo rank."
            embed_jogador.add_field(name="🏅 Rank Conquistado", value=f"**{cargo_nome_log}**", inline=False)
            await membro.send(embed=embed_jogador)
            
            avaliados_recentemente.add(self.candidato_id)
            await interaction.response.send_message(f"✅ Sucesso! O jogador subiu para {cargo_nome_log}.", ephemeral=True)
            
            # Desativa o botão de resultado
            if interaction.message:
                view = discord.ui.View.from_message(interaction.message)
                view.children[1].disabled = True # Desativa o 2º botão
                await interaction.message.edit(view=view)
        except:
            await interaction.response.send_message(f"✅ Rank atualizado no servidor, mas a DM do membro está fechada.", ephemeral=True)

# ------------------------------------------
# A VIEW COM OS DOIS BOTÕES
# ------------------------------------------
class AvaliacaoView(discord.ui.View):
    def __init__(self, candidato_id: int):
        super().__init__(timeout=None)
        self.candidato_id = candidato_id

    @discord.ui.button(label="📅 1. Agendar Arena", style=discord.ButtonStyle.primary, custom_id="btn_agendar")
    async def agendar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.candidato_id in agendados_recentemente:
            return await interaction.response.send_message("⚠️ Outro avaliador já agendou esta luta!", ephemeral=True)
        await interaction.response.send_modal(AgendarModal(candidato_id=self.candidato_id))

    @discord.ui.button(label="🏆 2. Definir Resultado", style=discord.ButtonStyle.success, custom_id="btn_resultado")
    async def resultado(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.candidato_id in avaliados_recentemente:
            return await interaction.response.send_message("⚠️ O resultado deste jogador já foi registrado!", ephemeral=True)
        await interaction.response.send_modal(ResultadoModal(candidato_id=self.candidato_id))

# =========================
# Botão Do Rejeitar
# =========================
class SolicitacaoView(discord.ui.View):
    def __init__(self, candidato_id: int):
        super().__init__(timeout=None) # Não expira sozinho
        self.candidato_id = candidato_id

    # Função auxiliar para desativar os botões após alguém clicar
    async def desativar_botoes(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

    # BOTÃO 1: ACEITAR
    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.success, custom_id="btn_aceitar")
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.desativar_botoes(interaction)
        
        candidato = interaction.client.get_user(self.candidato_id) or await interaction.client.fetch_user(self.candidato_id)
        if candidato:
            try:
                await candidato.send("🎉 **Parabéns!** Sua solicitação para entrar na **Celestial Trindade** foi **ACEITA**! Seja muito bem-vindo à guilda.")
            except discord.Forbidden:
                pass
        
        await interaction.followup.send("✅ Você aceitou o membro. Aviso enviado!", ephemeral=True)

    # BOTÃO 2: RECUSAR
    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger, custom_id="btn_recusar")
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.desativar_botoes(interaction)
        
        candidato = interaction.client.get_user(self.candidato_id) or await interaction.client.fetch_user(self.candidato_id)
        if candidato:
            try:
                await candidato.send("❌ **Aviso:** Sua solicitação para a **Celestial Trindade** foi **RECUSADA** pelos líderes no momento.")
            except discord.Forbidden:
                pass
        
        await interaction.followup.send("❌ Você recusou o membro. Aviso enviado!", ephemeral=True)

    # BOTÃO 3: FALTOU PEDIDO NO ROBLOX
    @discord.ui.button(label="⚠️ Faltou Pedido", style=discord.ButtonStyle.secondary, custom_id="btn_faltou")
    async def faltou_pedido(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.desativar_botoes(interaction)
        
        candidato = interaction.client.get_user(self.candidato_id) or await interaction.client.fetch_user(self.candidato_id)
        if candidato:
            try:
                link_grupo = "https://www.roblox.com/pt/communities/34214394/Celestial-Trindade#!/about"
                await candidato.send(f"⚠️ **Atenção:** Os líderes verificaram, mas **você ainda não enviou o pedido no grupo do Roblox**.\nPor favor, entre no link, clique em 'Join Group' (Entrar no Grupo) e faça o comando `/solicitar` novamente no servidor.\n🔗 {link_grupo}")
            except discord.Forbidden:
                pass
        
        await interaction.followup.send("⚠️ Você avisou que ele não fez o pedido no Roblox.", ephemeral=True)
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
async def on_member_join(member):
    # Calcula a idade da conta
    agora = datetime.now(timezone.utc)
    idade_conta = agora - member.created_at

    # Se a conta tiver menos de 7 dias (7 dias * 24h * 3600s)
    if idade_conta.total_seconds() < 604800:
        try:
            await member.send("🛡️ **Celestial Trindade:** Sua conta é muito recente. Para evitar fakes, só aceitamos contas com mais de 7 dias.")
            await member.kick(reason="Conta muito nova (possível alt/fake).")
        except:
            pass
        
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

# =========================
# COMANDO: ALLY COM CACHE BREAK (FIXED)
# =========================
@bot.tree.command(name="ally", description="Exibe a logo atualizada de uma guilda aliada")
@app_commands.describe(nome="Nome da guilda aliada", id_grupo="O ID numérico do grupo no Roblox")
async def ally(interaction: discord.Interaction, nome: str, id_grupo: str):
    # Defer evita o erro "Unknown Interaction" (404/10062)
    await interaction.response.defer() 

    link_grupo = f"https://www.roblox.com/communities/{id_grupo}"
    api_url = f"https://thumbnails.roblox.com/v1/groups/icons?groupIds={id_grupo}&size=420x420&format=Png&isCircular=false"
    
    logo_final = None
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                if data['data']:
                    # ?t= força o Discord a ignorar o cache da imagem antiga
                    logo_final = f"{data['data'][0]['imageUrl']}?t={int(time.time())}"

    embed = discord.Embed(
        title=f"🤝 Aliança: {nome}",
        description=f"**Celestial Trindade** caminha junto a **{nome}**.\n\n[Clique aqui para visitar o grupo]({link_grupo})",
        color=discord.Color.blue()
    )
    if logo_final: embed.set_image(url=logo_final)
    embed.set_footer(text="Celestial Trindade - Diplomacia")

    # Followup é obrigatório após o defer
    await interaction.followup.send(embed=embed)
    
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
    embed2.add_field(name="🚫 Combate e Traição", value="**3.** Proibido Grips/Mortes não justificadas contra membros ou Allys.\n**4.** Proibido deixar aliados morrerem na sua presença.\n**5.** Proibido usar o nome da guilda para causar má reputação. \n**6.** Proibido tentar Burlar as Regras (Má Fé)", inline=False)
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

# =========================
# SISTEMA DE BOTÕES (DMs DOS LÍDERES)
# =========================
class SolicitacaoView(discord.ui.View):
    def __init__(self, candidato_id: int):
        super().__init__(timeout=None)
        self.candidato_id = candidato_id

    async def desativar_botoes(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.success, custom_id="btn_aceitar")
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.desativar_botoes(interaction)
        candidato = interaction.client.get_user(self.candidato_id) or await interaction.client.fetch_user(self.candidato_id)
        if candidato:
            try:
                await candidato.send("🎉 **Parabéns!** Sua solicitação para entrar na **Celestial Trindade** foi **ACEITA**! Seja muito bem-vindo à guilda.")
            except: pass
        await interaction.followup.send("✅ Você aceitou o membro. Mensagem enviada!", ephemeral=True)

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger, custom_id="btn_recusar")
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.desativar_botoes(interaction)
        candidato = interaction.client.get_user(self.candidato_id) or await interaction.client.fetch_user(self.candidato_id)
        if candidato:
            try:
                await candidato.send("❌ **Aviso:** Sua solicitação para a **Celestial Trindade** foi **RECUSADA** pelos líderes no momento.")
            except: pass
        await interaction.followup.send("❌ Você recusou o membro. Mensagem enviada!", ephemeral=True)

    @discord.ui.button(label="⚠️ Faltou Pedido", style=discord.ButtonStyle.secondary, custom_id="btn_faltou")
    async def faltou_pedido(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.desativar_botoes(interaction)
        candidato = interaction.client.get_user(self.candidato_id) or await interaction.client.fetch_user(self.candidato_id)
        if candidato:
            try:
                link_grupo = "https://www.roblox.com/pt/communities/34214394/Celestial-Trindade#!/about"
                await candidato.send(f"⚠️ **Atenção:** Os líderes verificaram, mas **você ainda não enviou o pedido no grupo do Roblox**.\nPor favor, entre no link, clique em 'Join Group' e faça o comando `/solicitar` novamente.\n🔗 {link_grupo}")
            except: pass
        await interaction.followup.send("⚠️ Você avisou que ele não fez o pedido. Mensagem enviada!", ephemeral=True)

# =========================
# COMANDO /AVALIACAO
# =========================
@bot.tree.command(name="avaliacao", description="Solicita um teste de PvP")
async def avaliacao(interaction: discord.Interaction):
    # Defer com ephemeral=True para que apenas o jogador veja a confirmação
    await interaction.response.defer(ephemeral=True)

    # Lista de IDs dos seus avaliadores
    avaliadores_ids = [1129212119213146136, 1017444684022427738, 1277257295616540775]
    
    embed_aviso = discord.Embed(
        title="⚔️ Solicitação de Avaliação",
        description=f"O membro {interaction.user.mention} (`{interaction.user.name}`) deseja um teste de PvP.",
        color=discord.Color.gold()
    )
    embed_aviso.set_thumbnail(url=interaction.user.display_avatar.url)
    embed_aviso.set_footer(text="Clique no botão abaixo para agendar a arena ou definir o Rank.")

    sucesso = False
    for aval_id in avaliadores_ids:
        try:
            # Usamos fetch_user para garantir que o bot encontre o avaliador mesmo fora do cache
            avaliador = await bot.fetch_user(aval_id)
            if avaliador:
                # Criamos a View passando o ID do candidato
                view = AvaliacaoView(candidato_id=interaction.user.id)
                await avaliador.send(embed=embed_aviso, view=view)
                sucesso = True
                # Pequena pausa para não ser bloqueado pelo Discord (Rate Limit)
                await asyncio.sleep(0.3) 
        except Exception as e:
            print(f"Erro ao enviar para {aval_id}: {e}")
            continue

    if sucesso:
        await interaction.followup.send("✅ Sua solicitação foi enviada aos Avaliadores! Aguarde o retorno na sua DM.", ephemeral=True)
    else:
        await interaction.followup.send("❌ Não foi possível avisar os avaliadores. Verifique se as DMs deles estão abertas.", ephemeral=True)

# =========================
# COMANDO /SOLICITAR
# =========================
@bot.tree.command(name="solicitar", description="Pede aprovação no grupo do Roblox")
@app_commands.describe(nick_roblox="Seu nome de usuário (Username) no Roblox")
async def solicitar(interaction: discord.Interaction, nick_roblox: str):
    # Avisa o Discord que vai demorar (evita o bot cair no Render)
    await interaction.response.defer()

    adms_ids = [845105032449884161, 1129212119213146136, 1017444684022427738]
    cargos_id = [1395092778614132777]
    mencoes = " ".join([f"<@&{id_cargo}>" for id_cargo in cargos_id])
    link_grupo = "https://www.roblox.com/pt/communities/34214394/Celestial-Trindade#!/about"
    
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

    # Manda a mensagem pública no servidor
    await interaction.followup.send(
        content=f"🔔 {mencoes}, novo guerreiro aguardando aprovação!\n*A liderança já recebeu o painel de aprovação.*", 
        embed=embed
    )

    # Manda as DMs para os líderes COM OS BOTÕES
    for adm_id in adms_ids:
        try:
            admin = await bot.fetch_user(adm_id)
            if admin:
                view = SolicitacaoView(candidato_id=interaction.user.id)
                await admin.send(f"⚠️ **Ação Necessária:** {interaction.user.name} quer entrar na guilda. Escolha uma opção:", embed=embed, view=view)
                await asyncio.sleep(0.5) 
        except Exception as e:
            print(f"❌ Não consegui enviar DM para o admin {adm_id}: {e}")

# =========================
# COMANDOS ADMINISTRATIVOS
# =========================

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