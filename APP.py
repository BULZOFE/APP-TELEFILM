import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="TV Tracker Pro", page_icon="📺", layout="wide"
)

# --- DATI DI DEFAULT ---
DEFAULT_DATA = [
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
]

# --- RIPRISTINO DI SICUREZZA ---
# Se i dati non esistono o se le colonne sono corrotte, ricrea la tabella di default
if "df" not in st.session_state or "viste" not in st.session_state.df.columns:
  st.session_state.df = pd.DataFrame(DEFAULT_DATA)

# Pulsante di reset manuale nella barra laterale
with st.sidebar:
  st.header("⚙️ Opzioni")
  if st.button("🧹 Ripristina Serie di Default", use_container_width=True):
    st.session_state.df = pd.DataFrame(DEFAULT_DATA)
    st.rerun()


# --- FUNZIONI DI SUPPORTO ---
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


# --- INTERFACCIA PRINCIPALE ---
st.title("📺 Tracker Serie TV")

df = st.session_state.df

# Metriche in alto
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Serie Totali", len(df))
col_m2.metric(
    "In Corso", len(df[(df["viste"] > 0) & (df["viste"] < df["totali"])])
)
col_m3.metric("Completate", len(df[df["viste"] == df["totali"]]))
col_m4.metric("Episodi Visti", int(df["viste"].sum()))

st.divider()


# Funzione di rendering lista serie
def render_show_list(filtered_df):
  if filtered_df.empty:
    st.info("Nessuna serie presente.")
    return

  for idx, row in filtered_df.iterrows():
    show_name = row["show"]
    viste = int(row["viste"])
    totali = int(row["totali"])
    stagione = int(row["stagione"])
    genere = row["genere"]
    is_fav = row["preferito"]

    pct = int((viste / totali) * 100) if totali > 0 else 0
    fav_icon = "⭐" if is_fav else "☆"

    with st.container():
      st.subheader(f"{show_name} (S{stagione} • {genere})")
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
            st.rerun()
        else:
          st.button(
              "✅ Finito",
              key=f"btn_done_{idx}",
              disabled=True,
              use_container_width=True,
          )

      with c_popover:
        count_key = f"input_viste_{idx}"

        with st.popover("🛠️ Gestisci", use_container_width=True):
          st.markdown(f"### ⚙️ {show_name}")

          if count_key not in st.session_state:
            st.session_state[count_key] = viste

          st.number_input(
              "Puntate viste esatte:",
              min_value=0,
              max_value=totali,
              step=1,
              key=count_key,
          )

          st.markdown("---")
          btn_reset, btn_save, btn_exit = st.columns(3)

          with btn_reset:
            # RESET: Imposta a 0 e NON chiude il pop-up
            if st.button("🔄 Reset", key=f"reset_{idx}", use_container_width=True):
              st.session_state[count_key] = 0

          with btn_save:
            # SALVA: Salva le modifiche e CHIUDE il pop-up
            if st.button(
                "💾 Salva",
                key=f"save_{idx}",
                type="primary",
                use_container_width=True,
            ):
              set_show_watched_count(show_name, st.session_state[count_key])
              st.toast(f"Progresso di '{show_name}' salvato!")
              st.rerun()

          with btn_exit:
            # ESCI: Annulla e CHIUDE il pop-up senza salvare
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

      st.markdown("---")


render_show_list(st.session_state.df)
