Documento de Requisitos del Sistema (SRS)
Liga Timidina — Liga semanal de Magic: The Gathering Commander

Documento maestro para continuidad del desarrollo
Fecha: 28/09/2026

1. Propósito del documento

Este documento reúne la especificación funcional, reglas de negocio, arquitectura, modelo conceptual, privacidad, API, frontend, administración, pruebas y estado actual del proyecto Liga Timidina. Su objetivo es servir como contexto maestro para abrir una nueva conversación de desarrollo sin perder decisiones tomadas durante la implementación.

2. Visión general del producto

Liga Timidina es una aplicación web para gestionar una liga semanal de Magic: The Gathering Commander. Los jugadores registran sus mazos, participan en partidas semanales, obtienen puntos según reglas configurables y pueden recibir poderes/penalizaciones especiales denominados “No te flipes”. Los administradores tienen autoridad sobre resultados, puntuación, eventos, penalizaciones y auditoría.

2.1 Objetivos principales

Gestionar jugadores, perfiles, mazos y partidas de una liga Commander.

Mantener una clasificación por temporada y jornada.

Registrar resultados históricos y conservar snapshots suficientes para auditoría.

Configurar reglas de puntuación desde administración.

Gestionar eventos semanales y reglas especiales de juego.

Integrar DeckCheck para comprobar/consultar información de mazos.

Implementar el sistema “No te flipes” con poderes, penalizaciones, gracia, canje y auditoría.

Mantener separación estricta entre información pública, información del propio jugador e información exclusiva del administrador.

3. Alcance funcional

3.1 Jugadores

Registro e inicio de sesión.

Recuperación/cambio de contraseña.

Perfil con nombre de usuario, nombre visible y avatar.

Registro y gestión de mazos Commander.

Consulta de mazos de otros jugadores.

Consulta de clasificación y jornada actual.

Consulta de sus propias penalizaciones/handicaps y poderes disponibles.

Uso de un No te flipes disponible contra otro jugador.

Visualización del detalle de las penalizaciones que le han sido asignadas.

3.2 Liga y clasificación

Temporadas y jornadas semanales.

Clasificación acumulada por temporada.

Posición, puntos, victorias, partidas, eliminaciones y semanas.

Despliegue/consulta de resultados y mazos por jornada según la interfaz.

Indicadores visuales de estados especiales del jugador.

La clasificación debe incluir jugadores relevantes aunque todavía no tengan partidas, cuando su estado de liga lo justifique (por ejemplo, un jugador con No te flipes disponible).

3.3 Partidas

Una partida pertenece a una jornada y temporada.

Tiene administrador responsable, fecha/hora, notas y estado abierta/cerrada.

Cada MatchPlayer registra jugador, mazo, posición inicial/final, participación en evento, primera partida con el mazo, concesión, penalización de concesión, puntos extra y puntos calculados.

Las eliminaciones registran killer, víctima, turno y si fue la primera eliminación.

Al cerrar una partida se valida la integridad y se calcula la puntuación.

3.4 Eventos semanales

Los eventos pueden representar reglas especiales como:

Archenemy.

Planechase/Chaos.

2v2.

Turnos de 3 minutos y pérdida de vidas por overtime.

Cambios en vida inicial, daño de comandante o umbral de veneno.

Revelar la carta superior.

Manos abiertas.

Atacar solamente a izquierda/derecha.

Todos empiezan con un Treasure.

Empezar con dos tierras básicas.

Otros modificadores configurables que pueda necesitar la liga.

4. Reglas de puntuación

La puntuación debe ser configurable por temporada mediante ScoringRule.

WIN — victoria / primer puesto.

SECOND_PLACE — segundo puesto.

THIRD_PLACE — tercer puesto.

ELIMINATION — puntos por eliminación.

FIRST_ELIMINATION — bonificación por primera eliminación.

FIRST_DECK_PLAY — primera vez que se juega ese mazo.

ORIGINAL_DECK — mazo marcado como original y validado por administración.

WEEKLY_EVENT — participación/resultado asociado al evento semanal.

CONCESSION — penalización por concesión.

EXTRA_POINTS — puntos extraordinarios introducidos por administración con motivo obligatorio.

ScoringService calcula los puntos de cada MatchPlayer y los guarda. Los handicaps/penalizaciones pueden modificar la puntuación mediante el servicio correspondiente. RankingService agrega los resultados almacenados y aplica los ajustes que correspondan.

5. Autoridad administrativa

La administración es la autoridad final para resultados, puntuaciones, eventos, penalizaciones, log/auditoría y correcciones históricas.

Solo administración puede cerrar partidas.

Solo administración puede modificar resultados sensibles.

Solo administración puede conceder No te flipes.

Solo administración puede crear/configurar penalizaciones.

