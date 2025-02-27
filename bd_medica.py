import sqlite3
import hashlib
from datetime import datetime, timedelta

DB_NAME = "citas_medicas.db"

def conectar_bd():
    """
    Conecta a la base de datos SQLite y activa la verificación de claves foráneas.
    Devuelve la conexión.
    """
    conexion = sqlite3.connect(DB_NAME)
    conexion.execute("PRAGMA foreign_keys = ON;")
    return conexion

def crear_base_de_datos():
    """Crea la base de datos con todas sus tablas necesarias e inserta las 5 especialidades fijas."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    # Tabla Usuarios (actualizada para incluir seguridad y fotografía)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_usuario TEXT CHECK(tipo_usuario IN ('Paciente', 'Administrador')) NOT NULL,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            telefono TEXT CHECK(LENGTH(telefono) = 10) NOT NULL,
            cedula TEXT UNIQUE CHECK(LENGTH(cedula) = 10) NOT NULL,
            password TEXT NOT NULL,
            security_q1 TEXT,
            security_a1 TEXT,
            security_q2 TEXT,
            security_a2 TEXT,
            security_q3 TEXT,
            security_a3 TEXT,
            photo TEXT
        );
    """)
    # Tabla Especialidades
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Especialidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        );
    """)
    # Tabla Medicos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Medicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            especialidad_id INTEGER NOT NULL,
            telefono TEXT CHECK(LENGTH(telefono) = 10),
            email TEXT UNIQUE NOT NULL,
            usuario_id INTEGER,
            FOREIGN KEY (especialidad_id) REFERENCES Especialidades(id) ON DELETE CASCADE
        );
    """)
    # Tabla Horarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medico_id INTEGER NOT NULL,
            fecha DATE NOT NULL,
            hora TIME NOT NULL,
            estado TEXT CHECK(estado IN ('Disponible', 'Reservado')) DEFAULT 'Disponible',
            FOREIGN KEY (medico_id) REFERENCES Medicos(id) ON DELETE CASCADE,
            UNIQUE (medico_id, fecha, hora)
        );
    """)
    # Tabla Citas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            medico_id INTEGER NOT NULL,
            fecha DATE NOT NULL,
            hora TIME NOT NULL,
            estado TEXT CHECK(estado IN ('Pendiente', 'Presente', 'Ausente', 'Cancelada')) DEFAULT 'Pendiente',
            FOREIGN KEY (paciente_id) REFERENCES Usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (medico_id) REFERENCES Medicos(id) ON DELETE CASCADE,
            UNIQUE (paciente_id, fecha, hora)
        );
    """)
    # Insertar las 5 especialidades fijas si no existen
    especialidades_fijas = [
        "Medicina General",
        "Medicina Familiar",
        "Odontología",
        "Obstetricia",
        "Ginecología"
    ]
    for esp in especialidades_fijas:
        cursor.execute("INSERT OR IGNORE INTO Especialidades (nombre) VALUES (?)", (esp,))
    conexion.commit()
    conexion.close()
    print("✅ Base de datos creada e inicializada exitosamente.")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_credenciales(email, password):
    """Verifica si el usuario existe y la contraseña es correcta."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, tipo_usuario, password FROM Usuarios WHERE email = ?", (email,))
    usuario = cursor.fetchone()
    conexion.close()
    if usuario:
        user_id, tipo_usuario, hashed_pass = usuario
        if hashed_pass == hash_password(password):
            return True, tipo_usuario, user_id
    return False, None, None

def registrar_usuario_en_bd(tipo_usuario, nombres, apellidos, email, telefono, cedula, password, especialidad=None,
                            security_q1=None, security_a1=None, security_q2=None, security_a2=None, security_q3=None, security_a3=None,
                            photo=None):
    """
    Inserta un nuevo usuario en la tabla Usuarios, incluyendo las preguntas de seguridad y la fotografía.
    Si el usuario es Administrador, también se registra en la tabla Medicos con la especialidad dada.
    Retorna (exito: bool, mensaje: str, user_id: int|None).
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            INSERT INTO Usuarios (tipo_usuario, nombres, apellidos, email, telefono, cedula, password,
                                  security_q1, security_a1, security_q2, security_a2, security_q3, security_a3, photo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tipo_usuario, nombres, apellidos, email, telefono, cedula, hash_password(password),
              security_q1, security_a1, security_q2, security_a2, security_q3, security_a3, photo))
        user_id = cursor.lastrowid
        if tipo_usuario == "Administrador" and especialidad and especialidad != "Seleccionar":
            cursor.execute("SELECT id FROM Especialidades WHERE nombre = ?", (especialidad,))
            esp_id = cursor.fetchone()
            if esp_id is not None:
                esp_id = esp_id[0]
            else:
                return False, "❌ La especialidad seleccionada no existe.", None
            cursor.execute("""
                INSERT INTO Medicos (nombres, apellidos, especialidad_id, telefono, email, usuario_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nombres, apellidos, esp_id, telefono, email, user_id))
        conexion.commit()
        return True, "✅ Usuario registrado correctamente.", user_id
    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if "Usuarios.email" in error_msg:
            return False, "❌ El correo ya está registrado.", None
        elif "Usuarios.cedula" in error_msg:
            return False, "❌ La cédula ya está registrada.", None
        elif "Medicos.email" in error_msg:
            return False, "❌ Ya existe un médico con este correo.", None
        else:
            return False, f"❌ Error de integridad: {error_msg}", None
    finally:
        conexion.close()

def obtener_usuario(user_id):
    """Retorna (nombres, apellidos, email, telefono, cedula, tipo_usuario, photo) del usuario."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT nombres, apellidos, email, telefono, cedula, tipo_usuario, photo
        FROM Usuarios
        WHERE id = ?
    """, (user_id,))
    usuario = cursor.fetchone()
    conexion.close()
    return usuario

def actualizar_datos_usuario(user_id, nombres, apellidos, email, telefono):
    """Actualiza en la tabla Usuarios los datos básicos."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            UPDATE Usuarios 
            SET nombres = ?, apellidos = ?, email = ?, telefono = ?
            WHERE id = ?
        """, (nombres, apellidos, email, telefono, user_id))
        conexion.commit()
        return True, "Datos actualizados correctamente."
    except sqlite3.IntegrityError as e:
        msg = str(e)
        if "Usuarios.email" in msg:
            return False, "Ese correo ya está registrado por otro usuario."
        return False, f"Error al actualizar datos: {msg}"
    finally:
        conexion.close()

def cambiar_contrasena(user_id, old_password, new_password):
    """Verifica la contraseña actual y actualiza con la nueva (ya validada en la lógica de la interfaz)."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT password FROM Usuarios WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conexion.close()
        return False, "Usuario no encontrado."
    current_hashed = row[0]
    if current_hashed != hash_password(old_password):
        conexion.close()
        return False, "La contraseña actual no es correcta."
    try:
        cursor.execute("UPDATE Usuarios SET password = ? WHERE id = ?", (hash_password(new_password), user_id))
        conexion.commit()
        return True, "Contraseña actualizada correctamente."
    except sqlite3.Error as e:
        return False, f"Error al cambiar la contraseña: {e}"
    finally:
        conexion.close()

def obtener_especialidades():
    """Obtiene la lista de especialidades existentes."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM Especialidades")
    especialidades = cursor.fetchall()
    conexion.close()
    return especialidades

def obtener_medicos(especialidad_id=None, usuario_id=None):
    """
    Obtiene los médicos.
    Si se pasa un `especialidad_id`, filtra por esa especialidad.
    Si se pasa un `usuario_id`, retorna solo el médico cuyo usuario_id coincide (para panel de administrador).
    Si ninguno se pasa, retorna todos los médicos.
    Retorna [(id, "nombres apellidos"), ...].
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    if usuario_id is not None:
        cursor.execute("""
            SELECT id, (nombres || ' ' || apellidos) as nombre_completo
            FROM Medicos
            WHERE usuario_id = ?
        """, (usuario_id,))
    elif especialidad_id is not None:
        cursor.execute("""
            SELECT id, (nombres || ' ' || apellidos) as nombre_completo
            FROM Medicos
            WHERE especialidad_id = ?
        """, (especialidad_id,))
    else:
        cursor.execute("""
            SELECT id, (nombres || ' ' || apellidos) as nombre_completo
            FROM Medicos
        """)
    medicos = cursor.fetchall()
    conexion.close()
    return medicos

def obtener_pacientes_de_medico(medico_id):
    """
    Retorna la lista de pacientes (Usuarios) que han tenido (o tienen)
    al menos una cita con el médico dado.
    Formato: [(paciente_id, "Nombres Apellidos"), ...].
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT DISTINCT U.id, (U.nombres || ' ' || U.apellidos) AS nombre_completo
        FROM Citas C
        JOIN Usuarios U ON C.paciente_id = U.id
        WHERE C.medico_id = ?
        ORDER BY U.apellidos, U.nombres
    """, (medico_id,))
    data = cursor.fetchall()
    conexion.close()
    return data

