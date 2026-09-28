# Frontend corregido — No te flipes

Esta versión corrige la integración real de la aplicación que se sirve desde `src/App.jsx`.

## Cambios

- La clasificación real ahora pinta `status_icons` procedentes de `/api/league/standings/`.
- `NO_TE_FLIPES_AVAILABLE` se muestra con ⚡.
- `HANDICAP_ACTIVE` se muestra con ⛓.
- `PENALTY_ACTIVE` se muestra con !.
- Si hay más de uno del mismo estado, aparece el contador.
- El tooltip usa `label`, `description` y `remaining_games` que entrega el backend.
- No se inventa ni se expone en React el tipo secreto de una penalización: se pinta únicamente lo que el backend autoriza para ese usuario.
- La tarjeta de No te flipes aparece en la clasificación y en Mi perfil.
- La tarjeta ya no hace una petición innecesaria a `/accounts/me/`; recibe el ID del usuario autenticado desde `App.jsx`.
- El número de No te flipes disponibles se muestra correctamente (por ejemplo, `2 disponibles`).
- Se añade el favicon SVG para evitar el 404 de `/favicon.ico`.
- Se conserva la API y el backend existentes.

## Instalación

Desde `frontend/`:

```powershell
npm install
npm run dev
```

No copies `node_modules` ni `dist` de la versión anterior. El ZIP contiene el código fuente y `package-lock.json`, pero no las dependencias instaladas.

## Comprobación

La respuesta de `/api/league/standings/` debe contener `status_icons`. La clasificación real (`LeagueView` dentro de `src/App.jsx`) es la que ahora los renderiza.
