# Git, GitHub e PowerShell

Remote oficial:

```text
https://github.com/DevEdTech/Acervo-de-Imagens.git
```

## 1. Verificar Git

```powershell
git --version
```

## 2. Configurar usuário do Git

Execute uma vez na máquina:

```powershell
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@empresa.com.br"
```

Conferir:

```powershell
git config --global --list
```

## 3. Entrar na pasta do projeto

```powershell
cd "C:\Users\lucas.silveira\Documents\Codex\2026-07-29\ol-chat-tenho-esse-programa-que\template-ia-python-master"
```

## 4. Inicializar Git, se necessário

Use apenas se a pasta ainda não tiver `.git`:

```powershell
git init
git branch -M main
```

Neste projeto, o repositório já foi inicializado.

## 5. Configurar remote

```powershell
git remote add origin https://github.com/DevEdTech/Acervo-de-Imagens.git
```

Se o remote já existir:

```powershell
git remote set-url origin https://github.com/DevEdTech/Acervo-de-Imagens.git
```

Conferir:

```powershell
git remote -v
```

## 6. Verificar alterações

```powershell
git status --short --branch
```

## 7. Adicionar arquivos

```powershell
git add .
```

Se quiser revisar antes:

```powershell
git diff
git diff --staged
```

## 8. Criar commit

```powershell
git commit -m "Atualiza documentação e fluxo do acervo"
```

## 9. Enviar para GitHub

Primeiro envio:

```powershell
git push -u origin main
```

Próximos envios:

```powershell
git push
```

## 10. Se pedir login

O GitHub não aceita mais senha comum no Git via HTTPS. Use uma das opções:

- autenticar pelo navegador quando o Git Credential Manager abrir;
- usar token de acesso pessoal;
- usar GitHub CLI, se instalado.

## 11. Comandos úteis

Ver histórico:

```powershell
git log --oneline --decorate -10
```

Ver arquivos modificados:

```powershell
git status
```

Desfazer arquivo ainda não commitado, com cuidado:

```powershell
git restore caminho\do\arquivo
```

Não use `git reset --hard` sem backup e confirmação.