def obtener_horarios_disponibles(medico_id, fecha):
    """Obtiene los horarios disponibles para el médico en la fecha indicada."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT id, hora FROM Horarios 
        WHERE medico_id = ? AND fecha = ? AND estado = 'Disponible'
    """, (medico_id, fecha))
    horarios = cursor.fetchall()
    conexion.close()
    return horarios

def registrar_cita(paciente_id, medico_id, fecha, hora):
    """
    Registra la cita del paciente y actualiza el estado del horario a 'Reservado'.
    Devuelve una tupla (resultado, mensaje).
    """
    try:
        cita_dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
    except Exception:
        return False, "Formato de fecha u hora inválido."
    if cita_dt < datetime.now():
        return False, "No se puede agendar una cita en el pasado."
    conexion = conectar_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            INSERT INTO Citas (paciente_id, medico_id, fecha, hora, estado)
            VALUES (?, ?, ?, ?, 'Pendiente')
        """, (paciente_id, medico_id, fecha, hora))
        cursor.execute("""
            UPDATE Horarios SET estado = 'Reservado'
            WHERE medico_id = ? AND fecha = ? AND hora = ?
        """, (medico_id, fecha, hora))
        conexion.commit()
        return True, "✅ Cita agendada con éxito."
    except sqlite3.Error as e:
        return False, f"❌ Error al registrar la cita: {e}"
    finally:
        conexion.close()

def obtener_citas_paciente(user_id):
    """
    Retorna una lista de citas para el paciente con id user_id.
    Cada cita es una tupla: (cita_id, fecha, especialidad, medico, hora, medico_id)
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT Citas.id, Citas.fecha, Especialidades.nombre, 
               Medicos.nombres || ' ' || Medicos.apellidos AS medico, 
               Citas.hora,
               Medicos.id as medico_id
        FROM Citas
        JOIN Medicos ON Citas.medico_id = Medicos.id
        JOIN Especialidades ON Medicos.especialidad_id = Especialidades.id
        WHERE Citas.paciente_id = ?
    """, (user_id,))
    citas = cursor.fetchall()
    conexion.close()
    return citas

def cancelar_cita(paciente_id, medico_id, fecha, hora):
    """
    Cancela la cita del paciente y libera el horario (cambia a 'Disponible').
    Devuelve (resultado, mensaje).
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT estado FROM Citas WHERE paciente_id = ? AND medico_id = ? AND fecha = ? AND hora = ?", 
                       (paciente_id, medico_id, fecha, hora))
        estado = cursor.fetchone()
        if estado and estado[0] in ('Presente', 'Ausente'):
            return False, "No se puede cancelar una cita ya atendida."
        cursor.execute("""
            DELETE FROM Citas
            WHERE paciente_id = ? AND medico_id = ? AND fecha = ? AND hora = ?
        """, (paciente_id, medico_id, fecha, hora))
        cursor.execute("""
            UPDATE Horarios SET estado = 'Disponible'
            WHERE medico_id = ? AND fecha = ? AND hora = ?
        """, (medico_id, fecha, hora))
        conexion.commit()
        return True, "✅ Cita cancelada exitosamente."
    except sqlite3.Error as e:
        return False, f"❌ Error al cancelar la cita: {e}"
    finally:
        conexion.close()

