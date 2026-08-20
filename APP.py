import streamlit as st
import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime, timedelta

# Configurazione Pagina - Ottimizzata per iPhone
st.set_page_config(
    page_title="TV Tracker Pro",
    page_icon="📺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Tema Scuro ed Elementi Grafici Stile iOS / Mobile-First
st.markdown("""
<style>
    body { background-color: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .stApp { background-color: #0f172a; }
    .card {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border-radius: 18px; padding: 16px; border: 1px solid #334155;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); margin-bottom: 20px;
    }
    .card-title { font-size: 20px; font-weight: 800; color: #38bdf8; margin-bottom: 6px; }
    .badge-score { background-color: #f59e0b; color: #000; font-weight: bold; padding: 4px 10px; border-radius: 12px; font-size: 13px; float: right; }
    .badge-user-score { background-color: #10b981; color: #ffffff; font-weight: bold; padding: 4px 10px; border-radius: 12px; font-size: 13px; margin-right: 5px; }
    .badge-genre { background-color: #334155; color: #94a3b8; padding: 3px 8px; border-radius: 8px; font-size: 12px; margin-right: 6px; }
    .badge-provider { background-color: #0284c7; color: white; padding: 3px 8px; border-radius: 8px; font-size: 12px; }
    .ep-box { background: #1e293b; border-left: 4px solid #38bdf8; padding: 12px; margin: 12px 0; border-radius: 8px; font-size: 14px; }
    .stButton>button {
        width: 100%; background-color: #2563eb; color: white; font-weight: bold;
        border-radius: 12px; padding: 12px; border: none; font-size: 16px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Funzione per recuperare la locandina in automatico
@st.cache_data(ttl=86400)
def get_poster_url(show_name):
    try:
        url = f"https://api.tvmaze.com/singlesearch/shows?q={requests.utils.quote(show_name)}"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            if data and 'image' in data and data['image']:
                return data['image'].get('medium') or data['image'].get('original')
    except Exception:
        pass
    return "https://via.placeholder.com/210x295/1e293b/94a3b8?text=TV+Show"

# Pulizia e Caricamento Dati
def process_dataframe(df):
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df['TELEFILM'] = df['TELEFILM'].astype(str).str.strip()
    df['STATO'] = df['STATO'].astype(str).str.strip().str.upper().replace({'SCARICATA': 'S'})
    df['GENERE'] = df['GENERE'].astype(str).str.strip().str.upper().replace({'COMEDT': 'COMEDY', 'NAN': 'ALTRO'})
    df['ABBONAMENTO'] = df['ABBONAMENTO'].astype(str).str.strip().str.upper().replace({'NAN': 'SCONOSCIUTO'})
    
    df['GENERE'] = df.groupby('TELEFILM')['GENERE'].transform(lambda x: x.ffill().bfill()).fillna('ALTRO')
    df['ABBONAMENTO'] = df.groupby('TELEFILM')['ABBONAMENTO'].transform(lambda x: x.ffill().bfill()).fillna('NON SPECIFICATO')
    
    for col in ['S', 'E', 'PUNT TOT', 'PUNT VISTE', 'PERC', 'NUOVA', 'FINITO', 'VALORE', 'POS CLASSIFICA']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0)
            
    if 'VALORE' in df.columns:
        df['VALORE'] = df['VALORE'].clip(lower=0.0, upper=100.0)
        
    df['DATA_VISIONA'] = pd.to_datetime(df['DATA'].astype(str), format='%d/%m/%y', errors='coerce')
    return df

if 'df' not in st.session_state:
    if os.path.exists('TELEFILM2024_LIGHT.csv'):
        raw_df = pd.read_csv('TELEFILM2024_LIGHT.csv', sep=';', encoding='utf-8-sig', low_memory=False)
        st.session_state.df = process_dataframe(raw_df)
    else:
        st.session_state.df = None

# Punteggi Generi Personalizzabili
DEFAULT_GENRE_SCORES = {
    'SCI-FI': 15, 'THRILLER': 14, 'DRAMA': 12, 'ACTION': 11,
    'SUPERNATURAL': 10, 'CRIME': 10, 'FANTASY': 9, 'LEGAL': 8,
    'SPY': 8, 'HORROR': 7, 'MEDICAL': 6, 'ANIMATION': 5, 'COMEDY': 5, 'ALTRO': 0
}

if 'genre_scores' not in st.session_state:
    st.session_state.genre_scores = DEFAULT_GENRE_SCORES.copy()

# Utility Funzioni Modifica Puntate
def reset_show_progress(show_name):
    """Azzera le puntate viste e mette la prima puntata (S01E01) come Pronta (S)."""
    mask = st.session_state.df['TELEFILM'] == show_name
    st.session_state.df.loc[mask, 'STATO'] = 'N'
    # Prima puntata 'S'
    first_idx = st.session_state.df[mask].sort_values(by=['S', 'E']).index[0]
    st.session_state.df.loc[first_idx, 'STATO'] = 'S'

def set_show_watched_count(show_name, watched_count):
    """Imposta esattamente quante puntate sono state viste."""
    mask = st.session_state.df['TELEFILM'] == show_name
    sorted_indices = st.session_state.df[mask].sort_values(by=['S', 'E']).index
    for i, idx in enumerate(sorted_indices):
        if i < watched_count:
            st.session_state.df.loc[idx, 'STATO'] = 'V'
        elif i == watched_count:
            st.session_state.df.loc[idx, 'STATO'] = 'S'
        else:
            st.session_state.df.loc[idx, 'STATO'] = 'N'

# Header e Fallback File Uploader
st.title("📺 TV Tracker Pro")

if st.session_state.df is None:
    st.warning("⚠️ File `TELEFILM2024_LIGHT.csv` non trovato sul server.")
    uploaded_file = st.file_uploader("Carica il tuo file CSV per iniziare:", type=['csv'])
    if uploaded_file is not None:
        raw_df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig', low_memory=False)
        st.session_state.df = process_dataframe(raw_df)
        st.success("Database caricato con successo!")
        st.rerun()
    st.stop()

# Calcolo Punteggio Algoritmo
def calculate_score(series_df):
    valore = float(series_df['VALORE'].iloc[0])
    voto_personale = min(100.0, max(0.0, valore)) if valore > 0 else 70.0
    comp_voto = voto_personale * 0.20 # max 20 pt
    
    genere = series_df['GENERE'].iloc[0]
    p_genere = st.session_state.genre_scores.get(genere, 5)
    
    ready_eps = series_df[series_df['STATO'] == 'S']
    if len(ready_eps) == 0:
        return 0
    
    # 1. BOOSTER PROGRESSO VISIONE (fino a 40 pt in base alle puntate viste)
    tot_eps = len(series_df)
    viste_eps = len(series_df[series_df['STATO'] == 'V'])
    perc_viste = viste_eps / tot_eps if tot_eps > 0 else 0
    bonus_progresso = round(perc_viste * 40.0, 1)
    
    # 2. MALUS VETUSTÀ PUNTATA
    first_ready = ready_eps.sort_values(by=['S', 'E']).iloc[0]
    malus_eta = 0
    if pd.notnull(first_ready['DATA_VISIONA']):
        giorni_attesa = (datetime.now() - first_ready['DATA_VISIONA']).days
        if giorni_attesa > 30:
            malus_eta = min(20, (giorni_attesa - 30) // 15 * 2)
            
    # 3. BONUS NUOVA SERIE RIDOTTO (5 pt max)
    is_nuova = series_df['NUOVA'].iloc[0] == 1
    has_seen_any = viste_eps > 0
    bonus_nuova = 5 if (is_nuova and not has_seen_any) else 0
    
    # Inerzia recente
    three_months = datetime.now() - timedelta(days=90)
    recent = series_df[(series_df['STATO'] == 'V') & (series_df['DATA_VISIONA'] >= three_months)]
    bonus_inerzia = min(15, len(recent) * 2)
    
    # Bonus intera stagione pronta
    curr_season = first_ready['S']
    season_eps = series_df[series_df['S'] == curr_season]
    bonus_season = 10 if (season_eps['STATO'] == 'S').all() else 0
    
    # Malus cancellata
    is_finito = series_df['FINITO'].iloc[0] == 1
    malus_cancellata = 15 if is_finito else 0
    
    totale = comp_voto + p_genere + bonus_progresso + bonus_inerzia + bonus_season + bonus_nuova - malus_eta - malus_cancellata
    return round(max(0.0, totale), 1)

# Funzione per Renderizzare le Card
def render_show_cards(rank_df):
    for idx, row in rank_df.iterrows():
        poster_url = get_poster_url(row['show'])
        val_txt = f"{row['valore']:.0f}/100" if row['valore'] > 0 else "N/D"
        
        col_img, col_info = st.columns([1, 2.2])
        with col_img:
            st.image(poster_url, use_container_width=True)
            
        with col_info:
            st.markdown(f"""
            <div style="margin-bottom: 6px;">
                <span class="badge-score">⭐ {row['score']} pt</span>
                <span class="badge-user-score">👤 {val_txt}</span>
            </div>
            <div class="card-title">{row['show']}</div>
            <div>
                <span class="badge-genre">{row['genere']}</span>
                <span class="badge-provider">📺 {row['provider']}</span>
            </div>
            <div class="ep-box">
                <div><strong>Prossimo:</strong> S{row['season']:02d}E{row['episode']:02d}</div>
                <div style="font-size: 17px; font-weight: 800; color: #10b981; margin-top: 6px;">
                    📊 Viste {row['viste']} / {row['totali']} ({row['perc']:.0f}%)
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        col_b1, col_b2, col_b3 = st.columns([2, 1, 1])
        with col_b1:
            if st.button(f"▶️ S{row['season']:02d}E{row['episode']:02d}", key=f"btn_v_{row['show']}"):
                mask = (st.session_state.df['TELEFILM'] == row['show']) & \
                       (st.session_state.df['S'] == row['season']) & \
                       (st.session_state.df['E'] == row['episode'])
                st.session_state.df.loc[mask, 'STATO'] = 'V'
                st.session_state.df.loc[mask, 'DATA'] = datetime.now().strftime('%d/%m/%y')
                st.session_state.df.loc[mask, 'DATA_VISIONA'] = datetime.now()
                st.success(f"Segnato S{row['season']:02d}E{row['episode']:02d} come VISTO!")
                st.rerun()
        with col_b2:
            with st.popover("✏️ Voto"):
                st.caption("ℹ️ Voto massimo: 100")
                val_default = min(100.0, max(0.0, float(row['valore'])))
                nuovo_voto = st.number_input(
                    f"Voto per {row['show']}",
                    min_value=0.0,
                    max_value=100.0,
                    value=val_default,
                    step=5.0,
                    key=f"inp_val_{row['show']}"
                )
                if st.button("Salva Voto", key=f"save_val_{row['show']}"):
                    mask_show = st.session_state.df['TELEFILM'] == row['show']
                    st.session_state.df.loc[mask_show, 'VALORE'] = nuovo_voto
                    st.success("Voto salvato!")
                    st.rerun()
        with col_b3:
            with st.popover("🛠️ Gestisci"):
                st.markdown(f"**Gestione Puntate per {row['show']}**")
                
                # Reset veloce
                if st.button("🔄 Reset (0 Viste)", key=f"reset_{row['show']}"):
                    reset_show_progress(row['show'])
                    st.success("Progresso azzerato!")
                    st.rerun()
                
                st.markdown("---")
                # Imposta esatto viste
                new_count = st.number_input(
                    "Puntate Viste Esatte:",
                    min_value=0,
                    max_value=int(row['totali']),
                    value=int(row['viste']),
                    step=1,
                    key=f"count_{row['show']}"
                )
                if st.button("Salva Progresso", key=f"save_prog_{row['show']}"):
                    set_show_watched_count(row['show'], new_count)
                    st.success("Progresso aggiornato!")
                    st.rerun()

        st.markdown("<hr style='border:1px solid #1e293b; margin:15px 0;'>", unsafe_allow_html=True)

# Tab principali
tab1, tab2, tab3, tab4 = st.tabs(["🛋️ Divano", "📥 Aggiorna N➜S", "📁 Completate", "⚙️ Impostazioni"])

# TAB 1: DIVANO
with tab1:
    df_curr = st.session_state.df
    shows_with_S = df_curr[df_curr['STATO'] == 'S']['TELEFILM'].unique()
    
    if len(shows_with_S) == 0:
        st.info("🎉 Non hai nessuna puntata in stato 'S' (Pronta da vedere)! Vai nella scheda 'Aggiorna N➜S' per scaricarne altre.")
    else:
        rankings = []
        for show in shows_with_S:
            s_df = df_curr[df_curr['TELEFILM'] == show]
            score = calculate_score(s_df)
            valore_pers = float(s_df['VALORE'].iloc[0])
            next_ep = s_df[s_df['STATO'] == 'S'].sort_values(by=['S', 'E']).iloc[0]
            
            tot_eps = len(s_df)
            viste_eps = len(s_df[s_df['STATO'] == 'V'])
            
            rankings.append({
                'show': show, 'score': score, 'valore': valore_pers,
                'season': int(next_ep['S']), 'episode': int(next_ep['E']),
                'genere': s_df['GENERE'].iloc[0], 'provider': s_df['ABBONAMENTO'].iloc[0],
                'viste': viste_eps, 'totali': tot_eps, 'perc': (viste_eps / tot_eps * 100) if tot_eps > 0 else 0
            })
        
        full_rank_df = pd.DataFrame(rankings).sort_values(by='score', ascending=False)
        
        df_started = full_rank_df[full_rank_df['viste'] > 0]
        df_new = full_rank_df[full_rank_df['viste'] == 0]
        
        sub_tab1, sub_tab2 = st.tabs([f"▶️ In Corso ({len(df_started)})", f"🆕 Da Iniziare ({len(df_new)})"])
        
        with sub_tab1:
            if len(df_started) == 0:
                st.caption("Nessuna serie già iniziata tra quelle pronte.")
            else:
                render_show_cards(df_started)
                
        with sub_tab2:
            if len(df_new) == 0:
                st.caption("Nessuna nuova serie da iniziare tra quelle pronte.")
            else:
                render_show_cards(df_new)

# TAB 2: AGGIORNA N -> S
with tab2:
    st.subheader("📥 Aggiorna Puntate da Scaricare (N ➜ S)")
    df_curr = st.session_state.df
    shows_with_N = df_curr[df_curr['STATO'] == 'N']['TELEFILM'].unique()
    
    if len(shows_with_N) == 0:
        st.success("✨ Non ci sono puntate in stato 'N' da aggiornare!")
    else:
        st.write(f"Ci sono **{len(shows_with_N)}** serie con puntate da scaricare.")
        for show in shows_with_N:
            s_df = df_curr[df_curr['TELEFILM'] == show]
            n_eps = s_df[s_df['STATO'] == 'N'].sort_values(by=['S', 'E'])
            if len(n_eps) > 0:
                oldest_n = n_eps.iloc[0]
                poster_url = get_poster_url(show)
                
                with st.expander(f"📌 {show} - Prossima: S{int(oldest_n['S']):02d}E{int(oldest_n['E']):02d}", expanded=True):
                    col_p, col_d = st.columns([1, 2])
                    with col_p:
                        st.image(poster_url, use_container_width=True)
                    with col_d:
                        st.write(f"**Piattaforma:** {s_df['ABBONAMENTO'].iloc[0]}")
                        st.write(f"**Genere:** {s_df['GENERE'].iloc[0]}")
                        st.write(f"**Voto Personale:** {s_df['VALORE'].iloc[0]:.0f}/100")
                        
                        if st.button(f"✅ Pronta S{int(oldest_n['S']):02d}E{int(oldest_n['E']):02d}", key=f"btn_s_{show}_{oldest_n['S']}_{oldest_n['E']}"):
                            mask = (st.session_state.df['TELEFILM'] == show) & (st.session_state.df['S'] == oldest_n['S']) & (st.session_state.df['E'] == oldest_n['E'])
                            st.session_state.df.loc[mask, 'STATO'] = 'S'
                            st.rerun()
                            
                        if st.button(f"⏩ Tutta la Stagione {int(oldest_n['S'])} pronta", key=f"btn_s_all_{show}_{oldest_n['S']}"):
                            mask = (st.session_state.df['TELEFILM'] == show) & (st.session_state.df['S'] == oldest_n['S']) & (st.session_state.df['STATO'] == 'N')
                            st.session_state.df.loc[mask, 'STATO'] = 'S'
                            st.rerun()

# TAB 3: COMPLETATE
with tab3:
    st.subheader("📁 Archivio Serie Completate")
    completed_shows = [
        {'show': show, 'tot_episodes': len(group), 'genere': group['GENERE'].iloc[0], 'provider': group['ABBONAMENTO'].iloc[0], 'voto': group['VALORE'].iloc[0]}
        for show, group in st.session_state.df.groupby('TELEFILM') if (group['STATO'] == 'V').all()
    ]
    if len(completed_shows) > 0:
        st.dataframe(pd.DataFrame(completed_shows), use_container_width=True)
    else:
        st.info("Nessuna serie completata al 100%.")

# TAB 4: IMPOSTAZIONI, CORREZIONE DATI E BACKUP
with tab4:
    st.subheader("⚙️ Impostazioni e Gestione")
    
    # STRUMENTO DI CORREZIONE MANUALE SERIE
    with st.expander("✏️ Correzione Manuale Dati Serie / Episodi", expanded=True):
        st.caption("Seleziona una serie per modificare manualmente lo stato delle singole puntate o resettare i dati errati:")
        
        all_shows = sorted(st.session_state.df['TELEFILM'].unique())
        selected_show = st.selectbox("Seleziona la Serie TV:", all_shows, index=all_shows.index("The Capture") if "The Capture" in all_shows else 0)
        
        if selected_show:
            show_mask = st.session_state.df['TELEFILM'] == selected_show
            sub_df = st.session_state.df[show_mask].sort_values(by=['S', 'E'])
            
            tot_e = len(sub_df)
            v_e = len(sub_df[sub_df['STATO'] == 'V'])
            s_e = len(sub_df[sub_df['STATO'] == 'S'])
            n_e = len(sub_df[sub_df['STATO'] == 'N'])
            
            st.write(f"**Stato attuale:** Viste: `{v_e}` | Pronte (S): `{s_e}` | Da scaricare (N): `{n_e}` (Totale: `{tot_e}`)")
            
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                if st.button(f"🔄 Reset '{selected_show}' a 0 Viste", key="tab4_reset"):
                    reset_show_progress(selected_show)
                    st.success(f"Progresso di {selected_show} azzerato!")
                    st.rerun()
            with c_m2:
                new_v_count = st.number_input("Imposta quante viste:", min_value=0, max_value=tot_e, value=v_e, step=1, key="tab4_v_count")
                if st.button("Salva Conteggio", key="tab4_save_count"):
                    set_show_watched_count(selected_show, new_v_count)
                    st.success("Conteggio aggiornato!")
                    st.rerun()
                    
            st.markdown("**Modifica puntate singole nella tabella:**")
            st.caption("Significato stati: `V` = Visto | `S` = Pronto/Scaricato | `N` = Non scaricato")
            
            # Tabella Interattiva Modificabile
            editable_df = sub_df[['S', 'E', 'STATO', 'DATA']].copy()
            edited_data = st.data_editor(
                editable_df,
                column_config={
                    "S": st.column_config.NumberColumn("Stagione", disabled=True),
                    "E": st.column_config.NumberColumn("Episodio", disabled=True),
                    "STATO": st.column_config.SelectboxColumn("Stato", options=["V", "S", "N"], required=True),
                    "DATA": st.column_config.TextColumn("Data Visione")
                },
                use_container_width=True,
                hide_index=True,
                key=f"editor_{selected_show}"
            )
            
            if st.button("💾 Salva Modifiche Tabella Puntate", key="save_table_edits"):
                for _, ed_row in edited_data.iterrows():
                    m_ep = (st.session_state.df['TELEFILM'] == selected_show) & \
                           (st.session_state.df['S'] == ed_row['S']) & \
                           (st.session_state.df['E'] == ed_row['E'])
                    st.session_state.df.loc[m_ep, 'STATO'] = ed_row['STATO']
                    st.session_state.df.loc[m_ep, 'DATA'] = str(ed_row['DATA']) if pd.notnull(ed_row['DATA']) else ''
                st.success("Modifiche salvate con successo nel database!")
                st.rerun()

    st.markdown("---")

    with st.expander("🎭 Personalizza Punteggi Generi (Algoritmo)", expanded=False):
        st.caption("Modifica i punti bonus assegnati dall'algoritmo a ciascun genere:")
        updated_scores = {}
        for g, score in st.session_state.genre_scores.items():
            updated_scores[g] = st.number_input(f"Punti per {g}", min_value=0, value=int(score), key=f"g_score_{g}")
        if st.button("💾 Salva Punteggi Generi"):
            st.session_state.genre_scores = updated_scores
            st.success("Punteggi generi aggiornati!")
            st.rerun()
            
    st.markdown("---")
    
    st.subheader("📥 Download Backup Database")
    csv_bytes = st.session_state.df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="💾 Scarica File CSV Aggiornato",
        data=csv_bytes,
        file_name=f"TELEFILM_BACKUP_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
