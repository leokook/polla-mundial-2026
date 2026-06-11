import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from st_supabase_connection import SupabaseConnection

# Page configuration
st.set_page_config(page_title="World Cup 2026 Pool", page_icon="🏆", layout="centered")

# --- SUPABASE CONNECTION ---
# Conexión nativa, robusta y a prueba de alto tráfico
conn = st.connection("supabase", type=SupabaseConnection)
supabase = conn.client

# --- SQLITE LOCAL CONNECTION (To read matches) ---
def get_matches_db():
    conn_db = sqlite3.connect('worldcup2026.db')
    query = '''
        SELECT m.id, m.kickoff_at, t1.team_name as home, t2.team_name as away 
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
        ORDER BY m.kickoff_at ASC
    '''
    df = pd.read_sql_query(query, conn_db)
    conn_db.close()
    return df


# Sidebar menu
# --- INICIALIZAR MEMORIA GLOBAL ---
# Ponemos esto antes del menú para que la app siempre sepa si hay alguien logeado o no
if 'usuario_logeado' not in st.session_state:
    st.session_state['usuario_logeado'] = None

# --- SIDEBAR MENU ---
st.sidebar.title("🏆 Office Pool 2026")

# 1. Definimos la variable opciones_menu (¡Esto arregla el NameError!)
opciones_menu = ["Enter Predictions", "View Predictions", "Leaderboard", "Rules & Scoring"]

# 2. Verificamos si el usuario actual es el Administrador
if st.session_state['usuario_logeado'] == "Leonardo Guevara":
    opciones_menu.append("Admin Panel")

# 3. Dibujamos el menú usando la variable que acabamos de crear
pagina = st.sidebar.radio("Navigation", opciones_menu)

banderas_img = {
    "Mexico": "mx", "Canada": "ca", "USA": "us",
    "Argentina": "ar", "Brazil": "br", "Colombia": "co", "Ecuador": "ec", "Paraguay": "py", "Uruguay": "uy",
    "Austria": "at", "Belgium": "be", "Bosnia and Herzegovina": "ba", "Croatia": "hr", "Czech Republic": "cz",
    "England": "gb-eng", "France": "fr", "Denmark": "dk", "Germany": "de", "Netherlands": "nl", "Norway": "no",
    "Portugal": "pt", "Scotland": "gb-sct", "Spain": "es", "Sweden": "se", "Switzerland": "ch", "Turkey": "tr",
    "Australia": "au", "IR Iran": "ir", "Iraq": "iq", "Japan": "jp", "Jordan": "jo", "Qatar": "qa",
    "Saudi Arabia": "sa", "South Korea": "kr", "Uzbekistan": "uz",
    "Algeria": "dz", "Cabo Verde": "cv", "DR Congo": "cd", "Egypt": "eg", "Ghana": "gh", 
    "Côte d'Ivoire": "ci", "Morocco": "ma", "Senegal": "sn", "South Africa": "za", "Tunisia": "tn",
    "Curaçao": "cw", "Haiti": "ht", "Panama": "pa",
    "New Zealand": "nz"
}

