import streamlit as st
import json
import hashlib
import uuid
from datetime import datetime, date
from anthropic import Anthropic

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Appmax · Mapeamento de Processos",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CUSTOM CSS (Appmax palette) ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}
.stApp {
    background: #131326;
    color: #ffffff;
}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Top bar ── */
.appmax-header {
    background: rgba(19,19,38,0.97);
    border-bottom: 1px solid rgba(155,106,250,0.18);
    padding: 14px 36px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 999;
    backdrop-filter: blur(12px);
}
.appmax-logo {
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: #ffffff;
}
.appmax-logo span { color: #9B6AFA; }
.appmax-badge {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #AAEDFF;
    background: rgba(170,237,255,0.08);
    border: 1px solid rgba(170,237,255,0.22);
    padding: 4px 14px;
    border-radius: 100px;
}

/* ── Page wrapper ── */
.page-wrapper {
    max-width: 820px;
    margin: 0 auto;
    padding: 36px 24px 60px;
}

/* ── Step indicator ── */
.step-bar {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 28px;
}
.step-pip {
    height: 7px;
    border-radius: 100px;
    transition: all 0.3s;
}

/* ── Cards ── */
.card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(155,106,250,0.18);
    border-radius: 20px;
    padding: 28px 28px 24px;
    margin-bottom: 16px;
}
.card-title {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
    color: #ffffff;
}
.card-sub {
    font-size: 13px;
    color: #A8A7BC;
    margin-bottom: 22px;
    line-height: 1.6;
}

/* ── Section label ── */
.sec-label {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #9B6AFA;
    margin-bottom: 4px;
}

