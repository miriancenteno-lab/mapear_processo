import streamlit as st
import hashlib
import uuid
from datetime import datetime, date
from anthropic import Anthropic

st.set_page_config(
    page_title="Appmax · Mapeamento de Processos",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="auto",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
.stApp { background: #131326 !important; color: #fff !important; }
section[data-testid="stSidebar"] { background: #1a1a38 !important; }
#MainMenu, footer { visibility: hidden; }
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input {
    background: #F0EBFF !important;
    border: 1px solid rgba(155,106,250,0.4) !important;
    border-radius: 8px !important;
    color: #131326 !important;
    font-size: 14px !important;
}
.stSelectbox > div > div {
    background: #F0EBFF !important;
    border: 1px solid rgba(155,106,250,0.4) !important;
    border-radius: 8px !important;
    color: #131326 !important;
}
.stMultiSelect > div > div {
    background: #F0EBFF !important;
    border: 1px solid rgba(155,106,250,0.4) !important;
    border-radius: 8px !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label,
.stNumberInput label, .stDateInput label, .stRadio label, .stMultiSelect label {
    color: #C4A6FD !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
.stButton > button {
    background: #9B6AFA !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stButton > button:hover { background: #C4A6FD !important; color: #281E49 !important; }
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid rgba(155,106,250,0.4) !important;
    color: #C4A6FD !important;
}
.stRadio > div { gap: 8px !important; flex-wrap: wrap !important; }
.stRadio > div > label {
    background: rgba(155,106,250,0.10) !important;
    border: 1px solid rgba(155,106,250,0.40) !important;
    border-radius: 20px !important;
    padding: 7px 18px !important;
    color: #E6E0FC !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    cursor: pointer !important;
}
.stRadio > div > label:has(input:checked) {
    background: rgba(155,106,250,0.30) !important;
    border-color: #9B6AFA !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}
hr { border-color: rgba(155,106,250,0.15) !important; }
</style>
""", unsafe_allow_html=True)

# ── helpers ──────────────────────────────────────────────────
def hp(pw): return hashlib.sha256(pw.encode()).hexdigest()

def tempo_empresa(d):
    hoje = date.today()
    m = (hoje.year - d.year)*12 + (hoje.month - d.month)
    if m < 12: return f"{m} meses"
    a = m//12; r = m%12
    return f"{a} ano{'s' if a>1 else ''}" + (f" e {r} meses" if r else "")

def get_ai():
    try:
        key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        st.error("Configure ANTHROPIC_API_KEY nos Secrets do Streamlit Cloud.")
        st.stop()
    return Anthropic(api_key=key)

def call_ai(system, user, max_tokens=1600):
    try:
        r = get_ai().messages.create(
            model="claude-sonnet-4-5",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role":"user","content":user}]
        )
        return r.content[0].text
    except Exception as e:
        return f"Erro: {e}"

# ── Google Sheets ─────────────────────────────────────────────
def save_to_sheets(usuario, demanda, fluxograma, sugestao):
    try:
        import gspread, json
        from google.oauth2.service_account import Credentials
        creds_raw = st.secrets["GOOGLE_CREDENTIALS"]
        creds_dict = json.loads(creds_raw) if isinstance(creds_raw, str) else dict(creds_raw)
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(st.secrets["SHEET_ID"])
        try:
            ws = sh.worksheet("Mapeamentos")
        except Exception:
            ws = sh.add_worksheet("Mapeamentos", rows=1000, cols=22)
        headers = ["ID","Data/Hora","Nome","E-mail","Time","Cargo","Tempo Empresa",
                   "Nome Demanda","Tipo","Ferramentas","Objetivo","Problema",
                   "Impacto Tipo","Impacto Desc","Impacto Financeiro",
                   "Frequência","Gatilho","Descrição Livre","Fluxograma BPMN","Sugestão"]
        if not ws.row_values(1):
            ws.append_row(headers)
        ws.append_row([
            str(uuid.uuid4())[:8],
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            usuario.get("nome",""), usuario.get("email",""),
            usuario.get("time",""), usuario.get("cargo",""), usuario.get("tempo",""),
            demanda.get("nome",""), demanda.get("tipo",""), demanda.get("ferramentas",""),
            demanda.get("objetivo",""), demanda.get("problema",""),
            ", ".join(demanda.get("impacto_tipo",[])),
            demanda.get("impacto_desc",""), demanda.get("impacto_fin",""),
            demanda.get("freq",""), demanda.get("gatilho",""),
            demanda.get("descricao_livre",""), fluxograma, sugestao,
        ])
        return True, None
    except Exception as e:
        return False, str(e)

# ── Usuários (persistidos no Google Sheets) ───────────────────
ADMIN_EMAIL = "admin@appmax.com.br"
ADMIN_PW    = hp("admin2025")

def _get_users_ws():
    """Retorna a aba 'Usuarios' do Sheets, criando se não existir."""
    try:
        import gspread, json
        from google.oauth2.service_account import Credentials
        creds_raw  = st.secrets["GOOGLE_CREDENTIALS"]
        creds_dict = json.loads(creds_raw) if isinstance(creds_raw, str) else dict(creds_raw)
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(st.secrets["SHEET_ID"])
        try:
            ws = sh.worksheet("Usuarios")
        except Exception:
            ws = sh.add_worksheet("Usuarios", rows=500, cols=4)
            ws.append_row(["email", "nome", "pw_hash", "ativo"])
        return ws
    except Exception:
        return None

def get_users():
    """
    Retorna dict {email: {nome, pw, ativo}} lido do Sheets.
    Usa cache em session_state para evitar chamadas repetidas na mesma sessão.
    """
    # Invalida cache quando admin acabou de salvar
    if st.session_state.get("users_dirty"):
        st.session_state.pop("users_cache", None)
        st.session_state.pop("users_dirty", None)

    if "users_cache" in st.session_state:
        return st.session_state.users_cache

    ws = _get_users_ws()
    users = {}
    if ws:
        try:
            rows = ws.get_all_records()
            for r in rows:
                e = str(r.get("email","")).strip().lower()
                if e:
                    users[e] = {
                        "nome":  r.get("nome",""),
                        "pw":    r.get("pw_hash",""),
                        "ativo": str(r.get("ativo","1")) not in ("0","False","false",""),
                    }
        except Exception:
            pass
    # Fallback: se Sheets não configurado ainda, mantém demo local
    if not users:
        users = {"demo@appmax.com.br": {"nome":"Demo User","pw":hp("appmax2025"),"ativo":True}}

    st.session_state.users_cache = users
    return users

def add_user(email, nome, senha=""):
    """
    Adiciona usuário no Sheets.
    senha="" = primeiro acesso, usuário vai criar a própria senha.
    """
    ws = _get_users_ws()
    if ws:
        try:
            cell = ws.find(email.strip().lower())
            if cell:
                ws.delete_rows(cell.row)
        except Exception:
            pass
        pw_hash = hp(senha) if senha else ""
        ws.append_row([email.strip().lower(), nome, pw_hash, "1"])
    st.session_state.users_dirty = True

def set_user_password(email, nova_senha):
    """Grava senha criada pelo usuário no primeiro acesso."""
    ws = _get_users_ws()
    if not ws:
        return False, "Sheets não disponível"
    try:
        cell = ws.find(email.strip().lower())
        if cell:
            ws.update_cell(cell.row, 3, hp(nova_senha))
            st.session_state.users_dirty = True
            return True, None
        return False, "Usuário não encontrado"
    except Exception as e:
        return False, str(e)

def remove_user(email):
    """Remove usuário do Sheets e invalida cache."""
    ws = _get_users_ws()
    if ws:
        try:
            cell = ws.find(email.strip().lower())
            if cell:
                ws.delete_rows(cell.row)
        except Exception:
            pass
    st.session_state.users_dirty = True

# ── componentes ───────────────────────────────────────────────
def page_header():
    st.markdown("""
    <div style="border-bottom:1px solid rgba(155,106,250,0.15);padding-bottom:14px;margin-bottom:20px;
                display:flex;align-items:center;justify-content:space-between;">
        <div style="font-size:18px;font-weight:700;">
            <span style="color:#9B6AFA;">A</span>ppmax
            <span style="color:#A8A7BC;font-weight:300;font-size:15px;"> · Mapeamento de Processos</span>
        </div>
        <span style="font-size:10px;letter-spacing:2px;color:#AAEDFF;background:rgba(170,237,255,0.08);
                     border:1px solid rgba(170,237,255,0.22);padding:4px 12px;border-radius:100px;
                     font-family:monospace;">✦ IA ATIVA</span>
    </div>""", unsafe_allow_html=True)

def section_title(emoji, title, sub=""):
    st.markdown(f"""
    <div style="background:rgba(155,106,250,0.07);border:1px solid rgba(155,106,250,0.2);
                border-left:4px solid #9B6AFA;border-radius:0 12px 12px 0;padding:16px 20px;margin-bottom:20px;">
        <div style="font-size:18px;font-weight:700;color:#fff;">{emoji}&nbsp; {title}</div>
        {"<div style='font-size:13px;color:#A8A7BC;margin-top:4px;line-height:1.6;'>" + sub + "</div>" if sub else ""}
    </div>""", unsafe_allow_html=True)

def step_bar(current, total, labels):
    pips = ""
    for i in range(total):
        if i < current:    c,w = "#9B6AFA","32px"
        elif i == current: c,w = "#C4A6FD","48px"
        else:              c,w = "rgba(155,106,250,0.18)","8px"
        pips += f"<div style='height:6px;width:{w};border-radius:100px;background:{c};transition:all .3s'></div>"
    lbl = labels[min(current,len(labels)-1)]
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:5px;margin-bottom:24px;">
        {pips}
        <span style="font-size:11px;color:#A8A7BC;margin-left:10px;font-family:monospace;
                     letter-spacing:1px;text-transform:uppercase;">{current+1}/{total} · {lbl}</span>
    </div>""", unsafe_allow_html=True)

def hint(text):
    st.markdown(f"""
    <div style="background:rgba(170,237,255,0.05);border:1px solid rgba(170,237,255,0.15);
                border-radius:8px;padding:10px 14px;margin-bottom:10px;
                font-size:12px;color:#A8A7BC;line-height:1.6;">💡 {text}</div>
    """, unsafe_allow_html=True)

def bpmn_box(text):
    st.markdown(f"""
    <div style="background:rgba(69,51,124,0.18);border:1px solid rgba(155,106,250,0.3);
                border-radius:12px;padding:20px 22px;font-size:13px;color:#E6E0FC;
                line-height:1.9;white-space:pre-wrap;font-family:monospace;margin:12px 0;">
{text}
    </div>""", unsafe_allow_html=True)

# ── LOGIN ─────────────────────────────────────────────────────
def page_login():
    st.markdown("<br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.8, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;margin-bottom:32px;">
            <div style="font-size:36px;font-weight:700;letter-spacing:-1.5px;">
                <span style="color:#9B6AFA;">A</span>ppmax</div>
            <div style="font-size:13px;color:#A8A7BC;margin-top:6px;">
                Mapeamento Inteligente de Processos</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(155,106,250,0.2);
                    border-radius:16px;padding:30px 28px;">
        """, unsafe_allow_html=True)
        email = st.text_input("E-mail", placeholder="seu@appmax.com.br", key="li_e")

        # Detecta se é primeiro acesso (sem senha definida)
        e_check = email.strip().lower()
        users_check = get_users()
        u_check = users_check.get(e_check)
        primeiro_acesso = u_check and u_check.get("ativo") and not u_check.get("pw")

        if primeiro_acesso:
            st.markdown("""
            <div style="background:rgba(170,237,255,0.06);border:1px solid rgba(170,237,255,0.2);
                        border-radius:8px;padding:10px 14px;font-size:12px;color:#AAEDFF;margin:6px 0;">
                ✦ Primeiro acesso detectado. Crie sua senha abaixo.
            </div>""", unsafe_allow_html=True)
            nova_s1 = st.text_input("Crie sua senha", type="password", placeholder="Mínimo 6 caracteres", key="li_ns1")
            nova_s2 = st.text_input("Confirme sua senha", type="password", placeholder="Repita a senha", key="li_ns2")
            if st.button("Criar senha e entrar →", use_container_width=True):
                if len(nova_s1) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                elif nova_s1 != nova_s2:
                    st.error("As senhas não coincidem.")
                else:
                    with st.spinner("Salvando sua senha..."):
                        ok, err = set_user_password(e_check, nova_s1)
                    if ok:
                        st.session_state.update(auth=True, email=e_check, role="user",
                                                nome=u_check["nome"], page="cadastro")
                        st.rerun()
                    else:
                        st.error(f"Erro ao salvar senha: {err}")
        else:
            senha = st.text_input("Senha", type="password", placeholder="••••••••", key="li_s")
            if st.button("Entrar →", use_container_width=True):
                e = email.strip().lower()
                if e == ADMIN_EMAIL and hp(senha) == ADMIN_PW:
                    st.session_state.update(auth=True,email=e,role="admin",nome="Admin",page="admin")
                    st.rerun()
                else:
                    u = get_users().get(e)
                    if u and u["pw"] == hp(senha) and u.get("ativo"):
                        st.session_state.update(auth=True,email=e,role="user",nome=u["nome"],page="cadastro")
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos, ou acesso não liberado.")

        st.markdown("</div>", unsafe_allow_html=True)
        st.caption("Acesso liberado pelo administrador.")

# ── ADMIN ─────────────────────────────────────────────────────
def page_admin():
    section_title("⚙️","Painel Admin","Gerencie os usuários com acesso à ferramenta.")
    users = get_users()

    with st.expander("➕ Cadastrar novo usuário", expanded=True):
        st.markdown("""
        <div style="font-size:12px;color:#A8A7BC;margin-bottom:12px;line-height:1.6;">
            💡 Cadastre o e-mail do colaborador. Na primeira vez que ele acessar,
            o sistema vai pedir para criar a própria senha.
        </div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: nn = st.text_input("Nome completo", key="nu_n")
        with c2: ne = st.text_input("E-mail corporativo", key="nu_e")
        if st.button("Cadastrar usuário"):
            if nn and ne:
                with st.spinner("Salvando no Google Sheets..."):
                    add_user(ne, nn)   # sem senha — primeiro acesso
                st.success(f"✓ {nn} ({ne.strip().lower()}) cadastrado! No primeiro login, ele criará a própria senha.")
                st.rerun()
            else:
                st.warning("Preencha nome e e-mail.")

    st.markdown(f"---\n**Usuários cadastrados ({len(users)})**")
    if not users:
        st.caption("Nenhum usuário cadastrado ainda.")
    for em, u in list(users.items()):
        c1,c2,c3 = st.columns([3,2,1])
        with c1: st.markdown(f"**{u['nome']}** · `{em}`")
        with c2: st.caption("✅ Ativo" if u.get("ativo") else "🚫 Inativo")
        with c3:
            if st.button("Remover", key=f"rm_{em}"):
                with st.spinner("Removendo..."):
                    remove_user(em)
                st.rerun()

    st.markdown("---")
    sh_ok = "GOOGLE_CREDENTIALS" in st.secrets and "SHEET_ID" in st.secrets
    if sh_ok:
        try:
            import gspread, json
            from google.oauth2.service_account import Credentials
            creds_raw = st.secrets["GOOGLE_CREDENTIALS"]
            creds_dict = json.loads(creds_raw) if isinstance(creds_raw,str) else dict(creds_raw)
            scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict,scopes=scopes)
            gc = gspread.authorize(creds)
            sh = gc.open_by_key(st.secrets["SHEET_ID"])
            try:
                ws = sh.worksheet("Mapeamentos")
                all_r = ws.get_all_records()
                st.success(f"✓ Google Sheets conectado · {len(all_r)} mapeamento(s)")
                if all_r:
                    import pandas as pd
                    st.dataframe(pd.DataFrame(all_r), use_container_width=True)
            except Exception:
                st.info("Planilha conectada, sem dados ainda.")
        except Exception as e:
            st.error(f"Erro Google Sheets: {e}")
    else:
        st.warning("Google Sheets não configurado. Configure GOOGLE_CREDENTIALS e SHEET_ID nos Secrets.")

# ── ETAPA 1: CADASTRO ─────────────────────────────────────────
def page_cadastro():
    section_title("👤","Seus dados","Preencha seu cadastro para iniciar o mapeamento.")
    c1,c2 = st.columns(2)
    with c1:
        nome  = st.text_input("Nome completo",key="c_nome")
        time_ = st.selectbox("Time / Departamento",
            ["","Produto","Engenharia","People & Culture","Operações",
             "Comercial","Marketing","Financeiro","CS","TI","Outro"],key="c_time")
    with c2:
        email_ = st.text_input("E-mail corporativo",key="c_email",
                               value=st.session_state.get("email",""))
        cargo  = st.text_input("Cargo",key="c_cargo",placeholder="Ex: Analista de Operações")
    data_ = st.date_input("Data de ingresso na empresa",key="c_data",
                          min_value=date(2000,1,1),max_value=date.today(),value=date(2022,1,1))
    if data_:
        st.caption(f"⏱ Tempo de empresa: **{tempo_empresa(data_)}**")
    st.markdown("<br>",unsafe_allow_html=True)
    if st.button("Próximo →", disabled=not all([nome,email_,time_,cargo])):
        st.session_state.usuario = dict(
            nome=nome,email=email_,time=time_,cargo=cargo,
            data_ingresso=data_.isoformat(),tempo=tempo_empresa(data_))
        st.session_state.page = "demanda"; st.rerun()

# ── ETAPA 2: DADOS DA DEMANDA ─────────────────────────────────
def page_demanda():
    u = st.session_state.usuario
    section_title("📋","Dados da Demanda",
        f"Olá, <b style='color:#C4A6FD'>{u['nome']}</b>! Descreva a demanda que será mapeada.")

    hint("Use um nome simples que todos os envolvidos entendam do que se trata.")
    nome_d = st.text_input("Qual é a demanda que será mapeada?",key="d_nome",
                            placeholder="Ex: Envio de relatório semanal de performance")

    tipo = st.radio("Qual é o tipo da demanda?",[
        "⚡ Tarefa — Ação isolada ou etapa única, pontual e de curto prazo",
        "🔄 Processo — Conjunto de tarefas interligadas, organizadas em etapas sequenciais"
    ],key="d_tipo")
    tipo_c = "Tarefa" if "Tarefa" in tipo else "Processo"
    art    = "essa" if tipo_c=="Tarefa" else "esse"
    Art    = "Essa" if tipo_c=="Tarefa" else "Esse"

    st.markdown("---")
    hint("Insira o nome das ferramentas usadas: sistemas, planilhas, aplicativos, etc.")
    ferr = st.text_area(f"Quais ferramentas são necessárias para executar {art} {tipo_c}?",
        key="d_ferr",height=80,placeholder="Ex: Google Sheets, Salesforce, Slack, SAP...")
    obj  = st.text_area(f"Qual o objetivo {art} {tipo_c}? Por qual motivo você a executa?",
        key="d_obj",height=80,placeholder="A finalidade, o resultado esperado e o motivo de negócio.")
    prob = st.text_area("Qual problema ela resolve?",key="d_prob",height=70,
        placeholder="A dor, risco ou necessidade que motivou a criação.")

    st.markdown("---")
    st.markdown(f"<div style='color:#C4A6FD;font-size:12px;font-weight:600;text-transform:uppercase;"
                f"letter-spacing:.5px;margin-bottom:8px;'>Se você parar de fazer {art} {tipo_c} hoje, "
                f"qual é o impacto?</div>", unsafe_allow_html=True)
    imp_tipo = st.multiselect("Quem é impactado?",
        ["Empresa","Parceiro","Colegas do meu time","Colegas de outros times"],key="d_it")
    imp_desc = st.text_area("Descreva o impacto em detalhes",key="d_id",height=80)
    imp_fin  = st.radio("Você sabe mensurar o impacto financeiro?",
        ["Sim","Não","Parcialmente"],horizontal=True,key="d_if")

    st.markdown("---")
    freq = st.radio("Qual a frequência?",
        ["Diária","Semanal","Quinzenal","Mensal","Esporádica"],horizontal=True,key="d_freq")
    gatilho = ""
    if freq == "Esporádica":
        gatilho = st.text_input(
            f"Qual evento/ação desencadeia a realização {art} {tipo_c}?",key="d_gat")

    st.markdown("<br>",unsafe_allow_html=True)
    c1,c2 = st.columns([1,3])
    with c1:
        if st.button("← Voltar"):
            st.session_state.page="cadastro"; st.rerun()
    with c2:
        if st.button("Próximo → Mapear o processo",
                     disabled=not all([nome_d,ferr,obj,prob,imp_tipo,imp_desc])):
            st.session_state.demanda = dict(
                nome=nome_d,tipo=tipo_c,ferramentas=ferr,objetivo=obj,problema=prob,
                impacto_tipo=imp_tipo,impacto_desc=imp_desc,impacto_fin=imp_fin,
                freq=freq,gatilho=gatilho)
            st.session_state.page="mapeamento"
            st.session_state.fluxograma=""
            st.session_state.iteracoes=0
            st.rerun()

# ── ETAPA 3: MAPEAMENTO ───────────────────────────────────────
SYS_GERAR = """Você é especialista em mapeamento de processos e BPM.
Analise a descrição fornecida e:
1. Crie um **Fluxograma do Processo (Texto)** estruturado usando o formato:
[Início]
   ↓
[passo]
   ↓
[Decisão?]
   ├─ Não → [ação alternativa]
   └─ Sim ↓
[próximo passo]
   ↓
[Fim]

2. Liste os **Pontos de melhoria na descrição do processo**: perguntas objetivas sobre lacunas ou ambiguidades.
3. Finalize com: "Poderia validar se o fluxo está correto e informar se existe algum passo que não foi descrito?"
Responda em português brasileiro."""

SYS_AJUSTAR = """Você é especialista em mapeamento de processos e BPM.
Incorpore os ajustes informados pelo usuário ao fluxograma anterior e:
1. Gere novo **Fluxograma do Processo (Texto)** completo e atualizado
2. Liste novos **Pontos de melhoria** se ainda houver lacunas
3. Pergunte novamente se o fluxo está correto
Responda em português brasileiro."""

def page_mapeamento():
    d      = st.session_state.demanda
    tc     = d["tipo"]
    art    = "da tarefa" if tc=="Tarefa" else "do processo"
    fluxo  = st.session_state.get("fluxograma","")
    it     = st.session_state.get("iteracoes",0)

    section_title("🗺️",f"Mapeamento {art.title()}",
        f"<b style='color:#C4A6FD'>{d['nome']}</b> · {tc} · {d['freq']}")

    if not fluxo:
        st.markdown(f"""
        <div style="background:rgba(155,106,250,0.06);border:1px solid rgba(155,106,250,0.2);
                    border-radius:12px;padding:16px 18px;margin-bottom:16px;
                    font-size:13px;color:#A8A7BC;line-height:1.7;">
            <b style="color:#C4A6FD;">Orientação:</b> Descreva o processo passo a passo, desde o início
            até a conclusão. Informe todas as ações realizadas, sistemas utilizados, critérios de decisão
            e exceções existentes. A descrição deve ser clara o suficiente para que outra pessoa consiga
            executar a atividade apenas seguindo as instruções fornecidas. Este mapeamento será usado para
            documentar o processo, identificar melhorias e avaliar automações.
        </div>""", unsafe_allow_html=True)

        desc = st.text_area(f"Descreva {art} completo e detalhado:",
            key="map_desc",height=240,
            placeholder="Ex: Abra a planilha X, filtre os registros com queda de processamento "
                        "na última semana, copie as colunas A, C, D, cole no e-mail e envie para...")
        c1,c2 = st.columns([1,3])
        with c1:
            if st.button("← Voltar"):
                st.session_state.page="demanda"; st.rerun()
        with c2:
            if st.button("✦ Gerar Fluxograma com IA",
                         disabled=not(desc and len(desc.strip())>30)):
                with st.spinner("✦ Analisando e gerando fluxograma..."):
                    ctx = (f"Demanda: {d['nome']}\nTipo: {tc}\nFerramentas: {d['ferramentas']}\n"
                           f"Objetivo: {d['objetivo']}\nProblema: {d['problema']}\n\n"
                           f"Descrição fornecida pelo colaborador:\n{desc.strip()}")
                    resp = call_ai(SYS_GERAR, ctx)
                st.session_state.fluxograma      = resp
                st.session_state.descricao_livre = desc.strip()
                st.session_state.iteracoes       = 1
                # Adiciona descricao_livre ao dict demanda para o save_to_sheets
                st.session_state.demanda["descricao_livre"] = desc.strip()
                st.rerun()
    else:
        st.markdown(f"""
        <div style="font-size:13px;color:#A8A7BC;margin-bottom:10px;line-height:1.6;">
            <b style="color:#AAEDFF;">✦ IA</b>&nbsp; Com base nas informações que você digitou,
            segue o fluxograma {'da tarefa' if tc=='Tarefa' else 'do processo'}.
            Leia com atenção e verifique se todos os passos constam abaixo.
        </div>""", unsafe_allow_html=True)
        bpmn_box(fluxo)
        st.markdown("---")
        st.markdown("<div style='color:#C4A6FD;font-size:14px;font-weight:600;margin-bottom:10px;'>"
                    "O fluxograma reflete a atividade que você realiza?</div>",
                    unsafe_allow_html=True)
        resposta = st.radio("",
            ["✓ Sim, está correto — finalizar",
             "✎ Não, preciso fazer ajustes"],
            key=f"rev_{it}", label_visibility="collapsed")

        if "ajustes" in resposta:
            ajuste = st.text_area("Descreva os ajustes ou os passos que faltaram:",
                key=f"aj_{it}",height=140,
                placeholder="Ex: Faltou informar que antes de enviar o e-mail preciso salvar cópia no Drive...")
            if st.button("✦ Atualizar Fluxograma",key=f"upd_{it}",
                         disabled=not(ajuste and len(ajuste.strip())>10)):
                with st.spinner("✦ Atualizando fluxograma..."):
                    ctx = f"Fluxograma anterior:\n{fluxo}\n\nAjustes do colaborador:\n{ajuste.strip()}"
                    novo = call_ai(SYS_AJUSTAR, ctx)
                st.session_state.fluxograma = novo
                st.session_state.iteracoes += 1
                st.rerun()
        elif "finalizar" in resposta:
            if st.button("Próximo → Sugestão de melhoria"):
                st.session_state.page="sugestao"; st.rerun()

# ── ETAPA 4: SUGESTÃO ─────────────────────────────────────────
def page_sugestao():
    d = st.session_state.demanda
    art = "da" if d["tipo"]=="Tarefa" else "do"
    section_title("💡","Sugestão de Melhoria",
        f"Finalizamos o mapeamento {art} {d['tipo']} "
        f"<b style='color:#C4A6FD'>{d['nome']}</b>. Agora queremos ouvir sua opinião.")
    st.markdown("""<div style="font-size:15px;color:#E6E0FC;line-height:1.7;margin-bottom:20px;">
        Você identifica alguma oportunidade de melhoria, otimização ou automação para esta atividade?
        Caso sim, descreva sua sugestão.</div>""", unsafe_allow_html=True)
    sug = st.text_area("Sua sugestão (opcional):",key="sug",height=120,
        placeholder="Ex: Este processo poderia ser automatizado via integração entre as ferramentas X e Y...")
    st.markdown("<br>",unsafe_allow_html=True)
    c1,c2 = st.columns([1,3])
    with c1:
        if st.button("← Voltar"):
            st.session_state.page="mapeamento"; st.rerun()
    with c2:
        if st.button("✓ Finalizar e Salvar"):
            with st.spinner("Salvando no Google Sheets..."):
                ok,err = save_to_sheets(
                    st.session_state.usuario, st.session_state.demanda,
                    st.session_state.fluxograma, sug or "")
            st.session_state.update(save_ok=ok,save_err=err,sugestao=sug,page="encerramento")
            st.rerun()

# ── ETAPA 5: ENCERRAMENTO ─────────────────────────────────────
def page_encerramento():
    d  = st.session_state.demanda
    u  = st.session_state.usuario
    ok = st.session_state.get("save_ok")
    er = st.session_state.get("save_err","")
    art = "da" if d["tipo"]=="Tarefa" else "do"

    status_txt   = "✅ Mapeamento salvo no Google Sheets!" if ok \
                   else f"⚠️ Não foi possível salvar automaticamente ({er}). Copie o fluxograma manualmente."
    status_color = "#6FD48A" if ok else "#F4A460"

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(155,106,250,0.14),rgba(69,51,124,0.2));
                border:1px solid rgba(155,106,250,0.3);border-radius:18px;
                padding:40px 32px;text-align:center;margin:20px 0;">
        <div style="font-size:48px;margin-bottom:12px;">✦</div>
        <div style="font-size:22px;font-weight:700;margin-bottom:10px;">Mapeamento concluído!</div>
        <div style="font-size:14px;color:#A8A7BC;line-height:1.8;max-width:480px;margin:0 auto 20px;">
            Obrigado, <b style="color:#C4A6FD;">{u['nome']}</b>!<br>
            {d['tipo']} <b style="color:#fff;">{d['nome']}</b> foi mapeado{'a' if d['tipo']=='Tarefa' else ''} com sucesso.
        </div>
        <div style="font-size:13px;color:{status_color};background:rgba(255,255,255,0.05);
                    border-radius:8px;padding:10px 16px;display:inline-block;margin-bottom:24px;">
            {status_txt}
        </div>
        <div style="background:rgba(155,106,250,0.08);border-radius:10px;padding:14px 18px;
                    max-width:360px;margin:0 auto;text-align:left;font-size:13px;color:#E6E0FC;line-height:1.9;">
            📌 {d['tipo']}: {d['nome']}<br>
            👤 {u['nome']} · {u['time']}<br>
            📅 {d['freq']}{' · ' + d['gatilho'] if d.get('gatilho') else ''}<br>
            🛠️ {d['ferramentas'][:60]}{'...' if len(d['ferramentas'])>60 else ''}
        </div>
    </div>""", unsafe_allow_html=True)

    with st.expander("Ver fluxograma salvo"):
        bpmn_box(st.session_state.get("fluxograma",""))

    st.markdown("""
    <div style="background:rgba(170,237,255,0.06);border:1px solid rgba(170,237,255,0.2);
                border-radius:12px;padding:18px 20px;text-align:center;margin-top:16px;">
        <div style="font-size:15px;font-weight:600;color:#AAEDFF;margin-bottom:12px;">
            Deseja mapear uma nova demanda?</div>
    </div>""", unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        if st.button("✦ Mapear nova demanda", use_container_width=True):
            for k in ["demanda","fluxograma","iteracoes","sugestao",
                      "save_ok","save_err","descricao_livre"]:
                st.session_state.pop(k,None)
            st.session_state.page="demanda"; st.rerun()
    with c2:
        if st.button("Encerrar sessão", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ── MAIN ─────────────────────────────────────────────────────
def main():
    if not st.session_state.get("auth"):
        page_login(); return

    role = st.session_state.get("role","user")
    nome = st.session_state.get("nome","")
    page = st.session_state.get("page","cadastro")

    with st.sidebar:
        st.markdown(f"<div style='color:#C4A6FD;font-weight:700;font-size:15px;"
                    f"margin-bottom:14px;'>Olá, {nome.split()[0]} 👋</div>",
                    unsafe_allow_html=True)
        if role=="user":
            if st.button("↩ Recomeçar",use_container_width=True):
                for k in ["demanda","fluxograma","iteracoes","sugestao",
                          "save_ok","save_err","descricao_livre","usuario"]:
                    st.session_state.pop(k,None)
                st.session_state.page="cadastro"; st.rerun()
        if role=="admin":
            if st.button("⚙️ Painel Admin",use_container_width=True):
                st.session_state.page="admin"; st.rerun()
        st.markdown("---")
        if st.button("Sair",use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    page_header()

    PAGES  = ["cadastro","demanda","mapeamento","sugestao","encerramento"]
    LABELS = ["Cadastro","Demanda","Mapeamento","Melhoria","Concluído"]
    if role=="user" and page in PAGES:
        step_bar(PAGES.index(page), len(PAGES), LABELS)

    {"admin":page_admin,"cadastro":page_cadastro,"demanda":page_demanda,
     "mapeamento":page_mapeamento,"sugestao":page_sugestao,
     "encerramento":page_encerramento}.get(page, page_cadastro)()

if __name__=="__main__":
    main()