# --- PAGE 1: ENTER PREDICTIONS ---
if pagina == "Enter Predictions":
    st.title("⚽ Enter or Edit Your Predictions")
    

    # Leer usuarios directo desde Supabase
    try:
        res_users = supabase.table('users').select('*').execute()
        df_users = pd.DataFrame(res_users.data)
        if not df_users.empty:
            df_users['pin'] = df_users['pin'].astype(str).str.strip()
            lista_usuarios = ["Select your name..."] + df_users['user_name'].tolist()
        else:
            lista_usuarios = ["Select your name..."]
    except Exception as e:
        st.error("⚠️ Connection error. Please contact the administrator.")
        st.stop()

    # PANTALLA DE LOGIN
    if st.session_state['usuario_logeado'] is None:
        usuario_actual = st.selectbox("Who are you?", lista_usuarios)

        if usuario_actual != "Select your name..." and not df_users.empty:
            pin_real = df_users.loc[df_users['user_name'] == usuario_actual, 'pin'].values[0]
            pin_ingresado = st.text_input("Enter your PIN:", type="password").strip()
            
            if pin_ingresado == pin_real:
                st.session_state['usuario_logeado'] = usuario_actual
                st.rerun() 
            elif pin_ingresado != "":
                st.error("❌ Incorrect PIN. Please try again.")
                
    # PANTALLA DE PREDICCIONES
    else:
        usuario_actual = st.session_state['usuario_logeado']
        
        col_log1, col_log2 = st.columns([3, 1])
        with col_log1:
            st.success(f"✅ Logged in as: **{usuario_actual}**")
        with col_log2:
            if st.button("Logout"):
                st.session_state['usuario_logeado'] = None
                st.rerun()

        st.write("---")
        st.info("💡 You can edit your predictions up to 1 minute before kickoff.")
        
        # Obtener SOLO los votos de este usuario para que cargue rapidísimo
        try:
            res_votos = supabase.table('predictions').select('*').eq('usuario', usuario_actual).execute()
            df_votos_usuario = pd.DataFrame(res_votos.data)
        except:
            df_votos_usuario = pd.DataFrame()

        df_partidos = get_matches_db()
        
        for index, row in df_partidos.iterrows():
            match_id = str(row['id'])
            nombre_local = row['home']
            nombre_visita = row['away']
            fecha_str = row['kickoff_at'][:19]
            fecha_partido = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
            
            limite_modificacion = fecha_partido - timedelta(minutes=1)
            
            # Forzar la hora actual a la zona horaria de Toronto/Este
            ahora_toronto = pd.Timestamp.now('America/Toronto').to_pydatetime().replace(tzinfo=None)
            
            if ahora_toronto > limite_modificacion:
                st.warning(f"🔒 {nombre_local} vs {nombre_visita} - Match locked")
                continue
            
            goles_l_previo = 0
            goles_v_previo = 0
            texto_boton = "Save Prediction"
            
            if not df_votos_usuario.empty:
                voto_previo = df_votos_usuario[df_votos_usuario['match_id'] == match_id]
                
                if not voto_previo.empty:
                    goles_l_previo = int(voto_previo['goles_local'].values[0])
                    goles_v_previo = int(voto_previo['goles_visita'].values[0])
                    texto_boton = "Update Prediction"

            cod_local = banderas_img.get(nombre_local, "un")
            cod_visita = banderas_img.get(nombre_visita, "un")
            
            html_local = f"<img src='https://flagcdn.com/24x18/{cod_local}.png' style='vertical-align: middle; margin-right: 8px;'> <b>{nombre_local}</b>"
            html_visita = f"<img src='https://flagcdn.com/24x18/{cod_visita}.png' style='vertical-align: middle; margin-right: 8px;'> <b>{nombre_visita}</b>"

            with st.form(key=f"form_{match_id}"):
                st.write(f"📅 Kickoff: **{fecha_str}**")
                col1, col2, col3 = st.columns([2, 1, 2])
                with col1:
                    st.markdown(html_local, unsafe_allow_html=True)
                    goles_l = st.number_input("Goals", min_value=0, step=1, value=goles_l_previo, key=f"gl_{match_id}")
                with col2:
                    st.write("VS")
                with col3:
                    st.markdown(html_visita, unsafe_allow_html=True)
                    goles_v = st.number_input("Goals", min_value=0, step=1, value=goles_v_previo, key=f"gv_{match_id}")
                
                submit = st.form_submit_button(texto_boton)
                
                if submit:
                    # Usamos UPSERT: Inserta si no existe, o actualiza si ya existe la llave (usuario, match_id)
                    data_insert = {
                        "usuario": usuario_actual,
                        "match_id": match_id,
                        "goles_local": goles_l,
                        "goles_visita": goles_v
                    }
                    supabase.table("predictions").upsert(data_insert, on_conflict="usuario,match_id").execute()
                    
                    st.success("Prediction saved successfully! Reloading...")
                    st.rerun()

