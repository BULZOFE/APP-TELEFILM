import os
from urllib.parse import quote
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="TV Tracker Pro", page_icon="📺", layout="wide")

# Nomi file supportati nella cartella di lavoro
POSSIBILI_FILE = [
    "TELEFILM2024_LIGHT.csv",
    "TELEFILM_LIGHT.csv",
    "telefilm_light.csv",
    "TELEFILM.csv",
    "telefilm.csv",
]
PLACEHOLDER_POSTER = "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?q=80&w=400&auto=format&fit=crop"

st.markdown(
    """
<style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .badge-completed { background-color: #059669; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; display: inline-block; }
    .badge-in-progress { background-color: #0284c7; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; display: inline-block; }
    .badge-not-started { background-color: #475569; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; display: inline-block; }
    .badge-voto { padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; display: inline-block; margin-left: 5px; }

    [data-testid="stImage"] img {
        border-radius: 8px;
        max-height: 220px;
        object-fit: cover;
        
</style>
""",
    unsafe_allow_html=True,
)


def get_voto_badge_html(voto):
    """Restituisce il tag HTML del badge per il voto in base al valore (0-100) con colori differenti."""
    try:
        voto_val = float(voto)
    except (ValueError, TypeError):
        voto_val = 50.0

    if voto_val >= 80:
        style = "background-color: #15803d; color: #ffffff;"
    elif voto_val >= 60:
        style = "background-color: #22c55e; color: #ffffff;"
    elif voto_val >= 40:
        style = "background-color: #eab308; color: #000000;"
    else:
        style = "background-color: #ef4444; color: #ffffff;"

    return f'<span class="badge-voto" style="{style}">VOTO: {int(voto_val) if voto_val.is_integer() else round(voto_val, 1)}</span>'


# --- FUNZIONE API TMDB (Ottimizzata con w342) ---
@st.cache_data(ttl=86400, show_spinner=False)
def fetch_tmdb_poster(title, api_key):
    """Recupera l'URL della locandina da TMDB per una serie TV in formato ridotto w342."""
    if not api_key or not title:
        return None
    try:
        url = f"https://api.themoviedb.org/3/search/tv?api_key={api_key.strip()}&query={quote(title)}&language=it-IT"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results and results[0].get("poster_path"):
                # Modificato da w500 a w342 per ottimizzare peso e velocità
                return f"https://image.tmdb.org/t/p/w342{results[0]['poster_path']}"
    except Exception:
        pass
    return None


def trova_percorso_csv():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for nome in POSSIBILI_FILE:
        path_assoluto = os.path.join(base_dir, nome)
        if os.path.exists(path_assoluto):
            return path_assoluto
        if os.path.exists(nome):
            return nome
    return None


def load_data():
    file_path = trova_percorso_csv()
    if not file_path:
        return pd.DataFrame()

    try:
        try:
            df_raw = pd.read_csv(
                file_path, sep=";", encoding="utf-8-sig", low_memory=False
            )
        except Exception:
            df_raw = pd.read_csv(
                file_path, sep=None, engine="python", encoding="utf-8-sig"
            )

        df_raw.columns = df_raw.columns.astype(str).str.strip()
        cols_upper = [c.upper() for c in df_raw.columns]

        if "TELEFILM" in cols_upper:
            col_map = {c: c.upper() for c in df_raw.columns}
            df_raw = df_raw.rename(columns=col_map)

            df_valid = df_raw[
                df_raw["TELEFILM"].notna()
                & (df_raw["TELEFILM"].astype(str).str.strip() != "")
            ].copy()

            series_list = []
            for show_name, group in df_valid.groupby("TELEFILM", sort=False):
                show_str = str(show_name).strip()
                totali = len(group)

                viste = 0
                if "STATO" in group.columns:
                    viste = len(
                        group[group["STATO"].astype(str).str.upper() == "V"]
                    )
                elif "PUNT VISTE" in group.columns:
                    val_max = pd.to_numeric(
                        group["PUNT VISTE"], errors="coerce"
                    ).max()
                    viste = int(val_max) if pd.notna(val_max) else 0

                stagione = 1
                if "S" in group.columns:
                    seasons = pd.to_numeric(group["S"], errors="coerce").dropna()
                    if not seasons.empty:
                        stagione = int(seasons.max())

                genere = "N/D"
                if "GENERE" in group.columns:
                    genres = group["GENERE"].dropna().unique()
                    if (
                        len(genres) > 0
                        and str(genres[0]).strip() not in ["", "nan"]
                    ):
                        genere = str(genres[0]).strip()

                voto = 50.0
                if "VALORE" in group.columns:
                    vals = pd.to_numeric(
                        group["VALORE"], errors="coerce"
                    ).dropna()
                    if not vals.empty:
                        val_num = float(vals.iloc[0])
                        if 0 <= val_num <= 100:
                            voto = val_num

                series_list.append({
                    "show": show_str,
                    "stagione": stagione,
                    "viste": viste,
                    "totali": totali,
                    "genere": genere,
                    "voto": voto,
                    "preferito": False,
                    "locandina": PLACEHOLDER_POSTER,
                })

            return pd.DataFrame(series_list)

        else:
            df_raw.columns = df_raw.columns.str.lower()
            return df_raw

    except Exception as e:
        st.error(f"Errore nella lettura del file: {e}")
        return pd.DataFrame()


