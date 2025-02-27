import flet as ft
from bd_medica import verificar_credenciales, crear_base_de_datos, conectar_bd
import registro_flet
import interfaz_paciente
import interfaz_medico
import recuperar_clave  # Se importa el módulo de recuperación de contraseña
import os
import sys

def resource_path(relative_path):
    """Obtiene la ruta absoluta del recurso, compatible con PyInstaller."""
    try:
        # Cuando se usa PyInstaller, sys._MEIPASS contiene la ruta temporal de los recursos extraídos.
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def correo_existe(email: str) -> bool:
    """
    Verifica si el correo (en minúsculas y sin espacios) existe en la tabla Usuarios.
    Retorna True si existe, False en caso contrario.
    """
    email = email.strip().lower()
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Usuarios WHERE LOWER(email) = ?", (email,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def main(page: ft.Page):
    crear_base_de_datos()
    page.title = "Inicio de Sesión - Citas Médicas"
    page.theme_mode = ft.ThemeMode.LIGHT  # Tema por defecto
    page.window_width = 420
    page.window_height = 500
    page.padding = 30

    # Imagen de fondo
    img_path = resource_path("assets/fondo.png")

    def get_control_width():
        return min(350, page.width * 0.8)

    # Alternar tema
    def toggle_theme(e):
        page.theme_mode = (
            ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        )
        page.update()

    toggle_theme_button = ft.IconButton(
        icon=ft.Icons.BRIGHTNESS_6,
        tooltip="Cambiar tema (claro/oscuro)",
        on_click=toggle_theme,
        icon_color="blue"
    )

    # Tipo de usuario (Radio)
    user_type_radio = ft.RadioGroup(
        content=ft.Row(
            [
                ft.Radio(value="Paciente", label="👤 Paciente"),
                ft.Radio(value="Administrador", label="🩺 Administrador"),
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        value="Paciente"
    )

    email_input = ft.TextField(
        label="Correo electrónico", 
        width=get_control_width(), 
        height=45
    )
    password_input = ft.TextField(
        label="Contraseña", 
        password=True, 
        can_reveal_password=True, 
        width=get_control_width(), 
        height=45
    )

    # Indicador de carga
    loading_indicator = ft.ProgressBar(
        width=get_control_width(), 
        color="blue", 
        visible=False
    )

    # Ícono de "Olvidaste tu contraseña?"
    forgot_password_icon = ft.Icon(ft.Icons.LOCK_OUTLINE, size=16, color="blue")

    def update_forgot_icon(new_color: str):
        forgot_password_icon.color = new_color
        page.update()

    def forgot_password(_):
        update_forgot_icon("blue")
        page.snack_bar = ft.SnackBar(
            ft.Text("Redirigiendo a recuperación de contraseña...", color="white"),
            bgcolor="orange"
        )
        page.snack_bar.open = True
        page.update()
        page.clean()
        recuperar_clave.main(page)

    def login(_):
        # Reiniciar feedback visual
        email_input.border_color = None
        password_input.border_color = None
        page.update()

        # Mostrar spinner y deshabilitar botón
        loading_indicator.visible = True
        login_button.disabled = True
        page.update()

        # Validar campos
        if not email_input.value or not password_input.value:
            email_input.border_color = "red"
            password_input.border_color = "red"
            page.snack_bar = ft.SnackBar(
                ft.Text("Completa todos los campos", color="white"), 
                bgcolor="red"
            )
            page.snack_bar.open = True
            loading_indicator.visible = False
            login_button.disabled = False
            page.update()
            return

        email_val = email_input.value.strip().lower()

        if not correo_existe(email_val):
            email_input.border_color = "red"
            page.snack_bar = ft.SnackBar(
                ft.Text("El correo no está registrado", color="white"), 
                bgcolor="red"
            )
            page.snack_bar.open = True
            loading_indicator.visible = False
            login_button.disabled = False
            page.update()
            return

        valid, tipo_bd, user_id = verificar_credenciales(email_val, password_input.value)
        if valid:
            tipo_radio = user_type_radio.value
            if tipo_bd != tipo_radio:
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"Tu cuenta es '{tipo_bd}', no puedes ingresar como '{tipo_radio}'.", color="white"),
                    bgcolor="red"
                )
                page.snack_bar.open = True
                loading_indicator.visible = False
                login_button.disabled = False
                page.update()
                return
            else:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Inicio de sesión exitoso", color="white"), 
                    bgcolor="green"
                )
                page.snack_bar.open = True
                page.update()
                page.clean()
                if tipo_bd == "Paciente":
                    interfaz_paciente.main(page, user_id)
                else:
                    interfaz_medico.main(page, user_id)
        else:
            password_input.border_color = "red"
            page.snack_bar = ft.SnackBar(
                ft.Text("Contraseña incorrecta", color="white"), 
                bgcolor="red"
            )
            page.snack_bar.open = True
            page.update()

        loading_indicator.visible = False
        login_button.disabled = False
        page.update()

    def google_login(_):
        """
        Inicia el flujo de registro/inicio de sesión con Google.
        Llama al módulo registro_google que gestiona la autenticación, descarga del client_secret.json
        y la gestión del token.json (renovación y almacenamiento).
        """
        page.snack_bar = ft.SnackBar(
            ft.Text("Abriendo navegador para el registro con Google..."), bgcolor="blue"
        )
        page.snack_bar.open = True
        page.update()
        page.clean()
        import registro_google
        registro_google.main(page)

    def register(_):
        page.clean()
        registro_flet.main(page)

    forgot_password_link = ft.TextButton(
        content=ft.Row([
            forgot_password_icon,
            ft.Text(
                "Olvidaste tu contraseña?",
                style=ft.TextStyle(
                    decoration=ft.TextDecoration.UNDERLINE,
                    color="blue"
                )
            )
        ]),
        on_click=forgot_password
    )
    register_button = ft.TextButton("Registrarse", on_click=register)

    login_button = ft.ElevatedButton(
        "Iniciar Sesión",
        on_click=login,
        bgcolor="blue",
        color="white",
        width=get_control_width(),
        height=45,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            elevation=10,
            shadow_color="grey"
        )
    )
    google_button = ft.OutlinedButton(
        "Iniciar sesión con Google", 
        on_click=google_login, 
        width=get_control_width(), 
        height=45
    )

    # Título
    title_text = ft.Text(
        "Iniciar Sesión", 
        size=28, 
        weight=ft.FontWeight.BOLD, 
        text_align=ft.TextAlign.CENTER,
        color="blue"
    )

    content_column = ft.Column(
        [
            title_text,
            toggle_theme_button,
            user_type_radio,
            email_input,
            password_input,
            login_button,
            loading_indicator,
            google_button,
            ft.Row([forgot_password_link], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
            ft.Row([register_button], alignment=ft.MainAxisAlignment.CENTER)
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
    )

    card_container = ft.Container(
        content=content_column,
        padding=20,
        bgcolor="white",
        border_radius=12,
        shadow=ft.BoxShadow(
            blur_radius=8,
            spread_radius=2,
            color="grey",
            offset=ft.Offset(0, 4)
        ),
        animate=300
    )

    main_container = ft.Container(
        content=card_container,
        expand=True,
        alignment=ft.alignment.center,
        bgcolor=None
    )

    background_image = ft.Image(
        src=img_path,
        fit=ft.ImageFit.COVER,
        expand=True
    )

    overlay = ft.Container(
        expand=True,
        bgcolor="#66000000"
    )

    stack = ft.Stack(
        expand=True,
        controls=[
            background_image,
            overlay,
            main_container
        ]
    )

    page.add(stack)

    def on_resize(_):
        new_width = get_control_width()
        email_input.width = new_width
        password_input.width = new_width
        login_button.width = new_width
        google_button.width = new_width
        loading_indicator.width = new_width
        page.update()

    page.on_resize = on_resize

if __name__ == "__main__":
    ft.app(target=main)
