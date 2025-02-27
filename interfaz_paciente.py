import flet as ft
import datetime
from datetime import datetime as dt, timedelta, date
import calendar
import notificaciones_paciente

def update_notification_badge():
    notificaciones_paciente.generar_notificaciones(user_id)
    notifs = notificaciones_paciente.obtener_notificaciones(user_id)
    count = len([n for n in notifs if n["leido"] == 0])
    badge_text = str(count) if count > 0 else ""
    badge_container.content.value = badge_text
    badge_container.visible = True if count > 0 else False
    page.update()

from bd_medica import (
    crear_base_de_datos,
    obtener_medicos,
    obtener_horarios_disponibles,
    registrar_cita,
    obtener_usuario,
    actualizar_datos_usuario,
    cambiar_contrasena,
    obtener_citas_paciente,
    cancelar_cita,
    generar_horarios_disponibles,
    editar_cita
)

def main(page: ft.Page, user_id: int):
    # Asegurarse de que la base de datos y las tablas existan
    crear_base_de_datos()

    page.title = "Agendamiento de Citas Médicas - Paciente"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 900
    page.window_height = 600
    page.window_resizable = True
    page.padding = 20

    # 1) OBTENER DATOS DEL USUARIO (se espera foto como séptimo valor)
    user_data = obtener_usuario(user_id)
    if user_data:
        if len(user_data) == 7:
            nombres, apellidos, email, telefono, cedula, tipo_usuario, photo = user_data
        else:
            nombres, apellidos, email, telefono, cedula, tipo_usuario = user_data
            photo = None
        primer_nombre = nombres.split()[0]
        primer_apellido = apellidos.split()[0]
    else:
        nombres = apellidos = email = telefono = cedula = ""
        tipo_usuario = "Paciente"
        primer_nombre = "Usuario"
        primer_apellido = ""
        photo = None

    now = dt.now()
    bienvenida = ft.Text(
        f"Bienvenido, {primer_nombre} {primer_apellido}\n{now.strftime('%d/%m/%Y %H:%M')}",
        size=18,
        weight=ft.FontWeight.BOLD,
        color="#0D47A1",
        text_align=ft.TextAlign.CENTER
    )

    # 2) FUNCIONES DE DIÁLOGOS COMUNES
    def close_dialog(dlg: ft.AlertDialog):
        dlg.open = False
        page.update()

    # 3) DIÁLOGOS DE CONFIGURACIÓN
    def cambiar_contrasena_dialog(_):
        current_pw = ft.TextField(label="Contraseña Actual", password=True, can_reveal_password=True)
        new_pw = ft.TextField(label="Contraseña Nueva", password=True, can_reveal_password=True)
        conf_pw = ft.TextField(label="Confirmar Contraseña", password=True, can_reveal_password=True)
        msg = ft.Text(color="red")

        req_length  = ft.Text("● Mínimo 8 caracteres", color="red", size=12)
        req_upper   = ft.Text("● Al menos 1 mayúscula", color="red", size=12)
        req_digit   = ft.Text("● Al menos 1 dígito", color="red", size=12)
        req_special = ft.Text("● Al menos 1 símbolo (@$!%*?&)", color="red", size=12)

        password_requirements = ft.Column(
            [
                ft.Text("Requisitos de la nueva contraseña:", weight=ft.FontWeight.BOLD, size=13),
                req_length,
                req_upper,
                req_digit,
                req_special
            ],
            spacing=2
        )

        def update_newpw_requirements(_):
            pw = new_pw.value or ""
            req_length.color  = "green" if len(pw) >= 8 else "red"
            req_upper.color   = "green" if any(c.isupper() for c in pw) else "red"
            req_digit.color   = "green" if any(c.isdigit() for c in pw) else "red"
            req_special.color = "green" if any(c in "@$!%*?&" for c in pw) else "red"
            page.update()

        new_pw.on_change = update_newpw_requirements

        def intentar_cambiar():
            pw_current = current_pw.value or ""
            pw_new = new_pw.value or ""
            pw_conf = conf_pw.value or ""
            if not pw_current or not pw_new or not pw_conf:
                msg.value = "Todos los campos son obligatorios."
                page.update()
                return
            if pw_new == pw_current:
                msg.value = "La contraseña nueva no puede ser la misma que la actual."
                page.update()
                return

            import re
            if not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$', pw_new):
                msg.value = "La nueva contraseña no cumple los requisitos."
                page.update()
                return

            if pw_new != pw_conf:
                msg.value = "La confirmación no coincide."
                page.update()
                return

            ok, respuesta = cambiar_contrasena(user_id, pw_current, pw_new)
            if ok:
                page.snack_bar = ft.SnackBar(ft.Text(respuesta, color="white"), bgcolor="green")
                dialog.open = False
            else:
                msg.value = respuesta
                page.snack_bar = ft.SnackBar(ft.Text("Error al cambiar la contraseña", color="white"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

        def confirmar_cambio(_):
            intentar_cambiar()

        def close_dialog_btn(_):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cambiar Contraseña"),
            content=ft.Column([current_pw, new_pw, conf_pw, password_requirements, msg], tight=True),
            actions=[ft.TextButton("Cancelar", on_click=close_dialog_btn),
                     ft.ElevatedButton("Guardar", on_click=confirmar_cambio)],
            actions_alignment="end"
        )

        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def actualizar_datos_dialog(_):
        nombres_field = ft.TextField(label="Nombres", value=nombres)
        apellidos_field = ft.TextField(label="Apellidos", value=apellidos)
        email_field = ft.TextField(label="Correo", value=email)
        telefono_field = ft.TextField(label="Teléfono (10 dígitos)", value=telefono)
        msg = ft.Text(color="red")

        def intentar_actualizar():
            n = nombres_field.value.strip()
            a = apellidos_field.value.strip()
            em = email_field.value.strip()
            tel = telefono_field.value.strip()
            if not n or not a or not em or not tel:
                msg.value = "Ningún campo puede quedar vacío."
                page.update()
                return
            ok, respuesta = actualizar_datos_usuario(user_id, n, a, em, tel)
            if ok:
                page.snack_bar = ft.SnackBar(ft.Text(respuesta, color="white"), bgcolor="green")
                dialog.open = False
                nonlocal nombres, apellidos, email, telefono, primer_nombre, primer_apellido
                nombres = n
                apellidos = a
                email = em
                telefono = tel
                primer_nombre = n.split()[0]
                primer_apellido = a.split()[0]
                bienvenida.value = f"Bienvenido, {primer_nombre} {primer_apellido}\n{dt.now().strftime('%d/%m/%Y %H:%M')}"
            else:
                msg.value = respuesta
            page.snack_bar.open = True
            page.update()

        def confirmar_actualizacion(_):
            intentar_actualizar()

        def close_dialog_btn(_):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Actualizar Datos"),
            content=ft.Column([nombres_field, apellidos_field, email_field, telefono_field, msg], tight=True),
            actions=[ft.TextButton("Cancelar", on_click=close_dialog_btn),
                     ft.ElevatedButton("Guardar", on_click=confirmar_actualizacion)],
            actions_alignment="end"
        )

        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def cerrar_sesion_dialog(_):
        def do_cerrar_sesion(_2):
            dialog.open = False
            page.update()
            page.clean()
            import login_flet
            login_flet.main(page)
        def cancel_cerrar(_2):
            dialog.open = False
            page.update()
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cerrar Sesión"),
            content=ft.Text("¿Está seguro que desea cerrar sesión?"),
            actions=[ft.TextButton("No", on_click=cancel_cerrar),
                     ft.ElevatedButton("Sí", on_click=do_cerrar_sesion, bgcolor="red", color="white")],
            actions_alignment="end"
        )
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()

    # Menú de configuración con avatar circular (foto o ícono por defecto)
    def abrir_config_dialog(_):
        def btn_cambiar_contrasena(_2):
            config_dialog.open = False
            page.update()
            cambiar_contrasena_dialog(_2)
        def btn_actualizar_datos(_2):
            config_dialog.open = False
            page.update()
            actualizar_datos_dialog(_2)
        def btn_cerrar_sesion(_2):
            config_dialog.open = False
            page.update()
            cerrar_sesion_dialog(_2)
        def btn_cancelar(_2):
            config_dialog.open = False
            page.update()
        avatar = ft.Container(
            content=ft.Image(
                src_base64=photo, 
                width=80, 
                height=80, 
                fit=ft.ImageFit.COVER
            ) if photo else ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=80),
            border_radius=40,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            alignment=ft.alignment.center
        )
        content = ft.Column(
            controls=[
                avatar,
                ft.Divider(),
                ft.ElevatedButton("🔒 Cambiar Contraseña", on_click=btn_cambiar_contrasena),
                ft.ElevatedButton("✏️ Actualizar Datos", on_click=btn_actualizar_datos),
                ft.ElevatedButton("🚪 Cerrar Sesión", on_click=btn_cerrar_sesion)
            ],
            tight=True,
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER
        )
        config_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Configuración"),
            content=content,
            actions=[ft.TextButton("Cerrar", on_click=btn_cancelar)],
            actions_alignment="end"
        )
        if config_dialog not in page.overlay:
            page.overlay.append(config_dialog)
        config_dialog.open = True
        page.update()

    # 4) FUNCIONES DE NOTIFICACIONES
    def show_notifications(e):
        import notificaciones_paciente
        notificaciones_paciente.generar_notificaciones(user_id)
        notifs = notificaciones_paciente.obtener_notificaciones(user_id)
        notif_controls = []
        if not notifs:
            notif_controls.append(ft.Text("No hay notificaciones."))
        else:
            for notif in notifs:
                notif_id = notif["id"]
                def mark_read(e, notif_id=notif_id):
                    notificaciones_paciente.marcar_notificacion_leida(notif_id)
                    show_notifications(e)
                def delete_notif(e, notif_id=notif_id):
                    notificaciones_paciente.eliminar_notificacion(notif_id)
                    show_notifications(e)
                row = ft.Row(
                    controls=[
                        ft.Text(notif["message"], expand=True),
                        ft.IconButton(icon=ft.icons.CHECK, tooltip="Marcar como leído", on_click=mark_read, icon_color="green"),
                        ft.IconButton(icon=ft.icons.DELETE, tooltip="Eliminar notificación", on_click=delete_notif, icon_color="red")
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                )
                notif_controls.append(row)
        def close_notif_dialog(e):
            notif_dialog.open = False
            page.update()
        notif_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Notificaciones"),
            content=ft.Container(
                content=ft.Column(notif_controls, spacing=10, scroll=ft.ScrollMode.AUTO),
                height=300
            ),
            actions=[ft.TextButton("Cerrar", on_click=close_notif_dialog)],
            actions_alignment="end"
        )
        if notif_dialog not in page.overlay:
            page.overlay.append(notif_dialog)
        notif_dialog.open = True
        page.update()

    def update_notification_badge():
        import notificaciones_paciente
        notificaciones_paciente.generar_notificaciones(user_id)
        notifs = notificaciones_paciente.obtener_notificaciones(user_id)
        count = len([n for n in notifs if n["leido"] == 0])
        badge_text = str(count) if count > 0 else ""
        badge_container.content.value = badge_text
        badge_container.visible = True if count > 0 else False
        page.update()
    import threading
    def periodic_update():
        update_notification_badge()
        threading.Timer(10, periodic_update).start()  # Actualiza cada 10 segundos

    # 5) ÍCONOS DE CAMPANITA Y CONFIGURACIÓN (CABECERA)
    bell_icon_button = ft.IconButton(
        icon=ft.icons.NOTIFICATIONS,
        tooltip="Notificaciones",
        on_click=show_notifications,
        icon_color="blue"
    )
    badge_container = ft.Container(
        content=ft.Text("", color="white", size=10),
        bgcolor="red",
        border_radius=10,
        padding=ft.Padding(2, 2, 2, 2),
        alignment=ft.alignment.center,
        visible=False,
        width=20,
        height=20
    )
    bell_stack = ft.Stack(
        controls=[
            bell_icon_button,
            ft.Container(content=badge_container, alignment=ft.alignment.top_right)
        ]
    )
    update_notification_badge()

    menu_config_btn = ft.IconButton(
        icon=ft.icons.SETTINGS,
        tooltip="Configuración",
        on_click=abrir_config_dialog,
        icon_color="blue"
    )

    # 6) BLOQUE SUPERIOR: BIENVENIDA + ÍCONOS
    bloque_1 = ft.Container(
        content=ft.Row(
            controls=[
                bienvenida,
                ft.Row(controls=[bell_stack, menu_config_btn], spacing=10)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        padding=15,
        border=ft.border.all(1, "#aaa"),
        border_radius=10,
        bgcolor="#E3F2FD"
    )

    # 7) BLOQUE 2: PANEL DE AGENDAMIENTO DE CITA
    especialidades = [
        (1, "Medicina General"),
        (2, "Medicina Familiar"),
        (3, "Odontología"),
        (4, "Obstetricia"),
        (5, "Ginecología")
    ]
    especialidad_dropdown = ft.Dropdown(
        label="Especialidad",
        options=[ft.dropdown.Option(text=esp[1], key=str(esp[0])) for esp in especialidades],
        expand=True
    )
    medico_dropdown = ft.Dropdown(label="Médico", options=[], expand=True)
    hora_dropdown = ft.Dropdown(label="Seleccione una hora", options=[], expand=True)

    date_picker = ft.DatePicker(first_date=date.today())

    def on_date_selected(_):
        if date_picker.value:
            fecha_picker_btn.text = f"Fecha: {date_picker.value.strftime('%d/%m/%Y')}"
        page.update()

    date_picker.on_change = on_date_selected

    def open_date_picker(_):
        date_picker.open = True
        page.update()

    fecha_picker_btn = ft.ElevatedButton("Seleccionar Fecha", on_click=open_date_picker)

    def agendar_cita(_):
        if (not especialidad_dropdown.value or 
            not medico_dropdown.value or
            date_picker.value is None or
            not hora_dropdown.value):
            page.snack_bar = ft.SnackBar(ft.Text("Complete todos los campos", color="white"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return
        selected_date = date_picker.value
        if selected_date == date.today():
            now_time = dt.now().time()
            selected_time = dt.strptime(hora_dropdown.value, "%H:%M").time()
            if selected_time < now_time:
                page.snack_bar = ft.SnackBar(ft.Text("No se puede agendar una cita en horas pasadas", color="white"), bgcolor="red")
                page.snack_bar.open = True
                page.update()
                return
        def do_agendar():
            paciente_id = user_id
            med_id = int(medico_dropdown.value)
            fecha = selected_date.strftime("%Y-%m-%d")
            hora = hora_dropdown.value
            resultado, mensaje = registrar_cita(paciente_id, med_id, fecha, hora)
            if resultado:
                page.snack_bar = ft.SnackBar(ft.Text("¡Cita agendada con éxito! ✅", color="white"), bgcolor="green")
            else:
                page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="white"), bgcolor="red")
            page.snack_bar.open = True
            actualizar_horas(None)
            bloque_3_refrescar_calendario()
            page.update()
        def on_confirm_agendar():
            do_agendar()
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Agendamiento"),
            content=ft.Text("¿Está seguro que desea agendar esta cita?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: close_dialog(dialog)),
                ft.ElevatedButton("Agendar", on_click=lambda _: [close_dialog(dialog), on_confirm_agendar()], bgcolor="blue", color="white")
            ],
            actions_alignment="end"
        )
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()

    botones_accion = ft.Row(
        controls=[
            ft.ElevatedButton("Agendar", on_click=agendar_cita, bgcolor="#1976D2", color="white"),
            ft.OutlinedButton("Cancelar"),
            ft.OutlinedButton("Limpiar")
        ],
        spacing=10
    )

    bloque_2 = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Seleccione una especialidad:", size=14, weight=ft.FontWeight.BOLD),
                especialidad_dropdown,
                ft.Text("Seleccione un médico:", size=14, weight=ft.FontWeight.BOLD),
                medico_dropdown,
                ft.Text("Seleccione la fecha de la cita:", size=14, weight=ft.FontWeight.BOLD),
                fecha_picker_btn,
                ft.Text("Seleccione la hora disponible:", size=14, weight=ft.FontWeight.BOLD),
                hora_dropdown,
                botones_accion
            ],
            spacing=10
        ),
        padding=15,
        border=ft.border.all(1, "#aaa"),
        border_radius=10,
        bgcolor="#FFF3E0",
        width=350
    )

    # 8) FUNCIÓN PARA EDITAR CITA (CAMBIAR FECHA Y HORA)
    def editar_cita_dialog(cita_info):
        msg_edit = ft.Text("", color="red")
        edit_date_picker = ft.DatePicker(value=cita_info["fecha"], first_date=date.today())
        selected_date_text = ft.Text(value=cita_info["fecha"].strftime("%d/%m/%Y"), size=14)
        def open_edit_date_picker(_):
            edit_date_picker.open = True
            page.update()
        select_date_btn = ft.ElevatedButton("Seleccionar nueva fecha", on_click=open_edit_date_picker)
        def update_edit_horas(_):
            if not edit_date_picker.value:
                return
            med_id = cita_info["medico_id"]
            fecha_str = edit_date_picker.value.strftime("%Y-%m-%d")
            generar_horarios_disponibles(med_id, fecha_str)
            horarios = obtener_horarios_disponibles(med_id, fecha_str)
            if edit_date_picker.value == date.today():
                now_time = dt.now().time()
                horarios = [h for h in horarios if dt.strptime(h[1], "%H:%M").time() > now_time]
            new_time_dropdown.options = [ft.dropdown.Option(text=h[1], key=h[1]) for h in horarios]
            if any(h[1] == cita_info["hora"] for h in horarios):
                new_time_dropdown.value = cita_info["hora"]
            else:
                new_time_dropdown.value = None
            page.update()
        edit_date_picker.on_change = lambda e: (
            selected_date_text.__setattr__("value", edit_date_picker.value.strftime("%d/%m/%Y")),
            update_edit_horas(e),
            page.update()
        )
        new_time_dropdown = ft.Dropdown(label="Seleccione la hora disponible", options=[], expand=True)
        update_edit_horas(None)
        def guardar_edicion(_):
            if not edit_date_picker.value or not new_time_dropdown.value:
                msg_edit.value = "Debe seleccionar fecha y hora."
                page.update()
                return
            new_fecha_str = edit_date_picker.value.strftime("%Y-%m-%d")
            cita_id = cita_info["cita_id"]
            ok, res = editar_cita(cita_id, new_fecha_str, new_time_dropdown.value)
            if ok:
                page.snack_bar = ft.SnackBar(ft.Text(res, color="white"), bgcolor="green")
                edit_dialog.open = False
                bloque_3_refrescar_calendario()
            else:
                msg_edit.value = res
            page.snack_bar.open = True
            page.update()
        edit_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar Cita"),
            content=ft.Column([
                ft.Text("Seleccione nueva fecha:", size=14, weight=ft.FontWeight.BOLD),
                ft.Row([select_date_btn, selected_date_text], spacing=10),
                ft.Text("Seleccione nueva hora:", size=14, weight=ft.FontWeight.BOLD),
                new_time_dropdown,
                msg_edit
            ], spacing=10),
            actions=[ft.TextButton("Cancelar", on_click=lambda _: close_dialog(edit_dialog)),
                     ft.ElevatedButton("Guardar Cambios", on_click=guardar_edicion, bgcolor="blue", color="white")],
            actions_alignment="end"
        )
        if edit_dialog not in page.overlay:
            page.overlay.append(edit_dialog)
        edit_dialog.open = True
        if edit_date_picker not in page.overlay:
            page.overlay.append(edit_date_picker)
        page.update()

    # 9) BLOQUE 3: CALENDARIO DE CITAS
    today = date.today()
    current_year = today.year
    current_month = today.month
    def bloque_3_refrescar_calendario():
        nuevo_cal = crear_calendario(current_year, current_month)
        bloque_3.content.controls[1] = nuevo_cal
        page.update()
    def anterior_mes(_):
        nonlocal current_year, current_month
        current_month -= 1
        if current_month < 1:
            current_month = 12
            current_year -= 1
        bloque_3_refrescar_calendario()
    def siguiente_mes(_):
        nonlocal current_year, current_month
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
        bloque_3_refrescar_calendario()
    def crear_calendario(year: int, month: int) -> ft.Column:
        citas_paciente = obtener_citas_paciente(user_id)
        citas_dict = {}
        for c in citas_paciente:
            cita_id, fecha_str, especialidad, medico, hora, medico_id = c
            cita_date = dt.strptime(fecha_str, "%Y-%m-%d").date()
            if cita_date.year == year and cita_date.month == month:
                citas_dict.setdefault(cita_date.day, []).append({
                    "cita_id": cita_id,
                    "especialidad": especialidad,
                    "medico": medico,
                    "fecha": cita_date,
                    "hora": hora,
                    "medico_id": medico_id
                })
        dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        header = [ft.Container(content=ft.Text(d, weight="bold", size=12), alignment=ft.alignment.center, width=40, height=40) for d in dias_semana]
        cells = []
        first_weekday, num_days = calendar.monthrange(year, month)
        for _ in range(first_weekday):
            cells.append(ft.Container(width=40, height=40))
        for day in range(1, num_days + 1):
            bg_color = "#a5d6a7" if day in citas_dict else "white"
            def on_click_dia(selected_day=day):
                def _handle_click(_):
                    if selected_day not in citas_dict:
                        return
                    citas_del_dia = citas_dict[selected_day]
                    filas_citas = []
                    for cita_info in citas_del_dia:
                        detalle_str = f"Especialidad: {cita_info['especialidad']}\nMédico: {cita_info['medico']}\nFecha: {cita_info['fecha'].strftime('%d/%m/%Y')}\nHora: {cita_info['hora']}"
                        def on_cancel_btn(ci=cita_info):
                            def _cancel(_2):
                                def do_cancel():
                                    fecha_str = ci['fecha'].strftime("%Y-%m-%d")
                                    ok, mensaje = cancelar_cita(user_id, ci["medico_id"], fecha_str, ci["hora"])
                                    if ok:
                                        page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="white"), bgcolor="green")
                                    else:
                                        page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="white"), bgcolor="red")
                                    page.snack_bar.open = True
                                    detalle_dialog.open = False
                                    bloque_3_refrescar_calendario()
                                    page.update()
                                confirm_dialog = ft.AlertDialog(
                                    modal=True,
                                    title=ft.Text("Cancelar Cita"),
                                    content=ft.Text(f"¿Está seguro que desea cancelar esta cita de las {ci['hora']}?"),
                                    actions=[ft.TextButton("No", on_click=lambda _: close_dialog(confirm_dialog)),
                                             ft.ElevatedButton("Sí", on_click=lambda _: [close_dialog(confirm_dialog), do_cancel()], bgcolor="red", color="white")],
                                    actions_alignment="end"
                                )
                                if confirm_dialog not in page.overlay:
                                    page.overlay.append(confirm_dialog)
                                confirm_dialog.open = True
                                page.update()
                            return _cancel
                        def on_edit_btn(ci=cita_info):
                            def _edit(_):
                                editar_cita_dialog(ci)
                            return _edit
                        buttons_row = ft.Row(
                            controls=[
                                ft.ElevatedButton("Editar", on_click=on_edit_btn(cita_info), bgcolor="blue", color="white"),
                                ft.ElevatedButton("Cancelar", on_click=on_cancel_btn(cita_info), bgcolor="red", color="white")
                            ],
                            spacing=5
                        )
                        cita_container = ft.Container(
                            content=ft.Column([ft.Text(detalle_str, size=13), buttons_row], spacing=5, width=240),
                            padding=5,
                            bgcolor="#EEEEEE",
                            border_radius=5
                        )
                        filas_citas.append(cita_container)
                    def cerrar_dialogo(_2):
                        detalle_dialog.open = False
                        page.update()
                    detalle_dialog = ft.AlertDialog(
                        modal=True,
                        title=ft.Text(f"Citas del {selected_day}/{month}/{year}"),
                        content=ft.Container(content=ft.ListView(controls=filas_citas, spacing=10), height=300),
                        actions=[ft.TextButton("Cerrar", on_click=cerrar_dialogo)],
                        actions_alignment="end"
                    )
                    if detalle_dialog not in page.overlay:
                        page.overlay.append(detalle_dialog)
                    detalle_dialog.open = True
                    page.update()
                return _handle_click
            cell = ft.ElevatedButton(
                text=str(day),
                on_click=on_click_dia(day),
                width=40,
                height=40,
                bgcolor=bg_color
            )
            cells.append(cell)
        while len(cells) % 7 != 0:
            cells.append(ft.Container(width=40, height=40))
        grid = ft.GridView(expand=True, runs_count=7, spacing=5, run_spacing=5, controls=header + cells)
        month_name = calendar.month_name[month]
        nav_row = ft.Row([
            ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=anterior_mes),
            ft.Text(f"{month_name} {year}", size=16, weight=ft.FontWeight.BOLD),
            ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=siguiente_mes)
        ], alignment=ft.MainAxisAlignment.CENTER)
        return ft.Column([nav_row, ft.Container(content=grid, width=350, height=350, alignment=ft.alignment.center, padding=10, border=ft.border.all(1, "#aaa"), border_radius=10, bgcolor="#FFFDE7")], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    calendario_widget = crear_calendario(current_year, current_month)
    bloque_3 = ft.Container(
        content=ft.Column([ft.Text("Calendario de Citas", size=20, weight=ft.FontWeight.BOLD, color="#1B5E20"), calendario_widget],
                          alignment="center", horizontal_alignment="center", spacing=10, expand=True),
        padding=15,
        border=ft.border.all(1, "#aaa"),
        border_radius=10,
        bgcolor="#E8F5E9",
        expand=True
    )
    layout = ft.Column([bloque_1, ft.Row([bloque_2, bloque_3], spacing=15, expand=True)], spacing=20, expand=True)
    page.add(layout)
    page.overlay.append(date_picker)
    page.update()

    def actualizar_medicos(_):
        if not especialidad_dropdown.value:
            return
        esp_id = int(especialidad_dropdown.value)
        medicos = obtener_medicos(esp_id)
        medico_dropdown.options = [ft.dropdown.Option(text=m[1], key=str(m[0])) for m in medicos]
        medico_dropdown.value = None
        page.update()
    especialidad_dropdown.on_change = actualizar_medicos

    def actualizar_horas(_):
        if not medico_dropdown.value or date_picker.value is None:
            return
        med_id = int(medico_dropdown.value)
        fecha_str = date_picker.value.strftime("%Y-%m-%d")
        generar_horarios_disponibles(med_id, fecha_str)
        horarios = obtener_horarios_disponibles(med_id, fecha_str)
        if date_picker.value == date.today():
            now_time = dt.now().time()
            horarios = [h for h in horarios if dt.strptime(h[1], "%H:%M").time() > now_time]
        hora_dropdown.options = [ft.dropdown.Option(text=h[1], key=h[1]) for h in horarios]
        hora_dropdown.value = None
        page.update()
    def on_date_change(_):
        on_date_selected(_)
        actualizar_horas(_)
    periodic_update()

    date_picker.on_change = on_date_change
    medico_dropdown.on_change = actualizar_horas