def save_data():
    path_salvataggio = trova_percorso_csv() or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "TELEFILM2024_LIGHT.csv"
    )
    if "df" in st.session_state and not st.session_state.df.empty:
        st.session_state.df.to_csv(path_salvataggio, index=False)


# Inizializzazione Session State
if "df" not in st.session_state or st.session_state.df.empty:
    st.session_state.df = load_data()

if "voti_generi" not in st.session_state:
    st.session_state.voti_generi = {}

# Normalizzazione colonne
if not st.session_state.df.empty:
    req_cols = [
        "show",
        "stagione",
        "viste",
        "totali",
        "genere",
        "voto",
        "preferito",
    ]
    for col in req_cols:
        if col not in st.session_state.df.columns:
            if col == "preferito":
                st.session_state.df[col] = False
            elif col == "voto":
                st.session_state.df[col] = 50.0
            elif col in ["viste", "totali", "stagione"]:
                st.session_state.df[col] = 0
            else:
                st.session_state.df[col] = "N/D"

    if "locandina" not in st.session_state.df.columns:
        st.session_state.df["locandina"] = PLACEHOLDER_POSTER

    # Inizializza i voti predefiniti per i generi esistenti
    generi_presenti = (
        set(st.session_state.df["genere"].dropna().unique()) - {"", "N/D"}
    )
    for g in generi_presenti:
        if g not in st.session_state.voti_generi:
            st.session_state.voti_generi[g] = 50.0


def recalculate_all_votes():
    """Ricalcola in modo dinamico i voti di tutte le serie in base ai voti dei generi."""
    for idx, row in st.session_state.df.iterrows():
        gen = row.get("genere", "N/D")
        if gen in st.session_state.voti_generi:
            st.session_state.df.at[idx, "voto"] = float(
                st.session_state.voti_generi[gen]
            )
    save_data()


# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 Configurazione TMDB")
    tmdb_key = st.text_input(
        "Inserisci la tua API Key TMDB:",
        value="20df15041e975b04e0372df2462999a4",
        type="password",
        help="Ottieni la tua chiave gratuita su themoviedb.org",
    )
    st.session_state["tmdb_key"] = tmdb_key

    if st.button("🖼️ Aggiorna Locandine Mancanti", use_container_width=True):
        if not tmdb_key.strip():
            st.error("⚠️ Inserisci prima la tua API Key TMDB nel campo sopra!")
        else:
            updated_count = 0
            progress_bar = st.progress(0)
            total_items = len(st.session_state.df)

            for idx, row in st.session_state.df.iterrows():
                curr_loc = str(row.get("locandina", ""))

                if "image.tmdb.org" not in curr_loc:
                    poster_url = fetch_tmdb_poster(row["show"], tmdb_key)
                    if poster_url:
                        st.session_state.df.at[idx, "locandina"] = poster_url
                        updated_count += 1

                if total_items > 0:
                    progress_bar.progress((idx + 1) / total_items)

            progress_bar.empty()
            if updated_count > 0:
                save_data()
                st.success(f"Trovate e salvate {updated_count} nuove locandine!")
                st.rerun()
            else:
                st.info(
                    "Nessuna nuova locandina trovata o sono già tutte aggiornate."
                )

    st.markdown("---")
    st.header("🎭 Gestione Voti Generi")
    st.caption(
        "Modificando il voto di un genere, verranno ricalcolati i voti di tutte le serie appartenenti ad esso."
    )

    generi_list = sorted([
        g
        for g in st.session_state.df["genere"].dropna().unique()
        if str(g).strip() not in ["", "N/D"]
    ])
    for gen in generi_list:
        if gen not in st.session_state.voti_generi:
            st.session_state.voti_generi[gen] = 50.0

        current_gen_voto = int(st.session_state.voti_generi[gen])
        options_gen = list(range(0, 101, 5))
        if current_gen_voto not in options_gen:
            options_gen = sorted(list(set(options_gen + [current_gen_voto])))

        new_val = st.selectbox(
            f"Voto Genere: {gen}",
            options=options_gen,
            index=options_gen.index(current_gen_voto),
            key=f"sel_voto_gen_{gen}",
        )

        if new_val != current_gen_voto:
            st.session_state.voti_generi[gen] = float(new_val)
            recalculate_all_votes()
            st.toast(
                f"Voto per genere '{gen}' aggiornato a {new_val}. Voti serie ricalcolati!",
                icon="🔄",
            )
            st.rerun()

    st.markdown("---")
    st.header("⚙️ Gestione Dati")
    if st.button("🔄 Ricarica Dati da CSV", use_container_width=True):
        if "df" in st.session_state:
            del st.session_state["df"]
        st.rerun()

    st.markdown("---")
    st.header("💾 Backup")
    if not st.session_state.df.empty:
        csv_bytes = st.session_state.df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Scarica CSV Sintesi",
            data=csv_bytes,
            file_name="TELEFILM_SUMMARY.csv",
            mime="text/csv",
            use_container_width=True,
        )


# --- FUNZIONI AGGIORNAMENTO ---
def set_show_watched_count(show_name, count):
    st.session_state.df.loc[
        st.session_state.df["show"] == show_name, "viste"
    ] = int(count)
    save_data()


def set_show_voto(show_name, voto_val):
    st.session_state.df.loc[
        st.session_state.df["show"] == show_name, "voto"
    ] = float(voto_val)
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


def update_single_poster(show_name):
    key = st.session_state.get("tmdb_key", "")
    if not key:
        st.toast("Inserisci l'API Key TMDB nella barra laterale!", icon="⚠️")
        return
    poster_url = fetch_tmdb_poster(show_name, key)
    if poster_url:
        st.session_state.df.loc[
            st.session_state.df["show"] == show_name, "locandina"
        ] = poster_url
        save_data()
        st.toast(f"Locandina per '{show_name}' aggiornata!", icon="🖼️")
    else:
        st.toast(f"Nessuna locandina trovata per '{show_name}'.", icon="❌")


def delete_show(show_name):
    st.session_state.df = st.session_state.df[
        st.session_state.df["show"] != show_name
    ].reset_index(drop=True)
    save_data()


# --- INTERFACCIA PRINCIPALE ---
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

col_search, col_filter_genre = st.columns([3, 1])
with col_search:
    search_query = st.text_input("🔍 Cerca serie per titolo...", "").strip().lower()

with col_filter_genre:
    generi_disponibili = ["Tutti"]
    if not df.empty and "genere" in df.columns:
        generi_disponibili += sorted([
            g
            for g in df["genere"].dropna().unique().tolist()
            if str(g).strip() not in ["", "N/D"]
        ])
    selected_genre = st.selectbox("🎭 Filtra per Genere", generi_disponibili)

tab_all, tab_in_prog, tab_comp, tab_fav, tab_add = st.tabs([
    "📋 Tutte le Serie",
    "🍿 In Corso",
    "✅ Completate",
    "⭐ Preferiti",
    "➕ Aggiungi Serie",
])