Administración puede consultar todas las penalizaciones y su estado.

La eliminación de partidas cerradas requiere privilegios administrativos y confirmación explícita.

Las eliminaciones históricas deben reconstruir anchors de handicaps afectados y recalcular la temporada.

6. Sistema “No te flipes”

6.1 Concepto

“No te flipes” no es una penalización directa aplicada automáticamente. Es un poder que un jugador puede recibir y utilizar posteriormente contra otro jugador. El jugador que posee el poder sabe que dispone de él, pero no debe conocer de antemano qué penalización contiene.

6.2 Flujo

Un administrador concede uno o más poderes No te flipes a un jugador.

El poder queda disponible para el titular.

El titular selecciona a otro jugador como objetivo.

El titular no puede seleccionarse a sí mismo.

Al pulsar Lanzar, el backend realiza el sorteo real de la penalización.

La penalización seleccionada se crea/asigna al objetivo.

El poder queda consumido.

La respuesta del lanzamiento permite al lanzador conocer qué penalización acaba de lanzar.

La ruleta del frontend anima el resultado, pero no decide el resultado.

6.3 Privacidad

Regla crítica:

Antes del lanzamiento, el titular del poder NO puede consultar nombre, descripción, categoría, puntos, gracia o parámetros de la penalización.

Los demás jugadores tampoco deben recibir esos datos de una penalización ajena.

El jugador objetivo sí puede consultar el detalle de la penalización que tiene que cumplir.

El administrador puede consultar todas las penalizaciones y su historial.

La protección debe estar implementada en backend; ocultar campos solamente mediante React no es suficiente.

6.4 Aleatoriedad

La penalización se selecciona en el momento de lanzar el poder, no cuando el administrador lo concede. Las penalizaciones activas participan según sus pesos/ratios. Dos penalizaciones con el mismo peso deben tener la misma probabilidad relativa.

Estado conocido de pruebas: la funcionalidad de handicap ya está funcionando correctamente en la instalación del usuario. Existe un test pendiente de ajustar porque actualmente espera pesos [1, 1] mientras el catálogo real está proporcionando [60, 60]. La lógica funcional observada es correcta; el test debe reflejar la semántica real de pesos configurables.

6.5 Ruleta

Debe ser claramente visible y bastante más grande que la versión inicial.

Cada porción debe representar una penalización distinta disponible para el sorteo.

El nombre de la penalización debe poder leerse mientras gira.

El giro debe ser suficientemente lento al aproximarse al resultado final para permitir leer las últimas opciones.

Debe haber desaceleración progresiva (ease-out) y una parada inequívoca.

El resultado de la ruleta debe coincidir exactamente con el resultado elegido por backend.

Tras terminar, debe mostrar claramente la penalización lanzada, el objetivo y la información que el lanzador está autorizado a conocer.

7. Gracia y canje de handicaps

Cada definición de handicap tiene un número de partidas de gracia. Por ejemplo, con gracia 3, las partidas 1, 2 y 3 no reciben la penalización; desde la cuarta partida se aplica el penalty_points configurado mientras el handicap siga sin canjear.

El perfil del jugador debe mostrar los handicaps que tiene pendientes de canjear.

Debe mostrar cuántas partidas le quedan de gracia.

Debe mostrar los handicaps ya canjeados como historial.

El canje de un handicap detiene sus futuras penalizaciones.

Solo se puede consumir un handicap por MatchPlayer/partida.

Un handicap debe pertenecer al jugador y temporada correctos.

No se puede consumir en una partida cerrada o jornada cerrada.

8. Modelos principales

8.1 Accounts / Player

Player(AbstractUser)
- display_name
- avatar
- created_at
AUTH_USER_MODEL = accounts.Player

8.2 League

Season
- name
- start_date
- end_date
- active
- created_at

LeagueWeek
- season
- number
- date
- weekly_event
- closed
- created_at

ScoringRule
- season
- code
- name
- points
- description
- active

8.3 Matches

Match
- league_week
- administrator
- played_at
- notes
- closed
- created_at

MatchPlayer
- match
- player
- deck
- deck_name (snapshot)
- commander_name (snapshot)
- starting_position
- final_position
- first_play_of_deck
- participates_in_weekly_event
- conceded
- concession_penalty
- extra_points
- extra_points_reason
- points
- notes

Elimination
- match
- killer
- victim
- turn
- first_elimination
- created_at

8.4 Handicaps

El sistema contiene configuración de categorías, definiciones, asignaciones/handicaps, usos y poderes No te flipes (HandicapGrant). Los snapshots de configuración son importantes para conservar el significado histórico aunque una definición cambie posteriormente.

HandicapCategoryConfig: WEAK, MEDIUM, STRONG con pesos configurables.

