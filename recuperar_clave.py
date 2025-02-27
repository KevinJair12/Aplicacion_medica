import flet as ft
import re
import sqlite3
from bd_medica import conectar_bd, hash_password

# Opciones fijas para las preguntas de seguridad (las mismas que se usan en el registro)
SECURITY_QUESTIONS = [
    "¿Cuál es el nombre de tu primera mascota?",
    "¿Cuál es el apellido de soltera de tu madre?",
    "¿En qué ciudad naciste?",
    "¿Cuál es tu comida favorita?",
    "¿Cuál es el nombre de tu escuela secundaria?"
]

def reset_password(user_id: int, new_password: str) -> (bool, str):
    """Actualiza la contraseña del usuario en la base de datos."""
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("UPDATE Usuarios SET password = ? WHERE id = ?", (hash_password(new_password), user_id))
        conexion.commit()
        conexion.close()
        return True, "Contraseña actualizada correctamente."
    except sqlite3.Error as e:
        return False, f"Error al actualizar la contraseña: {e}"

def main(page: ft.Page):
    page.title = "Recuperar Contraseña - Citas Médicas"
    page.theme_mode = ft.ThemeMode.LIGHT
    # Se aumenta el ancho para poder mostrar dos bloques lado a lado
    page.window_width = 900  
    page.window_height = 700
    page.padding = 20

    def get_control_width():
        # Cada control se ajusta al 40% del ancho de la ventana (máximo 350px)
        return min(350, page.width * 0.4)

    # ----------------------------
    # Bloque Izquierdo: Identificación y Seguridad Grupo 1
    # ----------------------------
    cedula_input = ft.TextField(
        label="Cédula (10 dígitos)",
        width=get_control_width(),
        prefix_icon=ft.Icon(ft.Icons.BADGE),
        hint_text="Ingrese su cédula",
    )
    email_input = ft.TextField(
        label="Correo Electrónico",
        width=get_control_width(),
        prefix_icon=ft.Icon(ft.Icons.EMAIL),
        hint_text="Ingrese su correo",
    )
    identification_section = ft.Column(
        controls=[
            ft.Text("Identificación", size=20, weight=ft.FontWeight.BOLD),
            cedula_input,
            email_input,
        ],
        spacing=10
    )

    security_q1_dropdown = ft.Dropdown(
        label="Pregunta de Seguridad 1",
        width=get_control_width(),
        options=[ft.dropdown.Option("Seleccionar")] + [ft.dropdown.Option(q) for q in SECURITY_QUESTIONS],
        value="Seleccionar"
    )
    security_a1_input = ft.TextField(
        label="Respuesta 1",
        width=get_control_width(),
        prefix_icon=ft.Icon(ft.Icons.LOCK),
        hint_text="Ingrese su respuesta",
    )
    security_q2_dropdown = ft.Dropdown(
        label="Pregunta de Seguridad 2",
        width=get_control_width(),
        options=[ft.dropdown.Option("Seleccionar")] + [ft.dropdown.Option(q) for q in SECURITY_QUESTIONS],
        value="Seleccionar"
    )
    security_a2_input = ft.TextField(
        label="Respuesta 2",
        width=get_control_width(),
        prefix_icon=ft.Icon(ft.Icons.LOCK),
        hint_text="Ingrese su respuesta",
    )
    security_group1_section = ft.Column(
        controls=[
            ft.Text("Preguntas de Seguridad (Grupo 1)", size=20, weight=ft.FontWeight.BOLD),
            security_q1_dropdown,
            security_a1_input,
            security_q2_dropdown,
            security_a2_input,
        ],
        spacing=10
    )

    left_block = ft.Column(
        controls=[identification_section, security_group1_section],
        spacing=20,
        alignment=ft.MainAxisAlignment.START,
    )

    # ----------------------------
    # Bloque Derecho: Seguridad Grupo 2 y Nueva Contraseña
    # ----------------------------
    # Se elimina el título del grupo 2; se muestran directamente los campos
    security_q3_dropdown = ft.Dropdown(
        label="Pregunta de Seguridad 3",
        width=get_control_width(),
        options=[ft.dropdown.Option("Seleccionar")] + [ft.dropdown.Option(q) for q in SECURITY_QUESTIONS],
        value="Seleccionar"
    )
    security_a3_input = ft.TextField(
        label="Respuesta 3",
        width=get_control_width(),
        prefix_icon=ft.Icon(ft.Icons.LOCK),
        hint_text="Ingrese su respuesta",
    )
    security_group2_section = ft.Column(
        controls=[
            security_q3_dropdown,
            security_a3_input,
        ],
        spacing=10
    )

    # Sección de Nueva Contraseña
    new_password_input = ft.TextField(
        label="Nueva Contraseña",
        password=True,
        can_reveal_password=True,
        width=get_control_width(),
        prefix_icon=ft.Icon(ft.Icons.LOCK)
    )
    confirm_password_input = ft.TextField(
        label="Confirmar Contraseña",
        password=True,
        can_reveal_password=True,
        width=get_control_width(),
        prefix_icon=ft.Icon(ft.Icons.LOCK)
    )
    # Requisitos de la contraseña que se actualizan en tiempo real
    req_length = ft.Text("● Mínimo 8 caracteres", color="red", size=12)
    req_upper = ft.Text("● Al menos 1 mayúscula", color="red", size=12)
    req_digit = ft.Text("● Al menos 1 dígito", color="red", size=12)
    req_special = ft.Text("● Al menos 1 símbolo (@$!%*?&)", color="red", size=12)
    password_requirements_section = ft.Column(
        controls=[
            ft.Text("Requisitos de la contraseña:", weight=ft.FontWeight.BOLD, size=14),
            req_length,
            req_upper,
            req_digit,
            req_special,
        ],
        spacing=4
    )
    new_password_section = ft.Column(
        controls=[
            ft.Text("Establecer Nueva Contraseña", size=20, weight=ft.FontWeight.BOLD),
            new_password_input,
            confirm_password_input,
            password_requirements_section,
        ],
        spacing=10
    )

    right_block = ft.Column(
        controls=[security_group2_section, new_password_section],
        spacing=20,
        alignment=ft.MainAxisAlignment.END,
    )

    # ----------------------------
    # Sección de Acciones: Botones y mensaje global
    # ----------------------------
    global_message = ft.Text("", size=14)
    def regresar(_):
        page.clean()
        import login_flet
        login_flet.main(page)
    
    def recuperar(_):
        # Reiniciar mensajes de error
        global_message.value = ""
        cedula_input.error_text = ""
        email_input.error_text = ""
        security_q1_dropdown.error_text = ""
        security_a1_input.error_text = ""
        security_q2_dropdown.error_text = ""
        security_a2_input.error_text = ""
        security_q3_dropdown.error_text = ""
        security_a3_input.error_text = ""
        new_password_input.error_text = ""
        confirm_password_input.error_text = ""
        page.update()
    
        error = False
        # Validar campos de identificación y seguridad
        if not cedula_input.value.strip():
            cedula_input.error_text = "Obligatorio"
            error = True
        if not email_input.value.strip():
            email_input.error_text = "Obligatorio"
            error = True
        if security_q1_dropdown.value == "Seleccionar":
            security_q1_dropdown.error_text = "Seleccione una pregunta"
            error = True
        if not security_a1_input.value.strip():
            security_a1_input.error_text = "Obligatorio"
            error = True
        if security_q2_dropdown.value == "Seleccionar":
            security_q2_dropdown.error_text = "Seleccione una pregunta"
            error = True
        if not security_a2_input.value.strip():
            security_a2_input.error_text = "Obligatorio"
            error = True
        if security_q3_dropdown.value == "Seleccionar":
            security_q3_dropdown.error_text = "Seleccione una pregunta"
            error = True
        if not security_a3_input.value.strip():
            security_a3_input.error_text = "Obligatorio"
            error = True
        # Validar nueva contraseña y confirmación
        npw = new_password_input.value.strip()
        cpw = confirm_password_input.value.strip()
        if not npw:
            new_password_input.error_text = "Obligatorio"
            error = True
        elif not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$', npw):
            new_password_input.error_text = "No cumple los requisitos"
            error = True
        if not cpw:
            confirm_password_input.error_text = "Obligatorio"
            error = True
        if npw and cpw and npw != cpw:
            confirm_password_input.error_text = "Las contraseñas no coinciden"
            error = True
    
        if error:
            global_message.value = "Revise y corrija los errores en los campos."
            global_message.color = "red"
            page.update()
            return
    
        # Consultar la base de datos para verificar usuario, preguntas y respuestas
        cedula = cedula_input.value.strip()
        email = email_input.value.strip().lower()
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT id, security_q1, security_a1, security_q2, security_a2, security_q3, security_a3
                FROM Usuarios
                WHERE cedula = ? AND LOWER(email) = ?
            """, (cedula, email))
            usuario = cursor.fetchone()
            conexion.close()
        except Exception as e:
            global_message.value = f"Error al consultar la base de datos: {e}"
            global_message.color = "red"
            page.update()
            return
    
        if not usuario:
            global_message.value = "Usuario no encontrado."
            global_message.color = "red"
            page.update()
            return
    
        user_id, db_q1, db_a1, db_q2, db_a2, db_q3, db_a3 = usuario
    
        # Comparar preguntas y respuestas (convertidas a minúsculas y sin espacios laterales)
        if (security_q1_dropdown.value != db_q1 or
            security_a1_input.value.strip().lower() != (db_a1 or "").strip().lower() or
            security_q2_dropdown.value != db_q2 or
            security_a2_input.value.strip().lower() != (db_a2 or "").strip().lower() or
            security_q3_dropdown.value != db_q3 or
            security_a3_input.value.strip().lower() != (db_a3 or "").strip().lower()):
            global_message.value = "Las preguntas o respuestas no coinciden con nuestros registros."
            global_message.color = "red"
            page.update()
            return
    
        # Si todo es correcto, actualizar la contraseña en la base de datos
        exito, msg = reset_password(user_id, npw)
        global_message.value = msg
        global_message.color = "green" if exito else "red"
        page.update()
        if exito:
            import login_flet
            page.clean()
            login_flet.main(page)
    
    # Sección de acciones: botones y mensaje (colocados debajo de los dos bloques)
    actions_section = ft.Row(
        controls=[
            ft.ElevatedButton("Regresar", icon=ft.Icon(ft.Icons.ARROW_BACK), bgcolor="red", color="white", width=120, on_click=regresar),
            ft.ElevatedButton("Recuperar", icon=ft.Icon(ft.Icons.LOCK_OPEN), bgcolor="green", color="white", width=120, on_click=recuperar),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20
    )
    
    # Disponer los dos bloques en una fila
    blocks_row = ft.Row(
        controls=[
            ft.Container(content=left_block, padding=10, border=ft.border.all(1, "lightgray"), border_radius=5),
            ft.Container(content=right_block, padding=10, border=ft.border.all(1, "lightgray"), border_radius=5),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
    )
    
    # Finalmente, se organiza todo en una columna: los bloques y debajo la fila de acciones
    content = ft.Column(
        controls=[
            blocks_row,
            actions_section,
            global_message,
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
    )
    
    # Actualización dinámica de los requisitos de la contraseña
    def update_password_requirements(_):
        pw = new_password_input.value
        req_length.color = "green" if len(pw) >= 8 else "red"
        req_upper.color = "green" if any(c.isupper() for c in pw) else "red"
        req_digit.color = "green" if any(c.isdigit() for c in pw) else "red"
        req_special.color = "green" if any(c in "@$!%*?&" for c in pw) else "red"
        page.update()
    
    new_password_input.on_change = update_password_requirements
    
    page.clean()
    page.add(content)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