def render_cards(filtered_df, prefix="all"):
    if search_query:
        filtered_df = filtered_df[
            filtered_df["show"]
            .astype(str)
            .str.lower()
            .str.contains(search_query)
        ]

    if selected_genre != "Tutti":
        filtered_df = filtered_df[filtered_df["genere"] == selected_genre]

    if filtered_df.empty:
        st.info("Nessuna serie trovata.")
        return

    max_cards = 100
    total_count = len(filtered_df)

    if total_count > max_cards:
        st.caption(f"Mostrando le prime {max_cards} serie su {total_count}.")

    for idx, row in filtered_df.head(max_cards).iterrows():
        show_name = row["show"]
        viste = int(row["viste"])
        totali = int(row["totali"])
        stagione = int(row["stagione"])
        genere = row["genere"]
        is_fav = bool(row["preferito"])
        voto = row.get("voto", 50.0)

        img_url = (
            row.get("locandina", PLACEHOLDER_POSTER)
            if pd.notna(row.get("locandina"))
            else PLACEHOLDER_POSTER
        )

        pct = int((viste / totali) * 100) if totali > 0 else 0

        if viste == totali and totali > 0:
            badge = '<span class="badge-completed">COMPLETATO</span>'
        elif viste > 0:
            badge = '<span class="badge-in-progress">IN CORSO</span>'
        else:
            badge = '<span class="badge-not-started">DA INIZIARE</span>'

        voto_badge = get_voto_badge_html(voto)
        fav_icon = "⭐" if is_fav else "☆"

        with st.container():
            col_img, col_content = st.columns([1, 4])

            with col_img:
                st.image(img_url, use_container_width=True)

            with col_content:
                st.markdown(
                    f"### {show_name} {badge} {voto_badge}",
                    unsafe_allow_html=True,
                )
                st.caption(f"Stagione {stagione} • Genere: {genere}")
                st.progress(pct / 100)

                c_info, c_plus1, c_popover, c_fav = st.columns([3, 1.5, 1.5, 1])

                with c_info:
                    st.write(
                        f"Avanzamento: **{viste}/{totali}** puntate ({pct}%)"
                    )

                with c_plus1:
                    if viste < totali:
                        if st.button(
                            "➕ +1 Ep",
                            key=f"btn_plus_{prefix}_{idx}",
                            use_container_width=True,
                        ):
                            increment_show_count(show_name)
                            st.rerun()
                    else:
                        st.button(
                            "✅ Finito",
                            key=f"btn_done_{prefix}_{idx}",
                            disabled=True,
                            use_container_width=True,
                        )

                with c_popover:
                    count_key = f"input_viste_{prefix}_{idx}"
                    voto_key = f"input_voto_{prefix}_{idx}"
                    with st.popover("🛠️ Gestisci", use_container_width=True):
                        st.markdown(f"#### ⚙️ Modifica: {show_name}")
                        if count_key not in st.session_state:
                            st.session_state[count_key] = viste

                        st.number_input(
                            "Puntate viste esatte:",
                            min_value=0,
                            max_value=max(totali, 1),
                            step=1,
                            key=count_key,
                        )

                        # Menu a tendina per il voto della serie
                        voto_curr = int(voto)
                        voto_options = list(range(0, 101, 5))
                        if voto_curr not in voto_options:
                            voto_options = sorted(
                                list(set(voto_options + [voto_curr]))
                            )

                        st.selectbox(
                            "Voto Serie (Menu a tendina):",
                            options=voto_options,
                            index=voto_options.index(voto_curr)
                            if voto_curr in voto_options
                            else 10,
                            key=voto_key,
                        )

                        if st.button(
                            "🖼️ Scarica Locandina TMDB",
                            key=f"tmdb_btn_{prefix}_{idx}",
                            use_container_width=True,
                        ):
                            update_single_poster(show_name)
                            st.rerun()

                        st.markdown("---")
                        btn_reset, btn_save, btn_exit = st.columns(3)

                        with btn_reset:
                            if st.button(
                                "🔄 Reset",
                                key=f"reset_{prefix}_{idx}",
                                use_container_width=True,
                            ):
                                st.session_state[count_key] = 0

                        with btn_save:
                            if st.button(
                                "💾 Salva",
                                key=f"save_{prefix}_{idx}",
                                type="primary",
                                use_container_width=True,
                            ):
                                set_show_watched_count(
                                    show_name, st.session_state[count_key]
                                )
                                set_show_voto(
                                    show_name, st.session_state[voto_key]
                                )
                                st.toast(
                                    f"Modifiche salvate per '{show_name}'!"
                                )
                                st.rerun()

                        with btn_exit:
                            if st.button(
                                "❌ Esci",
                                key=f"exit_{prefix}_{idx}",
                                use_container_width=True,
                            ):
                                st.session_state[count_key] = viste
                                st.rerun()

                        st.markdown("---")
                        if st.button(
                            "🗑️ Elimina Serie",
                            key=f"del_{prefix}_{idx}",
                            use_container_width=True,
                        ):
                            delete_show(show_name)
                            st.toast(f"Serie '{show_name}' eliminata.")
                            st.rerun()

                with c_fav:
                    if st.button(
                        fav_icon,
                        key=f"btn_fav_{prefix}_{idx}",
                        use_container_width=True,
                    ):
                        toggle_favorite(show_name)
                        st.rerun()

            st.markdown("---")


