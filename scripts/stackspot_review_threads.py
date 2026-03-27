"""
scripts/stackspot_review_threads.py
"""

import os
import sys
import json
import glob
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

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
CYAN   = "\033[36m"
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


def revisar_arquivo(token, caminho, jest_info):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
    except Exception as e:
        return caminho, False, f"Nao consegui ler o arquivo: {e}"

    prompt = f"Output do Jest:\n{jest_info}\n\nArquivo: {caminho}\n{conteudo}"
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
    mensagem = r.json().get("message", "")
    reprovado = "reprovado" in mensagem.lower()
    return caminho, reprovado, mensagem


def main():
    token     = autenticar()
    arquivos  = coletar_arquivos()
    jest_info = carregar_jest()

    if not arquivos:
        print(f"{YELLOW}Nenhum arquivo encontrado para revisar.{RESET}")
        sys.exit(0)

    print(f"\nRevisando {len(arquivos)} arquivo(s) em paralelo...\n")
    for a in arquivos:
        print(f"   {CYAN}~ {a}{RESET}")
    print()

    resultados = []

    with ThreadPoolExecutor(max_workers=len(arquivos)) as executor:
        futures = {
            executor.submit(revisar_arquivo, token, caminho, jest_info): caminho
            for caminho in arquivos
        }
        for future in as_completed(futures):
            caminho, reprovado, mensagem = future.result()
            resultados.append((caminho, reprovado, mensagem))
            print("=" * 60)
            print(f"{BOLD}Arquivo: {caminho}{RESET}")
            print(mensagem)
            if reprovado:
                print(f"{BOLD}{RED}  FAIL  {caminho}{RESET}")
            else:
                print(f"{BOLD}{GREEN}  PASS  {caminho}{RESET}")
            print()

    reprovados = [c for c, rep, _ in resultados if rep]

    print("=" * 60)
    print(f"{BOLD}RESULTADO FINAL:{RESET}\n")
    for caminho, reprovado, _ in sorted(resultados, key=lambda x: x[0]):
        if reprovado:
            print(f"{RED}  x  {caminho}{RESET}")
        else:
            print(f"{GREEN}  v  {caminho}{RESET}")
    print()

    if reprovados:
        print(f"{BOLD}{RED}  FAIL  StackSpot AI{RESET}")
        print(f"{RED}    {len(reprovados)} arquivo(s) reprovado(s) — nao recomendado fazer o push.{RESET}")
        print(f"{RED}    Corrija os problemas acima e rode novamente.{RESET}\n")
        sys.exit(1)
    else:
        print(f"{BOLD}{GREEN}  PASS  StackSpot AI{RESET}")
        print(f"{GREEN}    v  Todos os arquivos aprovados — pode fazer o git push.{RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
