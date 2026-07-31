import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import hashlib
import json
import time
import requests
import webbrowser
import uuid
from datetime import datetime
from auth_server import iniciar_servidor
import openai
import base64
import re
import unicodedata
from PIL import Image, ImageOps
import imagehash
import openpyxl
from openpyxl import Workbook
import subprocess

# ============================================================
# CONFIGURAÇÕES
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
PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "uniasselvi-digital")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "uniasselvi-digital.appspot.com")

# >>> SUA CHAVE OPENAI <<<
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "SUA_CHAVE_OPENAI_AQUI")

# Caminhos no Firestore
COLLECTION_PATH = "acervo-visual-unificado/default/images"
COUNTERS_COLLECTION = "acervo-visual-unificado/default/counters"

# Prefixos aceitos
PREFIXOS_ACEITOS = ('shutterstock_', 'envato-', 'pexels', 'freestock')

# Extensões permitidas (incluindo EPS e AI)
EXTENSOES_PERMITIDAS = ('.jpg', '.jpeg', '.png', '.ai', '.eps', '.svg')
EXTENSOES_VETORIAIS = ('.eps', '.ai', '.svg')
THUMBNAIL_MAX_SIZE = (600, 600)
DISPLAY_FILE_LIMIT = 1000
LOG_MAX_LINES = 500
QUEUE_CHECKPOINT_INTERVAL = 10

# Configura o cliente OpenAI
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ============================================================
# INTERFACE GRÁFICA
# ============================================================
janela = tk.Tk()
janela.title("Catálogo Inteligente de Imagens v2.2")
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

# Variáveis globais
arquivos_encontrados = []
token_usuario = None
email_usuario = None
ultimo_erro_openai = None
linha_log_varredura = None

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def log(mensagem):
    log_texto.config(state='normal')
    log_texto.insert(tk.END, mensagem + '\n')
    linhas = int(log_texto.index('end-1c').split('.')[0])
    if linhas > LOG_MAX_LINES:
        log_texto.delete('1.0', f'{linhas - LOG_MAX_LINES}.0')
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
    log_texto.see(tk.END)
    log_texto.config(state='disabled')
    janela.update_idletasks()

def atualizar_metricas(encontrados, processados, duplicados, erros, progresso_valor=None):
    lbl_encontrados.config(text=f"Encontrados: {encontrados}")
    lbl_processados.config(text=f"Processados: {processados}")
    lbl_duplicados.config(text=f"Duplicados: {duplicados}")
    lbl_erros.config(text=f"Erros: {erros}")
    if progresso_valor is not None:
        progresso['value'] = progresso_valor
    janela.update_idletasks()

# ============================================================
# CONVERSÃO EPS/AI PARA JPG (ImageMagick + Ghostscript)
# ============================================================
def converter_para_jpg(entrada, saida, densidade=300, qualidade=90):
    """
    Converte EPS ou AI para JPG usando ImageMagick.
    Seleciona apenas o primeiro frame ([0]) para evitar duplicatas.
    """
    if not os.path.exists(entrada):
        log(f"❌ Arquivo de entrada não encontrado: {entrada}")
        return False

    # Verifica qual comando está disponível (magick ou convert)
    try:
        subprocess.run(['magick', '-version'], check=True, capture_output=True)
        comando_base = 'magick'
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(['convert', '-version'], check=True, capture_output=True)
            comando_base = 'convert'
        except (subprocess.CalledProcessError, FileNotFoundError):
            log("❌ ImageMagick não encontrado. Instale e tente novamente.")
            return False

    if comando_base == 'magick':
        cmd = ['magick', 'convert']
    else:
        cmd = ['convert']

    # Adiciona [0] para pegar apenas o primeiro frame
    entrada_com_frame = entrada + "[0]"

    cmd.extend([
        '-density', str(densidade),
        '-background', 'white',
        '-flatten',
        '-trim',
        '-quality', str(qualidade),
        entrada_com_frame,
        saida
    ])

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        log(f"   ❌ Erro na conversão: {e.stderr}")
        return False

