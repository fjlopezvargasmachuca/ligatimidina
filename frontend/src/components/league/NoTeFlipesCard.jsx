import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '../../api/client'
import './NoTeFlipesCard.css'

function asArray(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  return []
}

function playerName(player) {
  return player.display_name || player.username || `Jugador #${player.id}`
}

const ROULETTE_COLORS = [
  '#eadcff', '#fce7f3', '#dbeafe', '#dcfce7', '#fef3c7', '#ede9fe',
  '#fee2e2', '#e0f2fe', '#f3e8ff', '#cffafe', '#ffedd5', '#ecfccb',
]
const REVERSE_COLORS = ['#312e81', '#3b0764', '#111827', '#581c87', '#1f2937', '#4c1d95']

function rouletteGeometry(options, selectedId, colors = ROULETTE_COLORS) {
  const total = options.reduce((sum, option) => sum + Number(option.weight || 0), 0)
  if (!total) return { gradient: '#eadcff', segments: [], rotation: 2160 }
  let cursor = 0
  const segments = options.map((option, index) => {
    const angle = (Number(option.weight || 0) / total) * 360
    const start = cursor
    const end = cursor + angle
    const center = start + angle / 2
    cursor = end
    return { ...option, color: colors[index % colors.length], start, end, center }
  })
  const selected = segments.find((segment) => String(segment.id) === String(selectedId))
  return {
    gradient: segments.map((segment) => `${segment.color} ${segment.start}deg ${segment.end}deg`).join(', '),
    segments,
    rotation: 360 * 9 - (selected?.center || 0),
  }
}

function buildOutcomeOptions(options, reverseProbability) {
  const p = Math.max(0, Math.min(100, Number(reverseProbability || 0)))
  const total = options.reduce((sum, option) => sum + Number(option.weight || 0), 0) || 1
  const normal = options.map((option) => ({
    ...option,
    weight: (100 - p) * (Number(option.weight || 0) / total),
  }))
  return [...normal, { id: 'reverse', name: 'REVERSE', description: 'La penalización vuelve al lanzador.', weight: p }]
}

function getErrorMessage(error, fallback) {
  if (typeof error?.data === 'string' && error.data) return error.data
  if (error?.data?.detail) return error.data.detail
  return fallback
}

