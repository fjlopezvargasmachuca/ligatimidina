# BracketMTG

**BracketMTG** es una aplicación web para analizar mazos de **Magic: The Gathering – Commander**. Permite pegar una lista de cartas, seleccionar el comandante y obtener una estimación del bracket, condiciones de victoria, curva de maná, precios, interacción, motores del mazo, combos y recomendaciones.

La aplicación acepta nombres de cartas tanto en **español como en inglés** y normaliza internamente las cartas al nombre Oracle en inglés antes de realizar el análisis.

🌐 **Aplicación:** https://www.bracketmtg.com/

---

## Funcionalidades

### Análisis rápido

Pensado para obtener una respuesta inmediata antes de una partida:

- Estimación del bracket del mazo.
- Detección del plan de juego.
- Condiciones de victoria.
- Detección básica de combos.
- Normalización automática de nombres de cartas.

### Análisis completo

Incluye el análisis rápido y añade:

- Curva de maná.
- CMC / valor de maná medio.
- Número de tierras.
- Ramp.
- Robo de cartas.
- Tutores.
- Interacción.
- Motores del mazo.
- Combos detectados.
- Game Changers.
- Legalidad e identidad de color.
- Recomendaciones basadas en EDHREC.
- Precio individual de las cartas.
- Precio total aproximado del mazo.
- Cobertura de precios disponibles en Scryfall.
- Diagnóstico general de construcción.

---

## Cartas en español e inglés

BracketMTG permite utilizar listas mezcladas en ambos idiomas.

Por ejemplo:

```text
1 Anillo solar
1 Arcane Signet
1 Espadas en guadañas
1 Island
```

Antes del análisis, las cartas reconocidas se convierten a su nombre Oracle en inglés:

```text
1 Sol Ring
1 Arcane Signet
1 Swords to Plowshares
1 Island
```

La normalización también se aplica a:

- Commander.
- Partner / segundo Commander.
- Background.
- Companion.

Los resultados y las exportaciones utilizan los nombres en inglés para mantener compatibilidad con Scryfall, EDHREC y el resto de fuentes utilizadas por el analizador.

---

## Reglas de conteo de Commander

El analizador tiene en cuenta la zona de mando al validar las 100 cartas del mazo.

Ejemplos válidos:

```text
99 cartas de biblioteca + 1 Commander = 100
```

```text
98 cartas de biblioteca + 2 Commanders con Partner = 100
```

```text
98 cartas de biblioteca + 1 Commander + 1 Background = 100
```

Si el Commander también aparece dentro de la lista pegada, BracketMTG detecta esa copia y evita contarla dos veces.

> Un Companion no sustituye una carta de las 100 del mazo.

---

## Exportación del mazo

Después del análisis se puede descargar la lista como archivo `.txt`.

La exportación separa la zona de mando de la biblioteca y utiliza nombres en inglés:

```text
Commander
1 Aragorn, King of Gondor

Deck
1 Sol Ring
1 Arcane Signet
1 Swords to Plowshares
...
```

---

## Fuentes de datos

BracketMTG utiliza principalmente:

- **Scryfall** para información de cartas, legalidad, imágenes, datos Oracle y precios.
- **EDHREC** para información relacionada con Commander y recomendaciones.
- Servicios internos de análisis para combos, consistencia, curva de maná y clasificación del mazo.

Para mejorar el rendimiento, las consultas a cartas se realizan por lotes siempre que es posible y determinados resultados se almacenan temporalmente en caché en el backend.

---

## Tecnologías

### Frontend

- React 19
- Vite 8
- JavaScript
- CSS responsive
- ESLint

### Backend

- Node.js 22+
- Express 5
- MongoDB
- Mongoose
- JWT
- bcrypt
- Nodemailer
- Axios

### Infraestructura

- **Vercel** — frontend.
- **Render** — API/backend.
- **MongoDB Atlas** — base de datos.
- **GitHub** — control de versiones y despliegue continuo.

---

## Estructura del proyecto

```text
bracketmtg/
├── mtg-frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
└── mtg-deck-analyzer/
    ├── config/
    ├── middleware/
    ├── models/
    ├── routes/
    ├── services/
    ├── utils/
    ├── server.js
    ├── test.js
    └── package.json
```

En producción, frontend y backend pueden mantenerse en repositorios GitHub independientes.

---

# Instalación local

## Requisitos

- Node.js **22.12 o superior**.
- npm.
- Una base de datos MongoDB.
- Cuenta de Gmail con contraseña de aplicación si se quiere utilizar recuperación de contraseña y formulario de contacto.

---

## Backend

```bash
cd mtg-deck-analyzer
npm ci
```

Crea un archivo `.env` tomando como referencia `.env.example`:

```env
NODE_ENV=development
PORT=3001

MONGO_URI=mongodb+srv://USER:PASSWORD@HOST/DATABASE
JWT_SECRET=replace-with-a-long-random-secret

EMAIL_USER=deckbracket@gmail.com
EMAIL_PASS=your-gmail-app-password
EMAIL_FROM=BracketMTG <deckbracket@gmail.com>
CONTACT_TO=deckbracket@gmail.com

CLIENT_URL=http://localhost:5173
ALLOWED_ORIGINS=http://localhost:5173
```

