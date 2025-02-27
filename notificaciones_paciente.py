import sqlite3
from datetime import datetime, timedelta
from bd_medica import obtener_citas_paciente  # Asegúrate de que bd_medica.py esté en el mismo directorio

DB_NAME = "citas_medicas.db"

def conectar_bd():
    conexion = sqlite3.connect(DB_NAME)
    conexion.execute("PRAGMA foreign_keys = ON;")
    return conexion

def crear_tabla_notificaciones():
    """
    Crea la tabla Notificaciones si no existe.
    Cada notificación está asociada a un usuario (usuario_id) y, opcionalmente, a una cita (cita_id).
    Contiene un mensaje, un indicador de lectura y la fecha en que fue creada.
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Notificaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            leido INTEGER DEFAULT 0,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conexion.commit()
    conexion.close()

def actualizar_esquema():
    """
    Verifica si la columna 'cita_id' existe en la tabla Notificaciones.
    Si no existe, la agrega.
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("PRAGMA table_info(Notificaciones)")
    columns = [row[1] for row in cursor.fetchall()]
    if "cita_id" not in columns:
        cursor.execute("ALTER TABLE Notificaciones ADD COLUMN cita_id INTEGER")
        conexion.commit()
    conexion.close()

def generar_notificaciones(usuario_id):
    """
    Genera una notificación de bienvenida si el usuario aún no tiene ninguna notificación.
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM Notificaciones WHERE usuario_id = ?", (usuario_id,))
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute(
            "INSERT INTO Notificaciones (usuario_id, message, leido) VALUES (?, ?, ?)",
            (usuario_id, "Bienvenido a la aplicación de citas médicas.", 0)
        )
    conexion.commit()
    conexion.close()

def obtener_notificaciones(usuario_id):
    """
    Retorna una lista de notificaciones para el usuario.
    Cada notificación es un diccionario con las claves: id, cita_id, message, leido y fecha.
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT id, cita_id, message, leido, fecha 
        FROM Notificaciones 
        WHERE usuario_id = ? 
        ORDER BY fecha DESC
    """, (usuario_id,))
    rows = cursor.fetchall()
    conexion.close()
    notifs = []
    for row in rows:
        notifs.append({
            "id": row[0],
            "cita_id": row[1],
            "message": row[2],
            "leido": row[3],
            "fecha": row[4]
        })
    return notifs

def marcar_notificacion_leida(notif_id):
    """
    Marca la notificación identificada por notif_id como leída (leido = 1).
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("UPDATE Notificaciones SET leido = 1 WHERE id = ?", (notif_id,))
    conexion.commit()
    conexion.close()

def eliminar_notificacion(notif_id):
    """
    Elimina la notificación identificada por notif_id de la base de datos.
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM Notificaciones WHERE id = ?", (notif_id,))
    conexion.commit()
    conexion.close()

def generar_notificaciones_citas(usuario_id):
    """
    Revisa las citas agendadas del usuario y, si alguna está programada para aproximadamente 24 horas
    después del momento actual (con un margen de ±30 minutos), genera una notificación (si aún no existe)
    indicando que la cita se realizará en 24 horas.
    """
    citas = obtener_citas_paciente(usuario_id)
    now = datetime.now()
    for cita in citas:
        # La función obtener_citas_paciente devuelve:
        # (cita_id, fecha, especialidad, medico, hora, medico_id)
        cita_id, fecha_str, especialidad, medico, hora_str, medico_id = cita
        try:
            cita_dt = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M")
        except Exception:
            continue
        diff = cita_dt - now
        if timedelta(hours=23, minutes=30) <= diff <= timedelta(hours=24, minutes=30):
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("SELECT COUNT(*) FROM Notificaciones WHERE cita_id = ? AND usuario_id = ?", (cita_id, usuario_id))
            exists = cursor.fetchone()[0]
            if exists == 0:
                message = f"Tienes una cita agendada para el {fecha_str} a las {hora_str} en 24 horas."
                cursor.execute(
                    "INSERT INTO Notificaciones (usuario_id, cita_id, message, leido) VALUES (?, ?, ?, ?)",
                    (usuario_id, cita_id, message, 0)
                )
            conexion.commit()
            conexion.close()

# Al importar este módulo se asegura de que la tabla de notificaciones exista y se actualice el esquema.
crear_tabla_notificaciones()
actualizar_esquema()