# --- CONTENUTO TAB ---
with tab_all:
    render_cards(st.session_state.df, prefix="all")

with tab_in_prog:
    render_cards(
        st.session_state.df[
            (st.session_state.df["viste"] > 0)
            & (st.session_state.df["viste"] < st.session_state.df["totali"])
        ],
        prefix="prog",
    )

with tab_comp:
    render_cards(
        st.session_state.df[
            st.session_state.df["viste"] == st.session_state.df["totali"]
        ],
        prefix="comp",
    )

with tab_fav:
    render_cards(
        st.session_state.df[st.session_state.df["preferito"] == True],
        prefix="fav",
    )

with tab_add:
    st.subheader("➕ Aggiungi una nuova Serie TV")
    with st.form("form_add_show", clear_on_submit=True):
        c_add1, c_add2 = st.columns(2)
        with c_add1:
            new_title = st.text_input("Titolo Serie *")
            new_season = st.number_input(
                "Stagione", min_value=1, value=1, step=1
            )
            new_genre = st.text_input(
                "Genere (es. DRAMA, COMEDY, ACTION)", value="DRAMA"
            )
        with c_add2:
            new_tot = st.number_input(
                "Puntate Totali", min_value=1, value=10, step=1
            )
            new_viste = st.number_input(
                "Puntate Viste", min_value=0, value=0, step=1
            )
            new_fav = st.checkbox("Aggiungi ai Preferiti", value=False)

        st.markdown("---")
        st.markdown("##### 🎯 Voto Iniziale Serie / Genere")
        voto_options_add = list(range(0, 101, 5))
        new_voto_select = st.selectbox(
            "Seleziona Voto per questa Serie (o Voto per il nuovo Genere):",
            options=voto_options_add,
            index=10,  # Default 50
            help="Se il genere specificato è nuovo, questo voto verrà assegnato anche al genere.",
        )

        submit_btn = st.form_submit_button("➕ Salva Serie", type="primary")

        if submit_btn:
            if not new_title.strip():
                st.error("⚠️ Il titolo della serie è obbligatorio!")
            else:
                poster_url = PLACEHOLDER_POSTER
                tmdb_key = st.session_state.get("tmdb_key", "")
                if tmdb_key:
                    fetched = fetch_tmdb_poster(new_title.strip(), tmdb_key)
                    if fetched:
                        poster_url = fetched

                formatted_genre = (
                    new_genre.strip().upper() if new_genre.strip() else "N/D"
                )

                if (
                    formatted_genre != "N/D"
                    and formatted_genre not in st.session_state.voti_generi
                ):
                    st.session_state.voti_generi[formatted_genre] = float(
                        new_voto_select
                    )
                    st.toast(
                        f"Nuovo genere '{formatted_genre}' registrato con voto {new_voto_select}!",
                        icon="🎭",
                    )

                new_row = pd.DataFrame([{
                    "show": new_title.strip(),
                    "stagione": int(new_season),
                    "viste": int(min(new_viste, new_tot)),
                    "totali": int(new_tot),
                    "genere": formatted_genre,
                    "voto": float(new_voto_select),
                    "preferito": bool(new_fav),
                    "locandina": poster_url,
                }])

                st.session_state.df = pd.concat(
                    [st.session_state.df, new_row], ignore_index=True
                )
                save_data()
                st.success(
                    f"Serie '{new_title.strip()}' aggiunta con successo!"
                )
                st.rerun()
