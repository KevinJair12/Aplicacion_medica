# archivo: registro_google.py

import flet as ft
import requests
import webbrowser
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

def main(page: ft.Page):
    page.title = "Registro con Google"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 600
    page.window_height = 400
    page.padding = 0
    page.update()

    # 1) Preparamos el flujo OAuth sin run_local_server()
    flow = Flow.from_client_secrets_file(
        "client_secret.json",  # <-- Asegúrate de que sea credencial de tipo "Aplicación de escritorio"
        scopes=SCOPES
    )
    flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

    # 2) Generar la URL de autorización y abrir el navegador
    auth_url, _ = flow.authorization_url(prompt="consent")
    webbrowser.open(auth_url)

    # ----- INTERFAZ FLET -----
    # Creamos un TextField para que el usuario pegue el código de Google
    code_input = ft.TextField(
        label="Pega aquí el código de Google",
        autofocus=True,
        width=300,
    )

    # Texto de estado para mostrar mensajes de error
    status_text = ft.Text("", size=14, color="red", text_align=ft.TextAlign.CENTER)

    def cancel(_):
        """
        Si el usuario no desea continuar, limpiamos la pantalla y regresamos a login_flet.
        """
        page.snack_bar = ft.SnackBar(ft.Text("Autenticación cancelada."), bgcolor="red")
        page.snack_bar.open = True
        page.update()

        page.clean()
        import login_flet
        login_flet.main(page)

    def confirm(_):
        """
        El usuario pegó el código y hace clic en "Confirmar".
        Intentamos intercambiarlo por tokens y obtener los datos de usuario.
        """
        code = code_input.value.strip()
        if not code:
            status_text.value = "No ingresaste ningún código. Por favor, pégalo o presiona 'Cancelar'."
            status_text.color = "red"
            page.update()
            return

        try:
            # Intercambiar el código por tokens
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Obtener datos del usuario desde la API de Google
            resp = requests.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {credentials.token}"}
            )
            if resp.status_code != 200:
                raise Exception("Error al obtener datos de usuario.")

            user_info = resp.json()

            # Dividir los nombres
            given_name = user_info.get("given_name", "").strip()
            fn_parts = given_name.split(maxsplit=1)
            first_name = fn_parts[0] if len(fn_parts) > 0 else ""
            second_name = fn_parts[1] if len(fn_parts) > 1 else ""

            # Dividir los apellidos
            family_name = user_info.get("family_name", "").strip()
            ln_parts = family_name.split(maxsplit=1)
            last_name = ln_parts[0] if len(ln_parts) > 0 else ""
            second_last_name = ln_parts[1] if len(ln_parts) > 1 else ""

            prefill_data = {
                "first_name": first_name,
                "second_name": second_name,
                "last_name": last_name,
                "second_last_name": second_last_name,
                "email": user_info.get("email", ""),
                "phone": ""  # Google no provee teléfono por defecto
            }

            page.snack_bar = ft.SnackBar(ft.Text("¡Autenticación exitosa! Redirigiendo..."), bgcolor="green")
            page.snack_bar.open = True
            page.update()

            page.clean()
            import registro_flet
            registro_flet.main(page, prefill_data=prefill_data)

        except Exception as ex:
            status_text.value = f"Ocurrió un error: {str(ex)}"
            status_text.color = "red"
            page.update()

    # Botones "Confirmar" y "Cancelar"
    confirm_button = ft.ElevatedButton("Confirmar", on_click=confirm, bgcolor="blue", color="white")
    cancel_button = ft.ElevatedButton("Cancelar", on_click=cancel, bgcolor="red", color="white")

    # Contenido principal: título + instrucciones + TextField + Botones + Mensaje
    info_label = ft.Text(
        "Se abrió el navegador para que inicies sesión con Google.\n"
        "Copia el código que te muestre Google y pégalo aquí:",
        text_align=ft.TextAlign.CENTER,
        size=14
    )

    # "Tarjeta" centrada
    card_content = ft.Column(
        [
            ft.Text("Autenticación con Google", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            info_label,
            code_input,
            ft.Row(
                [confirm_button, cancel_button],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20
            ),
            status_text
        ],
        spacing=15,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    card_container = ft.Container(
        content=card_content,
        width=400,
        padding=20,
        bgcolor="white",
        border_radius=10,
        shadow=ft.BoxShadow(
            blur_radius=10,
            spread_radius=1,
            color="grey",
            offset=ft.Offset(0, 3)
        ),
    )

    # Para que se centre en la pantalla, usamos un Row o Stack expandida
    page.add(
        ft.Row(
            [card_container],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    )
    page.update()
