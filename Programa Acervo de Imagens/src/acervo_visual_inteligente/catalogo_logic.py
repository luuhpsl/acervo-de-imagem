import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import hashlib
import json
import time
import requests
import webbrowser
import uuid
import secrets
from datetime import datetime
from auth_server import iniciar_servidor
import base64
import re
import unicodedata
from PIL import Image, ImageOps
import imagehash
import openpyxl
from openpyxl import Workbook
import subprocess

try:
    from env_config import load_local_env
    load_local_env()
except Exception:
    pass

# ============================================================
# CONFIGURAÃ‡Ã•ES
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
PENDING_METADATA_DIR = os.path.join(
    "V:\\",
    "Producao_de_Materiais",
    "02_\u00c1reas",
    "05_Design editorial",
    "Lucas",
    "PROGRAMA_ACERVO"
)
PENDING_METADATA_FILE = os.path.join(PENDING_METADATA_DIR, "pending_metadata.json")
PENDING_METADATA_FALLBACK_DIR = os.path.join(os.path.expanduser("~"), "Documents", "PROGRAMA_ACERVO")
PENDING_METADATA_FALLBACK_FILE = os.path.join(PENDING_METADATA_FALLBACK_DIR, "pending_metadata.json")
PROCESSING_QUEUE_FILE = os.path.join(PENDING_METADATA_DIR, "processing_queue.json")
PROCESSING_QUEUE_FALLBACK_FILE = os.path.join(PENDING_METADATA_FALLBACK_DIR, "processing_queue.json")
PROJECT_ID = "uniasselvi-digital"
FIREBASE_API_KEY = "AIzaSyBD6TkUg5F_j9C2_VK6pWf-z34Iyszp0LE"
STORAGE_BUCKET = "uniasselvi-digital.appspot.com"

# Chave OpenAI: configure em .env.local ou como variavel de ambiente.
# Nunca deixe a chave real hardcoded no codigo, pois este arquivo vai para o GitHub.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Caminhos no Firestore
COLLECTION_PATH = "acervo-visual-unificado"

# Prefixos aceitos
PREFIXOS_ACEITOS = ('shutterstock_', 'envato-', 'pexels', 'freestock')

# ExtensÃµes permitidas (incluindo EPS e AI)
EXTENSOES_PERMITIDAS = ('.jpg', '.jpeg', '.png', '.ai', '.eps', '.svg')
EXTENSOES_VETORIAIS = ('.eps', '.ai', '.svg')
LARGE_MAX_SIZE = (2400, 2400)
MEDIUM_MAX_SIZE = (1600, 1600)
THUMBNAIL_MAX_SIZE = (400, 400)
VECTOR_PREVIEW_MAX_SIZE = (2000, 2000)
VECTOR_PREVIEW_DENSITY = 96
DISPLAY_FILE_LIMIT = 1000
LOG_MAX_LINES = 500
QUEUE_CHECKPOINT_INTERVAL = 10
CODIGO_ACERVO_PREFIXO = "ACV"
CODIGO_ACERVO_TAMANHO_ALEATORIO = 6
CODIGO_ACERVO_ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODIGOS_ACERVO_GERADOS = set()

OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"

# ============================================================
# INTERFACE GRÃFICA
# ============================================================
janela = tk.Tk()
janela.title("CatÃ¡logo Inteligente de Imagens v2.2")
janela.geometry("950x700")

lista_arquivos = tk.Listbox(janela, width=100, height=8)
lista_arquivos.pack(pady=5)

frame_metricas = tk.Frame(janela)
frame_metricas.pack(pady=5)
lbl_encontrados = tk.Label(frame_metricas, text="Encontrados: 0")
lbl_encontrados.pack(side='left', padx=10)
lbl_processados = tk.Label(frame_metricas, text="Processados: 0")
lbl_processados.pack(side='left', padx=10)
lbl_duplicados = tk.Label(frame_metricas, text="Duplicados: 0")
lbl_duplicados.pack(side='left', padx=10)
lbl_erros = tk.Label(frame_metricas, text="Erros: 0")
lbl_erros.pack(side='left', padx=10)

progresso = ttk.Progressbar(janela, orient='horizontal', length=800, mode='determinate')
progresso.pack(pady=5)

log_texto = scrolledtext.ScrolledText(janela, width=100, height=15, state='disabled', wrap=tk.CHAR)
log_texto.pack(pady=5)

# VariÃ¡veis globais
arquivos_encontrados = []
token_usuario = None
email_usuario = None
ultimo_erro_openai = None
linha_log_varredura = None
PAUSADO = False
PAUSA_LOGADA = False
PARAR_PROCESSAMENTO = False
mostrar_resultado_processamento = None
COR_VARIACAO_CACHE = {}

# ============================================================
# FUNÃ‡Ã•ES AUXILIARES
# ============================================================
def log(mensagem):
    estava_no_fim = log_texto.yview()[1] >= 0.98
    log_texto.config(state='normal')
    log_texto.insert(tk.END, mensagem + '\n')
    linhas = int(log_texto.index('end-1c').split('.')[0])
    if linhas > LOG_MAX_LINES:
        log_texto.delete('1.0', f'{linhas - LOG_MAX_LINES}.0')
    if estava_no_fim:
        log_texto.see(tk.END)
    log_texto.config(state='disabled')
    janela.update_idletasks()

def atualizar_log_varredura(percentual=None):
    global linha_log_varredura
    if percentual is None:
        mensagem = "Varredura: preparando..."
    else:
        percentual = max(0, min(100, int(percentual)))
        largura = 30
        preenchido = int((percentual / 100) * largura)
        barra = "#" * preenchido + "-" * (largura - preenchido)
        mensagem = f"Varredura: [{barra}] {percentual:3d}%"

    log_texto.config(state='normal')
    if linha_log_varredura is None:
        log_texto.insert(tk.END, mensagem + '\n')
        linha_log_varredura = log_texto.index("end-2l linestart")
    else:
        try:
            log_texto.delete(linha_log_varredura, f"{linha_log_varredura} lineend")
            log_texto.insert(linha_log_varredura, mensagem)
        except tk.TclError:
            linha_log_varredura = None
            log_texto.insert(tk.END, mensagem + '\n')
            linha_log_varredura = log_texto.index("end-2l linestart")
    if log_texto.yview()[1] >= 0.98:
        log_texto.see(tk.END)
    log_texto.config(state='disabled')
    janela.update_idletasks()

def atualizar_metricas(encontrados, processados, duplicados, erros, progresso_valor=None):
    lbl_encontrados.config(text=f"Encontrados: {formatar_numero(encontrados)}")
    lbl_processados.config(text=f"Processados: {formatar_numero(processados)}")
    lbl_duplicados.config(text=f"Duplicados: {formatar_numero(duplicados)}")
    lbl_erros.config(text=f"Erros: {formatar_numero(erros)}")
    if progresso_valor is not None:
        progresso['value'] = progresso_valor
    janela.update_idletasks()

# ============================================================
# CONVERSÃƒO EPS/AI PARA JPG (ImageMagick + Ghostscript)
# ============================================================
def converter_para_jpg(entrada, saida, densidade=VECTOR_PREVIEW_DENSITY, qualidade=88, tamanho_maximo=VECTOR_PREVIEW_MAX_SIZE):
    """
    Converte EPS, AI ou SVG para JPG usando ImageMagick.
    Seleciona apenas o primeiro frame ([0]) para evitar duplicatas e limita
    a imagem gerada para impedir JPGs temporarios gigantes.
    """
    if not os.path.exists(entrada):
        log(f"âŒ Arquivo de entrada nÃ£o encontrado: {entrada}")
        return False

    # Verifica qual comando estÃ¡ disponÃ­vel (magick ou convert)
    try:
        subprocess.run(['magick', '-version'], check=True, capture_output=True)
        comando_base = 'magick'
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(['convert', '-version'], check=True, capture_output=True)
            comando_base = 'convert'
        except (subprocess.CalledProcessError, FileNotFoundError):
            log("âŒ ImageMagick nÃ£o encontrado. Instale e tente novamente.")
            return False

    # Adiciona [0] para pegar apenas o primeiro frame
    entrada_com_frame = entrada + "[0]"
    largura_maxima, altura_maxima = tamanho_maximo
    resize_arg = f"{largura_maxima}x{altura_maxima}>"
    if comando_base == 'magick':
        cmd = ['magick']
    else:
        cmd = ['convert']

    cmd.extend([
        '-density', str(densidade),
        entrada_com_frame,
        '-background', 'white',
        '-alpha', 'remove',
        '-alpha', 'off',
        '-flatten',
        '-trim',
        '+repage',
        '-resize', resize_arg,
        '-strip',
        '-quality', str(qualidade),
        saida
    ])

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        log(f"   JPG de preview criado em {obter_resolucao(saida)} (limite {largura_maxima}x{altura_maxima}).")
        return True
    except subprocess.CalledProcessError as e:
        log(f"   âŒ Erro na conversÃ£o: {e.stderr}")
        return False

# ============================================================
# AUTENTICAÃ‡ÃƒO (FIREBASE)
# ============================================================
def criar_jpg_otimizado(entrada, saida, tamanho_maximo, qualidade=85):
    try:
        with Image.open(entrada) as img:
            img = ImageOps.exif_transpose(img)
            resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
            img.thumbnail(tamanho_maximo, resample)
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                fundo = Image.new("RGB", img.size, "white")
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                fundo.paste(img, mask=img.getchannel("A"))
                img = fundo
            elif img.mode != "RGB":
                img = img.convert("RGB")
            img.save(saida, "JPEG", quality=qualidade, optimize=True, progressive=True)
        return True
    except Exception as e:
        log(f"   Erro ao criar JPG otimizado: {str(e)}")
        return False

def obter_informacoes_usuario(token):
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_API_KEY}"
        response = requests.post(url, json={"idToken": token})
        if response.status_code == 200:
            dados = response.json()
            user = dados['users'][0]
            email = user.get('email') or ''
            if not email:
                for provider in user.get('providerUserInfo', []):
                    email = provider.get('email') or provider.get('rawId') or ''
                    if email:
                        break
            email = email or 'desconhecido'
            verified = user.get('emailVerified', False)
            return email, verified
        else:
            return None, False
    except Exception:
        return None, False

def obter_token():
    global token_usuario, email_usuario
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
                token_usuario = data.get('token')
                if token_usuario:
                    log("âœ… Token encontrado. Autenticando...")
                    email, verified = obter_informacoes_usuario(token_usuario)
                    if email:
                        email_usuario = email
                        log(f"ðŸ‘¤ UsuÃ¡rio: {email} (verificado: {verified})")
                        if not verified:
                            log("âš ï¸ ATENÃ‡ÃƒO: Email nÃ£o verificado. As regras exigem verificaÃ§Ã£o.")
                        return token_usuario
                    else:
                        log("âš ï¸ Token invÃ¡lido. SerÃ¡ solicitado novo login.")
                        token_usuario = None
        except Exception as e:
            log(f"âš ï¸ Erro ao ler token: {str(e)}")
            token_usuario = None

    log("ðŸ”‘ Abrindo navegador para login...")
    iniciar_servidor()
    webbrowser.open('http://localhost:5000')
    for _ in range(60):
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r') as f:
                    data = json.load(f)
                    token_usuario = data.get('token')
                    if token_usuario:
                        email, verified = obter_informacoes_usuario(token_usuario)
                        if email:
                            email_usuario = email
                            log(f"ðŸ‘¤ UsuÃ¡rio: {email} (verificado: {verified})")
                            return token_usuario
            except Exception:
                pass
        time.sleep(1)
    messagebox.showerror("Erro", "Tempo limite para login.")
    return None

