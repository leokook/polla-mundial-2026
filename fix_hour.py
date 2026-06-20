import sqlite3

def actualizar_varias_horas():
    # 1. Conectarse a la base de datos local
    conn = sqlite3.connect('worldcup2026.db')
    cursor = conn.cursor()

    # 2. Definir la lista de cambios
    # El formato DEBE SER estrictamente: ("NUEVA_HORA", ID_DEL_PARTIDO)
    # Puedes agregar tantos renglones como necesites separados por comas
    cambios = [
        ("2026-06-19 20:30:00", 31),
        ("2026-06-19 23:00:00", 32),
       # ("2026-06-22 18:00:00", 42)
    ]

    try:
        # 3. Ejecutar la actualización masiva usando executemany
        cursor.executemany("UPDATE matches SET kickoff_at = ? WHERE id = ?", cambios)
        
        # 4. Guardar los cambios
        conn.commit()
        print(f"✅ ¡Éxito! Se actualizaron correctamente {cursor.rowcount} partidos.")
        
    except sqlite3.Error as e:
        print(f"❌ Error al actualizar la base de datos: {e}")
        
    finally:
        # 5. Cerrar la conexión
        conn.close()

if __name__ == "__main__":
    actualizar_varias_horas()