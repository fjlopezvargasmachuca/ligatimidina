# No te flipes — actualización v5

Cambios incluidos:

- El perfil del jugador muestra las penalizaciones de No te flipes pendientes de canjear.
- El perfil permite consultar las penalizaciones ya canjeadas en un historial desplegable.
- La clasificación mantiene los iconos de estado.
- Los tooltips de los iconos se renderizan fuera de la tabla para evitar que `overflow-x: auto` los recorte.
- El panel de administración muestra si cada penalización ha sido canjeada y, cuando existe, la fecha del canje.
- Se conserva el secreto del tipo de No te flipes para el jugador que lo lanza.

Para instalar:

```powershell
cd C:\Users\fjavi\Documents\ligatimidina\frontend
npm install
npm run dev
```

Este frontend espera que el backend exponga en `/api/handicaps/players/<player_id>/` el estado completo de los handicaps del propio jugador y que los administradores puedan consultar todos los handicaps con `used`, `used_at` y `used_match_id`.
