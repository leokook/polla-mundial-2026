import streamlit as st
import sqlite3
from datetime import datetime, timedelta
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
    st.title("⚽ Ingresa o Modifica tus Pronósticos")
    
    usuarios = ["Selecciona tu nombre...", "Ana", "Carlos", "Diana", "Juan"]
    usuario_actual = st.selectbox("¿Quién eres?", usuarios)

    if usuario_actual != "Selecciona tu nombre...":
        st.write("---")
        st.info("💡 Puedes modificar tus resultados hasta 1 minuto antes del inicio del partido.")
        
        # Cargar predicciones existentes desde Google Sheets
        try:
            predicciones_existentes = conn_sheets.read(ttl=5)
            # Aseguramos que el match_id se lea como texto para evitar errores de comparación
            predicciones_existentes['match_id'] = predicciones_existentes['match_id'].astype(str) 
        except:
            predicciones_existentes = pd.DataFrame(columns=["usuario", "match_id", "goles_local", "goles_visita", "fecha_ingreso"])

        df_partidos = get_matches_db()
        
        for index, row in df_partidos.iterrows():
            match_id = str(row['id'])
            equipo_local = row['local']
            equipo_visita = row['visita']
            fecha_str = row['kickoff_at'][:19]
            fecha_partido = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
            
            # 1. EL NUEVO CANDADO DE TIEMPO (1 minuto antes)
            limite_modificacion = fecha_partido - timedelta(minutes=1)
            
            if datetime.now() > limite_modificacion:
                st.warning(f"🔒 {equipo_local} vs {equipo_visita} - Partido bloqueado")
                continue # Salta al siguiente partido, este ya no se puede editar
            
            # 2. BUSCAR SI YA HABÍA VOTADO PARA MOSTRAR SUS NÚMEROS
            goles_l_previo = 0
            goles_v_previo = 0
            texto_boton = "Guardar Pronóstico"
            
            if not predicciones_existentes.empty:
                voto_previo = predicciones_existentes[
                    (predicciones_existentes['usuario'] == usuario_actual) & 
                    (predicciones_existentes['match_id'] == match_id)
                ]
                
                if not voto_previo.empty:
                    goles_l_previo = int(voto_previo['goles_local'].values[0])
                    goles_v_previo = int(voto_previo['goles_visita'].values[0])
                    texto_boton = "Actualizar Pronóstico"
                    st.success(f"✏️ Ya tienes un pronóstico guardado para este partido, pero puedes cambiarlo.")

            # Mostrar el formulario
            with st.form(key=f"form_{match_id}"):
                st.write(f"📅 Inicio: **{fecha_str}**")
                col1, col2, col3 = st.columns([2, 1, 2])
                with col1:
                    st.write(f"**{equipo_local}**")
                    goles_l = st.number_input("Goles", min_value=0, step=1, value=goles_l_previo, key=f"gl_{match_id}")
                with col2:
                    st.write("VS")
                with col3:
                    st.write(f"**{equipo_visita}**")
                    goles_v = st.number_input("Goles", min_value=0, step=1, value=goles_v_previo, key=f"gv_{match_id}")
                
                submit = st.form_submit_button(texto_boton)
                
                if submit:
                    # Crear nueva fila con los datos actualizados
                    nueva_fila = pd.DataFrame([{
                        "usuario": usuario_actual,
                        "match_id": match_id,
                        "goles_local": goles_l,
                        "goles_visita": goles_v,
                        "fecha_ingreso": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }])
                    
                    # Si ya existía un voto, lo borramos de la tabla antes de meter el nuevo
                    if not predicciones_existentes.empty:
                        df_limpio = predicciones_existentes[
                            ~((predicciones_existentes['usuario'] == usuario_actual) & 
                              (predicciones_existentes['match_id'] == match_id))
                        ]
                        df_actualizado = pd.concat([df_limpio, nueva_fila], ignore_index=True)
                    else:
                        df_actualizado = nueva_fila

                    # Subir la tabla corregida a Google Sheets
                    conn_sheets.update(data=df_actualizado)
                    st.success("¡Pronóstico guardado exitosamente! Recargando...")
                    st.rerun()