def cancelar_cita_por_id(cita_id):
    """
    Cancela una cita según su ID (tabla Citas.id).
    Actualiza el estado a 'Cancelada' y libera el horario (estado = 'Disponible').
    Devuelve (resultado, mensaje).
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT paciente_id, medico_id, fecha, hora FROM Citas WHERE id = ?", (cita_id,))
        row = cursor.fetchone()
        if not row:
            conexion.close()
            return False, "❌ Cita no encontrada."
        paciente_id, medico_id, fecha, hora = row
        cursor.execute("UPDATE Citas SET estado = 'Cancelada' WHERE id = ?", (cita_id,))
        cursor.execute("""
            UPDATE Horarios 
            SET estado = 'Disponible'
            WHERE medico_id = ? AND fecha = ? AND hora = ?
        """, (medico_id, fecha, hora))
        conexion.commit()
        return True, "✅ Cita cancelada exitosamente."
    except sqlite3.Error as e:
        return False, f"❌ Error al cancelar la cita: {e}"
    finally:
        conexion.close()

def generar_horarios_disponibles(medico_id, fecha):
    """
    Genera horarios disponibles (cada 30 minutos) para el médico en la fecha indicada,
    únicamente si aún no existen registros para esa fecha.
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM Horarios WHERE medico_id = ? AND fecha = ?", (medico_id, fecha))
    if cursor.fetchone()[0] > 0:
        conexion.close()
        return
    hora_actual = datetime.strptime("08:00", "%H:%M")
    hora_fin = datetime.strptime("17:00", "%H:%M")
    while hora_actual <= hora_fin:
        cursor.execute("""
            INSERT INTO Horarios (medico_id, fecha, hora, estado)
            VALUES (?, ?, ?, 'Disponible')
        """, (medico_id, fecha, hora_actual.strftime("%H:%M")))
        hora_actual += timedelta(minutes=30)
    conexion.commit()
    conexion.close()

