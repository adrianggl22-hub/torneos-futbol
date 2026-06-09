# database.py - Versión para Render con PostgreSQL
import os
import psycopg2
import psycopg2.extras
import json
from datetime import datetime
from typing import List, Dict, Optional

# ==================== CONFIGURACIÓN ====================
# OBTENER URL DE POSTGRESQL DESDE VARIABLES DE ENTORNO
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    print(f"✅ Conectando a PostgreSQL en Render")
else:
    print("❌ ERROR: DATABASE_URL no encontrada. Usando SQLite (los datos se perderán)")

def get_db():
    """Obtiene la conexión a la base de datos"""
    if DATABASE_URL:
        # Usar PostgreSQL con RealDictCursor para acceder por nombre de columna
        try:
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
            return conn
        except Exception as e:
            print(f"❌ Error conectando a PostgreSQL: {e}")
            raise
    else:
        # Usar SQLite para desarrollo local
        import sqlite3
        conn = sqlite3.connect('torneos.db')
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Inicializa la base de datos creando las tablas necesarias"""
    print("📦 Inicializando base de datos...")
    
    if not DATABASE_URL:
        # Modo SQLite (desarrollo local)
        import sqlite3
        conn = sqlite3.connect('torneos.db')
        cursor = conn.cursor()
        
        # Crear tablas SQLite
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
                goles_contra INTEGER DEFAULT 0
            )
        ''')
        
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
                minutos_jugados INTEGER DEFAULT 0
            )
        ''')
        
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
                experiencia TEXT
            )
        ''')
        
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
                informe_arbitral TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS noticias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                torneo_id TEXT NOT NULL,
                titulo TEXT NOT NULL,
                contenido TEXT,
                fecha TEXT,
                tipo TEXT,
                url_media TEXT
            )
        ''')
        
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
        
        conn.commit()
        conn.close()
        print("✅ Base de datos SQLite inicializada")
        crear_usuarios_default_sqlite()
        return
    
    # ==================== MODO POSTGRESQL ====================
    conn = get_db()
    cursor = conn.cursor()
    
    # Crear tablas en PostgreSQL
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS torneos (
            id VARCHAR(8) PRIMARY KEY,
            nombre TEXT NOT NULL,
            categoria TEXT,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            fase TEXT DEFAULT 'liga',
            datos_playoffs TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipos (
            id SERIAL PRIMARY KEY,
            torneo_id VARCHAR(8) REFERENCES torneos(id) ON DELETE CASCADE,
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
            goles_contra INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jugadores (
            id SERIAL PRIMARY KEY,
            equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
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
            minutos_jugados INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cuerpo_tecnico (
            id SERIAL PRIMARY KEY,
            equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            nombre TEXT NOT NULL,
            rol TEXT,
            documento TEXT,
            telefono TEXT,
            email TEXT,
            fecha_nacimiento TEXT,
            especialidad TEXT,
            experiencia TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidos (
            id SERIAL PRIMARY KEY,
            torneo_id VARCHAR(8) REFERENCES torneos(id) ON DELETE CASCADE,
            id_local INTEGER,
            id_visitante INTEGER,
            nombre_local TEXT,
            nombre_visitante TEXT,
            fecha TEXT,
            hora TEXT,
            cancha TEXT,
            goles_local INTEGER,
            goles_visitante INTEGER,
            jugado INTEGER DEFAULT 0,
            datos_extra TEXT,
            informe_arbitral TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS noticias (
            id SERIAL PRIMARY KEY,
            torneo_id VARCHAR(8) REFERENCES torneos(id) ON DELETE CASCADE,
            titulo TEXT NOT NULL,
            contenido TEXT,
            fecha TEXT,
            tipo TEXT,
            url_media TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL,
            nombre TEXT,
            email TEXT,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Base de datos PostgreSQL inicializada correctamente")
    
    # Crear usuarios por defecto
    crear_usuarios_default_postgresql()

def crear_usuarios_default_sqlite():
    """Crea usuarios por defecto para SQLite"""
    import sqlite3
    conn = sqlite3.connect('torneos.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("📝 Creando usuarios por defecto...")
        cursor.execute('''
            INSERT INTO usuarios (username, password, rol, nombre, email)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', 'admin123', 'admin', 'Administrador del Sistema', 'admin@torneo.com'))
        
        cursor.execute('''
            INSERT INTO usuarios (username, password, rol, nombre, email)
            VALUES (?, ?, ?, ?, ?)
        ''', ('entrenador', 'entrenador123', 'entrenador', 'Entrenador General', 'entrenador@torneo.com'))
        
        cursor.execute('''
            INSERT INTO usuarios (username, password, rol, nombre, email)
            VALUES (?, ?, ?, ?, ?)
        ''', ('invitado', 'invitado123', 'invitado', 'Invitado', 'invitado@torneo.com'))
        
        conn.commit()
        print("✅ Usuarios por defecto creados")
    
    conn.close()

def crear_usuarios_default_postgresql():
    """Crea usuarios por defecto para PostgreSQL"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("📝 Creando usuarios por defecto para PostgreSQL...")
        
        usuarios = [
            ('admin', 'admin123', 'admin', 'Administrador del Sistema', 'admin@torneo.com'),
            ('entrenador', 'entrenador123', 'entrenador', 'Entrenador General', 'entrenador@torneo.com'),
            ('invitado', 'invitado123', 'invitado', 'Invitado', 'invitado@torneo.com')
        ]
        
        for u in usuarios:
            cursor.execute('''
                INSERT INTO usuarios (username, password, rol, nombre, email)
                VALUES (%s, %s, %s, %s, %s)
            ''', u)
        
        conn.commit()
        print("✅ Usuarios por defecto creados en PostgreSQL")
    
    conn.close()