# --- PAGE 2: LEADERBOARD ---
elif pagina == "Leaderboard":
    st.title("📊 Official Leaderboard")
    st.write("Points are calculated automatically based on the rules and stage multipliers.")
    
    try:
        res_votos = supabase.table('predictions').select('*').execute()
        df_votos = pd.DataFrame(res_votos.data)
        
        res_resultados = supabase.table('resultados_reales').select('*').execute()
        df_resultados = pd.DataFrame(res_resultados.data)
    except:
        df_votos = pd.DataFrame()
        df_resultados = pd.DataFrame()

    if not df_votos.empty and not df_resultados.empty and 'match_id' in df_resultados.columns:
        
        df_votos['match_id'] = df_votos['match_id'].astype(str)
        df_resultados = df_resultados.dropna(subset=['match_id'])
        df_resultados['match_id'] = df_resultados['match_id'].astype(str)
        
        df_completo = pd.merge(df_votos, df_resultados, on="match_id", how="inner")
        
        if not df_completo.empty:
            conn_db = sqlite3.connect('worldcup2026.db')
            df_partidos = pd.read_sql_query("SELECT id as match_id, stage_id FROM matches", conn_db)
            conn_db.close()
            
            df_partidos['match_id'] = df_partidos['match_id'].astype(str)
            df_completo = pd.merge(df_completo, df_partidos, on="match_id", how="left")
            
            def calcular_puntos(row):
                pred_l = int(row['goles_local'])
                pred_v = int(row['goles_visita'])
                real_l = int(row['goles_local_real'])
                real_v = int(row['goles_visita_real'])
                stage = int(row['stage_id'])
                
                puntos_base = 0
                diff_pred = pred_l - pred_v
                diff_real = real_l - real_v
                
                if pred_l == real_l and pred_v == real_v:
                    puntos_base = 5 
                else:
                    acerto_ganador = (diff_pred > 0 and diff_real > 0) or \
                                     (diff_pred < 0 and diff_real < 0) or \
                                     (diff_pred == 0 and diff_real == 0)
                    if acerto_ganador:
                        puntos_base = 3
                        if diff_pred == diff_real:
                            puntos_base += 1 
                
                multiplicador = 1
                if stage == 1:       
                    multiplicador = 1
                elif stage in [2, 3, 4]: 
                    multiplicador = 2
                elif stage in [5, 6, 7]: 
                    multiplicador = 3
                    
                return puntos_base * multiplicador
            
            df_completo['Puntos Obtenidos'] = df_completo.apply(calcular_puntos, axis=1)
            
            ranking = df_completo.groupby("usuario").agg(
                Puntos_Totales=('Puntos Obtenidos', 'sum'),
                Partidos_Acertados=('Puntos Obtenidos', lambda x: (x > 0).sum())
            ).reset_index()
            
            ranking = ranking.sort_values(by=["Puntos_Totales", "Partidos_Acertados"], ascending=[False, False])
            ranking = ranking.rename(columns={
                "usuario": "Player", 
                "Puntos_Totales": "🏆 Total Points",
                "Partidos_Acertados": "✅ Scoring Matches"
            })
            
            st.dataframe(ranking, use_container_width=True, hide_index=True)
            st.success("Leaderboard is up to date!")
            
        else:
            st.info("No predicted matches have been played yet.")
    else:
        st.info("The Administrator hasn't loaded any official results yet. The leaderboard is empty!")