HandicapDefinition: nombre, descripción, categoría, peso, gracia, puntos y parámetros de reversión.

Handicap: jugador, definición, temporada, administrador, anchor histórico, snapshots, rank/probabilidad y estado de uso.

HandicapUsage: relación uno-a-uno entre handicap y MatchPlayer, con recorded_by y fecha.

HandicapGrant: poder concedido al titular, consumible una vez y asociado al lanzamiento contra un objetivo.

9. Servicios y responsabilidades

ScoringService: calcular y guardar puntos de un MatchPlayer.

MatchService: cerrar partidas, validar posiciones/eliminaciones y recalcular.

RankingService: agregar clasificación y estadísticas.

HandicapService: asignar, consultar estado, seleccionar definiciones, consumir handicaps, calcular penalizaciones y recalcular temporadas.

Servicios de eventos: resolver reglas especiales semanales.

Servicios de integración DeckCheck: consultar/verificar información de mazos.

10. API y privacidad

10.1 Endpoints relevantes conocidos

GET  /api/accounts/me/
GET  /api/accounts/players/

GET  /api/league/standings/
GET  /api/league/current-week/

GET  /api/handicaps/categories/
GET  /api/handicaps/categories/<pk>/
GET  /api/handicaps/definitions/
POST /api/handicaps/definitions/create/
GET  /api/handicaps/definitions/<pk>/
GET  /api/handicaps/
POST /api/handicaps/create/
GET  /api/handicaps/<pk>/
GET  /api/handicaps/players/<player_id>/

GET  /api/handicaps/grants/mine/
POST /api/handicaps/grants/<id>/use/
GET  /api/handicaps/grants/

GET  /api/handicaps/matches/<match_pk>/players/<player_pk>/use/

10.2 Estado seguro de clasificación

La clasificación puede devolver indicadores como NO_TE_FLIPES_AVAILABLE, HANDICAP_ACTIVE y PENALTY_ACTIVE. El contenido sensible debe filtrarse según el usuario que consulta.

Titular/objetivo: puede recibir el detalle autorizado de su propio handicap.

Jugador tercero: solo recibe una descripción genérica del estado ajeno.

Administrador: puede recibir el detalle completo y el estado de canje.

11. Frontend

Frontend basado en React + Vite. La aplicación tiene una vista principal que muestra la liga/clasificación y una tarjeta NoTeFlipesCard integrada.

StandingsPage/LeagueView: clasificación, jornada y evento semanal.

StandingRow: jugador, estadísticas e iconos de estado.

NoTeFlipesCard: poderes disponibles, selección de objetivo y lanzamiento.

Perfil: handicaps pendientes, gracia restante y canjeados.

Panel administrativo: gestión de definiciones, poderes, penalizaciones y auditoría.

11.1 Indicadores visuales

⚡ — No te flipes disponible.

⛓ — handicap/penalización de No te flipes activa.

! — penalización administrativa.

Los iconos pueden mostrar contador si existen varias instancias.

Tooltip al hover y focus.

12. Administración y auditoría

Administración debe poder localizar cualquier handicap de cualquier jugador.

Debe saber si está usado/canjeado.

Debe conocer la partida donde se consumió.

Debe conocer quién lo concedió y, cuando corresponda, quién lo lanzó.

Debe poder comprobar que un jugador no está mintiendo sobre la penalización que tiene.

Debe existir suficiente historial para reconstruir estados después de borrar una partida histórica.

13. Eliminación histórica de partidas

Existe una operación administrativa para eliminar una partida cerrada, con jornada abierta y confirmación exacta “ELIMINAR PARTIDA”. Antes de recalcular la temporada se reconstruyen los anchors awarded_after_match de handicaps que apuntaban a la partida eliminada, buscando la partida cerrada anterior del mismo jugador.

14. Requisitos no funcionales

Responsive: escritorio y móvil.

Backend Django + Django REST Framework.

PostgreSQL como base de datos.

Python 3.13.x en el entorno conocido.

Frontend React/Vite.

Código organizado por apps y servicios.

No editar migraciones históricas ya aplicadas; generar nuevas migraciones.

Reglas sensibles deben validarse en backend.

Evitar filtrar información secreta aunque el frontend no la muestre.

Mantener tests automatizados de reglas de negocio.

Conservar snapshots históricos de datos que afecten a resultados.

15. Seguridad y privacidad

Autenticación para operaciones privadas.

Permisos administrativos para operaciones sensibles.

No confiar en flags del frontend para autorización.

No devolver secretos en endpoints públicos.

Un jugador no puede inspeccionar mediante API el tipo de handicap que otro jugador ha recibido.

El backend debe impedir autoobjetivos y doble consumo.

Las acciones administrativas deben quedar asociadas a un usuario.

16. Pruebas

