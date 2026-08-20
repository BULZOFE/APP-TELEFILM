import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="TV Tracker Pro", page_icon="📺", layout="wide"
)

PLACEHOLDER_POSTER = "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?q=80&w=400&auto=format&fit=crop"

# --- CONNESSIONE GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)


def load_data():
  try:
    # Read con ttl=0 per ottenere sempre i dati più aggiornati in tempo reale
    df = conn.read(ttl=0)
    return df
  except Exception as e:
    st.error(f"Errore nella connessione a Google Sheets: {e}")
    return pd.DataFrame()


def save_data():
  if "df" in st.session_state:
    save_df = st.session_state.df.copy()
    if "locandina_path" in save_df.columns:
      save_df = save_df.drop(columns=["locandina_path"])
    conn.update(data=save_df)


# Caricamento iniziale
if "df" not in st.session_state:
  st.session_state.df = load_data()

# Controllo e ripristino sicuro colonne
req_cols = ["show", "stagione", "viste", "totali", "genere", "preferito"]
for col in req_cols:
  if col not in st.session_state.df.columns:
    if col == "preferito":
      st.session_state.df[col] = False
    elif col in ["viste", "totali", "stagione"]:
      st.session_state.df[col] = 0
    else:
      st.session_state.df[col] = "N/D"

if "locandina_path" not in st.session_state.df.columns:
  img_cols = [
      c
      for c in st.session_state.df.columns
      if c.lower() in ["locandina", "immagine", "copertina", "poster", "image"]
  ]
  if img_cols:
    st.session_state.df["locandina_path"] = st.session_state.df[
        img_cols[0]
    ].fillna(PLACEHOLDER_POSTER)
  else:
    st.session_state.df["locandina_path"] = PLACEHOLDER_POSTER


# --- AGGIORNAMENTI ---
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
st.title("📺 Tracker Serie TV (Google Sheets)")

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

    img_url = row.get("locandina_path", PLACEHOLDER_POSTER)
    if pd.isna(img_url) or not str(img_url).strip():
      img_url = PLACEHOLDER_POSTER

    pct = int((viste / totali) * 100) if totali > 0 else 0
    fav_icon = "⭐" if is_fav else "☆"

    with st.container():
      col_img, col_content = st.columns([1, 4])

      with col_img:
        st.image(img_url, use_container_width=True)

      with col_content:
        st.markdown(f"### {show_name}")
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
              if st.button(
                  "🔄 Reset", key=f"reset_{idx}", use_container_width=True
              ):
                st.session_state[count_key] = 0

            with btn_save:
              if st.button(
                  "💾 Salva",
                  key=f"save_{idx}",
                  type="primary",
                  use_container_width=True,
              ):
                set_show_watched_count(show_name, st.session_state[count_key])
                st.toast(f"Progresso salvato su Google Sheets per '{show_name}'!")
                st.rerun()

            with btn_exit:
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
  st.subheader("➕ Aggiungi Nuova Serie a Google Sheets")
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

    submitted = st.form_submit_button("Aggiungi e Scrivi su Google Sheets")
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
        st.success(f"Serie '{new_title}' salvata su Google Sheets!")
        st.rerun()
