import flet as ft
import re
import base64
import io
import os

# Para redimensionar la imagen
from PIL import Image

from bd_medica import registrar_usuario_en_bd

def main(page: ft.Page, prefill_data=None):
    page.title = "Registro de Usuario - Citas Médicas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 800
    page.window_height = 700
    page.window_resizable = True
    page.padding = 15

    import interfaz_paciente
    import interfaz_medico  # Administrador

    left_width = 450
    right_width = 380
    full_width = left_width
    half_width = (left_width - 10) / 2

    # -------------------------------------------------------------
    # 1) VARIABLE PARA GUARDAR LA FOTO (Base64)
    # -------------------------------------------------------------
    photo_data = None

    # -------------------------------------------------------------
    # 2) Selección de usuario y especialidad
    # -------------------------------------------------------------
    user_type = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="Paciente", label="Paciente"),
            ft.Radio(value="Administrador", label="Administrador"),
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
        value="Paciente"
    )
    specialty_dropdown = ft.Dropdown(
        label="Especialidad (solo Administrador)",
        width=220,
        options=[
            ft.dropdown.Option("Seleccionar"),
            ft.dropdown.Option("Medicina General"),
            ft.dropdown.Option("Medicina Familiar"),
            ft.dropdown.Option("Odontología"),
            ft.dropdown.Option("Obstetricia"),
            ft.dropdown.Option("Ginecología"),
        ],
        value="Seleccionar",
        visible=False
    )

    def toggle_specialty_visibility(_):
        specialty_dropdown.visible = (user_type.value == "Administrador")
        page.update()

    user_type.on_change = toggle_specialty_visibility

    # -------------------------------------------------------------
    # 3) FILE PICKER PARA SUBIR FOTO Y PREVISUALIZAR
    # -------------------------------------------------------------
    file_picker = ft.FilePicker()

    # Imagen inicialmente oculta para no mostrar error src vacío
    img_preview = ft.Image(
        width=200,
        height=200,
        fit=ft.ImageFit.CONTAIN,
        visible=False
    )

    def on_pick_files(e: ft.FilePickerResultEvent):
        nonlocal photo_data
        if e.files and len(e.files) > 0:
            ruta_imagen = e.files[0].path
            try:
                # 1) Leer la imagen en binario
                file_size = os.path.getsize(ruta_imagen)
                size_in_mb = file_size / (1024 * 1024)
                if size_in_mb > 10:
                    page.snack_bar = ft.SnackBar(
                        ft.Text("❌ La imagen excede los 10 MB permitidos."),
                        bgcolor="red"
                    )
                    page.snack_bar.open = True
                    return

                with open(ruta_imagen, "rb") as f:
                    file_bytes = f.read()

                # 2) Redimensionar si excede el tamaño deseado (ej. 300×400)
                max_width, max_height = 300, 400
                image_pil = Image.open(io.BytesIO(file_bytes))
                original_width, original_height = image_pil.size

                # Si es más grande, se escala
                if original_width > max_width or original_height > max_height:
                    image_pil.thumbnail((max_width, max_height))

                # Guardar la imagen escalada en bytes
                output = io.BytesIO()
                image_pil.save(output, format="PNG")  # O el formato que prefieras
                scaled_bytes = output.getvalue()

                # Convertir a Base64 para la BD y para mostrar
                photo_data = base64.b64encode(scaled_bytes).decode("utf-8")

                # 3) Actualizar la previsualización
                img_preview.src_base64 = photo_data
                img_preview.visible = True
                img_preview.update()

                # Mensaje sobre la resolución
                new_width, new_height = image_pil.size
                final_size_kb = round(len(scaled_bytes) / 1024, 1)
                page.snack_bar = ft.SnackBar(
                    ft.Text(
                        f"Foto cargada.\n"
                        f"Resolución original: {original_width}x{original_height} px.\n"
                        f"Resolución final: {new_width}x{new_height} px.\n"
                        f"Tamaño final: {final_size_kb} KB."
                    ),
                    bgcolor="green"
                )
                page.snack_bar.open = True

            except Exception as err:
                page.snack_bar = ft.SnackBar(ft.Text(f"Error al leer la imagen: {err}"), bgcolor="red")
                page.snack_bar.open = True
        else:
            page.snack_bar = ft.SnackBar(ft.Text("No se seleccionó ninguna imagen"), bgcolor="red")
            page.snack_bar.open = True
        page.update()

    file_picker.on_result = on_pick_files
    page.overlay.append(file_picker)

    def subir_foto_click(e):
        file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)

    def eliminar_foto(e):
        nonlocal photo_data
        photo_data = None
        img_preview.src_base64 = None
        img_preview.visible = False
        img_preview.update()
        page.snack_bar = ft.SnackBar(ft.Text("Foto eliminada"), bgcolor="blue")
        page.snack_bar.open = True
        page.update()

    trash_icon = ft.IconButton(
        icon=ft.icons.DELETE,
        tooltip="Eliminar foto",
        on_click=eliminar_foto,
        icon_color="red"
    )

    block_avatar = ft.Column(
        controls=[
            ft.ElevatedButton(
                "Subir Fotografía",
                icon=ft.Icon(ft.Icons.CAMERA),
                on_click=subir_foto_click,
                width=200
            ),
            ft.Row([img_preview, trash_icon], alignment=ft.MainAxisAlignment.CENTER)
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8
    )

    # -------------------------------------------------------------
    # 4) CAMPOS DEL FORMULARIO
    # -------------------------------------------------------------
    first_name = ft.TextField(label="Primer Nombre *", width=half_width)
    second_name = ft.TextField(label="Segundo Nombre", width=half_width)
    last_name = ft.TextField(label="Primer Apellido *", width=half_width)
    second_last_name = ft.TextField(label="Segundo Apellido", width=half_width)
    email_input = ft.TextField(label="Correo Electrónico *", width=full_width)
    phone_input = ft.TextField(label="Teléfono (10 dígitos) *", width=half_width)
    cedula_input = ft.TextField(label="Cédula (10 dígitos) *", width=half_width)

    # -------------------------------------------------------------
    # 5) REQUISITOS DE CONTRASEÑA
    # -------------------------------------------------------------
    req_length = ft.Text("• Mínimo 8 caracteres", color="red", size=12)
    req_upper = ft.Text("• Al menos una letra mayúscula", color="red", size=12)
    req_digit = ft.Text("• Al menos un dígito", color="red", size=12)
    req_special = ft.Text("• Al menos un carácter especial (@$!%*?&)", color="red", size=12)
    password_reqs = ft.Column([req_length, req_upper, req_digit, req_special])

    password_input = ft.TextField(label="Contraseña *", password=True, can_reveal_password=True)
    confirm_password_input = ft.TextField(label="Repetir Contraseña *", password=True, can_reveal_password=True)

    def update_password_requirements(e):
        pwd = password_input.value or ""
        if len(pwd) >= 8:
            req_length.color = "green"
        else:
            req_length.color = "red"

        if re.search(r'[A-Z]', pwd):
            req_upper.color = "green"
        else:
            req_upper.color = "red"

        if re.search(r'\d', pwd):
            req_digit.color = "green"
        else:
            req_digit.color = "red"

        if re.search(r'[@$!%*?&]', pwd):
            req_special.color = "green"
        else:
            req_special.color = "red"

        password_reqs.update()
        page.update()

    password_input.on_change = update_password_requirements

    # Agrupamos contraseña y requisitos en una columna
    password_container = ft.Column(
        [
            password_input,
            password_reqs
        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        width=half_width
    )
    confirm_password_container = ft.Column(
        [
            confirm_password_input
        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        width=half_width
    )
    row_passwords = ft.Row(
        controls=[password_container, confirm_password_container],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START,
        spacing=8
    )

    # Prellenar si llega info
    if prefill_data:
        first_name.value = prefill_data.get("first_name", "")
        second_name.value = prefill_data.get("second_name", "")
        last_name.value = prefill_data.get("last_name", "")
        second_last_name.value = prefill_data.get("second_last_name", "")
        email_input.value = prefill_data.get("email", "")
        phone_input.value = prefill_data.get("phone", "")

    # -------------------------------------------------------------
    # 6) PREGUNTAS DE SEGURIDAD
    # -------------------------------------------------------------
    security_q_options = [
        ft.dropdown.Option("Seleccionar"),
        ft.dropdown.Option("¿Cuál es el nombre de tu primera mascota?"),
        ft.dropdown.Option("¿Cuál es el apellido de soltera de tu madre?"),
        ft.dropdown.Option("¿En qué ciudad naciste?"),
        ft.dropdown.Option("¿Cuál es tu comida favorita?"),
        ft.dropdown.Option("¿Cuál es el nombre de tu escuela secundaria?")
    ]

    security_q1_dropdown = ft.Dropdown(label="Pregunta 1 🔒", width=right_width * 0.9, options=security_q_options, value="Seleccionar")
    security_q1_answer = ft.TextField(label="Respuesta 1 *", width=right_width * 0.9)
    security_q2_dropdown = ft.Dropdown(label="Pregunta 2 🔒", width=right_width * 0.9, options=security_q_options, value="Seleccionar")
    security_q2_answer = ft.TextField(label="Respuesta 2 *", width=right_width * 0.9)
    security_q3_dropdown = ft.Dropdown(label="Pregunta 3 🔒", width=right_width * 0.9, options=security_q_options, value="Seleccionar")
    security_q3_answer = ft.TextField(label="Respuesta 3 *", width=right_width * 0.9)

    security_question1 = ft.Column([security_q1_dropdown, security_q1_answer], spacing=4)
    security_question2 = ft.Column([security_q2_dropdown, security_q2_answer], spacing=4)
    security_question3 = ft.Column([security_q3_dropdown, security_q3_answer], spacing=4)

    block2 = ft.Column(
        controls=[
            ft.Text("Preguntas de seguridad:", weight=ft.FontWeight.BOLD, size=16),
            security_question1,
            security_question2,
            security_question3,
        ],
        spacing=15
    )

    global_message = ft.Text("", size=14)

    # -------------------------------------------------------------
    # 7) FUNCIONES: LIMPIAR, CANCELAR, REGISTRAR
    # -------------------------------------------------------------
    def limpiar_campos(_):
        nonlocal photo_data
        for field in [
            first_name, second_name, last_name, second_last_name,
            email_input, phone_input, cedula_input,
            password_input, confirm_password_input,
            security_q1_answer, security_q2_answer, security_q3_answer
        ]:
            field.value = ""
            field.error_text = ""
            field.border_color = None

        security_q1_dropdown.value = "Seleccionar"
        security_q2_dropdown.value = "Seleccionar"
        security_q3_dropdown.value = "Seleccionar"
        specialty_dropdown.value = "Seleccionar"
        specialty_dropdown.visible = (user_type.value == "Administrador")
        global_message.value = ""

        # Limpiar foto y preview
        img_preview.src_base64 = None
        img_preview.visible = False
        img_preview.update()
        photo_data = None
        page.update()

    def cancelar(_):
        page.clean()
        import login_flet
        login_flet.main(page)

    def registrar(_):
        for field in [
            first_name, last_name, email_input, cedula_input, phone_input,
            password_input, confirm_password_input,
            security_q1_answer, security_q2_answer, security_q3_answer
        ]:
            field.error_text = ""
            field.border_color = None
        global_message.value = ""
        has_error = False

        # Validaciones
        if not first_name.value.strip():
            first_name.error_text = "El primer nombre es obligatorio"
            first_name.border_color = "red"
            has_error = True

        if not last_name.value.strip():
            last_name.error_text = "El primer apellido es obligatorio"
            last_name.border_color = "red"
            has_error = True

        if not email_input.value.strip():
            email_input.error_text = "El correo es obligatorio"
            email_input.border_color = "red"
            has_error = True
        elif "@" not in email_input.value:
            email_input.error_text = "Correo inválido"
            email_input.border_color = "red"
            has_error = True

        if not cedula_input.value.strip():
            cedula_input.error_text = "La cédula es obligatoria"
            cedula_input.border_color = "red"
            has_error = True
        elif not re.match(r'^\d{10}$', cedula_input.value.strip()):
            cedula_input.error_text = "La cédula debe tener 10 dígitos"
            cedula_input.border_color = "red"
            has_error = True

        if not phone_input.value.strip():
            phone_input.error_text = "El teléfono es obligatorio"
            phone_input.border_color = "red"
            has_error = True
        elif not re.match(r'^\d{10}$', phone_input.value.strip()):
            phone_input.error_text = "El teléfono debe tener 10 dígitos"
            phone_input.border_color = "red"
            has_error = True

        if not password_input.value:
            password_input.error_text = "La contraseña es obligatoria"
            password_input.border_color = "red"
            has_error = True
        elif not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$', password_input.value):
            password_input.error_text = "La contraseña no cumple los requisitos"
            password_input.border_color = "red"
            has_error = True

        if not confirm_password_input.value:
            confirm_password_input.error_text = "Debe repetir la contraseña"
            confirm_password_input.border_color = "red"
            has_error = True
        elif password_input.value != confirm_password_input.value:
            confirm_password_input.error_text = "Las contraseñas no coinciden"
            confirm_password_input.border_color = "red"
            has_error = True

        if security_q1_dropdown.value == "Seleccionar":
            security_q1_dropdown.error_text = "Seleccione una pregunta"
            has_error = True
        if not security_q1_answer.value.strip():
            security_q1_answer.error_text = "La respuesta es obligatoria"
            has_error = True

        if security_q2_dropdown.value == "Seleccionar":
            security_q2_dropdown.error_text = "Seleccione una pregunta"
            has_error = True
        if not security_q2_answer.value.strip():
            security_q2_answer.error_text = "La respuesta es obligatoria"
            has_error = True

        if security_q3_dropdown.value == "Seleccionar":
            security_q3_dropdown.error_text = "Seleccione una pregunta"
            has_error = True
        if not security_q3_answer.value.strip():
            security_q3_answer.error_text = "La respuesta es obligatoria"
            has_error = True

        # Evitar repetir preguntas
        if (security_q1_dropdown.value != "Seleccionar" and
            security_q2_dropdown.value != "Seleccionar" and
            security_q3_dropdown.value != "Seleccionar"):
            if len({security_q1_dropdown.value, security_q2_dropdown.value, security_q3_dropdown.value}) < 3:
                global_message.value = "Las preguntas de seguridad deben ser diferentes."
                global_message.color = "red"
                has_error = True

        page.update()
        if has_error:
            return

        global_message.value = "Registrando usuario..."
        global_message.color = "blue"
        page.update()

        # Construir nombres completos
        nombres = first_name.value.strip()
        if second_name.value.strip():
            nombres += " " + second_name.value.strip()

        apellidos = last_name.value.strip()
        if second_last_name.value.strip():
            apellidos += " " + second_last_name.value.strip()

        especialidad_seleccionada = (
            specialty_dropdown.value
            if (user_type.value == "Administrador" and specialty_dropdown.value != "Seleccionar")
            else None
        )

        exito, mensaje, new_user_id = registrar_usuario_en_bd(
            tipo_usuario=user_type.value,
            nombres=nombres,
            apellidos=apellidos,
            email=email_input.value.strip(),
            telefono=phone_input.value.strip(),
            cedula=cedula_input.value.strip(),
            password=password_input.value,
            especialidad=especialidad_seleccionada,
            security_q1=security_q1_dropdown.value, security_a1=security_q1_answer.value.strip(),
            security_q2=security_q2_dropdown.value, security_a2=security_q2_answer.value.strip(),
            security_q3=security_q3_dropdown.value, security_a3=security_q3_answer.value.strip(),
            photo=photo_data  # Imagen en Base64 (ya redimensionada)
        )

        global_message.value = mensaje
        global_message.color = "green" if exito else "red"
        page.update()

        if exito and new_user_id:
            page.clean()
            if user_type.value == "Paciente":
                interfaz_paciente.main(page, new_user_id)
            else:
                interfaz_medico.main(page, new_user_id)

    # -------------------------------------------------------------
    # 8) ESTRUCTURA VISUAL
    # -------------------------------------------------------------
    row_user_type = ft.Row(
        [user_type, specialty_dropdown],
        alignment=ft.MainAxisAlignment.SPACE_AROUND,
        spacing=10
    )
    row_names = ft.Row([first_name, second_name], spacing=8)
    row_surnames = ft.Row([last_name, second_last_name], spacing=8)
    row_email = email_input
    row_contact = ft.Row([phone_input, cedula_input], spacing=8)

    row_passwords = ft.Row(
        controls=[password_container, confirm_password_container],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START,
        spacing=8
    )

    block1 = ft.Column(
        [
            row_user_type,
            row_names,
            row_surnames,
            row_email,
            row_contact,
            row_passwords
        ],
        spacing=15
    )

    blocks_row = ft.Row(
        controls=[
            ft.Container(content=block1, width=left_width, padding=5),
            ft.Container(content=block2, width=right_width, padding=5)
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20
    )

    register_button = ft.ElevatedButton("Registrar", on_click=registrar, bgcolor="blue", color="white", width=150, height=40)
    clear_button = ft.OutlinedButton("Limpiar", on_click=limpiar_campos, width=150, height=40)
    cancel_button = ft.ElevatedButton("Cancelar", on_click=cancelar, bgcolor="red", color="white", width=150, height=40)

    form = ft.Column(
        [
            ft.Text("Registro de Usuario", size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            block_avatar,
            blocks_row,
            global_message,
            ft.Row([register_button, clear_button, cancel_button], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15
    )

    container = ft.Container(content=form, alignment=ft.alignment.center, padding=15)
    scrollable = ft.ListView(controls=[container], expand=True)
    page.add(scrollable)
    page.update()
