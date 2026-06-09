# app.py - Versión para Render con PostgreSQL
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, flash
from models import Torneo
import uuid
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from functools import wraps
from database import init_db, guardar_torneo, cargar_torneos, verificar_usuario, obtener_usuario_por_id, DATABASE_URL

# ==================== CONFIGURACIÓN DE RUTAS ABSOLUTAS ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui_cambiala_para_produccion'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Configurar rutas absolutas para carpetas
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
RESUMENES_FOLDER = os.path.join(BASE_DIR, 'resumenes')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESUMENES_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ==================== FUNCIÓN DE BACKUP AUTOMÁTICO ====================
def crear_backup_automatico():
    """Crea un backup automático de la base de datos antes de operaciones críticas"""
    import shutil
    from datetime import datetime
    
    backup_dir = os.path.join(BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f'torneos_backup_{fecha}.db')
    
    db_path = os.path.join(BASE_DIR, 'torneos.db')
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_file)
        print(f"💾 Backup automático creado: {backup_file}")
        return backup_file
    return None

# Inicializar base de datos
init_db()

# Cargar torneos existentes desde la base de datos
torneos = cargar_torneos()

print(f"📂 Base de datos cargada: {len(torneos)} torneo(s)")
for torneo_id, torneo in torneos.items():
    print(f"   - {torneo.nombre}: {len(torneo.equipos)} equipos")

# ==================== DECORADORES PARA PERMISOS ====================

def login_required(f):
    """Decorador para requerir inicio de sesión"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor inicia sesión para continuar', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorador para requerir rol de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor inicia sesión para continuar', 'warning')
            return redirect(url_for('login'))
        if session.get('rol') != 'admin':
            flash('No tienes permisos para realizar esta acción', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def check_permission(f):
    """Decorador para verificar permisos - los entrenadores solo pueden GET"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401

        # Si es entrenador o invitado y el método no es GET, denegar acceso
        if session.get('rol') in ['entrenador', 'invitado'] and request.method not in ['GET']:
            return jsonify({'error': 'No tienes permisos para modificar datos'}), 403

        return f(*args, **kwargs)
    return decorated_function