# --- PAGE: VIEW PREDICTIONS ---
elif pagina == "View Predictions":
    st.title("👀 View Others' Predictions")
    st.write("Curious about what your colleagues predicted? Select a match below.")
    st.info("🔒 **Anti-Cheat System:** To prevent copying, you can only view predictions for matches that are already locked (kickoff is less than 1 minute away).")

    df_partidos = get_matches_db()
    
    # Calcular la hora actual en Toronto para ser justos con los bloqueos
    ahora_toronto = pd.Timestamp.now('America/Toronto').to_pydatetime().replace(tzinfo=None)
    
    # Filtrar solo los partidos que ya pasaron su límite de modificación
    df_partidos['kickoff_dt'] = pd.to_datetime(df_partidos['kickoff_at'].str[:19])
    df_partidos['limite'] = df_partidos['kickoff_dt'] - timedelta(minutes=1)
    
    df_bloqueados = df_partidos[df_partidos['limite'] < ahora_toronto].copy()
    
    if df_bloqueados.empty:
        st.warning("No matches have been locked yet. Check back just before the first kickoff!")
    else:
        # Crear un diccionario para el menú desplegable (Ej: "Mexico vs Canada - 2026-06-11")
        opciones_partidos = df_bloqueados.apply(lambda x: f"{x['home']} vs {x['away']} ({x['kickoff_at'][:10]})", axis=1).tolist()
        ids_partidos = df_bloqueados['id'].astype(str).tolist()
        diccionario_partidos = dict(zip(opciones_partidos, ids_partidos))
        
        partido_seleccionado = st.selectbox("Select a locked match:", opciones_partidos)
        match_id_seleccionado = diccionario_partidos[partido_seleccionado]
        
        # Descargar de Supabase solo los votos de ese partido
        try:
            res_votos = supabase.table('predictions').select('*').eq('match_id', match_id_seleccionado).execute()
            df_votos_partido = pd.DataFrame(res_votos.data)
        except:
            df_votos_partido = pd.DataFrame()
            
        if not df_votos_partido.empty:
            # Obtener nombres de los equipos para las columnas
            equipo_local = df_bloqueados[df_bloqueados['id'].astype(str) == match_id_seleccionado]['home'].values[0]
            equipo_visita = df_bloqueados[df_bloqueados['id'].astype(str) == match_id_seleccionado]['away'].values[0]
            
            # Limpiar y renombrar la tabla para que se vea profesional
            df_votos_partido = df_votos_partido[['usuario', 'goles_local', 'goles_visita']]
            df_votos_partido = df_votos_partido.rename(columns={
                'usuario': 'Player',
                'goles_local': f'{equipo_local} Goals',
                'goles_visita': f'{equipo_visita} Goals'
            })
            
            # Ordenar alfabéticamente por jugador
            df_votos_partido = df_votos_partido.sort_values(by='Player')
            
            st.dataframe(df_votos_partido, use_container_width=True, hide_index=True)
            st.success(f"Showing {len(df_votos_partido)} predictions for this match.")
        else:
            st.info("Nobody submitted a prediction for this match. 😱")

# --- PAGE 3: RULES & SCORING ---
elif pagina == "Rules & Scoring":
    st.title("📖 Rules & Scoring System")
    
    st.markdown("""
    Welcome to the Office Pool! Here is everything you need to know to play and win.

    ### ⏱️ General Rules
    * **Lock Time:** You can enter or modify your predictions up to **1 minute before** the scheduled kickoff time. Once the match starts, predictions are sealed.
    * **90 Minutes Only:** For knockout stages, the score that counts is the one at the end of regular time (90 minutes + injury time). Extra time and penalty shootouts **do not count** towards your prediction.

    ---

    ### 🎯 Base Points
    Points are awarded based on how accurate your prediction is compared to the real official result.

    * 🥇 **Exact Match (Pleno) = 5 Points** You nailed the exact score of the match.
    * 🥈 **Winner + Exact Goal Difference = 4 Points** You guessed the correct winner and the exact margin of victory, but not the exact score.
    * 🥉 **Correct Winner or Draw = 3 Points** You correctly guessed who would win (or if it would be a tie), but missed the goal difference.
    * ❌ **Wrong Prediction = 0 Points** You guessed the wrong winner.

    ---

    ### 📈 Stage Multipliers
    As the tournament progresses, the stakes get higher! Your base points are multiplied depending on the tournament stage:

    * **Group Stage:** Base Points **x 1**
    * **Round of 32, Round of 16 & Quarter-Finals:** Base Points **x 2**
    * **Semi-Finals, 3rd Place Match & Final:** Base Points **x 3**

    ---

    ### 📝 Scoring Examples
    Let's say the real match between **Mexico and Canada** ends **2 - 1** (Mexico wins by 1 goal).
    Here is how different predictions would be scored during the Group Stage (Multiplier x1):
    """)

    st.markdown("""
    | Your Prediction | Base Points | Reason |
    | :--- | :---: | :--- |
    | **2 - 1** | **5** | 🥇 **Exact match!** Perfect score. |
    | **3 - 2** | **4** | 🥈 Correct winner (Mexico) + exact goal difference (+1). |
    | **1 - 0** | **4** | 🥈 Correct winner (Mexico) + exact goal difference (+1). |
    | **3 - 0** | **3** | 🥉 Correct winner (Mexico), but wrong goal difference (+3). |
    | **1 - 1** | **0** | ❌ Wrong result (you predicted a tie). |
    | **0 - 1** | **0** | ❌ Wrong winner (you predicted Canada). |
    """)
    
    st.info("💡 **Pro Tip:** In the final match (x3 multiplier), a perfect 'Exact Match' prediction is worth a massive **15 points** (5 base points x 3). Nobody is out of the game until the very end!")

