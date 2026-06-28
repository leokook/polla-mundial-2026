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
        ("2026-06-29 13:00:00", 76),
        ("2026-06-29 16:30:00", 74),
        ("2026-06-29 21:00:00", 75),
        ("2026-06-30 13:00:00", 78),
        ("2026-06-30 17:00:00", 77),
        ("2026-07-01 16:00:00", 82),
        ("2026-07-01 20:00:00", 81),
        ("2026-07-02 15:00:00", 84),
        ("2026-07-02 19:00:00", 83),
        ("2026-07-03 14:00:00", 88),
        ("2026-07-03 18:00:00", 86),
        ("2026-07-04 21:30:00", 87)
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