# No te flipes — V6

Cambios de esta versión:

- Al lanzar un No te flipes, el backend devuelve una revelación puntual de la penalización seleccionada.
- El frontend muestra una ruleta animada y, al terminar, enseña nombre, descripción, categoría, penalización y partidas de gracia.
- El endpoint `GET /api/handicaps/grants/mine/` sigue sin revelar la definición mientras el poder está pendiente.
- La clasificación, cuando la consulta un administrador, carga los handicaps y premios completos y permite ver en el tooltip todas las penalizaciones del jugador, incluidas las ya canjeadas.
- El perfil del jugador mantiene la separación entre penalizaciones pendientes y canjeadas.
