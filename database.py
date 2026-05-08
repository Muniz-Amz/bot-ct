from pymongo import MongoClient
from datetime import datetime

# Substitua pela sua senha real do usuário DreadlordSx
password = "SUA_SENHA_AQUI"
uri = f"mongodb+srv://DreadlordSx:{password}@cluster0.mouyxgd.mongodb.net/?appName=Cluster0"

client = MongoClient(uri)
db = client.amz_studios_db

# Coleções
servidores_col = db.servidores_ativos

def registrar_entrada_bot(guild_id, guild_name):
    servidores_col.update_one(
        {"guild_id": str(guild_id)},
        {"$set": {"nome": guild_name, "ativo": True, "data": datetime.now()}},
        upsert=True
    )

def registrar_saida_bot(guild_id):
    servidores_col.delete_one({"guild_id": str(guild_id)})