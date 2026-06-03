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
pagina = st.sidebar.radio("Navigation", ["Enter Predictions", "Leaderboard"])

banderas = {
    # Anfitriones
    "Mexico": "🇲🇽",
    "Canada": "🇨🇦",
    "USA": "🇺🇸",

    # CONMEBOL
    "Argentina": "🇦🇷",
    "Brazil": "🇧🇷",
    "Colombia": "🇨🇴",
    "Ecuador": "🇪🇨",
    "Paraguay": "🇵🇾",
    "Uruguay": "🇺🇾",

    # UEFA
    "Austria": "🇦🇹",
    "Belgium": "🇧🇪",
    "Bosnia and Herzegovina": "🇧🇦",
    "Croatia": "🇭🇷",
    "Czech Republic": "🇨🇿",
    "England": "🏴",
    "France": "🇫🇷",
    "Germany": "🇩🇪",
    "Netherlands": "🇳🇱",
    "Norway": "🇳🇴",
    "Portugal": "🇵🇹",
    "Scotland": "🏴",
    "Spain": "🇪🇸",
    "Sweden": "🇸🇪",
    "Switzerland": "🇨🇭",
    "Turkey": "🇹🇷",

    # AFC
    "Australia": "🇦🇺",
    "Iran": "🇮🇷",
    "Iraq": "🇮🇶",
    "Japan": "🇯🇵",
    "Jordan": "🇯🇴",
    "Qatar": "🇶🇦",
    "Saudi Arabia": "🇸🇦",
    "South Korea": "🇰🇷",
    "Uzbekistan": "🇺🇿",

    # CAF
    "Algeria": "🇩🇿",
    "Cape Verde": "🇨🇻",
    "DR Congo": "🇨🇩",
    "Egypt": "🇪🇬",
    "Ghana": "🇬🇭",
    "Ivory Coast": "🇨🇮",
    "Morocco": "🇲🇦",
    "Senegal": "🇸🇳",
    "South Africa": "🇿🇦",
    "Tunisia": "🇹🇳",

    # CONCACAF
    "Curacao": "🇨🇼",
    "Haiti": "🇭🇹",
    "Panama": "🇵🇦",

    # OFC
    "New Zealand": "🇳🇿"
}

# --- PAGE 1: ENTER PREDICTIONS ---
if pagina == "Enter Predictions":
    st.title("⚽ Enter or Edit Your Predictions")
    
    # DYNAMIC USER MANAGEMENT: Read from Google Sheets
    try:
        df_users = conn_sheets.read(worksheet="users", ttl=10)
        lista_usuarios = ["Select your name..."] + df_users['user_name'].dropna().tolist()
    except:
        lista_usuarios = ["Select your name...", "Admin: Create 'users' tab in Sheets"]
        
    usuario_actual = st.selectbox("Who are you?", lista_usuarios)

    if usuario_actual != "Select your name...":
        st.write("---")
        st.info("💡 You can edit your predictions up to 1 minute before kickoff.")
        
        # Load existing predictions to check for previous votes
        try:
            predicciones_existentes = conn_sheets.read(ttl=5)
            predicciones_existentes['match_id'] = predicciones_existentes['match_id'].astype(str) 
        except:
            predicciones_existentes = pd.DataFrame(columns=["usuario", "match_id", "goles_local", "goles_visita", "fecha_ingreso"])

        df_partidos = get_matches_db()
        
        for index, row in df_partidos.iterrows():
            match_id = str(row['id'])
            nombre_local = row['home']
            nombre_visita = row['away']
            
            # Buscamos la bandera en el diccionario
            bandera_local = banderas.get(nombre_local, "🏳️")
            bandera_visita = banderas.get(nombre_visita, "🏳️")
            
            # Unimos la bandera con el nombre
            equipo_local = f"{bandera_local} {nombre_local}"
            equipo_visita = f"{bandera_visita} {nombre_visita}"
            fecha_str = row['kickoff_at'][:19]
            fecha_partido = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
            fecha_str = row['kickoff_at'][:19]
            fecha_partido = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
            
            # 1. TIME LOCK (1 minute before kickoff)
            limite_modificacion = fecha_partido - timedelta(minutes=1)
            
            if datetime.now() > limite_modificacion:
                st.warning(f"🔒 {equipo_local} vs {equipo_visita} - Match locked")
                continue # Skip to next match
            
            # 2. CHECK IF USER ALREADY VOTED TO LOAD PREVIOUS NUMBERS
            goles_l_previo = 0
            goles_v_previo = 0
            texto_boton = "Save Prediction"
            
            if not predicciones_existentes.empty:
                voto_previo = predicciones_existentes[
                    (predicciones_existentes['usuario'] == usuario_actual) & 
                    (predicciones_existentes['match_id'] == match_id)
                ]
                
                if not voto_previo.empty:
                    goles_l_previo = int(voto_previo['goles_local'].values[0])
                    goles_v_previo = int(voto_previo['goles_visita'].values[0])
                    texto_boton = "Update Prediction"
                    st.success(f"✏️ You already have a prediction saved for this match, but you can change it.")

            # Display the form
            with st.form(key=f"form_{match_id}"):
                st.write(f"📅 Kickoff: **{fecha_str}**")
                col1, col2, col3 = st.columns([2, 1, 2])
                with col1:
                    st.write(f"**{equipo_local}**")
                    goles_l = st.number_input("Goals", min_value=0, step=1, value=goles_l_previo, key=f"gl_{match_id}")
                with col2:
                    st.write("VS")
                with col3:
                    st.write(f"**{equipo_visita}**")
                    goles_v = st.number_input("Goals", min_value=0, step=1, value=goles_v_previo, key=f"gv_{match_id}")
                
                submit = st.form_submit_button(texto_boton)
                
                if submit:
                    # Create new row with updated data
                    nueva_fila = pd.DataFrame([{
                        "usuario": usuario_actual,
                        "match_id": match_id,
                        "goles_local": goles_l,
                        "goles_visita": goles_v,
                        "fecha_ingreso": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }])
                    
                    # If vote existed, delete it before appending the new one
                    if not predicciones_existentes.empty:
                        df_limpio = predicciones_existentes[
                            ~((predicciones_existentes['usuario'] == usuario_actual) & 
                              (predicciones_existentes['match_id'] == match_id))
                        ]
                        df_actualizado = pd.concat([df_limpio, nueva_fila], ignore_index=True)
                    else:
                        df_actualizado = nueva_fila

                    # Upload corrected table to Google Sheets
                    conn_sheets.update(data=df_actualizado)
                    st.success("Prediction saved successfully! Reloading...")
                    st.rerun()

