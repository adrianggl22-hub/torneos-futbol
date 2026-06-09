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
        # Usar PostgreSQL en producción
        try:
            conn = psycopg2.connect(DATABASE_URL)
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
    else:
        # Modo SQLite
        cursor.execute('''
            INSERT OR REPLACE INTO torneos (id, nombre, categoria, fecha_inicio, fecha_fin, fase, datos_playoffs)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (torneo.id, torneo.nombre, torneo.categoria, torneo.fecha_inicio, torneo.fecha_fin, torneo.fase, json.dumps(torneo.playoffs)))
    
    conn.commit()
    conn.close()
    print(f"✅ Torneo '{torneo.nombre}' guardado correctamente")

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
                id_torneo=row[0],
                nombre=row[1],
                categoria=row[2],
                fecha_inicio=row[3],
                fecha_fin=row[4]
            )
            torneo.fase = row[5]
            if row[6]:
                torneo.playoffs = json.loads(row[6])
        else:
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
        
        torneos[torneo.id] = torneo
    
    conn.close()
    print(f"✅ Total: {len(torneos)} torneo(s) cargados correctamente")
    return torneos

def migrar_datos():
    """Función para migrar datos existentes (ejecutar una vez)"""
    print("🔄 Iniciando migración de datos...")
    print("✅ Migración completada")