def obtener_todas_citas(fecha=None, medico_id=None):
    """
    Retorna todas las citas. Filtra opcionalmente por fecha y/o médico.
    Devuelve una lista de tuplas: (cita_id, fecha, hora, paciente, medico, estado).
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    query = """
        SELECT C.id, C.fecha, C.hora,
               (U.nombres || ' ' || U.apellidos) AS paciente,
               (M.nombres || ' ' || M.apellidos) AS medico,
               C.estado
        FROM Citas C
        JOIN Usuarios U ON C.paciente_id = U.id
        JOIN Medicos M ON C.medico_id = M.id
        WHERE 1=1
    """
    params = []
    if fecha:
        query += " AND C.fecha = ?"
        params.append(fecha)
    if medico_id:
        query += " AND C.medico_id = ?"
        params.append(medico_id)
    query += " ORDER BY C.fecha, C.hora"
    cursor.execute(query, params)
    citas = cursor.fetchall()
    conexion.close()
    return citas

def editar_cita(cita_id, nueva_fecha, nueva_hora):
    """
    Cambia la fecha y hora de la cita, validando que la nueva fecha/hora no sean pasadas.
    Maneja la liberación del horario anterior y la reserva del nuevo.
    """
    try:
        new_dt = datetime.strptime(f"{nueva_fecha} {nueva_hora}", "%Y-%m-%d %H:%M")
    except Exception:
        return False, "Formato de fecha u hora inválido."
    if new_dt < datetime.now():
        return False, "No se puede agendar una cita en el pasado."
    conexion = conectar_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT medico_id, fecha, hora, estado FROM Citas WHERE id = ?", (cita_id,))
        cita_row = cursor.fetchone()
        if not cita_row:
            conexion.close()
            return False, "Cita no encontrada."
        med_id, old_fecha, old_hora, estado = cita_row
        if estado != 'Pendiente':
            return False, "Solo se pueden editar citas pendientes."
        cursor.execute("""
            UPDATE Horarios 
            SET estado = 'Disponible'
            WHERE medico_id = ? AND fecha = ? AND hora = ?
        """, (med_id, old_fecha, old_hora))
        cursor.execute("""
            UPDATE Citas 
            SET fecha = ?, hora = ?
            WHERE id = ?
        """, (nueva_fecha, nueva_hora, cita_id))
        cursor.execute("""
            UPDATE Horarios
            SET estado = 'Reservado'
            WHERE medico_id = ? AND fecha = ? AND hora = ?
        """, (med_id, nueva_fecha, nueva_hora))
        conexion.commit()
        return True, "Cita reagendada correctamente."
    except sqlite3.IntegrityError as e:
        return False, f"Error de integridad al editar la cita: {e}"
    finally:
        conexion.close()

def atender_cita(cita_id, asistencia):
    """
    Marca la cita con la asistencia indicada.
    La variable 'asistencia' debe ser 'Presente' o 'Ausente'.
    Solo se pueden atender citas en estado 'Pendiente'.
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT estado FROM Citas WHERE id = ?", (cita_id,))
        row = cursor.fetchone()
        if not row:
            conexion.close()
            return False, "Cita no encontrada."
        if row[0] != 'Pendiente':
            conexion.close()
            return False, "Solo se pueden atender citas pendientes."
        cursor.execute("UPDATE Citas SET estado = ? WHERE id = ?", (asistencia, cita_id))
        conexion.commit()
        return True, "Cita atendida correctamente."
    except sqlite3.Error as e:
        return False, f"Error al atender la cita: {e}"
    finally:
        conexion.close()

def registrar_cita_admin(paciente_id, medico_id, fecha, hora):
    """
    Agenda una cita a nombre de un paciente (como administrador).
    Es un alias de registrar_cita.
    """
    return registrar_cita(paciente_id, medico_id, fecha, hora)

def obtener_medico_id_por_usuario_id(user_id):
    """
    Dado un user_id (Usuarios.id), retorna el id del médico (Medicos.id)
    donde Medicos.usuario_id = user_id, o None si no existe.
    """
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT id FROM Medicos WHERE usuario_id = ?", (user_id,))
    row = cursor.fetchone()
    conexion.close()
    if row:
        return row[0]
    return None

# Si se ejecuta este módulo de forma independiente, se crea la base de datos.
if __name__ == "__main__":
    crear_base_de_datos()