/* ── AI bubble ── */
.ai-bubble {
    background: rgba(170,237,255,0.06);
    border: 1px solid rgba(170,237,255,0.22);
    border-radius: 12px;
    padding: 13px 16px;
    font-size: 13px;
    color: #AAEDFF;
    line-height: 1.65;
    margin-top: 10px;
    margin-bottom: 6px;
}
.ai-bubble strong { color: #ffffff; }

/* ── Step chip ── */
.step-chip {
    background: rgba(155,106,250,0.08);
    border: 1px solid rgba(155,106,250,0.22);
    border-radius: 10px;
    padding: 11px 15px;
    margin-bottom: 8px;
    font-size: 13px;
    line-height: 1.55;
    color: #E6E0FC;
    display: flex;
    gap: 10px;
    align-items: flex-start;
}
.step-num {
    background: #45337C;
    color: #C4A6FD;
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    min-width: 22px;
    height: 22px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 1px;
}

/* ── BPMN box ── */
.bpmn-box {
    background: rgba(69,51,124,0.18);
    border: 1px solid rgba(155,106,250,0.28);
    border-radius: 14px;
    padding: 20px 22px;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    line-height: 1.9;
    color: #E6E0FC;
    white-space: pre-wrap;
    margin: 14px 0;
}

/* ── Success banner ── */
.success-banner {
    background: linear-gradient(135deg, rgba(155,106,250,0.14), rgba(69,51,124,0.2));
    border: 1px solid rgba(155,106,250,0.32);
    border-radius: 20px;
    padding: 40px 32px;
    text-align: center;
}
.success-icon { font-size: 48px; margin-bottom: 12px; }
.success-title {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 10px;
}
.success-sub {
    font-size: 14px;
    color: #A8A7BC;
    line-height: 1.7;
    max-width: 440px;
    margin: 0 auto 24px;
}
.summary-box {
    background: rgba(155,106,250,0.07);
    border-radius: 12px;
    padding: 16px 20px;
    text-align: left;
    max-width: 340px;
    margin: 0 auto 28px;
    font-size: 13px;
    line-height: 1.8;
    color: #E6E0FC;
}

/* ── Login page ── */
.login-wrap {
    min-height: 100vh;
    background: #131326;
    display: flex;
    align-items: center;
    justify-content: center;
}
.login-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(155,106,250,0.22);
    border-radius: 24px;
    padding: 44px 40px;
    width: 100%;
    max-width: 400px;
    text-align: center;
}
.login-logo {
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -1px;
    margin-bottom: 6px;
}
.login-logo span { color: #9B6AFA; }
.login-tagline {
    font-size: 13px;
    color: #A8A7BC;
    margin-bottom: 32px;
    line-height: 1.6;
}

/* ── Streamlit widget overrides ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(155,106,250,0.28) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(155,106,250,0.6) !important;
    box-shadow: 0 0 0 2px rgba(155,106,250,0.12) !important;
}
.stSelectbox > div > div { color: #ffffff !important; }
.stButton > button {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
    letter-spacing: 0.2px !important;
}
.stButton > button[kind="primary"],
.stButton > button:first-child {
    background: #9B6AFA !important;
    border: none !important;
    color: #ffffff !important;
}
.stButton > button[kind="primary"]:hover {
    background: #C4A6FD !important;
    color: #281E49 !important;
}
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid rgba(155,106,250,0.35) !important;
    color: #C4A6FD !important;
}
label, .stRadio label, .stCheckbox label {
    color: #C4A6FD !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.4px !important;
    text-transform: uppercase !important;
}
.stRadio > div { gap: 8px !important; }
.stRadio > div > label {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(155,106,250,0.22) !important;
    border-radius: 100px !important;
    padding: 7px 18px !important;
    text-transform: none !important;
    font-size: 13px !important;
    letter-spacing: 0 !important;
    color: #A8A7BC !important;
    font-weight: 400 !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
}
.stRadio > div > label:has(input:checked) {
    background: rgba(155,106,250,0.15) !important;
    border-color: #9B6AFA !important;
    color: #C4A6FD !important;
    font-weight: 600 !important;
}
.stNumberInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(155,106,250,0.28) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
}
.stDateInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(155,106,250,0.28) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
}
div[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}
.stAlert {
    border-radius: 12px !important;
}
hr {
    border-color: rgba(155,106,250,0.15) !important;
    margin: 20px 0 !important;
}
</style>
""", unsafe_allow_html=True)


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def tempo_empresa(data_ingresso: date) -> str:
    hoje = date.today()
    meses = (hoje.year - data_ingresso.year) * 12 + (hoje.month - data_ingresso.month)
    if meses < 12:
        return f"{meses} meses"
    anos = meses // 12
    m = meses % 12
    return f"{anos} ano{'s' if anos > 1 else ''} e {m} meses" if m else f"{anos} ano{'s' if anos > 1 else ''}"

def get_client() -> Anthropic:
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        api_key = st.session_state.get("api_key_manual", "")
    if not api_key:
        st.error("⚠️ Chave da API não encontrada. Configure ANTHROPIC_API_KEY nos Secrets.")
        st.stop()
    return Anthropic(api_key=api_key)

def call_claude(system: str, user_msg: str) -> str:
    try:
        client = get_client()
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        return msg.content[0].text
    except Exception as e:
        return f"⚠️ Erro na IA: {str(e)}"

def init_storage():
    """Inicializa estrutura de dados na sessão."""
    if "db" not in st.session_state:
        st.session_state.db = {
            "usuarios": {},       # email → {dados}
            "mapeamentos": [],    # lista de processos mapeados
        }

def save_mapeamento(usuario, job_desc, processo):
    init_storage()
    st.session_state.db["mapeamentos"].append({
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().isoformat(),
        "usuario": usuario,
        "job_descriptor": job_desc,
        "processo": processo,
    })

def header(usuario=None):
    user_info = f"<span style='font-size:13px;color:#A8A7BC;'>👤 {usuario['nome']} · {usuario['time']}</span>" if usuario else ""
    st.markdown(f"""
    <div class='appmax-header'>
        <div class='appmax-logo'><span>A</span>ppmax &nbsp;·&nbsp; <span style='font-weight:300;font-size:15px;color:#A8A7BC;'>Mapeamento de Processos</span></div>
        <div style='display:flex;align-items:center;gap:16px;'>
            {user_info}
            <span class='appmax-badge'>✦ IA ativa</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def step_indicator(current: int, total: int, labels: list):
    html = "<div class='step-bar'>"
    for i in range(total):
        if i < current:
            color, width = "#9B6AFA", "28px"
        elif i == current:
            color, width = "#C4A6FD", "40px"
        else:
            color, width = "rgba(155,106,250,0.2)", "8px"
        html += f"<div class='step-pip' style='background:{color};width:{width};'></div>"
    label = labels[current] if current < len(labels) else ""
    html += f"<span style='font-family:monospace;font-size:11px;color:#A8A7BC;margin-left:8px;letter-spacing:1px;'>{current+1}/{total} · {label}</span>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ─── LOGIN ────────────────────────────────────────────────────────────────────
USERS = {
    "demo@appmax.com.br": {"pw": hash_pw("appmax2025"), "nome": "Demo User", "role": "user"},
    "gestor@appmax.com.br": {"pw": hash_pw("gestor2025"), "nome": "Gestor Appmax", "role": "gestor"},
}

def page_login():
    st.markdown("""
    <div style='min-height:100vh;display:flex;align-items:center;justify-content:center;padding:40px 20px;'>
        <div style='text-align:center;width:100%;max-width:420px;'>
            <div style='font-size:28px;font-weight:700;letter-spacing:-1px;margin-bottom:8px;'>
                <span style='color:#9B6AFA;'>A</span>ppmax
            </div>
            <div style='font-size:13px;color:#A8A7BC;margin-bottom:36px;line-height:1.6;'>
                Mapeamento Inteligente de Processos
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:16px;font-weight:700;margin-bottom:20px;text-align:center;'>Entrar na plataforma</div>", unsafe_allow_html=True)

        email = st.text_input("E-mail", placeholder="seu@appmax.com.br", key="login_email")
        senha = st.text_input("Senha", type="password", placeholder="••••••••", key="login_senha")

        if st.button("Entrar →", use_container_width=True, type="primary"):
            u = USERS.get(email.lower().strip())
            if u and u["pw"] == hash_pw(senha):
                st.session_state.logged_in = True
                st.session_state.login_email = email.lower().strip()
                st.session_state.login_role = u["role"]
                st.session_state.login_nome = u["nome"]
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos.")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:11px;color:#A8A7BC;text-align:center;line-height:1.8;'>Acesso demo:<br><code style='color:#9B6AFA;'>demo@appmax.com.br</code> / <code style='color:#9B6AFA;'>appmax2025</code><br><code style='color:#9B6AFA;'>gestor@appmax.com.br</code> / <code style='color:#9B6AFA;'>gestor2025</code></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ─── STEP 1: CADASTRO ────────────────────────────────────────────────────────
def step_cadastro():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>👤 Cadastro</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-sub'>Preencha seus dados para iniciar o mapeamento de processos.</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome completo", key="cad_nome")
        time_sel = st.selectbox("Time / Departamento", [
            "", "Produto", "Engenharia", "People & Culture", "Operações",
            "Comercial", "Marketing", "Financeiro", "CS", "TI", "Jurídico", "Outro"
        ], key="cad_time")
        funcao = st.text_input("Função que você exerce hoje (na prática)", key="cad_funcao",
                               placeholder="Ex: Analista de Suporte e Operações")
    with col2:
        email = st.text_input("E-mail corporativo", key="cad_email",
                              value=st.session_state.get("login_email", ""))
        cargo = st.text_input("Cargo formal", key="cad_cargo",
                              placeholder="Ex: Analista de Operações Pleno")
        data_ing = st.date_input("Data de ingresso na empresa", key="cad_data",
                                 min_value=date(2000, 1, 1), max_value=date.today(),
                                 value=date(2022, 1, 1))

    if data_ing:
        t = tempo_empresa(data_ing)
        st.markdown(f"<div style='font-size:11px;color:#AAEDFF;font-family:monospace;margin-top:-10px;margin-bottom:6px;'>⏱ {t} de empresa</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    ok = all([nome, email, time_sel, cargo, funcao])
    if st.button("Continuar →", type="primary", disabled=not ok, key="btn_cad"):
        st.session_state.usuario = {
            "nome": nome, "email": email, "time": time_sel,
            "cargo": cargo, "funcao": funcao,
            "data_ingresso": data_ing.isoformat(),
            "tempo_empresa": tempo_empresa(data_ing),
        }
        st.session_state.step = 1
        st.rerun()


# ─── STEP 2: JOB DESCRIPTOR ──────────────────────────────────────────────────
def step_job_descriptor():
    u = st.session_state.usuario

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>📋 Job Descriptor Real</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card-sub'>Descreva uma atividade principal que você realiza hoje, <strong style='color:#C4A6FD;'>{u['nome']}</strong>.</div>", unsafe_allow_html=True)

    tarefa = st.text_area("Tarefa realizada", max_chars=200, key="jd_tarefa",
                          placeholder="Ex: Consolido relatórios semanais de performance das campanhas de marketing",
                          height=80)
    col1, col2 = st.columns(2)
    with col1:
        ferramenta = st.text_input("Ferramenta ou sistema utilizado", key="jd_ferramenta",
                                   placeholder="Ex: Google Sheets, Salesforce, Notion...")
        motivo = st.text_input("Por que você realiza essa tarefa?", key="jd_motivo",
                               placeholder="Qual o motivo desta tarefa existir?")
    with col2:
        problema = st.text_area("Qual problema essa tarefa resolve?", key="jd_problema",
                                placeholder="Descreva o problema que ela resolve...", height=101)

    impacto_opts = ["Empresa", "Parceiros", "Meu time", "Outros times"]
    impacto = st.multiselect("Se você parar hoje, quem é impactado?", impacto_opts, key="jd_impacto")
    impacto_desc = st.text_area("Descreva o impacto em detalhes", key="jd_impacto_desc",
                                placeholder="Quais são as consequências concretas?", height=70)
    mensura = st.radio("Consegue mensurar o impacto financeiro?",
                       ["Sim", "Não", "Parcialmente"], horizontal=True, key="jd_mensura")

    # IA feedback
    if tarefa and ferramenta and st.button("✦ Analisar com IA", key="btn_ia_jd"):
        with st.spinner("Analisando..."):
            resp = call_claude(
                "Você é especialista em análise de processos corporativos. Avalie a descrição de uma tarefa de um colaborador em 2-3 frases curtas e construtivas sobre clareza e completude. Responda em português brasileiro.",
                f"Colaborador: {u['nome']} ({u['cargo']} - {u['time']})\nTarefa: \"{tarefa}\"\nFerramenta: \"{ferramenta}\"\nMotivo: \"{motivo}\""
            )
        st.markdown(f"<div class='ai-bubble'>✦ {resp}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    col_back, col_next = st.columns([1, 3])
    with col_back:
        if st.button("← Voltar", key="btn_jd_back"):
            st.session_state.step = 0
            st.rerun()
    with col_next:
        ok = bool(tarefa and ferramenta)
        if st.button("Continuar para Mapeamento →", type="primary", disabled=not ok, key="btn_jd_next"):
            st.session_state.job_descriptor = {
                "tarefa": tarefa, "ferramenta": ferramenta, "motivo": motivo,
                "problema": problema, "impacto": impacto,
                "impacto_desc": impacto_desc, "mensura": mensura,
            }
            st.session_state.step = 2
            st.session_state.passos = []
            st.session_state.meta_processo = {}
            st.session_state.bpmn_gerado = ""
            st.session_state.fase_mapeamento = "meta"
            st.rerun()


# ─── STEP 3: MAPEAMENTO ───────────────────────────────────────────────────────
def step_mapeamento():
    fase = st.session_state.get("fase_mapeamento", "meta")

    # ── FASE META ──
    if fase == "meta":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>🗺️ Mapeamento de Processo</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-sub'>Classifique e caracterize o que você vai mapear agora.</div>", unsafe_allow_html=True)

        tipo = st.radio("Tipo", [
            "⚡ Tarefa — Ação isolada e pontual",
            "🔄 Processo — Conjunto de tarefas sequenciais"
        ], key="mp_tipo")
        tipo_clean = "Tarefa" if "Tarefa" in tipo else "Processo"

        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input(f"Nome d{'a' if tipo_clean == 'Tarefa' else 'o'} {tipo_clean}", key="mp_nome",
                                 placeholder="Ex: Envio de relatório semanal")
            freq = st.selectbox("Frequência", ["", "Diária", "Semanal", "Quinzenal", "Mensal", "Esporádica"], key="mp_freq")
        with col2:
            ferramenta = st.text_input("Ferramenta ou sistema principal", key="mp_ferramenta",
                                       placeholder="Ex: Google Drive, Slack, SAP...")
            if freq and freq != "Esporádica":
                vezes = st.number_input(f"Quantas vezes por semana/mês?", min_value=1, max_value=99,
                                        value=1, key="mp_vezes")
            elif freq == "Esporádica":
                gatilho = st.text_input("O que desencadeia essa atividade?", key="mp_gatilho",
                                        placeholder="Ex: Solicitação do cliente, abertura de chamado...")

        st.markdown("</div>", unsafe_allow_html=True)

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Voltar", key="btn_mp_back"):
                st.session_state.step = 1
                st.rerun()
        with col_next:
            ok = bool(nome and freq)
            if st.button("Começar a mapear os passos →", type="primary", disabled=not ok, key="btn_mp_meta"):
                st.session_state.meta_processo = {
                    "tipo": tipo_clean,
                    "nome": nome,
                    "ferramenta": ferramenta,
                    "freq": freq,
                    "vezes": st.session_state.get("mp_vezes", 1) if freq != "Esporádica" else None,
                    "gatilho": st.session_state.get("mp_gatilho", "") if freq == "Esporádica" else "",
                }
                st.session_state.passos = []
                st.session_state.fase_mapeamento = "steps"
                st.rerun()

    # ── FASE STEPS ──
    elif fase == "steps":
        meta = st.session_state.meta_processo
        passos = st.session_state.passos

        st.markdown(f"""
        <div class='card'>
            <div class='card-title'>📝 Passos do {meta['tipo']}</div>
            <div class='card-sub'>
                <strong style='color:#C4A6FD;'>{meta['nome']}</strong>
                &nbsp;·&nbsp; {meta['tipo']} &nbsp;·&nbsp; {meta['freq']}
                &nbsp;·&nbsp; <span style='color:#A8A7BC;'>{len(passos)} passo{'s' if len(passos)!=1 else ''} registrado{'s' if len(passos)!=1 else ''}</span>
            </div>
        """, unsafe_allow_html=True)

        # Passos já registrados
        if passos:
            for i, p in enumerate(passos):
                st.markdown(f"""
                <div class='step-chip'>
                    <div class='step-num'>{str(i+1).zfill(2)}</div>
                    <div>{p}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        # Novo passo
        num_prox = len(passos) + 1
        novo = st.text_area(
            f"Passo {num_prox}" if passos else "Descreva o 1º passo",
            key=f"step_input_{num_prox}",
            placeholder="Descreva detalhadamente o que você faz neste passo...",
            max_chars=200,
            height=80,
        )

        # Validação IA
        if novo and len(novo.strip()) > 15:
            if st.button("✦ Validar passo com IA", key=f"btn_ia_step_{num_prox}"):
                with st.spinner("Analisando clareza do passo..."):
                    resp = call_claude(
                        f"Você é especialista em mapeamento de processos BPMN. Avalie se o passo está claro o suficiente. Se não estiver, faça 1 ou 2 perguntas objetivas de refinamento. Se estiver claro, responda apenas: '✓ Passo claro, pode continuar.' Seja muito conciso. Responda em português.",
                        f"Processo: \"{meta['nome']}\" ({meta['tipo']}). Passos anteriores: {len(passos)}.\nNovo passo: \"{novo.strip()}\""
                    )
                st.markdown(f"<div class='ai-bubble'>✦ {resp}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 1.5])
        with col1:
            if st.button("+ Salvar passo", type="primary", disabled=not novo.strip(), key=f"btn_salvar_{num_prox}"):
                st.session_state.passos.append(novo.strip())
                st.rerun()
        with col2:
            if passos and st.button("↩ Remover último", key="btn_remove"):
                st.session_state.passos.pop()
                st.rerun()
        with col3:
            if len(passos) >= 2:
                if st.button("Finalizar e gerar fluxograma ✦", key="btn_finalizar"):
                    st.session_state.fase_mapeamento = "gerando"
                    st.rerun()

        if len(passos) < 2:
            st.markdown("<div style='font-size:12px;color:#A8A7BC;margin-top:8px;'>💡 Adicione pelo menos 2 passos para finalizar.</div>", unsafe_allow_html=True)

    # ── FASE GERANDO BPMN ──
    elif fase == "gerando":
        meta = st.session_state.meta_processo
        passos = st.session_state.passos

        with st.spinner("✦ Gerando fluxograma BPMN..."):
            passos_txt = "\n".join([f"{i+1}. {p}" for i, p in enumerate(passos)])
            bpmn = call_claude(
                "Você é especialista em notação BPMN. Crie um fluxograma textual claro no estilo BPMN com: 🟢 Início → etapas → 🔴 Fim. Use emojis: 🟢 Início, 🔵 Tarefa, 🔷 Decisão/Condição, 🔴 Fim. Cada elemento em uma linha com seta →. Seja visual e claro. Responda APENAS o fluxograma, sem explicações extras.",
                f"Processo: \"{meta['nome']}\" ({meta['tipo']})\nPassos:\n{passos_txt}"
            )
            st.session_state.bpmn_gerado = bpmn
            st.session_state.fase_mapeamento = "confirm"
            st.rerun()

    # ── FASE CONFIRMAÇÃO ──
    elif fase == "confirm":
        meta = st.session_state.meta_processo
        passos = st.session_state.passos
        bpmn = st.session_state.bpmn_gerado

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>✦ Fluxograma Gerado</div>", unsafe_allow_html=True)
        st.markdown("<div class='card-sub'>A IA criou o fluxograma abaixo com base nos passos que você descreveu. Confira se está correto.</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='bpmn-box'>{bpmn}</div>", unsafe_allow_html=True)

        confirmado = st.radio(
            f"O fluxograma corresponde ao {meta['tipo'].lower()} que você realiza hoje?",
            ["✓ Sim, está correto", "✗ Faltou algo"], horizontal=True, key="bpmn_confirm"
        )

        faltou = ""
        if "Faltou" in confirmado:
            faltou = st.text_area("Qual passo faltou incluir?", key="bpmn_faltou",
                                  placeholder="Descreva o que não foi capturado no fluxograma...", height=80)

        st.markdown("<hr>", unsafe_allow_html=True)
        sugestao = st.text_area(
            "💡 Você tem alguma sugestão de melhoria para essa demanda?",
            key="bpmn_sugestao",
            placeholder="Opcional: ideia de automação, simplificação ou melhoria do processo...",
            height=70,
        )

        st.markdown("</div>", unsafe_allow_html=True)

        col_back, col_save = st.columns([1, 3])
        with col_back:
            if st.button("← Editar passos", key="btn_edit_steps"):
                st.session_state.fase_mapeamento = "steps"
                st.rerun()
        with col_save:
            if st.button("Salvar e finalizar ✓", type="primary", key="btn_save_final"):
                processo = {
                    **meta,
                    "passos": passos,
                    "bpmn": bpmn,
                    "confirmado": "Sim" if "Sim" in confirmado else "Não",
                    "faltou": faltou,
                    "sugestao": sugestao,
                }
                save_mapeamento(
                    st.session_state.usuario,
                    st.session_state.job_descriptor,
                    processo,
                )
                st.session_state.processo_salvo = processo
                st.session_state.step = 3
                st.rerun()


# ─── STEP 4: SUCESSO ─────────────────────────────────────────────────────────
def step_sucesso():
    u = st.session_state.usuario
    p = st.session_state.processo_salvo

    st.markdown(f"""
    <div class='success-banner'>
        <div class='success-icon'>✦</div>
        <div class='success-title'>Processo mapeado com sucesso!</div>
        <div class='success-sub'>
            <strong style='color:#C4A6FD;'>{p['nome']}</strong> ({p['tipo']}) foi registrado
            com <strong style='color:#ffffff;'>{len(p['passos'])} passos</strong> e o fluxograma foi gerado.
            {'Sua sugestão de melhoria foi registrada.' if p.get('sugestao') else ''}
        </div>
        <div class='summary-box'>
            <div style='font-family:monospace;font-size:10px;color:#A8A7BC;letter-spacing:1px;text-transform:uppercase;margin-bottom:10px;'>Resumo salvo</div>
            👤 {u['nome']} · {u['time']}<br>
            📌 {p['tipo']}: {p['nome']}<br>
            📅 {p['freq']} · {len(p['passos'])} passos<br>
            🛠️ {p.get('ferramenta', '—')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("+ Mapear outro processo", type="primary", use_container_width=True):
            st.session_state.step = 2
            st.session_state.fase_mapeamento = "meta"
            st.session_state.passos = []
            st.session_state.bpmn_gerado = ""
            st.rerun()
    with col2:
        if st.button("Ver todos os mapeamentos", use_container_width=True):
            st.session_state.step = 10
            st.rerun()


# ─── PÁGINA GESTÃO ────────────────────────────────────────────────────────────
def page_gestao():
    init_storage()
    dados = st.session_state.db.get("mapeamentos", [])

    st.markdown("<div class='page-wrapper'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-label'>Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:26px;font-weight:700;letter-spacing:-1px;margin-bottom:4px;'>Visão de Gestão</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:13px;color:#A8A7BC;margin-bottom:28px;'>{len(dados)} mapeamento{'s' if len(dados)!=1 else ''} registrado{'s' if len(dados)!=1 else ''} na sessão atual</div>", unsafe_allow_html=True)

    if not dados:
        st.markdown("<div class='ai-bubble'>ℹ️ Nenhum mapeamento registrado ainda nesta sessão. Faça login como usuário e mapeie alguns processos para ver os dados aqui.</div>", unsafe_allow_html=True)
    else:
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        times = set(d["usuario"]["time"] for d in dados)
        total_passos = sum(len(d["processo"]["passos"]) for d in dados)
        ferramentas = set(d["processo"].get("ferramenta","") for d in dados if d["processo"].get("ferramenta"))
        with col1:
            st.metric("Mapeamentos", len(dados))
        with col2:
            st.metric("Times ativos", len(times))
        with col3:
            st.metric("Total de passos", total_passos)
        with col4:
            st.metric("Ferramentas únicas", len(ferramentas))

        st.markdown("<hr>", unsafe_allow_html=True)

        # Lista de mapeamentos
        st.markdown("<div style='font-size:14px;font-weight:600;color:#C4A6FD;margin-bottom:14px;'>Processos Mapeados</div>", unsafe_allow_html=True)
        for d in reversed(dados):
            u = d["usuario"]
            p = d["processo"]
            ts = d["timestamp"][:16].replace("T", " às ")
            with st.expander(f"📌 {p['nome']} — {u['nome']} ({u['time']}) · {ts}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Tipo:** {p['tipo']}  \n**Frequência:** {p['freq']}  \n**Ferramenta:** {p.get('ferramenta','—')}")
                with col_b:
                    st.markdown(f"**Passos:** {len(p['passos'])}  \n**Confirmado:** {p.get('confirmado','—')}  \n**Cargo:** {u['cargo']}")

                st.markdown("**Passos mapeados:**")
                for i, s in enumerate(p["passos"]):
                    st.markdown(f"`{str(i+1).zfill(2)}` {s}")

                if p.get("sugestao"):
                    st.markdown(f"**💡 Sugestão de melhoria:** {p['sugestao']}")

                st.markdown("**Fluxograma BPMN gerado:**")
                st.code(p.get("bpmn", "—"), language=None)

        # Ferramentas mais citadas
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:14px;font-weight:600;color:#C4A6FD;margin-bottom:10px;'>Ferramentas Mais Utilizadas</div>", unsafe_allow_html=True)
        from collections import Counter
        ferr_list = [d["processo"].get("ferramenta", "") for d in dados if d["processo"].get("ferramenta")]
        if ferr_list:
            for ferr, count in Counter(ferr_list).most_common(8):
                pct = int(count / len(ferr_list) * 100)
                st.markdown(f"""
                <div style='display:flex;align-items:center;gap:12px;margin-bottom:8px;'>
                    <div style='font-size:13px;color:#E6E0FC;min-width:160px;'>{ferr}</div>
                    <div style='flex:1;background:rgba(155,106,250,0.1);border-radius:100px;height:6px;'>
                        <div style='width:{pct}%;background:#9B6AFA;height:6px;border-radius:100px;'></div>
                    </div>
                    <div style='font-size:12px;color:#A8A7BC;min-width:30px;'>{count}x</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ─── HISTÓRICO USUÁRIO ────────────────────────────────────────────────────────
def page_historico():
    init_storage()
    email = st.session_state.get("login_email", "")
    meus = [d for d in st.session_state.db["mapeamentos"] if d["usuario"]["email"] == email]

    st.markdown("<div class='page-wrapper'>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:22px;font-weight:700;letter-spacing:-0.5px;margin-bottom:20px;'>Meus Mapeamentos <span style='font-size:14px;color:#A8A7BC;font-weight:400;'>({len(meus)} registros)</span></div>", unsafe_allow_html=True)

    if not meus:
        st.markdown("<div class='ai-bubble'>ℹ️ Você ainda não mapeou nenhum processo. Clique em 'Novo Mapeamento' para começar.</div>", unsafe_allow_html=True)
    else:
        for d in reversed(meus):
            p = d["processo"]
            ts = d["timestamp"][:16].replace("T", " às ")
            with st.expander(f"📌 {p['nome']} · {p['tipo']} · {ts}"):
                st.markdown(f"**Frequência:** {p['freq']}  \n**Ferramenta:** {p.get('ferramenta','—')}  \n**Passos:** {len(p['passos'])}")
                for i, s in enumerate(p["passos"]):
                    st.markdown(f"`{str(i+1).zfill(2)}` {s}")
                st.code(p.get("bpmn", ""), language=None)

    if st.button("+ Novo Mapeamento", type="primary"):
        st.session_state.step = 2
        st.session_state.fase_mapeamento = "meta"
        st.session_state.passos = []
        st.session_state.bpmn_gerado = ""
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    init_storage()

    # Auth
    if not st.session_state.get("logged_in"):
        page_login()
        return

    role = st.session_state.get("login_role", "user")
    nome = st.session_state.get("login_nome", "")

    # Header
    usuario_hdr = st.session_state.get("usuario") or {"nome": nome, "time": role.title()}
    header(usuario_hdr)

    # Sidebar nav
    with st.sidebar:
        st.markdown(f"<div style='font-size:16px;font-weight:700;color:#C4A6FD;margin-bottom:20px;'>Olá, {nome.split()[0]} 👋</div>", unsafe_allow_html=True)
        if st.button("✦ Novo Mapeamento", use_container_width=True, type="primary"):
            st.session_state.step = 0
            st.rerun()
        if st.button("📂 Meus Mapeamentos", use_container_width=True):
            st.session_state.step = 10
            st.rerun()
        if role == "gestor":
            st.markdown("<hr>", unsafe_allow_html=True)
            if st.button("📊 Dashboard Gestão", use_container_width=True):
                st.session_state.step = 20
                st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("Sair", use_container_width=True):
            for k in ["logged_in", "login_email", "login_role", "login_nome",
                      "step", "usuario", "job_descriptor", "passos",
                      "meta_processo", "bpmn_gerado", "fase_mapeamento"]:
                st.session_state.pop(k, None)
            st.rerun()

    # Routing
    step = st.session_state.get("step", 0)

    # Página gestão
    if step == 20:
        if role != "gestor":
            st.error("Acesso restrito a gestores.")
        else:
            page_gestao()
        return

    # Histórico
    if step == 10:
        page_historico()
        return

    # Fluxo de mapeamento
    st.markdown("<div class='page-wrapper'>", unsafe_allow_html=True)

    STEP_LABELS = ["Cadastro", "Job Descriptor", "Mapeamento", "Concluído"]
    step_indicator(min(step, 3), 4, STEP_LABELS)

    if step == 0:
        step_cadastro()
    elif step == 1:
        step_job_descriptor()
    elif step == 2:
        step_mapeamento()
    elif step == 3:
        step_sucesso()

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
