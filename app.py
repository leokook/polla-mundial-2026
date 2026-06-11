import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Page configuration
st.set_page_config(page_title="World Cup 2026 Pool", page_icon="🏆", layout="centered")

# --- GOOGLE SHEETS CONNECTION ---
conn_sheets = st.connection("gsheets", type=GSheetsConnection)

# --- SQLITE LOCAL CONNECTION (To read matches) ---
def get_matches_db():
    conn = sqlite3.connect('worldcup2026.db')
    query = '''
        SELECT m.id, m.kickoff_at, t1.team_name as home, t2.team_name as away 
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
        ORDER BY m.kickoff_at ASC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Sidebar menu
st.sidebar.title("🏆 Office Pool 2026")
pagina = st.sidebar.radio("Navigation", ["Enter Predictions", "Leaderboard", "Rules & Scoring"])

banderas_img = {
    # Anfitriones
    "Mexico": "mx", "Canada": "ca", "USA": "us",
    # CONMEBOL
    "Argentina": "ar", "Brazil": "br", "Colombia": "co", "Ecuador": "ec", "Paraguay": "py", "Uruguay": "uy",
    # UEFA
    "Austria": "at", "Belgium": "be", "Bosnia and Herzegovina": "ba", "Croatia": "hr", "Czech Republic": "cz",
    "England": "gb-eng", "France": "fr", "Denmark": "dk", "Germany": "de", "Netherlands": "nl", "Norway": "no",
    "Portugal": "pt", "Scotland": "gb-sct", "Spain": "es", "Sweden": "se", "Switzerland": "ch", "Turkey": "tr",
    # AFC
    "Australia": "au", "IR Iran": "ir", "Iraq": "iq", "Japan": "jp", "Jordan": "jo", "Qatar": "qa",
    "Saudi Arabia": "sa", "South Korea": "kr", "Uzbekistan": "uz",
    # CAF
    "Algeria": "dz", "Cabo Verde": "cv", "DR Congo": "cd", "Egypt": "eg", "Ghana": "gh", 
    "Côte d'Ivoire": "ci", "Morocco": "ma", "Senegal": "sn", "South Africa": "za", "Tunisia": "tn",
    # CONCACAF
    "Curaçao": "cw", "Haiti": "ht", "Panama": "pa",
    # OFC
    "New Zealand": "nz"
}

# --- PAGE 1: ENTER PREDICTIONS ---
if pagina == "Enter Predictions":
    st.title("⚽ Enter or Edit Your Predictions")
    
    # 1. INICIALIZAR LA MEMORIA DEL NAVEGADOR (Evita los deslogueos)
    if 'usuario_logeado' not in st.session_state:
        st.session_state['usuario_logeado'] = None

    # 2. CARGAR USUARIOS CON TTL ALTO (10 Minutos) PARA NO SATURAR A GOOGLE
    try:
        df_users = conn_sheets.read(worksheet="users", ttl=600)
        df_users['pin'] = df_users['pin'].astype(str).str.replace('.0', '', regex=False).str.strip()
        lista_usuarios = ["Select your name..."] + df_users['user_name'].dropna().tolist()
    except Exception as e:
        st.error("⚠️ Connection to database is busy. Please refresh the page in a few seconds.")
        lista_usuarios = ["Select your name..."]
        df_users = pd.DataFrame()

    # 3. PANTALLA DE INICIO DE SESIÓN
    if st.session_state['usuario_logeado'] is None:
        usuario_actual = st.selectbox("Who are you?", lista_usuarios)

        if usuario_actual != "Select your name..." and not df_users.empty:
            pin_real = df_users.loc[df_users['user_name'] == usuario_actual, 'pin'].values[0]
            pin_ingresado = st.text_input("Enter your PIN:", type="password").strip()
            
            if pin_ingresado == pin_real:
                # Guardamos al usuario en la sesión de forma permanente
                st.session_state['usuario_logeado'] = usuario_actual
                st.rerun() 
            elif pin_ingresado != "":
                st.error("❌ Incorrect PIN. Please try again.")
                
    # 4. PANTALLA DE PREDICCIONES (Una vez que ya inició sesión)
    else:
        usuario_actual = st.session_state['usuario_logeado']
        
        # Mostrar quién está logeado y dar botón de salida
        col_log1, col_log2 = st.columns([3, 1])
        with col_log1:
            st.success(f"✅ Logged in as: **{usuario_actual}**")
        with col_log2:
            if st.button("Logout"):
                st.session_state['usuario_logeado'] = None
                st.rerun()

        st.write("---")
        st.info("💡 You can edit your predictions up to 1 minute before kickoff.")
        
        # Aumentamos el TTL a 60 segundos para evitar bloqueos
        try:
            predicciones_existentes = conn_sheets.read(ttl=60)
            predicciones_existentes['match_id'] = predicciones_existentes['match_id'].astype(str).str.replace('.0', '', regex=False).str.strip()
            predicciones_existentes['usuario'] = predicciones_existentes['usuario'].astype(str).str.strip()
        except:
            predicciones_existentes = pd.DataFrame(columns=["usuario", "match_id", "goles_local", "goles_visita", "fecha_ingreso"])

        # AQUÍ ESTÁ LA LÍNEA QUE TE FALTABA PARA EVITAR EL ERROR
        df_partidos = get_matches_db()
        
        for index, row in df_partidos.iterrows():
            match_id = str(row['id'])
            nombre_local = row['home']
            nombre_visita = row['away']
            fecha_str = row['kickoff_at'][:19]
            fecha_partido = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
            
            limite_modificacion = fecha_partido - timedelta(minutes=1)
            
            if datetime.now() > limite_modificacion:
                st.warning(f"🔒 {nombre_local} vs {nombre_visita} - Match locked")
                continue 
            
            goles_l_previo = 0
            goles_v_previo = 0
            texto_boton = "Save Prediction"
            
            if not predicciones_existentes.empty:
                voto_previo = predicciones_existentes[
                    (predicciones_existentes['usuario'] == usuario_actual) & 
                    (predicciones_existentes['match_id'] == match_id)
                ]
                
                if not voto_previo.empty:
                    goles_l_previo = int(float(voto_previo['goles_local'].values[0]))
                    goles_v_previo = int(float(voto_previo['goles_visita'].values[0]))
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
                    nueva_fila = pd.DataFrame([{
                        "usuario": usuario_actual,
                        "match_id": match_id,
                        "goles_local": goles_l,
                        "goles_visita": goles_v,
                        "fecha_ingreso": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }])
                    
                    if not predicciones_existentes.empty:
                        df_limpio = predicciones_existentes[
                            ~((predicciones_existentes['usuario'] == usuario_actual) & 
                              (predicciones_existentes['match_id'] == match_id))
                        ]
                        df_actualizado = pd.concat([df_limpio, nueva_fila], ignore_index=True)
                    else:
                        df_actualizado = nueva_fila

                    conn_sheets.update(data=df_actualizado)
                    st.success("Prediction saved successfully! Reloading...")
                    st.rerun()

# --- PAGE 2: LEADERBOARD ---
elif pagina == "Leaderboard":
    st.title("📊 Official Leaderboard")
    st.write("Points are calculated automatically based on the rules and stage multipliers.")
    
    try:
        # TTL subido a 60 para proteger de caídas
        df_votos = conn_sheets.read(ttl=60)
    except:
        df_votos = pd.DataFrame()
        
    try:
        df_resultados = conn_sheets.read(worksheet="resultados_reales", ttl=60)
    except:
        df_resultados = pd.DataFrame(columns=["match_id", "goles_local_real", "goles_visita_real"])

    if not df_votos.empty and not df_resultados.empty and 'match_id' in df_resultados.columns:
        
        df_votos['match_id'] = df_votos['match_id'].astype(str)
        df_resultados = df_resultados.dropna(subset=['match_id'])
        df_resultados['match_id'] = df_resultados['match_id'].astype(float).astype(int).astype(str)
        
        df_completo = pd.merge(df_votos, df_resultados, on="match_id", how="inner")
        
        if not df_completo.empty:
            conn = sqlite3.connect('worldcup2026.db')
            df_partidos = pd.read_sql_query("SELECT id as match_id, stage_id FROM matches", conn)
            conn.close()
            
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