# ============================================================
# AUTENTICAÇÃO (FIREBASE)
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
            email = user.get('email', 'desconhecido')
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
                    log("✅ Token encontrado. Autenticando...")
                    email, verified = obter_informacoes_usuario(token_usuario)
                    if email:
                        email_usuario = email
                        log(f"👤 Usuário: {email} (verificado: {verified})")
                        if not verified:
                            log("⚠️ ATENÇÃO: Email não verificado. As regras exigem verificação.")
                        return token_usuario
                    else:
                        log("⚠️ Token inválido. Será solicitado novo login.")
                        token_usuario = None
        except Exception as e:
            log(f"⚠️ Erro ao ler token: {str(e)}")
            token_usuario = None

    log("🔑 Abrindo navegador para login...")
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
                            log(f"👤 Usuário: {email} (verificado: {verified})")
                            return token_usuario
            except Exception:
                pass
        time.sleep(1)
    messagebox.showerror("Erro", "Tempo limite para login.")
    return None

# ============================================================
# FUNÇÕES FIRESTORE E STORAGE
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
                            log(f"   🔍 Similaridade visual (distância: {distancia})")
                            return doc
                    except:
                        pass
        return None
    except Exception:
        return None

def obter_proximo_codigo(ano):
    if not token_usuario:
        return 1
    doc_path = f"{COUNTERS_COLLECTION}/{ano}"
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{doc_path}"
    headers = {"Authorization": f"Bearer {token_usuario}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            current = int(data['fields']['value']['integerValue'])
            novo_valor = current + 1
        else:
            create_body = {"fields": {"value": {"integerValue": 0}}}
            create_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{COUNTERS_COLLECTION}?documentId={ano}"
            create_headers = {**headers, "Content-Type": "application/json"}
            create_resp = requests.post(create_url, headers=create_headers, json=create_body)
            if create_resp.status_code not in (200, 201):
                return 1
            novo_valor = 1
        update_body = {"fields": {"value": {"integerValue": novo_valor}}}
        update_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{doc_path}?updateMask.fieldPaths=value"
        update_headers = {**headers, "Content-Type": "application/json"}
        update_resp = requests.patch(update_url, headers=update_headers, json=update_body)
        if update_resp.status_code not in (200, 201):
            return 1
        return novo_valor
    except Exception:
        return 1

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
            log(f"   ❌ Upload falhou: {response.status_code}")
            return None
    except Exception as e:
        log(f"   ❌ Exceção no upload: {str(e)}")
        return None

def gravar_no_firestore(dados, doc_id):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{COLLECTION_PATH}?documentId={doc_id}"
    headers = {
        "Authorization": f"Bearer {token_usuario}",
        "Content-Type": "application/json"
    }
    fields = {}
    for key, value in dados.items():
        if isinstance(value, bool):
            fields[key] = {"booleanValue": value}
        elif isinstance(value, str):
            fields[key] = {"stringValue": value}
        elif isinstance(value, int):
            fields[key] = {"integerValue": str(value)}
        elif isinstance(value, float):
            fields[key] = {"doubleValue": value}
        elif isinstance(value, list):
            fields[key] = {"arrayValue": {"values": [{"stringValue": v} for v in value]}}
        elif isinstance(value, dict):
            fields[key] = {"mapValue": {"fields": value}}
        else:
            fields[key] = {"nullValue": None}
    body = {"fields": fields}
    try:
        response = requests.post(url, headers=headers, json=body)
        if response.status_code in (200, 201):
            origem = str(dados.get("origem", "")).strip().lower()
            if origem and origem != "desconhecido":
                origem_url = (
                    f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/"
                    f"acervo-visual-unificado/{origem}/images?documentId={doc_id}"
                )
                origem_response = requests.post(origem_url, headers=headers, json=body)
                if origem_response.status_code in (200, 201):
                    log(f"   Espelho salvo no Firestore por origem: {origem}")
                else:
                    log(f"   Aviso: nao foi possivel salvar espelho por origem ({origem}): {origem_response.status_code}")
            log(f"   💾 Dados salvos no Firestore (ID: {doc_id})")
            return True
        else:
            log(f"   ❌ Erro ao salvar no Firestore: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log(f"   ❌ Exceção ao salvar no Firestore: {str(e)}")
        return False

# ============================================================
# FUNÇÃO PARA DELETAR ARQUIVO DO STORAGE
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
            log(f"   ❌ Erro ao deletar {caminho_completo}: {response.status_code}")
            return False
    except Exception as e:
        log(f"   ❌ Exceção ao deletar {caminho_completo}: {str(e)}")
        return False

# ============================================================
# LIMPEZA DE REGISTROS SHUTTERSTOCK
# ============================================================
def limpar_shutterstock():
    """Remove todos os registros e arquivos relacionados à origem 'shutterstock'."""
    if not token_usuario:
        messagebox.showerror("Erro", "Você precisa estar autenticado.")
        return

    log("🔍 Buscando documentos Shutterstock no Firestore...")
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{COLLECTION_PATH}"
    headers = {"Authorization": f"Bearer {token_usuario}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            log(f"❌ Erro ao buscar documentos: {response.status_code}")
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
        log(f"❌ Erro ao consultar Firestore: {str(e)}")
        return

    if not docs_para_excluir:
        log("✅ Nenhum documento Shutterstock encontrado. Nada a fazer.")
        return

    resposta = messagebox.askyesno(
        "Confirmação",
        f"Você está prestes a excluir {len(docs_para_excluir)} documentos e seus arquivos do Storage.\n\nEsta ação é irreversível. Deseja continuar?"
    )
    if not resposta:
        log("❌ Operação cancelada pelo usuário.")
        return

    log(f"🗑️ Iniciando exclusão de {len(docs_para_excluir)} documentos Shutterstock...")
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
                log(f"   ❌ Erro ao excluir documento {doc_id}: {resp_fire.status_code}")
                erros += 1
                continue
        except Exception as e:
            log(f"   ❌ Exceção ao excluir documento {doc_id}: {str(e)}")
            erros += 1
            continue

        # 2. Excluir arquivos do Storage
        caminho_thumbnail = f"acervo-visual-unificado/thumbnails/shutterstock/{ano}/{nome_amigavel}.jpg"
        caminho_original = f"acervo-visual-unificado/originals/{tipo_arquivo_original}/shutterstock/{ano}/{nome_amigavel}{extensao}"

        if False:
            log(f"   ⚠️ Não foi possível deletar visualização: {caminho_visualizacao}")
            erros += 1
        else:
            log(f"   ✅ Visualização removida: {caminho_visualizacao}")

        if not deletar_arquivo_storage(caminho_thumbnail):
            log(f"   Nao foi possivel deletar thumbnail: {caminho_thumbnail}")
            erros += 1
        elif False:
            log(f"   Thumbnail removida: {caminho_thumbnail}")

        if caminho_original:
            if not deletar_arquivo_storage(caminho_original):
                log(f"   ⚠️ Não foi possível deletar original: {caminho_original}")
                erros += 1
            else:
                log(f"   ✅ Original removido: {caminho_original}")

        deletados += 1

    log(f"🏁 Limpeza concluída: {deletados} documentos removidos, {erros} erros.")
    messagebox.showinfo("Limpeza", f"Documentos removidos: {deletados}\nErros: {erros}")

# ============================================================
# ANÁLISE COM OPENAI (CHATGPT VISION)
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

def testar_openai():
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Responda apenas: OK"}],
            max_tokens=10
        )
        return bool(resposta and resposta.choices)
    except Exception as e:
        log(f"❌ Falha ao conectar com OpenAI: {str(e)}")
        return False

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
        Analise esta imagem e retorne APENAS um JSON válido com os seguintes campos:
        {
            "tipo_imagem": "ex: fotografia, ilustração, vetor, etc",
            "elementos_visuais": "descreva os principais elementos visuais",
            "estilo_tecnica": "ex: realista, abstrato, aquarela, 3D, etc",
            "formato": "ex: retrato, paisagem, quadrado, etc",
            "cores_predominantes": "liste as 3-5 cores principais em português",
            "area_conhecimento": "ex: natureza, tecnologia, saúde, educação, etc",
            "caracteristicas": "características marcantes da imagem",
            "palavras_chave_pt": ["palavra1", "palavra2", ..., "palavra10"],
            "palavras_chave_en": ["keyword1", "keyword2", ..., "keyword10"],
            "descricao_detalhada": "descrição rica e detalhada em português"
        }
        Certifique-se de incluir EXATAMENTE 10 palavras-chave em cada lista.
        """
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
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
            max_tokens=600
        )
        texto_resposta = resposta.choices[0].message.content
        json_match = re.search(r'\{.*\}', texto_resposta, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            ultimo_erro_openai = "Resposta da IA nao contem JSON valido."
            log("   ⚠️ Resposta da IA não contém JSON válido.")
            return None
    except Exception as e:
        log(f"   ❌ Erro no OpenAI: {str(e)}")
        return None

def obter_resolucao(caminho):
    try:
        with Image.open(caminho) as img:
            return f"{img.width}x{img.height}"
    except:
        return "Desconhecida"

# ============================================================
# EXPORTAÇÃO PARA EXCEL
# ============================================================
def exportar_para_excel():
    if not token_usuario:
        messagebox.showerror("Erro", "Você precisa estar autenticado.")
        return
    log("📊 Buscando dados do Firestore para exportar...")
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{COLLECTION_PATH}"
    headers = {"Authorization": f"Bearer {token_usuario}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            log(f"❌ Erro ao buscar dados: {response.status_code}")
            return
        dados = response.json()
        documentos = dados.get('documents', [])
        if not documentos:
            log("⚠️ Nenhum documento encontrado no Firestore.")
            return
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Acervo"
        
        cabecalhos = [
            "Nome do Arquivo", "Link da Imagem", "Link Thumbnail", "Link Original", "Tipo da Imagem", "Elementos Visuais",
            "Estilo/Técnica", "Formato", "Cores Predominantes", "Área do Conhecimento",
            "Características", "Palavras-chave PT", "Palavras-chave EN", "Descrição",
            "Resolução da Imagem", "Tamanho (MB)", "Código (UUID)", "Nome Amigável",
            "Data de Processamento", "Origem"
        ]
        ws.append(cabecalhos)
        
        for doc in documentos:
            campos = doc.get('fields', {})
            def get_valor(campo):
                if campo not in campos:
                    return ""
                valor = campos[campo]
                if 'stringValue' in valor:
                    return valor['stringValue']
                elif 'integerValue' in valor:
                    return int(valor['integerValue'])
                elif 'doubleValue' in valor:
                    return float(valor['doubleValue'])
                elif 'arrayValue' in valor:
                    return ", ".join([v['stringValue'] for v in valor['arrayValue'].get('values', [])])
                return ""
            
            linha = [
                get_valor("nome_original"),
                get_valor("url_visualizacao"),
                get_valor("url_thumbnail"),
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
                get_valor("codigo"),
                get_valor("nome_amigavel"),
                get_valor("data_processamento"),
                get_valor("origem")
            ]
            ws.append(linha)
        
        nome_arquivo = f"acervo_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb.save(nome_arquivo)
        log(f"✅ Excel exportado com sucesso: {nome_arquivo}")
        messagebox.showinfo("Exportação", f"Arquivo salvo como:\n{nome_arquivo}")
    except Exception as e:
        log(f"❌ Erro na exportação: {str(e)}")

# ============================================================
# FUNÇÃO PARA ABRIR A VITRINE WEB
# ============================================================
def abrir_vitrine():
    VITRINE_URL = "http://localhost:8080"  # ou "https://uniasselvi-digital.web.app"
    log(f"🌐 Abrindo vitrine web em: {VITRINE_URL}")
    webbrowser.open(VITRINE_URL)

# ============================================================
# FUNÇÕES DE HASH E PROCESSAMENTO
# ============================================================
def calcular_hash_sha256(caminho):
    sha256 = hashlib.sha256()
    try:
        with open(caminho, 'rb') as f:
            for bloco in iter(lambda: f.read(4096), b''):
                sha256.update(bloco)
        return sha256.hexdigest()
    except Exception as e:
        log(f"❌ Erro ao ler {caminho}: {str(e)}")
        return None

def calcular_phash(caminho):
    try:
        img = Image.open(caminho)
        phash = imagehash.phash(img)
        return str(phash)
    except Exception as e:
        log(f"   ⚠️ Erro ao calcular pHash: {str(e)}")
        return None

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

    if not sufixo:
        return (0, len(nome), nome.lower())
    if not arquivo_parece_copia(caminho):
        return (1, len(nome), nome.lower())
    return (2, len(nome), nome.lower())

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
        log(f"Removidas {removidos} pendencias com arquivo local ausente.")
    if not arquivos_validos:
        messagebox.showwarning("Pendencias", "Nenhuma pendencia possui arquivo local acessivel.")
        return
    arquivos_encontrados, arquivos_ignorados = filtrar_copias_por_numeracao(arquivos_validos)
    if arquivos_ignorados:
        log(f"Ignoradas {len(arquivos_ignorados)} pendencias duplicadas por mesma numeracao.")
    lista_arquivos.delete(0, tk.END)
    for caminho in arquivos_encontrados[:DISPLAY_FILE_LIMIT]:
        lista_arquivos.insert(tk.END, caminho)
    if len(arquivos_encontrados) > DISPLAY_FILE_LIMIT:
        lista_arquivos.insert(tk.END, f"... mais {len(arquivos_encontrados) - DISPLAY_FILE_LIMIT} arquivos pendentes ocultos na lista visual")
    salvar_fila_processamento(arquivos_encontrados, pasta_origem="pendencias", next_index=0, completed=False)
    atualizar_metricas(len(arquivos_encontrados), 0, 0, 0, 0)
    log(f"Reprocessando {len(arquivos_encontrados)} pendencias.")
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
    log(f"📁 Varrendo: {pasta}")
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
    for caminho in arquivos_encontrados[:DISPLAY_FILE_LIMIT]:
        lista_arquivos.insert(tk.END, caminho)
    if arquivos_ignorados:
        log(f"Ignoradas {len(arquivos_ignorados)} copias/variacoes com a mesma numeracao.")
    log(f"✅ Encontrados {total} arquivos.")
    if total > DISPLAY_FILE_LIMIT:
        lista_arquivos.insert(tk.END, f"... mais {total - DISPLAY_FILE_LIMIT} arquivos ocultos na lista visual")
        log(f"Lista visual limitada aos primeiros {DISPLAY_FILE_LIMIT} arquivos para manter o programa leve.")
    arquivo_fila = salvar_fila_processamento(arquivos_encontrados, pasta_origem=pasta, next_index=0, completed=False)
    if arquivo_fila:
        log(f"Fila de processamento salva em: {arquivo_fila}")
    atualizar_metricas(total, 0, 0, 0, 0)

def iniciar_processamento_antigo_sem_fila():
    global token_usuario
    if not arquivos_encontrados:
        messagebox.showerror("Erro", "Selecione uma pasta primeiro.")
        return
    if not token_usuario:
        token_usuario = obter_token()
        if not token_usuario:
            return

    if OPENAI_API_KEY == "SUA_CHAVE_OPENAI_AQUI":
        log("❌ ERRO: Chave da OpenAI não configurada.")
        messagebox.showerror("Erro", "Configure sua chave da OpenAI.")
        return

    log("🔍 Testando conexão com OpenAI...")
    if not testar_openai():
        log("❌ Falha na conexão com OpenAI.")
        messagebox.showerror("Erro", "Não foi possível conectar ao OpenAI.")
        return
    else:
        log("✅ Conexão com OpenAI OK!")

    log("🚀 Iniciando processamento...")
    total = len(arquivos_encontrados)
    processados = 0
    duplicados = 0
    erros = 0
    ano = datetime.now().year

    for idx, caminho in enumerate(arquivos_encontrados):
        nome = os.path.basename(caminho)
        log(f"[{idx+1}/{total}] 📷 {nome}")
        progresso['value'] = (idx / total) * 100

        # --- DETECTAR ORIGEM ---
        origem = detectar_origem(nome)
        if origem == 'desconhecido':
            log(f"   ⚠️ Origem não identificada para {nome}. Pulando.")
            erros += 1
            continue

        # --- HASH SHA-256 ---
        hash_sha256 = calcular_hash_sha256(caminho)
        if not hash_sha256:
            erros += 1
            atualizar_metricas(total, processados, duplicados, erros)
            continue

        # --- DUPLICIDADE EXATA ---
        if consultar_hash_no_firestore(hash_sha256):
            remover_pendencia(hash_sha256)
            log(f"   ⏭️ DUPLICADO EXATO (SHA-256). Pulando.")
            duplicados += 1
            atualizar_metricas(total, processados, duplicados, erros)
            continue

        # --- pHASH (visual) ---
        phash_str = calcular_phash(caminho)
        if phash_str:
            doc_similar = consultar_phash_similar(phash_str, limite_distancia=5)
            if doc_similar:
                remover_pendencia(hash_sha256)
                log(f"   🔄 DUPLICATA VISUAL (pHash similar). Pulando.")
                duplicados += 1
                atualizar_metricas(total, processados, duplicados, erros)
                continue
        else:
            log("   ⚠️ Não foi possível calcular pHash.")

        # --- IDENTIFICADORES ---
        uuid_img = str(uuid.uuid4())
        numero = obter_proximo_codigo(ano)
        nome_amigavel = f"IMG-{ano}-{numero:06d}"
        extensao = os.path.splitext(caminho)[1].lower()

        # --- CONVERSÃO EPS/AI PARA JPG (se necessário) ---
        imagem_para_analise = caminho
        imagem_convertida_temp = None

        if extensao in ('.eps', '.ai'):
            # Cria um JPG temporário para análise
            imagem_convertida_temp = os.path.join(os.path.dirname(caminho), f"temp_{uuid_img}.jpg")
            log(f"   🔄 Convertendo {extensao} para JPG...")
            if converter_para_jpg(caminho, imagem_convertida_temp, densidade=300, qualidade=90):
                imagem_para_analise = imagem_convertida_temp
                log(f"   ✅ Conversão concluída.")
            else:
                log(f"   ❌ Falha na conversão. Pulando.")
                erros += 1
                continue

        # --- UPLOAD DA IMAGEM CONVERTIDA (visualização) ---
        # --- ANALISE COM OPENAI (antes do upload) ---
        log(f"   ðŸ¤– Analisando com ChatGPT Vision...")
        metadados = analisar_imagem_com_openai(imagem_para_analise)
        resolucao_original = obter_resolucao(caminho)
        resolucao_visualizacao = obter_resolucao(imagem_para_analise)
        resolucao = resolucao_original if resolucao_original != "Desconhecida" else resolucao_visualizacao

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

        log(f"   âœ… AnÃ¡lise OpenAI concluÃ­da!")

        destino_visualizacao = f"acervo-visual-unificado/images/{origem}/{ano}/{nome_amigavel}.jpg"
        log(f"   📤 Upload visualização: {destino_visualizacao}")
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
            destino_original = f"acervo-visual-unificado/originals/{origem}/{ano}/{nome_amigavel}{extensao}"
            log(f"   📤 Upload original: {destino_original}")
            url_original = fazer_upload_imagem(caminho, destino_original)

        # --- ANÁLISE COM OPENAI (usando a imagem convertida) ---
        log(f"   🤖 Analisando com ChatGPT Vision...")
        metadados = analisar_imagem_com_openai(imagem_para_analise)

        # --- REMOVE ARQUIVO TEMPORÁRIO (se existir) ---
        if imagem_convertida_temp and os.path.exists(imagem_convertida_temp):
            os.remove(imagem_convertida_temp)

        # --- METADADOS ADICIONAIS ---
        tamanho_mb = round(os.path.getsize(caminho) / (1024 * 1024), 2)
        resolucao = obter_resolucao(imagem_para_analise)

        # --- MONTAR DOCUMENTO FIRESTORE ---
        dados_documento = {
            "uuid": uuid_img,
            "codigo": uuid_img,
            "nome_amigavel": nome_amigavel,
            "nome_original": nome,
            "url_visualizacao": url_visualizacao,
            "url_original": url_original,
            "origem": origem,
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
            log(f"   ✅ Análise OpenAI concluída!")
        else:
            log(f"   ⚠️ Falha na análise. Dados salvos parcialmente.")

        # --- SALVAR NO FIRESTORE ---
        if gravar_no_firestore(dados_documento, uuid_img):
            processados += 1
        else:
            erros += 1

        atualizar_metricas(total, processados, duplicados, erros)
        time.sleep(0.3)

    progresso['value'] = 100
    log(f"🏁 Processamento finalizado!")
    log(f"   ✅ Processados: {processados}")
    log(f"   ⏭️ Duplicados: {duplicados}")
    log(f"   ❌ Erros: {erros}")
    messagebox.showinfo("Concluído", f"Processados: {processados}\nDuplicados: {duplicados}\nErros: {erros}")

# ============================================================
# CONSTRUÇÃO DA INTERFACE
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

        phash_str = calcular_phash(caminho)
        if phash_str:
            doc_similar = consultar_phash_similar(phash_str, limite_distancia=5)
            if doc_similar:
                remover_pendencia(hash_sha256)
                log("   DUPLICATA VISUAL (pHash similar). Pulando.")
                duplicados += 1
                atualizar_metricas(total, processados, duplicados, erros)
                continue
        else:
            log("   Nao foi possivel calcular pHash.")

        extensao = os.path.splitext(caminho)[1].lower()
        arquivos_temp = []
        fonte_visualizacao = caminho

        if extensao in EXTENSOES_VETORIAIS:
            temp_uuid = str(uuid.uuid4())
            imagem_convertida_temp = os.path.join(os.path.dirname(caminho), f"temp_{temp_uuid}.jpg")
            log(f"   Convertendo {extensao} para JPG...")
            if converter_para_jpg(caminho, imagem_convertida_temp, densidade=300, qualidade=90):
                fonte_visualizacao = imagem_convertida_temp
                arquivos_temp.append(imagem_convertida_temp)
                log("   Conversao concluida.")
            else:
                log("   Falha na conversao. Pulando.")
                erros += 1
                atualizar_metricas(total, processados, duplicados, erros)
                continue

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
        resolucao_visualizacao = obter_resolucao(imagem_para_analise)
        resolucao = resolucao_original if resolucao_original != "Desconhecida" else resolucao_visualizacao

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
        numero = obter_proximo_codigo(ano)
        nome_amigavel = f"IMG-{ano}-{numero:06d}"
        tipo_arquivo_original = detectar_tipo_arquivo_original(extensao)

        destino_thumbnail = f"acervo-visual-unificado/thumbnails/{origem}/{ano}/{nome_amigavel}.jpg"
        log(f"   Upload thumbnail: {destino_thumbnail}")
        url_thumbnail = fazer_upload_imagem(thumbnail_temp, destino_thumbnail)
        if not url_thumbnail:
            erros += 1
            for temp in arquivos_temp:
                if os.path.exists(temp):
                    os.remove(temp)
            atualizar_metricas(total, processados, duplicados, erros)
            continue
        url_visualizacao = url_thumbnail
        destino_visualizacao = destino_thumbnail

        destino_original = f"acervo-visual-unificado/originals/{tipo_arquivo_original}/{origem}/{ano}/{nome_amigavel}{extensao}"
        log(f"   Upload original: {destino_original}")
        url_original = fazer_upload_imagem(caminho, destino_original)
        if not url_original:
            deletar_arquivo_storage(destino_thumbnail)
            erros += 1
            for temp in arquivos_temp:
                if os.path.exists(temp):
                    os.remove(temp)
            atualizar_metricas(total, processados, duplicados, erros)
            continue

        for temp in arquivos_temp:
            if os.path.exists(temp):
                os.remove(temp)

        tamanho_mb = round(os.path.getsize(caminho) / (1024 * 1024), 2)
        dados_documento = {
            "uuid": uuid_img,
            "codigo": uuid_img,
            "nome_amigavel": nome_amigavel,
            "nome_original": nome,
            "url_visualizacao": url_visualizacao,
            "url_thumbnail": url_thumbnail,
            "url_original": url_original,
            "storage_visualizacao": destino_visualizacao,
            "storage_thumbnail": destino_thumbnail,
            "storage_original": destino_original,
            "origem": origem,
            "tipo_arquivo_original": tipo_arquivo_original,
            "sha256": hash_sha256,
            "phash": phash_str if phash_str else "",
            "extensao": extensao,
            "tamanho_mb": tamanho_mb,
            "resolucao": resolucao,
            "resolucao_visualizacao": resolucao_visualizacao,
            "data_processamento": datetime.now().isoformat(),
            "tipo_imagem": metadados.get("tipo_imagem", ""),
            "elementos_visuais": metadados.get("elementos_visuais", ""),
            "estilo_tecnica": metadados.get("estilo_tecnica", ""),
            "formato": metadados.get("formato", ""),
            "cores_predominantes": metadados.get("cores_predominantes", ""),
            "area_conhecimento": metadados.get("area_conhecimento", ""),
            "caracteristicas": metadados.get("caracteristicas", ""),
            "palavras_chave_pt": metadados.get("palavras_chave_pt", []),
            "palavras_chave_en": metadados.get("palavras_chave_en", []),
            "descricao_detalhada": metadados.get("descricao_detalhada", ""),
            "sheet_synced": False
        }

        if gravar_no_firestore(dados_documento, uuid_img):
            processados += 1
            remover_pendencia(hash_sha256)
        else:
            deletar_arquivo_storage(destino_thumbnail)
            deletar_arquivo_storage(destino_original)
            erros += 1

        atualizar_metricas(total, processados, duplicados, erros)
        time.sleep(0.3)

    atualizar_checkpoint_processamento(total, completed=True)
    progresso['value'] = 100
    log("Processamento finalizado.")
    log(f"   Processados: {processados}")
    log(f"   Duplicados: {duplicados}")
    log(f"   Erros/Pendencias: {erros}")
    messagebox.showinfo("Concluido", f"Processados: {processados}\nDuplicados: {duplicados}\nErros/Pendencias: {erros}")

frame_botoes = tk.Frame(janela)
frame_botoes.pack(pady=5)

btn_selecionar = tk.Button(frame_botoes, text="📁 Selecionar Pasta", command=escolher_pasta)
btn_selecionar.pack(side='left', padx=5)

btn_iniciar = tk.Button(frame_botoes, text="▶ Iniciar Processamento", command=iniciar_processamento)
btn_iniciar.pack(side='left', padx=5)

btn_exportar = tk.Button(frame_botoes, text="📊 Baixar Excel", command=exportar_para_excel, bg="#e0f0e0")
btn_pendentes = tk.Button(frame_botoes, text="Reprocessar Pendentes", command=reprocessar_pendentes, bg="#fff2cc")
btn_pendentes.pack(side='left', padx=5)

btn_exportar.pack(side='left', padx=5)

btn_vitrine = tk.Button(frame_botoes, text="🌐 Abrir Vitrine", command=abrir_vitrine, bg="#d0e0ff")
btn_vitrine.pack(side='left', padx=5)

btn_limpar = tk.Button(frame_botoes, text="🧹 Limpar Shutterstock", command=limpar_shutterstock, bg="#ffcccc")
btn_limpar.pack(side='left', padx=5)

token_usuario = obter_token()
janela.mainloop()
