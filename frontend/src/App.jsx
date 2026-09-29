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

function LoginForm({ onAuthenticated, cookiesAllowed }) {
  const [form, setForm] = useState({
    username: '',
    password: '',
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    if (!cookiesAllowed) {
      setError('Para iniciar sesión debes aceptar las cookies técnicas necesarias para mantener la sesión y proteger los formularios.')
      return
    }
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

function RegisterForm({ onBack, cookiesAllowed }) {
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
    if (!cookiesAllowed) {
      setError('Para crear una cuenta debes aceptar las cookies técnicas necesarias para proteger el formulario.')
      return
    }
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
              <li>Las partidas de liga se plantean como Commander Bracket 3 (Upgraded): hasta 3 Game Changers, sin negación masiva de tierras ni combos intencionados de dos cartas que cierren la partida de forma temprana.</li>
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
            className={activeView === 'binders' ? 'active' : ''}
            onClick={() => onViewChange('binders')}
          >
            Carpetas
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
      return '✦'
    case 'HANDICAP_ACTIVE':
      return '☠'
    case 'PENALTY_ACTIVE':
      return 'Φ'
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
              <div className="public-deck-heading"><div><strong>{deck.name}</strong><span>{deck.commander}</span></div>{(deck.bracket || deck.analysis?.bracket) && <b className="public-bracket">Bracket {deck.bracket || deck.analysis?.bracket}</b>}</div>
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

function formatLeagueDate(value) {
  if (!value) return 'sin fecha'
  return new Date(`${value}T12:00:00`).toLocaleDateString('es-ES')
}

function PrizePoolCard({ pool }) {
  if (!pool) return null
  return <section className="league-card prize-pool-card">
    <div className="section-title"><span>Premios para el top 3</span><h2>Bote acumulado</h2></div>
    <div className="prize-pool-total"><strong>{Number(pool.total || 0).toFixed(2)} €</strong><span>Bote disponible</span></div>
    <div className="prize-podium">
      <div><b>1.º</b><strong>{Number(pool.top_1 || 0).toFixed(2)} €</strong><span>50%</span></div>
      <div><b>2.º</b><strong>{Number(pool.top_2 || 0).toFixed(2)} €</strong><span>30%</span></div>
      <div><b>3.º</b><strong>{Number(pool.top_3 || 0).toFixed(2)} €</strong><span>20%</span></div>
    </div>
    <p>Este mes hay <strong>{pool.premium_participants || 0}</strong> participantes premium y se reserva el <strong>{pool.prize_pool_percent || 0}%</strong> de sus cuotas para premios.</p>
    <small>Los premios se entregarán en material de Magic: The Gathering proporcionado por la tienda.</small>
  </section>
}

function FreeLeagueNotice({ settings }) {
  return <section className="league-card free-league-card">
    <div className="section-title"><span>Liga gratuita</span><h2>Hasta 3 partidas por jornada</h2></div>
    <p>{settings?.free_league_notice}</p>
  </section>
}

function MembershipCard({ user, settings }) {
  const premiumMode = settings?.mode === 'PREMIUM'
  if (!premiumMode) {
    return <section className="league-card membership-card">
      <div className="section-title"><span>Modalidad</span><h2>Liga gratuita</h2></div>
      <p>Todos los jugadores activos pueden disputar hasta <strong>3 partidas por jornada</strong>.</p>
      <p className="membership-warning">{settings?.free_league_notice}</p>
    </section>
  }
  const premium = Boolean(user?.subscription_active)
  return <section className="league-card membership-card">
    <div className="section-title"><span>Tu modalidad</span><h2>{premium ? 'Premium' : 'Estándar'}</h2></div>
    <p>{premium ? 'Puedes disputar hasta 3 partidas por jornada.' : 'La modalidad estándar permite 1 partida por jornada.'}</p>
    <p><strong>Premium: {Number(settings?.subscription_fee || 10).toFixed(2)} € al mes.</strong> Permite hasta 3 partidas por jornada y contribuye al bote mensual de premios.</p>
    <p className="membership-warning">El respeto es obligatorio en cualquier modalidad. Insultos, amenazas, acoso, trampas o faltas graves/reiteradas pueden implicar suspensión o expulsión de la liga aunque exista una suscripción abonada.</p>
    <a className="app-button paypal-button" href={settings?.paypal_url || 'https://paypal.me/machukador/10'} target="_blank" rel="noreferrer">Pagar suscripción con PayPal ↗</a>
    <small>La activación se valida desde administración. {user?.subscription_paid_until ? `Abonada hasta ${user.subscription_paid_until}.` : ''}</small>
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
      <div className="league-heading league-heading-centered">
        <img className="league-heading-logo" src="/liga-timidina-logo.svg" alt="Liga Timidina" />
        <div className="league-heading-title">
          <span>Clasificación</span>
          <h1>{data?.season?.name || 'Liga Timidina'}</h1>
        </div>

        <div className="league-season-date">
          <strong>Temporada {data?.season?.name || ''}:</strong>{' '}
          {formatLeagueDate(data?.season?.start_date)}
          {data?.season?.end_date ? ` – ${formatLeagueDate(data.season.end_date)}` : ''}
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

      <div className={`league-layout ${data?.league_settings?.mode === 'PREMIUM' ? 'league-layout--premium' : 'league-layout--free'}`}>
        <aside className="league-prize-sidebar">
          {data?.league_settings?.mode === 'PREMIUM'
            ? <PrizePoolCard pool={data?.prize_pool} />
            : <FreeLeagueNotice settings={data?.league_settings} />}
        </aside>
        <section className="league-card league-standings-card">
          <div className="league-table-wrap">
            <table className="league-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Jugador</th>
                  <th>Puntos</th>
                  <th>Victorias</th>
                  <th>Partidas</th>
                  <th title="Eliminaciones">Elim.</th>
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
      `¿Eliminar el mazo "${deck.name}"? Si ya se ha usado en una partida, puede estar protegido para conservar el histórico.`,
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
  const [leagueSettings, setLeagueSettings] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [response, deckResponse, settingsResponse] = await Promise.all([
          api.get(`/league/players/${user.id}/stats/`),
          api.get('/decks/mine/'),
          api.get('/league/settings/'),
        ])
        setStats(response)
        setProfileDecks(asArray(deckResponse))
        setLeagueSettings(settingsResponse)
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

          <MembershipCard user={user} settings={leagueSettings} />

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
            <div className="deck-list">{profileDecks.length ? profileDecks.map((deck) => <article className="deck-item" key={deck.id}><div className="deck-item-main"><div><strong>{deck.name}</strong><span>{deck.commander}</span></div>{(deck.bracket || deck.analysis?.bracket) && <span className="deck-status active">Bracket {deck.bracket || deck.analysis?.bracket}</span>}</div>{deck.deck_url && <a className="deckcheck-link" href={deck.deck_url} target="_blank" rel="noreferrer">Ver en DeckCheck ↗</a>}<DeckCardListViewer deck={deck}/></article>) : <div className="empty-message">No tienes mazos guardados.</div>}</div>
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

const BINDER_CONDITIONS = [
  ['MT', 'Mint'], ['NM', 'Near Mint'], ['EX', 'Excellent'], ['GD', 'Good'],
  ['LP', 'Light Played'], ['PL', 'Played'], ['PO', 'Poor'],
]

function BindersView({ user }) {
  const [binders, setBinders] = useState([])
  const [mine, setMine] = useState(null)
  const [selected, setSelected] = useState(null)
  const [page, setPage] = useState(0)
  const [flip, setFlip] = useState('')
  const [binderForm, setBinderForm] = useState({ title: 'Mi carpeta', description: '', public: true })
  const [cardForm, setCardForm] = useState({ card_name: '', condition: 'NM', foil: false, quantity: 1 })
  const [editingCardId, setEditingCardId] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  async function load(preferredId = null) {
    setError('')
    try {
      const [listResponse, mineResponse] = await Promise.all([
        api.get('/binders/'),
        api.get('/binders/mine/'),
      ])
      const list = asArray(listResponse)
      const myBinder = mineResponse?.exists ? mineResponse : null
      setBinders(list)
      setMine(myBinder)
      if (myBinder) setBinderForm({ title: myBinder.title || 'Mi carpeta', description: myBinder.description || '', public: myBinder.public !== false })
      const targetId = preferredId || selected?.id || myBinder?.id || list[0]?.id
      if (targetId) {
        const detail = Number(targetId) === Number(myBinder?.id) ? myBinder : await api.get(`/binders/${targetId}/`)
        setSelected(detail)
      } else {
        setSelected(null)
      }
    } catch (err) {
      setError(appErrorMessage(err, 'No se han podido cargar las carpetas.'))
    }
  }

  useEffect(() => { load() }, [user.id])

  useEffect(() => {
    const query = cardForm.card_name.trim()
    if (query.length < 2 || editingCardId) { setSuggestions([]); return undefined }
    const timer = setTimeout(async () => {
      try {
        const response = await api.get(`/decks/commanders/autocomplete/?q=${encodeURIComponent(query)}`)
        setSuggestions((response?.results || []).slice(0, 10))
      } catch { setSuggestions([]) }
    }, 250)
    return () => clearTimeout(timer)
  }, [cardForm.card_name, editingCardId])

  async function saveBinder(event) {
    event.preventDefault(); setSaving(true); setError(''); setNotice('')
    try {
      const response = await api.post('/binders/mine/', binderForm)
      setNotice(mine ? 'Carpeta actualizada.' : 'Carpeta creada.')
      setMine(response); setSelected(response); await load(response.id)
    } catch (err) { setError(appErrorMessage(err)) } finally { setSaving(false) }
  }

  function resetCardForm() {
    setEditingCardId(null)
    setCardForm({ card_name: '', condition: 'NM', foil: false, quantity: 1 })
    setSuggestions([])
  }

  async function saveCard(event) {
    event.preventDefault(); setSaving(true); setError(''); setNotice('')
    try {
      const payload = { ...cardForm, quantity: Number(cardForm.quantity) }
      if (editingCardId) await api.patch(`/binders/mine/cards/${editingCardId}/`, payload)
      else await api.post('/binders/mine/cards/', payload)
      setNotice(editingCardId ? 'Carta actualizada.' : 'Carta añadida a tu carpeta.')
      resetCardForm(); setPage(0); await load(mine?.id)
    } catch (err) { setError(appErrorMessage(err, 'No se ha podido guardar la carta.')) } finally { setSaving(false) }
  }

  function editCard(card) {
    setEditingCardId(card.id)
    setCardForm({ card_name: card.card_name, condition: card.condition, foil: Boolean(card.foil), quantity: card.quantity || 1 })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function deleteCard(card) {
    if (!window.confirm(`¿Quitar “${card.card_name}” de tu carpeta?`)) return
    try { await api.delete(`/binders/mine/cards/${card.id}/`); await load(mine?.id); setNotice('Carta eliminada de tu carpeta.') }
    catch (err) { setError(appErrorMessage(err)) }
  }

  async function refreshCardPrice(card) {
    setSaving(true); setError('')
    try { await api.post(`/binders/mine/cards/${card.id}/refresh/`); await load(mine?.id); setNotice(`Referencia de ${card.card_name} actualizada.`) }
    catch (err) { setError(appErrorMessage(err, 'No se ha podido actualizar la referencia.')) }
    finally { setSaving(false) }
  }

  async function openBinder(item) {
    try {
      const detail = Number(item.id) === Number(mine?.id) ? mine : await api.get(`/binders/${item.id}/`)
      setSelected(detail); setPage(0)
    } catch (err) { setError(appErrorMessage(err)) }
  }

  function turnPage(nextPage, direction) {
    setFlip(direction)
    window.setTimeout(() => { setPage(nextPage); setFlip('') }, 180)
  }

  const cards = selected?.cards || []
  const pageSize = 6
  const pageCount = Math.max(1, Math.ceil(cards.length / pageSize))
  const safePage = Math.min(page, pageCount - 1)
  const pageCards = cards.slice(safePage * pageSize, safePage * pageSize + pageSize)
  const ownSelected = Number(selected?.owner_id) === Number(user.id)

  return <main className="page-content binder-page">
    <div className="league-heading"><div><span>Comunidad</span><h1>Carpetas de cartas</h1><p>Escaparates personales para enseñar cartas disponibles. La Liga Timidina no intermedia pagos ni compraventas.</p></div></div>
    {error && <div className="app-alert error">{error}</div>}
    {notice && <div className="app-alert success">{notice}</div>}

    <div className="binder-layout">
      <aside className="league-card binder-owners">
        <div className="section-title"><span>Jugadores</span><h2>Carpetas públicas</h2></div>
        <div className="binder-owner-list">
          {mine && <button className={Number(selected?.id) === Number(mine.id) ? 'active' : ''} type="button" onClick={() => openBinder(mine)}><b>Mi carpeta</b><small>{mine.cards?.length || 0} cartas · editable</small></button>}
          {binders.filter((item) => Number(item.owner_id) !== Number(user.id)).map((item) => <button className={Number(selected?.id) === Number(item.id) ? 'active' : ''} type="button" key={item.id} onClick={() => openBinder(item)}><b>{item.owner_name || item.owner_username}</b><small>@{item.owner_username} · {item.cards_count} cartas</small></button>)}
          {!mine && binders.length === 0 && <div className="empty-message">Todavía no hay carpetas.</div>}
        </div>
      </aside>

      <section className="league-card binder-book-card">
        {selected ? <>
          <div className="binder-book-head"><div><span>{ownSelected ? 'Tu escaparate' : `@${selected.owner_username}`}</span><h2>{selected.title}</h2>{selected.description && <p>{selected.description}</p>}</div><b>Página {safePage + 1} / {pageCount}</b></div>
          <div className={`binder-sheet ${flip}`}>
            {pageCards.length ? pageCards.map((card) => <article className="binder-card" key={card.id}>
              <div className="binder-card-image">{card.image_url ? <img src={card.image_url} alt={card.card_name} loading="lazy" /> : <span>Sin imagen</span>}{card.foil && <b className="foil-badge">FOIL</b>}</div>
              <div className="binder-card-info"><strong>{card.card_name}</strong><span>{card.condition_display} · {card.quantity} ud.</span><div className="binder-price"><small>Referencia Cardmarket</small><b>{card.reference_price_eur != null ? `${Number(card.reference_price_eur).toFixed(2)} €` : 'Sin precio'}</b></div>{card.market_url && <a href={card.market_url} target="_blank" rel="noreferrer">Comprobar en Cardmarket ↗</a>}{ownSelected && <div className="binder-card-actions"><button type="button" onClick={() => editCard(card)}>Editar</button><button type="button" onClick={() => refreshCardPrice(card)} disabled={saving}>Actualizar precio</button><button type="button" onClick={() => deleteCard(card)}>Quitar</button></div>}</div>
            </article>) : <div className="binder-empty-page">Esta carpeta todavía no tiene cartas.</div>}
          </div>
          <div className="binder-page-controls"><button type="button" disabled={safePage <= 0 || flip} onClick={() => turnPage(safePage - 1, 'flip-back')}>← Página anterior</button><button type="button" disabled={safePage >= pageCount - 1 || flip} onClick={() => turnPage(safePage + 1, 'flip-next')}>Página siguiente →</button></div>
          <p className="binder-price-note">Los importes son referencias EUR obtenidas a través de Scryfall para la impresión consultada y pueden no coincidir con la oferta más barata en tiempo real. Comprueba edición, idioma, estado y acabado en Cardmarket antes de acordar una operación.</p>
        </> : <div className="binder-empty-page">Crea tu carpeta para empezar a exhibir cartas.</div>}
      </section>

      <aside className="league-card binder-editor">
        <div className="section-title"><span>Tu carpeta</span><h2>{mine ? 'Editar escaparate' : 'Crear carpeta'}</h2></div>
        <form className="binder-form" onSubmit={saveBinder}>
          <label>Título<input value={binderForm.title} maxLength={100} onChange={(e) => setBinderForm({...binderForm, title:e.target.value})} required /></label>
          <label>Descripción<textarea rows="3" value={binderForm.description} onChange={(e) => setBinderForm({...binderForm, description:e.target.value})} /></label>
          <label className="rules-accept"><input type="checkbox" checked={binderForm.public} onChange={(e) => setBinderForm({...binderForm, public:e.target.checked})}/><span>Visible para los demás jugadores</span></label>
          <button className="app-button primary" disabled={saving}>{mine ? 'Guardar carpeta' : 'Crear mi carpeta'}</button>
        </form>
        {mine && <form className="binder-form binder-card-form" onSubmit={saveCard}>
          <h3>{editingCardId ? 'Editar carta' : 'Añadir carta'}</h3>
          <label className="binder-autocomplete">Carta<input value={cardForm.card_name} autoComplete="off" onChange={(e) => setCardForm({...cardForm, card_name:e.target.value})} required />{suggestions.length > 0 && <div className="binder-suggestions">{suggestions.map((name) => <button type="button" key={name} onClick={() => { setCardForm({...cardForm, card_name:name}); setSuggestions([]) }}>{name}</button>)}</div>}</label>
          <div className="binder-form-row"><label>Estado<select value={cardForm.condition} onChange={(e) => setCardForm({...cardForm, condition:e.target.value})}>{BINDER_CONDITIONS.map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Cantidad<input type="number" min="1" max="99" value={cardForm.quantity} onChange={(e) => setCardForm({...cardForm, quantity:e.target.value})}/></label></div>
          <label className="rules-accept"><input type="checkbox" checked={cardForm.foil} onChange={(e) => setCardForm({...cardForm, foil:e.target.checked})}/><span>Foil</span></label>
          <div className="binder-card-actions"><button className="app-button primary" disabled={saving}>{editingCardId ? 'Guardar cambios' : 'Añadir a carpeta'}</button>{editingCardId && <button className="app-button ghost" type="button" onClick={resetCardForm}>Cancelar</button>}</div>
        </form>}
      </aside>
    </div>
  </main>
}

function ContactView({ user }) {
  const [messages, setMessages] = useState([])
  const [form, setForm] = useState({ subject: '', message: '' })
  const [replyDrafts, setReplyDrafts] = useState({})
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [collapsed, setCollapsed] = useState({})

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

  async function deleteConversation(item) {
    if (!window.confirm(`¿Eliminar definitivamente la conversación “${item.subject}”?`)) return
    try {
      await api.delete(`/accounts/contact/${item.id}/`)
      await load()
    } catch (err) { setError(appErrorMessage(err)) }
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
            <div className="contact-thread-badges"><span>{item.closed ? 'Cerrada' : 'Abierta'}</span>{!item.read && <b>Nueva</b>}<button className="contact-collapse" type="button" onClick={() => setCollapsed((current) => ({...current, [item.id]: !current[item.id]}))}>{collapsed[item.id] ? 'Mostrar' : 'Minimizar'}</button></div>
          </div>
          {!collapsed[item.id] && <>
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
            <button className="app-button danger" type="button" onClick={() => deleteConversation(item)}>Eliminar</button>
          </div>}
          </>}
        </article>) : <div className="empty-message">No hay mensajes.</div>}
      </div>
    </section>
  </main>
}

const COOKIE_CONSENT_KEY = 'liga_timidina_cookie_consent'

function CookieConsent({ consent, onAccept, onReject }) {
  if (consent === 'accepted') return null
  return <div className="cookie-banner" role="dialog" aria-live="polite" aria-label="Preferencias de cookies">
    <div>
      <strong>Cookies técnicas</strong>
      <p>La aplicación solo utiliza cookies técnicas de sesión y seguridad. Son necesarias para iniciar sesión y proteger los formularios; no usamos cookies publicitarias ni de analítica.</p>
      {consent === 'rejected' && <small>Has rechazado las cookies. No se iniciará ninguna sesión mientras mantengas esta elección.</small>}
    </div>
    <div className="cookie-actions">
      <button className="app-button ghost" type="button" onClick={onReject}>Rechazar</button>
      <button className="app-button primary" type="button" onClick={onAccept}>Aceptar cookies técnicas</button>
    </div>
  </div>
}


function LeagueRulesModal({ onClose }) {
  return createPortal(<div className="profile-modal-backdrop" onMouseDown={onClose}><section className="profile-modal rules-modal" onMouseDown={(e) => e.stopPropagation()}><button className="profile-modal-close" type="button" onClick={onClose}>×</button><span className="event-modal-eyebrow">Normas permanentes</span><h2>Normas de la Liga Timidina · Commander Bracket 3</h2><div className="league-rules-full"><h3>Formato de juego</h3><ul><li>Commander multijugador: mazo de 100 cartas contando el comandante, identidad de color y singleton salvo tierras básicas o cartas que indiquen lo contrario.</li><li>Las mesas se plantean normalmente para 4 jugadores. Cada jugador empieza con 40 vidas; recibir 21 o más puntos de daño de combate del mismo comandante durante la partida hace perder la partida.</li><li>La liga se juega con intención de <strong>Bracket 3 · Upgraded</strong>: mazos mejorados, con buena sinergia y calidad de cartas, pero sin planteamiento cEDH.</li><li>Se permiten hasta <strong>3 Game Changers</strong>. No se permite negación masiva de tierras ni combos intencionados de dos cartas que cierren la partida de forma temprana. Los turnos extra no deben encadenarse ni formar bucles.</li><li>Antes de empezar, los jugadores deben comunicar de buena fe elementos relevantes del mazo que puedan cambiar las expectativas de la mesa.</li></ul><h3>Convivencia</h3><ul><li>El respeto es obligatorio con jugadores, administración, organización y personal de la tienda, tanto en liga gratuita como de pago.</li><li>No se toleran insultos, amenazas, acoso, discriminación, trampas, manipulación de resultados ni hostigamiento mediante la aplicación.</li><li>Las discrepancias se tratan con calma y se trasladan a administración. Las conductas graves o reiteradas pueden implicar suspensión o <strong>expulsión de la liga</strong>, aunque el participante tenga una suscripción abonada.</li></ul><p className="rules-source-note">Las reglas de construcción y la lista de Game Changers pueden actualizarse. Consulta también la referencia oficial de Commander de Magic.</p><a className="app-button ghost" href="https://magic.wizards.com/en/formats/commander" target="_blank" rel="noreferrer">Reglas oficiales de Commander ↗</a></div></section></div>, document.body)
}

function AppFooter() {
  const [showRules, setShowRules] = useState(false)
  return <><footer className="app-footer">
    <span>© {new Date().getFullYear()} Liga Timidina · Todos los derechos reservados. <button className="footer-rules-link" type="button" onClick={() => setShowRules(true)}>Normas de la liga</button></span>
    <span className="partner-strip">Colaboraciones / servicios:
      <a href="https://magic.wizards.com/" target="_blank" rel="noreferrer"><img src="/partners/magic.svg" alt="" />Magic: The Gathering</a>
      <a href="https://deckcheck.co/" target="_blank" rel="noreferrer"><img src="/partners/deckcheck.svg" alt="" />DeckCheck</a>
      <a href="https://www.adadoypluma.es/" target="_blank" rel="noreferrer"><img src="/partners/adadoypluma.svg" alt="" />A Dado y Pluma · Triana</a>
    </span>
  </footer>{showRules && <LeagueRulesModal onClose={() => setShowRules(false)} />}</>
}

function App() {
  const [user, setUser] = useState(null)
  const [cookieConsent, setCookieConsent] = useState(() => localStorage.getItem(COOKIE_CONSENT_KEY))
  const [loading, setLoading] = useState(cookieConsent === 'accepted')
  const [authMode, setAuthMode] = useState('login')
  const [activeView, setActiveView] = useState('league')

  useEffect(() => {
    if (cookieConsent !== 'accepted') {
      setLoading(false)
      setUser(null)
      return
    }
    setLoading(true)
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
  }, [cookieConsent])

  function acceptCookies() {
    localStorage.setItem(COOKIE_CONSENT_KEY, 'accepted')
    setCookieConsent('accepted')
  }

  function rejectCookies() {
    localStorage.setItem(COOKIE_CONSENT_KEY, 'rejected')
    setCookieConsent('rejected')
    setUser(null)
    document.cookie = 'csrftoken=; Max-Age=0; path=/'
  }

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
          <RegisterForm onAuthenticated={handleAuthenticated} onBack={() => setAuthMode('login')} cookiesAllowed={cookieConsent === 'accepted'} />
          <AppFooter />
          <CookieConsent consent={cookieConsent} onAccept={acceptCookies} onReject={rejectCookies} />
        </>
      )
    }

    return (
      <>
        <LoginForm
          onAuthenticated={handleAuthenticated}
          cookiesAllowed={cookieConsent === 'accepted'}
        />

        <button
          className="auth-register-link"
          onClick={() => setAuthMode('register')}
        >
          ¿Todavía no tienes cuenta? Crear cuenta
        </button>
        <AppFooter />
        <CookieConsent consent={cookieConsent} onAccept={acceptCookies} onReject={rejectCookies} />
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

      {activeView === 'binders' && (
        <BindersView user={user} />
      )}

      {activeView === 'profile' && (
        <ProfileView user={user} onUserUpdated={setUser} />
      )}

      {activeView === 'contact' && <ContactView user={user} />}

      {activeView === 'admin' && user.is_staff && (
        <AdminDashboard currentUser={user} />
      )}
      <AppFooter />
      <CookieConsent consent={cookieConsent} onAccept={acceptCookies} onReject={rejectCookies} />
    </div>
  )
}

export default App