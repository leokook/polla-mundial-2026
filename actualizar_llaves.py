import sqlite3

def actualizar_partido(match_id, nombre_local, nombre_visita):
    conn = sqlite3.connect('worldcup2026.db')
    cursor = conn.cursor()

    try:
        # Buscar el ID del equipo local
        cursor.execute("SELECT id FROM teams WHERE team_name = ?", (nombre_local,))
        res_local = cursor.fetchone()
        if not res_local:
            print(f"❌ Error: No se encontró el equipo '{nombre_local}'. Revisa la ortografía.")
            return
        id_local = res_local[0]

        # Buscar el ID del equipo visitante
        cursor.execute("SELECT id FROM teams WHERE team_name = ?", (nombre_visita,))
        res_visita = cursor.fetchone()
        if not res_visita:
            print(f"❌ Error: No se encontró el equipo '{nombre_visita}'. Revisa la ortografía.")
            return
        id_visita = res_visita[0]

        # Actualizar el partido con los nuevos equipos
        cursor.execute("""
            UPDATE matches 
            SET home_team_id = ?, away_team_id = ? 
            WHERE id = ?
        """, (id_local, id_visita, match_id))
        
        conn.commit()
        print(f"✅ ¡Éxito! Partido {match_id} actualizado: {nombre_local} vs {nombre_visita}")

    except sqlite3.Error as e:
        print(f"❌ Error SQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # --- AGREGA TUS PARTIDOS AQUÍ ---
    # Reemplaza el número por el ID del partido de octavos
    # y los nombres por los equipos clasificados (en inglés, exactamente como están en tu app)
    
    actualizar_partido(73, "South Africa", "Canada")
    actualizar_partido(76, "Brazil", "Japan")
    actualizar_partido(75, "Netherlands", "Morocco")
    actualizar_partido(81, "USA", "Bosnia and Herzegovina")
    #actualizar_partido(74, "Germany", "xxx")
    #actualizar_partido(79, "Mexico", "xxx")
    #actualizar_partido(85, "Switzerland", "xxx")
    #actualizar_partido(88, "Australia", "xxx")
    #actualizar_partido(78, "Côte d'Ivoire", "xxx")
  