# --- PÁGINA 2: DASHBOARD ---
# --- PÁGINA 2: DASHBOARD (TABLA DE POSICIONES) ---
elif pagina == "Tabla de Posiciones":
    st.title("📊 Leaderboard Oficial")
    st.write("Los puntos se calculan automáticamente aplicando las reglas y multiplicadores por fase.")
    
    # 1. Traer predicciones de los usuarios (lee la primera pestaña por defecto)
    try:
        df_votos = conn_sheets.read(ttl=10)
    except:
        df_votos = pd.DataFrame()
        
    # 2. Traer resultados reales oficiales (lee la pestaña que acabas de crear)
    try:
        df_resultados = conn_sheets.read(worksheet="resultados_reales", ttl=10)
    except:
        df_resultados = pd.DataFrame(columns=["match_id", "goles_local_real", "goles_visita_real"])

    # Verificamos que existan datos en ambas tablas para empezar a calcular
    if not df_votos.empty and not df_resultados.empty and 'match_id' in df_resultados.columns:
        
        # Limpiar datos para evitar errores si Google Sheets los lee como texto
        df_votos['match_id'] = df_votos['match_id'].astype(str)
        df_resultados = df_resultados.dropna(subset=['match_id']) # Quitar filas vacías
        df_resultados['match_id'] = df_resultados['match_id'].astype(float).astype(int).astype(str)
        
        # Unir lo que votó la gente con los resultados reales
        df_completo = pd.merge(df_votos, df_resultados, on="match_id", how="inner")
        
        if not df_completo.empty:
            # 3. Traer los stage_id de la base de datos local para saber qué fase es
            conn = sqlite3.connect('worldcup2026.db')
            df_partidos = pd.read_sql_query("SELECT id as match_id, stage_id FROM matches", conn)
            conn.close()
            
            df_partidos['match_id'] = df_partidos['match_id'].astype(str)
            df_completo = pd.merge(df_completo, df_partidos, on="match_id", how="left")
            
            # 4. LÓGICA DE PUNTOS PERSONALIZADA
            def calcular_puntos(row):
                pred_l = int(row['goles_local'])
                pred_v = int(row['goles_visita'])
                real_l = int(row['goles_local_real'])
                real_v = int(row['goles_visita_real'])
                stage = int(row['stage_id'])
                
                puntos_base = 0
                diff_pred = pred_l - pred_v
                diff_real = real_l - real_v
                
                # A. Marcador Exacto (Pleno)
                if pred_l == real_l and pred_v == real_v:
                    puntos_base = 5 
                else:
                    # B. ¿Acertó al ganador o al empate?
                    acerto_ganador = (diff_pred > 0 and diff_real > 0) or \
                                     (diff_pred < 0 and diff_real < 0) or \
                                     (diff_pred == 0 and diff_real == 0)
                    if acerto_ganador:
                        puntos_base = 3
                        # C. Bonus por diferencia de goles exacta
                        if diff_pred == diff_real:
                            puntos_base += 1 # 3 + 1 = 4 puntos totales
                
                # APLICAR MULTIPLICADOR POR FASE
                multiplicador = 1
                if stage == 1:       # Fase de Grupos
                    multiplicador = 1
                elif stage in [2, 3, 4]: # 16vos, Octavos y Cuartos
                    multiplicador = 2
                elif stage in [5, 6, 7]: # Semifinales, 3er Puesto y Final
                    multiplicador = 3
                    
                return puntos_base * multiplicador
            
            # Aplicar la fórmula fila por fila
            df_completo['Puntos Obtenidos'] = df_completo.apply(calcular_puntos, axis=1)
            
            # 5. Agrupar por compañero y sumar sus puntos
            ranking = df_completo.groupby("usuario").agg(
                Puntos_Totales=('Puntos Obtenidos', 'sum'),
                Partidos_Acertados=('Puntos Obtenidos', lambda x: (x > 0).sum())
            ).reset_index()
            
            # Ordenar de mayor a menor y dar formato a la tabla
            ranking = ranking.sort_values(by=["Puntos_Totales", "Partidos_Acertados"], ascending=[False, False])
            ranking = ranking.rename(columns={
                "usuario": "Compañero", 
                "Puntos_Totales": "🏆 Puntos Totales",
                "Partidos_Acertados": "✅ Partidos con Puntos"
            })
            
            st.dataframe(ranking, use_container_width=True, hide_index=True)
            st.success("¡Tabla actualizada al día de hoy!")
            
        else:
            st.info("Aún no se han jugado los partidos que la gente ha pronosticado.")
    else:
        st.info("El Administrador aún no ha cargado resultados oficiales. ¡La tabla de posiciones está en cero!")
