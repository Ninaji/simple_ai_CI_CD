"""
scripts/stackspot_review.py
"""

import os
import sys
import json
import glob
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

CLIENT_ID     = os.environ["STACKSPOT_CLIENT_ID"]
CLIENT_SECRET = os.environ["STACKSPOT_CLIENT_SECRET"]
REALM         = os.environ["STACKSPOT_REALM"]
AGENT_ID      = os.environ["STACKSPOT_AGENT_ID"]

AUTH_URL  = f"https://idm.stackspot.com/{REALM}/oidc/oauth/token"
AGENT_URL = f"https://genai-inference-app.stackspot.com/v1/agent/{AGENT_ID}/chat"

RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def carregar_reviewignore():
    """Le o .reviewignore e retorna um set de caminhos ignorados."""
    ignorados = set()
    try:
        with open(".reviewignore", "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if linha and not linha.startswith("#"):
                    # Normaliza separadores para comparacao cross-platform
                    ignorados.add(linha.replace("\\", "/"))
    except FileNotFoundError:
        pass
    return ignorados


def coletar_arquivos():
    ignorados = carregar_reviewignore()
    arquivos = []

    for caminho in glob.glob("**/js/**/*.js", recursive=True):
        if "node_modules" not in caminho:
            if caminho.replace("\\", "/") not in ignorados:
                arquivos.append(caminho)

    for caminho in glob.glob("**/scripts/**/*.py", recursive=True):
        if caminho.replace("\\", "/") not in ignorados:
            arquivos.append(caminho)

    return arquivos


def ler_arquivos(lista):
    if not lista:
        print(f"{YELLOW}AVISO: Nenhum arquivo encontrado para revisar.{RESET}")
        sys.exit(0)

    print("Arquivos encontrados para revisao:")
    codigo = ""
    for caminho in lista:
        print(f"   + {caminho}")
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                conteudo = f.read()
            codigo += f"\n\n{'─'*40}\nArquivo: {caminho}\n{'─'*40}\n{conteudo}"
        except Exception as e:
            print(f"{YELLOW}   AVISO: nao consegui ler {caminho}: {e}{RESET}")
    return codigo


def autenticar():
    print("Autenticando na StackSpot AI...")
    r = requests.post(
        AUTH_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
    )
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        print(f"{RED}ERRO: Token não retornado.{RESET}")
        sys.exit(1)
    print("Autenticado!")
    return token


def carregar_jest():
    try:
        with open("jest-results.json") as f:
            d = json.load(f)
        return (
            f"Resultado Jest: {d.get('numPassedTests',0)}/"
            f"{d.get('numTotalTests',0)} testes passaram. "
            f"Sucesso: {d.get('success', False)}"
        )
    except FileNotFoundError:
        return "Resultado Jest: nao encontrado."


def revisar(token, codigo, jest_info):
    print("\nEnviando para o agente StackSpot AI...")
    prompt = f"Output do Jest:\n{jest_info}\n\nArquivos:\n{codigo}"
    r = requests.post(
        AGENT_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "streaming": False,
            "user_prompt": prompt,
            "stackspot_knowledge": True,
            "return_ks_in_response": False,
        },
    )
    r.raise_for_status()
    return r.json().get("message", "")


def decidir(mensagem):
    print("\n" + "=" * 60)
    print(f"{BOLD}RESPOSTA DO AGENTE:{RESET}")
    print(mensagem)
    print("=" * 60 + "\n")

    lower = mensagem.lower()

    if "reprovado" in lower:
        print(f"{BOLD}{RED}  FAIL  StackSpot AI{RESET}")
        print(f"{RED}    x  Codigo reprovado — nao recomendado fazer o push.{RESET}")
        print(f"{RED}       Corrija os problemas acima e rode novamente.{RESET}\n")
        sys.exit(1)

    if "aprovado" in lower:
        print(f"{BOLD}{GREEN}  PASS  StackSpot AI{RESET}")
        print(f"{GREEN}    v  Codigo aprovado — pode fazer o git push.{RESET}\n")
        sys.exit(0)

    print(f"{YELLOW}  WARN  StackSpot AI — resposta ambigua, aprovando com ressalvas.{RESET}\n")
    sys.exit(0)


if __name__ == "__main__":
    token     = autenticar()
    arquivos  = coletar_arquivos()
    codigo    = ler_arquivos(arquivos)
    jest_info = carregar_jest()
    resposta  = revisar(token, codigo, jest_info)
    decidir(resposta)
