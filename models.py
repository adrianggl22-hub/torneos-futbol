# models.py
from datetime import datetime
from typing import Dict, List, Optional
import json

class Jugador:
    """Clase para representar un jugador"""
    def __init__(self, id: int, nombre: str, equipo_id: int, numero: int = 0, posicion: str = "",
                 nombre_abreviado: str = "", documento: str = "", fecha_nacimiento: str = "",
                 telefono: str = "", email: str = "", altura: int = None, peso: float = None,
                 pierna_habil: str = "", goles: int = 0, asistencias: int = 0,
                 tarjetas_amarillas: int = 0, tarjetas_rojas: int = 0,
                 partidos_jugados: int = 0, minutos_jugados: int = 0):
        self.id = id
        self.nombre = nombre
        self.equipo_id = equipo_id
        self.numero = numero
        self.posicion = posicion
        self.nombre_abreviado = nombre_abreviado
        self.documento = documento
        self.fecha_nacimiento = fecha_nacimiento
        self.telefono = telefono
        self.email = email
        self.altura = altura
        self.peso = peso
        self.pierna_habil = pierna_habil
        self.goles = goles
        self.asistencias = asistencias
        self.tarjetas_amarillas = tarjetas_amarillas
        self.tarjetas_rojas = tarjetas_rojas
        self.partidos_jugados = partidos_jugados
        self.minutos_jugados = minutos_jugados
    
    def to_dict(self) -> dict:
        """Convierte el jugador a diccionario para JSON"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'equipo_id': self.equipo_id,
            'numero': self.numero,
            'posicion': self.posicion,
            'nombre_abreviado': self.nombre_abreviado,
            'documento': self.documento,
            'fecha_nacimiento': self.fecha_nacimiento,
            'telefono': self.telefono,
            'email': self.email,
            'altura': self.altura,
            'peso': self.peso,
            'pierna_habil': self.pierna_habil,
            'goles': self.goles,
            'asistencias': self.asistencias,
            'tarjetas_amarillas': self.tarjetas_amarillas,
            'tarjetas_rojas': self.tarjetas_rojas,
            'partidos_jugados': self.partidos_jugados,
            'minutos_jugados': self.minutos_jugados
        }


class MiembroCuerpoTecnico:
    """Clase para representar un miembro del cuerpo técnico"""
    def __init__(self, id: int, nombre: str, equipo_id: int, rol: str = "",
                 documento: str = "", telefono: str = "", email: str = "",
                 fecha_nacimiento: str = "", especialidad: str = "", experiencia: str = ""):
        self.id = id
        self.nombre = nombre
        self.equipo_id = equipo_id
        self.rol = rol
        self.documento = documento
        self.telefono = telefono
        self.email = email
        self.fecha_nacimiento = fecha_nacimiento
        self.especialidad = especialidad
        self.experiencia = experiencia
    
    def to_dict(self) -> dict:
        """Convierte el miembro a diccionario para JSON"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'equipo_id': self.equipo_id,
            'rol': self.rol,
            'documento': self.documento,
            'telefono': self.telefono,
            'email': self.email,
            'fecha_nacimiento': self.fecha_nacimiento,
            'especialidad': self.especialidad,
            'experiencia': self.experiencia
        }