# ============================================================
# FUNÃ‡Ã•ES FIRESTORE E STORAGE
# ============================================================
def consultar_hash_no_firestore(hash_sha256):
    if not token_usuario:
        return None
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents:runQuery"
    headers = {"Authorization": f"Bearer {token_usuario}", "Content-Type": "application/json"}
    body = {
        "structuredQuery": {
            "from": [{"collectionId": COLLECTION_PATH}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "sha256"},
                    "op": "EQUAL",
                    "value": {"stringValue": hash_sha256}
                }
            },
            "limit": 1
        }
    }
    try:
        response = requests.post(url, headers=headers, json=body)
        if response.status_code == 200:
            dados = response.json()
            if dados and len(dados) > 0 and 'document' in dados[0]:
                return dados[0]['document']
        return None
    except Exception:
        return None

def consultar_phash_similar(phash_str, limite_distancia=5):
    if not token_usuario:
        return None
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{COLLECTION_PATH}"
    headers = {"Authorization": f"Bearer {token_usuario}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None
        dados = response.json()
        documentos = dados.get('documents', [])
        phash_atual = imagehash.hex_to_hash(phash_str)
        for doc in documentos:
            campos = doc.get('fields', {})
            if 'phash' in campos:
                phash_doc = campos['phash'].get('stringValue')
                if phash_doc:
                    try:
                        phash_doc_hash = imagehash.hex_to_hash(phash_doc)
                        distancia = phash_atual - phash_doc_hash
                        if distancia <= limite_distancia:
                            log(f"   ðŸ” Similaridade visual (distÃ¢ncia: {distancia})")
                            return doc
                    except:
                        pass
        return None
    except Exception:
        return None

def gerar_codigo_acervo(ano):
    ano_curto = str(ano or datetime.now().year)[-2:]
    for _ in range(100):
        sufixo = ''.join(secrets.choice(CODIGO_ACERVO_ALFABETO) for _ in range(CODIGO_ACERVO_TAMANHO_ALEATORIO))
        codigo = f"{CODIGO_ACERVO_PREFIXO}{ano_curto}{sufixo}"
        if codigo not in CODIGOS_ACERVO_GERADOS:
            CODIGOS_ACERVO_GERADOS.add(codigo)
            return codigo
    sufixo_fallback = uuid.uuid4().hex[:CODIGO_ACERVO_TAMANHO_ALEATORIO].upper()
    codigo = f"{CODIGO_ACERVO_PREFIXO}{ano_curto}{sufixo_fallback}"
    CODIGOS_ACERVO_GERADOS.add(codigo)
    return codigo

def fazer_upload_imagem(caminho_local, destino):
    url = f"https://firebasestorage.googleapis.com/v0/b/{STORAGE_BUCKET}/o?uploadType=media&name={destino}"
    headers = {"Authorization": f"Bearer {token_usuario}", "Content-Type": "application/octet-stream"}
    try:
        with open(caminho_local, 'rb') as f:
            response = requests.post(url, headers=headers, data=f)
        if response.status_code == 200:
            url_publica = f"https://firebasestorage.googleapis.com/v0/b/{STORAGE_BUCKET}/o/{destino.replace('/', '%2F')}?alt=media"
            return url_publica
        else:
            log(f"   âŒ Upload falhou: {response.status_code}")
            return None
    except Exception as e:
        log(f"   âŒ ExceÃ§Ã£o no upload: {str(e)}")
        return None

def converter_valor_firestore(value):
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    if isinstance(value, int):
        return {"integerValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, list):
        valores = [converter_valor_firestore(v) for v in value]
        return {"arrayValue": {"values": valores}} if valores else {"arrayValue": {}}
    if isinstance(value, dict):
        return {"mapValue": {"fields": {k: converter_valor_firestore(v) for k, v in value.items()}}}
    if value is None:
        return {"nullValue": None}
    return {"stringValue": str(value)}

def gravar_no_firestore(dados, doc_id):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{COLLECTION_PATH}?documentId={doc_id}"
    headers = {
        "Authorization": f"Bearer {token_usuario}",
        "Content-Type": "application/json"
    }
    fields = {key: converter_valor_firestore(value) for key, value in dados.items()}
    body = {"fields": fields}
    try:
        response = requests.post(url, headers=headers, json=body)
        if response.status_code in (200, 201):
            log(f"   ðŸ’¾ Dados salvos no Firestore (ID: {doc_id})")
            return True
        else:
            log(f"   âŒ Erro ao salvar no Firestore: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log(f"   âŒ ExceÃ§Ã£o ao salvar no Firestore: {str(e)}")
        return False

# ============================================================
# FUNÃ‡ÃƒO PARA DELETAR ARQUIVO DO STORAGE
# ============================================================
def deletar_arquivo_storage(caminho_completo):
    """Deleta um arquivo do Firebase Storage usando a API REST."""
    url = f"https://firebasestorage.googleapis.com/v0/b/{STORAGE_BUCKET}/o/{caminho_completo.replace('/', '%2F')}"
    headers = {"Authorization": f"Bearer {token_usuario}"}
    try:
        response = requests.delete(url, headers=headers)
        if response.status_code in (200, 204):
            return True
        else:
            log(f"   âŒ Erro ao deletar {caminho_completo}: {response.status_code}")
            return False
    except Exception as e:
        log(f"   âŒ ExceÃ§Ã£o ao deletar {caminho_completo}: {str(e)}")
        return False

def obter_id_documento_firestore(doc):
    nome_doc = doc.get("name", "") if isinstance(doc, dict) else ""
    return nome_doc.split("/")[-1] if nome_doc else ""

def obter_caminhos_storage_documento(doc):
    caminhos = []
    for campo in ("storage_original", "storage_medium", "storage_visualizacao", "storage_thumbnail", "storage_thumb"):
        caminho = obter_string_firestore(doc, campo)
        if caminho and caminho not in caminhos:
            caminhos.append(caminho)

    doc_id = obter_id_documento_firestore(doc)
    extensao = obter_extensao_firestore(doc)
    if doc_id and extensao:
        pasta = f"acervo-visual-unificado/{doc_id}"
        pasta_legacy = f"acervo-visual-unificado/assets/{doc_id}"
        asset_code = obter_string_firestore(doc, "asset_code") or obter_string_firestore(doc, "codigo") or obter_string_firestore(doc, "nome_amigavel") or doc_id
        caminhos_novos = [
            f"{pasta}/{doc_id}_original.{extensao}",
            f"{pasta}/{doc_id}_large.jpg",
            f"{pasta}/{doc_id}_medium.jpg",
            f"{pasta}/{doc_id}_thumb.jpg",
            f"{pasta_legacy}/{asset_code}_original.{extensao}",
            f"{pasta_legacy}/{asset_code}_large.jpg",
            f"{pasta_legacy}/{asset_code}_medium.jpg",
            f"{pasta_legacy}/{asset_code}_thumb.jpg",
        ]
        for caminho in caminhos_novos:
            if caminho not in caminhos:
                caminhos.append(caminho)
    return caminhos

def deletar_documento_firestore_por_doc(doc):
    nome_doc = doc.get("name", "") if isinstance(doc, dict) else ""
    if not nome_doc:
        return False
    url = f"https://firestore.googleapis.com/v1/{nome_doc}"
    headers = {"Authorization": f"Bearer {token_usuario}"}
    try:
        response = requests.delete(url, headers=headers)
        if response.status_code in (200, 204):
            return True
        log(f"   Erro ao excluir documento repetido do Firestore: {response.status_code}")
        return False
    except Exception as e:
        log(f"   Excecao ao excluir documento repetido do Firestore: {str(e)}")
        return False

def excluir_registro_repetido_substituido(doc, motivo):
    doc_id = obter_id_documento_firestore(doc)
    log(f"   Removendo repetido substituido ({doc_id}): {motivo}.")
    for caminho_storage in obter_caminhos_storage_documento(doc):
        deletar_arquivo_storage(caminho_storage)
    if deletar_documento_firestore_por_doc(doc):
        log("   Registro repetido removido do Firestore.")

# ============================================================
# LIMPEZA DE REGISTROS SHUTTERSTOCK
# ============================================================
def limpar_shutterstock():
    """Remove todos os registros e arquivos relacionados Ã  origem 'shutterstock'."""
    if not token_usuario:
        messagebox.showerror("Erro", "VocÃª precisa estar autenticado.")
        return

    log("ðŸ” Buscando documentos Shutterstock no Firestore...")
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{COLLECTION_PATH}"
    headers = {"Authorization": f"Bearer {token_usuario}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            log(f"âŒ Erro ao buscar documentos: {response.status_code}")
            return
        dados = response.json()
        documentos = dados.get('documents', [])
        docs_para_excluir = []
        for doc in documentos:
            campos = doc.get('fields', {})
            origem = campos.get('origem', {}).get('stringValue', '')
            if origem.lower() == 'shutterstock':
                doc_id = doc['name'].split('/')[-1]
                nome_amigavel = campos.get('nome_amigavel', {}).get('stringValue', '')
                ano = campos.get('data_processamento', {}).get('stringValue', '')
                if ano:
                    ano = ano[:4]
                else:
                    ano = '2026'
                extensao = campos.get('extensao', {}).get('stringValue', '.jpg')
                tipo_arquivo_original = campos.get('tipo_arquivo_original', {}).get('stringValue', detectar_tipo_arquivo_original(extensao))
                docs_para_excluir.append({
                    'id': doc_id,
                    'nome_amigavel': nome_amigavel,
                    'ano': ano,
                    'extensao': extensao,
                    'tipo_arquivo_original': tipo_arquivo_original
                })
    except Exception as e:
        log(f"âŒ Erro ao consultar Firestore: {str(e)}")
        return

    if not docs_para_excluir:
        log("âœ… Nenhum documento Shutterstock encontrado. Nada a fazer.")
        return

    resposta = messagebox.askyesno(
        "ConfirmaÃ§Ã£o",
        f"VocÃª estÃ¡ prestes a excluir {len(docs_para_excluir)} documentos e seus arquivos do Storage.\n\nEsta aÃ§Ã£o Ã© irreversÃ­vel. Deseja continuar?"
    )
    if not resposta:
        log("âŒ OperaÃ§Ã£o cancelada pelo usuÃ¡rio.")
        return

    log(f"ðŸ—‘ï¸ Iniciando exclusÃ£o de {len(docs_para_excluir)} documentos Shutterstock...")
    deletados = 0
    erros = 0

    for doc in docs_para_excluir:
        doc_id = doc['id']
        nome_amigavel = doc['nome_amigavel']
        ano = doc['ano']
        extensao = doc['extensao']
        tipo_arquivo_original = doc['tipo_arquivo_original']

        # 1. Excluir documento do Firestore
        url_del_firestore = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{COLLECTION_PATH}/{doc_id}"
        try:
            resp_fire = requests.delete(url_del_firestore, headers=headers)
            if resp_fire.status_code not in (200, 204):
                log(f"   âŒ Erro ao excluir documento {doc_id}: {resp_fire.status_code}")
                erros += 1
                continue
        except Exception as e:
            log(f"   âŒ ExceÃ§Ã£o ao excluir documento {doc_id}: {str(e)}")
            erros += 1
            continue

        # 2. Excluir arquivos do Storage
        caminho_thumbnail = f"acervo-visual-unificado/thumbnails/shutterstock/{ano}/{nome_amigavel}.jpg"
        caminho_original = f"acervo-visual-unificado/originals/{tipo_arquivo_original}/shutterstock/{ano}/{nome_amigavel}{extensao}"

        if False:
            log(f"   âš ï¸ NÃ£o foi possÃ­vel deletar visualizaÃ§Ã£o: {caminho_visualizacao}")
            erros += 1
        else:
            log(f"   âœ… VisualizaÃ§Ã£o removida: {caminho_visualizacao}")

        if not deletar_arquivo_storage(caminho_thumbnail):
            log(f"   Nao foi possivel deletar thumbnail: {caminho_thumbnail}")
            erros += 1
        elif False:
            log(f"   Thumbnail removida: {caminho_thumbnail}")

        if caminho_original:
            if not deletar_arquivo_storage(caminho_original):
                log(f"   âš ï¸ NÃ£o foi possÃ­vel deletar original: {caminho_original}")
                erros += 1
            else:
                log(f"   âœ… Original removido: {caminho_original}")

        deletados += 1

    log(f"ðŸ Limpeza concluÃ­da: {deletados} documentos removidos, {erros} erros.")
    messagebox.showinfo("Limpeza", f"Documentos removidos: {deletados}\nErros: {erros}")

# ============================================================
# ANÃLISE COM OPENAI (CHATGPT VISION)
# ============================================================
def limpar_shutterstock():
    if not token_usuario:
        messagebox.showerror("Erro", "Voce precisa estar autenticado.")
        return

    log("Buscando documentos Shutterstock no Firestore...")
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{COLLECTION_PATH}"
    headers = {"Authorization": f"Bearer {token_usuario}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            log(f"Erro ao buscar documentos: {response.status_code}")
            return
        documentos = response.json().get('documents', [])
    except Exception as e:
        log(f"Erro ao consultar Firestore: {str(e)}")
        return

    docs_para_excluir = []
    for doc in documentos:
        campos = doc.get('fields', {})
        origem = campos.get('origem', {}).get('stringValue', '')
        if origem.lower() != 'shutterstock':
            continue
        extensao = campos.get('extensao', {}).get('stringValue', '.jpg')
        docs_para_excluir.append({
            'id': doc['name'].split('/')[-1],
            'nome_amigavel': campos.get('nome_amigavel', {}).get('stringValue', ''),
            'ano': campos.get('data_processamento', {}).get('stringValue', '2026')[:4],
            'extensao': extensao,
            'tipo_arquivo_original': campos.get('tipo_arquivo_original', {}).get('stringValue', detectar_tipo_arquivo_original(extensao))
        })

    if not docs_para_excluir:
        log("Nenhum documento Shutterstock encontrado. Nada a fazer.")
        return

    resposta = messagebox.askyesno(
        "Confirmacao",
        f"Voce esta prestes a excluir {len(docs_para_excluir)} documentos e seus arquivos do Storage.\n\nEsta acao e irreversivel. Deseja continuar?"
    )
    if not resposta:
        log("Operacao cancelada pelo usuario.")
        return

    deletados = 0
    erros = 0
    for doc in docs_para_excluir:
        doc_id = doc['id']
        nome_amigavel = doc['nome_amigavel']
        ano = doc['ano'] or '2026'
        extensao = doc['extensao']
        tipo_arquivo_original = doc['tipo_arquivo_original']

        url_del_firestore = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{COLLECTION_PATH}/{doc_id}"
        try:
            resp_fire = requests.delete(url_del_firestore, headers=headers)
            if resp_fire.status_code not in (200, 204):
                log(f"   Erro ao excluir documento {doc_id}: {resp_fire.status_code}")
                erros += 1
                continue
        except Exception as e:
            log(f"   Excecao ao excluir documento {doc_id}: {str(e)}")
            erros += 1
            continue

        caminhos_storage = [
            f"acervo-visual-unificado/thumbnails/shutterstock/{ano}/{nome_amigavel}.jpg",
            f"acervo-visual-unificado/originals/{tipo_arquivo_original}/shutterstock/{ano}/{nome_amigavel}{extensao}",
        ]
        for caminho_storage in caminhos_storage:
            if not deletar_arquivo_storage(caminho_storage):
                log(f"   Nao foi possivel deletar: {caminho_storage}")
                erros += 1
            else:
                log(f"   Removido: {caminho_storage}")
        deletados += 1

    log(f"Limpeza concluida: {deletados} documentos removidos, {erros} erros.")
    messagebox.showinfo("Limpeza", f"Documentos removidos: {deletados}\nErros: {erros}")

def obter_openai_api_key():
    return (os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY or "").strip()

def chamar_openai_chat(payload, timeout=120):
    chave = obter_openai_api_key()
    if not chave or chave == "SUA_CHAVE_OPENAI_AQUI":
        raise RuntimeError("Chave da OpenAI nao configurada.")

    response = requests.post(
        OPENAI_CHAT_COMPLETIONS_URL,
        headers={
            "Authorization": f"Bearer {chave}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=timeout,
    )
    if response.status_code >= 400:
        detalhes = response.text[:500] if response.text else ""
        raise RuntimeError(f"OpenAI HTTP {response.status_code}: {detalhes}")
    return response.json()

def testar_openai():
    try:
        prompt = """
        Analise esta imagem e retorne APENAS um JSON valido, sem texto adicional.

        Campos obrigatorios:
        {
            "knowledge_area": "uma das areas controladas",
            "visual_type": "um dos tipos visuais controlados",
            "colors": ["cor1", "cor2", "cor3", "cor4", "cor5", "color1", "color2", "color3", "color4", "color5"],
            "description": "descricao acessivel, objetiva e factual em portugues",
            "keywords": ["15 termos no total"],
            "orientation": "paisagem, retrato, quadrado ou panoramica"
        }

        Areas controladas para knowledge_area:
        Ciencias da Saude; Ciencias Biologicas; Exatas e da terra; Ciencias Humanas;
        Ciencias Sociais Aplicadas; Engenharias; Linguagens; Ciencias Agrarias;
        Direito; Gastronomia; Linguistica Letras e Artes; Producao Cultural e Design.

        Tipos controlados para visual_type:
        Fotografia; Ilustracao; Arte vetorial; Infografico; Diagrama ou fluxograma;
        Grafico de dados; Tabela ou matriz; Mapa; Interface digital; Mockup;
        Textura ou padrao; Produto ou objeto isolado; Cena 3D.

        Regras da description:
        Comece informando o tipo visual e o assunto principal. Descreva apenas o que e visivel,
        sem interpretacoes subjetivas. Inclua elementos principais, posicao, cores, luz,
        profundidade e textos visiveis, se houver. Textos visiveis devem ficar entre aspas.
        Use texto corrido, claro, acessivel e moderado em tamanho.

        Regras de keywords:
        Gere exatamente 15 termos no campo keywords. Os 10 primeiros termos devem ser em
        portugues e os 5 ultimos em ingles. Nao separe por idioma; mantenha tudo em uma
        unica lista. Evite termos repetidos, traducoes diretas excessivas e ideias duplicadas.
        Nao use o mesmo conceito em dois idiomas, por exemplo: nao use "vetor" e "vector",
        "ilustracao" e "illustration", "grafico" e "graphic", "arte" e "art" no mesmo retorno.
        Termos tecnicos, siglas, nomes de tecnologias e palavras amplamente usadas em ingles
        tambem no portugues devem ser mantidos na forma original, como CPU, hardware, software,
        notebook, login, upload, download, dashboard, layout e mockup. Nao duplique o mesmo
        conceito em portugues e ingles quando o termo original ja for o uso natural nos dois
        idiomas; nesses casos, escolha outro termo complementar relevante.

        Regras de orientation:
        Use exclusivamente uma destas quatro opcoes: paisagem, retrato, quadrado ou panoramica.
        Use panoramica apenas quando a imagem for muito mais larga do que alta.

        Padronizacao dos campos controlados:
        Para knowledge_area, visual_type, colors, keywords e orientation,
        retorne os valores sem acento, em letras minusculas e com
        hifen no lugar de espacos. Exemplo: "Ciencias Humanas" deve virar
        "ciencias-humanas"; "sala de aula" deve virar "sala-de-aula".
        A description deve permanecer em texto corrido normal, com acentos quando necessario.
        """
        resposta = chamar_openai_chat({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Responda apenas: OK"}],
            "max_tokens": 10,
        }, timeout=45)
        return bool(resposta.get("choices"))
    except Exception as e:
        log(f"âŒ Falha ao conectar com OpenAI: {str(e)}")
        return False

def carregar_json_resposta_ia(texto_resposta):
    global ultimo_erro_openai
    if not texto_resposta:
        ultimo_erro_openai = "Resposta vazia da IA."
        return None

    json_match = re.search(r'\{.*\}', texto_resposta, re.DOTALL)
    if not json_match:
        ultimo_erro_openai = "Resposta da IA nao contem JSON valido."
        log("   Resposta da IA nao contem JSON valido.")
        return None

    texto_json = json_match.group()
    try:
        return json.loads(texto_json)
    except json.JSONDecodeError as erro_original:
        texto_corrigido = re.sub(r',(\s*[}\]])', r'\1', texto_json)
        if texto_corrigido != texto_json:
            try:
                log("   JSON da IA tinha virgula sobrando; corrigido localmente.")
                return json.loads(texto_corrigido)
            except json.JSONDecodeError:
                pass
        ultimo_erro_openai = f"JSON invalido retornado pela IA: {erro_original}"
        log(f"   JSON invalido retornado pela IA: {erro_original}")
        return None

def formatar_duracao(segundos):
    segundos = max(0, int(segundos))
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

def formatar_numero(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(valor)

def formatar_tamanho_bytes(bytes_total):
    try:
        tamanho = float(bytes_total)
    except (TypeError, ValueError):
        return "0 KB"
    unidades = ["B", "KB", "MB", "GB", "TB"]
    indice = 0
    while tamanho >= 1024 and indice < len(unidades) - 1:
        tamanho /= 1024
        indice += 1
    if indice == 0:
        return f"{int(tamanho)} {unidades[indice]}"
    texto = f"{tamanho:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    return f"{texto} {unidades[indice]}"

def calcular_tamanho_total(arquivos):
    total = 0
    for caminho in arquivos:
        try:
            total += os.path.getsize(caminho)
        except OSError:
            continue
    return total

def analisar_imagem_com_openai(caminho_imagem):
    global ultimo_erro_openai
    ultimo_erro_openai = None
    try:
        with open(caminho_imagem, 'rb') as f:
            imagem_bytes = f.read()
        imagem_base64 = base64.b64encode(imagem_bytes).decode('utf-8')
        
        extensao = os.path.splitext(caminho_imagem)[1].lower()
        mime_type = "image/jpeg"
        if extensao == '.png':
            mime_type = "image/png"
        elif extensao == '.webp':
            mime_type = "image/webp"
        elif extensao in ['.jpg', '.jpeg']:
            mime_type = "image/jpeg"
        
        prompt = """
        Analise esta imagem e retorne APENAS um JSON valido, sem texto adicional.

        Campos obrigatorios:
        {
            "knowledge_area": "uma das areas controladas",
            "visual_type": "um dos tipos visuais controlados",
            "colors": ["cor1", "cor2", "cor3", "cor4", "cor5", "color1", "color2", "color3", "color4", "color5"],
            "description": "descricao acessivel, objetiva e factual em portugues",
            "keywords": ["15 termos no total"],
            "orientation": "paisagem, retrato, quadrado ou panoramica"
        }

        Areas controladas para knowledge_area:
        Ciencias da Saude; Ciencias Biologicas; Exatas e da terra; Ciencias Humanas;
        Ciencias Sociais Aplicadas; Engenharias; Linguagens; Ciencias Agrarias;
        Direito; Gastronomia; Linguistica Letras e Artes; Producao Cultural e Design.

        Tipos controlados para visual_type:
        Fotografia; Ilustracao; Arte vetorial; Infografico; Diagrama ou fluxograma;
        Grafico de dados; Tabela ou matriz; Mapa; Interface digital; Mockup;
        Textura ou padrao; Produto ou objeto isolado; Cena 3D.

        Regras da description:
        Comece informando o tipo visual e o assunto principal. Descreva apenas o que e visivel,
        sem interpretacoes subjetivas. Inclua elementos principais, posicao, cores, luz,
        profundidade e textos visiveis, se houver. Textos visiveis devem ficar entre aspas.
        Use texto corrido, claro, acessivel e moderado em tamanho.

        Regras de colors:
        Gere ate 10 cores predominantes no campo colors. As 5 primeiras devem ser em portugues
        e as 5 ultimas em ingles. Nao separe por idioma; mantenha tudo em uma unica lista.
        Evite repeticoes e traducoes desnecessarias quando o termo for igual ou amplamente
        usado nos dois idiomas.

        Regras de keywords:
        Gere exatamente 15 termos no campo keywords. Os 10 primeiros termos devem ser em
        portugues e os 5 ultimos em ingles. Nao separe por idioma; mantenha tudo em uma
        unica lista. Evite termos repetidos, traducoes diretas excessivas e ideias duplicadas.
        Nao use o mesmo conceito em dois idiomas, por exemplo: nao use "vetor" e "vector",
        "ilustracao" e "illustration", "grafico" e "graphic", "arte" e "art" no mesmo retorno.
        Termos tecnicos, siglas, nomes de tecnologias e palavras amplamente usadas em ingles
        tambem no portugues devem ser mantidos na forma original, como CPU, hardware, software,
        notebook, login, upload, download, dashboard, layout e mockup. Nao duplique o mesmo
        conceito em portugues e ingles quando o termo original ja for o uso natural nos dois
        idiomas; nesses casos, escolha outro termo complementar relevante.

        Regras de orientation:
        Use exclusivamente uma destas quatro opcoes: paisagem, retrato, quadrado ou panoramica.
        Use panoramica apenas quando a imagem for muito mais larga do que alta.

        Padronizacao dos campos controlados:
        Para knowledge_area, visual_type, colors, keywords e orientation,
        retorne os valores sem acento, em letras minusculas e com hifen no lugar de espacos.
        Exemplo: "Ciencias Humanas" deve virar "ciencias-humanas"; "sala de aula" deve virar
        "sala-de-aula". A description deve permanecer em texto corrido normal, com acentos
        quando necessario.
        """
        resposta = chamar_openai_chat({
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{imagem_base64}",
                                "detail": "low"
                            }
                        }
                    ]
                }
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 1000,
        })
        texto_resposta = resposta["choices"][0]["message"]["content"]
        return carregar_json_resposta_ia(texto_resposta)
    except Exception as e:
        ultimo_erro_openai = str(e)
        log(f"   âŒ Erro no OpenAI: {str(e)}")
        return None

def obter_resolucao(caminho):
    try:
        with Image.open(caminho) as img:
            return f"{img.width}x{img.height}"
    except:
        return "Desconhecida"

def normalizar_lista_metadado(valor, limite=None):
    if isinstance(valor, list):
        itens = [str(item).strip() for item in valor if str(item).strip()]
    elif isinstance(valor, str):
        itens = [item.strip() for item in valor.split(",") if item.strip()]
    else:
        itens = []
    return itens[:limite] if limite else itens

def slug_metadado(valor):
    texto = str(valor or "").strip().lower()
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    return texto.strip("-")

def normalizar_lista_slug(valor, limite=None):
    itens = [slug_metadado(item) for item in normalizar_lista_metadado(valor, limite)]
    itens = [item for item in itens if item]
    return itens[:limite] if limite else itens

def chave_conceito_keyword(keyword):
    slug = slug_metadado(keyword)
    equivalencias = {
        "vector": "vetor",
        "vetor": "vetor",
        "illustration": "ilustracao",
        "ilustracao": "ilustracao",
        "graphic": "grafico",
        "grafico": "grafico",
        "graph": "grafico",
        "art": "arte",
        "arte": "arte",
        "technology": "tecnologia",
        "tecnologia": "tecnologia",
        "computer": "computador",
        "computador": "computador",
        "equipment": "equipamento",
        "equipamento": "equipamento",
        "industry": "industria",
        "industria": "industria",
        "education": "educacao",
        "educacao": "educacao",
        "health": "saude",
        "saude": "saude",
        "food": "alimento",
        "alimento": "alimento",
        "business": "negocios",
        "negocios": "negocios",
        "person": "pessoa",
        "pessoa": "pessoa",
        "people": "pessoas",
        "pessoas": "pessoas",
    }
    return equivalencias.get(slug, slug)

def normalizar_keywords_metadados(valor, limite=15):
    keywords = []
    vistos = set()
    for item in normalizar_lista_metadado(valor):
        slug = slug_metadado(item)
        if not slug:
            continue
        chave = chave_conceito_keyword(slug)
        if chave in vistos:
            continue
        vistos.add(chave)
        keywords.append(slug)
        if limite and len(keywords) >= limite:
            break
    return keywords

def normalizar_orientacao_metadado(valor, largura=0, altura=0):
    orientacao = slug_metadado(valor)
    aliases = {
        "horizontal": "paisagem",
        "landscape": "paisagem",
        "paisagem": "paisagem",
        "vertical": "retrato",
        "portrait": "retrato",
        "retrato": "retrato",
        "square": "quadrado",
        "quadrado": "quadrado",
        "panorama": "panoramica",
        "panoramic": "panoramica",
        "panoramica": "panoramica",
    }
    if orientacao in aliases:
        return aliases[orientacao]

    try:
        largura = int(largura or 0)
        altura = int(altura or 0)
    except Exception:
        largura = 0
        altura = 0

    if largura <= 0 or altura <= 0:
        return ""

    proporcao = largura / altura
    if 0.9 <= proporcao <= 1.1:
        return "quadrado"
    if proporcao >= 2.0:
        return "panoramica"
    if proporcao > 1:
        return "paisagem"
    return "retrato"

def normalizar_cores_metadados(metadados, limite=10):
    cores = []
    for campo in ("colors", "predominant_colors", "cores_predominantes", "predominant_colors_pt", "predominant_colors_en"):
        valor = metadados.get(campo, []) if isinstance(metadados, dict) else []
        cores.extend(normalizar_lista_metadado(valor))

    cores_normalizadas = []
    vistos = set()
    for cor in cores:
        cor_slug = slug_metadado(cor)
        if not cor_slug or cor_slug in vistos:
            continue
        vistos.add(cor_slug)
        cores_normalizadas.append(cor_slug)
        if limite and len(cores_normalizadas) >= limite:
            break
    return cores_normalizadas

def montar_resolucoes(original, large=None, medium=None, thumb=None):
    if thumb is None:
        return f"original: {original}; medium: {large}; thumb: {medium}"
    return f"original: {original}; large: {large}; medium: {medium}; thumb: {thumb}"

def obter_dimensoes_arquivo(caminho):
    try:
        with Image.open(caminho) as img:
            return int(img.width), int(img.height)
    except Exception:
        return 0, 0

def montar_info_arquivo(url, caminho):
    largura, altura = obter_dimensoes_arquivo(caminho)
    return {
        "url": url or "",
        "size_bytes": os.path.getsize(caminho) if caminho and os.path.exists(caminho) else 0,
        "width": largura,
        "height": altura
    }

def obter_map_firestore(doc, campo):
    fields = doc.get("fields", {}) if isinstance(doc, dict) else {}
    valor = fields.get(campo, {})
    if not isinstance(valor, dict):
        return {}
    return valor.get("mapValue", {}).get("fields", {})

def obter_valor_firestore_typed(valor):
    if not isinstance(valor, dict):
        return ""
    if "stringValue" in valor:
        return valor["stringValue"]
    if "integerValue" in valor:
        try:
            return int(valor["integerValue"])
        except Exception:
            return valor["integerValue"]
    if "doubleValue" in valor:
        try:
            return float(valor["doubleValue"])
        except Exception:
            return valor["doubleValue"]
    if "booleanValue" in valor:
        return bool(valor["booleanValue"])
    if "arrayValue" in valor:
        return ", ".join(
            str(obter_valor_firestore_typed(v))
            for v in valor["arrayValue"].get("values", [])
        )
    return ""

def obter_file_firestore(doc, versao, campo):
    files = obter_map_firestore(doc, "files")
    versao_map = files.get(versao, {})
    if not isinstance(versao_map, dict):
        return ""
    campos_versao = versao_map.get("mapValue", {}).get("fields", {})
    return obter_valor_firestore_typed(campos_versao.get(campo, {}))

# ============================================================
# EXPORTAÃ‡ÃƒO PARA EXCEL
# ============================================================
def exportar_para_excel():
    if not token_usuario:
        messagebox.showerror("Erro", "VocÃª precisa estar autenticado.")
        return
    log("ðŸ“Š Buscando dados do Firestore para exportar...")
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{COLLECTION_PATH}"
    headers = {"Authorization": f"Bearer {token_usuario}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            log(f"âŒ Erro ao buscar dados: {response.status_code}")
            return
        dados = response.json()
        documentos = dados.get('documents', [])
        if not documentos:
            log("âš ï¸ Nenhum documento encontrado no Firestore.")
            return
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Acervo"
        
        cabecalhos = [
            "Nome do Arquivo", "Link Thumbnail", "Link Original", "Tipo da Imagem", "Elementos Visuais",
            "Estilo/TÃ©cnica", "Formato", "Cores Predominantes", "Ãrea do Conhecimento",
            "CaracterÃ­sticas", "Palavras-chave PT", "Palavras-chave EN", "DescriÃ§Ã£o",
            "ResoluÃ§Ã£o da Imagem", "Tamanho (MB)", "Nome AmigÃ¡vel",
            "Data de Processamento", "Origem"
        ]
        cabecalhos = [
            "Nome Original", "Area do Conhecimento", "Tipo Visual",
            "Cores", "Descricao", "Keywords", "Extensao",
            "Orientacao", "Data de Processamento", "Origem", "pHash", "SHA-256",
            "Tamanho (bytes)", "Resolucoes", "URL Original", "URL Large", "URL Medium", "URL Thumb"
        ]
        ws.append(cabecalhos)
        
        for doc in documentos:
            campos = doc.get('fields', {})
            def get_valor(campo):
                if campo not in campos:
                    return ""
                return obter_valor_firestore_typed(campos[campo])
            
            linha = [
                get_valor("nome_original"),
                get_valor("url_thumbnail") or get_valor("url_visualizacao"),
                get_valor("url_original"),
                get_valor("tipo_imagem"),
                get_valor("elementos_visuais"),
                get_valor("estilo_tecnica"),
                get_valor("formato"),
                get_valor("cores_predominantes"),
                get_valor("area_conhecimento"),
                get_valor("caracteristicas"),
                get_valor("palavras_chave_pt"),
                get_valor("palavras_chave_en"),
                get_valor("descricao_detalhada"),
                get_valor("resolucao"),
                get_valor("tamanho_mb"),
                get_valor("nome_amigavel"),
                get_valor("data_processamento"),
                get_valor("origem")
            ]
            linha = [
                get_valor("original_name") or get_valor("nome_original"),
                get_valor("knowledge_area") or get_valor("area_conhecimento"),
                get_valor("visual_type") or get_valor("tipo_imagem"),
                get_valor("colors") or get_valor("predominant_colors") or get_valor("predominant_colors_pt") or get_valor("cores_predominantes"),
                get_valor("description") or get_valor("descricao_detalhada"),
                get_valor("keywords") or get_valor("palavras_chave_pt"),
                get_valor("extension") or normalizar_extensao(get_valor("extensao")),
                get_valor("orientation") or get_valor("formato"),
                get_valor("processed_at") or get_valor("data_processamento"),
                get_valor("source") or get_valor("origem"),
                get_valor("phash"),
                get_valor("sha256"),
                obter_file_firestore(doc, "original", "size_bytes") or get_valor("size_bytes") or get_valor("tamanho_mb"),
                montar_resolucoes(
                    f"{obter_file_firestore(doc, 'original', 'width')}x{obter_file_firestore(doc, 'original', 'height')}",
                    f"{obter_file_firestore(doc, 'large', 'width')}x{obter_file_firestore(doc, 'large', 'height')}",
                    f"{obter_file_firestore(doc, 'medium', 'width')}x{obter_file_firestore(doc, 'medium', 'height')}",
                    f"{obter_file_firestore(doc, 'thumb', 'width')}x{obter_file_firestore(doc, 'thumb', 'height')}"
                ) if obter_file_firestore(doc, "original", "width") else (get_valor("resolutions") or get_valor("resolucao")),
                obter_file_firestore(doc, "original", "url") or get_valor("url_original"),
                obter_file_firestore(doc, "large", "url") or get_valor("url_large"),
                obter_file_firestore(doc, "medium", "url") or get_valor("url_medium") or get_valor("url_visualizacao"),
                obter_file_firestore(doc, "thumb", "url") or get_valor("url_thumb") or get_valor("url_thumbnail")
            ]
            ws.append(linha)
        
        nome_arquivo = f"acervo_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb.save(nome_arquivo)
        log(f"âœ… Excel exportado com sucesso: {nome_arquivo}")
        messagebox.showinfo("ExportaÃ§Ã£o", f"Arquivo salvo como:\n{nome_arquivo}")
    except Exception as e:
        log(f"âŒ Erro na exportaÃ§Ã£o: {str(e)}")

# ============================================================
# FUNÃ‡ÃƒO PARA ABRIR A VITRINE WEB
# ============================================================
def abrir_vitrine():
    VITRINE_URL = "http://localhost:8080"  # ou "https://uniasselvi-digital.web.app"
    log(f"ðŸŒ Abrindo vitrine web em: {VITRINE_URL}")
    webbrowser.open(VITRINE_URL)

# ============================================================
# FUNÃ‡Ã•ES DE HASH E PROCESSAMENTO
# ============================================================
def calcular_hash_sha256(caminho):
    sha256 = hashlib.sha256()
    try:
        with open(caminho, 'rb') as f:
            for bloco in iter(lambda: f.read(4096), b''):
                sha256.update(bloco)
        return sha256.hexdigest()
    except Exception as e:
        log(f"âŒ Erro ao ler {caminho}: {str(e)}")
        return None

def calcular_phash(caminho):
    try:
        img = Image.open(caminho)
        phash = imagehash.phash(img)
        return str(phash)
    except Exception as e:
        log(f"   âš ï¸ Erro ao calcular pHash: {str(e)}")
        return None

def detectar_caracteristica_cor_por_nome(nome_arquivo):
    stem = os.path.splitext(os.path.basename(nome_arquivo))[0].lower()
    stem = texto_sem_acentos(stem)
    if re.search(r'(^|[\s_\-().])(?:pb|p-b|p_b|bw|bn|preto[ _-]?branco|preto[ _-]?e[ _-]?branco|black[ _-]?white|black[ _-]?and[ _-]?white|grayscale|greyscale|mono|monocromatico|monochrome)(?:$|[\s_\-().])', stem):
        return "preto_e_branco"
    if re.search(r'(^|[\s_\-().])(?:color|colour|colored|colorida|colorido|cores|fullcolor|full[ _-]?color)(?:$|[\s_\-().])', stem):
        return "colorida"
    return None

def detectar_caracteristica_cor(caminho):
    if caminho in COR_VARIACAO_CACHE:
        return COR_VARIACAO_CACHE[caminho]

    por_nome = detectar_caracteristica_cor_por_nome(caminho)
    if por_nome:
        COR_VARIACAO_CACHE[caminho] = por_nome
        return por_nome

    extensao = os.path.splitext(caminho)[1].lower()
    if extensao in EXTENSOES_VETORIAIS:
        COR_VARIACAO_CACHE[caminho] = "desconhecida"
        return "desconhecida"

    try:
        with Image.open(caminho) as img:
            if img.mode in ("1", "L", "LA"):
                COR_VARIACAO_CACHE[caminho] = "preto_e_branco"
                return "preto_e_branco"
            img = ImageOps.exif_transpose(img).convert("RGB")
            img.thumbnail((64, 64))
            pixels = list(img.getdata())
        if not pixels:
            resultado = "desconhecida"
        else:
            deltas = [max(pixel) - min(pixel) for pixel in pixels]
            media_delta = sum(deltas) / len(deltas)
            proporcao_colorida = sum(1 for delta in deltas if delta > 18) / len(deltas)
            if media_delta <= 4 and proporcao_colorida < 0.01:
                resultado = "preto_e_branco"
            elif media_delta >= 8 or proporcao_colorida >= 0.03:
                resultado = "colorida"
            else:
                resultado = "desconhecida"
    except Exception:
        resultado = "desconhecida"

    COR_VARIACAO_CACHE[caminho] = resultado
    return resultado

def detectar_origem(nome_arquivo):
    """Retorna a origem baseada no prefixo do arquivo."""
    nome_lower = nome_arquivo.lower()
    if nome_lower.startswith('shutterstock_'):
        return 'shutterstock'
    elif nome_lower.startswith('envato-'):
        return 'envato'
    elif nome_lower.startswith('pexels'):
        return 'pexels'
    elif nome_lower.startswith('freestock'):
        return 'freestock'
    else:
        return 'desconhecido'

def texto_sem_acentos(texto):
    normalizado = unicodedata.normalize('NFKD', texto)
    return ''.join(char for char in normalizado if not unicodedata.combining(char))

def extrair_chave_numeracao(caminho):
    nome = os.path.basename(caminho)
    origem = detectar_origem(nome)
    if origem == 'desconhecido':
        return None

    stem = os.path.splitext(nome)[0].lower()
    if origem == 'shutterstock':
        restante = stem[len('shutterstock_'):]
    elif origem == 'envato':
        restante = stem[len('envato-'):]
    elif origem == 'pexels':
        restante = stem[len('pexels'):]
    else:
        restante = stem[len('freestock'):]

    match = re.search(r'\d+', restante)
    if not match:
        return None
    return origem, match.group(0)

def formatar_chave_numeracao(caminho):
    chave = extrair_chave_numeracao(caminho)
    if not chave:
        return ""
    origem, numero = chave
    return f"{origem}:{numero}"

def obter_string_firestore(doc, campo):
    fields = doc.get("fields", {}) if isinstance(doc, dict) else {}
    valor = fields.get(campo, {})
    return valor.get("stringValue", "") if isinstance(valor, dict) else ""

def obter_numero_firestore(doc, campo, padrao=0):
    fields = doc.get("fields", {}) if isinstance(doc, dict) else {}
    valor = fields.get(campo, {})
    if not isinstance(valor, dict):
        return padrao
    try:
        if "integerValue" in valor:
            return int(valor.get("integerValue", padrao))
        if "doubleValue" in valor:
            return float(valor.get("doubleValue", padrao))
        if "stringValue" in valor and str(valor.get("stringValue", "")).strip():
            return float(valor.get("stringValue"))
    except Exception:
        return padrao
    return padrao

def normalizar_extensao(extensao):
    return (extensao or "").lower().lstrip(".")

def extensao_eh_vetorial(extensao):
    return f".{normalizar_extensao(extensao)}" in EXTENSOES_VETORIAIS

def obter_extensao_firestore(doc):
    return normalizar_extensao(obter_string_firestore(doc, "extension") or obter_string_firestore(doc, "extensao"))

def extrair_primeira_resolucao(texto):
    match = re.search(r'(\d+)\s*x\s*(\d+)', texto or "", re.IGNORECASE)
    if not match:
        return (0, 0)
    return (int(match.group(1)), int(match.group(2)))

def pixels_da_resolucao(texto):
    largura, altura = extrair_primeira_resolucao(texto)
    return largura * altura

def pixels_do_arquivo(caminho):
    try:
        with Image.open(caminho) as img:
            return img.width * img.height
    except Exception:
        return 0

def obter_pixels_firestore(doc):
    largura = obter_file_firestore(doc, "original", "width")
    altura = obter_file_firestore(doc, "original", "height")
    if largura and altura:
        try:
            return int(largura) * int(altura)
        except Exception:
            pass
    return pixels_da_resolucao(obter_string_firestore(doc, "resolutions") or obter_string_firestore(doc, "resolucao"))

def obter_tamanho_bytes_firestore(doc):
    size_bytes = obter_file_firestore(doc, "original", "size_bytes") or obter_numero_firestore(doc, "size_bytes", 0)
    if size_bytes:
        return int(size_bytes)
    tamanho_mb = obter_numero_firestore(doc, "tamanho_mb", 0)
    if tamanho_mb:
        return int(float(tamanho_mb) * 1024 * 1024)
    return 0

def obter_caracteristica_cor_firestore(doc):
    caracteristica = obter_string_firestore(doc, "caracteristica_cor")
    if caracteristica:
        return caracteristica
    nome_original = obter_string_firestore(doc, "original_name") or obter_string_firestore(doc, "nome_original")
    return detectar_caracteristica_cor_por_nome(nome_original) or "desconhecida"

def deve_enviar_por_prioridade_visual(doc_similar, caminho_atual, extensao_atual):
    ext_atual = normalizar_extensao(extensao_atual)
    ext_doc = obter_extensao_firestore(doc_similar)
    atual_vetor = extensao_eh_vetorial(ext_atual)
    doc_vetor = extensao_eh_vetorial(ext_doc)

    if atual_vetor and not doc_vetor:
        return True, "arquivo vetorial tem prioridade sobre raster parecido"
    if doc_vetor and not atual_vetor:
        return False, "arquivo vetorial parecido ja existe no acervo"
    if atual_vetor and doc_vetor:
        return False, "arquivo vetorial parecido ja existe no acervo"

    pixels_atual = pixels_do_arquivo(caminho_atual)
    pixels_doc = obter_pixels_firestore(doc_similar)
    bytes_atual = os.path.getsize(caminho_atual) if os.path.exists(caminho_atual) else 0
    bytes_doc = obter_tamanho_bytes_firestore(doc_similar)

    if pixels_doc and pixels_atual > pixels_doc * 1.05:
        return True, "raster parecido com resolucao maior que a versao existente"
    if pixels_atual and pixels_doc > pixels_atual * 1.05:
        return False, "raster parecido com resolucao menor que a versao existente"
    if bytes_doc and bytes_atual > bytes_doc * 1.10:
        return True, "raster parecido com tamanho em bytes maior que a versao existente"
    return False, "raster parecido ja existe com qualidade equivalente ou superior"

def deve_manter_colorida_com_pb_existente(doc_similar, chave_numeracao, caracteristica_cor):
    if caracteristica_cor != "colorida" or not chave_numeracao:
        return False
    chave_doc = obter_string_firestore(doc_similar, "chave_numeracao")
    if not chave_doc:
        nome_original = obter_string_firestore(doc_similar, "original_name") or obter_string_firestore(doc_similar, "nome_original")
        chave_doc = formatar_chave_numeracao(nome_original)
    return chave_doc == chave_numeracao and obter_caracteristica_cor_firestore(doc_similar) == "preto_e_branco"

def arquivo_parece_copia(caminho):
    stem = os.path.splitext(os.path.basename(caminho))[0].lower()
    stem = texto_sem_acentos(stem)
    return bool(re.search(r'(^|[\s_\-().])(?:copia|copy)(?:$|[\s_\-().])', stem))

def prioridade_arquivo_original(caminho):
    nome = os.path.basename(caminho)
    stem = os.path.splitext(nome)[0].lower()
    origem = detectar_origem(nome)
    if origem == 'shutterstock':
        restante = stem[len('shutterstock_'):]
    elif origem == 'envato':
        restante = stem[len('envato-'):]
    elif origem == 'pexels':
        restante = stem[len('pexels'):]
    elif origem == 'freestock':
        restante = stem[len('freestock'):]
    else:
        restante = stem

    match = re.search(r'\d+', restante)
    sufixo = ''
    if match:
        sufixo = restante[match.end():].strip(' _-.()')

    prioridade_cor = {
        "colorida": 0,
        "desconhecida": 1,
        "preto_e_branco": 2,
    }.get(detectar_caracteristica_cor(caminho), 1)

    if not sufixo:
        prioridade_nome = 0
    elif not arquivo_parece_copia(caminho):
        prioridade_nome = 1
    else:
        prioridade_nome = 2
    return (prioridade_cor, prioridade_nome, len(nome), nome.lower())

def filtrar_copias_por_numeracao(caminhos):
    grupos = {}
    sem_chave = []
    for caminho in caminhos:
        chave = extrair_chave_numeracao(caminho)
        if chave is None:
            sem_chave.append(caminho)
            continue
        grupos.setdefault(chave, []).append(caminho)

    escolhidos = set(sem_chave)
    ignorados = []
    for itens in grupos.values():
        escolhido = sorted(itens, key=prioridade_arquivo_original)[0]
        escolhidos.add(escolhido)
        ignorados.extend(item for item in itens if item != escolhido)

    filtrados = [caminho for caminho in caminhos if caminho in escolhidos]
    return filtrados, ignorados

def detectar_tipo_arquivo_original(extensao):
    if extensao in EXTENSOES_VETORIAIS:
        return "vector"
    return "raster"

def obter_arquivo_pendencias():
    for caminho in (PENDING_METADATA_FILE, PENDING_METADATA_FALLBACK_FILE):
        pasta = os.path.dirname(caminho)
        try:
            os.makedirs(pasta, exist_ok=True)
            teste = caminho + ".write_test"
            with open(teste, 'w') as f:
                f.write("ok")
            os.remove(teste)
            return caminho
        except Exception:
            continue
    return PENDING_METADATA_FALLBACK_FILE

def obter_arquivo_fila_processamento():
    for caminho in (PROCESSING_QUEUE_FILE, PROCESSING_QUEUE_FALLBACK_FILE):
        pasta = os.path.dirname(caminho)
        try:
            os.makedirs(pasta, exist_ok=True)
            teste = caminho + ".write_test"
            with open(teste, 'w') as f:
                f.write("ok")
            os.remove(teste)
            return caminho
        except Exception:
            continue
    return PROCESSING_QUEUE_FALLBACK_FILE

def carregar_fila_processamento():
    arquivo = obter_arquivo_fila_processamento()
    if not os.path.exists(arquivo):
        return None
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        if isinstance(dados, dict) and isinstance(dados.get("files"), list):
            return dados
    except Exception as e:
        log(f"Erro ao ler fila de processamento: {str(e)}")
    return None

def salvar_fila_processamento(arquivos, pasta_origem=None, next_index=0, completed=False):
    arquivo = obter_arquivo_fila_processamento()
    dados = {
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "source_folder": pasta_origem or "",
        "total": len(arquivos),
        "next_index": next_index,
        "completed": completed,
        "files": arquivos
    }
    try:
        arquivo_temp = arquivo + ".tmp"
        with open(arquivo_temp, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False)
        os.replace(arquivo_temp, arquivo)
        return arquivo
    except Exception as e:
        log(f"Erro ao salvar fila de processamento: {str(e)}")
        return None

def atualizar_checkpoint_processamento(next_index, completed=False):
    fila = carregar_fila_processamento()
    if not fila:
        return
    fila["next_index"] = next_index
    fila["completed"] = completed
    fila["updated_at"] = datetime.now().isoformat()
    arquivo = obter_arquivo_fila_processamento()
    try:
        arquivo_temp = arquivo + ".tmp"
        with open(arquivo_temp, 'w', encoding='utf-8') as f:
            json.dump(fila, f, ensure_ascii=False)
        os.replace(arquivo_temp, arquivo)
    except Exception as e:
        log(f"Erro ao atualizar checkpoint: {str(e)}")

def apagar_fila_processamento():
    removidos = []
    caminhos = {
        PROCESSING_QUEUE_FILE,
        PROCESSING_QUEUE_FALLBACK_FILE,
        PROCESSING_QUEUE_FILE + ".tmp",
        PROCESSING_QUEUE_FALLBACK_FILE + ".tmp",
    }
    for caminho in caminhos:
        try:
            if os.path.exists(caminho):
                os.remove(caminho)
                removidos.append(caminho)
        except Exception as e:
            log(f"Erro ao apagar fila de processamento ({caminho}): {str(e)}")
    return removidos

def carregar_pendencias():
    arquivo = obter_arquivo_pendencias()
    if not os.path.exists(arquivo):
        return {}
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        if isinstance(dados, dict):
            return dados
    except Exception as e:
        log(f"   Erro ao ler fila de pendencias: {str(e)}")
    return {}

def salvar_pendencias(pendencias):
    arquivo = obter_arquivo_pendencias()
    pasta = os.path.dirname(arquivo)
    try:
        os.makedirs(pasta, exist_ok=True)
        arquivo_temp = arquivo + ".tmp"
        with open(arquivo_temp, 'w', encoding='utf-8') as f:
            json.dump(pendencias, f, ensure_ascii=False, indent=2)
        os.replace(arquivo_temp, arquivo)
        return arquivo
    except Exception as e:
        log(f"   Erro ao salvar fila de pendencias: {str(e)}")
        return None

def registrar_pendencia(caminho, origem, hash_sha256, phash_str, extensao, motivo):
    pendencias = carregar_pendencias()
    chave = hash_sha256 or caminho
    anterior = pendencias.get(chave, {})
    pendencias[chave] = {
        "caminho": caminho,
        "nome_original": os.path.basename(caminho),
        "origem": origem,
        "chave_numeracao": formatar_chave_numeracao(caminho),
        "caracteristica_cor": detectar_caracteristica_cor(caminho),
        "sha256": hash_sha256 or "",
        "phash": phash_str or "",
        "extensao": extensao,
        "tentativas": int(anterior.get("tentativas", 0)) + 1,
        "ultimo_erro": motivo or "Falha ao gerar metadados pela IA.",
        "criado_em": anterior.get("criado_em", datetime.now().isoformat()),
        "atualizado_em": datetime.now().isoformat()
    }
    arquivo = salvar_pendencias(pendencias)
    return arquivo

def remover_pendencia(hash_sha256):
    if not hash_sha256:
        return
    pendencias = carregar_pendencias()
    if hash_sha256 in pendencias:
        del pendencias[hash_sha256]
        salvar_pendencias(pendencias)

def reprocessar_pendentes():
    global arquivos_encontrados
    pendencias = carregar_pendencias()
    if not pendencias:
        messagebox.showinfo("Pendencias", "Nao ha imagens pendentes para reprocessar.")
        return
    arquivos_validos = []
    removidos = 0
    for chave, item in list(pendencias.items()):
        caminho = item.get("caminho")
        if caminho and os.path.exists(caminho):
            arquivos_validos.append(caminho)
        else:
            del pendencias[chave]
            removidos += 1
    if removidos:
        salvar_pendencias(pendencias)
        log(f"Removidas {formatar_numero(removidos)} pendencias com arquivo local ausente.")
    if not arquivos_validos:
        messagebox.showwarning("Pendencias", "Nenhuma pendencia possui arquivo local acessivel.")
        return
    arquivos_encontrados, arquivos_ignorados = filtrar_copias_por_numeracao(arquivos_validos)
    if arquivos_ignorados:
        log(f"Ignoradas {formatar_numero(len(arquivos_ignorados))} pendencias duplicadas por mesma numeracao.")
    lista_arquivos.delete(0, tk.END)
    for caminho in arquivos_encontrados[:DISPLAY_FILE_LIMIT]:
        lista_arquivos.insert(tk.END, caminho)
    if len(arquivos_encontrados) > DISPLAY_FILE_LIMIT:
        lista_arquivos.insert(tk.END, f"... mais {formatar_numero(len(arquivos_encontrados) - DISPLAY_FILE_LIMIT)} arquivos pendentes ocultos na lista visual")
    salvar_fila_processamento(arquivos_encontrados, pasta_origem="pendencias", next_index=0, completed=False)
    atualizar_metricas(len(arquivos_encontrados), 0, 0, 0, 0)
    log(f"Reprocessando {formatar_numero(len(arquivos_encontrados))} pendencias.")
    iniciar_processamento()

def escolher_pasta():
    global arquivos_encontrados, linha_log_varredura
    pasta = filedialog.askdirectory()
    if not pasta:
        return
    lista_arquivos.delete(0, tk.END)
    arquivos_encontrados = []
    arquivos_candidatos = []
    linha_log_varredura = None
    atualizar_log_varredura(None)
    total_arquivos_varredura = 0
    for _raiz, _subpastas, arquivos in os.walk(pasta):
        total_arquivos_varredura += len(arquivos)

    if total_arquivos_varredura == 0:
        atualizar_log_varredura(100)
    else:
        atualizar_log_varredura(0)

    arquivos_verificados = 0
    ultimo_percentual_logado = 0
    log(f"ðŸ“ Varrendo: {pasta}")
    for raiz, subpastas, arquivos in os.walk(pasta):
        for arquivo in arquivos:
            arquivos_verificados += 1
            if total_arquivos_varredura:
                percentual = int((arquivos_verificados / total_arquivos_varredura) * 100)
                if percentual >= ultimo_percentual_logado + 10 or arquivos_verificados == total_arquivos_varredura:
                    ultimo_percentual_logado = percentual
                    atualizar_log_varredura(percentual)
            nome_lower = arquivo.lower()
            if not any(nome_lower.startswith(p) for p in PREFIXOS_ACEITOS):
                continue
            if not nome_lower.endswith(EXTENSOES_PERMITIDAS):
                continue
            caminho = os.path.join(raiz, arquivo)
            arquivos_candidatos.append(caminho)
            if len(arquivos_candidatos) % 1000 == 0:
                atualizar_metricas(len(arquivos_candidatos), 0, 0, 0)
    arquivos_encontrados, arquivos_ignorados = filtrar_copias_por_numeracao(arquivos_candidatos)
    total = len(arquivos_encontrados)
    tamanho_total = calcular_tamanho_total(arquivos_encontrados)
    for caminho in arquivos_encontrados[:DISPLAY_FILE_LIMIT]:
        lista_arquivos.insert(tk.END, caminho)
    if arquivos_ignorados:
        log(f"Ignoradas {formatar_numero(len(arquivos_ignorados))} copias/variacoes com a mesma numeracao.")
    log(f"âœ… Encontrados {formatar_numero(total)} arquivos ({formatar_tamanho_bytes(tamanho_total)}).")
    if total > DISPLAY_FILE_LIMIT:
        lista_arquivos.insert(tk.END, f"... mais {formatar_numero(total - DISPLAY_FILE_LIMIT)} arquivos ocultos na lista visual")
        log(f"Lista visual limitada aos primeiros {formatar_numero(DISPLAY_FILE_LIMIT)} arquivos para manter o programa leve.")
    arquivo_fila = salvar_fila_processamento(arquivos_encontrados, pasta_origem=pasta, next_index=0, completed=False)
    if arquivo_fila:
        log(f"Fila de processamento salva em: {arquivo_fila}")
    atualizar_metricas(total, 0, 0, 0, 0)

def iniciar_processamento_antigo_sem_fila():
    global token_usuario
    log("Fluxo antigo sem fila redirecionado para o processamento atual.")
    return iniciar_processamento()

    if not arquivos_encontrados:
        messagebox.showerror("Erro", "Selecione uma pasta primeiro.")
        return
    if not token_usuario:
        token_usuario = obter_token()
        if not token_usuario:
            return

    if OPENAI_API_KEY == "SUA_CHAVE_OPENAI_AQUI":
        log("âŒ ERRO: Chave da OpenAI nÃ£o configurada.")
        messagebox.showerror("Erro", "Configure sua chave da OpenAI.")
        return

    log("ðŸ” Testando conexÃ£o com OpenAI...")
    if not testar_openai():
        log("âŒ Falha na conexÃ£o com OpenAI.")
        messagebox.showerror("Erro", "NÃ£o foi possÃ­vel conectar ao OpenAI.")
        return
    else:
        log("âœ… ConexÃ£o com OpenAI OK!")

    log("ðŸš€ Iniciando processamento...")
    total = len(arquivos_encontrados)
    processados = 0
    duplicados = 0
    erros = 0
    ano = datetime.now().year

    for idx, caminho in enumerate(arquivos_encontrados):
        nome = os.path.basename(caminho)
        log(f"[{idx+1}/{total}] ðŸ“· {nome}")
        progresso['value'] = (idx / total) * 100

        # --- DETECTAR ORIGEM ---
        origem = detectar_origem(nome)
        if origem == 'desconhecido':
            log(f"   âš ï¸ Origem nÃ£o identificada para {nome}. Pulando.")
            erros += 1
            continue

        chave_numeracao = formatar_chave_numeracao(caminho)
        caracteristica_cor = detectar_caracteristica_cor(caminho)
        if caracteristica_cor != "desconhecida":
            log(f"   VariaÃ§Ã£o de cor: {caracteristica_cor}.")

        # --- HASH SHA-256 ---
        hash_sha256 = calcular_hash_sha256(caminho)
        if not hash_sha256:
            erros += 1
            atualizar_metricas(total, processados, duplicados, erros)
            continue

        # --- DUPLICIDADE EXATA ---
        if consultar_hash_no_firestore(hash_sha256):
            remover_pendencia(hash_sha256)
            log(f"   â­ï¸ DUPLICADO EXATO (SHA-256). Pulando.")
            duplicados += 1
            atualizar_metricas(total, processados, duplicados, erros)
            continue

        # --- pHASH (visual) ---
        phash_str = calcular_phash(caminho)
        if phash_str:
            doc_similar = consultar_phash_similar(phash_str, limite_distancia=5)
            if doc_similar:
                if deve_manter_colorida_com_pb_existente(doc_similar, chave_numeracao, caracteristica_cor):
                    log("   VariaÃ§Ã£o colorida encontrada para item que existia em PB. Mantendo para upload.")
                else:
                    remover_pendencia(hash_sha256)
                    log(f"   ðŸ”„ DUPLICATA VISUAL (pHash similar). Pulando.")
                    duplicados += 1
                    atualizar_metricas(total, processados, duplicados, erros)
                    continue
        else:
            log("   âš ï¸ NÃ£o foi possÃ­vel calcular pHash.")

        # --- IDENTIFICADORES ---
        uuid_img = str(uuid.uuid4())
        codigo_acervo = gerar_codigo_acervo(ano)
        nome_amigavel = codigo_acervo
        extensao = os.path.splitext(caminho)[1].lower()

        # --- CONVERSÃƒO EPS/AI PARA JPG (se necessÃ¡rio) ---
        imagem_para_analise = caminho
        imagem_convertida_temp = None

        if extensao in ('.eps', '.ai'):
            # Cria um JPG temporÃ¡rio para anÃ¡lise
            imagem_convertida_temp = os.path.join(os.path.dirname(caminho), f"temp_{uuid_img}.jpg")
            log(f"   ðŸ”„ Convertendo {extensao} para JPG...")
            if converter_para_jpg(caminho, imagem_convertida_temp):
                imagem_para_analise = imagem_convertida_temp
                log(f"   âœ… ConversÃ£o concluÃ­da.")
            else:
                log(f"   âŒ Falha na conversÃ£o. Pulando.")
                erros += 1
                continue

        # --- UPLOAD DA IMAGEM CONVERTIDA (visualizaÃ§Ã£o) ---
        # --- ANALISE COM OPENAI (antes do upload) ---
        log(f"   Ã°Å¸Â¤â€“ Analisando com ChatGPT Vision...")
        metadados = analisar_imagem_com_openai(imagem_para_analise)
        resolucao_original = obter_resolucao(caminho)
        resolucao_medium = obter_resolucao(medium_temp)
        resolucao_thumb = obter_resolucao(thumbnail_temp)
        resolucao = montar_resolucoes(resolucao_original, resolucao_medium, resolucao_thumb)

        if imagem_convertida_temp and os.path.exists(imagem_convertida_temp):
            os.remove(imagem_convertida_temp)
            imagem_convertida_temp = None

        if not metadados:
            motivo = ultimo_erro_openai or "Falha ao gerar metadados pela IA."
            arquivo_pendencias = registrar_pendencia(caminho, origem, hash_sha256, phash_str, extensao, motivo)
            if arquivo_pendencias:
                log(f"   Pendente salvo em: {arquivo_pendencias}")
            log("   Upload e Firestore pulados para evitar cadastro incompleto.")
            erros += 1
            atualizar_metricas(total, processados, duplicados, erros)
            if ultimo_erro_openai and ultimo_erro_openai != "Resposta da IA nao contem JSON valido.":
                atualizar_checkpoint_processamento(idx + 1, completed=False)
                log("Processamento pausado apos falha da OpenAI. A fila pode ser retomada depois.")
                messagebox.showwarning("Pausado", "A OpenAI falhou durante o processamento. O arquivo atual ficou pendente e a fila foi salva para retomar depois.")
                return
            continue

        log(f"   Ã¢Å“â€¦ AnÃƒÂ¡lise OpenAI concluÃƒÂ­da!")

        destino_pasta = f"acervo-visual-unificado/{uuid_img}"
        destino_visualizacao = f"{destino_pasta}/{uuid_img}_thumb.jpg"
        log(f"   ðŸ“¤ Upload visualizaÃ§Ã£o: {destino_visualizacao}")
        url_visualizacao = fazer_upload_imagem(imagem_para_analise, destino_visualizacao)
        if not url_visualizacao:
            erros += 1
            if imagem_convertida_temp and os.path.exists(imagem_convertida_temp):
                os.remove(imagem_convertida_temp)
            atualizar_metricas(total, processados, duplicados, erros)
            continue

        # --- UPLOAD DO ARQUIVO ORIGINAL (se for EPS/AI) ---
        url_original = None
        if extensao in ('.eps', '.ai'):
            destino_original = f"{destino_pasta}/{uuid_img}_original{extensao}"
            log(f"   ðŸ“¤ Upload original: {destino_original}")
            url_original = fazer_upload_imagem(caminho, destino_original)

        # --- ANÃLISE COM OPENAI (usando a imagem convertida) ---
        log(f"   ðŸ¤– Analisando com ChatGPT Vision...")
        metadados = analisar_imagem_com_openai(imagem_para_analise)

        # --- REMOVE ARQUIVO TEMPORÃRIO (se existir) ---
        if imagem_convertida_temp and os.path.exists(imagem_convertida_temp):
            os.remove(imagem_convertida_temp)

        # --- METADADOS ADICIONAIS ---
        tamanho_mb = round(os.path.getsize(caminho) / (1024 * 1024), 2)
        resolucao = obter_resolucao(imagem_para_analise)

        # --- MONTAR DOCUMENTO FIRESTORE ---
        dados_documento = {
            "uuid": uuid_img,
            "codigo": codigo_acervo,
            "nome_amigavel": nome_amigavel,
            "nome_original": nome,
            "url_visualizacao": url_visualizacao,
            "url_original": url_original,
            "origem": origem,
            "chave_numeracao": chave_numeracao,
            "sha256": hash_sha256,
            "phash": phash_str if phash_str else "",
            "extensao": extensao,
            "tamanho_mb": tamanho_mb,
            "resolucao": resolucao,
            "data_processamento": datetime.now().isoformat(),
            "tipo_imagem": metadados.get("tipo_imagem", "") if metadados else "",
            "elementos_visuais": metadados.get("elementos_visuais", "") if metadados else "",
            "estilo_tecnica": metadados.get("estilo_tecnica", "") if metadados else "",
            "formato": metadados.get("formato", "") if metadados else "",
            "cores_predominantes": metadados.get("cores_predominantes", "") if metadados else "",
            "area_conhecimento": metadados.get("area_conhecimento", "") if metadados else "",
            "caracteristicas": metadados.get("caracteristicas", "") if metadados else "",
            "palavras_chave_pt": metadados.get("palavras_chave_pt", []) if metadados else [],
            "palavras_chave_en": metadados.get("palavras_chave_en", []) if metadados else [],
            "descricao_detalhada": metadados.get("descricao_detalhada", "") if metadados else "",
            "sheet_synced": False
        }

        if metadados:
            log(f"   âœ… AnÃ¡lise OpenAI concluÃ­da!")
        else:
            log(f"   âš ï¸ Falha na anÃ¡lise. Dados salvos parcialmente.")

        # --- SALVAR NO FIRESTORE ---
        if gravar_no_firestore(dados_documento, uuid_img):
            processados += 1
        else:
            erros += 1

        atualizar_metricas(total, processados, duplicados, erros)
        time.sleep(0.3)

    progresso['value'] = 100
    log(f"ðŸ Processamento finalizado!")
    log(f"   âœ… Processados: {processados}")
    log(f"   â­ï¸ Duplicados: {duplicados}")
    log(f"   âŒ Erros: {erros}")
    messagebox.showinfo("ConcluÃ­do", f"Processados: {processados}\nDuplicados: {duplicados}\nErros: {erros}")

# ============================================================
# CONSTRUÃ‡ÃƒO DA INTERFACE
# ============================================================
def iniciar_processamento():
    global token_usuario, arquivos_encontrados
    fila_processamento = carregar_fila_processamento()
    inicio_processamento = 0
    if not arquivos_encontrados:
        if fila_processamento and not fila_processamento.get("completed") and fila_processamento.get("files"):
            arquivos_encontrados = fila_processamento.get("files", [])
            inicio_processamento = min(int(fila_processamento.get("next_index", 0)), len(arquivos_encontrados))
            lista_arquivos.delete(0, tk.END)
            for caminho in arquivos_encontrados[inicio_processamento:inicio_processamento + DISPLAY_FILE_LIMIT]:
                lista_arquivos.insert(tk.END, caminho)
            if len(arquivos_encontrados) - inicio_processamento > DISPLAY_FILE_LIMIT:
                lista_arquivos.insert(tk.END, f"... mais {len(arquivos_encontrados) - inicio_processamento - DISPLAY_FILE_LIMIT} arquivos ocultos na lista visual")
            log(f"Retomando fila salva a partir do item {inicio_processamento + 1} de {len(arquivos_encontrados)}.")
        else:
            messagebox.showerror("Erro", "Selecione uma pasta primeiro.")
            return
    elif fila_processamento and not fila_processamento.get("completed"):
        arquivos_fila = fila_processamento.get("files", [])
        if (
            len(arquivos_fila) == len(arquivos_encontrados)
            and (not arquivos_encontrados or arquivos_fila[0] == arquivos_encontrados[0])
            and (not arquivos_encontrados or arquivos_fila[-1] == arquivos_encontrados[-1])
        ):
            inicio_processamento = min(int(fila_processamento.get("next_index", 0)), len(arquivos_encontrados))
    if arquivos_encontrados:
        arquivos_filtrados, arquivos_ignorados = filtrar_copias_por_numeracao(arquivos_encontrados)
        if arquivos_ignorados:
            ja_percorridos = set(arquivos_encontrados[:inicio_processamento])
            inicio_processamento = sum(1 for caminho in arquivos_filtrados if caminho in ja_percorridos)
            arquivos_encontrados = arquivos_filtrados
            atualizar_checkpoint_processamento(inicio_processamento, completed=False)
            log(f"Ignoradas {len(arquivos_ignorados)} copias/variacoes da fila por mesma numeracao.")
    if not token_usuario:
        token_usuario = obter_token()
        if not token_usuario:
            return

    if OPENAI_API_KEY == "SUA_CHAVE_OPENAI_AQUI":
        log("ERRO: Chave da OpenAI nao configurada.")
        messagebox.showerror("Erro", "Configure sua chave da OpenAI.")
        return

    log("Testando conexao com OpenAI...")
    openai_disponivel = testar_openai()
    if openai_disponivel:
        log("Conexao com OpenAI OK.")
    else:
        log("Falha na conexao com OpenAI. Nenhum arquivo sera enviado; a fila foi mantida para retomar depois.")
        messagebox.showerror("Erro", "Nao foi possivel conectar ao OpenAI. A fila ficou salva para retomar depois.")
        return
    log("Iniciando processamento protegido...")
    tempo_inicio_processamento = time.time()
    total = len(arquivos_encontrados)
    processados = 0
    duplicados = 0
    erros = 0
    ano = datetime.now().year

    if inicio_processamento >= total:
        log("Fila de processamento ja foi concluida.")
        atualizar_checkpoint_processamento(total, completed=True)
        messagebox.showinfo("Concluido", "A fila de processamento ja foi concluida.")
        return

    for idx in range(inicio_processamento, total):
        caminho = arquivos_encontrados[idx]
        if (idx - inicio_processamento) % QUEUE_CHECKPOINT_INTERVAL == 0:
            atualizar_checkpoint_processamento(idx, completed=False)
        nome = os.path.basename(caminho)
        log(f"[{idx+1}/{total}] {nome}")
        progresso['value'] = (idx / total) * 100

        origem = detectar_origem(nome)
        if origem == 'desconhecido':
            log(f"   Origem nao identificada para {nome}. Pulando.")
            erros += 1
            atualizar_metricas(total, processados, duplicados, erros)
            continue

        chave_numeracao = formatar_chave_numeracao(caminho)
        caracteristica_cor = detectar_caracteristica_cor(caminho)
        if caracteristica_cor != "desconhecida":
            log(f"   Variacao de cor: {caracteristica_cor}.")

        hash_sha256 = calcular_hash_sha256(caminho)
        if not hash_sha256:
            erros += 1
            atualizar_metricas(total, processados, duplicados, erros)
            continue

        if consultar_hash_no_firestore(hash_sha256):
            remover_pendencia(hash_sha256)
            log("   DUPLICADO EXATO (SHA-256). Pulando.")
            duplicados += 1
            atualizar_metricas(total, processados, duplicados, erros)
            continue

        extensao = os.path.splitext(caminho)[1].lower()
        doc_repetido_para_excluir = None
        motivo_exclusao_repetido = ""
        phash_str = calcular_phash(caminho)
        if phash_str:
            doc_similar = consultar_phash_similar(phash_str, limite_distancia=5)
            if doc_similar:
                if deve_manter_colorida_com_pb_existente(doc_similar, chave_numeracao, caracteristica_cor):
                    motivo_exclusao_repetido = "nova versao colorida substitui variacao PB semelhante"
                    doc_repetido_para_excluir = doc_similar
                    log("   Variacao colorida encontrada para item que existia em PB. A nova versao vai substituir a anterior se o upload concluir.")
                else:
                    deve_enviar, motivo_prioridade = deve_enviar_por_prioridade_visual(doc_similar, caminho, extensao)
                    if deve_enviar:
                        motivo_exclusao_repetido = motivo_prioridade
                        doc_repetido_para_excluir = doc_similar
                        log(f"   Similar visual encontrado, mas esta versao vai substituir a anterior se o upload concluir: {motivo_prioridade}.")
                    else:
                        remover_pendencia(hash_sha256)
                        log(f"   DUPLICATA VISUAL (pHash similar). Pulando: {motivo_prioridade}.")
                        duplicados += 1
                        atualizar_metricas(total, processados, duplicados, erros)
                        continue
        else:
            log("   Nao foi possivel calcular pHash.")

        arquivos_temp = []
        fonte_visualizacao = caminho

        if extensao in EXTENSOES_VETORIAIS:
            temp_uuid = str(uuid.uuid4())
            imagem_convertida_temp = os.path.join(os.path.dirname(caminho), f"temp_{temp_uuid}.jpg")
            log(f"   Convertendo {extensao} para JPG...")
            if converter_para_jpg(caminho, imagem_convertida_temp):
                fonte_visualizacao = imagem_convertida_temp
                arquivos_temp.append(imagem_convertida_temp)
                log("   Conversao concluida.")
            else:
                log("   Falha na conversao. Pulando.")
                erros += 1
                atualizar_metricas(total, processados, duplicados, erros)
                continue

        large_temp = os.path.join(os.path.dirname(caminho), f"large_{uuid.uuid4().hex}.jpg")
        if not criar_jpg_otimizado(fonte_visualizacao, large_temp, LARGE_MAX_SIZE, qualidade=90):
            for temp in arquivos_temp:
                if os.path.exists(temp):
                    os.remove(temp)
            erros += 1
            atualizar_metricas(total, processados, duplicados, erros)
            continue
        arquivos_temp.append(large_temp)

        medium_temp = os.path.join(os.path.dirname(caminho), f"medium_{uuid.uuid4().hex}.jpg")
        if not criar_jpg_otimizado(fonte_visualizacao, medium_temp, MEDIUM_MAX_SIZE, qualidade=88):
            for temp in arquivos_temp:
                if os.path.exists(temp):
                    os.remove(temp)
            erros += 1
            atualizar_metricas(total, processados, duplicados, erros)
            continue
        arquivos_temp.append(medium_temp)

        thumbnail_temp = os.path.join(os.path.dirname(caminho), f"thumbnail_{uuid.uuid4().hex}.jpg")
        if not criar_jpg_otimizado(fonte_visualizacao, thumbnail_temp, THUMBNAIL_MAX_SIZE, qualidade=82):
            for temp in arquivos_temp:
                if os.path.exists(temp):
                    os.remove(temp)
            erros += 1
            atualizar_metricas(total, processados, duplicados, erros)
            continue
        arquivos_temp.append(thumbnail_temp)

        imagem_para_analise = thumbnail_temp

        log("   Analisando com ChatGPT Vision...")
        if openai_disponivel:
            metadados = analisar_imagem_com_openai(imagem_para_analise)
        else:
            metadados = None
        resolucao_original = obter_resolucao(caminho)
        resolucao_large = obter_resolucao(large_temp)
        resolucao_medium = obter_resolucao(medium_temp)
        resolucao_thumb = obter_resolucao(thumbnail_temp)
        resolucao = montar_resolucoes(resolucao_original, resolucao_large, resolucao_medium, resolucao_thumb)

        if not metadados:
            if openai_disponivel:
                motivo = ultimo_erro_openai or "Falha ao gerar metadados pela IA."
            else:
                motivo = "Falha no teste inicial da OpenAI. Creditos, chave, limite ou conexao podem estar indisponiveis."
            for temp in arquivos_temp:
                if os.path.exists(temp):
                    os.remove(temp)
            arquivo_pendencias = registrar_pendencia(caminho, origem, hash_sha256, phash_str, extensao, motivo)
            if arquivo_pendencias:
                log(f"   Pendente salvo em: {arquivo_pendencias}")
            log("   Upload e Firestore pulados para evitar cadastro incompleto.")
            erros += 1
            atualizar_metricas(total, processados, duplicados, erros)
            if ultimo_erro_openai and ultimo_erro_openai != "Resposta da IA nao contem JSON valido.":
                atualizar_checkpoint_processamento(idx + 1, completed=False)
                log("Processamento pausado apos falha da OpenAI. A fila pode ser retomada depois.")
                messagebox.showwarning("Pausado", "A OpenAI falhou durante o processamento. O arquivo atual ficou pendente e a fila foi salva para retomar depois.")
                return
            continue

        log("   Analise OpenAI concluida.")

        uuid_img = str(uuid.uuid4())

        destino_pasta = f"acervo-visual-unificado/{uuid_img}"
        destino_thumbnail = f"{destino_pasta}/{uuid_img}_thumb.jpg"
        destino_medium = f"{destino_pasta}/{uuid_img}_medium.jpg"
        destino_large = f"{destino_pasta}/{uuid_img}_large.jpg"
        destino_original = f"{destino_pasta}/{uuid_img}_original{extensao}"

        log(f"   Upload thumb: {destino_thumbnail}")
        url_thumbnail = fazer_upload_imagem(thumbnail_temp, destino_thumbnail)
        if not url_thumbnail:
            erros += 1
            for temp in arquivos_temp:
                if os.path.exists(temp):
                    os.remove(temp)
            atualizar_metricas(total, processados, duplicados, erros)
            continue

        log(f"   Upload medium: {destino_medium}")
        url_medium = fazer_upload_imagem(medium_temp, destino_medium)
        if not url_medium:
            deletar_arquivo_storage(destino_thumbnail)
            erros += 1
            for temp in arquivos_temp:
                if os.path.exists(temp):
                    os.remove(temp)
            atualizar_metricas(total, processados, duplicados, erros)
            continue

        log(f"   Upload large: {destino_large}")
        url_large = fazer_upload_imagem(large_temp, destino_large)
        if not url_large:
            deletar_arquivo_storage(destino_thumbnail)
            deletar_arquivo_storage(destino_medium)
            erros += 1
            for temp in arquivos_temp:
                if os.path.exists(temp):
                    os.remove(temp)
            atualizar_metricas(total, processados, duplicados, erros)
            continue

        log(f"   Upload original: {destino_original}")
        url_original = fazer_upload_imagem(caminho, destino_original)
        if not url_original:
            deletar_arquivo_storage(destino_thumbnail)
            deletar_arquivo_storage(destino_medium)
            deletar_arquivo_storage(destino_large)
            erros += 1
            for temp in arquivos_temp:
                if os.path.exists(temp):
                    os.remove(temp)
            atualizar_metricas(total, processados, duplicados, erros)
            continue

        files_metadata = {
            "original": montar_info_arquivo(url_original, caminho),
            "large": montar_info_arquivo(url_large, large_temp),
            "medium": montar_info_arquivo(url_medium, medium_temp),
            "thumb": montar_info_arquivo(url_thumbnail, thumbnail_temp)
        }

        for temp in arquivos_temp:
            if os.path.exists(temp):
                os.remove(temp)

        dados_documento = {
            "original_name": nome,
            "knowledge_area": slug_metadado(metadados.get("knowledge_area", "")),
            "visual_type": slug_metadado(metadados.get("visual_type", "")),
            "colors": normalizar_cores_metadados(metadados, 10),
            "description": metadados.get("description", ""),
            "keywords": normalizar_keywords_metadados(metadados.get("keywords", []), 15),
            "extension": normalizar_extensao(extensao),
            "orientation": normalizar_orientacao_metadado(
                metadados.get("orientation", ""),
                files_metadata["large"].get("width"),
                files_metadata["large"].get("height")
            ),
            "processed_at": datetime.now().isoformat(),
            "source": slug_metadado(origem),
            "chave_numeracao": chave_numeracao,
            "sha256": hash_sha256,
            "phash": phash_str if phash_str else "",
            "files": files_metadata
        }

        if gravar_no_firestore(dados_documento, uuid_img):
            processados += 1
            remover_pendencia(hash_sha256)
            if doc_repetido_para_excluir:
                excluir_registro_repetido_substituido(doc_repetido_para_excluir, motivo_exclusao_repetido)
        else:
            deletar_arquivo_storage(destino_thumbnail)
            deletar_arquivo_storage(destino_medium)
            deletar_arquivo_storage(destino_original)
            erros += 1

        atualizar_metricas(total, processados, duplicados, erros)
        time.sleep(0.3)
        if globals().get("PARAR_PROCESSAMENTO", False):
            apagar_fila_processamento()
            globals()["PARAR_PROCESSAMENTO"] = False
            log("Processamento parado. Fila de processamento apagada.")
            return

    atualizar_checkpoint_processamento(total, completed=True)
    progresso['value'] = 100
    log("Processamento finalizado.")
    tempo_total = formatar_duracao(time.time() - tempo_inicio_processamento)
    log(f"   Processados: {processados}")
    log(f"   Duplicados: {duplicados}")
    log(f"   Erros/Pendencias: {erros}")
    log(f"   Tempo total: {tempo_total}")
    if callable(mostrar_resultado_processamento):
        mostrar_resultado_processamento(processados, duplicados, erros, tempo_total)
    else:
        messagebox.showinfo("Concluido", f"Processados: {processados}\nDuplicados: {duplicados}\nErros/Pendencias: {erros}\nTempo: {tempo_total}")

frame_botoes = tk.Frame(janela)
frame_botoes.pack(pady=5)

btn_selecionar = tk.Button(frame_botoes, text="ðŸ“ Selecionar Pasta", command=escolher_pasta)
btn_selecionar.pack(side='left', padx=5)

btn_iniciar = tk.Button(frame_botoes, text="â–¶ Iniciar Processamento", command=iniciar_processamento)
btn_iniciar.pack(side='left', padx=5)

btn_exportar = tk.Button(frame_botoes, text="ðŸ“Š Baixar Excel", command=exportar_para_excel, bg="#e0f0e0")
btn_pendentes = tk.Button(frame_botoes, text="Reprocessar Pendentes", command=reprocessar_pendentes, bg="#fff2cc")
btn_pendentes.pack(side='left', padx=5)

btn_exportar.pack(side='left', padx=5)

btn_vitrine = tk.Button(frame_botoes, text="ðŸŒ Abrir Vitrine", command=abrir_vitrine, bg="#d0e0ff")
btn_vitrine.pack(side='left', padx=5)

btn_limpar = tk.Button(frame_botoes, text="ðŸ§¹ Limpar Shutterstock", command=limpar_shutterstock, bg="#ffcccc")
btn_limpar.pack(side='left', padx=5)

token_usuario = obter_token()
janela.mainloop()

