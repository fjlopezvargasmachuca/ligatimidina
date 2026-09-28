import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from './api/client'
import AdminDashboard from './AdminDashboard'
import NoTeFlipesCard from './components/league/NoTeFlipesCard'
import PlayerHandicapsCard from './components/league/PlayerHandicapsCard'
import './App.css'

function asArray(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  return []
}

function appErrorMessage(error, fallback = 'Ha ocurrido un error.') {
  if (typeof error?.data === 'string' && error.data) return error.data
  if (error?.data?.detail) return error.data.detail

  if (error?.data && typeof error.data === 'object') {
    const parts = Object.entries(error.data).flatMap(([field, value]) => {
      if (Array.isArray(value)) return value.map((item) => `${field}: ${item}`)
      return [`${field}: ${value}`]
    })
    if (parts.length) return parts.join(' · ')
  }

  return error?.message || fallback
}

const EMPTY_DECK_FORM = {
  name: '',
  commander: '',
  description: '',
  deck_url: '',
  card_list: '',
  active: true,
}

function enrichAdminStandings(standings, handicaps, grants) {
  const handicapsByPlayer = new Map()
  const grantsByHolder = new Map()

  handicaps.forEach((handicap) => {
    const playerId = Number(handicap.player)
    const current = handicapsByPlayer.get(playerId) || []
    current.push(handicap)
    handicapsByPlayer.set(playerId, current)
  })

  grants.forEach((grant) => {
    const holderId = Number(grant.holder)
    const current = grantsByHolder.get(holderId) || []
    current.push(grant)
    grantsByHolder.set(holderId, current)
  })

  return standings.map((player) => {
    const playerId = Number(player.player_id)
    const playerHandicaps = handicapsByPlayer.get(playerId) || []
    const playerGrants = grantsByHolder.get(playerId) || []
    const availableGrants = playerGrants.filter((grant) => !grant.used)

    const detailedHandicaps = playerHandicaps.map((handicap) => ({
      id: handicap.id,
      name: handicap.definition_name || handicap.name || 'No te flipes',
      description: handicap.description || 'Sin descripción.',
      used: Boolean(handicap.used),
      expired: Boolean(handicap.expired),
      remaining_games: handicap.remaining_games,
      games_played: handicap.games_played,
      penalty_points: handicap.penalty_points_snapshot,
      grace_games: handicap.grace_games_snapshot,
      award_reason: handicap.award_reason,
      assigned_by_player_name: handicap.assigned_by_player_name,
      awarded_by_name: handicap.awarded_by_name,
      awarded_at: handicap.awarded_at,
      used_at: handicap.used_at,
      used_match_id: handicap.used_match_id,
    }))

    const existingIcons = Array.isArray(player.status_icons)
      ? player.status_icons.filter(
          (status) =>
            status.type !== 'HANDICAP_ACTIVE' &&
            status.type !== 'NO_TE_FLIPES_AVAILABLE',
        )
      : []

    if (detailedHandicaps.length > 0) {
      existingIcons.push({
        type: 'HANDICAP_ACTIVE',
        label: `No te flipes (${detailedHandicaps.length})`,
        count: detailedHandicaps.length,
        items: detailedHandicaps,
      })
    }

    if (availableGrants.length > 0) {
      existingIcons.push({
        type: 'NO_TE_FLIPES_AVAILABLE',
        label: `No te flipes disponibles (${availableGrants.length})`,
        count: availableGrants.length,
        description: 'El jugador tiene poderes pendientes de lanzar.',
      })
    }

    return {
      ...player,
      status_icons: existingIcons,
    }
  })
}

