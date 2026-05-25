import streamlit as st
import hashlib
import uuid
from datetime import datetime, date
from anthropic import Anthropic

# ─── CONFIG ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Appmax · Mapeamento de Processos",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="auto",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
.stApp { background: #131326 !important; color: #fff !important; }
section[data-testid="stSidebar"] { background: #1a1a38 !important; }
#MainMenu, footer { visibility: hidden; }

/* inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(155,106,250,0.3) !important;
    border-radius: 8px !important;
    color: #131326 !important;
}
.stSelectbox > div > div {
    background: #1e1e40 !important;
    border: 1px solid rgba(155,106,250,0.3) !important;
    border-radius: 8px !important;
    color: #131326 !important;
}
/* labels */
.stTextInput label, .stTextArea label, .stSelectbox label,
.stNumberInput label, .stDateInput label, .stRadio label,
.stMultiSelect label {
    color: #C4A6FD !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
/* buttons */
.stButton > button {
    background: #9B6AFA !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover { background: #C4A6FD !important; color: #281E49 !important; }
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid rgba(155,106,250,0.4) !important;
    color: #C4A6FD !important;
}
/* radio */
.stRadio > div > label {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(155,106,250,0.2) !important;
    border-radius: 20px !important;
    padding: 6px 16px !important;
    margin-right: 6px !important;
    color: #A8A7BC !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    cursor: pointer !important;
}
.stRadio > div > label:has(input:checked) {
    background: rgba(155,106,250,0.15) !important;
    border-color: #9B6AFA !important;
    color: #C4A6FD !important;
    font-weight: 600 !important;
}
/* multiselect */
.stMultiSelect > div > div {
    background: #1e1e40 !important;
    border: 1px solid rgba(155,106,250,0.3) !important;
    border-radius: 8px !important;
}
/* expander */
.streamlit-expanderHeader {
    background: rgba(155,106,250,0.07) !important;
    border: 1px solid rgba(155,106,250,0.2) !important;
    border-radius: 8px !important;
    color: #C4A6FD !important;
}
hr { border-color: rgba(155,106,250,0.15) !important; }
</style>
""", unsafe_allow_html=True)

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def hp(pw): return hashlib.sha256(pw.encode()).hexdigest()

def tempo_empresa(d):
    hoje = date.today()
    m = (hoje.year - d.year) * 12 + (hoje.month - d.month)
    if m < 12: return f"{m} meses"
    a = m // 12; r = m % 12
    return f"{a} ano{'s' if a>1 else ''}" + (f" e {r} meses" if r else "")

def get_client():
    try:
        key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        st.error("⚠️ Configure ANTHROPIC_API_KEY nos Secrets do Streamlit Cloud.")
        st.stop()
    return Anthropic(api_key=key)

def call_ai(system, user):
    try:
        r = get_client().messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": user}]
        )
        return r.content[0].text
    except Exception as e:
        return f"⚠️ {e}"

def init_db():
    if "db" not in st.session_state:
        st.session_state.db = {"mapeamentos": []}

def save_map(usuario, job, processo):
    init_db()
    st.session_state.db["mapeamentos"].append({
        "id": str(uuid.uuid4())[:8],
        "ts": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "usuario": usuario, "job": job, "processo": processo,
    })

# ─── USUÁRIOS ─────────────────────────────────────────────────────────────────
USERS = {
    "demo@appmax.com.br":   {"pw": hp("appmax2025"),  "nome": "Demo User",      "role": "user"},
    "gestor@appmax.com.br": {"pw": hp("gestor2025"),  "nome": "Gestor Appmax",  "role": "gestor"},
}

# ─── COMPONENTES VISUAIS ──────────────────────────────────────────────────────
def card_header(emoji, title, subtitle=""):
    st.markdown(f"""
    <div style="background:rgba(155,106,250,0.07);border:1px solid rgba(155,106,250,0.2);
                border-radius:14px;padding:20px 24px;margin-bottom:20px;">
        <div style="font-size:20px;font-weight:700;color:#fff;margin-bottom:4px;">{emoji} {title}</div>
        {"<div style='font-size:13px;color:#A8A7BC;line-height:1.6;'>" + subtitle + "</div>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)

def ai_bubble(text):
    if text:
        st.markdown(f"""
        <div style="background:rgba(170,237,255,0.06);border:1px solid rgba(170,237,255,0.25);
                    border-radius:10px;padding:12px 16px;margin:8px 0;
                    font-size:13px;color:#AAEDFF;line-height:1.6;">
            ✦ {text}
        </div>
        """, unsafe_allow_html=True)

def step_bar(current, total, labels):
    pips = ""
    for i in range(total):
        if i < current:   c, w = "#9B6AFA", "28px"
        elif i == current: c, w = "#C4A6FD", "40px"
        else:              c, w = "rgba(155,106,250,0.2)", "8px"
        pips += f"<div style='height:7px;width:{w};border-radius:100px;background:{c};transition:all .3s'></div>"
    lbl = labels[current] if current < len(labels) else ""
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:6px;margin-bottom:24px;">
        {pips}
        <span style="font-size:11px;color:#A8A7BC;margin-left:8px;font-family:monospace;letter-spacing:1px;">
            {current+1}/{total} · {lbl}
        </span>
    </div>
    """, unsafe_allow_html=True)

def step_chip(num, text):
    st.markdown(f"""
    <div style="background:rgba(155,106,250,0.08);border:1px solid rgba(155,106,250,0.2);
                border-radius:10px;padding:10px 14px;margin-bottom:6px;
                font-size:13px;color:#E6E0FC;display:flex;gap:10px;align-items:flex-start;">
        <span style="background:#45337C;color:#C4A6FD;font-family:monospace;font-size:10px;
                     font-weight:700;min-width:22px;height:22px;border-radius:50%;
                     display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;">
            {str(num).zfill(2)}
        </span>
        <span>{text}</span>
    </div>
    """, unsafe_allow_html=True)

def info_box(text, color="#F0EBFF", tcolor="#3D1F8F"):
    st.markdown(f"""
    <div style="background:{color};border-radius:10px;padding:14px 18px;
                margin:10px 0;font-size:13px;color:{tcolor};line-height:1.6;">
        {text}
    </div>
    """, unsafe_allow_html=True)

# ─── LOGIN ────────────────────────────────────────────────────────────────────
def page_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.6, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;margin-bottom:32px;">
            <div style="font-size:32px;font-weight:700;letter-spacing:-1px;">
                <span style="color:#9B6AFA;">A</span>ppmax
            </div>
            <div style="font-size:14px;color:#A8A7BC;margin-top:6px;">
                Mapeamento Inteligente de Processos
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown("""
            <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(155,106,250,0.2);
                        border-radius:16px;padding:32px;">
            """, unsafe_allow_html=True)

            email = st.text_input("E-mail", placeholder="seu@appmax.com.br", key="li_email")
            senha = st.text_input("Senha", type="password", placeholder="••••••••", key="li_senha")

            if st.button("Entrar →", use_container_width=True):
                u = USERS.get(email.strip().lower())
                if u and u["pw"] == hp(senha):
                    st.session_state.auth = True
                    st.session_state.email = email.strip().lower()
                    st.session_state.role  = u["role"]
                    st.session_state.nome  = u["nome"]
                    st.session_state.step  = 0
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")

            st.markdown("<hr style='margin:20px 0'>", unsafe_allow_html=True)
            st.markdown("""
            <div style="font-size:12px;color:#A8A7BC;text-align:center;line-height:2;">
                <b style="color:#C4A6FD;">Demo:</b><br>
                demo@appmax.com.br / appmax2025<br>
                gestor@appmax.com.br / gestor2025
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ─── STEP 1: CADASTRO ─────────────────────────────────────────────────────────
def step_cadastro():
    card_header("👤", "Cadastro", "Preencha seus dados para iniciar o mapeamento.")
    c1, c2 = st.columns(2)
    with c1:
        nome   = st.text_input("Nome completo", key="cn")
        time_  = st.selectbox("Time", ["","Produto","Engenharia","People & Culture",
                               "Operações","Comercial","Marketing","Financeiro","CS","TI","Outro"], key="ct")
        funcao = st.text_input("Função que você exerce hoje (na prática)", key="cf",
                               placeholder="Ex: Analista de Suporte e Operações")
    with c2:
        email_ = st.text_input("E-mail corporativo", key="ce",
                               value=st.session_state.get("email",""))
        cargo  = st.text_input("Cargo formal", key="cc",
                               placeholder="Ex: Analista de Operações Pleno")
        data_  = st.date_input("Data de ingresso", key="cd",
                               min_value=date(2000,1,1), max_value=date.today(),
                               value=date(2022,1,1))

    if data_:
        t = tempo_empresa(data_)
        st.caption(f"⏱ {t} de empresa")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Continuar →", disabled=not all([nome, email_, time_, cargo, funcao])):
        st.session_state.usuario = dict(
            nome=nome, email=email_, time=time_, cargo=cargo,
            funcao=funcao, data_ingresso=data_.isoformat(),
            tempo=tempo_empresa(data_)
        )
        st.session_state.step = 1
        st.rerun()

# ─── STEP 2: JOB DESCRIPTOR ───────────────────────────────────────────────────
def step_job():
    u = st.session_state.usuario
    card_header("📋", "Job Descriptor Real",
                f"Descreva uma atividade principal que você realiza hoje, <b style='color:#C4A6FD'>{u['nome']}</b>.")

    tarefa   = st.text_area("Tarefa realizada", max_chars=200, key="jt",
                            placeholder="Ex: Consolido relatórios semanais de performance das campanhas", height=80)
    c1, c2 = st.columns(2)
    with c1:
        ferr   = st.text_input("Ferramenta ou sistema", key="jf", placeholder="Ex: Google Sheets, Salesforce...")
        motivo = st.text_input("Por que você realiza essa tarefa?", key="jm")
    with c2:
        prob   = st.text_area("Qual problema resolve?", key="jp", height=95,
                              placeholder="Descreva o problema que ela resolve...")

    impacto = st.multiselect("Se você parar hoje, quem é impactado?",
                             ["Empresa","Parceiros","Meu time","Outros times"], key="ji")
    imp_d   = st.text_area("Descreva o impacto", key="jid", height=70)
    mensura = st.radio("Consegue mensurar impacto financeiro?",
                       ["Sim","Não","Parcialmente"], horizontal=True, key="jme")

    if tarefa and ferr:
        if st.button("✦ Analisar com IA", key="ai_job"):
            with st.spinner("Analisando..."):
                resp = call_ai(
                    "Você é especialista em análise de processos corporativos. "
                    "Avalie a descrição da tarefa em 2 frases curtas e construtivas. "
                    "Responda em português brasileiro.",
                    f"Colaborador: {u['nome']} ({u['cargo']} - {u['time']})\n"
                    f"Tarefa: \"{tarefa}\"\nFerramenta: \"{ferr}\"\nMotivo: \"{motivo}\""
                )
            ai_bubble(resp)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([1,3])
    with c1:
        if st.button("← Voltar", key="jback"):
            st.session_state.step = 0; st.rerun()
    with c2:
        if st.button("Continuar para Mapeamento →", disabled=not (tarefa and ferr)):
            st.session_state.job = dict(
                tarefa=tarefa, ferr=ferr, motivo=motivo, prob=prob,
                impacto=impacto, imp_d=imp_d, mensura=mensura
            )
            st.session_state.step = 2
            st.session_state.passos = []
            st.session_state.fase = "meta"
            st.session_state.pop("bpmn", None)
            st.rerun()

# ─── STEP 3: MAPEAMENTO ───────────────────────────────────────────────────────
def step_mapeamento():
    fase = st.session_state.get("fase", "meta")

    # ── META ──────────────────────────────────────────────────
    if fase == "meta":
        card_header("🗺️", "Mapeamento de Processo", "Classifique e caracterize o que você vai mapear.")

        tipo = st.radio("Tipo", [
            "⚡ Tarefa — Ação isolada e pontual",
            "🔄 Processo — Conjunto de tarefas sequenciais"
        ], key="mt")
        tipo_c = "Tarefa" if "Tarefa" in tipo else "Processo"

        c1, c2 = st.columns(2)
        with c1:
            nome  = st.text_input(f"Nome d{'a' if tipo_c=='Tarefa' else 'o'} {tipo_c}", key="mn")
            freq  = st.selectbox("Frequência", ["","Diária","Semanal","Quinzenal","Mensal","Esporádica"], key="mf")
        with c2:
            ferr  = st.text_input("Ferramenta principal", key="mfe", placeholder="Ex: Google Drive, Slack...")
            if freq and freq != "Esporádica":
                vezes = st.number_input("Quantas vezes por período?", min_value=1, value=1, key="mv")
            elif freq == "Esporádica":
                gatilho = st.text_input("O que desencadeia essa atividade?", key="mg")

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns([1,3])
        with c1:
            if st.button("← Voltar", key="mback"):
                st.session_state.step = 1; st.rerun()
        with c2:
            if st.button("Começar a mapear os passos →", disabled=not (nome and freq)):
                st.session_state.meta = dict(
                    tipo=tipo_c, nome=nome, ferr=ferr, freq=freq,
                    vezes=st.session_state.get("mv",1) if freq!="Esporádica" else None,
                    gatilho=st.session_state.get("mg","") if freq=="Esporádica" else "",
                )
                st.session_state.passos = []
                st.session_state.fase = "steps"
                st.rerun()

    # ── STEPS ─────────────────────────────────────────────────
    elif fase == "steps":
        meta   = st.session_state.meta
        passos = st.session_state.passos

        card_header("📝", f"Passos do {meta['tipo']}",
                    f"<b style='color:#C4A6FD'>{meta['nome']}</b> · {meta['tipo']} · {meta['freq']} "
                    f"· {len(passos)} passo{'s' if len(passos)!=1 else ''} registrado{'s' if len(passos)!=1 else ''}")

        for i, p in enumerate(passos):
            step_chip(i+1, p)

        if passos:
            st.markdown("<br>", unsafe_allow_html=True)

        num = len(passos) + 1
        novo = st.text_area(
            f"{'Descreva o 1º passo' if not passos else f'Passo {num}'}",
            key=f"si_{num}", max_chars=200, height=80,
            placeholder="Descreva detalhadamente o que você faz neste passo..."
        )

        if novo and len(novo.strip()) > 15:
            if st.button("✦ Validar com IA", key=f"vai_{num}"):
                with st.spinner("Analisando clareza do passo..."):
                    resp = call_ai(
                        "Você é especialista em mapeamento de processos BPMN. "
                        "Avalie se o passo está claro. Se não, faça 1-2 perguntas curtas de refinamento. "
                        "Se estiver claro responda apenas: '✓ Passo claro, pode continuar.' "
                        "Seja muito conciso. Responda em português.",
                        f"Processo: \"{meta['nome']}\" ({meta['tipo']}). "
                        f"Passos anteriores: {len(passos)}.\nNovo passo: \"{novo.strip()}\""
                    )
                ai_bubble(resp)

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("+ Salvar passo", disabled=not novo.strip()):
                st.session_state.passos.append(novo.strip())
                st.rerun()
        with c2:
            if passos and st.button("↩ Remover último"):
                st.session_state.passos.pop(); st.rerun()
        with c3:
            if len(passos) >= 2:
                if st.button("Finalizar e gerar fluxograma ✦"):
                    st.session_state.fase = "gerando"; st.rerun()

        if len(passos) < 2:
            st.caption("💡 Adicione pelo menos 2 passos para finalizar.")

    # ── GERANDO ───────────────────────────────────────────────
    elif fase == "gerando":
        meta   = st.session_state.meta
        passos = st.session_state.passos
        with st.spinner("✦ Gerando fluxograma BPMN..."):
            txt = "\n".join(f"{i+1}. {p}" for i,p in enumerate(passos))
            bpmn = call_ai(
                "Você é especialista em notação BPMN. Crie um fluxograma textual claro: "
                "🟢 Início → etapas → 🔴 Fim. "
                "Use: 🟢 Início, 🔵 Tarefa, 🔷 Decisão, 🔴 Fim. "
                "Cada elemento em uma linha com seta →. Responda APENAS o fluxograma.",
                f"Processo: \"{meta['nome']}\" ({meta['tipo']})\nPassos:\n{txt}"
            )
        st.session_state.bpmn = bpmn
        st.session_state.fase = "confirm"
        st.rerun()

    # ── CONFIRM ───────────────────────────────────────────────
    elif fase == "confirm":
        meta   = st.session_state.meta
        passos = st.session_state.passos
        bpmn   = st.session_state.get("bpmn","")

        card_header("✦", "Fluxograma Gerado",
                    "A IA criou o fluxograma abaixo. Confira se está correto.")

        st.markdown(f"""
        <div style="background:rgba(69,51,124,0.18);border:1px solid rgba(155,106,250,0.28);
                    border-radius:12px;padding:20px;font-family:monospace;font-size:13px;
                    line-height:1.9;color:#E6E0FC;white-space:pre-wrap;margin:12px 0;">
{bpmn}
        </div>
        """, unsafe_allow_html=True)

        ok = st.radio(
            f"O fluxograma corresponde ao {meta['tipo'].lower()} que você realiza hoje?",
            ["✓ Sim, está correto", "✗ Faltou algo"], horizontal=True, key="bconf"
        )
        faltou = ""
        if "Faltou" in ok:
            faltou = st.text_area("Qual passo faltou incluir?", key="bf", height=70)

        st.markdown("---")
        sugestao = st.text_area("💡 Sugestão de melhoria para essa demanda? (opcional)",
                                key="bsug", height=70)

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns([1,3])
        with c1:
            if st.button("← Editar passos"):
                st.session_state.fase = "steps"; st.rerun()
        with c2:
            if st.button("Salvar e finalizar ✓"):
                save_map(
                    st.session_state.usuario,
                    st.session_state.job,
                    {**meta, "passos": passos, "bpmn": bpmn,
                     "confirmado": "Sim" if "Sim" in ok else "Não",
                     "faltou": faltou, "sugestao": sugestao}
                )
                st.session_state.processo_salvo = {**meta, "passos": passos, "sugestao": sugestao}
                st.session_state.step = 3
                st.rerun()

# ─── STEP 4: SUCESSO ─────────────────────────────────────────────────────────
def step_sucesso():
    u = st.session_state.usuario
    p = st.session_state.processo_salvo

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(155,106,250,0.14),rgba(69,51,124,0.2));
                border:1px solid rgba(155,106,250,0.3);border-radius:18px;
                padding:40px 32px;text-align:center;margin:20px 0;">
        <div style="font-size:48px;margin-bottom:12px;">✦</div>
        <div style="font-size:22px;font-weight:700;margin-bottom:10px;">Processo mapeado!</div>
        <div style="font-size:14px;color:#A8A7BC;line-height:1.7;max-width:440px;margin:0 auto 24px;">
            <b style="color:#C4A6FD;">{p['nome']}</b> ({p['tipo']}) registrado com
            <b style="color:#fff;">{len(p['passos'])} passos</b>.
            {' Sugestão de melhoria registrada.' if p.get('sugestao') else ''}
        </div>
        <div style="background:rgba(155,106,250,0.08);border-radius:10px;padding:14px 18px;
                    max-width:320px;margin:0 auto;text-align:left;font-size:13px;
                    color:#E6E0FC;line-height:1.9;">
            👤 {u['nome']} · {u['time']}<br>
            📌 {p['tipo']}: {p['nome']}<br>
            📅 {p['freq']} · {len(p['passos'])} passos<br>
            🛠️ {p.get('ferr','—')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("+ Mapear outro processo", use_container_width=True):
            st.session_state.step = 2
            st.session_state.fase = "meta"
            st.session_state.passos = []
            st.session_state.pop("bpmn", None)
            st.rerun()
    with c2:
        if st.button("📂 Ver meus mapeamentos", use_container_width=True):
            st.session_state.step = 10; st.rerun()

# ─── HISTÓRICO ────────────────────────────────────────────────────────────────
def page_historico():
    init_db()
    email = st.session_state.get("email","")
    meus  = [d for d in st.session_state.db["mapeamentos"] if d["usuario"]["email"]==email]

    st.markdown(f"### 📂 Meus Mapeamentos  <span style='font-size:14px;color:#A8A7BC;font-weight:400'>({len(meus)} registros)</span>", unsafe_allow_html=True)

    if not meus:
        info_box("ℹ️ Você ainda não mapeou nenhum processo. Clique em 'Novo Mapeamento' para começar.")
    else:
        for d in reversed(meus):
            p = d["processo"]
            with st.expander(f"📌 {p['nome']} · {p['tipo']} · {d['ts']}"):
                st.markdown(f"**Frequência:** {p['freq']}  \n**Ferramenta:** {p.get('ferr','—')}  \n**Passos:** {len(p['passos'])}")
                for i,s in enumerate(p["passos"]):
                    step_chip(i+1, s)
                if p.get("bpmn"):
                    st.code(p["bpmn"], language=None)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("+ Novo Mapeamento"):
        st.session_state.step = 2
        st.session_state.fase = "meta"
        st.session_state.passos = []
        st.rerun()

# ─── GESTÃO ───────────────────────────────────────────────────────────────────
def page_gestao():
    init_db()
    dados = st.session_state.db["mapeamentos"]

    st.markdown("### 📊 Dashboard de Gestão")
    st.caption(f"{len(dados)} mapeamento{'s' if len(dados)!=1 else ''} registrado{'s' if len(dados)!=1 else ''} nesta sessão")

    if not dados:
        info_box("ℹ️ Nenhum mapeamento registrado ainda. Faça login como colaborador e mapeie alguns processos.")
        return

    c1,c2,c3,c4 = st.columns(4)
    times = set(d["usuario"]["time"] for d in dados)
    total_passos = sum(len(d["processo"]["passos"]) for d in dados)
    ferrs = set(d["processo"].get("ferr","") for d in dados if d["processo"].get("ferr"))
    c1.metric("Mapeamentos", len(dados))
    c2.metric("Times ativos", len(times))
    c3.metric("Total de passos", total_passos)
    c4.metric("Ferramentas únicas", len(ferrs))

    st.markdown("---")
    st.markdown("**Processos Mapeados**")
    for d in reversed(dados):
        u, p = d["usuario"], d["processo"]
        with st.expander(f"📌 {p['nome']} — {u['nome']} ({u['time']}) · {d['ts']}"):
            c1,c2 = st.columns(2)
            with c1:
                st.markdown(f"**Tipo:** {p['tipo']}  \n**Freq:** {p['freq']}  \n**Ferramenta:** {p.get('ferr','—')}")
            with c2:
                st.markdown(f"**Passos:** {len(p['passos'])}  \n**Confirmado:** {p.get('confirmado','—')}  \n**Cargo:** {u['cargo']}")
            for i,s in enumerate(p["passos"]):
                step_chip(i+1, s)
            if p.get("sugestao"):
                info_box(f"💡 <b>Sugestão:</b> {p['sugestao']}", "#EAF8FF", "#1A5C70")
            if p.get("bpmn"):
                st.code(p["bpmn"], language=None)

    st.markdown("---")
    st.markdown("**Ferramentas Mais Citadas**")
    from collections import Counter
    fl = [d["processo"].get("ferr","") for d in dados if d["processo"].get("ferr")]
    if fl:
        for ferr, cnt in Counter(fl).most_common(8):
            pct = int(cnt/len(fl)*100)
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
                <div style="font-size:13px;color:#E6E0FC;min-width:160px;">{ferr}</div>
                <div style="flex:1;background:rgba(155,106,250,0.1);border-radius:100px;height:6px;">
                    <div style="width:{pct}%;background:#9B6AFA;height:6px;border-radius:100px;"></div>
                </div>
                <div style="font-size:12px;color:#A8A7BC;min-width:24px;">{cnt}x</div>
            </div>
            """, unsafe_allow_html=True)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    init_db()

    if not st.session_state.get("auth"):
        page_login()
        return

    role = st.session_state.get("role","user")
    nome = st.session_state.get("nome","")

    # ── Header ──
    st.markdown(f"""
    <div style="border-bottom:1px solid rgba(155,106,250,0.15);
                padding:14px 0 14px;margin-bottom:8px;
                display:flex;align-items:center;justify-content:space-between;">
        <div style="font-size:18px;font-weight:700;">
            <span style="color:#9B6AFA;">A</span>ppmax
            <span style="color:#A8A7BC;font-weight:300;font-size:15px;"> · Mapeamento de Processos</span>
        </div>
        <span style="font-size:10px;letter-spacing:2px;color:#AAEDFF;
                     background:rgba(170,237,255,0.08);border:1px solid rgba(170,237,255,0.22);
                     padding:4px 12px;border-radius:100px;font-family:monospace;">✦ IA ATIVA</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ──
    with st.sidebar:
        st.markdown(f"<div style='color:#C4A6FD;font-weight:700;font-size:16px;margin-bottom:16px;'>Olá, {nome.split()[0]} 👋</div>", unsafe_allow_html=True)
        if st.button("✦ Novo Mapeamento", use_container_width=True):
            st.session_state.step = 0; st.rerun()
        if st.button("📂 Meus Mapeamentos", use_container_width=True):
            st.session_state.step = 10; st.rerun()
        if role == "gestor":
            st.markdown("---")
            if st.button("📊 Dashboard Gestão", use_container_width=True):
                st.session_state.step = 20; st.rerun()
        st.markdown("---")
        if st.button("Sair", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    # ── Routing ──
    step = st.session_state.get("step", 0)

    if step == 20:
        page_gestao() if role == "gestor" else st.error("Acesso restrito.")
        return
    if step == 10:
        page_historico()
        return

    LABELS = ["Cadastro","Job Descriptor","Mapeamento","Concluído"]
    step_bar(min(step,3), 4, LABELS)

    if   step == 0: step_cadastro()
    elif step == 1: step_job()
    elif step == 2: step_mapeamento()
    elif step == 3: step_sucesso()

if __name__ == "__main__":
    main()
