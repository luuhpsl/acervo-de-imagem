# Login e build do executavel

## Problema corrigido

O login podia abrir o navegador em `http://localhost:5000`, mas nao concluir a autenticacao. Isso acontecia quando as variaveis `FIREBASE_API_KEY` e `FIREBASE_APP_ID` estavam vazias ou nao eram carregadas antes da pagina de login.

## Solucao aplicada

O programa agora carrega automaticamente o arquivo `.env.local` antes de inicializar:

- servidor local de login (`auth_server.py`);
- logica principal do acervo (`catalogo_logic.py`);
- interface grafica (`main.py` / `gui.py`).

Se `.env.local` nao existir ou estiver incompleto, o codigo usa valores Firebase padrao do projeto `uniasselvi-digital`.

## Arquivo de ambiente

O arquivo esperado fica na pasta do programa ou ao lado do executavel:

```text
.env.local
```

Campos principais:

```text
FIREBASE_API_KEY=...
FIREBASE_APP_ID=...
```

O arquivo `.env.local.example` serve como modelo.

## E-mail do usuario

Tambem foi aplicado fallback para buscar o e-mail dentro de `providerUserInfo`, quando o Firebase Identity Toolkit nao retorna `email` no nivel principal da resposta.

## Gerar EXE com Nuitka

Use o arquivo:

```text
gerar_exe_nuitka.bat
```

Ele:

1. entra na pasta correta do programa;
2. cria `.env.local` a partir do exemplo se estiver ausente;
3. instala Nuitka se necessario;
4. gera o executavel em:

```text
executavel\nuitka\main.dist\Acervo-de-Imagens.exe
```

O build inclui icones, fontes, HTML da vitrine, regras Firebase, `auth_server.py`, `catalogo_logic.py`, `env_config.py` e `.env.local`.