function LoginForm({ onAuthenticated }) {
  const [form, setForm] = useState({
    username: '',
    password: '',
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const user = await api.post(
        '/accounts/login/',
        form,
      )

      onAuthenticated(user)
    } catch (requestError) {
      setError(
        requestError.data?.non_field_errors?.join?.(' ') ||
          requestError.message ||
          'No se ha podido iniciar sesión.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <span>LT</span>
          <div>
            <strong>Liga Timidina</strong>
            <small>Commander League</small>
          </div>
        </div>

        <div className="auth-heading">
          <span>Bienvenido</span>
          <h1>Iniciar sesión</h1>
          <p>
            Accede para consultar tu liga y gestionar tus mazos.
          </p>
        </div>

        {error && (
          <div className="app-alert error">{error}</div>
        )}
        {success && (
          <div className="app-alert success">{success}</div>
        )}

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >
          <label>
            Usuario
            <input
              type="text"
              autoComplete="username"
              value={form.username}
              onChange={(event) =>
                setForm({
                  ...form,
                  username: event.target.value,
                })
              }
              required
            />
          </label>

          <label>
            Contraseña
            <input
              type="password"
              autoComplete="current-password"
              value={form.password}
              onChange={(event) =>
                setForm({
                  ...form,
                  password: event.target.value,
                })
              }
              required
            />
          </label>

          <button
            className="app-button primary"
            type="submit"
            disabled={loading}
          >
            {loading ? 'Entrando…' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}

function RegisterForm({ onBack }) {
  const [form, setForm] = useState({
    username: '',
    first_name: '',
    last_name: '',
    display_name: '',
    email: '',
    terms_accepted: false,
    password: '',
    password_confirm: '',
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const result = await api.post(
        '/accounts/register/',
        form,
      )
      setSuccess(result?.detail || 'Cuenta creada. Debe validarla un administrador antes de poder acceder.')
    } catch (requestError) {
      const data = requestError.data

      if (data && typeof data === 'object') {
        const messages = Object.entries(data)
          .flatMap(([field, value]) => {
            if (Array.isArray(value)) {
              return value.map(
                (message) => `${field}: ${message}`,
              )
            }

            return `${field}: ${value}`
          })

        setError(
          messages.join(' · ') ||
            'No se ha podido crear la cuenta.',
        )
      } else {
        setError(
          requestError.message ||
            'No se ha podido crear la cuenta.',
        )
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <span>LT</span>
          <div>
            <strong>Liga Timidina</strong>
            <small>Commander League</small>
          </div>
        </div>

        <div className="auth-heading">
          <span>Primera vez</span>
          <h1>Crear cuenta</h1>
          <p>
            Regístrate para participar en la Liga Timidina.
          </p>
        </div>

        {error && (
          <div className="app-alert error">
            {error}
          </div>
        )}
        {success && (
          <div className="app-alert success">{success}</div>
        )}


        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >
          <label>
            Usuario
            <input
              type="text"
              autoComplete="username"
              value={form.username}
              onChange={(event) =>
                setForm({
                  ...form,
                  username: event.target.value,
                })
              }
              required
            />
          </label>

          <div className="auth-name-grid">
            <label>
              Nombre
              <input
                type="text"
                autoComplete="given-name"
                value={form.first_name}
                onChange={(event) => setForm({ ...form, first_name: event.target.value })}
                required
              />
            </label>
            <label>
              Apellidos
              <input
                type="text"
                autoComplete="family-name"
                value={form.last_name}
                onChange={(event) => setForm({ ...form, last_name: event.target.value })}
                required
              />
            </label>
          </div>

          <label>
            Nombre visible
            <input
              type="text"
              value={form.display_name}
              onChange={(event) =>
                setForm({
                  ...form,
                  display_name: event.target.value,
                })
              }
              required
            />
          </label>

          <label>
            Email
            <input
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              required
            />
          </label>

          <label>
            Contraseña
            <input
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={(event) =>
                setForm({
                  ...form,
                  password: event.target.value,
                })
              }
              minLength={8}
              required
            />
          </label>

          <label>
            Repetir contraseña
            <input
              type="password"
              autoComplete="new-password"
              value={form.password_confirm}
              onChange={(event) =>
                setForm({
                  ...form,
                  password_confirm: event.target.value,
                })
              }
              minLength={8}
              required
            />
          </label>

          <div className="league-rules-box">
            <strong>Normas básicas de la Liga Timidina</strong>
            <ul>
              <li>Respeta a jugadores, organización, administración y personal de la tienda, dentro y fuera del espacio de juego cuando el incidente esté relacionado con la liga.</li>
              <li>No se toleran amenazas, acoso, insultos, discriminación, trampas, suplantación, manipulación de resultados ni uso abusivo de la aplicación.</li>
              <li>Las discrepancias de partida se resuelven con calma y se trasladan a administración; no se utilizará la aplicación para hostigar a otros jugadores.</li>
              <li>Las infracciones pueden implicar advertencias, suspensión o expulsión de la liga y de sus servicios. Los incidentes graves podrán comunicarse a la tienda y, cuando corresponda, a las autoridades competentes.</li>
              <li>El nombre y apellidos se solicitan para identificar correctamente a participantes y gestionar incidencias. No se muestran en el perfil público.</li>
            </ul>
            <label className="rules-accept">
              <input type="checkbox" checked={form.terms_accepted} onChange={(event) => setForm({ ...form, terms_accepted: event.target.checked })} required />
              <span>He leído y acepto las normas de la liga.</span>
            </label>
          </div>

          <button
            className="app-button primary"
            type="submit"
            disabled={loading || !form.terms_accepted}
          >
            {loading ? 'Creando…' : 'Crear cuenta'}
          </button>

          <button
            className="app-button ghost"
            type="button"
            onClick={onBack}
          >
            Volver a iniciar sesión
          </button>
        </form>
      </div>
    </div>
  )
}

function Navbar({
  user,
  activeView,
  onViewChange,
  onLogout,
}) {
  return (
    <header className="app-navbar">
      <div className="app-navbar-inner">
        <button
          className="app-logo"
          onClick={() => onViewChange('league')}
        >
          <span>LT</span>
          <div>
            <strong>Liga Timidina</strong>
            <small>Commander League</small>
          </div>
        </button>

        <nav className="app-nav">
          <button
            className={
              activeView === 'league'
                ? 'active'
                : ''
            }
            onClick={() => onViewChange('league')}
          >
            Liga
          </button>

          <button
            className={
              activeView === 'decks'
                ? 'active'
                : ''
            }
            onClick={() => onViewChange('decks')}
          >
            Mazos
          </button>

          <button
            className={
              activeView === 'profile'
                ? 'active'
                : ''
            }
            onClick={() => onViewChange('profile')}
          >
            Mi perfil
          </button>

          <button
            className={activeView === 'contact' ? 'active' : ''}
            onClick={() => onViewChange('contact')}
          >
            Contacto
          </button>

          {user?.is_staff && (
            <button
              className={
                activeView === 'admin'
                  ? 'active'
                  : ''
              }
              onClick={() => onViewChange('admin')}
            >
              Administración
            </button>
          )}
        </nav>

        <div className="app-user">
          <span>
            {user?.display_name || user?.username}
          </span>

          <button
            className="app-logout"
            onClick={onLogout}
          >
            Salir
          </button>
        </div>
      </div>
    </header>
  )
}

function getStatusIconClass(type) {
  switch (type) {
    case 'NO_TE_FLIPES_AVAILABLE':
      return 'league-status-icon league-status-icon--power'
    case 'HANDICAP_ACTIVE':
      return 'league-status-icon league-status-icon--handicap'
    case 'PENALTY_ACTIVE':
      return 'league-status-icon league-status-icon--penalty'
    default:
      return 'league-status-icon'
  }
}

function getStatusIcon(type) {
  switch (type) {
    case 'NO_TE_FLIPES_AVAILABLE':
      return '⚡'
    case 'HANDICAP_ACTIVE':
      return '⛓'
    case 'PENALTY_ACTIVE':
      return '!'
    default:
      return '•'
  }
}

function LeagueStatusIcon({ status }) {
  const count = Number(status?.count || 0)
  const icon = getStatusIcon(status?.type)
  const [open, setOpen] = useState(false)
  const [position, setPosition] = useState({ top: 0, left: 0 })

  function updateTooltipPosition(target) {
    const rect = target.getBoundingClientRect()
    const width = 280
    const estimatedHeight = Math.min(420, 150 + ((status?.items?.length || 0) * 82))
    const gap = 10
    const left = Math.min(
      Math.max(rect.left + rect.width / 2 - width / 2, 12),
      Math.max(window.innerWidth - width - 12, 12),
    )
    const below = rect.bottom + gap
    const top = below + estimatedHeight <= window.innerHeight
      ? below
      : Math.max(rect.top - estimatedHeight - gap, 12)

    setPosition({ top, left })
  }

  function showTooltip(event) {
    updateTooltipPosition(event.currentTarget)
    setOpen(true)
  }

  function hideTooltip() {
    setOpen(false)
  }

  useEffect(() => {
    if (!open) return undefined

    function reposition() {
      const element = document.activeElement
      if (element?.dataset?.statusIcon === 'true') {
        updateTooltipPosition(element)
      }
    }

    window.addEventListener('resize', reposition)
    window.addEventListener('scroll', reposition, true)

    return () => {
      window.removeEventListener('resize', reposition)
      window.removeEventListener('scroll', reposition, true)
    }
  }, [open])

  const tooltip = open ? createPortal(
    <span
      className="league-status-tooltip"
      role="tooltip"
      style={{ top: position.top, left: position.left }}
    >
      <strong>{status?.label || 'Estado'}</strong>

      {status?.description && (
        <span>{status.description}</span>
      )}

      {Array.isArray(status?.items) && status.items.length > 0 && (
        <span className="league-status-tooltip__items">
          {status.items.map((item) => (
            <span className="league-status-tooltip__item" key={item.id}>
              <strong>{item.name}</strong>
              <span>{item.description}</span>
              <span className="league-status-tooltip__meta">
                Penalización: -{item.penalty_points ?? 0} · Gracia: {item.grace_games ?? 0}
              </span>
              {item.assigned_by_player_name && (
                <span className="league-status-tooltip__meta">
                  Lanzado por: {item.assigned_by_player_name}
                </span>
              )}
              {item.award_reason && (
                <span className="league-status-tooltip__meta">
                  Motivo: {item.award_reason}
                </span>
              )}
              {item.used_match_id && (
                <span className="league-status-tooltip__meta">
                  Canjeada en partida #{item.used_match_id}
                </span>
              )}
              <em>
                {item.used
                  ? `Canjeada${item.used_at ? ` · ${new Intl.DateTimeFormat('es-ES', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(item.used_at))}` : ''}.`
                  : item.expired
                    ? `Penaliza desde la siguiente partida. Gracia restante: ${item.remaining_games ?? 0}.`
                    : `Pendiente · quedan ${item.remaining_games ?? 0} partidas de gracia.`}
              </em>
            </span>
          ))}
        </span>
      )}

      {status?.remaining_games != null && (
        <em>
          {status.remaining_games === 1
            ? 'Queda 1 partida de gracia.'
            : `Quedan ${status.remaining_games} partidas de gracia.`}
        </em>
      )}
    </span>,
    document.body,
  ) : null

  return (
    <>
      <span
        className={getStatusIconClass(status?.type)}
        tabIndex={0}
        data-status-icon="true"
        aria-label={status?.label || 'Estado del jugador'}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
      >
        {icon}

        {count > 1 && (
          <small>{count}</small>
        )}
      </span>

      {tooltip}
    </>
  )
}

function LeaguePlayerName({ player, onOpen }) {
  const statusIcons = Array.isArray(player?.status_icons)
    ? player.status_icons
    : []

  return (
    <button className="league-player-cell league-player-button" type="button" onClick={() => onOpen?.(player)}>
      {player.avatar ? <img className="league-avatar" src={player.avatar} alt="" /> : <span className="league-avatar league-avatar--fallback">{(player.display_name || player.username || '?').charAt(0).toUpperCase()}</span>}
      <div>
      <div className="league-player-main">
        <strong>
          {player.display_name || player.username}
        </strong>

        {statusIcons.length > 0 && (
          <span
            className="league-status-icons"
            aria-label="Estados del jugador"
          >
            {statusIcons.map((status, index) => (
              <LeagueStatusIcon
                key={`${status.type || 'status'}-${index}`}
                status={status}
              />
            ))}
          </span>
        )}
      </div>

      <small>@{player.username}</small>
      </div>
    </button>
  )
}

function PlayerProfileModal({ player, onClose }) {
  const [stats, setStats] = useState(null)
  const [decks, setDecks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    Promise.all([
      api.get(`/league/players/${player.player_id}/stats/`),
      api.get(`/decks/?owner=${player.player_id}`),
    ]).then(([statsData, deckData]) => {
      if (!cancelled) { setStats(statsData); setDecks(asArray(deckData)) }
    }).finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [player.player_id])

  return createPortal(
    <div className="profile-modal-backdrop" onMouseDown={onClose}>
      <section className="profile-modal" onMouseDown={(event) => event.stopPropagation()}>
        <button className="profile-modal-close" type="button" onClick={onClose}>×</button>
        <div className="profile-modal-heading">
          {player.avatar ? <img className="profile-modal-avatar" src={player.avatar} alt="" /> : <span className="profile-modal-avatar profile-modal-avatar--fallback">{(player.display_name || '?').charAt(0).toUpperCase()}</span>}
          <div><span>Perfil público</span><h2>{player.display_name || player.username}</h2><small>@{player.username}</small></div>
        </div>
        {loading ? <div className="page-loading">Cargando perfil…</div> : <>
          <h3>Últimas 5 partidas</h3>
          <div className="history-list compact">
            {stats?.history?.length ? stats.history.slice(0, 5).map((item, index) => (
              <div className="history-item" key={`${item.week_number}-${index}`}>
                <div><strong>Jornada {item.week_number}</strong><span>{item.deck_name} · {item.commander}</span></div>
                <div><strong>#{item.final_position}</strong><span>{item.points} pts</span></div>
              </div>
            )) : <div className="empty-message">Aún no ha jugado partidas cerradas.</div>}
          </div>
          <h3>Mazos activos</h3>
          <div className="public-profile-decks">
            {decks.length ? decks.map((deck) => <article className="public-deck-card" key={deck.id}>
              <div className="public-deck-heading"><div><strong>{deck.name}</strong><span>{deck.commander}</span></div>{deck.analysis?.bracket && <b className="public-bracket">Bracket {deck.analysis.bracket}</b>}</div>
              {deck.deck_url && <a href={deck.deck_url} target="_blank" rel="noreferrer">Ver en DeckCheck ↗</a>}
              {deck.card_list && <DeckCardListViewer deck={deck} />}
            </article>) : <div className="empty-message">No tiene mazos activos.</div>}
          </div>
        </>}
      </section>
    </div>, document.body
  )
}

function WeekCountdown({ week }) {
  const [now, setNow] = useState(Date.now())
  useEffect(() => { const id = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(id) }, [])
  if (!week?.date) return null
  const end = new Date(`${week.date}T00:00:00`)
  end.setDate(end.getDate() + 7)
  const ms = Math.max(0, end.getTime() - now)
  const days = Math.floor(ms / 86400000)
  const hours = Math.floor((ms % 86400000) / 3600000)
  const minutes = Math.floor((ms % 3600000) / 60000)
  const seconds = Math.floor((ms % 60000) / 1000)
  return <div className="week-countdown"><span>Próximo evento en</span><strong>{days}d {hours}h {minutes}m {seconds}s</strong></div>
}

function WeeklyEventModal({ week, onClose }) {
  const event = week?.weekly_event
  if (!event) return null
  return createPortal(
    <div className="profile-modal-backdrop" onMouseDown={onClose}>
      <section className="event-modal" onMouseDown={(e) => e.stopPropagation()}>
        <button className="profile-modal-close" type="button" onClick={onClose}>×</button>
        <span className="event-modal-eyebrow">Evento semanal · Jornada {week.number}</span>
        <h2>{event.name}</h2>
        {event.description && <p className="event-modal-description">{event.description}</p>}
        <div className="event-modal-grid">
          <div><span>Reglas</span><p>{event.rules || 'Sin reglas adicionales.'}</p></div>
          <div><span>Puntos extra</span><strong>{Number(event.extra_points || 0) > 0 ? `+${event.extra_points}` : event.extra_points || 0} puntos</strong><small>Se aplican cuando el administrador registra que has cumplido el evento.</small></div>
        </div>
      </section>
    </div>,
    document.body,
  )
}

function SupportCard({ user }) {
  return <section className="league-card support-card">
    <div className="section-title"><span>Apoya la liga</span><h2>Inscripción y premios</h2></div>
    <p><strong>Suscripción: 10 € al mes.</strong> La modalidad gratuita permite hasta 1 partida por jornada; con suscripción mensual validada, hasta 3.</p>
    <p className="support-distribution">De las aportaciones destinadas a la liga: <strong>40%</strong> se reserva para premios a participantes y <strong>60%</strong> para organización, tienda y mantenimiento de la web.</p>
    <a className="app-button paypal-button" href="https://paypal.me/machukador/10" target="_blank" rel="noreferrer">Pagar / aportar 10 € con PayPal ↗</a>
    <small>El pago no activa automáticamente la suscripción: administración debe validarlo. Estado actual: <strong>{user?.subscription_active ? 'suscripción activa' : 'modalidad gratuita'}</strong>.</small>
  </section>
}

function LeagueView({ user }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [currentWeek, setCurrentWeek] = useState(null)
  const [showEvent, setShowEvent] = useState(false)

  async function load() {
    setLoading(true)
    setError('')

    try {
      const [response, weekResponse] = await Promise.all([api.get('/league/standings/'), api.get('/league/current-week/').catch(() => null)])
      setCurrentWeek(weekResponse)

      if (user?.is_staff) {
        const [handicapsResponse, grantsResponse] = await Promise.all([
          api.get('/handicaps/'),
          api.get('/handicaps/grants/'),
        ])

        setData({
          ...response,
          standings: enrichAdminStandings(
            response?.standings || [],
            asArray(handicapsResponse),
            asArray(grantsResponse),
          ),
        })
      } else {
        setData(response)
      }
    } catch (requestError) {
      setError(
        requestError.data?.detail ||
          requestError.message ||
          'No se ha podido cargar la clasificación.',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [user])

  if (loading) {
    return (
      <main className="page-content">
        <div className="page-loading">
          Cargando clasificación…
        </div>
      </main>
    )
  }

  if (error) {
    return (
      <main className="page-content">
        <div className="app-alert error">
          {error}
        </div>
      </main>
    )
  }

  const standings = data?.standings || []
  const visibleStandings = standings.filter((player) => `${player.display_name || ''} ${player.username || ''}`.toLowerCase().includes(search.trim().toLowerCase()))

  return (
    <main className="page-content">
      <div className="league-heading">
        <div>
          <span>Clasificación</span>
          <h1>
            {data?.season?.name || 'Liga Timidina'}
          </h1>
        </div>

        <div className="league-season-date">
          {data?.season?.start_date}
          {data?.season?.end_date
            ? ` → ${data.season.end_date}`
            : ''}
        </div>
      </div>

      <div className="league-tools">
        <input className="league-search" type="search" placeholder="Buscar jugador…" value={search} onChange={(event) => setSearch(event.target.value)} />
        {currentWeek && <div className="current-week-stack">
          <div className="current-week-date">Jornada {currentWeek.number} · {new Date(`${currentWeek.date}T12:00:00`).toLocaleDateString('es-ES')}</div>
          <button className="current-week-card event-card-button" type="button" onClick={() => currentWeek.weekly_event && setShowEvent(true)} disabled={!currentWeek.weekly_event}>
            <span>EVENTO SEMANAL</span>
            <strong>{currentWeek.weekly_event?.name || 'Sin evento asignado'}</strong>
            <em>{currentWeek.weekly_event ? '(Pulsar para leer las reglas)' : 'Esta jornada no tiene evento.'}</em>
            <WeekCountdown week={currentWeek} />
          </button>
        </div>}
      </div>

      <div className="league-layout">
        <section className="league-card">
          <div className="league-table-wrap">
            <table className="league-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Jugador</th>
                  <th>Puntos</th>
                  <th>Victorias</th>
                  <th>Partidas</th>
                  <th>Eliminaciones</th>
                  <th>Semanas</th>
                </tr>
              </thead>

              <tbody>
                {visibleStandings.length === 0 ? (
                  <tr>
                    <td colSpan="7">
                      Todavía no hay resultados.
                    </td>
                  </tr>
                ) : (
                  visibleStandings.map((player, index) => (
                    <tr key={player.player_id || index}>
                      <td>
                        {player.position || index + 1}
                      </td>
                      <td>
                        <LeaguePlayerName player={player} onOpen={setSelectedPlayer} />
                      </td>
                      <td>
                        <strong>
                          {player.points ?? 0}
                        </strong>
                      </td>
                      <td>{player.wins ?? 0}</td>
                      <td>{player.games ?? 0}</td>
                      <td>{player.eliminations ?? 0}</td>
                      <td>{player.weeks ?? 0}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="league-sidebar">
          <NoTeFlipesCard currentUserId={user?.id} />
          <SupportCard user={user} />
        </aside>
      </div>
      {selectedPlayer && <PlayerProfileModal player={selectedPlayer} onClose={() => setSelectedPlayer(null)} />}
      {showEvent && currentWeek?.weekly_event && <WeeklyEventModal week={currentWeek} onClose={() => setShowEvent(false)} />}
    </main>
  )
}

function parseCardList(text) {
  return (text || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean).map((line) => {
    const match = line.match(/^(\d+)\s*[xX]?\s+(.+)$/)
    return { quantity: match ? Number(match[1]) : 1, name: match ? match[2].trim() : line }
  })
}

function DeckCardListViewer({ deck }) {
  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const cards = parseCardList(deck.card_list)

  async function showCard(card) {
    setLoading(true); setError('')
    try { setSelected(await api.get(`/decks/cards/lookup/?name=${encodeURIComponent(card.name)}`)) }
    catch (err) { setError(appErrorMessage(err, 'No se ha encontrado la carta.')) }
    finally { setLoading(false) }
  }

  if (!cards.length) return null
  if (!open) return <button className="app-button ghost deck-list-toggle" type="button" onClick={() => setOpen(true)}>Ver listado ({cards.reduce((sum, card) => sum + card.quantity, 0)} cartas)</button>

  if (selected) {
    return <div className="card-preview" onClick={() => setSelected(null)} role="button" tabIndex={0} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') setSelected(null) }}>
      {selected.image ? <img src={selected.image} alt={selected.name} /> : <div className="empty-message">Sin imagen disponible.</div>}
      <strong>{selected.name}</strong><span>Haz clic para volver al listado.</span>
    </div>
  }

  return <div className="deck-card-list">
    <div className="deck-card-list-head"><strong>Listado</strong><button type="button" onClick={() => setOpen(false)}>Cerrar</button></div>
    {error && <div className="app-alert error">{error}</div>}
    {cards.map((card, index) => <button type="button" key={`${card.name}-${index}`} onClick={() => showCard(card)} disabled={loading}><span>{card.quantity}×</span>{card.name}</button>)}
    {loading && <small>Cargando carta…</small>}
  </div>
}

function DecksView({ user }) {
  const [myDecks, setMyDecks] = useState([])
  const [form, setForm] = useState(EMPTY_DECK_FORM)
  const [editingId, setEditingId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [commanderSuggestions, setCommanderSuggestions] = useState([])

  async function load() {
    setLoading(true)
    setError('')
    try {
      const mineResponse = await api.get('/decks/mine/')
      setMyDecks(asArray(mineResponse))
    } catch (requestError) {
      setError(appErrorMessage(requestError, 'No se han podido cargar los mazos.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    async function loadDecks() {
      await load()
    }

    loadDecks()
  }, [user.id])

  function resetForm() {
    setEditingId(null)
    setForm(EMPTY_DECK_FORM)
  }

  function startEdit(deck) {
    setEditingId(deck.id)
    setForm({
      name: deck.name || '',
      commander: deck.commander || '',
      description: deck.description || '',
      deck_url: deck.deck_url || '',
      card_list: deck.card_list || '',
      active: Boolean(deck.active),
    })
    setError('')
    setSuccess('')
  }

  function changeField(event) {
    const { name, value, type, checked } = event.target
    setForm((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  useEffect(() => {
    const query = form.commander.trim()
    if (query.length < 2) {
      setCommanderSuggestions([])
      return undefined
    }
    const timer = setTimeout(async () => {
      try {
        const response = await api.get(`/decks/commanders/autocomplete/?q=${encodeURIComponent(query)}`)
        setCommanderSuggestions(Array.isArray(response?.results) ? response.results : [])
      } catch {
        setCommanderSuggestions([])
      }
    }, 250)
    return () => clearTimeout(timer)
  }, [form.commander])

  async function saveDeck(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')

    try {
      if (editingId) {
        await api.patch(`/decks/${editingId}/update/`, form)
        setSuccess('Mazo actualizado correctamente.')
      } else {
        await api.post('/decks/create/', form)
        setSuccess('Mazo creado correctamente.')
      }
      resetForm()
      await load()
    } catch (requestError) {
      setError(appErrorMessage(requestError, 'No se ha podido guardar el mazo.'))
    } finally {
      setSaving(false)
    }
  }

  async function deleteDeck(deck) {
    const confirmed = window.confirm(
      `¿Eliminar el mazo "${deck.name}"? Si ya se ha usado en una partida, el backend puede impedir el borrado para proteger el histórico.`,
    )
    if (!confirmed) return

    setSaving(true)
    setError('')
    try {
      await api.delete(`/decks/${deck.id}/delete/`)
      if (editingId === deck.id) resetForm()
      setSuccess('Mazo eliminado correctamente.')
      await load()
    } catch (requestError) {
      setError(appErrorMessage(requestError, 'No se ha podido eliminar el mazo.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <main className="page-content">
      <div className="league-heading">
        <div>
          <span>Mazos</span>
          <h1>Decks de la liga</h1>
        </div>
        <div className="league-season-date">
          Gestiona tus mazos. Los mazos públicos se consultan desde el perfil de cada jugador en la clasificación.
        </div>
      </div>

      {error && <div className="app-alert error">{error}</div>}
      {success && <div className="app-alert success">{success}</div>}

      <div className="decks-layout">
        <section className="league-card deck-editor-card">
          <div className="section-title">
            <span>{editingId ? 'Edición' : 'Nuevo mazo'}</span>
            <h2>{editingId ? 'Editar mi mazo' : 'Registrar mazo Commander'}</h2>
          </div>

          <form className="deck-form" onSubmit={saveDeck}>
            <label>
              Nombre del mazo
              <input name="name" value={form.name} onChange={changeField} required />
            </label>
            <label>
              Comandante
              <input name="commander" list="commander-suggestions" value={form.commander} onChange={changeField} autoComplete="off" required />
              <datalist id="commander-suggestions">{commanderSuggestions.map((name) => <option value={name} key={name} />)}</datalist>
              <small>Empieza a escribir y se sugerirán nombres de cartas reales de Scryfall.</small>
            </label>
            <label>
              Descripción
              <textarea name="description" value={form.description} onChange={changeField} rows="4" />
            </label>
            <label>
              URL del mazo
              <input name="deck_url" type="url" value={form.deck_url} onChange={changeField} placeholder="https://deckcheck.co/app/decklist/…" />
            </label>
            <label>
              Listado de cartas (una por línea)
              <textarea name="card_list" value={form.card_list} onChange={changeField} rows="9" placeholder="1 Sol Ring\n1 Command Tower\n…" />
              <small>Detectadas {parseCardList(form.card_list).reduce((sum, card) => sum + card.quantity, 0)} cartas. La API pública de DeckCheck es de consulta y no permite crear mazos automáticamente; guarda la lista aquí y <a href="https://deckcheck.co/app/builder" target="_blank" rel="noreferrer">ábrela en DeckCheck ↗</a> para importarla.</small>
            </label>
            <label className="deck-checkbox">
              <input name="active" type="checkbox" checked={form.active} onChange={changeField} />
              <span>Mazo activo</span>
            </label>
            <div className="deck-form-actions">
              <button className="app-button primary" type="submit" disabled={saving}>
                {saving ? 'Guardando…' : editingId ? 'Guardar cambios' : 'Registrar mazo'}
              </button>
              {editingId && (
                <button className="app-button ghost" type="button" onClick={resetForm} disabled={saving}>
                  Cancelar
                </button>
              )}
            </div>
          </form>
        </section>

        <section className="league-card">
          <div className="section-title">
            <span>Propios</span>
            <h2>Mis mazos ({myDecks.length})</h2>
          </div>

          {loading ? (
            <div className="page-loading">Cargando mazos…</div>
          ) : myDecks.length === 0 ? (
            <div className="empty-message">Todavía no has registrado ningún mazo.</div>
          ) : (
            <div className="deck-list">
              {myDecks.map((deck) => (
                <article className="deck-item" key={deck.id}>
                  <div className="deck-item-main">
                    <div>
                      <strong>{deck.name}</strong>
                      <span>{deck.commander}</span>
                    </div>
                    <span className={`deck-status ${deck.active ? 'active' : 'inactive'}`}>
                      {deck.active ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                  {deck.analysis && (
                    <div className="deck-analysis">
                      {deck.analysis.bracket && <span>Bracket {deck.analysis.bracket}</span>}
                      {deck.analysis.crispi_score != null && <span>CRISPI {deck.analysis.crispi_score}</span>}
                    </div>
                  )}
                  {deck.deck_url && <a className="deckcheck-link" href={deck.deck_url} target="_blank" rel="noreferrer">DeckCheck ↗</a>}
                  <DeckCardListViewer deck={deck} />
                  <div className="deck-actions">
                    <button className="app-button ghost" type="button" onClick={() => startEdit(deck)} disabled={saving}>
                      Editar
                    </button>
                    <button className="app-button ghost deck-delete" type="button" onClick={() => deleteDeck(deck)} disabled={saving}>
                      Eliminar
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="league-card deckcheck-help-card">
        <div className="section-title"><span>Integración</span><h2>DeckCheck</h2></div>
        <p>Los mazos de otros jugadores se consultan desde su perfil público en la clasificación. Para importar una lista nueva en DeckCheck, copia tu listado y usa su constructor; después pega aquí la URL pública generada.</p>
        <a className="app-button ghost" href="https://deckcheck.co/app/builder" target="_blank" rel="noreferrer">Abrir DeckCheck ↗</a>
      </section>
    </main>
  )
}

function AccountSettingsCard({ user, onUserUpdated }) {
  const [displayName, setDisplayName] = useState(user.display_name || '')
  const [avatar, setAvatar] = useState(null)
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    new_password_confirm: '',
  })
  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPassword, setSavingPassword] = useState(false)
  const [profileMessage, setProfileMessage] = useState('')
  const [passwordMessage, setPasswordMessage] = useState('')
  const [error, setError] = useState('')

  async function saveProfile(event) {
    event.preventDefault()
    setSavingProfile(true)
    setError('')
    setProfileMessage('')

    try {
      let payload
      if (avatar) {
        payload = new FormData()
        payload.append('display_name', displayName)
        payload.append('avatar', avatar)
      } else {
        payload = { display_name: displayName }
      }

      const updated = await api.patch('/accounts/profile/', payload)
      onUserUpdated(updated)
      setAvatar(null)
      setProfileMessage('Perfil actualizado.')
    } catch (requestError) {
      setError(appErrorMessage(requestError, 'No se ha podido actualizar el perfil.'))
    } finally {
      setSavingProfile(false)
    }
  }

  async function changePassword(event) {
    event.preventDefault()
    setSavingPassword(true)
    setError('')
    setPasswordMessage('')
    try {
      const response = await api.post('/accounts/change-password/', passwordForm)
      setPasswordForm({
        current_password: '',
        new_password: '',
        new_password_confirm: '',
      })
      setPasswordMessage(response.detail || 'Contraseña actualizada.')
    } catch (requestError) {
      setError(appErrorMessage(requestError, 'No se ha podido cambiar la contraseña.'))
    } finally {
      setSavingPassword(false)
    }
  }

  return (
    <div className="profile-settings-grid">
      <section className="league-card profile-settings-card">
        <div className="section-title">
          <span>Cuenta</span>
          <h2>Editar perfil</h2>
        </div>
        <form className="profile-settings-form" onSubmit={saveProfile}>
          <label>
            Usuario
            <input value={user.username} disabled />
          </label>
          <label>
            Nombre visible
            <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} required />
          </label>
          <label>
            Avatar
            <input type="file" accept="image/*" onChange={(event) => setAvatar(event.target.files?.[0] || null)} />
          </label>
          {profileMessage && <div className="profile-inline-success">{profileMessage}</div>}
          <button className="app-button primary" type="submit" disabled={savingProfile}>
            {savingProfile ? 'Guardando…' : 'Guardar perfil'}
          </button>
        </form>
      </section>

      <section className="league-card profile-settings-card">
        <div className="section-title">
          <span>Seguridad</span>
          <h2>Cambiar contraseña</h2>
        </div>
        <form className="profile-settings-form" onSubmit={changePassword}>
          <label>
            Contraseña actual
            <input
              type="password"
              autoComplete="current-password"
              value={passwordForm.current_password}
              onChange={(event) => setPasswordForm({ ...passwordForm, current_password: event.target.value })}
              required
            />
          </label>
          <label>
            Nueva contraseña
            <input
              type="password"
              autoComplete="new-password"
              minLength={8}
              value={passwordForm.new_password}
              onChange={(event) => setPasswordForm({ ...passwordForm, new_password: event.target.value })}
              required
            />
          </label>
          <label>
            Repetir nueva contraseña
            <input
              type="password"
              autoComplete="new-password"
              minLength={8}
              value={passwordForm.new_password_confirm}
              onChange={(event) => setPasswordForm({ ...passwordForm, new_password_confirm: event.target.value })}
              required
            />
          </label>
          {passwordMessage && <div className="profile-inline-success">{passwordMessage}</div>}
          <button className="app-button primary" type="submit" disabled={savingPassword}>
            {savingPassword ? 'Actualizando…' : 'Cambiar contraseña'}
          </button>
        </form>
      </section>

      {error && <div className="app-alert error profile-settings-error">{error}</div>}
    </div>
  )
}

function ProfileView({ user, onUserUpdated }) {
  const [stats, setStats] = useState(null)
  const [profileDecks, setProfileDecks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [response, deckResponse] = await Promise.all([
          api.get(`/league/players/${user.id}/stats/`),
          api.get('/decks/mine/'),
        ])
        setStats(response)
        setProfileDecks(asArray(deckResponse))
      } catch {
        setStats(null)
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [user.id])

  return (
    <main className="page-content">
      <div className="profile-heading">
        <div className={`profile-avatar ${user.avatar ? 'profile-avatar--image' : ''}`}>
          {user.avatar ? (
            <img src={user.avatar} alt="" />
          ) : (
            (user.display_name || user.username || '?').charAt(0).toUpperCase()
          )}
        </div>

        <div>
          <span>Perfil</span>
          <h1>
            {user.display_name || user.username}
          </h1>
          <p>@{user.username}</p>
        </div>
      </div>

      {loading ? (
        <div className="page-loading">
          Cargando estadísticas…
        </div>
      ) : stats ? (
        <>
          <div className="profile-stats">
            <div>
              <span>Puntos</span>
              <strong>{stats.points}</strong>
            </div>
            <div>
              <span>Victorias</span>
              <strong>{stats.wins}</strong>
            </div>
            <div>
              <span>Partidas</span>
              <strong>{stats.games}</strong>
            </div>
            <div>
              <span>Eliminaciones</span>
              <strong>{stats.eliminations}</strong>
            </div>
          </div>

          <section className="league-card">
            <div className="section-title">
              <span>Historial</span>
              <h2>Últimas partidas</h2>
            </div>

            {stats.history?.length ? (
              <div className="history-list">
                {stats.history.map((item, index) => (
                  <div
                    className="history-item"
                    key={`${item.week_number}-${item.deck_id}-${index}`}
                  >
                    <div>
                      <strong>
                        Semana {item.week_number}
                      </strong>
                      <span>
                        {item.deck_name} ·{' '}
                        {item.commander}
                      </span>
                    </div>

                    <div>
                      <strong>
                        #{item.final_position}
                      </strong>
                      <span>
                        {item.points} puntos
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-message">
                Todavía no hay partidas cerradas.
              </div>
            )}
          </section>

          <section className="league-card profile-decks-section">
            <div className="section-title"><span>Mazos</span><h2>Mis mazos guardados</h2></div>
            <div className="deck-list">{profileDecks.length ? profileDecks.map((deck) => <article className="deck-item" key={deck.id}><div className="deck-item-main"><div><strong>{deck.name}</strong><span>{deck.commander}</span></div>{deck.analysis?.bracket && <span className="deck-status active">Bracket {deck.analysis.bracket}</span>}</div>{deck.deck_url && <a className="deckcheck-link" href={deck.deck_url} target="_blank" rel="noreferrer">Ver en DeckCheck ↗</a>}<DeckCardListViewer deck={deck}/></article>) : <div className="empty-message">No tienes mazos guardados.</div>}</div>
          </section>

          <PlayerHandicapsCard playerId={user.id} />
        </>
      ) : (
        <div className="app-alert error">
          Todavía no hay estadísticas disponibles.
        </div>
      )}

      <AccountSettingsCard user={user} onUserUpdated={onUserUpdated} />

      <div className="profile-power-section">
        <NoTeFlipesCard currentUserId={user?.id} />
      </div>
    </main>
  )
}

function ContactView({ user }) {
  const [messages, setMessages] = useState([])
  const [form, setForm] = useState({ subject: '', message: '' })
  const [replyDrafts, setReplyDrafts] = useState({})
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  async function load() {
    try {
      setMessages(asArray(await api.get('/accounts/contact/')))
    } catch (err) {
      setError(appErrorMessage(err))
    }
  }

  useEffect(() => { load() }, [user.id])

  async function send(event) {
    event.preventDefault()
    setError('')
    setNotice('')
    try {
      await api.post('/accounts/contact/', form)
      setForm({ subject: '', message: '' })
      setNotice('Conversación enviada a administración.')
      await load()
    } catch (err) {
      setError(appErrorMessage(err, 'No se ha podido enviar el mensaje.'))
    }
  }

  async function sendReply(item) {
    const body = (replyDrafts[item.id] || '').trim()
    if (!body) return
    setError('')
    try {
      await api.post(`/accounts/contact/${item.id}/reply/`, { body })
      setReplyDrafts((current) => ({ ...current, [item.id]: '' }))
      await load()
    } catch (err) {
      setError(appErrorMessage(err, 'No se ha podido enviar la respuesta.'))
    }
  }

  async function updateConversation(item, patch) {
    try {
      await api.patch(`/accounts/contact/${item.id}/`, patch)
      await load()
    } catch (err) {
      setError(appErrorMessage(err))
    }
  }

  return <main className="page-content">
    <div className="league-heading"><div><span>Soporte</span><h1>Contacto con administración</h1></div></div>
    {error && <div className="app-alert error">{error}</div>}
    {notice && <div className="app-alert success">{notice}</div>}

    {!user.is_staff && <section className="league-card contact-card">
      <div className="section-title"><span>Nueva conversación</span><h2>Escribir a administración</h2></div>
      <p className="contact-help">Para evitar spam se permiten hasta 3 conversaciones nuevas cada 24 horas. Si el asunto ya existe, responde dentro de esa conversación.</p>
      <form className="deck-form" onSubmit={send}>
        <label>Asunto<input value={form.subject} onChange={(e) => setForm({...form, subject:e.target.value})} required maxLength={160}/></label>
        <label>Mensaje<textarea rows="7" value={form.message} onChange={(e) => setForm({...form, message:e.target.value})} required/></label>
        <button className="app-button primary">Enviar mensaje</button>
      </form>
    </section>}

    <section className="league-card contact-card">
      <div className="section-title"><span>{user.is_staff ? 'Buzón administrativo' : 'Historial'}</span><h2>{user.is_staff ? 'Conversaciones recibidas' : 'Mis conversaciones'}</h2></div>
      <div className="contact-thread-list">
        {messages.length ? messages.map((item) => <article className={`contact-thread ${item.read ? '' : 'unread'}`} key={item.id}>
          <div className="contact-thread-head">
            <div><strong>{item.subject}</strong><span>{item.sender_name || item.sender_username} · @{item.sender_username} · {new Date(item.created_at).toLocaleString('es-ES')}</span></div>
            <div className="contact-thread-badges"><span>{item.closed ? 'Cerrada' : 'Abierta'}</span>{!item.read && <b>Nueva</b>}</div>
          </div>
          <div className="contact-bubble user-bubble"><small>{item.sender_name || item.sender_username}</small><p>{item.message}</p></div>
          {(item.replies || []).map((reply) => <div className={`contact-bubble ${reply.sender_is_staff ? 'admin-bubble' : 'user-bubble'}`} key={reply.id}>
            <small>{reply.sender_is_staff ? 'Administración' : (reply.sender_name || reply.sender_username)} · {new Date(reply.created_at).toLocaleString('es-ES')}</small>
            <p>{reply.body}</p>
          </div>)}
          {!item.closed && <div className="contact-reply-box">
            <textarea rows="3" placeholder={user.is_staff ? `Responder a @${item.sender_username}…` : 'Añadir información a esta conversación…'} value={replyDrafts[item.id] || ''} onChange={(e) => setReplyDrafts((current) => ({...current, [item.id]: e.target.value}))}/>
            <button className="app-button primary" type="button" onClick={() => sendReply(item)}>Responder</button>
          </div>}
          {user.is_staff && <div className="contact-admin-actions">
            {!item.read && <button className="app-button ghost" type="button" onClick={() => updateConversation(item, { read: true })}>Marcar como leído</button>}
            <button className="app-button ghost" type="button" onClick={() => updateConversation(item, { closed: !item.closed })}>{item.closed ? 'Reabrir' : 'Cerrar conversación'}</button>
          </div>}
        </article>) : <div className="empty-message">No hay mensajes.</div>}
      </div>
    </section>
  </main>
}

function AppFooter() {
  return <footer className="app-footer">
    <span>© {new Date().getFullYear()} Liga Timidina · Todos los derechos reservados.</span>
    <span className="partner-strip">Colaboraciones / servicios:
      <a href="https://magic.wizards.com/" target="_blank" rel="noreferrer"><img src="/partners/magic.svg" alt="" />Magic: The Gathering</a>
      <a href="https://deckcheck.co/" target="_blank" rel="noreferrer"><img src="/partners/deckcheck.svg" alt="" />DeckCheck</a>
      <a href="https://www.adadoypluma.es/" target="_blank" rel="noreferrer"><img src="/partners/adadoypluma.svg" alt="" />A Dado y Pluma · Triana</a>
    </span>
  </footer>
}

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [authMode, setAuthMode] = useState('login')
  const [activeView, setActiveView] = useState('league')

  useEffect(() => {
    async function loadCurrentUser() {
      try {
        const currentUser = await api.get(
          '/accounts/me/',
        )

        setUser(currentUser)
      } catch {
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    loadCurrentUser()
  }, [])

  async function handleLogout() {
    try {
      await api.post('/accounts/logout/')
    } finally {
      setUser(null)
      setActiveView('league')
    }
  }

  function handleAuthenticated(authenticatedUser) {
    setUser(authenticatedUser)

    setActiveView(
      authenticatedUser?.is_staff
        ? 'admin'
        : 'league',
    )
  }

  if (loading) {
    return (
      <div className="app-loading-screen">
        <div className="app-loading-mark">LT</div>
        <span>Cargando Liga Timidina…</span>
      </div>
    )
  }

  if (!user) {
    if (authMode === 'register') {
      return (
        <>
          <RegisterForm onAuthenticated={handleAuthenticated} onBack={() => setAuthMode('login')} />
          <AppFooter />
        </>
      )
    }

    return (
      <>
        <LoginForm
          onAuthenticated={handleAuthenticated}
        />

        <button
          className="auth-register-link"
          onClick={() => setAuthMode('register')}
        >
          ¿Todavía no tienes cuenta? Crear cuenta
        </button>
        <AppFooter />
      </>
    )
  }

  return (
    <div className="app">
      <Navbar
        user={user}
        activeView={activeView}
        onViewChange={setActiveView}
        onLogout={handleLogout}
      />

      {activeView === 'league' && (
        <LeagueView user={user} />
      )}

      {activeView === 'decks' && (
        <DecksView user={user} />
      )}

      {activeView === 'profile' && (
        <ProfileView user={user} onUserUpdated={setUser} />
      )}

      {activeView === 'contact' && <ContactView user={user} />}

      {activeView === 'admin' && user.is_staff && (
        <AdminDashboard currentUser={user} />
      )}
      <AppFooter />
    </div>
  )
}

export default App