Las pruebas de handicaps deben cubrir como mínimo:

Grace countdown.

Penalización desde la cuarta partida cuando grace=3.

Consumir handicap detiene penalizaciones futuras.

Solo un handicap por partida y jugador.

Asignación sin anchor usa la última partida cerrada.

Asignación sin partidas previas empieza correctamente.

Administración puede asignar.

El titular puede usar un grant.

No puede autoobjetivarse.

No puede usar un grant dos veces.

Otro jugador no puede usar el grant.

El lanzamiento selecciona desde el catálogo en el momento del lanzamiento.

La selección respeta pesos configurados.

La respuesta de lanzamiento revela solo al lanzador la penalización recién seleccionada.

El administrador puede auditar el uso.

El perfil refleja pendientes y canjeados.

La clasificación muestra estados sin filtrar secretos.

16.1 Incidencia de test conocida

En la ejecución más reciente de `python manage.py test handicaps` se obtuvieron 17 tests y 1 fallo. El fallo es test_launch_selects_from_weighted_catalog_at_launch_time: el test esperaba weights=[1,1], pero el catálogo real devuelve [60,60]. Esto debe resolverse alineando el test con la configuración de pesos real, no degradando el algoritmo de ponderación.

17. Estado actual del proyecto

La clasificación con iconos de No te flipes funciona.

El lanzamiento de No te flipes funciona.

El sistema de handicap funciona correctamente según las comprobaciones del usuario.

El perfil muestra los No te flipes disponibles y los handicaps que debe canjear, con gracia restante.

La ruleta visual funciona.

Pendiente: hacer la ruleta mucho más grande.

Pendiente: mostrar cada penalización en una porción de la ruleta.

Pendiente: hacer que el giro desacelere más en las posiciones finales para facilitar la lectura.

Pendiente: corregir el test de pesos [1,1] frente a [60,60].

Pendiente: asegurar que el administrador vea desde la clasificación el detalle completo de las penalizaciones al pasar el ratón.

Pendiente: continuar ampliando la auditoría administrativa.

18. Decisiones de diseño que NO deben perderse

No te flipes es un PODER, no una penalización directa.

El titular elige el objetivo, NO el tipo de penalización.

El tipo de penalización se sortea en el momento de lanzar.

El titular no debe conocer la penalización antes de lanzarla.

Después de lanzarla, el titular puede conocer qué penalización acaba de enviar.

El receptor puede conocer la penalización que tiene.

Administración puede conocer todas.

El backend decide siempre el resultado del sorteo.

La ruleta es una representación visual del resultado real, no el mecanismo de aleatoriedad.

No se deben modificar migraciones históricas.

Cuando se entregue un cambio de código importante, preferencia por archivos completos y tests.

19. Convenciones de trabajo para futuras conversaciones

Cuando se modifique un bloque importante, entregar el archivo completo que debe sustituirse.

Después del cambio, indicar los comandos exactos de migración y tests.

Agrupar comandos Git cuando proceda.

No repetir secretos, contraseñas ni SECRET_KEY.

Si falta un archivo para diagnosticar un problema, pedir el archivo concreto antes de inventar su contenido.

Priorizar soluciones funcionales y completas sobre parches parciales.

Mantener compatibilidad con el código existente siempre que no contradiga una regla de negocio.

Antes de cambiar backend por un problema visual, comprobar qué componente está realmente montado en la aplicación.

20. Próximos pasos recomendados

Corregir el único test fallido de pesos [1,1] vs [60,60].

Rediseñar la ruleta para mayor tamaño y mejor legibilidad.

Generar sectores proporcionalmente a los pesos reales y rotación final con easing.

Añadir prueba de que el resultado visual coincide con el resultado backend.

Completar vista administrativa de penalizaciones en clasificación.

Revisar perfil para separar claramente poderes disponibles de handicaps que debe canjear.

Continuar con las funciones generales de liga: eventos, mazos, DeckCheck, estadísticas, etc.

Preparar una batería de tests de regresión de toda la aplicación antes de cambios mayores.

21. Resumen para iniciar una nueva conversación

Proyecto: Liga Timidina. Stack: Django + DRF + PostgreSQL + React/Vite. El sistema gestiona una liga semanal de Commander, clasificación, partidas, mazos, eventos, puntuación configurable y un sistema privado de poderes/handicaps llamado No te flipes. La regla crítica es que el titular de un No te flipes puede elegir el objetivo pero no el tipo de penalización y no conoce su contenido antes del lanzamiento. El backend realiza el sorteo real en el momento de uso y la ruleta frontend únicamente anima ese resultado. Los jugadores pueden consultar sus propios handicaps, la administración puede auditar todos. El sistema de handicap ya funciona; queda ajustar un test de pesos y mejorar la ruleta y la visibilidad administrativa.