# --- PAGE: ADMIN PANEL (EXCLUSIVE) ---
elif pagina == "Admin Panel":
    st.title("⚙️ Administrator Control Panel")
    st.write("Welcome, boss! Here you can load official match results to update the leaderboard.")
    
    # 1. Traer los partidos de la base de datos local
    df_partidos = get_matches_db()
    
    # Crear un formato cómodo para el menú desplegable (Ej: "1 - Mexico vs South Africa")
    opciones_partidos = df_partidos.apply(lambda x: f"{x['id']} - {x['home']} vs {x['away']}", axis=1).tolist()
    partido_seleccionado = st.selectbox("Select the match that just finished:", opciones_partidos)
    
    # Extraer el ID real del partido seleccionado
    match_id_real = partido_seleccionado.split(" - ")[0]
    
    # 2. Verificar si este partido ya tenía un resultado guardado antes en Supabase
    try:
        res_existente = supabase.table('resultados_reales').select('*').eq('match_id', match_id_real).execute()
        df_existente = pd.DataFrame(res_existente.data)
    except:
        df_existente = pd.DataFrame()
        
    goles_l_previo = 0
    goles_v_previo = 0
    texto_boton_admin = "Save Official Result"
    
    if not df_existente.empty:
        goles_l_previo = int(df_existente['goles_local_real'].values[0])
        goles_v_previo = int(df_existente['goles_visita_real'].values[0])
        texto_boton_admin = "Update Official Result"
        st.warning(f"⚠️ This match already has a saved result ({goles_l_previo} - {goles_v_previo}). Saving again will overwrite it.")

    # 3. Formulario para ingresar el marcador real
    # Obtenemos los nombres de los equipos para que el formulario sea muy visual
    partido_info = df_partidos[df_partidos['id'].astype(str) == match_id_real].iloc[0]
    
    with st.form(key="form_admin_resultados"):
        st.subheader("⚽ Enter Final Score (90 Mins)")
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.markdown(f"**{partido_info['home']}**")
            goles_local_real = st.number_input("Goals", min_value=0, step=1, value=goles_l_previo, key="admin_gl")
        with col2:
            st.write("VS")
        with col3:
            st.markdown(f"**{partido_info['away']}**")
            goles_visita_real = st.number_input("Goals", min_value=0, step=1, value=goles_v_previo, key="admin_gv")
            
        submit_admin = st.form_submit_button(texto_boton_admin)
        
        if submit_admin:
            # Estructura de datos para Supabase
            data_resultado = {
                "match_id": str(match_id_real),
                "goles_local_real": int(goles_local_real),
                "goles_visita_real": int(goles_visita_real)
            }
            
            # Guardar en Supabase usando UPSERT (crea o actualiza por llave primaria 'match_id')
            try:
                supabase.table("resultados_reales").upsert(data_resultado).execute()
                st.success(f"🏆 Result for {partido_info['home']} {goles_local_real} - {goles_visita_real} {partido_info['away']} saved successfully!")
                st.balloons() # ¡Efecto de globos para celebrar!
            except Exception as e:
                st.error(f"❌ Error saving to database: {e}")
