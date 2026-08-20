import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="TV Tracker Pro", page_icon="📺", layout="wide"
)

NOME_FILE_CSV = "TELEFILM_LIGHT.csv"
PLACEHOLDER_POSTER = "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?q=80&w=400&auto=format&fit=crop"

# --- CSS PER FLASHCARD E BADGE ---
st.markdown(
    """
<style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .badge-completed { background-color: #059669; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; display: inline-block; }
    .badge-in-progress { background-color: #0284c7; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; display: inline-block; }
    .badge-not-started { background-color: #475569; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; display: inline-block; }
</style>
""",
    unsafe_allow_html=True,
)


# --- LETTURA E SALVATAGGIO CSV ---
def load_data():
  if os.path.exists(NOME_FILE_CSV):
    try:
      df = pd.read_csv(NOME_FILE_CSV)
      if not df.empty:
        return df
    except Exception as e:
      st.error(f"Errore nella lettura del file CSV: {e}")

  # Struttura base di ripiego se il file non esiste
  return pd.DataFrame(
      columns=[
          "show",
          "stagione",
          "viste",
          "totali",
          "genere",
          "preferito",
          "locandina",
      ]
  )


def save_data():
  if "df" in st.session_state and not st.session_state.df.empty:
    st.session_state.df.to_csv(NOME_FILE_CSV, index=False)


if "df" not in st.session_state:
  st.session_state.df = load_data()

# Controllo preventivo delle colonne per evitare crash
df_state = st.session_state.df
for col in ["show", "stagione", "viste", "totali", "genere", "preferito"]:
  if col not in df_state.columns:
    if col == "preferito":
      df_state[col] = False
    elif col in ["viste", "totali", "stagione"]:
      df_state[col] = 0
    else:
      df_state[col] = "N/D"

if "locandina" not in df_state.columns:
  # Cerca se la colonna dell'immagine ha un altro nome nel CSV
  alt_cols = [
      c
      for c in df_state.columns
      if c.lower() in ["locandina_path", "immagine", "copertina", "poster"]
  ]
  df_state["locandina"] = (
      df_state[alt_cols[0]] if alt_cols else PLACEHOLDER_POSTER
  )


# --- FUNZIONI AGGIORNAMENTO ---
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


# --- INTERFACCIA ---
st.title("📺 Tracker Serie TV")

# Sidebar con tasto di Backup in locale per non perdere i dati
with st.sidebar:
  st.header("💾 Backup Manuale")
  if not st.session_state.df.empty:
    csv_bytes = st.session_state.df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Scarica CSV sul PC",
        data=csv_bytes,
        file_name="TELEFILM_LIGHT.csv",
        mime="text/csv",
        use_container_width=True,
    )

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
    st.info("Nessuna serie presente in questa categoria.")
    return

  for idx, row in filtered_df.iterrows():
    show_name = row["show"]
    viste = int(row["viste"])
    totali = int(row["totali"])
    stagione = int(row["stagione"])
    genere = row["genere"]
    is_fav = bool(row["preferito"])

    img_url = (
        row.get("locandina", PLACEHOLDER_POSTER)
        if pd.notna(row.get("locandina"))
        else PLACEHOLDER_POSTER
    )
    if not str(img_url).strip():
      img_url = PLACEHOLDER_POSTER

    pct = int((viste / totali) * 100) if totali > 0 else 0

    if viste == totali:
      badge = '<span class="badge-completed">COMPLETATO</span>'
    elif viste > 0:
      badge = '<span class="badge-in-progress">IN CORSO</span>'
    else:
      badge = '<span class="badge-not-started">DA INIZIARE</span>'

    fav_icon = "⭐" if is_fav else "☆"

    with st.container():
      col_img, col_content = st.columns([1, 4])

      with col_img:
        st.image(img_url, use_container_width=True)

      with col_content:
        st.markdown(f"### {show_name} {badge}", unsafe_allow_html=True)
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
                st.toast(f"Progresso salvato per '{show_name}'!")
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
  render_cards(
      st.session_state.df[
          (st.session_state.df["viste"] > 0)
          & (st.session_state.df["viste"] < st.session_state.df["totali"])
      ]
  )

with tab_comp:
  render_cards(
      st.session_state.df[
          st.session_state.df["viste"] == st.session_state.df["totali"]
      ]
  )

with tab_fav:
  render_cards(
      st.session_state.df[st.session_state.df["preferito"] == True]
  )

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

    submitted = st.form_submit_button("Aggiungi alla lista")
    if submitted and new_title.strip() != "":
      img_val = new_img.strip() if new_img.strip() != "" else PLACEHOLDER_POSTER
      new_row = {
          "show": new_title.strip(),
          "stagione": int(new_season),
          "viste": int(new_viste),
          "totali": int(new_tot),
          "genere": new_genre,
          "preferito": False,
          "locandina": img_val,
      }
      st.session_state.df = pd.concat(
          [st.session_state.df, pd.DataFrame([new_row])], ignore_index=True
      )
      save_data()
      st.success(f"Serie '{new_title}' aggiunta con successo!")
      st.rerun()
