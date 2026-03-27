# StackSpot AI — Review Agent Template

Template de pipeline com revisao de codigo automatica via StackSpot AI.
Clone este repositorio como base para qualquer novo projeto.

---

## Estrutura do repositorio

```
.
├── .github/
│   └── workflows/
│       └── ci-cd.yml              <- Pipeline GitHub Actions
├── assets/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js                <- Arquivos JS revisados pelo agente
├── scripts/
│   ├── stackspot_review.py        <- Revisao concatenada (1 chamada)
│   └── stackspot_review_threads.py <- Revisao em paralelo (1 por arquivo)
├── tests/
│   └── xss.test.js                <- Testes Jest
├── .env.example                   <- Modelo do .env (sem credenciais)
├── .gitignore                     <- Ignora .env, node_modules, etc.
├── .reviewignore                  <- Arquivos ignorados pelo agente
├── index.html
├── package.json                   <- Scripts npm e config Jest
└── requirements.txt               <- Dependencias Python
```

---

## Secrets necessarios no GitHub

Va em **Settings -> Secrets and variables -> Actions** e adicione:

| Secret | Onde encontrar |
|---|---|
| `STACKSPOT_CLIENT_ID` | Portal StackSpot -> Settings -> Organization -> Service Credentials |
| `STACKSPOT_CLIENT_SECRET` | Portal StackSpot -> Settings -> Organization -> Service Credentials |
| `STACKSPOT_REALM` | Nome da sua organizacao (aparece na URL do portal) |
| `STACKSPOT_AGENT_ID` | Portal StackSpot -> Contents -> Agents -> seu agente -> API Usage |

---

## O que NAO sobe para o GitHub

Os arquivos abaixo estao no `.gitignore` e nunca devem ir ao repositorio:

```
.env               <- suas credenciais reais
node_modules/      <- instalado via npm install
jest-results.json  <- gerado automaticamente
coverage/          <- gerado pelo Jest
```

Sobe o `.env.example` no lugar do `.env`.
Qualquer pessoa que clonar o projeto copia o exemplo e preenche com suas proprias credenciais.

---

## Como usar este template em um novo projeto

### Opcao 1 — Template Repository (recomendado)

1. Acesse este repositorio no GitHub
2. Clique em **Use this template -> Create a new repository**
3. Defina o nome do novo projeto e clique em **Create repository**
4. Clone o novo repositorio:
   ```
   git clone https://github.com/SEU_USUARIO/NOVO_PROJETO.git
   cd NOVO_PROJETO
   ```
5. Instale as dependencias:
   ```
   npm install
   pip install -r requirements.txt
   ```
6. Crie o `.env` a partir do exemplo:
   ```
   cp .env.example .env
   ```
7. Preencha o `.env` com suas credenciais
8. Adicione os 4 Secrets no GitHub do novo repositorio

### Opcao 2 — Clone direto

```
git clone https://github.com/SEU_USUARIO/xss-lab.git meu-novo-projeto
cd meu-novo-projeto
npm install
pip install -r requirements.txt
cp .env.example .env
```

---

## Como marcar como Template Repository

1. Va em **Settings** do repositorio no GitHub
2. Na secao **General**, marque **Template repository**
3. Salve

A partir dai o botao **Use this template** aparece para qualquer repositorio novo.

---

## Comandos disponiveis

```
npm test                  -> roda os testes Jest
npm run review            -> agente revisa todos os arquivos (1 chamada)
npm run review:threads    -> agente revisa em paralelo (1 chamada por arquivo)
npm run pipeline          -> Jest + revisao concatenada
npm run pipeline:threads  -> Jest + revisao em paralelo
```

---

## Como subir o projeto pela primeira vez

```
git init
git add .
git commit -m "feat: setup inicial com stackspot review agent"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/xss-lab.git
git push -u origin main
```

Depois do push va em **Actions** no GitHub para acompanhar a pipeline rodando.

---

## O que o agente revisa

O agente analisa automaticamente:

- Todos os arquivos `.js` dentro de pastas `js/`
- Todos os arquivos `.py` dentro de pastas `scripts/`

Para ignorar arquivos especificos adicione o caminho no `.reviewignore`:

```
# .reviewignore
scripts/stackspot_review.py
scripts/stackspot_review_threads.py
assets/js/biblioteca-externa.js
```
