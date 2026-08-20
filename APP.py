import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="TV Tracker Pro", page_icon="📺", layout="wide"
)

# ⚠️ INSERISCI QUI IL NOME ESATTO DEL TUO FILE CSV (es. "serie.csv", "shows.csv", "serie_tv.csv")
NOME_FILE_CSV = "TELEFILM_LIGHT.csv"


# --- CARICAMENTO E SALVATAGGIO CSV ---
def load_data():
  if os.path.exists(NOME_FILE_CSV):
    try:
      df = pd.read_csv(NOME_FILE_CSV)
      # Verifica la presenza delle colonne necessarie
      req_cols = {"show", "stagione", "viste", "totali", "genere", "preferito"}
      if req_cols.issubset(df.columns):
        return df
      else:
        st.error(
            f"Il file '{NOME_FILE_CSV}' esiste ma mancano alcune colonne"
            f" obbligatorie: {req_cols - set(df.columns)}"
        )
    except Exception as e:
      st.error(f"Errore nella lettura del file CSV: {e}")
  else:
    st.warning(
        f"Impossibile trovare il file '{NOME_FILE_CSV}' nella cartella dell'app."
    )

  # Ritorna un DataFrame vuoto con le colonne giuste se il file non viene trovato
  return pd.DataFrame(
      columns=["show", "stagione", "viste", "totali", "genere", "preferito"]
  )


def save_data():
  if "df" in st.session_state:
    st.session_state.df.to_csv(NOME_FILE_CSV, index=False)


# Inizializzazione dello stato dalla lettura del CSV
if "df" not in st.session_state:
  st.session_state.df = load_data()


# --- FUNZIONI DI AGGIORNAMENTO DATI ---
def set_show_watched_count(show_name, count):
  st.session_state.df.loc[
      st.session_state.df["show"] == show_name, "viste"
  ] = int(count)
  save_data()


def increment_show_count(show_name):
  idx = st.session_state.df[st.session_state.df["show"] == show_name].index
  if not idx.empty:
    curr = st.session_state.df.loc[idx[0], "viste"]
    tot = st.session_state.df.loc[idx[0], "totali"]
    if curr < tot:
      st.session_state.df.loc[idx[0], "viste"] = curr + 1
      save_data()


def toggle_favorite(show_name):
  idx = st.session_state.df[st.session_state.df["show"] == show_name].index
  if not idx.empty:
    st.session_state.df.loc[idx[0], "preferito"] = not st.session_state.df.loc[
        idx[0], "preferito"
    ]
    save_data()


# --- INTERFACCIA UTENTE ---
st.title("📺 Tracker Serie TV (da CSV)")

df = st.session_state.df

# Metriche generali
if not df.empty:
  col_m1, col_m2, col_m3, col_m4 = st.columns(4)
  col_m1.metric("Serie Totali", len(df))
  col_m2.metric(
      "In Corso", len(df[(df["viste"] > 0) & (df["viste"] < df["totali"])])
  )
  col_m3.metric("Completate", len(df[df["viste"] == df["totali"]]))
  col_m4.metric("Episodi Visti", int(df["viste"].sum()))
  st.divider()

tab_list, tab_add = st.tabs(["📋 Le mie Serie", "➕ Aggiungi Serie"])

with tab_list:
  if df.empty:
    st.error(
        f"Nessun dato trovato nel file `{NOME_FILE_CSV}`. Controlla che il nome"
        " del file nel codice sia corretto e che si trovi nella stessa cartella"
        " di `APP.py`."
    )
  else:
    for idx, row in df.iterrows():
      show_name = row["show"]
      viste = int(row["viste"])
      totali = int(row["totali"])
      stagione = int(row["stagione"])
      genere = row["genere"]
      is_fav = bool(row["preferito"])

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

          # Pop-up di gestione
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
              # Porta a 0 SENZA salvare sul CSV e SENZA chiudere il pop-up
              if st.button(
                  "🔄 Reset", key=f"reset_{idx}", use_container_width=True
              ):
                st.session_state[count_key] = 0

            with btn_save:
              # Salva sul CSV e CHIUDE il pop-up
              if st.button(
                  "💾 Salva",
                  key=f"save_{idx}",
                  type="primary",
                  use_container_width=True,
              ):
                set_show_watched_count(show_name, st.session_state[count_key])
                st.toast(f"Progresso salvato nel file CSV per '{show_name}'!")
                st.rerun()

            with btn_exit:
              # Ripristina valore e CHIUDE il pop-up senza salvare
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

with tab_add:
  st.subheader("➕ Aggiungi Nuova Serie al CSV")
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

    submitted = st.form_submit_button("Aggiungi e Scrivi su CSV")
    if submitted:
      if new_title.strip() != "":
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
        save_data()
        st.success(f"Serie '{new_title}' aggiunta al CSV!")
        st.rerun()
