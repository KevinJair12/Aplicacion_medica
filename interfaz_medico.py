import flet as ft
import datetime
from datetime import date, datetime as dt, timedelta
import calendar

from bd_medica import (
    crear_base_de_datos,
    obtener_todas_citas,
    registrar_cita_admin,
    editar_cita,
    cambiar_contrasena,
    actualizar_datos_usuario,
    obtener_medico_id_por_usuario_id,
    cancelar_cita_por_id,
    atender_cita,
    obtener_usuario
)

def main(page: ft.Page, admin_id: int):
    # Asegurarse de que la base de datos y las tablas existan
    crear_base_de_datos()

    # Se obtiene el id del médico correspondiente al administrador logueado.
    medico_id = obtener_medico_id_por_usuario_id(admin_id)
    # Se obtiene la información del usuario (administrador) para mostrar nombre y foto.
    user_data = obtener_usuario(admin_id)
    if user_data:
        if len(user_data) == 7:
            nombres, apellidos, email, telefono, cedula, tipo_usuario, photo = user_data
        else:
            nombres, apellidos, email, telefono, cedula, tipo_usuario = user_data
            photo = None
        nombre_admin = f"{nombres.split()[0]} {apellidos.split()[0]}"
    else:
        nombre_admin = "Administrador"
        photo = None

    page.title = "Panel de Administrador - Citas Médicas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 950
    page.window_height = 700
    page.window_resizable = True
    page.padding = 20

    # ----------------- DIÁLOGOS Y UTILIDADES -----------------
    def dialog_confirmacion(titulo: str, mensaje: str, on_confirm: callable):
        def do_confirm(e):
            d.open = False
            page.update()
            on_confirm()
        def do_cancel(e):
            d.open = False
            page.update()
        d = ft.AlertDialog(
            modal=True,
            title=ft.Text(titulo),
            content=ft.Text(mensaje),
            actions=[
                ft.TextButton("Cancelar", on_click=do_cancel),
                ft.ElevatedButton("Sí", on_click=do_confirm, bgcolor="blue", color="white")
            ],
            actions_alignment="end",
        )
        if d not in page.overlay:
            page.overlay.append(d)
        d.open = True
        page.update()

    def cerrar_sesion(e):
        page.clean()
        import login_flet
        login_flet.main(page)

    # --------------- CONFIGURACIÓN (DIÁLOGOS) -----------------
    def cambiar_contrasena_dialog(e):
        current_pw = ft.TextField(label="Contraseña Actual", password=True, can_reveal_password=True)
        new_pw = ft.TextField(label="Contraseña Nueva", password=True, can_reveal_password=True)
        conf_pw = ft.TextField(label="Confirmar Contraseña", password=True, can_reveal_password=True)
        msg = ft.Text(color="red")
        req_length  = ft.Text("● Mínimo 8 caracteres", color="red")
        req_upper   = ft.Text("● Al menos 1 mayúscula", color="red")
        req_digit   = ft.Text("● Al menos 1 dígito", color="red")
        req_special = ft.Text("● Al menos 1 símbolo (@$!%*?&)", color="red")
        requisitos_col = ft.Column([
            ft.Text("Requisitos de la nueva contraseña:", weight=ft.FontWeight.BOLD),
            req_length, req_upper, req_digit, req_special
        ], spacing=5)
        def on_newpw_change(e2):
            pw = new_pw.value or ""
            req_length.color  = "green" if len(pw) >= 8 else "red"
            req_upper.color   = "green" if any(c.isupper() for c in pw) else "red"
            req_digit.color   = "green" if any(c.isdigit() for c in pw) else "red"
            req_special.color = "green" if any(c in "@$!%*?&" for c in pw) else "red"
            page.update()
        new_pw.on_change = on_newpw_change
        def do_change():
            pw_curr = current_pw.value.strip()
            pw_new = new_pw.value.strip()
            pw_conf = conf_pw.value.strip()
            if not pw_curr or not pw_new or not pw_conf:
                msg.value = "Todos los campos son obligatorios."
                page.update()
                return
            if pw_new == pw_curr:
                msg.value = "La contraseña nueva no puede ser igual a la actual."
                page.update()
                return
            import re
            if not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$', pw_new):
                msg.value = "La nueva contraseña no cumple los requisitos."
                page.update()
                return
            if pw_new != pw_conf:
                msg.value = "Las contraseñas no coinciden."
                page.update()
                return
            ok, mensaje = cambiar_contrasena(admin_id, pw_curr, pw_new)
            if ok:
                page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="white"), bgcolor="green")
                dialog.open = False
            else:
                msg.value = mensaje
                page.snack_bar = ft.SnackBar(ft.Text("Error al cambiar la contraseña", color="white"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
        def confirmar_cambio(e2):
            def on_confirm():
                do_change()
            dialog_confirmacion("Cambiar Contraseña", "¿Está seguro que desea cambiar la contraseña?", on_confirm)
        def close_dialog(e2):
            dialog.open = False
            page.update()
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cambiar Contraseña"),
            content=ft.Column([current_pw, new_pw, conf_pw, requisitos_col, msg], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.ElevatedButton("Guardar", on_click=confirmar_cambio)
            ],
            actions_alignment="end"
        )
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def actualizar_datos_dialog(e):
        nombres_tf = ft.TextField(label="Nombres", value="")
        apellidos_tf = ft.TextField(label="Apellidos", value="")
        email_tf = ft.TextField(label="Correo", value="")
        tel_tf = ft.TextField(label="Teléfono (10 dígitos)", value="")
        msg = ft.Text(color="red")
        def do_update():
            n = nombres_tf.value.strip()
            a = apellidos_tf.value.strip()
            em = email_tf.value.strip()
            t = tel_tf.value.strip()
            if not n or not a or not em or not t:
                msg.value = "Ningún campo puede quedar vacío."
                page.update()
                return
            ok, texto = actualizar_datos_usuario(admin_id, n, a, em, t)
            if ok:
                page.snack_bar = ft.SnackBar(ft.Text(texto, color="white"), bgcolor="green")
                dial.open = False
            else:
                msg.value = texto
            page.snack_bar.open = True
            page.update()
        def confirmar_update(e2):
            def on_confirm():
                do_update()
            dialog_confirmacion("Actualizar Datos", "¿Desea actualizar los datos?", on_confirm)
        def close_dialog(e2):
            dial.open = False
            page.update()
        dial = ft.AlertDialog(
            modal=True,
            title=ft.Text("Actualizar Datos"),
            content=ft.Column([nombres_tf, apellidos_tf, email_tf, tel_tf, msg], spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.ElevatedButton("Guardar", on_click=confirmar_update)
            ],
            actions_alignment="end"
        )
        if dial not in page.overlay:
            page.overlay.append(dial)
        dial.open = True
        page.update()

    def cerrar_sesion_dialog(e):
        def do_cerrar_sesion(e2):
            dialog.open = False
            page.update()
            page.clean()
            import login_flet
            login_flet.main(page)
        def do_cancel(e2):
            dialog.open = False
            page.update()
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cerrar Sesión"),
            content=ft.Text("¿Está seguro que desea cerrar sesión?"),
            actions=[
                ft.TextButton("No", on_click=lambda e: close_dialog(dialog)),
                ft.ElevatedButton("Sí", on_click=lambda e: [close_dialog(dialog), do_cerrar_sesion(None)], bgcolor="red", color="white")
            ],
            actions_alignment="end"
        )
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()

    # Menú de configuración con avatar circular (foto o ícono por defecto)
    def abrir_config_dialog(e):
        def btn_cambiar_contrasena(e2):
            config_dlg.open = False
            page.update()
            cambiar_contrasena_dialog(e2)
        def btn_actualizar_datos(e2):
            config_dlg.open = False
            page.update()
            actualizar_datos_dialog(e2)
        def btn_cerrar_sesion(e2):
            config_dlg.open = False
            page.update()
            cerrar_sesion_dialog(e2)
        def btn_cancelar(e2):
            config_dlg.open = False
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
        config_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Configuración de Administrador"),
            content=content,
            actions=[ft.TextButton("Cerrar", on_click=btn_cancelar)],
            actions_alignment="end"
        )
        if config_dlg not in page.overlay:
            page.overlay.append(config_dlg)
        config_dlg.open = True
        page.update()

    def close_dialog(dlg):
        dlg.open = False
        page.update()

    # --- REINTEGRO de los IconButton (botón de Configuración) ---
    menu_config_btn = ft.IconButton(
        icon=ft.icons.SETTINGS,
        icon_color="blue",
        icon_size=24,
        tooltip="Configuración",
        on_click=abrir_config_dialog
    )

    header_bar = ft.Row(
        [
            ft.Text(f"Bienvenido, {nombre_admin}\n{dt.now().strftime('%d/%m/%Y %H:%M')}",
                    size=20, weight=ft.FontWeight.BOLD, color="#0D47A1", text_align=ft.TextAlign.CENTER),
            ft.Row([
                menu_config_btn,
                ft.ElevatedButton("Cerrar Sesión", icon=ft.icons.LOGOUT, icon_color="white",
                                   bgcolor="red", on_click=cerrar_sesion)
            ])
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # ------------- TAB 1: CITAS ACTIVAS -------------
    filter_date_active = ft.DatePicker(first_date=date(2020, 1, 1))
    filter_search_active = ft.TextField(label="Buscar (Paciente/Médico)")
    btn_refresh_active = ft.IconButton(
        icon=ft.icons.REFRESH,
        icon_color="blue",
        icon_size=20,
        tooltip="Limpiar Filtros",
        on_click=lambda e: [
            setattr(filter_date_active, "value", None),
            setattr(filter_search_active, "value", ""),
            cargar_citas_activas(),
            page.update()
        ]
    )

    citas_data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Fecha")),
            ft.DataColumn(ft.Text("Hora")),
            ft.DataColumn(ft.Text("Paciente")),
            ft.DataColumn(ft.Text("Médico")),
            ft.DataColumn(ft.Text("Estado")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[]
    )

    def cargar_citas_activas():
        citas = obtener_todas_citas(medico_id=medico_id)
        active = [c for c in citas if c[5].strip().lower() == "pendiente"]
        fecha_filter = filter_date_active.value.strftime("%Y-%m-%d") if filter_date_active.value else None
        search_filter = filter_search_active.value.strip().lower() if filter_search_active.value else ""
        filtradas = []
        for c in active:
            _, fecha, hora, paciente, medico, estado = c
            if fecha_filter and fecha != fecha_filter:
                continue
            if search_filter and (search_filter not in paciente.lower() and search_filter not in medico.lower()):
                continue
            filtradas.append(c)
        citas_data_table.rows.clear()
        for c in filtradas:
            c_id, c_fecha, c_hora, c_paciente, c_medico, c_estado = c
            def atender_cita_click(e, cid=c_id):
                def confirmar_atencion(asistencia):
                    def on_confirm():
                        ok, mensaje = atender_cita(cid, asistencia)
                        if ok:
                            page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="white"), bgcolor="green")
                        else:
                            page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="white"), bgcolor="red")
                        page.snack_bar.open = True
                        cargar_citas_activas()
                        cargar_historial()
                        page.update()
                    dialog_confirmacion("Atender Cita", f"¿Está seguro de marcar esta cita como {asistencia}?", on_confirm)
                atencion_dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Atender Cita"),
                    content=ft.Column([
                        ft.ElevatedButton("Presente", on_click=lambda e: confirmar_atencion("Presente")),
                        ft.ElevatedButton("Ausente", on_click=lambda e: confirmar_atencion("Ausente")),
                        ft.TextButton("Cancelar", on_click=lambda e: [setattr(atencion_dlg, "open", False), page.update()])
                    ], spacing=10, tight=True),
                    actions_alignment="end"
                )
                if atencion_dlg not in page.overlay:
                    page.overlay.append(atencion_dlg)
                atencion_dlg.open = True
                page.update()
            def cancelar_cita_click(e, cid=c_id):
                def do_cancel():
                    ok, mensaje = cancelar_cita_por_id(cid)
                    if ok:
                        page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="white"), bgcolor="green")
                    else:
                        page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="white"), bgcolor="red")
                    page.snack_bar.open = True
                    cargar_citas_activas()
                    cargar_historial()
                    page.update()
                dialog_confirmacion("Cancelar Cita", "¿Está seguro de cancelar esta cita?", do_cancel)
            acciones = ft.Row([
                ft.ElevatedButton("Atender", on_click=atender_cita_click, icon=ft.icons.CHECK, icon_color="white", bgcolor="blue", color="white"),
                ft.ElevatedButton("Cancelar", on_click=cancelar_cita_click, icon=ft.icons.DELETE, icon_color="white", bgcolor="red", color="white")
            ], spacing=5)
            row = ft.DataRow(cells=[
                ft.DataCell(ft.Text(c_fecha)),
                ft.DataCell(ft.Text(c_hora)),
                ft.DataCell(ft.Text(c_paciente)),
                ft.DataCell(ft.Text(c_medico)),
                ft.DataCell(ft.Text(c_estado)),
                ft.DataCell(acciones)
            ])
            citas_data_table.rows.append(row)
        page.update()

    # ------------- TAB 2: AGENDAR CITA -------------
    paciente_dropdown = ft.Dropdown(label="Paciente", width=200, options=[])
    medico2_dropdown = ft.Dropdown(label="Médico", width=200, options=[])
    date_picker_agendar = ft.DatePicker(first_date=date.today())
    hora_dropdown_agendar = ft.Dropdown(label="Hora disponible", width=150, options=[])
    msg_agendar = ft.Text(color="red")

    def cargar_pacientes_y_medicos():
        paciente_dropdown.options.clear()
        from bd_medica import obtener_pacientes_de_medico
        pacientes_dropdown_data = obtener_pacientes_de_medico(medico_id)
        for pid, pnombre in pacientes_dropdown_data:
            paciente_dropdown.options.append(ft.dropdown.Option(key=str(pid), text=pnombre))
        paciente_dropdown.value = None
        from bd_medica import obtener_medicos
        med_list = obtener_medicos(usuario_id=admin_id)
        medico2_dropdown.options.clear()
        for m_ in med_list:
            mid, mname = m_
            medico2_dropdown.options.append(ft.dropdown.Option(key=str(mid), text=mname))
        medico2_dropdown.value = None
        page.update()

    cargar_pacientes_y_medicos()

    def actualizar_horas_agendar(e):
        if not medico2_dropdown.value or date_picker_agendar.value is None:
            return
        med_id = int(medico2_dropdown.value)
        fecha_str = date_picker_agendar.value.strftime("%Y-%m-%d")
        from bd_medica import obtener_horarios_disponibles
        horarios = obtener_horarios_disponibles(med_id, fecha_str)
        if not horarios:
            horarios = []
            inicio = dt.strptime("08:00", "%H:%M")
            fin = dt.strptime("17:00", "%H:%M")
            while inicio <= fin:
                hora_str = inicio.strftime("%H:%M")
                if date_picker_agendar.value == date.today():
                    if inicio.time() >= dt.now().time():
                        horarios.append((None, hora_str))
                else:
                    horarios.append((None, hora_str))
                inicio += timedelta(minutes=30)
        hora_dropdown_agendar.options = [ft.dropdown.Option(text=h[1], key=h[1]) for h in horarios]
        hora_dropdown_agendar.value = None
        page.update()

    date_picker_agendar.on_change = lambda e: actualizar_horas_agendar(e)
    medico2_dropdown.on_change = actualizar_horas_agendar

    def agendar_cita_paciente(e):
        if not paciente_dropdown.value or not medico2_dropdown.value or date_picker_agendar.value is None or not hora_dropdown_agendar.value:
            msg_agendar.value = "Complete todos los campos."
            page.update()
            return
        selected_datetime = dt.strptime(f"{date_picker_agendar.value.strftime('%Y-%m-%d')} {hora_dropdown_agendar.value}", "%Y-%m-%d %H:%M")
        if selected_datetime < dt.now():
            msg_agendar.value = "No se puede agendar una cita en el pasado."
            page.update()
            return
        pac_id = int(paciente_dropdown.value)
        med_id = int(medico2_dropdown.value)
        fecha = date_picker_agendar.value.strftime("%Y-%m-%d")
        hora = hora_dropdown_agendar.value
        def do_agendar():
            ok, mensaje = registrar_cita_admin(pac_id, med_id, fecha, hora)
            if ok:
                page.snack_bar = ft.SnackBar(ft.Text(mensaje + " ✅", color="white"), bgcolor="green")
                paciente_dropdown.value = None
                medico2_dropdown.value = None
                date_picker_agendar.value = None
                hora_dropdown_agendar.value = None
                msg_agendar.value = ""
            else:
                page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="white"), bgcolor="red")
            page.snack_bar.open = True
            cargar_citas_activas()
            cargar_historial()  # Actualizar historial al agendar
            page.update()
        dialog_confirmacion("Agendar Cita", "¿Confirmar agendamiento?", do_agendar)

    tab_agendar = ft.Column([
        ft.Text("Agendar una nueva cita para un paciente", size=16, weight="bold"),
        paciente_dropdown,
        medico2_dropdown,
        ft.Row([
            ft.ElevatedButton("Seleccionar Fecha", on_click=lambda e: [setattr(date_picker_agendar, "open", True), page.update()]),
            date_picker_agendar
        ], spacing=10),
        hora_dropdown_agendar,
        msg_agendar,
        ft.ElevatedButton("Agendar", on_click=agendar_cita_paciente, icon=ft.icons.ADD)
    ], spacing=10, expand=True)

    # ------------- TAB 3: HISTORIAL DE CITAS -------------
    def cargar_historial():
        citas = obtener_todas_citas(medico_id=medico_id)
        historial = [c for c in citas if c[5].strip().lower() in ["presente", "ausente", "cancelada"]]
        estado_val = filtro_estado.value.strip() if filtro_estado.value else ""
        estado_filter = estado_val if (estado_val and estado_val.lower() != "todos") else None
        fecha_filter = filtro_datepicker.value.strftime("%Y-%m-%d") if filtro_datepicker.value else None
        busqueda = campo_busqueda.value.strip().lower() if campo_busqueda.value else ""
        resultados = []
        if not estado_filter and not fecha_filter and not busqueda:
            resultados = historial
        else:
            for c in historial:
                _, fecha, hora, paciente, medico, estado = c
                if estado_filter and estado.strip().lower() != estado_filter.lower():
                    continue
                if fecha_filter and fecha != fecha_filter:
                    continue
                if busqueda and (busqueda not in paciente.lower() and busqueda not in medico.lower()):
                    continue
                resultados.append(c)
        historial_data_table.rows.clear()
        for c in resultados:
            c_id, c_fecha, c_hora, c_paciente, c_medico, c_estado = c
            row = ft.DataRow(cells=[
                ft.DataCell(ft.Text(c_fecha)),
                ft.DataCell(ft.Text(c_hora)),
                ft.DataCell(ft.Text(c_paciente)),
                ft.DataCell(ft.Text(c_medico)),
                ft.DataCell(ft.Text(c_estado)),
            ])
            historial_data_table.rows.append(row)
        page.update()

    filtro_estado = ft.Dropdown(
        label="Estado",
        options=[
            ft.dropdown.Option(key="", text="Todos"),
            ft.dropdown.Option(key="Pendiente", text="Pendiente"),
            ft.dropdown.Option(key="Presente", text="Presente"),
            ft.dropdown.Option(key="Ausente", text="Ausente"),
            ft.dropdown.Option(key="Cancelada", text="Cancelada")
        ],
        value=""
    )
    filtro_datepicker = ft.DatePicker(first_date=date(2023, 1, 1))
    campo_busqueda = ft.TextField(label="Buscar por paciente (nombres/apellidos)")
    btn_actualizar = ft.IconButton(
        icon=ft.icons.REFRESH,
        icon_color="blue",
        icon_size=20,
        tooltip="Limpiar Filtros",
        on_click=lambda e: [
            setattr(filtro_estado, "value", ""),
            setattr(filtro_datepicker, "value", None),
            setattr(campo_busqueda, "value", ""),
            cargar_historial(),
            page.update()
        ]
    )
    historial_data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Fecha")),
            ft.DataColumn(ft.Text("Hora")),
            ft.DataColumn(ft.Text("Paciente")),
            ft.DataColumn(ft.Text("Médico")),
            ft.DataColumn(ft.Text("Estado")),
        ],
        rows=[]
    )
    
    scrollable_historial = ft.ListView(
        controls=[historial_data_table],
        height=300,
        expand=False
    )

    def buscar_historial(e):
        cargar_historial()

    filtro_estado.on_change = lambda e: cargar_historial()
    filtro_datepicker.on_change = lambda e: cargar_historial()

    tab_historial = ft.Column([
        ft.Text("Historial de Citas", size=16, weight="bold"),
        ft.Row([
            filtro_estado,
            ft.ElevatedButton("Seleccionar Fecha", on_click=lambda e: [setattr(filtro_datepicker, "open", True), page.update()]),
            filtro_datepicker,
            campo_busqueda,
            ft.ElevatedButton("Buscar", on_click=buscar_historial),
            btn_actualizar
        ], spacing=10),
        scrollable_historial
    ], spacing=10, expand=True)

    scrollable_table = ft.ListView(
        controls=[citas_data_table],
        height=300,
        expand=False
    )

    filter_search_active = ft.TextField(label="Buscar (Paciente/Médico)")

    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Citas Activas", content=ft.Column([
                ft.Row([
                    filter_date_active,
                    filter_search_active,
                    btn_refresh_active
                ], spacing=10),
                scrollable_table
            ])),
            ft.Tab(text="Agendar Cita", content=tab_agendar),
            ft.Tab(text="Historial", content=tab_historial),
        ],
        expand=1,
        on_change=lambda e: cargar_historial() if e.control.selected_index == 2 else None
    )

    layout = ft.Column([
        header_bar,
        ft.Divider(),
        tabs
    ], spacing=10, expand=True)

    page.add(layout)
    cargar_citas_activas()
    cargar_historial()
    page.update()
