import sqlite3

def actualizar_hora_partido():
    # 1. Conectarse a la base de datos local
    conn = sqlite3.connect('worldcup2026.db')
    cursor = conn.cursor()

    # 2. Definir los cambios (ID del partido y la nueva fecha/hora en formato YYYY-MM-DD HH:MM:SS)
    # Aquí pongo el ejemplo del partido 31 que mencionaste antes
    partido_id = 31
    nueva_hora = "2026-06-19 20:30:00"

    try:
        # 3. Ejecutar la actualización
        cursor.execute("UPDATE matches SET kickoff_at = ? WHERE id = ?", (nueva_hora, partido_id))
        
        # 4. Guardar los cambios
        conn.commit()
        print(f"✅ ¡Éxito! La hora del partido {partido_id} se ha actualizado a {nueva_hora}.")
        
    except sqlite3.Error as e:
        print(f"❌ Error al actualizar la base de datos: {e}")
        
    finally:
        # 5. Cerrar la conexión
        conn.close()

if __name__ == "__main__":
    actualizar_hora_partido()