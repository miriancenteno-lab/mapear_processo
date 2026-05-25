# ✦ Appmax · Mapeamento de Processos — MVP

Ferramenta interna para mapeamento inteligente de processos manuais,
assistida por IA (Claude da Anthropic).

---

## 🚀 Deploy no Streamlit Cloud (passo a passo)

### 1. Pré-requisitos
- Conta no GitHub (gratuita): https://github.com
- Conta no Streamlit Cloud (gratuita): https://share.streamlit.io
- Chave da API Anthropic: https://console.anthropic.com/settings/keys

---

### 2. Subir o projeto no GitHub

```bash
# No terminal, dentro da pasta do projeto:
git init
git add .
git commit -m "feat: MVP Appmax Mapeamento de Processos"

# Criar repositório no GitHub e conectar:
git remote add origin https://github.com/SEU_USUARIO/appmax-mapeamento.git
git push -u origin main
```

---

### 3. Deploy no Streamlit Cloud

1. Acesse https://share.streamlit.io
2. Clique em **"New app"**
3. Conecte sua conta do GitHub
4. Selecione:
   - **Repository:** appmax-mapeamento
   - **Branch:** main
   - **Main file path:** app.py
5. Clique em **"Deploy!"**

---

### 4. Configurar a chave da API (OBRIGATÓRIO)

Sem essa etapa a IA não funciona.

1. No Streamlit Cloud, abra seu app
2. Clique em **"⋮" (três pontos)** → **"Settings"** → **"Secrets"**
3. Cole o conteúdo abaixo:

```toml
ANTHROPIC_API_KEY = "sk-ant-sua-chave-aqui"
```

4. Clique em **"Save"** → o app reinicia automaticamente

---

### 5. Compartilhar com usuários

Após o deploy, você terá uma URL no formato:
```
https://appmax-mapeamento-XXXX.streamlit.app
```

Compartilhe essa URL com os colaboradores.

**Credenciais de acesso padrão:**

| E-mail | Senha | Perfil |
|---|---|---|
| `demo@appmax.com.br` | `appmax2025` | Colaborador |
| `gestor@appmax.com.br` | `gestor2025` | Gestor (acesso ao dashboard) |

> ⚠️ Para produção, substitua os usuários hardcoded no arquivo `app.py`
> (seção `USERS`) pelos usuários reais da Appmax.

---

## 📁 Estrutura do projeto

```
appmax_mvp/
├── app.py                        # Aplicação principal
├── requirements.txt              # Dependências Python
├── .gitignore                    # Ignora secrets e cache
├── .streamlit/
│   ├── config.toml               # Tema visual Appmax
│   └── secrets.toml.example      # Template da chave de API
└── README.md                     # Este arquivo
```

---

## 🔐 Adicionar mais usuários

No `app.py`, localize a seção `USERS` e adicione:

```python
USERS = {
    "colaborador@appmax.com.br": {
        "pw": hash_pw("senha_escolhida"),
        "nome": "Nome Completo",
        "role": "user"          # "user" ou "gestor"
    },
    # ... outros usuários
}
```

---

## 💡 Funcionalidades do MVP

| Funcionalidade | Status |
|---|---|
| Login com e-mail e senha | ✅ |
| Cadastro de colaborador | ✅ |
| Job Descriptor com análise de IA | ✅ |
| Mapeamento passo a passo | ✅ |
| Validação de passo pela IA | ✅ |
| Geração de fluxograma BPMN | ✅ |
| Confirmação e sugestão de melhoria | ✅ |
| Histórico de mapeamentos por usuário | ✅ |
| Dashboard de gestão | ✅ |
| Perfis de acesso (user / gestor) | ✅ |
| Persistência em banco de dados | 🔜 Fase 2 |
| Exportação de relatórios | 🔜 Fase 2 |

---

## 📊 Custo estimado de IA

- ~US$ 0,11 por colaborador no ciclo completo
- ~US$ 11 para 100 colaboradores
- Modelo: `claude-sonnet-4-20250514` via Anthropic API
