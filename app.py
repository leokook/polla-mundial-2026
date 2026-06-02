import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuración de página
st.set_page_config(page_title="Polla Mundial 2026", page_icon="🏆", layout="centered")

# --- CONEXIÓN A GOOGLE SHEETS (Para guardar) ---
conn_sheets = st.connection("gsheets", type=GSheetsConnection)

# --- CONEXIÓN A SQLITE LOCAL (Para leer partidos) ---
def get_matches_db():
    conn = sqlite3.connect('worldcup2026.db')
    query = '''
        SELECT m.id, m.kickoff_at, t1.team_name as local, t2.team_name as visita 
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
        ORDER BY m.kickoff_at ASC
        LIMIT 15
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Menú lateral
st.sidebar.title("🏆 Polla Oficina 2026")
pagina = st.sidebar.radio("Navegación", ["Ingresar Predicciones", "Tabla de Posiciones"])

# --- PÁGINA 1: INGRESO DE DATOS ---
if pagina == "Ingresar Predicciones":
    st.title("⚽ Ingresa tus Pronósticos")
    
    usuarios = ["Selecciona tu nombre...", "Ana", "Carlos", "Diana", "Juan"]
    usuario_actual = st.selectbox("¿Quién eres?", usuarios)

    if usuario_actual != "Selecciona tu nombre...":
        st.write("---")
        
        # Cargar predicciones existentes desde Google Sheets para verificar duplicados
        try:
            predicciones_existentes = conn_sheets.read(ttl=5) # ttl=5 obliga a refrescar cada 5 segs
        except:
            predicciones_existentes = pd.DataFrame(columns=["usuario", "match_id", "goles_local", "goles_visita", "fecha_ingreso"])

        df_partidos = get_matches_db()
        
        for index, row in df_partidos.iterrows():
            match_id = int(row['id'])
            equipo_local = row['local']
            equipo_visita = row['visita']
            fecha_str = row['kickoff_at'][:19]
            fecha_partido = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
            
            # 1. CANDADO DE TIEMPO (Si el partido ya empezó)
            if datetime.now() > fecha_partido:
                st.warning(f"🔒 {equipo_local} vs {equipo_visita} - Partido cerrado")
                continue
            
            # 2. CANDADO DE MODIFICACIÓN (Si el usuario ya votó en este partido)
            ya_voto = False
            if not predicciones_existentes.empty:
                # Convertimos a string o int seguro para comparar
                match_id_str = str(match_id)
                votos_usuario = predicciones_existentes[predicciones_existentes['usuario'] == usuario_actual]
                if match_id in votos_usuario['match_id'].astype(int).values:
                    ya_voto = True
            
            if ya_voto:
                st.success(f"✅ {equipo_local} vs {equipo_visita} - ¡Tu pronóstico ya fue registrado!")
            else:
                # Si no ha votado y está a tiempo, se muestra el formulario
                with st.form(key=f"form_{match_id}"):
                    st.write(f"📅 Hora del partido: **{fecha_str}**")
                    col1, col2, col3 = st.columns([2, 1, 2])
                    with col1:
                        st.write(f"**{equipo_local}**")
                        goles_l = st.number_input("Goles", min_value=0, step=1, key=f"gl_{match_id}")
                    with col2:
                        st.write("VS")
                    with col3:
                        st.write(f"**{equipo_visita}**")
                        goles_v = st.number_input("Goles", min_value=0, step=1, key=f"gv_{match_id}")
                    
                    submit = st.form_submit_button("Guardar Pronóstico")
                    
                    if submit:
                        # Crear nueva fila de datos
                        nueva_fila = pd.DataFrame([{
                            "usuario": usuario_actual,
                            "match_id": match_id,
                            "goles_local": goles_l,
                            "goles_visita": goles_v,
                            "fecha_ingreso": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }])
                        
                        # Concatenar y subir a Google Sheets
                        df_actualizado = pd.concat([predicciones_existentes, nueva_fila], ignore_index=True)
                        conn_sheets.update(data=df_actualizado)
                        st.success("¡Guardado en la nube! Recargando...")
                        st.rerun()

# --- PÁGINA 2: DASHBOARD ---
elif pagina == "Tabla de Posiciones":
    st.title("📊 Leaderboard en Tiempo Real")
    
    try:
        df_votos = conn_sheets.read(ttl=10)
    except:
        df_votos = pd.DataFrame()
        
    if not df_votos.empty:
        # Contar cuántos partidos lleva cada uno
        ranking = df_votos.groupby("usuario").size().reset_index(name="Partidos Pronosticados")
        ranking = ranking.rename(columns={"usuario": "Compañero"})
        st.dataframe(ranking, use_container_width=True, hide_index=True)
    else:
        st.info("Nadie ha participado aún. ¡Vayan a la pestaña de predicciones!")