export default function NoTeFlipesCard({ currentUserId }) {
  const [currentUser, setCurrentUser] = useState(currentUserId ? { id: currentUserId } : null)
  const [grants, setGrants] = useState([])
  const [players, setPlayers] = useState([])
  const [targetPlayer, setTargetPlayer] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [authenticated, setAuthenticated] = useState(true)
  const [roulette, setRoulette] = useState(null)

  async function load() {
    setLoading(true)
    setError('')
    try {
      if (!currentUserId) {
        setAuthenticated(false); setCurrentUser(null); setGrants([]); setPlayers([]); return
      }
      setCurrentUser({ id: currentUserId })
      setAuthenticated(true)
      const [grantsResponse, playersResponse] = await Promise.all([
        api.get('/handicaps/grants/mine/'),
        api.get('/accounts/players/'),
      ])
      setGrants(asArray(grantsResponse))
      setPlayers(asArray(playersResponse))
    } catch (requestError) {
      if (requestError?.status === 401 || requestError?.status === 403) {
        setAuthenticated(false); setCurrentUser(null); setGrants([]); setPlayers([]); return
      }
      setError(getErrorMessage(requestError, 'No se ha podido cargar tu No te flipes.'))
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [currentUserId])

  const availableGrants = useMemo(() => grants.filter((grant) => grant.available), [grants])
  const availableGrant = availableGrants[0] || null
  const targetOptions = useMemo(() => players
    .filter((player) => Number(player.id) !== Number(currentUser?.id))
    .filter((player) => player.is_active !== false)
    .sort((a, b) => playerName(a).localeCompare(playerName(b), 'es')), [players, currentUser])

  async function launch(event) {
    event.preventDefault()
    if (!availableGrant || !targetPlayer) return
    const target = targetOptions.find((player) => Number(player.id) === Number(targetPlayer))
    if (!target) { setError('Selecciona un jugador válido.'); return }
    if (!window.confirm(`¿Lanzar tu No te flipes contra ${playerName(target)}?\n\nLa ruleta te mostrará el resultado al terminar.`)) return

    setSaving(true); setError(''); setSuccess('')
    try {
      const response = await api.post(`/handicaps/grants/${availableGrant.id}/use/`, { target_player: Number(targetPlayer) })
      const handicap = response?.handicap
      const options = asArray(response?.roulette_options)
      if (!handicap || options.length === 0) throw new Error('El servidor no ha devuelto el resultado del lanzamiento.')

      const outcomeOptions = buildOutcomeOptions(options, handicap.reversal_probability)
      const selectedOutcome = handicap.reversed ? 'reverse' : handicap.definition
      setTargetPlayer('')
      setRoulette({
        phase: 'outcome',
        targetName: playerName(target),
        handicap,
        options,
        outcomeGeometry: rouletteGeometry(outcomeOptions, selectedOutcome),
        penaltyGeometry: rouletteGeometry(options, handicap.definition, REVERSE_COLORS),
      })
      setSuccess(handicap.reversed
        ? '¡Ha salido REVERSE! La penalización vuelve hacia ti y no cuenta para el límite antiacoso.'
        : 'No te flipes lanzado correctamente.')
      await load()
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No se ha podido lanzar el No te flipes.'))
    } finally { setSaving(false) }
  }

  function finishOutcomeSpin() {
    setRoulette((current) => {
      if (!current) return current
      return { ...current, phase: current.handicap.reversed ? 'reverse-intro' : 'result' }
    })
  }

  function beginReversePenalty() {
    setRoulette((current) => current ? { ...current, phase: 'reverse-penalty' } : current)
  }

  function finishReversePenalty() {
    setRoulette((current) => current ? { ...current, phase: 'result' } : current)
  }

  const rouletteOverlay = roulette ? createPortal(
    <div className={`no-te-flipes-roulette ${roulette.handicap.reversed ? 'is-reversed' : ''}`} role="dialog" aria-modal="true" aria-label="Resultado del No te flipes">
      <div className="no-te-flipes-roulette__backdrop" />
      <div className={`no-te-flipes-roulette__dialog ${roulette.phase === 'reverse-penalty' || roulette.phase === 'reverse-intro' ? 'reverse-dialog' : ''}`}>
        <div className="no-te-flipes-roulette__eyebrow">No te flipes</div>
        <h2>{roulette.phase === 'outcome' ? '¿Penalización o REVERSE?' : roulette.phase === 'reverse-intro' ? '¡REVERSE!' : roulette.phase === 'reverse-penalty' ? 'Ahora gira tu sanción…' : roulette.handicap.reversed ? 'El reverse se ha resuelto' : '¡Penalización lanzada!'}</h2>
        <p className="no-te-flipes-roulette__target">
          {roulette.handicap.reversed ? <>La penalización vuelve a <strong>ti</strong>.</> : <>Objetivo: <strong>{roulette.targetName}</strong></>}
        </p>

        {roulette.phase === 'outcome' && <RouletteWheel geometry={roulette.outcomeGeometry} onEnd={finishOutcomeSpin} />}

        {roulette.phase === 'reverse-intro' && <div className="reverse-announcement">
          <div className="reverse-word">REVERSE</div>
          <p>No cuenta como envío ni como recepción directa para el límite antiacoso. La segunda ruleta decidirá visualmente qué sanción te ha vuelto.</p>
          <button className="button button--primary" type="button" onClick={beginReversePenalty}>Girar la ruleta del reverse</button>
        </div>}

        {roulette.phase === 'reverse-penalty' && <RouletteWheel geometry={roulette.penaltyGeometry} onEnd={finishReversePenalty} dark />}

        {roulette.phase === 'result' && <div className="no-te-flipes-roulette__result">
          <div className="no-te-flipes-roulette__result-icon">{roulette.handicap.reversed ? '↩' : '⛓'}</div>
          <div>
            <span>{roulette.handicap.category_display || roulette.handicap.category || 'No te flipes'}</span>
            <strong>{roulette.handicap.name || roulette.handicap.definition_name}</strong>
            {roulette.handicap.description && <p>{roulette.handicap.description}</p>}
            <div className="no-te-flipes-roulette__metrics">
              <span>Penalización: <strong>-{roulette.handicap.penalty_points ?? 0}</strong></span>
              <span>Gracia: <strong>{roulette.handicap.grace_games ?? 0} partidas</strong></span>
              {roulette.handicap.reversed && <span>Prob. reverse usada: <strong>{roulette.handicap.reversal_probability}%</strong></span>}
            </div>
          </div>
        </div>}

        {roulette.phase === 'result' && <button className="button button--primary no-te-flipes-roulette__close" type="button" onClick={() => setRoulette(null)}>Entendido</button>}
      </div>
    </div>, document.body) : null

  if (!authenticated) return null
  if (loading) return <section className="card no-te-flipes-card"><div className="card__eyebrow">No te flipes</div><h2 className="card__title">Tu poder</h2><p className="no-te-flipes-card__muted">Comprobando si tienes un No te flipes disponible…</p></section>

  return <>
    <section className="card no-te-flipes-card">
      <div className="card__eyebrow">No te flipes</div>
      <div className="no-te-flipes-card__heading"><div><h2 className="card__title">Tu poder</h2><p className="no-te-flipes-card__intro">Elige objetivo. El backend decide el resultado; la ruleta solo lo representa.</p></div>{availableGrants.length > 0 && <span className="no-te-flipes-card__badge">{availableGrants.length === 1 ? '1 disponible' : `${availableGrants.length} disponibles`}</span>}</div>
      {availableGrant ? <form className="no-te-flipes-card__form" onSubmit={launch}>
        <label htmlFor="no-te-flipes-target">Jugador objetivo</label>
        <select id="no-te-flipes-target" value={targetPlayer} onChange={(event) => setTargetPlayer(event.target.value)} disabled={saving}>
          <option value="">Selecciona un jugador</option>{targetOptions.map((player) => <option key={player.id} value={player.id}>{playerName(player)}</option>)}
        </select>
        <button className="button button--primary" type="submit" disabled={saving || !targetPlayer}>{saving ? 'Lanzando…' : 'Lanzar No te flipes'}</button>
        <p className="no-te-flipes-card__secret">Existe una probabilidad baja de REVERSE. Si ocurre, aparecerá como una cuña propia y después se mostrará una segunda ruleta.</p>
      </form> : <div className="no-te-flipes-card__empty"><strong>No tienes un No te flipes disponible.</strong><span>Cuando el administrador te conceda uno aparecerá aquí.</span></div>}
      {error && <p className="no-te-flipes-card__message no-te-flipes-card__message--error" role="alert">{error}</p>}
      {success && <p className="no-te-flipes-card__message no-te-flipes-card__message--success" role="status">{success}</p>}
    </section>
    {rouletteOverlay}
  </>
}

function RouletteWheel({ geometry, onEnd, dark = false }) {
  return <div className={`no-te-flipes-roulette__wheel-wrap ${dark ? 'dark-wheel-wrap' : ''}`} aria-hidden="true">
    <span className="no-te-flipes-roulette__pointer">▼</span>
    <div className={`no-te-flipes-roulette__wheel no-te-flipes-roulette__wheel--spinning ${dark ? 'dark-wheel' : ''}`} onAnimationEnd={onEnd} style={{ '--roulette-gradient': `conic-gradient(${geometry.gradient})`, '--roulette-rotation': `${geometry.rotation}deg` }}>
      {geometry.segments.map((segment) => <span className="no-te-flipes-roulette__segment-label" key={segment.id} style={{ transform: `rotate(${segment.center}deg) translateY(var(--roulette-label-radius)) rotate(-${segment.center}deg)` }}>{segment.name}</span>)}
      <div className="no-te-flipes-roulette__wheel-center">{dark ? '↩' : '🎲'}</div>
    </div>
  </div>
}