def save_torneo(torneo_id):
    """Guarda un torneo específico en la base de datos con verificación"""
    if torneo_id in torneos:
        guardar_torneo(torneos[torneo_id])
        print(f"💾 Torneo '{torneos[torneo_id].nombre}' guardado en BD")
        
        # Verificar que se guardó correctamente (adaptado para PostgreSQL)
        try:
            from database import get_db
            conn = get_db()
            cursor = conn.cursor()
            
            # Usar placeholder correcto según la base de datos
            if DATABASE_URL:
                cursor.execute("SELECT COUNT(*) FROM torneos WHERE id = %s", (torneo_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM torneos WHERE id = ?", (torneo_id,))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 0:
                print(f"   ✅ Verificado: Torneo existe en BD")
            else:
                print(f"   ⚠️ ADVERTENCIA: Torneo no encontrado en BD después de guardar")
        except Exception as e:
            print(f"   ⚠️ Error en verificación: {e}")

# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        usuario = verificar_usuario(username, password)

        if usuario:
            session['usuario_id'] = usuario['id']
            session['username'] = usuario['username']
            session['rol'] = usuario['rol']
            session['nombre'] = usuario['nombre']
            flash(f'✅ Bienvenido {usuario["nombre"]}', 'success')

            # Redirigir según el rol
            if usuario['rol'] == 'admin':
                return redirect(url_for('index'))
            else:
                return redirect(url_for('index_entrenador'))
        else:
            flash('❌ Usuario o contraseña incorrectos', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash('✅ Sesión cerrada correctamente', 'success')
    return redirect(url_for('login'))

# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
def index():
    """Vista principal - redirige al login si no está autenticado"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    if session.get('rol') == 'entrenador' or session.get('rol') == 'invitado':
        return redirect(url_for('index_entrenador'))
    return render_template('index.html', torneos=torneos, rol=session.get('rol'))

@app.route('/index_entrenador')
@login_required
def index_entrenador():
    """Vista para entrenadores (solo lectura)"""
    return render_template('index_entrenador.html', torneos=torneos, rol=session.get('rol'))

@app.route('/registro_equipo/<torneo_id>')
@login_required
def registro_equipo(torneo_id):
    if torneo_id not in torneos:
        return redirect(url_for('index'))
    return render_template('registro_equipo.html', torneo=torneos[torneo_id], torneo_id=torneo_id)

@app.route('/noticias/<torneo_id>')
@login_required
def noticias(torneo_id):
    if torneo_id not in torneos:
        return redirect(url_for('index'))
    return render_template('noticias.html', torneo=torneos[torneo_id], torneo_id=torneo_id)

@app.route('/estadisticas/<torneo_id>')
@login_required
def estadisticas(torneo_id):
    if torneo_id not in torneos:
        return redirect(url_for('index'))
    return render_template('estadisticas.html', torneo=torneos[torneo_id], torneo_id=torneo_id)

@app.route('/resumen_partido/<torneo_id>/<int:partido_id>')
@login_required
def resumen_partido(torneo_id, partido_id):
    if torneo_id not in torneos:
        return redirect(url_for('index'))

    torneo = torneos[torneo_id]
    resumen = torneo.get_resumen_partido(partido_id)

    if not resumen:
        return redirect(url_for('ver_torneo', torneo_id=torneo_id))

    return render_template('resumen_partido.html', torneo_id=torneo_id,
                          resumen=resumen, torneo=torneo)

@app.route('/imprimir_resumen/<torneo_id>/<int:partido_id>')
@login_required
def imprimir_resumen(torneo_id, partido_id):
    """Genera un PDF con el resumen del partido"""
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]
    resumen = torneo.get_resumen_partido(partido_id)

    if not resumen:
        return jsonify({'error': 'Resumen no disponible'}), 404

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0f3460'),
        alignment=1
    )
    story.append(Paragraph(f"Resumen del Partido", title_style))
    story.append(Spacer(1, 0.3*inch))

    partido = resumen['partido']
    story.append(Paragraph(f"{partido['nombre_local']} vs {partido['nombre_visitante']}", styles['Heading2']))

    fecha_mostrar = partido['fecha'] if partido['fecha'] else 'Por definir'
    hora_mostrar = partido['hora'] if partido['hora'] else 'Por definir'
    cancha_mostrar = partido['cancha'] if partido['cancha'] else 'Por definir'

    story.append(Paragraph(f"Fecha: {fecha_mostrar} - Hora: {hora_mostrar}", styles['Normal']))
    story.append(Paragraph(f"Cancha: {cancha_mostrar}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    result_style = ParagraphStyle(
        'ResultStyle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#10b981'),
        alignment=1
    )
    story.append(Paragraph(f"Resultado: {partido['goles_local']} - {partido['goles_visitante']}", result_style))
    story.append(Spacer(1, 0.3*inch))

    if resumen['goleadores']['local'] or resumen['goleadores']['visitante']:
        story.append(Paragraph("Goleadores:", styles['Heading3']))

        data = [['Equipo', 'Jugador', 'Minuto']]
        for gol in resumen['goleadores']['local']:
            data.append([partido['nombre_local'], gol['nombre'], str(gol['minuto'])])
        for gol in resumen['goleadores']['visitante']:
            data.append([partido['nombre_visitante'], gol['nombre'], str(gol['minuto'])])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)

    doc.build(story)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"resumen_{partido_id}.pdf", mimetype='application/pdf')

# ==================== RUTA PARA IMPRIMIR PLANTILLA ====================
@app.route('/imprimir_plantilla/<torneo_id>/<int:equipo_id>')
@login_required
def imprimir_plantilla(torneo_id, equipo_id):
    """Genera un PDF con la lista de jugadoras y cuerpo técnico del equipo"""
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]

    if equipo_id not in torneo.equipos:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    equipo = torneo.equipos[equipo_id]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#0f3460'),
        alignment=1,
        spaceAfter=20
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceAfter=15
    )

    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0f3460'),
        alignment=0,
        spaceAfter=10,
        spaceBefore=20
    )

    story.append(Paragraph(f"PLANTILLA DE JUGADORAS", title_style))
    story.append(Paragraph(f"{equipo.nombre}", subtitle_style))
    story.append(Spacer(1, 0.2*inch))

    # ==================== CUERPO TÉCNICO ====================
    story.append(Paragraph("CUERPO TÉCNICO", section_title_style))

    if len(equipo.cuerpo_tecnico) == 0:
        story.append(Paragraph("No hay miembros registrados en el cuerpo técnico", styles['Normal']))
    else:
        ct_data = [['Rol', 'Nombre', 'Documento', 'Teléfono', 'Email', 'Especialidad']]
        orden_roles = ['Entrenador/a', 'Asistente Técnico', 'Preparador Físico', 'Médico/a', 'Kinesiólogo/a', 'Psicólogo/a', 'Utilero/a', 'Coordinador/a']

        miembros_ordenados = sorted(equipo.cuerpo_tecnico.values(),
                                   key=lambda m: orden_roles.index(m.rol) if m.rol in orden_roles else 999)

        for miembro in miembros_ordenados:
            rol_limpio = miembro.rol
            for char in ['👨‍🏫', '👥', '💪', '🩺', '💆', '🧠', '🧹', '📋', ' ']:
                rol_limpio = rol_limpio.replace(char, '')
            rol_limpio = rol_limpio.strip()

            ct_data.append([
                rol_limpio if rol_limpio else miembro.rol,
                miembro.nombre,
                miembro.documento or '-',
                miembro.telefono or '-',
                miembro.email or '-',
                miembro.especialidad or '-'
            ])

        ct_table = Table(ct_data, repeatRows=1)
        ct_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(ct_table)

    story.append(Spacer(1, 0.3*inch))

    # ==================== JUGADORAS ====================
    story.append(Paragraph("JUGADORAS", section_title_style))

    data = [['#', 'Nombre completo', 'Posición', 'Documento', 'Edad']]
    jugadores_ordenados = sorted(equipo.jugadores.values(), key=lambda j: j.numero)

    for jugador in jugadores_ordenados:
        edad = ''
        if jugador.fecha_nacimiento:
            try:
                nacimiento = datetime.strptime(jugador.fecha_nacimiento, "%Y-%m-%d")
                hoy = datetime.now()
                edad_calculada = hoy.year - nacimiento.year
                if (hoy.month, hoy.day) < (nacimiento.month, nacimiento.day):
                    edad_calculada -= 1
                edad = str(edad_calculada)
            except:
                edad = ''

        data.append([
            str(jugador.numero),
            jugador.nombre,
            jugador.posicion,
            jugador.documento or '-',
            edad or '-'
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.3*inch))

    resumen_data = [
        ['RESUMEN DEL EQUIPO'],
        [f'Total Jugadoras: {len(equipo.jugadores)}'],
        [f'Total Cuerpo Técnico: {len(equipo.cuerpo_tecnico)}'],
        [f'Fecha de emisión: {datetime.now().strftime("%d/%m/%Y %H:%M")}']
    ]

    resumen_table = Table(resumen_data, colWidths=[500])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fdf4')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(resumen_table)

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#94a3b8'),
        alignment=1
    )
    story.append(Paragraph("Documento generado por Sistema de Torneos de Fútbol", footer_style))

    doc.build(story)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"plantilla_{equipo.nombre}.pdf", mimetype='application/pdf')

# ==================== RUTA PARA IMPRIMIR CALENDARIO ====================
@app.route('/imprimir_calendario/<torneo_id>')
@login_required
def imprimir_calendario(torneo_id):
    """Genera un PDF con el calendario completo de todos los partidos del torneo organizado por jornadas"""
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#0f3460'),
        alignment=1,
        spaceAfter=15
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceAfter=25
    )

    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#0f3460'),
        alignment=0,
        spaceAfter=10,
        spaceBefore=15
    )

    story.append(Paragraph(f"CALENDARIO DE JUEGOS", title_style))
    story.append(Paragraph(f"{torneo.nombre}", subtitle_style))

    num_equipos = len(torneo.equipos)
    info_data = [
        ['Categoría:', torneo.categoria],
        ['Fecha de inicio:', torneo.fecha_inicio],
        ['Cantidad de equipos:', str(num_equipos)],
        ['Total de partidos:', str(len(torneo.partidos))],
        ['Formato:', 'Todos contra todos (Una sola ronda)'],
        ['Fecha de emisión:', datetime.now().strftime("%d/%m/%Y %H:%M")]
    ]

    info_table = Table(info_data, colWidths=[150, 350])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0f3460')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#334155')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))

    todos_partidos = list(torneo.partidos.values())
    if num_equipos >= 2:
        partidos_por_jornada = num_equipos // 2
    else:
        partidos_por_jornada = 1

    jornadas = []
    for i in range(0, len(todos_partidos), partidos_por_jornada):
        jornada_partidos = todos_partidos[i:i+partidos_por_jornada]
        if jornada_partidos:
            jornadas.append(jornada_partidos)

    for idx, jornada_partidos in enumerate(jornadas, 1):
        story.append(Paragraph(f"JORNADA {idx}", section_title_style))

        data = [['HORA', 'EQUIPO LOCAL', 'VS', 'EQUIPO VISITANTE', 'CANCHA']]

        for partido in jornada_partidos:
            fecha_mostrar = partido.fecha if partido.fecha else 'Por definir'
            hora_mostrar = partido.hora if partido.hora else 'Por definir'
            cancha_mostrar = partido.cancha if partido.cancha else 'Por definir'
            
            resultado = ""
            if partido.jugado:
                resultado = f" ({partido.goles_local} - {partido.goles_visitante})"

            data.append([
                hora_mostrar,
                f"{partido.nombre_local}{resultado}",
                "vs",
                partido.nombre_visitante,
                cancha_mostrar
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(table)
        story.append(Spacer(1, 0.2*inch))

    resumen_data = [
        ['RESUMEN DEL CALENDARIO'],
        [f'Total de jornadas: {len(jornadas)}'],
        [f'Total de partidos: {len(todos_partidos)}'],
        [f'Partidos jugados: {len([p for p in todos_partidos if p.jugado])}'],
        [f'Partidos pendientes: {len([p for p in todos_partidos if not p.jugado])}']
    ]

    resumen_table = Table(resumen_data, colWidths=[500])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fdf4')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(resumen_table)

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#94a3b8'),
        alignment=1
    )
    story.append(Paragraph("Documento generado por Sistema de Torneos de Fútbol", footer_style))

    doc.build(story)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"calendario_{torneo.nombre}.pdf", mimetype='application/pdf')

@app.route('/torneo/<torneo_id>')
@login_required
def ver_torneo(torneo_id):
    if torneo_id not in torneos:
        return redirect(url_for('index'))
    return render_template('torneo.html', torneo=torneos[torneo_id], torneo_id=torneo_id, rol=session.get('rol'))

@app.route('/torneo_entrenador/<torneo_id>')
@login_required
def ver_torneo_entrenador(torneo_id):
    """Vista de torneo para entrenadores (solo lectura)"""
    if torneo_id not in torneos:
        return redirect(url_for('index_entrenador'))
    return render_template('torneo_entrenador.html', torneo=torneos[torneo_id], torneo_id=torneo_id, rol=session.get('rol'))

# ==================== RUTA PARA INFORME ARBITRAL ====================
@app.route('/informe_arbitral/<torneo_id>/<int:partido_id>')
@login_required
def ver_informe_arbitral(torneo_id, partido_id):
    """Muestra el formulario de informe arbitral"""
    if torneo_id not in torneos:
        return redirect(url_for('index'))

    torneo = torneos[torneo_id]

    if partido_id not in torneo.partidos:
        return redirect(url_for('ver_torneo', torneo_id=torneo_id))

    partido = torneo.partidos[partido_id]
    informe = partido.get_informe_arbitral()

    return render_template('informe_arbitral.html',
                          torneo=torneo,
                          partido=partido,
                          informe=informe,
                          torneo_id=torneo_id)

# ==================== API RUTAS ====================

@app.route('/crear_torneo', methods=['POST'])
@admin_required
def crear_torneo():
    nombre = request.json.get('nombre')
    categoria = request.json.get('categoria', 'Libre')

    if not nombre:
        return jsonify({'error': 'El nombre es requerido'}), 400

    torneo_id = str(uuid.uuid4())[:8]
    torneos[torneo_id] = Torneo(torneo_id, nombre, categoria)
    save_torneo(torneo_id)

    return jsonify({'id': torneo_id, 'nombre': nombre})

# ==================== RUTA PARA ELIMINAR TORNEO ====================

@app.route('/api/torneo/<torneo_id>/eliminar', methods=['DELETE'])
@admin_required
def eliminar_torneo(torneo_id):
    """Elimina un torneo completamente"""
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404
    
    nombre_torneo = torneos[torneo_id].nombre
    
    # Eliminar el torneo del diccionario
    del torneos[torneo_id]
    
    # Guardar los cambios (esto eliminará el torneo de la BD)
    from database import get_db
    conn = get_db()
    cursor = conn.cursor()
    
    # Eliminar de la base de datos PostgreSQL
    if DATABASE_URL:
        cursor.execute("DELETE FROM torneos WHERE id = %s", (torneo_id,))
    else:
        cursor.execute("DELETE FROM torneos WHERE id = ?", (torneo_id,))
    conn.commit()
    conn.close()
    
    print(f"🗑️ Torneo '{nombre_torneo}' (ID: {torneo_id}) eliminado permanentemente")
    
    return jsonify({
        'success': True, 
        'mensaje': f'Torneo "{nombre_torneo}" eliminado correctamente'
    })

# ==================== RUTA PARA LISTAR TORNEOS ====================

@app.route('/api/torneos/listar')
@admin_required
def listar_torneos():
    """Lista todos los torneos con opción de eliminar"""
    lista = []
    for torneo_id, torneo in torneos.items():
        lista.append({
            'id': torneo_id,
            'nombre': torneo.nombre,
            'categoria': torneo.categoria,
            'equipos': len(torneo.equipos),
            'partidos': len(torneo.partidos)
        })
    return jsonify(lista)

@app.route('/api/torneo/<torneo_id>/info')
@login_required
def torneo_info(torneo_id):
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404
    return jsonify(torneos[torneo_id].to_dict())

@app.route('/api/torneo/<torneo_id>/equipos', methods=['GET', 'POST', 'DELETE'])
@login_required
@check_permission
def gestion_equipos(torneo_id):
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]

    if request.method == 'GET':
        equipos = [equipo.to_dict() for equipo in torneo.equipos.values()]
        return jsonify(equipos)

    elif request.method == 'POST':
        data = request.json
        nombre = data.get('nombre', '').strip()
        
        if not nombre:
            return jsonify({'error': 'Nombre requerido'}), 400
        
        # ========== VALIDACIÓN PARA EVITAR ERROR DE INTEGER VACÍO ==========
        # Convertir valores vacíos a None para que PostgreSQL los trate como NULL
        anio_fundacion = data.get('anio_fundacion', '')
        if anio_fundacion == '' or anio_fundacion is None:
            anio_fundacion = None
        else:
            try:
                # Intentar convertir a entero
                anio_fundacion = int(anio_fundacion)
            except (ValueError, TypeError):
                anio_fundacion = None
        
        estadio = data.get('estadio', '')
        if estadio == '':
            estadio = None
        
        entrenador = data.get('entrenador', '')
        if entrenador == '':
            entrenador = None
        # ========== FIN VALIDACIÓN ==========

        if torneo.agregar_equipo(nombre, entrenador, anio_fundacion, estadio):
            save_torneo(torneo_id)
            return jsonify({'success': True, 'mensaje': f'Equipo {nombre} agregado'})
        else:
            return jsonify({'error': 'El equipo ya existe'}), 400

    elif request.method == 'DELETE':
        equipo_id = request.json.get('equipo_id')
        if torneo.eliminar_equipo(equipo_id):
            save_torneo(torneo_id)
            return jsonify({'success': True, 'mensaje': 'Equipo eliminado'})
        else:
            return jsonify({'error': 'Equipo no encontrado'}), 404

# ==================== RUTA PARA AGREGAR JUGADOR POR NOMBRE DE EQUIPO ====================

@app.route('/api/torneo/<torneo_id>/equipo/agregar_jugador_por_nombre', methods=['POST'])
@login_required
@check_permission
def agregar_jugador_por_nombre(torneo_id):
    """Agrega un jugador a un equipo usando el nombre del equipo en lugar del ID"""
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]
    data = request.json

    equipo_nombre = data.get('equipo_nombre', '').strip()

    if not equipo_nombre:
        return jsonify({'error': 'El nombre del equipo es requerido'}), 400

    # Buscar el equipo por nombre (insensible a mayúsculas/minúsculas)
    equipo_encontrado = None
    for equipo in torneo.equipos.values():
        if equipo.nombre.lower() == equipo_nombre.lower():
            equipo_encontrado = equipo
            break

    if not equipo_encontrado:
        # Sugerir equipos similares si no se encuentra
        equipos_similares = [e.nombre for e in torneo.equipos.values()
                            if equipo_nombre.lower() in e.nombre.lower()]

        mensaje = f'Equipo "{equipo_nombre}" no encontrado'
        if equipos_similares:
            mensaje += f'. Equipos disponibles: {", ".join(equipos_similares)}'

        return jsonify({'error': mensaje}), 404

    # Validar datos requeridos
    nombre = data.get('nombre', '').strip()
    numero = data.get('numero')
    posicion = data.get('posicion', '')

    if not nombre:
        return jsonify({'error': 'El nombre del jugador es requerido'}), 400

    if not numero:
        return jsonify({'error': 'El número de camiseta es requerido'}), 400

    # Agregar jugador al equipo encontrado
    if equipo_encontrado.agregar_jugador(
        nombre=nombre,
        numero=int(numero),
        posicion=posicion,
        nombre_abreviado=data.get('nombre_abreviado', ''),
        documento=data.get('documento', ''),
        fecha_nacimiento=data.get('fecha_nacimiento', ''),
        telefono=data.get('telefono', ''),
        email=data.get('email', ''),
        altura=data.get('altura'),
        peso=data.get('peso'),
        pierna_habil=data.get('pierna_habil', '')
    ):
        save_torneo(torneo_id)
        return jsonify({'success': True, 'mensaje': f'✅ Jugador {nombre} agregado al equipo {equipo_encontrado.nombre}'})

    return jsonify({'error': f'El número {numero} ya está en uso en el equipo {equipo_encontrado.nombre}'}), 400

# ==================== RUTAS DE JUGADORES - VERSIÓN CORREGIDA ====================

@app.route('/api/torneo/<torneo_id>/equipo/<int:equipo_id>/jugadores', methods=['GET', 'POST', 'DELETE'])
@login_required
@check_permission
def gestion_jugadores(torneo_id, equipo_id):
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]

    if equipo_id not in torneo.equipos:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    equipo = torneo.equipos[equipo_id]

    if request.method == 'GET':
        return jsonify([j.to_dict() for j in equipo.jugadores.values()])

    elif request.method == 'POST':
        data = request.json
        print(f"📝 === AGREGANDO JUGADOR ===")
        print(f"   Equipo ID: {equipo_id}")
        print(f"   Equipo: {equipo.nombre}")
        print(f"   Nombre: {data.get('nombre')}")
        print(f"   Número: {data.get('numero')}")
        print(f"   Posición: {data.get('posicion')}")
        
        # ========== VALIDACIÓN PARA EVITAR ERRORES DE TIPO EN POSTGRESQL ==========
        # Convertir valores vacíos a None para PostgreSQL
        altura = data.get('altura')
        if altura == '' or altura is None:
            altura = None
        else:
            try:
                altura = float(altura) if altura else None
            except (ValueError, TypeError):
                altura = None
                
        peso = data.get('peso')
        if peso == '' or peso is None:
            peso = None
        else:
            try:
                peso = float(peso) if peso else None
            except (ValueError, TypeError):
                peso = None
        
        # Fecha de nacimiento: si es cadena vacía, convertir a None
        fecha_nacimiento = data.get('fecha_nacimiento', '')
        if fecha_nacimiento == '':
            fecha_nacimiento = None
        
        # Teléfono y email: si son vacíos, convertir a None
        telefono = data.get('telefono', '')
        if telefono == '':
            telefono = None
            
        email = data.get('email', '')
        if email == '':
            email = None
            
        documento = data.get('documento', '')
        if documento == '':
            documento = None
        # ========== FIN VALIDACIÓN ==========
        
        if equipo.agregar_jugador(
            nombre=data['nombre'],
            numero=data['numero'],
            posicion=data['posicion'],
            nombre_abreviado=data.get('nombre_abreviado', ''),
            documento=documento,
            fecha_nacimiento=fecha_nacimiento,
            telefono=telefono,
            email=email,
            altura=altura,
            peso=peso,
            pierna_habil=data.get('pierna_habil', '')
        ):
            print(f"   ✅ Jugador agregado en memoria. Total ahora: {len(equipo.jugadores)}")
            
            # Crear backup antes de guardar
            crear_backup_automatico()
            
            # Guardar en BD
            save_torneo(torneo_id)
            
            # Verificar que se guardó
            from database import get_db
            conn = get_db()
            cursor = conn.cursor()
            if DATABASE_URL:
                cursor.execute("SELECT COUNT(*) FROM jugadores WHERE equipo_id = %s", (equipo_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM jugadores WHERE equipo_id = ?", (equipo_id,))
            count = cursor.fetchone()[0]
            conn.close()
            print(f"   📊 Jugadores en BD después de guardar: {count}")
            
            return jsonify({'success': True, 'mensaje': 'Jugador agregado'})
        else:
            print(f"   ❌ Error: Número {data['numero']} ya existe")
            return jsonify({'error': 'Número de camiseta ya existe'}), 400

    elif request.method == 'DELETE':
        jugador_id = request.json.get('jugador_id')

        # Verificar si existe antes de eliminar
        if jugador_id not in equipo.jugadores:
            return jsonify({'error': 'Jugador no encontrado'}), 404

        # Obtener información para debug
        jugador = equipo.jugadores[jugador_id]
        print(f"🗑️ Eliminando jugador: {jugador.nombre} (ID: {jugador_id}) del equipo {equipo.nombre}")

        # Eliminar de memoria
        if equipo.eliminar_jugador(jugador_id):
            # Crear backup antes de guardar cambios
            crear_backup_automatico()
            
            # Guardar cambios en la base de datos
            save_torneo(torneo_id)

            # Eliminar también de la BD directamente para asegurar
            from database import get_db
            conn = get_db()
            cursor = conn.cursor()
            if DATABASE_URL:
                cursor.execute('DELETE FROM jugadores WHERE id = %s AND equipo_id = %s', (jugador_id, equipo_id))
            else:
                cursor.execute('DELETE FROM jugadores WHERE id = ? AND equipo_id = ?', (jugador_id, equipo_id))
            conn.commit()

            # Verificar que se eliminó correctamente
            if DATABASE_URL:
                cursor.execute('SELECT COUNT(*) FROM jugadores WHERE id = %s', (jugador_id,))
            else:
                cursor.execute('SELECT COUNT(*) FROM jugadores WHERE id = ?', (jugador_id,))
            exists = cursor.fetchone()[0] > 0
            conn.close()

            if exists:
                print(f"⚠️ ADVERTENCIA: El jugador {jugador_id} aún existe en la BD después de eliminar")
                return jsonify({'error': 'Error al eliminar de la base de datos'}, 500)

            print(f"✅ Jugador {jugador.nombre} eliminado correctamente")
            return jsonify({'success': True, 'mensaje': 'Jugador eliminado'})

        return jsonify({'error': 'No se pudo eliminar el jugador'}), 500

# ==================== FUNCIÓN ACTUALIZADA PARA TARJETAS ====================
@app.route('/api/torneo/<torneo_id>/equipo/<int:equipo_id>/jugadores/<int:jugador_id>', methods=['PUT'])
@login_required
@check_permission
def actualizar_jugador(torneo_id, equipo_id, jugador_id):
    """Actualiza los datos de un jugador, incluyendo sus goles y tarjetas"""
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]

    if equipo_id not in torneo.equipos:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    equipo = torneo.equipos[equipo_id]

    if jugador_id not in equipo.jugadores:
        return jsonify({'error': 'Jugador no encontrado'}), 404

    data = request.json
    jugador = equipo.jugadores[jugador_id]

    # Actualizar campos básicos
    jugador.nombre = data.get('nombre', jugador.nombre)
    jugador.nombre_abreviado = data.get('nombre_abreviado', jugador.nombre_abreviado)
    jugador.posicion = data.get('posicion', jugador.posicion)
    jugador.numero = data.get('numero', jugador.numero)
    jugador.documento = data.get('documento', jugador.documento)
    jugador.fecha_nacimiento = data.get('fecha_nacimiento', jugador.fecha_nacimiento)
    jugador.telefono = data.get('telefono', jugador.telefono)
    jugador.email = data.get('email', jugador.email)
    jugador.altura = data.get('altura', jugador.altura)
    jugador.peso = data.get('peso', jugador.peso)
    jugador.pierna_habil = data.get('pierna_habil', jugador.pierna_habil)

    # Actualizar goles
    if 'goles' in data:
        jugador.goles = data.get('goles', jugador.goles)

    # Actualizar tarjetas amarillas
    if 'tarjetas_amarillas' in data:
        jugador.tarjetas_amarillas = data.get('tarjetas_amarillas', jugador.tarjetas_amarillas)

    # Actualizar tarjetas rojas
    if 'tarjetas_rojas' in data:
        jugador.tarjetas_rojas = data.get('tarjetas_rojas', jugador.tarjetas_rojas)

    save_torneo(torneo_id)
    return jsonify({'success': True, 'mensaje': 'Jugador actualizado correctamente'})

# ==================== RUTAS PARA CUERPO TÉCNICO MEJORADAS ====================

@app.route('/api/torneo/<torneo_id>/equipo/<int:equipo_id>/cuerpo_tecnico', methods=['GET', 'POST'])
@login_required
@check_permission
def gestion_cuerpo_tecnico(torneo_id, equipo_id):
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]

    if equipo_id not in torneo.equipos:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    equipo = torneo.equipos[equipo_id]

    if request.method == 'GET':
        return jsonify([m.to_dict() for m in equipo.cuerpo_tecnico.values()])

    elif request.method == 'POST':
        data = request.json
        if equipo.agregar_miembro_cuerpo_tecnico(
            nombre=data['nombre'],
            rol=data['rol'],
            documento=data.get('documento', ''),
            telefono=data.get('telefono', ''),
            email=data.get('email', ''),
            fecha_nacimiento=data.get('fecha_nacimiento', ''),
            especialidad=data.get('especialidad', ''),
            experiencia=data.get('experiencia', '')
        ):
            save_torneo(torneo_id)
            return jsonify({'success': True, 'mensaje': 'Miembro agregado al cuerpo técnico'})
        return jsonify({'error': 'No se pudo agregar el miembro'}), 400

@app.route('/api/torneo/<torneo_id>/equipo/<int:equipo_id>/cuerpo_tecnico/<int:miembro_id>', methods=['PUT', 'DELETE'])
@login_required
@check_permission
def gestion_miembro_cuerpo_tecnico(torneo_id, equipo_id, miembro_id):
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]

    if equipo_id not in torneo.equipos:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    equipo = torneo.equipos[equipo_id]

    if request.method == 'PUT':
        data = request.json
        if equipo.actualizar_miembro_cuerpo_tecnico(miembro_id, data):
            save_torneo(torneo_id)
            return jsonify({'success': True, 'mensaje': 'Miembro actualizado correctamente'})
        return jsonify({'error': 'Miembro no encontrado'}), 404

    elif request.method == 'DELETE':
        # Verificar si existe antes de eliminar
        if miembro_id not in equipo.cuerpo_tecnico:
            return jsonify({'error': 'Miembro no encontrado'}), 404

        # Obtener información para debug
        miembro = equipo.cuerpo_tecnico[miembro_id]
        print(f"🗑️ Eliminando miembro del cuerpo técnico: {miembro.nombre} (ID: {miembro_id}, Rol: {miembro.rol}) del equipo {equipo.nombre}")

        # Eliminar de memoria
        if equipo.eliminar_miembro_cuerpo_tecnico(miembro_id):
            # Guardar cambios en la base de datos
            save_torneo(torneo_id)

            # Eliminar también de la BD directamente para asegurar
            from database import get_db
            conn = get_db()
            cursor = conn.cursor()
            if DATABASE_URL:
                cursor.execute('DELETE FROM cuerpo_tecnico WHERE id = %s AND equipo_id = %s', (miembro_id, equipo_id))
            else:
                cursor.execute('DELETE FROM cuerpo_tecnico WHERE id = ? AND equipo_id = ?', (miembro_id, equipo_id))
            conn.commit()

            # Verificar que se eliminó correctamente
            if DATABASE_URL:
                cursor.execute('SELECT COUNT(*) FROM cuerpo_tecnico WHERE id = %s', (miembro_id,))
            else:
                cursor.execute('SELECT COUNT(*) FROM cuerpo_tecnico WHERE id = ?', (miembro_id,))
            exists = cursor.fetchone()[0] > 0
            conn.close()

            if exists:
                print(f"⚠️ ADVERTENCIA: El miembro {miembro_id} aún existe en la BD después de eliminar")
                return jsonify({'error': 'Error al eliminar de la base de datos'}, 500)

            print(f"✅ Miembro {miembro.nombre} eliminado correctamente")
            return jsonify({'success': True, 'mensaje': 'Miembro eliminado'})

        return jsonify({'error': 'No se pudo eliminar el miembro'}), 500

@app.route('/api/torneo/<torneo_id>/partido/<int:partido_id>', methods=['PUT'])
@login_required
@check_permission
def editar_partido(torneo_id, partido_id):
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]

    if partido_id not in torneo.partidos:
        return jsonify({'error': 'Partido no encontrado'}), 404

    partido = torneo.partidos[partido_id]
    data = request.json

    if 'fecha' in data:
        partido.fecha = data['fecha'] if data['fecha'] else ""
    if 'hora' in data:
        partido.hora = data['hora'] if data['hora'] else ""
    if 'cancha' in data:
        partido.cancha = data['cancha'] if data['cancha'] else ""

    save_torneo(torneo_id)
    return jsonify({'success': True, 'mensaje': 'Partido actualizado correctamente'})

# ==================== RUTA PARA GUARDAR INFORME ARBITRAL ====================
@app.route('/api/torneo/<torneo_id>/partido/<int:partido_id>/informe_arbitral', methods=['POST', 'GET'])
@login_required
@check_permission
def api_informe_arbitral(torneo_id, partido_id):
    """Guarda o obtiene el informe arbitral de un partido"""
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]

    if partido_id not in torneo.partidos:
        return jsonify({'error': 'Partido no encontrado'}), 404

    partido = torneo.partidos[partido_id]

    if request.method == 'POST':
        data = request.json
        partido.guardar_informe_arbitral(data)
        save_torneo(torneo_id)
        return jsonify({'success': True, 'mensaje': 'Informe arbitral guardado'})

    else:  # GET
        return jsonify(partido.get_informe_arbitral())

@app.route('/api/torneo/<torneo_id>/registro_equipo', methods=['POST'])
@login_required
@check_permission
def registro_equipo_api(torneo_id):
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]
    data = request.json

    if torneo.agregar_equipo_formulario(data):
        save_torneo(torneo_id)
        return jsonify({'success': True, 'mensaje': 'Equipo registrado exitosamente. Espera confirmación.'})
    else:
        return jsonify({'error': 'El equipo ya está registrado'}), 400

# ==================== RUTA PARA BORRAR CALENDARIO ====================

@app.route('/api/torneo/<torneo_id>/borrar_calendario', methods=['DELETE'])
@login_required
@admin_required
def borrar_calendario(torneo_id):
    """Borra todos los partidos del calendario de un torneo"""
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]
    cantidad = len(torneo.partidos)

    # Limpiar todos los partidos
    torneo.partidos.clear()
    torneo.proximo_id_partido = 1

    # Guardar cambios en la base de datos
    save_torneo(torneo_id)

    print(f"🗑️ Se eliminaron {cantidad} partidos del torneo {torneo.nombre}")

    return jsonify({
        'success': True,
        'mensaje': f'Se eliminaron {cantidad} partidos del calendario'
    })

# ==================== RUTA PARA BACKUP MANUAL ====================

@app.route('/api/torneo/<torneo_id>/backup', methods=['POST'])
@admin_required
def crear_backup_manual(torneo_id):
    """Crea un backup manual de la base de datos"""
    import shutil
    from datetime import datetime

    backup_dir = os.path.join(BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f'torneos_backup_{fecha}.db')

    db_path = os.path.join(BASE_DIR, 'torneos.db')
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_file)
        print(f"✅ Backup manual creado: {backup_file}")
        return jsonify({'success': True, 'mensaje': f'Backup creado: {backup_file}'})

    return jsonify({'error': 'No se pudo crear backup'}), 500

# ==================== RUTAS PARA FIXTURE, RESULTADOS, ETC ====================

@app.route('/api/torneo/<torneo_id>/fixture', methods=['POST', 'GET'])
@login_required
@check_permission
def fixture(torneo_id):
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]

    if request.method == 'POST':
        if len(torneo.equipos) < 2:
            return jsonify({'error': 'Se necesitan al menos 2 equipos'}), 400

        torneo.generar_fixture()
        save_torneo(torneo_id)
        return jsonify({'success': True, 'mensaje': f'Fixture generado con {len(torneo.partidos)} partidos'})

    else:
        return jsonify({
            'pendientes': torneo.get_partidos_pendientes(),
            'jugados': torneo.get_partidos_jugados()
        })

@app.route('/api/torneo/<torneo_id>/resultado', methods=['POST'])
@login_required
@check_permission
def registrar_resultado(torneo_id):
    """Registra el resultado de un partido con goleadores"""
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]
    data = request.json

    partido_id = data.get('partido_id')
    goles_local = data.get('goles_local')
    goles_visitante = data.get('goles_visitante')
    goleadores = data.get('goleadores', {})

    # Validar que los datos requeridos estén presentes
    if partido_id is None:
        return jsonify({'error': 'ID de partido requerido'}), 400
    if goles_local is None or goles_visitante is None:
        return jsonify({'error': 'Los goles son requeridos'}), 400

    # Convertir a enteros
    try:
        goles_local = int(goles_local)
        goles_visitante = int(goles_visitante)
    except ValueError:
        return jsonify({'error': 'Los goles deben ser números válidos'}), 400

    # Verificar que el partido existe
    if partido_id not in torneo.partidos:
        return jsonify({'error': 'Partido no encontrado'}), 404

    # Registrar el resultado con goleadores
    if torneo.registrar_resultado_completo(partido_id, goles_local, goles_visitante, goleadores):
        save_torneo(torneo_id)
        return jsonify({'success': True, 'mensaje': 'Resultado registrado correctamente'})
    else:
        return jsonify({'error': 'No se pudo registrar el resultado. Verifica que el partido existe.'}), 400

@app.route('/api/torneo/<torneo_id>/tabla')
@login_required
def tabla_posiciones(torneo_id):
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]
    return jsonify(torneo.get_tabla_posiciones())

@app.route('/api/torneo/<torneo_id>/ranking/goleadores')
@login_required
def ranking_goleadores(torneo_id):
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]
    limite = request.args.get('limite', 15, type=int)
    return jsonify(torneo.get_ranking_goleadores(limite))

@app.route('/api/torneo/<torneo_id>/noticias', methods=['GET', 'POST'])
@login_required
@check_permission
def gestion_noticias(torneo_id):
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]

    if request.method == 'GET':
        return jsonify([n.to_dict() for n in torneo.noticias.values()])

    elif request.method == 'POST':
        data = request.json
        noticia = torneo.agregar_noticia(
            titulo=data['titulo'],
            contenido=data['contenido'],
            tipo=data.get('tipo', 'noticia'),
            url_media=data.get('url_media')
        )
        save_torneo(torneo_id)
        return jsonify(noticia.to_dict())

@app.route('/api/torneo/<torneo_id>/estadisticas/partido/<int:partido_id>')
@login_required
def estadisticas_partido(torneo_id, partido_id):
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]
    resumen = torneo.get_resumen_partido(partido_id)

    if resumen:
        return jsonify(resumen)
    return jsonify({'error': 'Partido no encontrado'}), 404

# ==================== RUTAS PARA PLAYOFFS (ACTUALIZADAS) ====================

@app.route('/api/torneo/<torneo_id>/generar_playoffs', methods=['POST'])
@admin_required
def generar_playoffs(torneo_id):
    """Genera los playoffs después de la liga (semifinales ida/vuelta + final única)"""
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]

    if len(torneo.equipos) < 4:
        return jsonify({'error': 'Se necesitan al menos 4 equipos para playoffs'}), 400

    # Verificar que todos los partidos de liga estén jugados
    partidos_liga = [p for p in torneo.partidos.values() if not p.jugado and not isinstance(p.id, str)]
    if partidos_liga:
        return jsonify({'error': f'Debes completar los {len(partidos_liga)} partidos de la liga antes de generar playoffs'}), 400

    torneo.generar_playoffs()
    torneo.generar_partidos_semifinales()
    save_torneo(torneo_id)

    return jsonify({'success': True, 'mensaje': 'Playoffs generados correctamente'})

@app.route('/api/torneo/<torneo_id>/registrar_semifinal', methods=['POST'])
@admin_required
def registrar_semifinal(torneo_id):
    """Registra el resultado de un partido de semifinal (ida o vuelta)"""
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]
    data = request.json

    llave = data.get('llave')
    partido_tipo = data.get('tipo')
    goles_local = data.get('goles_local')
    goles_visitante = data.get('goles_visitante')

    if not llave or not partido_tipo:
        return jsonify({'error': 'Datos incompletos'}), 400

    if torneo.registrar_resultado_semifinal(llave, partido_tipo, goles_local, goles_visitante):
        save_torneo(torneo_id)
        return jsonify({'success': True, 'mensaje': 'Resultado registrado correctamente'})

    return jsonify({'error': 'Error al registrar resultado'}), 400

@app.route('/api/torneo/<torneo_id>/registrar_final', methods=['POST'])
@admin_required
def registrar_final(torneo_id):
    """Registra el resultado de la final"""
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]
    data = request.json

    goles_local = data.get('goles_local')
    goles_visitante = data.get('goles_visitante')

    if torneo.registrar_resultado_final(goles_local, goles_visitante):
        save_torneo(torneo_id)
        return jsonify({'success': True, 'mensaje': '¡Resultado de la final registrado!'})

    return jsonify({'error': 'Error al registrar resultado de la final'}), 400

@app.route('/api/torneo/<torneo_id>/playoffs')
@login_required
def get_playoffs(torneo_id):
    """Obtiene la información de los playoffs"""
    if torneo_id not in torneos:
        return jsonify({'error': 'Torneo no encontrado'}), 404

    torneo = torneos[torneo_id]
    return jsonify(torneo.get_info_playoffs())

# ==================== GESTIÓN DE USUARIOS (SOLO ADMIN) ====================

@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    """Panel de administración de usuarios"""
    from database import get_db
    conn = get_db()
    cursor = conn.cursor()
    if DATABASE_URL:
        cursor.execute("SELECT id, username, rol, nombre, email, creado_en FROM usuarios ORDER BY id")
    else:
        cursor.execute("SELECT id, username, rol, nombre, email, creado_en FROM usuarios ORDER BY id")
    usuarios = cursor.fetchall()
    conn.close()
    return render_template('admin_usuarios.html', usuarios=usuarios)

@app.route('/admin/usuario/agregar', methods=['POST'])
@admin_required
def admin_agregar_usuario():
    """Agrega un nuevo usuario"""
    from database import get_db
    username = request.form.get('username')
    password = request.form.get('password')
    rol = request.form.get('rol')
    nombre = request.form.get('nombre')
    email = request.form.get('email')

    conn = get_db()
    cursor = conn.cursor()
    try:
        if DATABASE_URL:
            cursor.execute('''
                INSERT INTO usuarios (username, password, rol, nombre, email)
                VALUES (%s, %s, %s, %s, %s)
            ''', (username, password, rol, nombre, email))
        else:
            cursor.execute('''
                INSERT INTO usuarios (username, password, rol, nombre, email)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password, rol, nombre, email))
        conn.commit()
        flash('✅ Usuario agregado correctamente', 'success')
    except Exception as e:
        print(f"Error al agregar usuario: {e}")
        flash('❌ Error: El nombre de usuario ya existe', 'danger')
    conn.close()
    return redirect(url_for('admin_usuarios'))

@app.route('/admin/usuario/eliminar/<int:usuario_id>')
@admin_required
def admin_eliminar_usuario(usuario_id):
    """Elimina un usuario"""
    if usuario_id == session.get('usuario_id'):
        flash('❌ No puedes eliminarte a ti mismo', 'danger')
        return redirect(url_for('admin_usuarios'))

    from database import get_db
    conn = get_db()
    cursor = conn.cursor()
    if DATABASE_URL:
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
    else:
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    conn.commit()
    conn.close()
    flash('✅ Usuario eliminado', 'success')
    return redirect(url_for('admin_usuarios'))

# ==================== RUTA DE DEPURACIÓN (OPCIONAL) ====================

@app.route('/api/debug/equipo/<int:equipo_id>/cuerpo_tecnico')
@admin_required
def debug_cuerpo_tecnico(equipo_id):
    """Endpoint de depuración para ver el cuerpo técnico"""
    for torneo_id, torneo in torneos.items():
        if equipo_id in torneo.equipos:
            equipo = torneo.equipos[equipo_id]
            return jsonify({
                'torneo': torneo.nombre,
                'equipo': equipo.nombre,
                'miembros': [m.to_dict() for m in equipo.cuerpo_tecnico.values()],
                'cantidad': len(equipo.cuerpo_tecnico),
                'proximo_id': equipo.proximo_id_cuerpo_tecnico,
                'ids_actuales': list(equipo.cuerpo_tecnico.keys())
            })
    return jsonify({'error': 'Equipo no encontrado'}), 404

# ==================== RUTA DE VERIFICACIÓN DE DATOS ====================

@app.route('/api/debug/verificar_datos')
@admin_required
def verificar_datos():
    """Endpoint para verificar cuántos datos hay en la BD"""
    from database import get_db
    conn = get_db()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute("SELECT COUNT(*) FROM jugadores")
        total_jugadores = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT e.nombre, COUNT(j.id) as total
            FROM equipos e
            LEFT JOIN jugadores j ON e.id = j.equipo_id
            GROUP BY e.id
        """)
        equipos = cursor.fetchall()
    else:
        cursor.execute("SELECT COUNT(*) FROM jugadores")
        total_jugadores = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT e.nombre, COUNT(j.id) as total
            FROM equipos e
            LEFT JOIN jugadores j ON e.id = j.equipo_id
            GROUP BY e.id
        """)
        equipos = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'total_jugadores': total_jugadores,
        'equipos': [{'nombre': e[0], 'jugadores': e[1]} for e in equipos]
    })

# ==================== INICIO DE LA APLICACIÓN (SOLO PARA DESARROLLO LOCAL) ====================
if __name__ == '__main__':
    app.run(debug=False)
