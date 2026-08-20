import datetime
import pandas as pd
import streamlit as st

# Configurazione Pagina
st.set_page_config(
    page_title="TV Tracker Pro",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS Personalizzato
st.markdown(
    """
<style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .show-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .badge-completed {
        background-color: #059669;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-in-progress {
        background-color: #0284c7;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-not-started {
        background-color: #475569;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Inizializzazione Dati
def init_data():
  if "df" not in st.session_state:
    data = [
        {
            "show": "Breaking Bad",
            "stagione": 1,
            "viste": 5,
            "totali": 7,
            "genere": "Drammatico",
            "preferito": True,
        },
        {
            "show": "Stranger Things",
            "stagione": 4,
            "viste": 9,
            "totali": 9,
            "genere": "Sci-Fi",
            "preferito": True,
        },
        {
            "show": "The Bear",
            "stagione": 2,
            "viste": 3,
            "totali": 10,
            "genere": "Commedia/Dramma",
            "preferito": False,
        },
        {
            "show": "Attack on Titan",
            "stagione": 1,
            "viste": 0,
            "totali": 25,
            "genere": "Anime",
            "preferito": False,
        },
        {
            "show": "Planet Earth III",
            "stagione": 1,
            "viste": 6,
            "totali": 6,
            "genere": "Documentario",
            "preferito": False,
        },
    ]
    st.session_state.df = pd.DataFrame(data)


init_data()


# Funzioni di Modifica Stato Database
def set_show_watched_count(show_name, count):
  st.session_state.df.loc[
      st.session_state.df["show"] == show_name, "viste"
  ] = int(count)


def increment_show_count(show_name):
  idx = st.session_state.df[st.session_state.df["show"] == show_name].index
  if not idx.empty:
    curr = st.session_state.df.loc[idx[0], "viste"]
    tot = st.session_state.df.loc[idx[0], "totali"]
    if curr < tot:
      st.session_state.df.loc[idx[0], "viste"] = curr + 1


def toggle_favorite(show_name):
  idx = st.session_state.df[st.session_state.df["show"] == show_name].index
  if not idx.empty:
    st.session_state.df.loc[idx[0], "preferito"] = not st.session_state.df.loc[
        idx[0], "preferito"
    ]


# Intestazione App
st.title("📺 Tracker Serie TV & Show")
st.caption("Monitora i tuoi progressi di visione e gestisci le tue serie.")

# Metric Dashboard
df = st.session_state.df
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
total_shows = len(df)
completed_shows = len(df[df["viste"] == df["totali"]])
in_progress_shows = len(df[(df["viste"] > 0) & (df["viste"] < df["totali"])])
total_episodes_watched = int(df["viste"].sum())

col_m1.metric("Serie Totali", total_shows)
col_m2.metric("In Corso", in_progress_shows)
col_m3.metric("Completate", completed_shows)
col_m4.metric("Episodi Visti", total_episodes_watched)

st.divider()

# Tab per Filtri
tab_all, tab_in_progress, tab_completed, tab_favs, tab_add = st.tabs([
    "📋 Tutti gli Show",
    "🍿 In Corso",
    "✅ Completati",
    "⭐ Preferiti",
    "➕ Aggiungi Serie",
])


# Render scheda Serie TV
def render_show_list(filtered_df):
  if filtered_df.empty:
    st.info("Nessuna serie trovata in questa sezione.")
    return

  for idx, row in filtered_df.iterrows():
    show_name = row["show"]
    viste = int(row["viste"])
    totali = int(row["totali"])
    stagione = int(row["stagione"])
    genere = row["genere"]
    is_fav = row["preferito"]

    pct = int((viste / totali) * 100) if totali > 0 else 0

    if viste == totali:
      badge_html = '<span class="badge-completed">COMPLETATO</span>'
    elif viste > 0:
      badge_html = '<span class="badge-in-progress">IN CORSO</span>'
    else:
      badge_html = '<span class="badge-not-started">DA INIZIARE</span>'

    fav_icon = "⭐" if is_fav else "☆"

    with st.container():
      st.markdown(
          f"""
            <div class="show-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <h3 style="margin: 0; padding: 0; font-size: 1.2rem;">{show_name} {badge_html}</h3>
                    <span style="color: #94a3b8; font-size: 0.85rem;">Stagione {stagione} • {genere}</span>
                </div>
            </div>
            """,
          unsafe_allow_html=True,
      )

      st.progress(pct / 100)

      c_info, c_plus1, c_popover, c_fav = st.columns([3, 1.5, 1.5, 1])

      with c_info:
        st.caption(f"Avanzamento: **{viste}/{totali}** puntate ({pct}%)")

      with c_plus1:
        if viste < totali:
          if st.button(
              "➕ +1 Ep", key=f"btn_plus_{idx}", use_container_width=True
          ):
            increment_show_count(show_name)
            st.toast(f"Aggiunto 1 episodio a '{show_name}'!")
            st.rerun()
        else:
          st.button(
              "✅ Finito",
              key=f"btn_done_{idx}",
              disabled=True,
              use_container_width=True,
          )

      with c_popover:
        # Chiave univoca per l'input di questa serie
        count_key = f"input_viste_{idx}"

        # Pop-up di Gestione Avanzata
        with st.popover("🛠️ Gestisci", use_container_width=True):
          st.markdown(f"### ⚙️ {show_name}")
          st.caption(f"Stagione {stagione} • Totale puntate: **{totali}**")

          # Inizializza lo stato dell'input se non presente
          if count_key not in st.session_state:
            st.session_state[count_key] = viste

          # Input numerico
          st.number_input(
              "Puntate viste esatte:",
              min_value=0,
              max_value=totali,
              step=1,
              key=count_key,
          )

          st.markdown("---")

          # Pulsanti di Azione all'interno del Pop-up
          btn_reset, btn_save, btn_exit = st.columns(3)

          with btn_reset:
            # RESET: Imposta l'input a 0 nel session_state, NON salva nel DB e NON fa st.rerun() -> Il pop-up rimane APERTO!
            if st.button("🔄 Reset", key=f"reset_{idx}", use_container_width=True):
              st.session_state[count_key] = 0

          with btn_save:
            # SALVA: Salva il valore nel DB, mostra toast e fa st.rerun() -> Il pop-up si CHIUDE!
            if st.button(
                "💾 Salva",
                key=f"save_{idx}",
                type="primary",
                use_container_width=True,
            ):
              new_val = st.session_state[count_key]
              set_show_watched_count(show_name, new_val)
              st.toast(
                  f"Progresso di '{show_name}' salvato a {new_val}/{totali}!"
              )
              st.rerun()

          with btn_exit:
            # ESCI: Ripristina il valore originale (annullando modifiche o reset) e fa st.rerun() -> Il pop-up si CHIUDE senza salvare!
            if st.button(
                "❌ Esci", key=f"exit_{idx}", use_container_width=True
            ):
              st.session_state[count_key] = viste
              st.rerun()

      with c_fav:
        if st.button(
            fav_icon, key=f"btn_fav_{idx}", use_container_width=True
        ):
          toggle_favorite(show_name)
          st.rerun()

      st.markdown("<br>", unsafe_allow_html=True)


# Rendering delle varie schede
with tab_all:
  render_show_list(st.session_state.df)

with tab_in_progress:
  df_prog = st.session_state.df[
      (st.session_state.df["viste"] > 0)
      & (st.session_state.df["viste"] < st.session_state.df["totali"])
  ]
  render_show_list(df_prog)

with tab_completed:
  df_comp = st.session_state.df[
      st.session_state.df["viste"] == st.session_state.df["totali"]
  ]
  render_show_list(df_comp)

with tab_favs:
  df_fav = st.session_state.df[st.session_state.df["preferito"] == True]
  render_show_list(df_fav)

with tab_add:
  st.subheader("➕ Aggiungi Nuova Serie TV")
  with st.form("add_show_form", clear_on_submit=True):
    new_title = st.text_input("Titolo della Serie TV:")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
      new_season = st.number_input("Stagione:", min_value=1, value=1)
      new_genre = st.selectbox(
          "Genere:",
          [
              "Drammatico",
              "Commedia",
              "Sci-Fi",
              "Anime",
              "Documentario",
              "Thriller",
              "Azione",
          ],
      )
    with col_f2:
      new_tot = st.number_input("Totale Puntate:", min_value=1, value=10)
      new_viste = st.number_input(
          "Puntate già Viste:", min_value=0, max_value=new_tot, value=0
      )

    submitted = st.form_submit_button("Aggiungi Serie")
    if submitted:
      if new_title.strip() == "":
        st.error("Il titolo non può essere vuoto.")
      else:
        new_row = {
            "show": new_title.strip(),
            "stagione": int(new_season),
            "viste": int(new_viste),
            "totali": int(new_tot),
            "genere": new_genre,
            "preferito": False,
        }
        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame([new_row])], ignore_index=True
        )
        st.success(f"Serie '{new_title}' aggiunta con successo!")
        st.rerun()