def verificar_usuario(username, password):
    """Verifica las credenciales de un usuario"""
    conn = get_db()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (username, password))
    else:
        cursor.execute("SELECT * FROM usuarios WHERE username = ? AND password = ?", (username, password))
    
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def obtener_usuario_por_id(usuario_id):
    """Obtiene un usuario por su ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
    else:
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def guardar_torneo(torneo):
    """Guarda un torneo completo en la base de datos"""
    conn = get_db()
    cursor = conn.cursor()
    
    print(f"💾 Guardando torneo: {torneo.nombre} (ID: {torneo.id})")
    
    if DATABASE_URL:
        # Modo PostgreSQL
        cursor.execute('''
            INSERT INTO torneos (id, nombre, categoria, fecha_inicio, fecha_fin, fase, datos_playoffs)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                nombre = EXCLUDED.nombre,
                categoria = EXCLUDED.categoria,
                fecha_inicio = EXCLUDED.fecha_inicio,
                fecha_fin = EXCLUDED.fecha_fin,
                fase = EXCLUDED.fase,
                datos_playoffs = EXCLUDED.datos_playoffs
        ''', (torneo.id, torneo.nombre, torneo.categoria, torneo.fecha_inicio, torneo.fecha_fin, torneo.fase, json.dumps(torneo.playoffs)))
        
        # Guardar equipos
        for equipo in torneo.equipos.values():
            cursor.execute('''
                INSERT INTO equipos (id, torneo_id, nombre, entrenador, anio_fundacion, estadio,
                                    puntos, partidos_jugados, ganados, empatados, perdidos,
                                    goles_favor, goles_contra)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    entrenador = EXCLUDED.entrenador,
                    puntos = EXCLUDED.puntos,
                    partidos_jugados = EXCLUDED.partidos_jugados,
                    ganados = EXCLUDED.ganados,
                    empatados = EXCLUDED.empatados,
                    perdidos = EXCLUDED.perdidos,
                    goles_favor = EXCLUDED.goles_favor,
                    goles_contra = EXCLUDED.goles_contra
            ''', (equipo.id, torneo.id, equipo.nombre, equipo.entrenador, equipo.anio_fundacion, equipo.estadio,
                  equipo.puntos, equipo.partidos_jugados, equipo.ganados, equipo.empatados, equipo.perdidos,
                  equipo.goles_favor, equipo.goles_contra))
            
            # Guardar jugadores del equipo
            for jugador in equipo.jugadores.values():
                cursor.execute('''
                    INSERT INTO jugadores 
                    (id, equipo_id, nombre, numero, posicion, nombre_abreviado, documento,
                     fecha_nacimiento, telefono, email, altura, peso, pierna_habil,
                     goles, asistencias, tarjetas_amarillas, tarjetas_rojas, partidos_jugados, minutos_jugados)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        nombre = EXCLUDED.nombre,
                        numero = EXCLUDED.numero,
                        posicion = EXCLUDED.posicion,
                        goles = EXCLUDED.goles,
                        tarjetas_amarillas = EXCLUDED.tarjetas_amarillas,
                        tarjetas_rojas = EXCLUDED.tarjetas_rojas
                ''', (jugador.id, equipo.id, jugador.nombre, jugador.numero, jugador.posicion, jugador.nombre_abreviado,
                      jugador.documento, jugador.fecha_nacimiento, jugador.telefono, jugador.email, jugador.altura, jugador.peso,
                      jugador.pierna_habil, jugador.goles, jugador.asistencias, jugador.tarjetas_amarillas,
                      jugador.tarjetas_rojas, jugador.partidos_jugados, jugador.minutos_jugados))
            
            # Guardar cuerpo técnico
            for miembro in equipo.cuerpo_tecnico.values():
                cursor.execute('''
                    INSERT INTO cuerpo_tecnico
                    (id, equipo_id, nombre, rol, documento, telefono, email, fecha_nacimiento, especialidad, experiencia)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        nombre = EXCLUDED.nombre,
                        rol = EXCLUDED.rol,
                        documento = EXCLUDED.documento,
                        telefono = EXCLUDED.telefono,
                        email = EXCLUDED.email
                ''', (miembro.id, equipo.id, miembro.nombre, miembro.rol, miembro.documento,
                      miembro.telefono, miembro.email, miembro.fecha_nacimiento,
                      miembro.especialidad, miembro.experiencia))
        
        # Guardar partidos
        for partido in torneo.partidos.values():
            informe_arbitral = getattr(partido, 'informe_arbitral', {})
            cursor.execute('''
                INSERT INTO partidos
                (id, torneo_id, id_local, id_visitante, nombre_local, nombre_visitante,
                 fecha, hora, cancha, goles_local, goles_visitante, jugado, datos_extra, informe_arbitral)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    fecha = EXCLUDED.fecha,
                    hora = EXCLUDED.hora,
                    cancha = EXCLUDED.cancha,
                    goles_local = EXCLUDED.goles_local,
                    goles_visitante = EXCLUDED.goles_visitante,
                    jugado = EXCLUDED.jugado,
                    datos_extra = EXCLUDED.datos_extra,
                    informe_arbitral = EXCLUDED.informe_arbitral
            ''', (partido.id, torneo.id, partido.id_local, partido.id_visitante,
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
                  json.dumps(informe_arbitral)))
        
        # Guardar noticias
        for noticia in torneo.noticias.values():
            cursor.execute('''
                INSERT INTO noticias
                (id, torneo_id, titulo, contenido, fecha, tipo, url_media)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    titulo = EXCLUDED.titulo,
                    contenido = EXCLUDED.contenido,
                    fecha = EXCLUDED.fecha,
                    tipo = EXCLUDED.tipo,
                    url_media = EXCLUDED.url_media
            ''', (noticia.id, torneo.id, noticia.titulo, noticia.contenido,
                  noticia.fecha, noticia.tipo, noticia.url_media))
        
        conn.commit()
        conn.close()
        print(f"✅ Torneo '{torneo.nombre}' guardado correctamente en PostgreSQL")
        
    else:
        # Modo SQLite
        cursor.execute('''
            INSERT OR REPLACE INTO torneos (id, nombre, categoria, fecha_inicio, fecha_fin, fase, datos_playoffs)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (torneo.id, torneo.nombre, torneo.categoria, torneo.fecha_inicio, torneo.fecha_fin, torneo.fase, json.dumps(torneo.playoffs)))
        
        # Guardar equipos (SQLite)
        for equipo in torneo.equipos.values():
            cursor.execute('''
                INSERT OR REPLACE INTO equipos (id, torneo_id, nombre, entrenador, anio_fundacion, estadio,
                                              puntos, partidos_jugados, ganados, empatados, perdidos,
                                              goles_favor, goles_contra)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (equipo.id, torneo.id, equipo.nombre, equipo.entrenador, equipo.anio_fundacion, equipo.estadio,
                  equipo.puntos, equipo.partidos_jugados, equipo.ganados, equipo.empatados, equipo.perdidos,
                  equipo.goles_favor, equipo.goles_contra))
            
            # Guardar jugadores (SQLite)
            for jugador in equipo.jugadores.values():
                cursor.execute('''
                    INSERT OR REPLACE INTO jugadores 
                    (id, equipo_id, nombre, numero, posicion, nombre_abreviado, documento,
                     fecha_nacimiento, telefono, email, altura, peso, pierna_habil,
                     goles, asistencias, tarjetas_amarillas, tarjetas_rojas, partidos_jugados, minutos_jugados)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (jugador.id, equipo.id, jugador.nombre, jugador.numero, jugador.posicion, jugador.nombre_abreviado,
                      jugador.documento, jugador.fecha_nacimiento, jugador.telefono, jugador.email, jugador.altura, jugador.peso,
                      jugador.pierna_habil, jugador.goles, jugador.asistencias, jugador.tarjetas_amarillas,
                      jugador.tarjetas_rojas, jugador.partidos_jugados, jugador.minutos_jugados))
            
            # Guardar cuerpo técnico (SQLite)
            for miembro in equipo.cuerpo_tecnico.values():
                cursor.execute('''
                    INSERT OR REPLACE INTO cuerpo_tecnico
                    (id, equipo_id, nombre, rol, documento, telefono, email, fecha_nacimiento, especialidad, experiencia)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (miembro.id, equipo.id, miembro.nombre, miembro.rol, miembro.documento,
                      miembro.telefono, miembro.email, miembro.fecha_nacimiento,
                      miembro.especialidad, miembro.experiencia))
        
        # Guardar partidos (SQLite)
        for partido in torneo.partidos.values():
            informe_arbitral = getattr(partido, 'informe_arbitral', {})
            cursor.execute('''
                INSERT OR REPLACE INTO partidos
                (id, torneo_id, id_local, id_visitante, nombre_local, nombre_visitante,
                 fecha, hora, cancha, goles_local, goles_visitante, jugado, datos_extra, informe_arbitral)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (partido.id, torneo.id, partido.id_local, partido.id_visitante,
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
                  json.dumps(informe_arbitral)))
        
        # Guardar noticias (SQLite)
        for noticia in torneo.noticias.values():
            cursor.execute('''
                INSERT OR REPLACE INTO noticias
                (id, torneo_id, titulo, contenido, fecha, tipo, url_media)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (noticia.id, torneo.id, noticia.titulo, noticia.contenido,
                  noticia.fecha, noticia.tipo, noticia.url_media))
        
        conn.commit()
        conn.close()
        print(f"✅ Torneo '{torneo.nombre}' guardado correctamente en SQLite")

def cargar_torneos():
    """Carga todos los torneos desde la base de datos"""
    from models import Torneo, Equipo, Jugador, MiembroCuerpoTecnico, Partido, Noticia
    
    conn = get_db()
    cursor = conn.cursor()
    
    torneos = {}
    
    if DATABASE_URL:
        cursor.execute('SELECT * FROM torneos')
    else:
        cursor.execute('SELECT * FROM torneos')
    
    torneos_rows = cursor.fetchall()
    
    print(f"📂 Cargando {len(torneos_rows)} torneo(s) desde la base de datos...")
    
    for row in torneos_rows:
        if DATABASE_URL:
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
            
            # Cargar equipos
            cursor.execute('SELECT * FROM equipos WHERE torneo_id = %s', (torneo.id,))
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
                
                # Cargar jugadores
                cursor.execute('SELECT * FROM jugadores WHERE equipo_id = %s', (equipo.id,))
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
                
                # Cargar cuerpo técnico
                cursor.execute('SELECT * FROM cuerpo_tecnico WHERE equipo_id = %s', (equipo.id,))
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
                
                torneo.equipos[equipo.id] = equipo
            
            # Cargar partidos
            cursor.execute('SELECT * FROM partidos WHERE torneo_id = %s', (torneo.id,))
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
        else:
            # Modo SQLite
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
            
            # Cargar equipos (SQLite)
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
                
                # Cargar jugadores (SQLite)
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
                
                # Cargar cuerpo técnico (SQLite)
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
                
                torneo.equipos[equipo.id] = equipo
            
            # Cargar partidos (SQLite)
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
        
        torneos[torneo.id] = torneo
        print(f"  ✅ Torneo: {torneo.nombre} - {len(torneo.equipos)} equipos, {len(torneo.partidos)} partidos")
    
    conn.close()
    print(f"✅ Total: {len(torneos)} torneo(s) cargados correctamente")
    return torneos

def migrar_datos():
    """Función para migrar datos existentes (ejecutar una vez)"""
    print("🔄 Iniciando migración de datos...")
    print("✅ Migración completada")