Inicia el backend:

```bash
npm run dev
```

O:

```bash
npm start
```

La API estará disponible normalmente en:

```text
http://localhost:3001
```

### Tests

```bash
npm test
```

Los tests incluyen comprobaciones del flujo del analizador, normalización ES/EN, zona de mando, precios, CMC y exportación.

---

## Frontend

```bash
cd mtg-frontend
npm ci
```

Crea un `.env`:

```env
VITE_API_URL=http://localhost:3001
```

Inicia Vite:

```bash
npm run dev
```

La aplicación estará disponible normalmente en:

```text
http://localhost:5173
```

### Validación

```bash
npm run lint
npm run build
```

---

# Variables de entorno

## Backend

| Variable | Descripción | Obligatoria |
| --- | --- | --- |
| `NODE_ENV` | Entorno de ejecución | Sí |
| `PORT` | Puerto del servidor | No |
| `MONGO_URI` | Conexión MongoDB | Sí |
| `JWT_SECRET` | Clave de firma de sesiones | Sí |
| `EMAIL_USER` | Cuenta para enviar emails | Para email |
| `EMAIL_PASS` | Contraseña de aplicación Gmail | Para email |
| `EMAIL_FROM` | Remitente mostrado | No |
| `CONTACT_TO` | Destino del formulario | No |
| `CLIENT_URL` | URL del frontend | Sí |
| `ALLOWED_ORIGINS` | Orígenes CORS permitidos | Sí |
| `SPANISH_CARD_INDEX_URL` | Índice opcional español → inglés | No |

> No subas nunca el archivo `.env`, contraseñas, tokens ni credenciales al repositorio.

### Gmail

`EMAIL_PASS` debe ser una **contraseña de aplicación de Google**, no la contraseña habitual de Gmail.

---

## Frontend

| Variable | Descripción |
| --- | --- |
| `VITE_API_URL` | URL pública de la API |

Producción actual:

```env
VITE_API_URL=https://bracketmtg.onrender.com
```

Con subdominio propio:

```env
VITE_API_URL=https://api.bracketmtg.com
```

---

# Despliegue

## Vercel

Configuración recomendada:

```text
Framework: Vite
Build Command: npm run build
Output Directory: dist
Node.js: 22+
```

Variable:

```env
VITE_API_URL=https://bracketmtg.onrender.com
```

Con GitHub conectado a `main`, cada `git push` puede generar automáticamente un nuevo deployment.

---

## Render

Configuración recomendada:

```text
Runtime: Node
Build Command: npm ci
Start Command: npm start
Node.js: 22+
```

Variables principales:

```env
NODE_ENV=production
MONGO_URI=...
JWT_SECRET=...

EMAIL_USER=deckbracket@gmail.com
EMAIL_PASS=...
EMAIL_FROM=BracketMTG <deckbracket@gmail.com>
CONTACT_TO=deckbracket@gmail.com

CLIENT_URL=https://www.bracketmtg.com
ALLOWED_ORIGINS=https://www.bracketmtg.com,https://bracketmtg.com
```

Con Auto Deploy activado sobre `main`, los nuevos commits se despliegan automáticamente.

---

# Seguridad

La aplicación incluye:

- Contraseñas almacenadas mediante bcrypt.
- Sesiones firmadas con JWT.
- Cookie de sesión `httpOnly`.
- Validación de sesión en servidor.
- Rate limiting en autenticación y endpoints sensibles.
- CORS limitado a dominios configurados.
- Sanitización del formulario de contacto.
- Tokens de recuperación de contraseña con caducidad.
- Validación de entradas y tamaños máximos.

Las credenciales deben almacenarse únicamente como variables de entorno.

---

# Actualizar el proyecto

## Frontend

```bash
cd mtg-frontend

npm ci
npm run lint
npm run build

git add -A
git commit -m "Update BracketMTG frontend"
git push origin main
```

## Backend

```bash
cd mtg-deck-analyzer

npm ci
npm test

git add -A
git commit -m "Update BracketMTG backend"
git push origin main
```

---

# Aviso sobre los brackets

La clasificación mostrada por BracketMTG es una **estimación automática** basada en las características detectables de la lista.

La intención del jugador, el entorno de juego y las expectativas de la mesa también influyen en cómo debe considerarse un mazo de Commander, por lo que el resultado debe utilizarse como orientación y no como clasificación oficial.

---

# Disclaimer

BracketMTG es un proyecto independiente y no está afiliado, patrocinado ni respaldado por Wizards of the Coast.

Magic: The Gathering, Commander y sus respectivos nombres, símbolos e imágenes son propiedad de sus titulares correspondientes.

Los datos utilizados por la aplicación proceden de servicios externos como Scryfall y EDHREC y están sujetos a sus respectivos términos y disponibilidad.

---

## Estado del proyecto

El proyecto se encuentra en desarrollo activo. Las mejoras actuales están centradas en:

- precisión del análisis de Commander;
- tiempos de respuesta;
- compatibilidad de nombres en distintos idiomas;
- calidad de recomendaciones;
- experiencia responsive en móvil y escritorio;
- estabilidad de precios y fuentes externas.

---

**BracketMTG — analiza el mazo, entiende el plan, juega mejor.**
