import discord
from discord import app_commands, Interaction
from discord.ext import commands
from PIL import Image
import os
import uuid
from flask import Flask
from threading import Thread
import sys
import traceback
import time
import asyncio  # IMPORTANTE: Necessário para não travar o bot

# =========================
# Configurações e Token
# =========================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    print("[ERROR] DISCORD_TOKEN não encontrado nas variáveis de ambiente!")
    # Não vamos dar sys.exit aqui para o Render não ficar reiniciando em loop,
    # mas o bot não vai logar sem token.
else:
    print(f"[INFO] Token detectado: {DISCORD_TOKEN[:5]}***")

# =========================
# Keep Alive Render (Servidor Web)
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot está online e operante!"

def run_flask():
    # O Render define a porta automaticamente na variável PORT
    port = int(os.environ.get("PORT", 8080))
    print(f"[INFO] Servidor web rodando na porta {port}")
    try:
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        print(f"[ERROR] Falha ao iniciar Flask: {e}")

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True # Garante que a thread morra se o programa principal fechar
    t.start()

# Inicia o servidor web imediatamente
keep_alive()

# =========================
# Configuração do Bot
# =========================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# =========================
# Eventos do Bot
# =========================
@bot.event
async def on_ready():
    print(f"✅ Bot logado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"[INFO] {len(synced)} slash commands sincronizados!")
    except Exception as e:
        print(f"[ERROR] Falha ao sincronizar comandos: {e}")

# =========================
# Funções Auxiliares
# =========================
user_cooldowns = {}

def check_cooldown(user_id):
    now = time.time()
    last = user_cooldowns.get(user_id, 0)
    if now - last < 10:  # Reduzi um pouco para teste, pode voltar para 15
        return int(10 - (now - last))
    user_cooldowns[user_id] = now
    return 0

# Função que roda em outra thread para não travar o bot
def converter_imagem_sync(input_path, output_path):
    # O 'with' garante que o arquivo seja fechado e libere memória RAM
    with Image.open(input_path) as img:
        # Otimização opcional: converter para RGB evita erros com PNGs transparentes em alguns casos
        if img.mode == 'P':
            img = img.convert('RGB')
        img.save(output_path, format="GIF", save_all=True, duration=500, loop=0)

# =========================
# Slash Command: /gifct
# =========================
@bot.tree.command(name="gifct", description="Converte PNG/JPG em GIF")
async def gifct(interaction: Interaction, file: discord.Attachment):
    # 1. Verifica Cooldown
    cd = check_cooldown(interaction.user.id)
    if cd > 0:
        await interaction.response.send_message(f"⏳ Aguarde {cd}s antes de usar novamente.", ephemeral=True)
        return

    # 2. Validação básica de arquivo
    filename_lower = file.filename.lower()
    if not filename_lower.endswith((".png", ".jpg", ".jpeg")):
        await interaction.response.send_message("❌ O arquivo precisa ser PNG ou JPG/JPEG.", ephemeral=True)
        return

    # 3. DEFER (O Pulo do Gato)
    # Avisa o Discord que vamos processar algo pesado. Isso evita o erro de "Interaction Failed".
    await interaction.response.defer()

    img_path = None
    gif_path = None

    try:
        # Prepara diretório temporário
        os.makedirs("temp", exist_ok=True)
        file_id = str(uuid.uuid4())
        ext = ".png" if filename_lower.endswith(".png") else ".jpg"
        
        img_path = os.path.join("temp", f"{file_id}{ext}")
        gif_path = os.path.join("temp", f"{file_id}.gif")

        # Salva o arquivo original
        await file.save(img_path)
        print(f"[PROCESSANDO] Imagem salva: {img_path}")

        # 4. Executa a conversão SEM TRAVAR o bot
        # asyncio.to_thread joga a função pesada para fora do loop principal
        await asyncio.to_thread(converter_imagem_sync, img_path, gif_path)
        
        print(f"[SUCESSO] GIF criado: {gif_path}")

        # Envia o resultado (usamos followup porque já demos defer)
        await interaction.followup.send(
            "✅ GIF criado com sucesso:",
            file=discord.File(gif_path)
        )

    except Exception as e:
        print(f"[ERROR] Erro no comando gifct: {e}")
        traceback.print_exc()
        try:
            await interaction.followup.send(f"❌ Ocorreu um erro ao processar sua imagem: {e}")
        except:
            pass

    finally:
        # 5. Limpeza de arquivos
        # Pequeno delay para garantir que o Discord já enviou o arquivo antes de deletar
        await asyncio.sleep(1) 
        for path in (img_path, gif_path):
            try:
                if path and os.path.exists(path):
                    os.remove(path)
                    print(f"[CLEANUP] Removido: {path}")
            except Exception as ex:
                print(f"[WARNING] Falha ao remover {path}: {ex}")

# =========================
# Iniciar Bot
# =========================
if __name__ == "__main__":
    if DISCORD_TOKEN:
        try:
            bot.run(DISCORD_TOKEN)
        except discord.errors.HTTPException as e:
            if e.status == 429:
                print("[FATAL] Rate Limit do Discord atingido (429). O bot foi bloqueado temporariamente.")
                # Render vai tentar reiniciar, mas vai falhar até o bloqueio passar
            else:
                print(f"[FATAL] Erro HTTP: {e}")
        except Exception as e:
            print(f"[FATAL] Erro ao iniciar: {e}")
    else:
        print("[FATAL] Não foi possível iniciar: Token ausente.")