class Equipo:
    """Clase para representar un equipo"""
    def __init__(self, id_equipo: int, nombre: str, entrenador: str = "",
                 anio_fundacion: int = None, estadio: str = ""):
        self.id = id_equipo
        self.nombre = nombre
        self.entrenador = entrenador
        self.anio_fundacion = anio_fundacion
        self.estadio = estadio
        self.jugadores: Dict[int, Jugador] = {}
        self.cuerpo_tecnico: Dict[int, MiembroCuerpoTecnico] = {}
        
        # Estadísticas
        self.puntos = 0
        self.partidos_jugados = 0
        self.ganados = 0
        self.empatados = 0
        self.perdidos = 0
        self.goles_favor = 0
        self.goles_contra = 0
        self.diferencia_goles = 0
        
        # IDs autoincrementales
        self.proximo_id_jugador = 1
        self.proximo_id_cuerpo_tecnico = 1
    
    def agregar_jugador(self, nombre: str, numero: int, posicion: str,
                        nombre_abreviado: str = "", documento: str = "",
                        fecha_nacimiento: str = "", telefono: str = "",
                        email: str = "", altura: int = None, peso: float = None,
                        pierna_habil: str = "") -> bool:
        """Agrega un jugador al equipo"""
        # Verificar que el número no esté en uso
        for jugador in self.jugadores.values():
            if jugador.numero == numero:
                return False
        
        jugador = Jugador(
            id=self.proximo_id_jugador,
            nombre=nombre,
            equipo_id=self.id,
            numero=numero,
            posicion=posicion,
            nombre_abreviado=nombre_abreviado,
            documento=documento,
            fecha_nacimiento=fecha_nacimiento,
            telefono=telefono,
            email=email,
            altura=altura,
            peso=peso,
            pierna_habil=pierna_habil
        )
        self.jugadores[jugador.id] = jugador
        self.proximo_id_jugador += 1
        return True
    
    def eliminar_jugador(self, jugador_id: int) -> bool:
        """Elimina un jugador del equipo"""
        if jugador_id in self.jugadores:
            del self.jugadores[jugador_id]
            return True
        return False
    
    def agregar_miembro_cuerpo_tecnico(self, nombre: str, rol: str,
                                        documento: str = "", telefono: str = "",
                                        email: str = "", fecha_nacimiento: str = "",
                                        especialidad: str = "", experiencia: str = "") -> bool:
        """Agrega un miembro al cuerpo técnico"""
        miembro = MiembroCuerpoTecnico(
            id=self.proximo_id_cuerpo_tecnico,
            nombre=nombre,
            equipo_id=self.id,
            rol=rol,
            documento=documento,
            telefono=telefono,
            email=email,
            fecha_nacimiento=fecha_nacimiento,
            especialidad=especialidad,
            experiencia=experiencia
        )
        self.cuerpo_tecnico[miembro.id] = miembro
        self.proximo_id_cuerpo_tecnico += 1
        return True
    
    def eliminar_miembro_cuerpo_tecnico(self, miembro_id: int) -> bool:
        """Elimina un miembro del cuerpo técnico"""
        if miembro_id in self.cuerpo_tecnico:
            del self.cuerpo_tecnico[miembro_id]
            return True
        return False
    
    def actualizar_miembro_cuerpo_tecnico(self, miembro_id: int, datos: dict) -> bool:
        """Actualiza los datos de un miembro del cuerpo técnico"""
        if miembro_id in self.cuerpo_tecnico:
            miembro = self.cuerpo_tecnico[miembro_id]
            miembro.nombre = datos.get('nombre', miembro.nombre)
            miembro.rol = datos.get('rol', miembro.rol)
            miembro.documento = datos.get('documento', miembro.documento)
            miembro.telefono = datos.get('telefono', miembro.telefono)
            miembro.email = datos.get('email', miembro.email)
            miembro.fecha_nacimiento = datos.get('fecha_nacimiento', miembro.fecha_nacimiento)
            miembro.especialidad = datos.get('especialidad', miembro.especialidad)
            miembro.experiencia = datos.get('experiencia', miembro.experiencia)
            return True
        return False
    
    def to_dict(self) -> dict:
        """Convierte el equipo a diccionario para JSON"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'entrenador': self.entrenador,
            'anio_fundacion': self.anio_fundacion,
            'estadio': self.estadio,
            'jugadores': [j.to_dict() for j in self.jugadores.values()],
            'cuerpo_tecnico': [m.to_dict() for m in self.cuerpo_tecnico.values()],
            'estadisticas': {
                'puntos': self.puntos,
                'partidos_jugados': self.partidos_jugados,
                'ganados': self.ganados,
                'empatados': self.empatados,
                'perdidos': self.perdidos,
                'goles_favor': self.goles_favor,
                'goles_contra': self.goles_contra,
                'diferencia_goles': self.diferencia_goles
            }
        }


class Partido:
    """Clase para representar un partido"""
    def __init__(self, id_partido: int, id_local: int, id_visitante: int,
                 nombre_local: str, nombre_visitante: str, fecha: str = "",
                 hora: str = "", cancha: str = ""):
        self.id = id_partido
        self.id_local = id_local
        self.id_visitante = id_visitante
        self.nombre_local = nombre_local
        self.nombre_visitante = nombre_visitante
        self.fecha = fecha
        self.hora = hora
        self.cancha = cancha
        self.goles_local = 0
        self.goles_visitante = 0
        self.jugado = False
        self.goleadores_local = []
        self.goleadores_visitante = []
        self.amonestados_local = []
        self.amonestados_visitante = []
        self.informe_arbitral = {}
    
    def registrar_resultado(self, goles_local: int, goles_visitante: int,
                            goleadores_local: list = None, goleadores_visitante: list = None) -> None:
        """Registra el resultado del partido"""
        self.goles_local = goles_local
        self.goles_visitante = goles_visitante
        self.jugado = True
        if goleadores_local:
            self.goleadores_local = goleadores_local
        if goleadores_visitante:
            self.goleadores_visitante = goleadores_visitante
    
    def guardar_informe_arbitral(self, datos: dict) -> None:
        """Guarda el informe arbitral del partido"""
        self.informe_arbitral = datos
    
    def get_informe_arbitral(self) -> dict:
        """Obtiene el informe arbitral"""
        return self.informe_arbitral
    
    def to_dict(self) -> dict:
        """Convierte el partido a diccionario para JSON"""
        return {
            'id': self.id,
            'id_local': self.id_local,
            'id_visitante': self.id_visitante,
            'nombre_local': self.nombre_local,
            'nombre_visitante': self.nombre_visitante,
            'fecha': self.fecha,
            'hora': self.hora,
            'cancha': self.cancha,
            'goles_local': self.goles_local,
            'goles_visitante': self.goles_visitante,
            'jugado': self.jugado,
            'goleadores_local': self.goleadores_local,
            'goleadores_visitante': self.goleadores_visitante
        }


class Noticia:
    """Clase para representar una noticia"""
    def __init__(self, id: int, titulo: str, contenido: str, fecha: str = None,
                 tipo: str = "noticia", url_media: str = "", torneo_id: str = ""):
        self.id = id
        self.titulo = titulo
        self.contenido = contenido
        self.fecha = fecha or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.tipo = tipo
        self.url_media = url_media
        self.torneo_id = torneo_id
    
    def to_dict(self) -> dict:
        """Convierte la noticia a diccionario para JSON"""
        return {
            'id': self.id,
            'titulo': self.titulo,
            'contenido': self.contenido,
            'fecha': self.fecha,
            'tipo': self.tipo,
            'url_media': self.url_media,
            'torneo_id': self.torneo_id
        }


class Torneo:
    """Clase principal para gestionar un torneo"""
    def __init__(self, id_torneo: str, nombre: str, categoria: str = "Libre",
                 fecha_inicio: str = "", fecha_fin: str = ""):
        self.id = id_torneo
        self.nombre = nombre
        self.categoria = categoria
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.equipos: Dict[int, Equipo] = {}
        self.partidos: Dict[int, Partido] = {}
        self.noticias: Dict[int, Noticia] = {}
        self.fase = "liga"
        self.playoffs = {}
        
        # IDs autoincrementales
        self.proximo_id_equipo = 1
        self.proximo_id_partido = 1
        self.proximo_id_noticia = 1
    
    def agregar_equipo(self, nombre: str, entrenador: str = "",
                       anio_fundacion: int = None, estadio: str = "") -> bool:
        """Agrega un equipo al torneo"""
        # Verificar que no exista un equipo con el mismo nombre
        for equipo in self.equipos.values():
            if equipo.nombre.lower() == nombre.lower():
                return False
        
        equipo = Equipo(
            id_equipo=self.proximo_id_equipo,
            nombre=nombre,
            entrenador=entrenador,
            anio_fundacion=anio_fundacion,
            estadio=estadio
        )
        self.equipos[equipo.id] = equipo
        self.proximo_id_equipo += 1
        return True
    
    def eliminar_equipo(self, equipo_id: int) -> bool:
        """Elimina un equipo del torneo"""
        if equipo_id in self.equipos:
            # Eliminar partidos relacionados
            partidos_a_eliminar = []
            for partido in self.partidos.values():
                if partido.id_local == equipo_id or partido.id_visitante == equipo_id:
                    partidos_a_eliminar.append(partido.id)
            for pid in partidos_a_eliminar:
                del self.partidos[pid]
            
            del self.equipos[equipo_id]
            return True
        return False
    
    def agregar_equipo_formulario(self, datos: dict) -> bool:
        """Agrega un equipo desde el formulario de registro"""
        return self.agregar_equipo(
            nombre=datos['nombre'],
            entrenador=datos.get('entrenador', ''),
            anio_fundacion=datos.get('anio_fundacion'),
            estadio=datos.get('estadio', '')
        )
    
    def generar_fixture(self) -> None:
        """
        Genera el fixture del torneo (todos contra todos a DOS vueltas) con partidos INTERCALADOS.
        Para N equipos, se generan 2*(N-1) jornadas.
        Cada jornada tiene N/2 partidos (si N es par).
        Los partidos de ida y vuelta se intercalan para evitar rachas largas de local/visitante.
        """
        equipos_ids = list(self.equipos.keys())
        n = len(equipos_ids)
        
        if n < 2:
            return
        
        # Limpiar partidos existentes
        self.partidos.clear()
        self.proximo_id_partido = 1
        
        # Algoritmo round-robin (una sola vuelta)
        # Si el número de equipos es impar, agregamos un "descanso" (None)
        equipos_con_descanso = equipos_ids.copy()
        if n % 2 != 0:
            equipos_con_descanso.append(None)
            n += 1
        
        # Almacenar los partidos de la primera vuelta (ida)
        partidos_ida = []
        
        for ronda in range(n - 1):
            partidos_ronda = []
            for i in range(n // 2):
                local = equipos_con_descanso[i]
                visitante = equipos_con_descanso[n - 1 - i]
                
                if local is not None and visitante is not None:
                    partidos_ronda.append((local, visitante))
            
            partidos_ida.append(partidos_ronda)
            
            # Rotar equipos
            ultimo = equipos_con_descanso.pop()
            equipos_con_descanso.insert(1, ultimo)
        
        # Generar la segunda vuelta (vuelta) intercambiando localías
        partidos_vuelta = []
        for ronda in partidos_ida:
            partidos_ronda_vuelta = []
            for local, visitante in ronda:
                partidos_ronda_vuelta.append((visitante, local))
            partidos_vuelta.append(partidos_ronda_vuelta)
        
        # INTERCALAR los partidos: mezclar ida y vuelta para evitar rachas
        # Ejemplo: J1: ida, J2: vuelta, J3: ida, J4: vuelta, J5: ida, J6: vuelta...
        partidos_intercalados = []
        for i in range(len(partidos_ida)):
            partidos_intercalados.append(('ida', partidos_ida[i]))
            partidos_intercalados.append(('vuelta', partidos_vuelta[i]))
        
        # Crear los objetos Partido en orden intercalado
        for tipo, ronda in partidos_intercalados:
            for local_id, visitante_id in ronda:
                partido = Partido(
                    id_partido=self.proximo_id_partido,
                    id_local=local_id,
                    id_visitante=visitante_id,
                    nombre_local=self.equipos[local_id].nombre,
                    nombre_visitante=self.equipos[visitante_id].nombre
                )
                self.partidos[partido.id] = partido
                self.proximo_id_partido += 1
        
        total_jornadas = len(partidos_intercalados)
        partidos_por_jornada = len(partidos_intercalados[0][1]) if partidos_intercalados else 0
        
        # Verificar balance de localías
        local_count = {}
        for equipo_id in equipos_ids:
            local_count[equipo_id] = 0
        for partido in self.partidos.values():
            local_count[partido.id_local] += 1
        
        print(f"✅ Fixture generado con {len(self.partidos)} partidos (DOS vueltas INTERCALADAS)")
        print(f"   📅 {total_jornadas} jornadas")
        print(f"   ⚽ {partidos_por_jornada} partidos por jornada")
        print(f"   🏠 Partidos como local por equipo: { {self.equipos[eid].nombre: local_count[eid] for eid in equipos_ids} }")
        
        # Mostrar secuencia de local/visitante para verificar la alternancia
        if equipos_ids:
            equipo_ejemplo = equipos_ids[0]
            secuencia = []
            for partido in self.partidos.values():
                if partido.id_local == equipo_ejemplo:
                    secuencia.append("🏠 LOCAL")
                elif partido.id_visitante == equipo_ejemplo:
                    secuencia.append("✈️ VISITANTE")
            print(f"   🔄 Secuencia para {self.equipos[equipo_ejemplo].nombre}: {' -> '.join(secuencia)}")
    
    def registrar_resultado_completo(self, partido_id: int, goles_local: int,
                                      goles_visitante: int, goleadores: dict) -> bool:
        """Registra el resultado completo de un partido con goleadores"""
        if partido_id not in self.partidos:
            return False
        
        partido = self.partidos[partido_id]
        
        # Registrar el resultado
        partido.registrar_resultado(
            goles_local=goles_local,
            goles_visitante=goles_visitante,
            goleadores_local=goleadores.get('local', []),
            goleadores_visitante=goleadores.get('visitante', [])
        )
        
        # Actualizar estadísticas de los equipos
        equipo_local = self.equipos[partido.id_local]
        equipo_visitante = self.equipos[partido.id_visitante]
        
        equipo_local.partidos_jugados += 1
        equipo_visitante.partidos_jugados += 1
        
        equipo_local.goles_favor += goles_local
        equipo_local.goles_contra += goles_visitante
        equipo_visitante.goles_favor += goles_visitante
        equipo_visitante.goles_contra += goles_local
        
        if goles_local > goles_visitante:
            equipo_local.ganados += 1
            equipo_local.puntos += 3
            equipo_visitante.perdidos += 1
        elif goles_local < goles_visitante:
            equipo_visitante.ganados += 1
            equipo_visitante.puntos += 3
            equipo_local.perdidos += 1
        else:
            equipo_local.empatados += 1
            equipo_local.puntos += 1
            equipo_visitante.empatados += 1
            equipo_visitante.puntos += 1
        
        equipo_local.diferencia_goles = equipo_local.goles_favor - equipo_local.goles_contra
        equipo_visitante.diferencia_goles = equipo_visitante.goles_favor - equipo_visitante.goles_contra
        
        # Actualizar estadísticas de jugadores (goleadores)
        for gol in partido.goleadores_local:
            if isinstance(gol, dict):
                nombre_jugador = gol.get('nombre', '')
                for jugador in equipo_local.jugadores.values():
                    if jugador.nombre == nombre_jugador:
                        jugador.goles += 1
                        break
        
        for gol in partido.goleadores_visitante:
            if isinstance(gol, dict):
                nombre_jugador = gol.get('nombre', '')
                for jugador in equipo_visitante.jugadores.values():
                    if jugador.nombre == nombre_jugador:
                        jugador.goles += 1
                        break
        
        return True
    
    def get_partidos_pendientes(self) -> list:
        """Obtiene los partidos pendientes"""
        return [p.to_dict() for p in self.partidos.values() if not p.jugado]
    
    def get_partidos_jugados(self) -> list:
        """Obtiene los partidos jugados con detalles de goleadores"""
        partidos_jugados = []
        for p in self.partidos.values():
            if p.jugado:
                partido_dict = p.to_dict()
                partido_dict['goleadores_local'] = p.goleadores_local
                partido_dict['goleadores_visitante'] = p.goleadores_visitante
                partidos_jugados.append(partido_dict)
        return partidos_jugados
    
    def get_tabla_posiciones(self) -> list:
        """Obtiene la tabla de posiciones ordenada"""
        tabla = []
        for equipo in self.equipos.values():
            tabla.append({
                'id': equipo.id,
                'nombre': equipo.nombre,
                'pj': equipo.partidos_jugados,
                'g': equipo.ganados,
                'e': equipo.empatados,
                'p': equipo.perdidos,
                'gf': equipo.goles_favor,
                'gc': equipo.goles_contra,
                'dg': equipo.diferencia_goles,
                'pts': equipo.puntos
            })
        
        # Ordenar por puntos, luego diferencia de goles, luego goles a favor
        tabla.sort(key=lambda x: (-x['pts'], -x['dg'], -x['gf']))
        return tabla
    
    def get_ranking_goleadores(self, limite: int = 15) -> list:
        """Obtiene el ranking de goleadores del torneo"""
        goleadores = []
        
        for equipo in self.equipos.values():
            for jugador in equipo.jugadores.values():
                if jugador.goles > 0:
                    goleadores.append({
                        'id': jugador.id,
                        'nombre': jugador.nombre,
                        'nombre_abreviado': jugador.nombre_abreviado,
                        'numero': jugador.numero,
                        'goles': jugador.goles,
                        'equipo': equipo.nombre,
                        'equipo_id': equipo.id
                    })
        
        goleadores.sort(key=lambda x: -x['goles'])
        return goleadores[:limite]
    
    def get_resumen_partido(self, partido_id: int) -> dict:
        """Obtiene el resumen detallado de un partido"""
        if partido_id not in self.partidos:
            return None
        
        partido = self.partidos[partido_id]
        
        # Obtener goleadores con nombres
        goleadores_local = []
        for gol_nombre in partido.goleadores_local:
            # Buscar si el nombre tiene minuto
            if isinstance(gol_nombre, dict):
                goleadores_local.append(gol_nombre)
            else:
                goleadores_local.append({'nombre': gol_nombre, 'minuto': ''})
        
        goleadores_visitante = []
        for gol_nombre in partido.goleadores_visitante:
            if isinstance(gol_nombre, dict):
                goleadores_visitante.append(gol_nombre)
            else:
                goleadores_visitante.append({'nombre': gol_nombre, 'minuto': ''})
        
        return {
            'partido': partido.to_dict(),
            'goleadores': {
                'local': goleadores_local,
                'visitante': goleadores_visitante
            }
        }
    
    def agregar_noticia(self, titulo: str, contenido: str, tipo: str = "noticia",
                        url_media: str = "") -> Noticia:
        """Agrega una noticia al torneo"""
        noticia = Noticia(
            id=self.proximo_id_noticia,
            titulo=titulo,
            contenido=contenido,
            tipo=tipo,
            url_media=url_media,
            torneo_id=self.id
        )
        self.noticias[noticia.id] = noticia
        self.proximo_id_noticia += 1
        return noticia
    
    def generar_playoffs(self) -> None:
        """
        Genera los playoffs después de la liga.
        Clasifican los 4 primeros equipos de la tabla.
        Semifinales: 1º vs 4º y 2º vs 3º (ida y vuelta)
        Final: Ganadores de semifinales (un solo partido)
        """
        tabla = self.get_tabla_posiciones()
        if len(tabla) < 4:
            print("⚠️ No hay suficientes equipos para playoffs (mínimo 4)")
            return
        
        # Tomar los 4 primeros equipos
        primero = tabla[0]
        segundo = tabla[1]
        tercero = tabla[2]
        cuarto = tabla[3]
        
        self.fase = "playoffs"
        self.playoffs = {
            'clasificados': [
                {'posicion': 1, 'equipo_id': primero['id'], 'nombre': primero['nombre'], 'puntos': primero['pts']},
                {'posicion': 2, 'equipo_id': segundo['id'], 'nombre': segundo['nombre'], 'puntos': segundo['pts']},
                {'posicion': 3, 'equipo_id': tercero['id'], 'nombre': tercero['nombre'], 'puntos': tercero['pts']},
                {'posicion': 4, 'equipo_id': cuarto['id'], 'nombre': cuarto['nombre'], 'puntos': cuarto['pts']}
            ],
            'semifinales': {
                'llave1': {
                    'equipo1': {'id': primero['id'], 'nombre': primero['nombre'], 'goles': 0},
                    'equipo2': {'id': cuarto['id'], 'nombre': cuarto['nombre'], 'goles': 0},
                    'partido_ida': None,
                    'partido_vuelta': None,
                    'jugado': False,
                    'ganador': None,
                    'ganador_nombre': None,
                    'goles_eq1': 0,
                    'goles_eq2': 0
                },
                'llave2': {
                    'equipo1': {'id': segundo['id'], 'nombre': segundo['nombre'], 'goles': 0},
                    'equipo2': {'id': tercero['id'], 'nombre': tercero['nombre'], 'goles': 0},
                    'partido_ida': None,
                    'partido_vuelta': None,
                    'jugado': False,
                    'ganador': None,
                    'ganador_nombre': None,
                    'goles_eq1': 0,
                    'goles_eq2': 0
                }
            },
            'final': {
                'equipo1': None,
                'equipo2': None,
                'partido': None,
                'jugado': False,
                'campeon': None,
                'campeon_nombre': None
            }
        }
        
        print(f"✅ Playoffs generados")
        print(f"   🏆 1º {primero['nombre']} vs 4º {cuarto['nombre']}")
        print(f"   🏆 2º {segundo['nombre']} vs 3º {tercero['nombre']}")
    
    def generar_partidos_semifinales(self) -> None:
        """Genera los partidos de ida y vuelta de las semifinales"""
        if self.fase != 'playoffs' or not self.playoffs:
            return
        
        # Limpiar partidos de playoffs existentes (los que empiezan con SF_ o FINAL)
        self.partidos = {k: v for k, v in self.partidos.items() 
                        if not (isinstance(k, str) and (k.startswith('SF_') or k == 'FINAL'))}
        
        # Generar partidos de semifinales
        # Llave 1: 1º vs 4º
        llave1 = self.playoffs['semifinales']['llave1']
        equipo1_id = llave1['equipo1']['id']
        equipo2_id = llave1['equipo2']['id']
        
        # Partido de ida: equipo1 vs equipo2
        partido_ida_llave1 = Partido(
            id_partido=self.proximo_id_partido,
            id_local=equipo1_id,
            id_visitante=equipo2_id,
            nombre_local=self.equipos[equipo1_id].nombre,
            nombre_visitante=self.equipos[equipo2_id].nombre
        )
        self.partidos['SF1_IDA'] = partido_ida_llave1
        self.proximo_id_partido += 1
        
        # Partido de vuelta: equipo2 vs equipo1
        partido_vuelta_llave1 = Partido(
            id_partido=self.proximo_id_partido,
            id_local=equipo2_id,
            id_visitante=equipo1_id,
            nombre_local=self.equipos[equipo2_id].nombre,
            nombre_visitante=self.equipos[equipo1_id].nombre
        )
        self.partidos['SF1_VUELTA'] = partido_vuelta_llave1
        self.proximo_id_partido += 1
        
        # Llave 2: 2º vs 3º
        llave2 = self.playoffs['semifinales']['llave2']
        equipo1_id = llave2['equipo1']['id']
        equipo2_id = llave2['equipo2']['id']
        
        # Partido de ida: equipo1 vs equipo2
        partido_ida_llave2 = Partido(
            id_partido=self.proximo_id_partido,
            id_local=equipo1_id,
            id_visitante=equipo2_id,
            nombre_local=self.equipos[equipo1_id].nombre,
            nombre_visitante=self.equipos[equipo2_id].nombre
        )
        self.partidos['SF2_IDA'] = partido_ida_llave2
        self.proximo_id_partido += 1
        
        # Partido de vuelta: equipo2 vs equipo1
        partido_vuelta_llave2 = Partido(
            id_partido=self.proximo_id_partido,
            id_local=equipo2_id,
            id_visitante=equipo1_id,
            nombre_local=self.equipos[equipo2_id].nombre,
            nombre_visitante=self.equipos[equipo1_id].nombre
        )
        self.partidos['SF2_VUELTA'] = partido_vuelta_llave2
        self.proximo_id_partido += 1
        
        print(f"✅ Partidos de semifinales generados (ida y vuelta)")
    
    def registrar_resultado_semifinal(self, llave: str, partido_tipo: str, goles_local: int, goles_visitante: int) -> bool:
        """
        Registra el resultado de un partido de semifinal
        llave: 'llave1' o 'llave2'
        partido_tipo: 'ida' o 'vuelta'
        """
        partido_key = f'SF1_{partido_tipo.upper()}' if llave == 'llave1' else f'SF2_{partido_tipo.upper()}'
        
        if partido_key not in self.partidos:
            return False
        
        partido = self.partidos[partido_key]
        partido.registrar_resultado(goles_local, goles_visitante)
        
        # Actualizar el playoff
        if llave == 'llave1':
            self.playoffs['semifinales']['llave1'][f'partido_{partido_tipo}'] = {
                'goles_local': goles_local,
                'goles_visitante': goles_visitante
            }
        else:
            self.playoffs['semifinales']['llave2'][f'partido_{partido_tipo}'] = {
                'goles_local': goles_local,
                'goles_visitante': goles_visitante
            }
        
        # Verificar si ya se completó la llave
        self._verificar_ganador_semifinal(llave)
        
        return True
    
    def _verificar_ganador_semifinal(self, llave: str) -> None:
        """Verifica si una semifinal ya tiene ganador y actualiza el playoff"""
        data = self.playoffs['semifinales'][llave]
        
        if data['partido_ida'] and data['partido_vuelta']:
            # Determinar qué equipo es local en cada partido
            if llave == 'llave1':
                partido_ida = self.partidos['SF1_IDA']
                partido_vuelta = self.partidos['SF1_VUELTA']
            else:
                partido_ida = self.partidos['SF2_IDA']
                partido_vuelta = self.partidos['SF2_VUELTA']
            
            # Calcular resultado global
            goles_eq1 = 0
            goles_eq2 = 0
            
            # Partido ida
            if partido_ida.id_local == data['equipo1']['id']:
                goles_eq1 += partido_ida.goles_local
                goles_eq2 += partido_ida.goles_visitante
            else:
                goles_eq1 += partido_ida.goles_visitante
                goles_eq2 += partido_ida.goles_local
            
            # Partido vuelta
            if partido_vuelta.id_local == data['equipo1']['id']:
                goles_eq1 += partido_vuelta.goles_local
                goles_eq2 += partido_vuelta.goles_visitante
            else:
                goles_eq1 += partido_vuelta.goles_visitante
                goles_eq2 += partido_vuelta.goles_local
            
            data['goles_eq1'] = goles_eq1
            data['goles_eq2'] = goles_eq2
            data['jugado'] = True
            
            if goles_eq1 > goles_eq2:
                data['ganador'] = data['equipo1']['id']
                data['ganador_nombre'] = data['equipo1']['nombre']
            elif goles_eq2 > goles_eq1:
                data['ganador'] = data['equipo2']['id']
                data['ganador_nombre'] = data['equipo2']['nombre']
            else:
                # En caso de empate global, gana el que mejor se desempeñó fuera de casa
                goles_visitante_eq1 = 0
                goles_visitante_eq2 = 0
                
                if partido_ida.id_visitante == data['equipo1']['id']:
                    goles_visitante_eq1 += partido_ida.goles_visitante
                else:
                    goles_visitante_eq2 += partido_ida.goles_visitante
                
                if partido_vuelta.id_visitante == data['equipo1']['id']:
                    goles_visitante_eq1 += partido_vuelta.goles_visitante
                else:
                    goles_visitante_eq2 += partido_vuelta.goles_visitante
                
                if goles_visitante_eq1 > goles_visitante_eq2:
                    data['ganador'] = data['equipo1']['id']
                    data['ganador_nombre'] = data['equipo1']['nombre']
                else:
                    data['ganador'] = data['equipo2']['id']
                    data['ganador_nombre'] = data['equipo2']['nombre']
            
            # Actualizar la final si ambas llaves tienen ganador
            self._actualizar_final()
    
    def _actualizar_final(self) -> None:
        """Actualiza la final con los ganadores de las semifinales"""
        ganador1 = self.playoffs['semifinales']['llave1'].get('ganador')
        ganador2 = self.playoffs['semifinales']['llave2'].get('ganador')
        
        if ganador1 and ganador2:
            self.playoffs['final']['equipo1'] = {
                'id': ganador1,
                'nombre': self.equipos[ganador1].nombre
            }
            self.playoffs['final']['equipo2'] = {
                'id': ganador2,
                'nombre': self.equipos[ganador2].nombre
            }
            
            # Limpiar partido final existente
            if 'FINAL' in self.partidos:
                del self.partidos['FINAL']
            
            # Generar partido final
            partido_final = Partido(
                id_partido=self.proximo_id_partido,
                id_local=ganador1,
                id_visitante=ganador2,
                nombre_local=self.equipos[ganador1].nombre,
                nombre_visitante=self.equipos[ganador2].nombre
            )
            self.partidos['FINAL'] = partido_final
            self.proximo_id_partido += 1
            
            print(f"✅ Final generada: {self.equipos[ganador1].nombre} vs {self.equipos[ganador2].nombre}")
    
    def registrar_resultado_final(self, goles_local: int, goles_visitante: int) -> bool:
        """Registra el resultado de la final"""
        if 'FINAL' not in self.partidos:
            return False
        
        partido = self.partidos['FINAL']
        partido.registrar_resultado(goles_local, goles_visitante)
        
        self.playoffs['final']['partido'] = {
            'goles_local': goles_local,
            'goles_visitante': goles_visitante
        }
        self.playoffs['final']['jugado'] = True
        
        # Determinar campeón
        if goles_local > goles_visitante:
            self.playoffs['final']['campeon'] = self.playoffs['final']['equipo1']['id']
            self.playoffs['final']['campeon_nombre'] = self.playoffs['final']['equipo1']['nombre']
        elif goles_visitante > goles_local:
            self.playoffs['final']['campeon'] = self.playoffs['final']['equipo2']['id']
            self.playoffs['final']['campeon_nombre'] = self.playoffs['final']['equipo2']['nombre']
        else:
            # En caso de empate, se define en penales
            self.playoffs['final']['empate'] = True
            self.playoffs['final']['campeon_nombre'] = f"Empate - Definir en penales"
        
        self.fase = "finalizado"
        
        print(f"🏆 CAMPEÓN: {self.playoffs['final']['campeon_nombre']}")
        
        return True
    
    def get_info_playoffs(self) -> dict:
        """Obtiene la información completa de los playoffs"""
        return self.playoffs
    
    def to_dict(self) -> dict:
        """Convierte el torneo a diccionario para JSON"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'categoria': self.categoria,
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            'equipos': [e.to_dict() for e in self.equipos.values()],
            'partidos': {k: p.to_dict() if isinstance(p, Partido) else p for k, p in self.partidos.items()},
            'noticias': [n.to_dict() for n in self.noticias.values()],
            'fase': self.fase,
            'playoffs': self.playoffs
        }