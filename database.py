# database.py - Versión que limpia y recrea las tablas automáticamente
import os
import psycopg2
import psycopg2.extras
import json
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    print(f"✅ Conectando a PostgreSQL en Render")
else:
    print("❌ ERROR: DATABASE_URL no encontrada")

def get_db():
    """Obtiene la conexión a la base de datos"""
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        import sqlite3
        conn = sqlite3.connect('torneos.db')
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Inicializa la base de datos - Limpia y recrea todas las tablas"""
    print("📦 Inicializando base de datos...")
    
    if not DATABASE_URL:
        # Modo SQLite
        import sqlite3
        conn = sqlite3.connect('torneos.db')
        cursor = conn.cursor()
        
        # Eliminar tablas existentes
        cursor.execute("DROP TABLE IF EXISTS jugadores")
        cursor.execute("DROP TABLE IF EXISTS cuerpo_tecnico")
        cursor.execute("DROP TABLE IF EXISTS partidos")
        cursor.execute("DROP TABLE IF EXISTS noticias")
        cursor.execute("DROP TABLE IF EXISTS equipos")
        cursor.execute("DROP TABLE IF EXISTS torneos")
        cursor.execute("DROP TABLE IF EXISTS usuarios")
        
        # Crear tablas
        cursor.execute('''CREATE TABLE torneos (id TEXT PRIMARY KEY, nombre TEXT NOT NULL, categoria TEXT, fecha_inicio TEXT, fecha_fin TEXT, fase TEXT, datos_playoffs TEXT)''')
        cursor.execute('''CREATE TABLE equipos (id INTEGER PRIMARY KEY AUTOINCREMENT, torneo_id TEXT, nombre TEXT, entrenador TEXT, anio_fundacion INTEGER, estadio TEXT, puntos INTEGER DEFAULT 0, partidos_jugados INTEGER DEFAULT 0, ganados INTEGER DEFAULT 0, empatados INTEGER DEFAULT 0, perdidos INTEGER DEFAULT 0, goles_favor INTEGER DEFAULT 0, goles_contra INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE jugadores (id INTEGER PRIMARY KEY AUTOINCREMENT, equipo_id INTEGER, nombre TEXT, numero INTEGER, posicion TEXT, nombre_abreviado TEXT, documento TEXT, fecha_nacimiento TEXT, telefono TEXT, email TEXT, altura INTEGER, peso REAL, pierna_habil TEXT, goles INTEGER DEFAULT 0, asistencias INTEGER DEFAULT 0, tarjetas_amarillas INTEGER DEFAULT 0, tarjetas_rojas INTEGER DEFAULT 0, partidos_jugados INTEGER DEFAULT 0, minutos_jugados INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE cuerpo_tecnico (id INTEGER PRIMARY KEY AUTOINCREMENT, equipo_id INTEGER, nombre TEXT, rol TEXT, documento TEXT, telefono TEXT, email TEXT, fecha_nacimiento TEXT, especialidad TEXT, experiencia TEXT)''')
        cursor.execute('''CREATE TABLE partidos (id INTEGER PRIMARY KEY AUTOINCREMENT, torneo_id TEXT, id_local INTEGER, id_visitante INTEGER, nombre_local TEXT, nombre_visitante TEXT, fecha TEXT, hora TEXT, cancha TEXT, goles_local INTEGER, goles_visitante INTEGER, jugado INTEGER DEFAULT 0, datos_extra TEXT, informe_arbitral TEXT)''')
        cursor.execute('''CREATE TABLE noticias (id INTEGER PRIMARY KEY AUTOINCREMENT, torneo_id TEXT, titulo TEXT, contenido TEXT, fecha TEXT, tipo TEXT, url_media TEXT)''')
        cursor.execute('''CREATE TABLE usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, rol TEXT, nombre TEXT, email TEXT, creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Insertar usuarios
        cursor.execute("INSERT INTO usuarios (username, password, rol, nombre, email) VALUES (?, ?, ?, ?, ?)", ('admin', 'admin123', 'admin', 'Administrador', 'admin@torneo.com'))
        cursor.execute("INSERT INTO usuarios (username, password, rol, nombre, email) VALUES (?, ?, ?, ?, ?)", ('entrenador', 'entrenador123', 'entrenador', 'Entrenador', 'entrenador@torneo.com'))
        cursor.execute("INSERT INTO usuarios (username, password, rol, nombre, email) VALUES (?, ?, ?, ?, ?)", ('invitado', 'invitado123', 'invitado', 'Invitado', 'invitado@torneo.com'))
        
        conn.commit()
        conn.close()
        print("✅ Base de datos SQLite inicializada")
        return
    
    # ==================== MODO POSTGRESQL ====================
    conn = get_db()
    cursor = conn.cursor()
    
    print("🔄 Limpiando tablas existentes...")
    
    # Eliminar tablas en orden correcto (primero las que tienen dependencias)
    cursor.execute("DROP TABLE IF EXISTS jugadores CASCADE")
    cursor.execute("DROP TABLE IF EXISTS cuerpo_tecnico CASCADE")
    cursor.execute("DROP TABLE IF EXISTS partidos CASCADE")
    cursor.execute("DROP TABLE IF EXISTS noticias CASCADE")
    cursor.execute("DROP TABLE IF EXISTS equipos CASCADE")
    cursor.execute("DROP TABLE IF EXISTS torneos CASCADE")
    cursor.execute("DROP TABLE IF EXISTS usuarios CASCADE")
    
    print("🔄 Recreando tablas...")
    
    # Crear tablas
    cursor.execute('''
        CREATE TABLE torneos (
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
        CREATE TABLE equipos (
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
        CREATE TABLE jugadores (
            id SERIAL,
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
            minutos_jugados INTEGER DEFAULT 0,
            PRIMARY KEY (id, equipo_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE cuerpo_tecnico (
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
        CREATE TABLE partidos (
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
        CREATE TABLE noticias (
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
        CREATE TABLE usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL,
            nombre TEXT,
            email TEXT,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("🔄 Creando usuarios por defecto...")
    
    # Insertar usuarios
    cursor.execute('''
        INSERT INTO usuarios (username, password, rol, nombre, email) 
        VALUES (%s, %s, %s, %s, %s)
    ''', ('admin', 'admin123', 'admin', 'Administrador del Sistema', 'admin@torneo.com'))
    
    cursor.execute('''
        INSERT INTO usuarios (username, password, rol, nombre, email) 
        VALUES (%s, %s, %s, %s, %s)
    ''', ('entrenador', 'entrenador123', 'entrenador', 'Entrenador General', 'entrenador@torneo.com'))
    
    cursor.execute('''
        INSERT INTO usuarios (username, password, rol, nombre, email) 
        VALUES (%s, %s, %s, %s, %s)
    ''', ('invitado', 'invitado123', 'invitado', 'Invitado', 'invitado@torneo.com'))
    
    conn.commit()
    conn.close()
    print("✅ Base de datos PostgreSQL inicializada correctamente")

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
        # Guardar torneo
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
            
            # Guardar jugadores
            for jugador in equipo.jugadores.values():
                cursor.execute('''
                    INSERT INTO jugadores 
                    (id, equipo_id, nombre, numero, posicion, nombre_abreviado, documento,
                     fecha_nacimiento, telefono, email, altura, peso, pierna_habil,
                     goles, asistencias, tarjetas_amarillas, tarjetas_rojas, partidos_jugados, minutos_jugados)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id, equipo_id) DO UPDATE SET
                        nombre = EXCLUDED.nombre,
                        numero = EXCLUDED.numero,
                        posicion = EXCLUDED.posicion,
                        nombre_abreviado = EXCLUDED.nombre_abreviado,
                        documento = EXCLUDED.documento,
                        fecha_nacimiento = EXCLUDED.fecha_nacimiento,
                        telefono = EXCLUDED.telefono,
                        email = EXCLUDED.email,
                        altura = EXCLUDED.altura,
                        peso = EXCLUDED.peso,
                        pierna_habil = EXCLUDED.pierna_habil,
                        goles = EXCLUDED.goles,
                        asistencias = EXCLUDED.asistencias,
                        tarjetas_amarillas = EXCLUDED.tarjetas_amarillas,
                        tarjetas_rojas = EXCLUDED.tarjetas_rojas,
                        partidos_jugados = EXCLUDED.partidos_jugados,
                        minutos_jugados = EXCLUDED.minutos_jugados
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
                        email = EXCLUDED.email,
                        fecha_nacimiento = EXCLUDED.fecha_nacimiento,
                        especialidad = EXCLUDED.especialidad,
                        experiencia = EXCLUDED.experiencia
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
        print(f"✅ Torneo '{torneo.nombre}' guardado correctamente en PostgreSQL")
        
    else:
        # Modo SQLite (similar pero con sintaxis SQLite)
        cursor.execute('INSERT OR REPLACE INTO torneos (id, nombre, categoria, fecha_inicio, fecha_fin, fase, datos_playoffs) VALUES (?, ?, ?, ?, ?, ?, ?)',
                      (torneo.id, torneo.nombre, torneo.categoria, torneo.fecha_inicio, torneo.fecha_fin, torneo.fase, json.dumps(torneo.playoffs)))
        
        for equipo in torneo.equipos.values():
            cursor.execute('INSERT OR REPLACE INTO equipos (id, torneo_id, nombre, entrenador, anio_fundacion, estadio, puntos, partidos_jugados, ganados, empatados, perdidos, goles_favor, goles_contra) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                          (equipo.id, torneo.id, equipo.nombre, equipo.entrenador, equipo.anio_fundacion, equipo.estadio,
                           equipo.puntos, equipo.partidos_jugados, equipo.ganados, equipo.empatados, equipo.perdidos,
                           equipo.goles_favor, equipo.goles_contra))
            
            for jugador in equipo.jugadores.values():
                cursor.execute('INSERT OR REPLACE INTO jugadores (id, equipo_id, nombre, numero, posicion, nombre_abreviado, documento, fecha_nacimiento, telefono, email, altura, peso, pierna_habil, goles, asistencias, tarjetas_amarillas, tarjetas_rojas, partidos_jugados, minutos_jugados) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                              (jugador.id, equipo.id, jugador.nombre, jugador.numero, jugador.posicion, jugador.nombre_abreviado,
                               jugador.documento, jugador.fecha_nacimiento, jugador.telefono, jugador.email, jugador.altura, jugador.peso,
                               jugador.pierna_habil, jugador.goles, jugador.asistencias, jugador.tarjetas_amarillas,
                               jugador.tarjetas_rojas, jugador.partidos_jugados, jugador.minutos_jugados))
            
            for miembro in equipo.cuerpo_tecnico.values():
                cursor.execute('INSERT OR REPLACE INTO cuerpo_tecnico (id, equipo_id, nombre, rol, documento, telefono, email, fecha_nacimiento, especialidad, experiencia) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                              (miembro.id, equipo.id, miembro.nombre, miembro.rol, miembro.documento, miembro.telefono,
                               miembro.email, miembro.fecha_nacimiento, miembro.especialidad, miembro.experiencia))
        
        for partido in torneo.partidos.values():
            cursor.execute('INSERT OR REPLACE INTO partidos (id, torneo_id, id_local, id_visitante, nombre_local, nombre_visitante, fecha, hora, cancha, goles_local, goles_visitante, jugado, datos_extra, informe_arbitral) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                          (partido.id, torneo.id, partido.id_local, partido.id_visitante, partido.nombre_local, partido.nombre_visitante,
                           partido.fecha, partido.hora, partido.cancha, partido.goles_local, partido.goles_visitante,
                           1 if partido.jugado else 0, json.dumps({'goleadores_local': partido.goleadores_local, 'goleadores_visitante': partido.goleadores_visitante}),
                           json.dumps(getattr(partido, 'informe_arbitral', {}))))
        
        conn.commit()
        print(f"✅ Torneo '{torneo.nombre}' guardado correctamente en SQLite")
    
    conn.close()

def cargar_torneos():
    """Carga todos los torneos desde la base de datos"""
    from models import Torneo, Equipo, Jugador, MiembroCuerpoTecnico, Partido
    
    conn = get_db()
    cursor = conn.cursor()
    torneos = {}
    
    if DATABASE_URL:
        cursor.execute('SELECT * FROM torneos')
    else:
        cursor.execute('SELECT * FROM torneos')
    
    for row in cursor.fetchall():
        torneo = Torneo(row['id'], row['nombre'], row['categoria'], row['fecha_inicio'], row['fecha_fin'])
        torneo.fase = row['fase'] if row['fase'] else 'liga'
        if row['datos_playoffs']:
            torneo.playoffs = json.loads(row['datos_playoffs'])
        
        # Cargar equipos
        if DATABASE_URL:
            cursor.execute('SELECT * FROM equipos WHERE torneo_id = %s', (torneo.id,))
        else:
            cursor.execute('SELECT * FROM equipos WHERE torneo_id = ?', (torneo.id,))
        
        for eq in cursor.fetchall():
            equipo = Equipo(eq['id'], eq['nombre'], eq['entrenador'] or '', eq['anio_fundacion'], eq['estadio'] or '')
            equipo.puntos = eq['puntos']
            equipo.partidos_jugados = eq['partidos_jugados']
            equipo.ganados = eq['ganados']
            equipo.empatados = eq['empatados']
            equipo.perdidos = eq['perdidos']
            equipo.goles_favor = eq['goles_favor']
            equipo.goles_contra = eq['goles_contra']
            
            # Cargar jugadores
            if DATABASE_URL:
                cursor.execute('SELECT * FROM jugadores WHERE equipo_id = %s', (equipo.id,))
            else:
                cursor.execute('SELECT * FROM jugadores WHERE equipo_id = ?', (equipo.id,))
            
            for jug in cursor.fetchall():
                jugador = Jugador(jug['id'], jug['nombre'], equipo.id, jug['numero'] or 0, jug['posicion'] or '',
                                 jug['nombre_abreviado'] or '', jug['documento'] or '', jug['fecha_nacimiento'] or '',
                                 jug['telefono'] or '', jug['email'] or '', jug['altura'], jug['peso'],
                                 jug['pierna_habil'] or '', jug['goles'] or 0, jug['asistencias'] or 0,
                                 jug['tarjetas_amarillas'] or 0, jug['tarjetas_rojas'] or 0,
                                 jug['partidos_jugados'] or 0, jug['minutos_jugados'] or 0)
                equipo.jugadores[jugador.id] = jugador
                if jugador.id >= equipo.proximo_id_jugador:
                    equipo.proximo_id_jugador = jugador.id + 1
            
            # Cargar cuerpo técnico
            if DATABASE_URL:
                cursor.execute('SELECT * FROM cuerpo_tecnico WHERE equipo_id = %s', (equipo.id,))
            else:
                cursor.execute('SELECT * FROM cuerpo_tecnico WHERE equipo_id = ?', (equipo.id,))
            
            for ct in cursor.fetchall():
                miembro = MiembroCuerpoTecnico(ct['id'], ct['nombre'], equipo.id, ct['rol'] or '',
                                               ct['documento'] or '', ct['telefono'] or '', ct['email'] or '',
                                               ct['fecha_nacimiento'] or '', ct['especialidad'] or '', ct['experiencia'] or '')
                equipo.cuerpo_tecnico[miembro.id] = miembro
            
            torneo.equipos[equipo.id] = equipo
        
        # Cargar partidos
        if DATABASE_URL:
            cursor.execute('SELECT * FROM partidos WHERE torneo_id = %s', (torneo.id,))
        else:
            cursor.execute('SELECT * FROM partidos WHERE torneo_id = ?', (torneo.id,))
        
        for par in cursor.fetchall():
            datos_extra = json.loads(par['datos_extra']) if par['datos_extra'] else {}
            partido = Partido(par['id'], par['id_local'], par['id_visitante'], par['nombre_local'], par['nombre_visitante'],
                             par['fecha'] or '', par['hora'] or '', par['cancha'] or '')
            partido.goles_local = par['goles_local'] or 0
            partido.goles_visitante = par['goles_visitante'] or 0
            partido.jugado = bool(par['jugado'])
            partido.goleadores_local = datos_extra.get('goleadores_local', [])
            partido.goleadores_visitante = datos_extra.get('goleadores_visitante', [])
            torneo.partidos[partido.id] = partido
        
        torneos[torneo.id] = torneo
    
    conn.close()
    print(f"📂 Cargados {len(torneos)} torneo(s)")
    return torneos

def migrar_datos():
    """Función para migrar datos existentes"""
    print("🔄 Migración de datos completada")
