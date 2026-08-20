import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="TV Tracker Pro", page_icon="📺", layout="wide"
)

# ⚠️ INSERISCI IL NOME ESATTO DEL TUO FILE CSV
NOME_FILE_CSV = "TELEFILM_LIGHT.csv"

# LOCANDINA DI DEFAULT (se non presente nel CSV o se il link manca)
PLACEHOLDER_POSTER = "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?q=80&w=400&auto=format&fit=crop"

# --- CSS PERSONALIZZATO (FLASH CARD & BADGE) ---
st.markdown(
    """
<style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* Contenitore Flash Card */
    .show-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .show-card:hover {
        border-color: #38bdf8;
    }

    /* Badge di Stato */
    .badge-completed {
        background-color: #059669;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-in-progress {
        background-color: #0284c7;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-not-started {
        background-color: #475569;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }

    /* Styling Locandina */
    .poster-img {
        border-radius: 8px;
        object-fit: cover;
        width: 100%;
        height: 180px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- GESTIONE E CARICAMENTO CSV ---
def load_data():
  if os.path.exists(NOME_FILE_CSV):
    try:
      df = pd.read_csv(NOME_FILE_CSV)

      # Assicura le colonne fondamentali
      req_cols = ["show", "stagione", "viste", "totali", "genere", "preferito"]
      for col in req_cols:
        if col not in df.columns:
          if col == "preferito":
            df[col] = False
          elif col in ["viste", "totali", "stagione"]:
            df[col] = 0
          else:
            df[col] = "N/D"

      # Individua o crea la colonna per le locandine
      img_cols = [
          c
          for c in df.columns
          if c.lower()
          in ["locandina", "immagine", "copertina", "poster", "image"]
      ]
      if img_cols:
        df["locandina_path"] = df[img_cols[0]].fillna(PLACEHOLDER_POSTER)
      else:
        df["locandina_path"] = PLACEHOLDER_POSTER

      return df
    except Exception as e:
      st.error(f"Errore durante la lettura del file CSV: {e}")

  st.warning(
      f"File `{NOME_FILE_CSV}` non trovato. Verifica il percorso o aggiungi la"
      " prima serie."
  )
  return pd.DataFrame(
      columns=[
          "show",
          "stagione",
          "viste",
          "totali",
          "genere",
          "preferito",
          "locandina_path",
      ]
  )


def save_data():
  if "df" in st.session_state:
    save_df = st.session_state.df.copy()
    # Rimuove la colonna temporanea creata per la gestione interna se presente
    if (
        "locandina_path" in save_df.columns
        and "locandina_path" not in pd.read_csv(NOME_FILE_CSV).columns
    ):
      save_df = save_df.drop(columns=["locandina_path"])
    save_df.to_csv(NOME_FILE_CSV, index=False)


# Caricamento iniziale
if "df" not in st.session_state:
  st.session_state.df = load_data()


# --- AGGIORNAMENTI STATO ---
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
st.title("📺 Tracker Serie TV")

df = st.session_state.df

if not df.empty:
  col_m1, col_m2, col_m3, col_m4 = st.columns(4)
  col_m1.metric("Serie Totali", len(df))
  col_m2.metric(
      "In Corso", len(df[(df["viste"] > 0) & (df["viste"] < df["totali"])])
  )
  col_m3.metric("Completate", len(df[df["viste"] == df["totali"]]))
  col_m4.metric("Episodi Visti", int(df["viste"].sum()))
  st.divider()

tab_all, tab_in_prog, tab_comp, tab_fav, tab_add = st.tabs([
    "📋 Tutte le Serie",
    "🍿 In Corso",
    "✅ Completate",
    "⭐ Preferiti",
    "➕ Aggiungi Serie",
])


# FUNZIONE RENDERING FLASH CARD CON LOCANDINE
def render_cards(filtered_df):
  if filtered_df.empty:
    st.info("Nessuna serie da mostrare in questa categoria.")
    return

  for idx, row in filtered_df.iterrows():
    show_name = row["show"]
    viste = int(row["viste"])
    totali = int(row["totali"])
    stagione = int(row["stagione"])
    genere = row["genere"]
    is_fav = bool(row["preferito"])
    img_url = (
        row["locandina_path"]
        if pd.notna(row["locandina_path"])
        else PLACEHOLDER_POSTER
    )

    pct = int((viste / totali) * 100) if totali > 0 else 0

    # Determina il badge
    if viste == totali:
      badge_html = '<span class="badge-completed">COMPLETATO</span>'
    elif viste > 0:
      badge_html = '<span class="badge-in-progress">IN CORSO</span>'
    else:
      badge_html = '<span class="badge-not-started">DA INIZIARE</span>'

    fav_icon = "⭐" if is_fav else "☆"

    # Struttura Flash Card (2 colonne: Locandina a sinistra, Info & Controlli a destra)
    with st.container():
      col_img, col_content = st.columns([1, 4])

      with col_img:
        st.image(img_url, use_container_width=True)

      with col_content:
        st.markdown(
            f"### {show_name} {badge_html}", unsafe_allow_html=True
        )
        st.caption(f"Stagione {stagione} • Genere: {genere}")
        st.progress(pct / 100)

        c_info, c_plus1, c_popover, c_fav = st.columns([3, 1.5, 1.5, 1])

        with c_info:
          st.write(f"Avanzamento: **{viste}/{totali}** puntate ({pct}%)")

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

          # Pop-up di Gestione
          with st.popover("🛠️ Gestisci", use_container_width=True):
            st.markdown(f"#### ⚙️ Modifica: {show_name}")

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
              # Porta a 0 SENZA salvare sul CSV e NON CHIUDE il pop-up
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
                st.toast(f"Progresso salvato per '{show_name}'!")
                st.rerun()

            with btn_exit:
              # Annulla le modifiche e CHIUDE il pop-up senza salvare
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


# POPOLAMENTO SCHEDE TABS
with tab_all:
  render_cards(st.session_state.df)

with tab_in_prog:
  df_prog = st.session_state.df[
      (st.session_state.df["viste"] > 0)
      & (st.session_state.df["viste"] < st.session_state.df["totali"])
  ]
  render_cards(df_prog)

with tab_comp:
  df_comp = st.session_state.df[
      st.session_state.df["viste"] == st.session_state.df["totali"]
  ]
  render_cards(df_comp)

with tab_fav:
  df_fav = st.session_state.df[st.session_state.df["preferito"] == True]
  render_cards(df_fav)

with tab_add:
  st.subheader("➕ Aggiungi Nuova Serie al CSV")
  with st.form("add_show_form", clear_on_submit=True):
    new_title = st.text_input("Titolo della Serie TV:")
    new_img = st.text_input("URL Locandina/Immagine (Opzionale):")
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
        img_val = new_img.strip() if new_img.strip() != "" else PLACEHOLDER_POSTER
        new_row = {
            "show": new_title.strip(),
            "stagione": int(new_season),
            "viste": int(new_viste),
            "totali": int(new_tot),
            "genere": new_genre,
            "preferito": False,
            "locandina_path": img_val,
        }
        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame([new_row])], ignore_index=True
        )
        save_data()
        st.success(f"Serie '{new_title}' aggiunta al file CSV!")
        st.rerun()