# --- PAGE 2: LEADERBOARD ---
elif pagina == "Leaderboard":
    st.title("📊 Official Leaderboard")
    st.write("Points are calculated automatically based on the rules and stage multipliers.")
    
    # 1. Fetch user predictions
    try:
        df_votos = conn_sheets.read(ttl=10)
    except:
        df_votos = pd.DataFrame()
        
    # 2. Fetch real official results
    try:
        df_resultados = conn_sheets.read(worksheet="resultados_reales", ttl=10)
    except:
        df_resultados = pd.DataFrame(columns=["match_id", "goles_local_real", "goles_visita_real"])

    # Verify both tables have data to calculate
    if not df_votos.empty and not df_resultados.empty and 'match_id' in df_resultados.columns:
        
        # Clean data to avoid type mismatches
        df_votos['match_id'] = df_votos['match_id'].astype(str)
        df_resultados = df_resultados.dropna(subset=['match_id'])
        df_resultados['match_id'] = df_resultados['match_id'].astype(float).astype(int).astype(str)
        
        # Merge votes with real results
        df_completo = pd.merge(df_votos, df_resultados, on="match_id", how="inner")
        
        if not df_completo.empty:
            # 3. Fetch stage_id from local DB
            conn = sqlite3.connect('worldcup2026.db')
            df_partidos = pd.read_sql_query("SELECT id as match_id, stage_id FROM matches", conn)
            conn.close()
            
            df_partidos['match_id'] = df_partidos['match_id'].astype(str)
            df_completo = pd.merge(df_completo, df_partidos, on="match_id", how="left")
            
            # 4. CUSTOM POINTS LOGIC
            def calcular_puntos(row):
                pred_l = int(row['goles_local'])
                pred_v = int(row['goles_visita'])
                real_l = int(row['goles_local_real'])
                real_v = int(row['goles_visita_real'])
                stage = int(row['stage_id'])
                
                puntos_base = 0
                diff_pred = pred_l - pred_v
                diff_real = real_l - real_v
                
                # A. Exact Match (Pleno)
                if pred_l == real_l and pred_v == real_v:
                    puntos_base = 5 
                else:
                    # B. Guessed the winner or draw?
                    acerto_ganador = (diff_pred > 0 and diff_real > 0) or \
                                     (diff_pred < 0 and diff_real < 0) or \
                                     (diff_pred == 0 and diff_real == 0)
                    if acerto_ganador:
                        puntos_base = 3
                        # C. Exact goal difference bonus
                        if diff_pred == diff_real:
                            puntos_base += 1 # 3 + 1 = 4 points total
                
                # STAGE MULTIPLIER
                multiplicador = 1
                if stage == 1:       # Group Stage
                    multiplicador = 1
                elif stage in [2, 3, 4]: # Round of 32, 16, Quarters
                    multiplicador = 2
                elif stage in [5, 6, 7]: # Semis, 3rd Place, Final
                    multiplicador = 3
                    
                return puntos_base * multiplicador
            
            # Apply formula row by row
            df_completo['Puntos Obtenidos'] = df_completo.apply(calcular_puntos, axis=1)
            
            # 5. Group by player and sum points
            ranking = df_completo.groupby("usuario").agg(
                Puntos_Totales=('Puntos Obtenidos', 'sum'),
                Partidos_Acertados=('Puntos Obtenidos', lambda x: (x > 0).sum())
            ).reset_index()
            
            # Sort highest to lowest
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
