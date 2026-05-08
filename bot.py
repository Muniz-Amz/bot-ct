import discord
from discord import app_commands, Interaction
from discord.ext import commands, tasks
import os
import asyncio
import logging
import pymongo
from flask import Flask, jsonify, request
from flask_cors import CORS
from threading import Thread
from datetime import datetime, timezone, timedelta

# =========================
# CONFIGURAÇÕES DE BANCO E LOG
# =========================
logging.basicConfig(level=logging.INFO)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URL = os.getenv("MONGO_URL") # Certifique-se que esta variável está no seu Environment no Render

# Conexão com MongoDB
cluster = pymongo.MongoClient(MONGO_URL)
db = cluster["amz_database"]
collection_limpeza = db["config_limpeza"]
servidores_col = db["servidores_ativos"] # Coleção para gerenciar servidores ativos

CONFIG_LIMPEZA_DINAMICA = {}

# =========================
# FUNÇÕES DE BANCO DE DADOS
# =========================

def registrar_entrada_bot(guild_id, guild_name):
    """Salva no banco que o bot está presente no servidor"""
    servidores_col.update_one(
        {"guild_id": str(guild_id)},
        {"$set": {"nome": guild_name, "ativo": True, "ultima_atualizacao": datetime.now(timezone.utc)}},
        upsert=True
    )

def registrar_saida_bot(guild_id):
    """Remove do banco quando o bot sai do servidor"""
    servidores_col.delete_one({"guild_id": str(guild_id)})

def carregar_configs_banco():
    """Busca as configurações de limpeza no MongoDB"""
    global CONFIG_LIMPEZA_DINAMICA
    try:
        dados = collection_limpeza.find({})
        for item in dados:
            canal_id = int(item["canal_id"])
            dias = int(item["dias"])
            CONFIG_LIMPEZA_DINAMICA[canal_id] = dias
        print(f"📁 [AMZ] {len(CONFIG_LIMPEZA_DINAMICA)} canais de limpeza carregados!")
    except Exception as e:
        print(f"❌ Erro ao acessar o MongoDB: {e}")

# ==========================
# SISTEMA KEEP ALIVE (FLASK)
# ==========================
app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "🛡️ AMZ Bot - Sistema Online!"

# Rota para o site saber onde o bot está
@app.route('/api/bot-servidores', methods=['GET'])
def buscar_servidores_ativos():
    try:
        servidores = servidores_col.find({}, {"guild_id": 1, "_id": 0})
        lista_ids = [s['guild_id'] for s in servidores]
        return jsonify(lista_ids), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/configurar-limpeza', methods=['POST'])
def configurar_limpeza_api():
    global CONFIG_LIMPEZA_DINAMICA
    dados = request.json
    try:
        c_id = int(dados.get('canal_id'))
        dias = int(dados.get('dias'))
        if 1 <= dias <= 7:
            collection_limpeza.update_one({"canal_id": c_id}, {"$set": {"dias": dias}}, upsert=True)
            CONFIG_LIMPEZA_DINAMICA[c_id] = dias
            return jsonify({"status": "sucesso"}), 200
        return jsonify({"status": "erro", "msg": "Use entre 1 e 7 dias"}), 400
    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)}), 400

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()

# =========================
# CONFIGURAÇÃO DO BOT
# =========================
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True          
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# --- EVENTOS DE SINCRONIZAÇÃO DE SERVIDORES ---

@bot.event
async def on_ready():
    carregar_configs_banco() 
    
    # Sincroniza todos os servidores atuais com o banco
    for guild in bot.guilds:
        registrar_entrada_bot(guild.id, guild.name)
    
    if not motor_limpeza_amz.is_running():
        motor_limpeza_amz.start()
        
    print(f"✅ Bot logado como {bot.user}")
    print(f"📡 Monitorando {len(bot.guilds)} servidores.")

@bot.event
async def on_guild_join(guild):
    registrar_entrada_bot(guild.id, guild.name)
    print(f"✅ Novo servidor registrado: {guild.name}")

@bot.event
async def on_guild_remove(guild):
    registrar_saida_bot(guild.id)
    print(f"❌ Bot removido e banco atualizado: {guild.name}")

# --- COMANDOS E TAREFAS (LOOP) ---

@tasks.loop(hours=1)
async def motor_limpeza_amz():
    agora = datetime.now(timezone.utc)
    for canal_id, dias in list(CONFIG_LIMPEZA_DINAMICA.items()):
        canal = bot.get_channel(canal_id)
        if canal:
            try:
                limite = agora - timedelta(days=dias)
                deleted = await canal.purge(before=limite, check=lambda m: not m.pinned)
                if len(deleted) > 0:
                    print(f"🧹 Limpeza: {len(deleted)} mensagens removidas no canal {canal_id}")
            except Exception as e:
                print(f"❌ Erro ao limpar canal {canal_id}: {e}")

# --- COMANDOS SLASH ---

@bot.tree.command(name="ping", description="Verifica a latência do bot")
async def ping(interaction: Interaction):
    await interaction.response.send_message(f"🏓 **Pong!** `{round(bot.latency * 1000)}ms`")

@bot.command()
@commands.has_permissions(administrator=True)
async def deploy(ctx):
    try:
        await bot.tree.sync()
        await ctx.send("✅ Comandos Slash sincronizados!")
    except Exception as e:
        await ctx.send(f"❌ Erro ao sincronizar: {e}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)