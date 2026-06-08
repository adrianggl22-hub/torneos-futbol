# database.py - Versión para PythonAnywhere con rutas absolutas
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from models import Torneo, Equipo, Jugador, MiembroCuerpoTecnico, Partido, Noticia

# ==================== CONFIGURACIÓN DE RUTAS ABSOLUTAS ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'torneos.db')

def get_db():
    """Obtiene la conexión a la base de datos usando ruta absoluta"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos creando las tablas necesarias"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabla de torneos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS torneos (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            categoria TEXT,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            fase TEXT DEFAULT 'liga',
            datos_playoffs TEXT
        )
    ''')
    
    # Tabla de equipos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            torneo_id TEXT NOT NULL,
            nombre TEXT NOT NULL,
            entrenador TEXT,
            anio_fundacion INTEGER,
            estadio TEXT,
            puntos INTEGER DEFAULT 0,
            partidos_jugados INTEGER DEFAULT 0,
            ganados INTEGER DEFAULT 0,
            empatados INTEGER DEFAULT 0,
            perdidos INTEGER DEFAULT 0,
            goles_favor INTEGER DEFAULT 0,
            goles_contra INTEGER DEFAULT 0,
            FOREIGN KEY (torneo_id) REFERENCES torneos(id)
        )
    ''')
    
    # Tabla de jugadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jugadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            numero INTEGER,
            posicion TEXT,
            nombre_abreviado TEXT,
            documento TEXT,
            fecha_nacimiento TEXT,
            telefono TEXT,
            email TEXT,
            altura INTEGER,
            peso REAL,
            pierna_habil TEXT,
            goles INTEGER DEFAULT 0,
            asistencias INTEGER DEFAULT 0,
            tarjetas_amarillas INTEGER DEFAULT 0,
            tarjetas_rojas INTEGER DEFAULT 0,
            partidos_jugados INTEGER DEFAULT 0,
            minutos_jugados INTEGER DEFAULT 0,
            FOREIGN KEY (equipo_id) REFERENCES equipos(id)
        )
    ''')
    
    # Tabla de cuerpo técnico
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cuerpo_tecnico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            rol TEXT,
            documento TEXT,
            telefono TEXT,
            email TEXT,
            fecha_nacimiento TEXT,
            especialidad TEXT,
            experiencia TEXT,
            FOREIGN KEY (equipo_id) REFERENCES equipos(id)
        )
    ''')
    
    # Tabla de partidos (con columna informe_arbitral)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            torneo_id TEXT NOT NULL,
            id_local INTEGER NOT NULL,
            id_visitante INTEGER NOT NULL,
            nombre_local TEXT,
            nombre_visitante TEXT,
            fecha TEXT,
            hora TEXT,
            cancha TEXT,
            goles_local INTEGER,
            goles_visitante INTEGER,
            jugado INTEGER DEFAULT 0,
            datos_extra TEXT,
            informe_arbitral TEXT,
            FOREIGN KEY (torneo_id) REFERENCES torneos(id)
        )
    ''')
    
    # Tabla de noticias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            torneo_id TEXT NOT NULL,
            titulo TEXT NOT NULL,
            contenido TEXT,
            fecha TEXT,
            tipo TEXT,
            url_media TEXT,
            FOREIGN KEY (torneo_id) REFERENCES torneos(id)
        )
    ''')
    
    # ==================== TABLAS PARA AUTENTICACIÓN ====================
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL,
            nombre TEXT,
            email TEXT,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de sesiones (para tracking de sesiones)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sesiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            token TEXT,
            ultimo_acceso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')
    
    # Verificar si falta la columna informe_arbitral en tablas existentes
    try:
        cursor.execute("PRAGMA table_info(partidos)")
        columnas = cursor.fetchall()
        columnas_nombres = [col['name'] for col in columnas]
        
        if 'informe_arbitral' not in columnas_nombres:
            print("⚠️ Agregando columna informe_arbitral a la tabla partidos...")
            cursor.execute("ALTER TABLE partidos ADD COLUMN informe_arbitral TEXT")
            print("✅ Columna informe_arbitral agregada")
    except Exception as e:
        print(f"⚠️ Error verificando columnas: {e}")
    
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente")
    
    # Crear usuarios por defecto
    crear_usuarios_default()

def crear_usuarios_default():
    """Crea usuarios por defecto si no existen"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar si ya hay usuarios
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("📝 Creando usuarios por defecto...")
        
        # Usuario administrador (contraseña: admin123)
        cursor.execute('''
            INSERT INTO usuarios (username, password, rol, nombre, email)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', 'admin123', 'admin', 'Administrador del Sistema', 'admin@torneo.com'))
        
        # Usuario entrenador (contraseña: entrenador123)
        cursor.execute('''
            INSERT INTO usuarios (username, password, rol, nombre, email)
            VALUES (?, ?, ?, ?, ?)
        ''', ('entrenador', 'entrenador123', 'entrenador', 'Entrenador General', 'entrenador@torneo.com'))
        
        # Usuario invitado (solo lectura) - opcional
        cursor.execute('''
            INSERT INTO usuarios (username, password, rol, nombre, email)
            VALUES (?, ?, ?, ?, ?)
        ''', ('invitado', 'invitado123', 'invitado', 'Invitado', 'invitado@torneo.com'))
        
        conn.commit()
        print("✅ Usuarios por defecto creados:")
        print("   👑 Admin: admin / admin123 (Acceso total)")
        print("   👨‍🏫 Entrenador: entrenador / entrenador123 (Solo lectura)")
        print("   👤 Invitado: invitado / invitado123 (Solo lectura)")
    else:
        print(f"✅ Usuarios ya existen ({count} usuarios en el sistema)")
    
    conn.close()

def verificar_usuario(username, password):
    """Verifica las credenciales de un usuario"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE username = ? AND password = ?', (username, password))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def obtener_usuario_por_id(usuario_id):
    """Obtiene un usuario por su ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE id = ?', (usuario_id,))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def guardar_sesion(usuario_id, token, ip_address):
    """Guarda una sesión de usuario"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sesiones (usuario_id, token, ip_address, ultimo_acceso)
        VALUES (?, ?, ?, ?)
    ''', (usuario_id, token, ip_address, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def actualizar_sesion(token):
    """Actualiza el último acceso de una sesión"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE sesiones 
        SET ultimo_acceso = ? 
        WHERE token = ?
    ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), token))
    conn.commit()
    conn.close()

def guardar_torneo(torneo: Torneo):
    """Guarda un torneo completo en la base de datos"""
    conn = get_db()
    cursor = conn.cursor()
    
    print(f"💾 Guardando torneo: {torneo.nombre} (ID: {torneo.id})")
    print(f"   📊 Contadores: equipos={torneo.proximo_id_equipo}, partidos={torneo.proximo_id_partido}")
    
    # Guardar torneo
    cursor.execute('''
        INSERT OR REPLACE INTO torneos (id, nombre, categoria, fecha_inicio, fecha_fin, fase, datos_playoffs)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        torneo.id, torneo.nombre, torneo.categoria,
        torneo.fecha_inicio, torneo.fecha_fin,
        torneo.fase, json.dumps(torneo.playoffs)
    ))
    
    # Guardar equipos
    for equipo in torneo.equipos.values():
        cursor.execute('''
            INSERT OR REPLACE INTO equipos (id, torneo_id, nombre, entrenador, anio_fundacion, estadio,
                                          puntos, partidos_jugados, ganados, empatados, perdidos,
                                          goles_favor, goles_contra)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            equipo.id, torneo.id, equipo.nombre, equipo.entrenador, equipo.anio_fundacion, equipo.estadio,
            equipo.puntos, equipo.partidos_jugados, equipo.ganados, equipo.empatados, equipo.perdidos,
            equipo.goles_favor, equipo.goles_contra
        ))
        
        # Guardar jugadores del equipo
        for jugador in equipo.jugadores.values():
            cursor.execute('''
                INSERT OR REPLACE INTO jugadores 
                (id, equipo_id, nombre, numero, posicion, nombre_abreviado, documento,
                 fecha_nacimiento, telefono, email, altura, peso, pierna_habil,
                 goles, asistencias, tarjetas_amarillas, tarjetas_rojas, partidos_jugados, minutos_jugados)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                jugador.id, equipo.id, jugador.nombre, jugador.numero, jugador.posicion,
                jugador.nombre_abreviado, jugador.documento, jugador.fecha_nacimiento,
                jugador.telefono, jugador.email, jugador.altura, jugador.peso, jugador.pierna_habil,
                jugador.goles, jugador.asistencias, jugador.tarjetas_amarillas, jugador.tarjetas_rojas,
                jugador.partidos_jugados, jugador.minutos_jugados
            ))
        
        # Guardar cuerpo técnico
        for miembro in equipo.cuerpo_tecnico.values():
            cursor.execute('''
                INSERT OR REPLACE INTO cuerpo_tecnico
                (id, equipo_id, nombre, rol, documento, telefono, email, fecha_nacimiento, especialidad, experiencia)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                miembro.id, equipo.id, miembro.nombre, miembro.rol, miembro.documento,
                miembro.telefono, miembro.email, miembro.fecha_nacimiento,
                miembro.especialidad, miembro.experiencia
            ))
    
    # Guardar partidos
    for partido in torneo.partidos.values():
        # Obtener informe_arbitral (puede no existir en partidos antiguos)
        informe_arbitral = getattr(partido, 'informe_arbitral', {})
        
        cursor.execute('''
            INSERT OR REPLACE INTO partidos
            (id, torneo_id, id_local, id_visitante, nombre_local, nombre_visitante,
             fecha, hora, cancha, goles_local, goles_visitante, jugado, datos_extra, informe_arbitral)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            partido.id, torneo.id, partido.id_local, partido.id_visitante,
            partido.nombre_local, partido.nombre_visitante,
            partido.fecha, partido.hora, partido.cancha,
            partido.goles_local, partido.goles_visitante,
            1 if partido.jugado else 0,
            json.dumps({
                'goleadores_local': partido.goleadores_local,
                'goleadores_visitante': partido.goleadores_visitante,
                'amonestados_local': partido.amonestados_local,
                'amonestados_visitante': partido.amonestados_visitante
            }),
            json.dumps(informe_arbitral)
        ))
    
    # Guardar noticias
    for noticia in torneo.noticias.values():
        cursor.execute('''
            INSERT OR REPLACE INTO noticias
            (id, torneo_id, titulo, contenido, fecha, tipo, url_media)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            noticia.id, torneo.id, noticia.titulo, noticia.contenido,
            noticia.fecha, noticia.tipo, noticia.url_media
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ Torneo '{torneo.nombre}' guardado correctamente")

def cargar_torneos():
    """Carga todos los torneos desde la base de datos"""
    from models import Torneo, Equipo, Jugador, MiembroCuerpoTecnico, Partido, Noticia
    import json
    
    conn = get_db()
    cursor = conn.cursor()
    
    torneos = {}
    
    # Cargar torneos
    cursor.execute('SELECT * FROM torneos')
    torneos_rows = cursor.fetchall()
    
    print(f"📂 Cargando {len(torneos_rows)} torneo(s) desde la base de datos...")
    
    for row in torneos_rows:
        torneo = Torneo(
            id_torneo=row['id'],
            nombre=row['nombre'],
            categoria=row['categoria'],
            fecha_inicio=row['fecha_inicio'],
            fecha_fin=row['fecha_fin']
        )
        torneo.fase = row['fase']
        if row['datos_playoffs']:
            torneo.playoffs = json.loads(row['datos_playoffs'])
        
        # Inicializar contadores
        max_equipo_id = 0
        max_partido_id = 0
        max_noticia_id = 0
        
        # Cargar equipos
        cursor.execute('SELECT * FROM equipos WHERE torneo_id = ?', (torneo.id,))
        for eq_row in cursor.fetchall():
            equipo = Equipo(
                id_equipo=eq_row['id'],
                nombre=eq_row['nombre'],
                entrenador=eq_row['entrenador'] or '',
                anio_fundacion=eq_row['anio_fundacion'],
                estadio=eq_row['estadio'] or ''
            )
            equipo.puntos = eq_row['puntos']
            equipo.partidos_jugados = eq_row['partidos_jugados']
            equipo.ganados = eq_row['ganados']
            equipo.empatados = eq_row['empatados']
            equipo.perdidos = eq_row['perdidos']
            equipo.goles_favor = eq_row['goles_favor']
            equipo.goles_contra = eq_row['goles_contra']
            equipo.diferencia_goles = equipo.goles_favor - equipo.goles_contra
            
            # Actualizar máximo ID de equipo
            if eq_row['id'] > max_equipo_id:
                max_equipo_id = eq_row['id']
            
            # Inicializar contadores del equipo
            max_jugador_id = 0
            max_ct_id = 0
            
            # Cargar jugadores
            cursor.execute('SELECT * FROM jugadores WHERE equipo_id = ?', (equipo.id,))
            for jug_row in cursor.fetchall():
                jugador = Jugador(
                    id=jug_row['id'],
                    nombre=jug_row['nombre'],
                    equipo_id=equipo.id,
                    numero=jug_row['numero'],
                    posicion=jug_row['posicion'] or '',
                    nombre_abreviado=jug_row['nombre_abreviado'] or '',
                    documento=jug_row['documento'] or '',
                    fecha_nacimiento=jug_row['fecha_nacimiento'] or '',
                    telefono=jug_row['telefono'] or '',
                    email=jug_row['email'] or '',
                    altura=jug_row['altura'],
                    peso=jug_row['peso'],
                    pierna_habil=jug_row['pierna_habil'] or '',
                    goles=jug_row['goles'] or 0,
                    asistencias=jug_row['asistencias'] or 0,
                    tarjetas_amarillas=jug_row['tarjetas_amarillas'] or 0,
                    tarjetas_rojas=jug_row['tarjetas_rojas'] or 0,
                    partidos_jugados=jug_row['partidos_jugados'] or 0,
                    minutos_jugados=jug_row['minutos_jugados'] or 0
                )
                equipo.jugadores[jugador.id] = jugador
                if jugador.id > max_jugador_id:
                    max_jugador_id = jugador.id
            
            # Cargar cuerpo técnico
            cursor.execute('SELECT * FROM cuerpo_tecnico WHERE equipo_id = ?', (equipo.id,))
            for ct_row in cursor.fetchall():
                miembro = MiembroCuerpoTecnico(
                    id=ct_row['id'],
                    nombre=ct_row['nombre'],
                    equipo_id=equipo.id,
                    rol=ct_row['rol'] or '',
                    documento=ct_row['documento'] or '',
                    telefono=ct_row['telefono'] or '',
                    email=ct_row['email'] or '',
                    fecha_nacimiento=ct_row['fecha_nacimiento'] or '',
                    especialidad=ct_row['especialidad'] or '',
                    experiencia=ct_row['experiencia'] or ''
                )
                equipo.cuerpo_tecnico[miembro.id] = miembro
                if miembro.id > max_ct_id:
                    max_ct_id = miembro.id
            
            # Actualizar contadores del equipo
            equipo.proximo_id_jugador = max_jugador_id + 1 if max_jugador_id > 0 else 1
            equipo.proximo_id_cuerpo_tecnico = max_ct_id + 1 if max_ct_id > 0 else 1
            
            torneo.equipos[equipo.id] = equipo
        
        # Actualizar contadores del torneo
        torneo.proximo_id_equipo = max_equipo_id + 1 if max_equipo_id > 0 else 1
        
        # Cargar partidos
        cursor.execute('SELECT * FROM partidos WHERE torneo_id = ?', (torneo.id,))
        for par_row in cursor.fetchall():
            datos_extra = json.loads(par_row['datos_extra']) if par_row['datos_extra'] else {}
            informe_arbitral = json.loads(par_row['informe_arbitral']) if par_row['informe_arbitral'] else {}
            
            partido = Partido(
                id_partido=par_row['id'],
                id_local=par_row['id_local'],
                id_visitante=par_row['id_visitante'],
                nombre_local=par_row['nombre_local'],
                nombre_visitante=par_row['nombre_visitante'],
                fecha=par_row['fecha'] or '',
                hora=par_row['hora'] or '',
                cancha=par_row['cancha'] or ''
            )
            partido.goles_local = par_row['goles_local'] or 0
            partido.goles_visitante = par_row['goles_visitante'] or 0
            partido.jugado = bool(par_row['jugado'])
            partido.goleadores_local = datos_extra.get('goleadores_local', [])
            partido.goleadores_visitante = datos_extra.get('goleadores_visitante', [])
            partido.amonestados_local = datos_extra.get('amonestados_local', [])
            partido.amonestados_visitante = datos_extra.get('amonestados_visitante', [])
            partido.informe_arbitral = informe_arbitral
            
            torneo.partidos[partido.id] = partido
            if partido.id > max_partido_id:
                max_partido_id = partido.id
        
        torneo.proximo_id_partido = max_partido_id + 1 if max_partido_id > 0 else 1
        
        # Cargar noticias
        cursor.execute('SELECT * FROM noticias WHERE torneo_id = ?', (torneo.id,))
        for not_row in cursor.fetchall():
            noticia = Noticia(
                id=not_row['id'],
                titulo=not_row['titulo'],
                contenido=not_row['contenido'],
                fecha=not_row['fecha'],
                tipo=not_row['tipo'],
                url_media=not_row['url_media'],
                torneo_id=torneo.id
            )
            torneo.noticias[noticia.id] = noticia
            if noticia.id > max_noticia_id:
                max_noticia_id = noticia.id
        
        torneo.proximo_id_noticia = max_noticia_id + 1 if max_noticia_id > 0 else 1
        
        torneos[torneo.id] = torneo
        print(f"  ✅ Torneo: {torneo.nombre} - {len(torneo.equipos)} equipos, {len(torneo.partidos)} partidos")
        print(f"     📊 Contadores: equipos={torneo.proximo_id_equipo}, partidos={torneo.proximo_id_partido}")
    
    conn.close()
    print(f"✅ Total: {len(torneos)} torneo(s) cargados correctamente")
    return torneos

def migrar_datos():
    """Función para migrar datos existentes (ejecutar una vez)"""
    print("🔄 Iniciando migración de datos...")
    
    # Verificar y agregar columna informe_arbitral si no existe
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(partidos)")
        columnas = cursor.fetchall()
        columnas_nombres = [col['name'] for col in columnas]
        
        if 'informe_arbitral' not in columnas_nombres:
            print("⚠️ Agregando columna informe_arbitral...")
            cursor.execute("ALTER TABLE partidos ADD COLUMN informe_arbitral TEXT")
            conn.commit()
            print("✅ Columna agregada")
        else:
            print("✅ Columna informe_arbitral ya existe")
    except Exception as e:
        print(f"⚠️ Error: {e}")
    
    conn.close()
    print("✅ Migración completada")