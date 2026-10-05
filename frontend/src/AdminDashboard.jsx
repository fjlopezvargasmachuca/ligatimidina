import { useEffect, useMemo, useState } from 'react'
import { api } from './api/client'
import './AdminDashboard.css'

function nowLocalInputValue() {
  const now = new Date()
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}

function emptyMatchForm() {
  return { league_week: '', played_at: nowLocalInputValue(), notes: '' }
}

const EMPTY_PLAYER_FORM = {
  player: '',
  deck: '',
  starting_position: '',
  final_position: '',
  first_play_of_deck: false,
  completed_weekly_event: false,
  conceded: false,
  concession_penalty: false,
  notes: '',
}

const EMPTY_ELIMINATION_FORM = {
  killer: '',
  victim: '',
  turn: '',
  first_elimination: false,
}

const SCORING_RULE_OPTIONS = [
  { code: 'WIN', label: 'Victoria' },
  { code: 'SECOND_PLACE', label: 'Segundo puesto' },
  { code: 'THIRD_PLACE', label: 'Tercer puesto' },
  { code: 'FIRST_DECK_PLAY', label: 'Primera partida con este mazo' },
  { code: 'ORIGINAL_DECK', label: 'Mazo original validado' },
  { code: 'WEEKLY_EVENT', label: 'Evento semanal' },
  { code: 'FIRST_ELIMINATION', label: 'Primera eliminación' },
  { code: 'ELIMINATION', label: 'Eliminación' },
  { code: 'CONCESSION', label: 'Penalización por concesión' },
]

const EMPTY_SCORING_RULE_FORM = {
  season: '',
  code: '',
  name: '',
  points: '',
  description: '',
  active: true,
}

const EMPTY_ADMIN_USER_FORM = {
  username: '',
  first_name: '',
  last_name: '',
  display_name: '',
  email: '',
  password: '',
  password_confirm: '',
  is_active: true,
  is_staff: false,
  membership_plan: 'FREE',
  subscription_paid_until: '',
}

function asArray(data) {
  if (Array.isArray(data)) {
    return data
  }

  if (Array.isArray(data?.results)) {
    return data.results
  }

  return []
}

function formatDate(value) {
  if (!value) return '—'

  return new Intl.DateTimeFormat('es-ES', {
    dateStyle: 'medium',
  }).format(new Date(`${value}T00:00:00`))
}

function formatDateTime(value) {
  if (!value) return '—'

  return new Intl.DateTimeFormat('es-ES', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value))
}

function getErrorMessage(error) {
  if (!error) {
    return 'Ha ocurrido un error.'
  }

  if (typeof error.data === 'string' && error.data) {
    return error.data
  }

  if (error.data && typeof error.data === 'object') {
    const messages = []

    Object.entries(error.data).forEach(([field, value]) => {
      if (Array.isArray(value)) {
        messages.push(`${field}: ${value.join(', ')}`)
      } else if (typeof value === 'string') {
        messages.push(`${field}: ${value}`)
      } else {
        messages.push(`${field}: ${JSON.stringify(value)}`)
      }
    })

    if (messages.length) {
      return messages.join(' · ')
    }
  }

  return error.message || 'Ha ocurrido un error.'
}

function SectionHeader({ eyebrow, title, description }) {
  return (
    <div className="admin-section-header">
      <div>
        {eyebrow && <span className="admin-eyebrow">{eyebrow}</span>}
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
    </div>
  )
}

function StatusBadge({ children, tone = 'neutral' }) {
  return (
    <span className={`admin-status admin-status-${tone}`}>
      {children}
    </span>
  )
}

function StatCard({ label, value, detail }) {
  return (
    <article className="admin-stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {detail && <small>{detail}</small>}
    </article>
  )
}

function AdminNavIcon({ type }) {
  const paths = {
    dashboard: 'M4 12 12 5l8 7v7a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z',
    users: 'M8 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm8 1a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM2 21v-2a6 6 0 0 1 12 0v2m1 0v-1a5 5 0 0 1 7-4.6',
    seasons: 'M6 3v3m12-3v3M4 9h16M5 5h14a1 1 0 0 1 1 1v14H4V6a1 1 0 0 1 1-1Zm3 8h3v3H8zm5 0h3v3h-3z',
    weeks: 'M5 4h14v16H5zM8 8h8M8 12h8M8 16h5',
    events: 'm12 3 1.7 4.3L18 9l-4.3 1.7L12 15l-1.7-4.3L6 9l4.3-1.7L12 3Zm6 11 .9 2.1L21 17l-2.1.9L18 20l-.9-2.1L15 17l2.1-.9L18 14Z',
    scoring: 'M7 4h10v4a5 5 0 0 1-10 0V4Zm0 2H4v2a4 4 0 0 0 4 4m9-6h3v2a4 4 0 0 1-4 4M12 13v5m-4 2h8',
    handicaps: 'M12 3v18M5 7h14M7 7l-4 7h8L7 7Zm10 0-4 7h8l-4-7Z',
    matches: 'M7 4h10l2 13H5L7 4Zm2 4h6m-5 4h4M8 20h8',
    settings: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm0-5v2m0 14v2M3 12h2m14 0h2M5.6 5.6 7 7m10 10 1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4',
  }
  return <svg className="admin-nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d={paths[type] || paths.dashboard} /></svg>
}

function AdminDashboard({ currentUser }) {
  const [activeSection, setActiveSection] = useState('dashboard')
  const [leagueSettings, setLeagueSettings] = useState(null)
  const [prizePool, setPrizePool] = useState(null)
  const [settingsForm, setSettingsForm] = useState({ mode: 'PREMIUM', subscription_fee: '10.00', prize_pool_percent: '20.00', paypal_url: 'https://paypal.me/machukador/10', free_league_notice: '' })

  const [seasons, setSeasons] = useState([])
  const [weeks, setWeeks] = useState([])
  const [events, setEvents] = useState([])
  const [players, setPlayers] = useState([])
  const [adminPlayers, setAdminPlayers] = useState([])
  const [decks, setDecks] = useState([])
  const [matches, setMatches] = useState([])

  const [currentWeek, setCurrentWeek] = useState(null)
  const [selectedMatch, setSelectedMatch] = useState(null)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [matchForm, setMatchForm] = useState(() => emptyMatchForm())
  const [playerForm, setPlayerForm] = useState(EMPTY_PLAYER_FORM)
  const [eliminationForm, setEliminationForm] = useState(
    EMPTY_ELIMINATION_FORM,
  )
  const [scoringRules, setScoringRules] = useState([])
  const [scoringRuleForm, setScoringRuleForm] = useState(
    EMPTY_SCORING_RULE_FORM,
  )
  const [editingScoringRuleId, setEditingScoringRuleId] = useState(null)
  const [editingSeasonId, setEditingSeasonId] = useState(null)
  const [editingEventId, setEditingEventId] = useState(null)
  const [userForm, setUserForm] = useState(EMPTY_ADMIN_USER_FORM)
  const [editingUserId, setEditingUserId] = useState(null)

  const [handicapCategories, setHandicapCategories] = useState([])
  const [handicapDefinitions, setHandicapDefinitions] = useState([])
  const [assignedHandicaps, setAssignedHandicaps] = useState([])
  const [handicapGrants, setHandicapGrants] = useState([])
  const [handicapForm, setHandicapForm] = useState({
    player: '',
    season: '',
    award_reason: '',
  })
  const [handicapDefinitionForm, setHandicapDefinitionForm] = useState({
    name: '',
    description: '',
    category: 'WEAK',
    selection_weight: 1,
    grace_games: 3,
    penalty_points: 2,
    reversal_base_percent: 8,
    reversal_rank_step_percent: 0.5,
    reversal_min_percent: 2,
    reversal_max_percent: 12,
    active: true,
  })
  const [editingHandicapDefinitionId, setEditingHandicapDefinitionId] = useState(null)

  const [seasonForm, setSeasonForm] = useState({
    name: '',
    start_date: '',
    end_date: '',
    active: true,
  })

  const [weekForm, setWeekForm] = useState({
    season: '',
    date: '',
    weekly_event: '',
  })

  const [eventForm, setEventForm] = useState({
    name: '',
    description: '',
    rules: '',
    extra_points: 0,
    active: true,
  })

  const [weekEventDrafts, setWeekEventDrafts] = useState({})

  const activeSeason = useMemo(
    () => seasons.find((season) => season.active) || null,
    [seasons],
  )

  const activePlayers = useMemo(
    () =>
      [...players].sort((a, b) =>
        (a.display_name || a.username).localeCompare(
          b.display_name || b.username,
          'es',
        ),
      ),
    [players],
  )

  const selectedPlayerDecks = useMemo(() => {
    if (!playerForm.player) return []

    return decks
      .filter(
        (deck) =>
          deck.active &&
          String(deck.owner) === String(playerForm.player),
      )
      .sort((a, b) => a.name.localeCompare(b.name, 'es'))
  }, [decks, playerForm.player])

  const matchPlayerIds = useMemo(() => {
    if (!selectedMatch?.players) return []

    return selectedMatch.players.map((item) => Number(item.player))
  }, [selectedMatch])

  const matchPlayerOptions = useMemo(() => {
    if (!selectedMatch?.players) return []

    const registeredPlayerIds = new Set(
      selectedMatch.players.map((item) => Number(item.player)),
    )

    return players
      .filter((player) => registeredPlayerIds.has(Number(player.id)))
      .map((player) => ({
        id: Number(player.id),
        name: player.display_name || player.username,
      }))
      .sort((a, b) => a.name.localeCompare(b.name, 'es'))
  }, [players, selectedMatch])

  async function loadInitialData() {
    setLoading(true)
    setError('')

    try {
      const [
        seasonsResponse,
        weeksResponse,
        eventsResponse,
        playersResponse,
        decksResponse,
        matchesResponse,
      ] = await Promise.all([
        api.get('/league/seasons/'),
        api.get('/league/weeks/'),
        api.get('/events/'),
        api.get('/accounts/players/'),
        api.get('/decks/'),
        api.get('/matches/'),
      ])

      setSeasons(asArray(seasonsResponse))
      setWeeks(asArray(weeksResponse))
      setEvents(asArray(eventsResponse))
      setPlayers(asArray(playersResponse))
      setDecks(asArray(decksResponse))
      setMatches(asArray(matchesResponse))

      try {
        const [settingsResponse, poolResponse] = await Promise.all([
          api.get('/league/settings/'),
          api.get('/league/prize-pool/').catch(() => null),
        ])
        setLeagueSettings(settingsResponse)
        setSettingsForm({
          mode: settingsResponse.mode,
          subscription_fee: settingsResponse.subscription_fee,
          prize_pool_percent: settingsResponse.prize_pool_percent,
          paypal_url: settingsResponse.paypal_url,
          free_league_notice: settingsResponse.free_league_notice,
        })
        setPrizePool(poolResponse?.enabled === false ? null : poolResponse)
      } catch {
        setLeagueSettings(null)
        setPrizePool(null)
      }

      try {
        const currentWeekResponse = await api.get(
          '/league/current-week/',
        )
        setCurrentWeek(currentWeekResponse)
      } catch {
        setCurrentWeek(null)
      }
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

  async function refreshSection() {
    setError('')

    try {
      if (activeSection === 'dashboard') {
        const [seasonsResponse, weeksResponse, matchesResponse] =
          await Promise.all([
            api.get('/league/seasons/'),
            api.get('/league/weeks/'),
            api.get('/matches/'),
          ])

        setSeasons(asArray(seasonsResponse))
        setWeeks(asArray(weeksResponse))
        setMatches(asArray(matchesResponse))

        try {
          const currentWeekResponse = await api.get(
            '/league/current-week/',
          )
          setCurrentWeek(currentWeekResponse)
        } catch {
          setCurrentWeek(null)
        }
      }

      if (activeSection === 'seasons') {
        const response = await api.get('/league/seasons/')
        setSeasons(asArray(response))
      }

      if (activeSection === 'weeks') {
        const [weeksResponse, seasonsResponse, eventsResponse] =
          await Promise.all([
            api.get('/league/weeks/'),
            api.get('/league/seasons/'),
            api.get('/events/'),
          ])

        setWeeks(asArray(weeksResponse))
        setSeasons(asArray(seasonsResponse))
        setEvents(asArray(eventsResponse))
      }

      if (activeSection === 'events') {
        const response = await api.get('/events/')
        setEvents(asArray(response))
      }

      if (activeSection === 'settings') {
        const [settingsResponse, poolResponse] = await Promise.all([
          api.get('/league/settings/'),
          api.get('/league/prize-pool/').catch(() => null),
        ])
        setLeagueSettings(settingsResponse)
        setSettingsForm({
          mode: settingsResponse.mode,
          subscription_fee: settingsResponse.subscription_fee,
          prize_pool_percent: settingsResponse.prize_pool_percent,
          paypal_url: settingsResponse.paypal_url,
          free_league_notice: settingsResponse.free_league_notice,
        })
        setPrizePool(poolResponse?.enabled === false ? null : poolResponse)
      }

      if (activeSection === 'scoring') {
        const response = await api.get('/league/scoring-rules/')
        setScoringRules(asArray(response))
      }

      if (activeSection === 'handicaps') {
        const [categoriesResponse, definitionsResponse, handicapsResponse, grantsResponse, playersResponse, seasonsResponse] = await Promise.all([
          api.get('/handicaps/categories/'),
          api.get('/handicaps/definitions/'),
          api.get('/handicaps/'),
          api.get('/handicaps/grants/'),
          api.get('/accounts/players/'),
          api.get('/league/seasons/'),
        ])

        setHandicapCategories(asArray(categoriesResponse))
        setHandicapDefinitions(asArray(definitionsResponse))
        setAssignedHandicaps(asArray(handicapsResponse))
        setHandicapGrants(asArray(grantsResponse))
        setPlayers(asArray(playersResponse))
        setSeasons(asArray(seasonsResponse))
      }

      if (activeSection === 'users') {
        const [adminPlayersResponse, playersResponse] = await Promise.all([
          api.get('/accounts/admin/players/'),
          api.get('/accounts/players/'),
        ])
        setAdminPlayers(asArray(adminPlayersResponse))
        setPlayers(asArray(playersResponse))
      }

      if (activeSection === 'matches') {
        const [
          matchesResponse,
          weeksResponse,
          playersResponse,
          decksResponse,
        ] = await Promise.all([
          api.get('/matches/'),
          api.get('/league/weeks/'),
          api.get('/accounts/players/'),
          api.get('/decks/'),
        ])

        setMatches(asArray(matchesResponse))
        setWeeks(asArray(weeksResponse))
        setPlayers(asArray(playersResponse))
        setDecks(asArray(decksResponse))

        if (selectedMatch?.id) {
          try {
            const detail = await api.get(
              `/matches/${selectedMatch.id}/`,
            )
            setSelectedMatch(detail)
          } catch {
            setSelectedMatch(null)
          }
        }
      }
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    }
  }

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (!loading) {
      refreshSection()
    }
    // Intencionadamente solo cambia al navegar entre secciones.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSection])

  useEffect(() => {
    setSuccess('')
    setError('')
  }, [activeSection])

  function showSuccess(message) {
    setSuccess(message)
    setError('')
  }

  function showError(requestError) {
    setSuccess('')
    setError(getErrorMessage(requestError))
  }

  function handleMatchFieldChange(event) {
    const { name, value } = event.target

    setMatchForm((current) => ({
      ...current,
      [name]: value,
    }))
  }

  function handlePlayerFieldChange(event) {
    const { name, value, type, checked } = event.target

    setPlayerForm((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value,
      ...(name === 'player' ? { deck: '' } : {}),
    }))
  }

  function handleEliminationFieldChange(event) {
    const { name, value, type, checked } = event.target

    setEliminationForm((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value,
      ...(name === 'killer' ? { victim: '' } : {}),
    }))
  }

  async function createMatch(event) {
    event.preventDefault()
    setSaving(true)
    setError('')

    try {
      const response = await api.post('/matches/create/', {
        league_week: Number(matchForm.league_week),
        played_at: matchForm.played_at,
        notes: matchForm.notes,
      })

      showSuccess(`Partida #${response.id} creada.`)

      setMatchForm(emptyMatchForm())

      await refreshMatches()

      const detail = await api.get(`/matches/${response.id}/`)
      setSelectedMatch(detail)
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  async function refreshMatches() {
    const response = await api.get('/matches/')
    setMatches(asArray(response))
  }

  async function openMatch(matchId) {
    setError('')

    try {
      const response = await api.get(`/matches/${matchId}/`)
      setSelectedMatch(response)
      setActiveSection('matches')
    } catch (requestError) {
      showError(requestError)
    }
  }

  async function addPlayerToMatch(event) {
    event.preventDefault()

    if (!selectedMatch) return

    setSaving(true)
    setError('')

    try {
      await api.post(
        `/matches/${selectedMatch.id}/players/create/`,
        {
          player: Number(playerForm.player),
          deck: Number(playerForm.deck),
          starting_position: playerForm.starting_position
            ? Number(playerForm.starting_position)
            : null,
          final_position: playerForm.final_position
            ? Number(playerForm.final_position)
            : null,
          first_play_of_deck: playerForm.first_play_of_deck,
          completed_weekly_event:
            playerForm.completed_weekly_event,
          conceded: playerForm.conceded,
          concession_penalty: playerForm.concession_penalty,
          notes: playerForm.notes,
        },
      )

      const detail = await api.get(
        `/matches/${selectedMatch.id}/`,
      )

      setSelectedMatch(detail)
      setPlayerForm(EMPTY_PLAYER_FORM)
      showSuccess('Jugador añadido a la partida.')
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  async function updateMatchPlayer(playerResultId, payload) {
    if (!selectedMatch) return

    setSaving(true)
    setError('')

    try {
      const response = await api.patch(
        `/matches/${selectedMatch.id}/players/${playerResultId}/`,
        payload,
      )

      setSelectedMatch((current) =>
        current
          ? {
              ...current,
              players: current.players.map((player) =>
                player.id === response.id ? response : player,
              ),
            }
          : current,
      )

      showSuccess('Resultado del jugador actualizado.')
    } catch (requestError) {
      showError(requestError)
      throw requestError
    } finally {
      setSaving(false)
    }
  }

  async function addElimination(event) {
    event.preventDefault()

    if (!selectedMatch) return

    setSaving(true)
    setError('')

    try {
      await api.post(
        `/matches/${selectedMatch.id}/eliminations/create/`,
        {
          killer: Number(eliminationForm.killer),
          victim: Number(eliminationForm.victim),
          turn: eliminationForm.turn
            ? Number(eliminationForm.turn)
            : null,
          first_elimination:
            eliminationForm.first_elimination,
        },
      )

      const detail = await api.get(
        `/matches/${selectedMatch.id}/`,
      )

      setSelectedMatch(detail)
      setEliminationForm(EMPTY_ELIMINATION_FORM)
      showSuccess('Eliminación registrada.')
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  async function closeMatch() {
    if (!selectedMatch) return

    const confirmed = window.confirm(
      '¿Cerrar esta partida? Después de cerrarla no se podrán modificar sus resultados.',
    )

    if (!confirmed) return

    setSaving(true)
    setError('')

    try {
      await api.post(`/matches/${selectedMatch.id}/close/`)

      const detail = await api.get(
        `/matches/${selectedMatch.id}/`,
      )

      setSelectedMatch(detail)

      await refreshMatches()

      showSuccess('Partida cerrada correctamente.')
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  async function deleteClosedMatch() {
    if (!selectedMatch?.closed) return

    const confirmation = window.prompt(
      'Esta operación elimina una partida cerrada y recalcula la temporada. Para continuar escribe exactamente: ELIMINAR PARTIDA',
    )

    if (confirmation === null) return

    if (confirmation !== 'ELIMINAR PARTIDA') {
      setError(
        'Confirmación incorrecta. La partida no se ha eliminado.',
      )
      return
    }

    setSaving(true)
    setError('')

    try {
      await api.delete(`/matches/${selectedMatch.id}/delete/`, {
        body: { confirmation },
      })

      setSelectedMatch(null)
      await refreshSection()
      showSuccess(
        'Partida eliminada. La temporada y los anchors históricos afectados se han recalculado.',
      )
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  function handleScoringRuleFieldChange(event) {
    const { name, value, type, checked } = event.target

    setScoringRuleForm((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  function startEditingScoringRule(rule) {
    setEditingScoringRuleId(rule.id)
    setScoringRuleForm({
      season: String(rule.season),
      code: rule.code,
      name: rule.name,
      points: String(rule.points),
      description: rule.description || '',
      active: rule.active,
    })
  }

  function resetScoringRuleForm() {
    setEditingScoringRuleId(null)
    setScoringRuleForm(EMPTY_SCORING_RULE_FORM)
  }

  async function saveScoringRule(event) {
    event.preventDefault()
    setSaving(true)
    setError('')

    try {
      const payload = {
        season: Number(scoringRuleForm.season),
        code: scoringRuleForm.code,
        name: scoringRuleForm.name.trim(),
        points: Number(scoringRuleForm.points),
        description: scoringRuleForm.description.trim(),
        active: scoringRuleForm.active,
      }

      if (editingScoringRuleId) {
        await api.patch(
          `/league/scoring-rules/${editingScoringRuleId}/`,
          payload,
        )
        showSuccess('Regla de puntuación actualizada.')
      } else {
        await api.post('/league/scoring-rules/create/', payload)
        showSuccess('Regla de puntuación creada.')
      }

      const response = await api.get('/league/scoring-rules/')
      setScoringRules(asArray(response))
      resetScoringRuleForm()
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  async function deleteScoringRule(rule) {
    if (!window.confirm(`¿Eliminar la regla “${rule.name}”? Solo se podrá borrar si aún no forma parte de una jornada cerrada.`)) return
    setSaving(true)
    setError('')
    try {
      await api.delete(`/league/scoring-rules/${rule.id}/`)
      setScoringRules(asArray(await api.get('/league/scoring-rules/')))
      if (Number(editingScoringRuleId) === Number(rule.id)) resetScoringRuleForm()
      showSuccess('Regla de puntuación eliminada.')
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  async function toggleScoringRule(rule) {
    setSaving(true)
    setError('')

    try {
      await api.patch(`/league/scoring-rules/${rule.id}/`, {
        active: !rule.active,
      })

      const response = await api.get('/league/scoring-rules/')
      setScoringRules(asArray(response))
      showSuccess(
        rule.active
          ? 'Regla desactivada.'
          : 'Regla activada.',
      )
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  function handleHandicapFormChange(event) {
    const { name, value } = event.target
    setHandicapForm((current) => ({ ...current, [name]: value }))
  }

  function handleHandicapDefinitionFieldChange(event) {
    const { name, value, type, checked } = event.target
    setHandicapDefinitionForm((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  function resetHandicapDefinitionForm() {
    setEditingHandicapDefinitionId(null)
    setHandicapDefinitionForm({
      name: '',
      description: '',
      category: 'WEAK',
      selection_weight: 1,
      grace_games: 3,
      penalty_points: 2,
      reversal_base_percent: 8,
      reversal_rank_step_percent: 0.5,
      reversal_min_percent: 2,
      reversal_max_percent: 12,
      active: true,
    })
  }

  function editHandicapDefinition(definition) {
    setEditingHandicapDefinitionId(definition.id)
    setHandicapDefinitionForm({
      name: definition.name || '',
      description: definition.description || '',
      category: definition.category || 'WEAK',
      selection_weight: definition.selection_weight ?? 1,
      grace_games: definition.grace_games ?? 3,
      penalty_points: definition.penalty_points ?? 2,
      reversal_base_percent: definition.reversal_base_percent ?? 50,
      reversal_rank_step_percent: definition.reversal_rank_step_percent ?? 5,
      reversal_min_percent: definition.reversal_min_percent ?? 5,
      reversal_max_percent: definition.reversal_max_percent ?? 95,
      active: definition.active !== false,
    })
  }

  async function saveHandicapDefinition(event) {
    event.preventDefault()
    setSaving(true)
    setError('')

    try {
      const payload = {
        name: handicapDefinitionForm.name.trim(),
        description: handicapDefinitionForm.description.trim(),
        category: handicapDefinitionForm.category,
        selection_weight: Number(handicapDefinitionForm.selection_weight),
        grace_games: Number(handicapDefinitionForm.grace_games),
        penalty_points: Number(handicapDefinitionForm.penalty_points),
        reversal_base_percent: Number(handicapDefinitionForm.reversal_base_percent),
        reversal_rank_step_percent: Number(handicapDefinitionForm.reversal_rank_step_percent),
        reversal_min_percent: Number(handicapDefinitionForm.reversal_min_percent),
        reversal_max_percent: Number(handicapDefinitionForm.reversal_max_percent),
        active: handicapDefinitionForm.active,
      }

      if (editingHandicapDefinitionId) {
        await api.patch(`/handicaps/definitions/${editingHandicapDefinitionId}/`, payload)
        showSuccess('Handicap actualizado.')
      } else {
        await api.post('/handicaps/definitions/create/', payload)
        showSuccess('Handicap creado.')
      }

      const response = await api.get('/handicaps/definitions/')
      setHandicapDefinitions(asArray(response))
      resetHandicapDefinitionForm()
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  async function deleteHandicapDefinition(definition) {
    if (!window.confirm(`¿Eliminar “${definition.name}”? Solo se podrá borrar si todavía no forma parte del histórico.`)) return
    setSaving(true)
    try {
      await api.delete(`/handicaps/definitions/${definition.id}/`)
      setHandicapDefinitions(asArray(await api.get('/handicaps/definitions/')))
      showSuccess('Handicap eliminado del catálogo.')
    } catch (requestError) { showError(requestError) } finally { setSaving(false) }
  }

  async function editHandicapGrant(grant) {
    const awardReason = window.prompt('Motivo del premio:', grant.award_reason || '')
    if (awardReason === null || !awardReason.trim()) return
    setSaving(true)
    try {
      await api.patch(`/handicaps/grants/${grant.id}/`, { award_reason: awardReason.trim() })
      setHandicapGrants(asArray(await api.get('/handicaps/grants/')))
      showSuccess('Premio actualizado.')
    } catch (requestError) { showError(requestError) } finally { setSaving(false) }
  }

  async function deleteHandicapGrant(grant) {
    if (!window.confirm('¿Eliminar este premio concedido?')) return
    setSaving(true)
    try {
      await api.delete(`/handicaps/grants/${grant.id}/`)
      setHandicapGrants(asArray(await api.get('/handicaps/grants/')))
      showSuccess('Premio eliminado.')
    } catch (requestError) { showError(requestError) } finally { setSaving(false) }
  }

  async function editAssignedHandicap(handicap) {
    const awardReason = window.prompt('Motivo original:', handicap.award_reason || '')
    if (awardReason === null) return
    const grace = window.prompt('Partidas de gracia:', String(handicap.grace_games_snapshot ?? 0))
    if (grace === null) return
    const penalty = window.prompt('Puntos de penalización por partida:', String(handicap.penalty_points_snapshot ?? 0))
    if (penalty === null) return
    setSaving(true)
    try {
      await api.patch(`/handicaps/${handicap.id}/`, {
        award_reason: awardReason.trim(),
        grace_games_snapshot: Number(grace),
        penalty_points_snapshot: Number(penalty),
      })
      setAssignedHandicaps(asArray(await api.get('/handicaps/')))
      showSuccess('No te flipes actualizado.')
    } catch (requestError) { showError(requestError) } finally { setSaving(false) }
  }

  async function deleteAssignedHandicap(handicap) {
    if (!window.confirm('¿Eliminar este No te flipes lanzado? Si aún no se ha canjeado, el poder volverá a quedar disponible.')) return
    setSaving(true)
    try {
      await api.delete(`/handicaps/${handicap.id}/`)
      const [handicapsResponse, grantsResponse] = await Promise.all([api.get('/handicaps/'), api.get('/handicaps/grants/')])
      setAssignedHandicaps(asArray(handicapsResponse))
      setHandicapGrants(asArray(grantsResponse))
      showSuccess('No te flipes eliminado.')
    } catch (requestError) { showError(requestError) } finally { setSaving(false) }
  }

  async function saveHandicapCategory(category) {
    setSaving(true)
    setError('')

    try {
      await api.patch(`/handicaps/categories/${category.id}/`, {
        selection_weight: Number(category.selection_weight),
        active: category.active,
      })
      const response = await api.get('/handicaps/categories/')
      setHandicapCategories(asArray(response))
      showSuccess(`Categoría ${category.category_display || category.category} actualizada.`)
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  async function assignHandicap(event) {
    event.preventDefault()
    setSaving(true)
    setError('')

    try {
      const payload = {
        player: Number(handicapForm.player),
        season: Number(handicapForm.season),
        award_reason: handicapForm.award_reason.trim(),
      }
      await api.post('/handicaps/create/', payload)
      const response = await api.get('/handicaps/')
      setAssignedHandicaps(asArray(response))
      setHandicapForm((current) => ({
        ...current,
        player: '',
        award_reason: '',
      }))
      showSuccess('No te flipes asignado correctamente.')
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  function handleUserFieldChange(event) {
    const { name, value, type, checked } = event.target
    setUserForm((current) => {
      const next = {
        ...current,
        [name]: type === 'checkbox' ? checked : value,
      }
      if (name === 'membership_plan' && value !== 'SUPPORTER') {
        next.subscription_paid_until = ''
      }
      return next
    })
  }

  function resetUserForm() {
    setEditingUserId(null)
    setUserForm(EMPTY_ADMIN_USER_FORM)
  }

  function editUser(player) {
    setEditingUserId(player.id)
    setUserForm({
      username: player.username || '',
      first_name: player.first_name || '',
      last_name: player.last_name || '',
      display_name: player.display_name || '',
      email: player.email || '',
      password: '',
      password_confirm: '',
      is_active: Boolean(player.is_active),
      is_staff: Boolean(player.is_staff),
      membership_plan: player.membership_plan || 'FREE',
      subscription_paid_until: player.subscription_paid_until || '',
    })
    setSuccess('')
    setError('')
  }

  async function refreshUserLists() {
    const [adminPlayersResponse, playersResponse] = await Promise.all([
      api.get('/accounts/admin/players/'),
      api.get('/accounts/players/'),
    ])
    setAdminPlayers(asArray(adminPlayersResponse))
    setPlayers(asArray(playersResponse))
  }

  async function saveUser(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')

    try {
      if (editingUserId) {
        await api.patch(`/accounts/admin/players/${editingUserId}/`, {
          username: userForm.username,
          first_name: userForm.first_name,
          last_name: userForm.last_name,
          display_name: userForm.display_name,
          email: userForm.email,
          is_active: userForm.is_active,
          is_staff: userForm.is_staff,
          membership_plan: userForm.membership_plan,
          subscription_paid_until: userForm.subscription_paid_until || null,
        })

        if (userForm.password || userForm.password_confirm) {
          await api.post(
            `/accounts/admin/players/${editingUserId}/reset-password/`,
            {
              new_password: userForm.password,
              new_password_confirm: userForm.password_confirm,
            },
          )
        }

        showSuccess('Usuario actualizado correctamente.')
      } else {
        await api.post('/accounts/admin/players/', {
          ...userForm,
          subscription_paid_until: userForm.membership_plan === 'SUPPORTER'
            ? (userForm.subscription_paid_until || null)
            : null,
        })
        showSuccess('Usuario creado correctamente.')
      }

      await refreshUserLists()
      resetUserForm()
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  async function toggleUserAdmin(player) {
    if (!currentUser?.is_superuser || Number(player.id) === Number(currentUser?.id) || player.is_superuser) return
    const makeAdmin = !player.is_staff
    const confirmed = window.confirm(
      `¿${makeAdmin ? 'Conceder' : 'Retirar'} permisos de administrador a ${player.display_name || player.username}?`,
    )
    if (!confirmed) return
    setSaving(true)
    setError('')
    try {
      await api.patch(`/accounts/admin/players/${player.id}/`, { is_staff: makeAdmin })
      await refreshUserLists()
      showSuccess(makeAdmin ? 'Permisos de administrador concedidos.' : 'Permisos de administrador retirados.')
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  async function toggleUserActive(player) {
    const action = player.is_active ? 'desactivar' : 'activar'
    const confirmed = window.confirm(
      `¿Seguro que quieres ${action} a ${player.display_name || player.username}?`,
    )
    if (!confirmed) return

    setSaving(true)
    try {
      await api.patch(`/accounts/admin/players/${player.id}/`, {
        is_active: !player.is_active,
      })
      await refreshUserLists()
      showSuccess(`Usuario ${player.is_active ? 'desactivado' : 'activado'} correctamente.`)
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  function editSeason(season) {
    setEditingSeasonId(season.id)
    setSeasonForm({
      name: season.name || '',
      start_date: season.start_date || '',
      end_date: season.end_date || '',
      active: Boolean(season.active),
    })
  }

  function cancelSeasonEdit() {
    setEditingSeasonId(null)
    setSeasonForm({ name: '', start_date: '', end_date: '', active: true })
  }

  async function saveSeason(event) {
    event.preventDefault()
    setSaving(true)
    try {
      const payload = {
        name: seasonForm.name,
        start_date: seasonForm.start_date,
        end_date: seasonForm.end_date || null,
        active: seasonForm.active,
      }
      if (editingSeasonId) {
        await api.patch(`/league/seasons/${editingSeasonId}/`, payload)
        showSuccess('Temporada actualizada correctamente.')
      } else {
        await api.post('/league/seasons/create/', payload)
        showSuccess('Temporada creada correctamente.')
      }
      cancelSeasonEdit()
      setSeasons(asArray(await api.get('/league/seasons/')))
      setWeeks(asArray(await api.get('/league/weeks/')))
    } catch (requestError) {
      showError(requestError)
    } finally { setSaving(false) }
  }

  async function deleteSeason(season) {
    if (!window.confirm(`¿Eliminar la temporada “${season.name}”? Solo se permite si todavía no contiene partidas.`)) return
    setSaving(true)
    try {
      await api.delete(`/league/seasons/${season.id}/`)
      setSeasons(asArray(await api.get('/league/seasons/')))
      setWeeks(asArray(await api.get('/league/weeks/')))
      if (editingSeasonId === season.id) cancelSeasonEdit()
      showSuccess('Temporada eliminada.')
    } catch (requestError) { showError(requestError) } finally { setSaving(false) }
  }

  async function finalizeSeason(season) {
    if (!window.confirm(`¿Finalizar “${season.name}”? La clasificación, penalizaciones, bonificaciones y No te flipes de esta temporada quedarán como histórico y la siguiente temporada empezará limpia.`)) return
    setSaving(true)
    try {
      await api.post(`/league/seasons/${season.id}/finalize/`)
      setSeasons(asArray(await api.get('/league/seasons/')))
      showSuccess('Temporada finalizada y protegida como histórico.')
    } catch (requestError) { showError(requestError) } finally { setSaving(false) }
  }

  async function saveLeagueSettings(event) {
    event.preventDefault()
    setSaving(true)
    try {
      const response = await api.patch('/league/settings/', {
        mode: settingsForm.mode,
        subscription_fee: Number(settingsForm.subscription_fee),
        prize_pool_percent: Number(settingsForm.prize_pool_percent),
        paypal_url: settingsForm.paypal_url,
        free_league_notice: settingsForm.free_league_notice,
      })
      setLeagueSettings(response)
      const poolResponse = await api.get('/league/prize-pool/').catch(() => null)
      setPrizePool(poolResponse?.enabled === false ? null : poolResponse)
      showSuccess('Configuración de la liga actualizada.')
    } catch (requestError) { showError(requestError) } finally { setSaving(false) }
  }


  function resetEventForm() {
    setEditingEventId(null)
    setEventForm({ name: '', description: '', rules: '', extra_points: 0, active: true })
  }

  function editEvent(item) {
    setEditingEventId(item.id)
    setEventForm({
      name: item.name || '',
      description: item.description || '',
      rules: item.rules || '',
      extra_points: item.extra_points ?? 0,
      active: item.active !== false,
    })
  }

  async function saveEvent(event) {
    event.preventDefault()
    setSaving(true)

    try {
      const payload = {
        name: eventForm.name,
        description: eventForm.description,
        rules: eventForm.rules,
        extra_points: Number(eventForm.extra_points),
        active: eventForm.active,
      }
      if (editingEventId) {
        await api.patch(`/events/${editingEventId}/`, payload)
        showSuccess('Evento semanal actualizado.')
      } else {
        await api.post('/events/create/', payload)
        showSuccess('Evento semanal creado correctamente.')
      }
      resetEventForm()
      setEvents(asArray(await api.get('/events/')))
      setWeeks(asArray(await api.get('/league/weeks/')))
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  async function deleteEvent(item) {
    if (!window.confirm(`¿Eliminar el evento “${item.name}”? Si está en una jornada abierta se quitará de esa jornada; si ya forma parte de una jornada cerrada no se permitirá.`)) return
    setSaving(true)
    try {
      await api.delete(`/events/${item.id}/`)
      if (Number(editingEventId) === Number(item.id)) resetEventForm()
      setEvents(asArray(await api.get('/events/')))
      setWeeks(asArray(await api.get('/league/weeks/')))
      showSuccess('Evento semanal eliminado.')
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  async function createWeek(event) {
    event.preventDefault()
    setSaving(true)

    try {
      const payload = {
        season: Number(weekForm.season),
        date: weekForm.date,
      }
      if (weekForm.weekly_event) payload.weekly_event = Number(weekForm.weekly_event)
      await api.post('/league/weeks/create/', payload)

      setWeekForm({
        season: '',
        date: '',
        weekly_event: '',
      })

      const response = await api.get('/league/weeks/')
      setWeeks(asArray(response))

      showSuccess('Jornada creada correctamente.')
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  function updateWeekEventDraft(weekId, value) {
    setWeekEventDrafts((current) => ({
      ...current,
      [weekId]: value,
    }))
  }

  async function saveWeekEvent(week) {
    setSaving(true)

    try {
      const value =
        weekEventDrafts[week.id] !== undefined
          ? weekEventDrafts[week.id]
          : week.weekly_event || ''

      await api.patch(`/league/weeks/${week.id}/`, {
        weekly_event: value ? Number(value) : null,
      })

      const response = await api.get('/league/weeks/')
      setWeeks(asArray(response))

      showSuccess(
        `Evento de la jornada ${week.number} actualizado.`,
      )
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  async function closeWeek(week) {
    const confirmed = window.confirm(
      `¿Cerrar la jornada ${week.number}? Esta acción requiere que todas sus partidas estén completas y cerradas.`,
    )

    if (!confirmed) return

    setSaving(true)

    try {
      await api.post(`/league/weeks/${week.id}/close/`)

      const response = await api.get('/league/weeks/')
      setWeeks(asArray(response))

      showSuccess(`Jornada ${week.number} cerrada.`)
    } catch (requestError) {
      showError(requestError)
    } finally {
      setSaving(false)
    }
  }

  function selectSection(section) {
    setActiveSection(section)
    setSelectedMatch(null)
  }

  if (loading) {
    return (
      <section className="admin-page">
        <div className="admin-loading">
          <div className="admin-spinner" />
          <span>Cargando administración…</span>
        </div>
      </section>
    )
  }

  return (
    <section className="admin-page">
      <div className="admin-shell">
        <aside className="admin-sidebar">
          <div className="admin-brand">
            <span className="admin-brand-mark">LT</span>
            <div>
              <strong>Liga Timidina</strong>
              <small>Administración</small>
            </div>
          </div>

          <nav className="admin-nav">
            <button
              className={
                activeSection === 'dashboard'
                  ? 'admin-nav-item active'
                  : 'admin-nav-item'
              }
              onClick={() => selectSection('dashboard')}
            >
              <AdminNavIcon type="dashboard" />
              Dashboard
            </button>

            <button
              className={
                activeSection === 'users'
                  ? 'admin-nav-item active'
                  : 'admin-nav-item'
              }
              onClick={() => selectSection('users')}
            >
              <AdminNavIcon type="users" />
              Usuarios
            </button>

            <button
              className={
                activeSection === 'seasons'
                  ? 'admin-nav-item active'
                  : 'admin-nav-item'
              }
              onClick={() => selectSection('seasons')}
            >
              <AdminNavIcon type="seasons" />
              Temporadas
            </button>

            <button
              className={
                activeSection === 'weeks'
                  ? 'admin-nav-item active'
                  : 'admin-nav-item'
              }
              onClick={() => selectSection('weeks')}
            >
              <AdminNavIcon type="weeks" />
              Jornadas
            </button>

            <button
              className={
                activeSection === 'events'
                  ? 'admin-nav-item active'
                  : 'admin-nav-item'
              }
              onClick={() => selectSection('events')}
            >
              <AdminNavIcon type="events" />
              Eventos
            </button>

            <button
              className={
                activeSection === 'scoring'
                  ? 'admin-nav-item active'
                  : 'admin-nav-item'
              }
              onClick={() => selectSection('scoring')}
            >
              <AdminNavIcon type="scoring" />
              Puntuación
            </button>

            <button
              className={
                activeSection === 'handicaps'
                  ? 'admin-nav-item active'
                  : 'admin-nav-item'
              }
              onClick={() => selectSection('handicaps')}
            >
              <AdminNavIcon type="handicaps" />
              No te flipes
            </button>

            <button
              className={activeSection === 'settings' ? 'admin-nav-item active' : 'admin-nav-item'}
              onClick={() => selectSection('settings')}
            >
              <AdminNavIcon type="settings" />
              Liga y premios
            </button>

            <button
              className={
                activeSection === 'matches'
                  ? 'admin-nav-item active'
                  : 'admin-nav-item'
              }
              onClick={() => selectSection('matches')}
            >
              <AdminNavIcon type="matches" />
              Partidas
            </button>
          </nav>
        </aside>

        <main className="admin-main">
          <header className="admin-topbar">
            <div>
              <span className="admin-eyebrow">
                Panel de administración
              </span>
              <h1>
                {activeSection === 'dashboard' && 'Dashboard'}
                {activeSection === 'users' && 'Usuarios'}
                {activeSection === 'seasons' && 'Temporadas'}
                {activeSection === 'weeks' && 'Jornadas'}
                {activeSection === 'events' && 'Eventos semanales'}
                {activeSection === 'scoring' && 'Puntuación'}
                {activeSection === 'handicaps' && 'No te flipes'}
                {activeSection === 'settings' && 'Liga y premios'}
                {activeSection === 'matches' && 'Partidas'}
              </h1>
            </div>

          </header>

          {error && (
            <div className="admin-alert error">
              <strong>Error</strong>
              <span>{error}</span>
              <button onClick={() => setError('')}>×</button>
            </div>
          )}

          {success && (
            <div className="admin-alert success">
              <strong>Listo</strong>
              <span>{success}</span>
              <button onClick={() => setSuccess('')}>×</button>
            </div>
          )}

          {activeSection === 'dashboard' && (
            <DashboardSection
              activeSeason={activeSeason}
              currentWeek={currentWeek}
              weeks={weeks}
              matches={matches}
              onOpenMatch={openMatch}
              onGoToMatches={() => selectSection('matches')}
            />
          )}

          {activeSection === 'settings' && (
            <LeagueSettingsSection
              pool={prizePool}
              form={settingsForm}
              setForm={setSettingsForm}
              onSubmit={saveLeagueSettings}
              saving={saving}
            />
          )}

          {activeSection === 'users' && (
            <UsersSection
              users={adminPlayers}
              form={userForm}
              editingUserId={editingUserId}
              currentUserId={currentUser?.id}
              currentUserIsSuperuser={Boolean(currentUser?.is_superuser)}
              saving={saving}
              onFieldChange={handleUserFieldChange}
              onSubmit={saveUser}
              onEdit={editUser}
              onCancel={resetUserForm}
              onToggleActive={toggleUserActive}
              onToggleAdmin={toggleUserAdmin}
              leagueSettings={leagueSettings}
            />
          )}

          {activeSection === 'seasons' && (
            <SeasonsSection
              seasons={seasons}
              form={seasonForm}
              setForm={setSeasonForm}
              onSubmit={saveSeason}
              saving={saving}
              editingSeasonId={editingSeasonId}
              onEdit={editSeason}
              onCancel={cancelSeasonEdit}
              onDelete={deleteSeason}
              onFinalize={finalizeSeason}
            />
          )}

          {activeSection === 'weeks' && (
            <WeeksSection
              weeks={weeks}
              seasons={seasons}
              events={events}
              form={weekForm}
              setForm={setWeekForm}
              onSubmit={createWeek}
              saving={saving}
              eventDrafts={weekEventDrafts}
              onEventDraftChange={updateWeekEventDraft}
              onSaveEvent={saveWeekEvent}
              onCloseWeek={closeWeek}
            />
          )}

          {activeSection === 'events' && (
            <EventsSection
              events={events}
              form={eventForm}
              setForm={setEventForm}
              onSubmit={saveEvent}
              saving={saving}
              editingEventId={editingEventId}
              onEdit={editEvent}
              onDelete={deleteEvent}
              onCancel={resetEventForm}
            />
          )}

          {activeSection === 'scoring' && (
            <ScoringSection
              seasons={seasons}
              weeks={weeks}
              rules={scoringRules}
              form={scoringRuleForm}
              editingRuleId={editingScoringRuleId}
              saving={saving}
              onFieldChange={handleScoringRuleFieldChange}
              onSubmit={saveScoringRule}
              onEdit={startEditingScoringRule}
              onToggle={toggleScoringRule}
              onDelete={deleteScoringRule}
              onCancel={resetScoringRuleForm}
            />
          )}

          {activeSection === 'handicaps' && (
            <HandicapsSection
              categories={handicapCategories}
              definitions={handicapDefinitions}
              assignedHandicaps={assignedHandicaps}
              handicapGrants={handicapGrants}
              players={activePlayers}
              seasons={seasons}
              form={handicapForm}
              definitionForm={handicapDefinitionForm}
              editingDefinitionId={editingHandicapDefinitionId}
              saving={saving}
              onFormChange={handleHandicapFormChange}
              onDefinitionFieldChange={handleHandicapDefinitionFieldChange}
              onAssign={assignHandicap}
              onSaveDefinition={saveHandicapDefinition}
              onEditDefinition={editHandicapDefinition}
              onDeleteDefinition={deleteHandicapDefinition}
              onCancelDefinition={resetHandicapDefinitionForm}
              onSaveCategory={saveHandicapCategory}
              onEditGrant={editHandicapGrant}
              onDeleteGrant={deleteHandicapGrant}
              onEditAssigned={editAssignedHandicap}
              onDeleteAssigned={deleteAssignedHandicap}
            />
          )}

          {activeSection === 'matches' && (
            <MatchesSection
              matches={matches}
              weeks={weeks}
              players={activePlayers}
              selectedMatch={selectedMatch}
              matchForm={matchForm}
              playerForm={playerForm}
              eliminationForm={eliminationForm}
              selectedPlayerDecks={selectedPlayerDecks}
              matchPlayerOptions={matchPlayerOptions}
              matchPlayerIds={matchPlayerIds}
              saving={saving}
              onMatchFieldChange={handleMatchFieldChange}
              onPlayerFieldChange={handlePlayerFieldChange}
              onEliminationFieldChange={
                handleEliminationFieldChange
              }
              onCreateMatch={createMatch}
              onOpenMatch={openMatch}
              onAddPlayer={addPlayerToMatch}
              onUpdatePlayer={updateMatchPlayer}
              onAddElimination={addElimination}
              onCloseMatch={closeMatch}
              onDeleteMatch={deleteClosedMatch}
              onRefreshMatches={refreshMatches}
            />
          )}
        </main>
      </div>
    </section>
  )
}

function LeagueSettingsSection({ pool, form, setForm, onSubmit, saving }) {
  const premiumMode = form.mode === 'PREMIUM'
  return (
    <div className="admin-content">
      <div className="admin-two-column">
        <section className="admin-card">
          <SectionHeader eyebrow="Modalidad" title="Funcionamiento de la liga" description="Cambia entre liga gratuita y liga con suscripción sin alterar el histórico de temporadas." />
          <form className="admin-form" onSubmit={onSubmit}>
            <label>
              Modalidad actual
              <select value={form.mode} onChange={(event) => setForm({ ...form, mode: event.target.value })}>
                <option value="FREE">Liga gratuita · hasta 3 partidas por jornada</option>
                <option value="PREMIUM">Liga con suscripción · estándar 1 / premium 3</option>
              </select>
            </label>
            <div className="admin-form-grid">
              <label>
                Cuota premium mensual (€)
                <input type="number" min="0" step="0.01" value={form.subscription_fee} onChange={(event) => setForm({ ...form, subscription_fee: event.target.value })} disabled={!premiumMode} />
              </label>
              <label>
                Porcentaje para el bote (%)
                <input type="number" min="0" max="100" step="0.01" value={form.prize_pool_percent} onChange={(event) => setForm({ ...form, prize_pool_percent: event.target.value })} disabled={!premiumMode} />
                <small>Por defecto 20%. Puedes adaptarlo cada mes para cubrir servidor, dominio y otros costes fijos.</small>
              </label>
            </div>
            <label>
              Enlace de pago
              <input type="url" value={form.paypal_url} onChange={(event) => setForm({ ...form, paypal_url: event.target.value })} disabled={!premiumMode} />
            </label>
            <label>
              Aviso de convivencia para liga gratuita
              <textarea rows="5" value={form.free_league_notice} onChange={(event) => setForm({ ...form, free_league_notice: event.target.value })} />
            </label>
            <button className="admin-button primary" type="submit" disabled={saving}>{saving ? 'Guardando…' : 'Guardar configuración'}</button>
          </form>
        </section>
        <section className="admin-card">
          <SectionHeader eyebrow="Bote" title="Premios del mes" description={premiumMode ? 'El bote acumula la reserva del mes sobre el saldo heredado del mes anterior.' : 'El bote queda oculto mientras la liga sea gratuita.'} />
          {!premiumMode || !pool ? <div className="admin-empty">Liga gratuita: no se muestran cuotas ni bote de premios.</div> : (
            <div className="admin-prize-summary">
              <StatCard label="Premium este mes" value={pool.premium_participants || 0} detail={`${pool.subscription_fee || form.subscription_fee} € / mes`} />
              <StatCard label="Aportación del mes" value={`${Number(pool.monthly_contribution || 0).toFixed(2)} €`} detail={`${pool.prize_pool_percent || form.prize_pool_percent}% reservado`} />
              <StatCard label="Bote acumulado" value={`${Number(pool.total || 0).toFixed(2)} €`} detail={`Heredado: ${Number(pool.carry_in || 0).toFixed(2)} €`} />
              <div className="admin-info-strip">Reparto mostrado al público: 1.º 50%, 2.º 30% y 3.º 20%. Los premios se entregan en material de Magic proporcionado por la tienda.</div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function UsersSection({
  users,
  form,
  editingUserId,
  currentUserId,
  currentUserIsSuperuser,
  saving,
  onFieldChange,
  onSubmit,
  onEdit,
  onCancel,
  onToggleActive,
  onToggleAdmin,
  leagueSettings,
}) {
  const [query, setQuery] = useState('')

  const filteredUsers = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase('es')
    if (!normalized) return users

    return users.filter((player) =>
      [player.username, player.display_name, player.email]
        .filter(Boolean)
        .some((value) => value.toLocaleLowerCase('es').includes(normalized)),
    )
  }, [query, users])

  const activeCount = users.filter((player) => player.is_active).length
  const adminCount = users.filter((player) => player.is_staff).length
  const editingSelf = Number(editingUserId) === Number(currentUserId)
  const editingTarget = users.find((player) => Number(player.id) === Number(editingUserId))
  const protectedAdmin = Boolean(editingTarget?.is_staff && !currentUserIsSuperuser && !editingSelf)

  return (
    <div className="admin-content">
      <div className="admin-stats-grid">
        <StatCard label="Usuarios" value={users.length} detail="Cuentas registradas" />
        <StatCard label="Activos" value={activeCount} detail="Pueden iniciar sesión" />
        <StatCard label="Inactivos" value={users.length - activeCount} detail="Acceso bloqueado" />
        <StatCard label="Administradores" value={adminCount} detail="Con acceso al panel" />
      </div>

      {currentUserIsSuperuser && <div className="admin-info-strip"><strong>Modo superadministrador.</strong> Puedes conceder o retirar el rol de administrador desde la tabla de usuarios o al editar una cuenta.</div>}

      <div className="admin-two-column admin-users-layout">
        <section className="admin-card">
          <SectionHeader
            eyebrow={editingUserId ? 'Edición' : 'Alta'}
            title={editingUserId ? 'Editar usuario' : 'Crear usuario'}
            description={
              editingUserId
                ? 'Actualiza sus datos, permisos o establece una contraseña nueva.'
                : 'Da de alta un jugador sin iniciar sesión con su cuenta.'
            }
          />

          <form className="admin-form" onSubmit={onSubmit}>
            <label>
              Usuario
              <input
                name="username"
                value={form.username}
                onChange={onFieldChange}
                autoComplete="off"
                required
              />
            </label>

            <div className="admin-form-grid">
              <label>
                Nombre
                <input name="first_name" value={form.first_name || ''} onChange={onFieldChange} autoComplete="off" />
              </label>
              <label>
                Apellidos
                <input name="last_name" value={form.last_name || ''} onChange={onFieldChange} autoComplete="off" />
              </label>
            </div>

            <label>
              Nombre visible
              <input
                name="display_name"
                value={form.display_name}
                onChange={onFieldChange}
                required
              />
            </label>

            <label>
              Email
              <input
                name="email"
                type="email"
                value={form.email}
                onChange={onFieldChange}
                autoComplete="off"
                required
              />
            </label>

            <div className="admin-form-grid">
              <label>
                {editingUserId ? 'Nueva contraseña' : 'Contraseña'}
                <input
                  name="password"
                  type="password"
                  value={form.password}
                  onChange={onFieldChange}
                  minLength={8}
                  autoComplete="new-password"
                  required={!editingUserId}
                  placeholder={editingUserId ? 'Dejar vacía para conservar' : ''}
                />
              </label>

              <label>
                Repetir contraseña
                <input
                  name="password_confirm"
                  type="password"
                  value={form.password_confirm}
                  onChange={onFieldChange}
                  minLength={8}
                  autoComplete="new-password"
                  required={!editingUserId || Boolean(form.password)}
                />
              </label>
            </div>

            <div className="admin-user-flags">
              <label className="admin-checkbox-row">
                <input
                  name="is_active"
                  type="checkbox"
                  checked={form.is_active}
                  onChange={onFieldChange}
                  disabled={editingSelf || protectedAdmin}
                />
                <span>
                  <strong>Usuario activo</strong>
                  <small>Permite iniciar sesión y aparecer en la liga.</small>
                </span>
              </label>

              <label className="admin-checkbox-row">
                <input
                  name="is_staff"
                  type="checkbox"
                  checked={form.is_staff}
                  onChange={onFieldChange}
                  disabled={!currentUserIsSuperuser || editingSelf || protectedAdmin}
                />
                <span>
                  <strong>Administrador</strong>
                  <small>{currentUserIsSuperuser ? 'Como superadministrador puedes conceder o retirar este rol.' : 'Solo un superadministrador puede cambiar este rol.'}</small>
                </span>
              </label>

              <label>
                Modalidad
                <select name="membership_plan" value={form.membership_plan || 'FREE'} onChange={onFieldChange} disabled={leagueSettings?.mode === 'FREE'}>
                  <option value="FREE">Estándar · 1 partida/jornada</option>
                  <option value="SUPPORTER">Premium · hasta 3 partidas/jornada</option>
                </select>
              </label>

              {leagueSettings?.mode !== 'FREE' && form.membership_plan === 'SUPPORTER' && (
                <label>
                  Suscripción abonada hasta (opcional)
                  <input name="subscription_paid_until" type="date" value={form.subscription_paid_until || ''} onChange={onFieldChange} />
                  <small>Si se deja vacía, la aportación se considera vigente hasta que administración la cambie. Si la fecha vence, el usuario vuelve automáticamente a las condiciones gratuitas/estándar; la cuenta sigue activa.</small>
                </label>
              )}
            </div>

            {editingSelf && (
              <div className="admin-info-strip">No puedes desactivar ni quitar los permisos de tu propia cuenta desde aquí.</div>
            )}
            {protectedAdmin && (
              <div className="admin-info-strip">Solo un superadministrador puede bloquear o degradar a otro administrador.</div>
            )}

            <div className="admin-form-actions">
              <button className="admin-button primary" type="submit" disabled={saving}>
                {saving ? 'Guardando…' : editingUserId ? 'Guardar cambios' : 'Crear usuario'}
              </button>
              {editingUserId && (
                <button className="admin-button secondary" type="button" onClick={onCancel} disabled={saving}>
                  Cancelar
                </button>
              )}
            </div>
          </form>
        </section>

        <section className="admin-card admin-card-wide">
          <SectionHeader
            eyebrow="Cuentas"
            title="Administrar usuarios"
            description="Busca, edita permisos y activa o desactiva cuentas sin borrar su historial."
          />

          <div className="admin-user-search">
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar por usuario, nombre o email…"
            />
            <span>{filteredUsers.length} resultados</span>
          </div>

          {filteredUsers.length === 0 ? (
            <div className="admin-empty">No hay usuarios que coincidan con la búsqueda.</div>
          ) : (
            <div className="admin-table-wrap">
              <table className="admin-table admin-users-table">
                <thead>
                  <tr>
                    <th>Jugador</th>
                    <th>Email</th>
                    <th>Rol</th>
                    <th>Estado</th>
                    <th>Alta</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((player) => {
                    const isSelf = Number(player.id) === Number(currentUserId)
                    return (
                      <tr key={player.id}>
                        <td>
                          <strong>{player.display_name || player.username}</strong>
                          <small>@{player.username}{isSelf ? ' · tú' : ''}</small>
                        </td>
                        <td>{player.email || '—'}<small>{leagueSettings?.mode === 'FREE' ? 'Participación activa' : player.subscription_active ? `Aportación vigente${player.subscription_paid_until ? ` hasta ${player.subscription_paid_until}` : ''}` : 'Condiciones gratuitas/estándar'}</small></td>
                        <td>
                          {player.is_superuser ? (
                            <StatusBadge tone="warning">Superadmin</StatusBadge>
                          ) : player.is_staff ? (
                            <StatusBadge tone="warning">Admin</StatusBadge>
                          ) : (
                            <StatusBadge>Jugador</StatusBadge>
                          )}
                        </td>
                        <td>
                          {player.is_active ? (
                            <StatusBadge tone="success">Activo</StatusBadge>
                          ) : (
                            <StatusBadge>Inactivo</StatusBadge>
                          )}
                        </td>
                        <td>{formatDateTime(player.created_at)}</td>
                        <td>
                          <div className="admin-table-actions">
                            <button
                              className="admin-button small secondary"
                              type="button"
                              onClick={() => onEdit(player)}
                              disabled={saving}
                            >
                              Editar
                            </button>
                            {currentUserIsSuperuser && !isSelf && !player.is_superuser && (
                              <button
                                className="admin-button small secondary"
                                type="button"
                                onClick={() => onToggleAdmin(player)}
                                disabled={saving}
                              >
                                {player.is_staff ? 'Quitar admin' : 'Hacer admin'}
                              </button>
                            )}
                            <button
                              className="admin-button small secondary"
                              type="button"
                              onClick={() => onToggleActive(player)}
                              disabled={saving || isSelf || (player.is_staff && !currentUserIsSuperuser)}
                            >
                              {player.is_active ? 'Desactivar' : 'Activar'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function DashboardSection({
  activeSeason,
  currentWeek,
  weeks,
  matches,
  onOpenMatch,
  onGoToMatches,
}) {
  const openWeeks = weeks.filter((week) => !week.closed)
  const openMatches = matches.filter((match) => !match.closed)

  return (
    <div className="admin-content">
      <div className="admin-stats-grid">
        <StatCard
          label="Temporada activa"
          value={activeSeason?.name || '—'}
          detail={
            activeSeason
              ? `Desde ${formatDate(activeSeason.start_date)}`
              : 'No hay temporada activa'
          }
        />

        <StatCard
          label="Jornada abierta"
          value={
            currentWeek ? `Semana ${currentWeek.number}` : '—'
          }
          detail={
            currentWeek
              ? formatDate(currentWeek.date)
              : 'No hay ninguna jornada abierta'
          }
        />

        <StatCard
          label="Partidas abiertas"
          value={openMatches.length}
          detail={`${matches.length} partidas registradas`}
        />

        <StatCard
          label="Jornadas abiertas"
          value={openWeeks.length}
          detail={`${weeks.length} jornadas totales`}
        />
      </div>

      <div className="admin-dashboard-grid">
        <section className="admin-card admin-card-wide">
          <SectionHeader
            eyebrow="Ahora"
            title="Jornada actual"
            description="Jornada actualmente abierta para registrar partidas."
          />

          {currentWeek ? (
            <div className="admin-current-week">
              <div className="admin-current-week-number">
                <span>SEMANA</span>
                <strong>{currentWeek.number}</strong>
              </div>

              <div className="admin-current-week-info">
                <h3>{formatDate(currentWeek.date)}</h3>

                {currentWeek.weekly_event ? (
                  <>
                    <strong>
                      {currentWeek.weekly_event.name}
                    </strong>
                    <p>
                      {currentWeek.weekly_event.description ||
                        'Sin descripción.'}
                    </p>
                  </>
                ) : (
                  <p>Sin evento semanal asignado.</p>
                )}
              </div>
            </div>
          ) : (
            <div className="admin-empty">
              No hay ninguna jornada abierta actualmente.
            </div>
          )}
        </section>

        <section className="admin-card">
          <SectionHeader
            eyebrow="Acción rápida"
            title="Registrar partida"
            description="Crea una partida y empieza a introducir resultados."
          />

          <button
            className="admin-button primary full"
            onClick={onGoToMatches}
          >
            Nueva partida
          </button>
        </section>
      </div>

      <section className="admin-card">
        <SectionHeader
          eyebrow="Actividad"
          title="Partidas recientes"
          description="Las últimas partidas registradas."
        />

        {matches.length === 0 ? (
          <div className="admin-empty">
            Todavía no hay partidas registradas.
          </div>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Partida</th>
                  <th>Jornada</th>
                  <th>Fecha</th>
                  <th>Jugadores</th>
                  <th>Estado</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {matches.slice(0, 8).map((match) => (
                  <tr key={match.id}>
                    <td>#{match.id}</td>
                    <td>Semana {match.league_week_number}</td>
                    <td>{formatDateTime(match.played_at)}</td>
                    <td>{match.player_count ?? '—'}</td>
                    <td>
                      {match.closed ? (
                        <StatusBadge tone="success">
                          Cerrada
                        </StatusBadge>
                      ) : (
                        <StatusBadge tone="warning">
                          Abierta
                        </StatusBadge>
                      )}
                    </td>
                    <td>
                      <button
                        className="admin-button small secondary"
                        onClick={() => onOpenMatch(match.id)}
                      >
                        Ver
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {openMatches.length > 0 && (
        <div className="admin-info-strip">
          Hay {openMatches.length}{' '}
          {openMatches.length === 1
            ? 'partida abierta'
            : 'partidas abiertas'}{' '}
          que todavía requieren resultados o cierre.
        </div>
      )}
    </div>
  )
}

function SeasonsSection({
  seasons,
  form,
  setForm,
  onSubmit,
  saving,
  editingSeasonId,
  onEdit,
  onCancel,
  onDelete,
  onFinalize,
}) {
  return (
    <div className="admin-content">
      <div className="admin-two-column">
        <section className="admin-card">
          <SectionHeader
            eyebrow={editingSeasonId ? 'Corrección' : 'Nueva temporada'}
            title={editingSeasonId ? 'Editar temporada' : 'Crear temporada'}
            description="Las jornadas se numeran automáticamente a partir de las fechas de la temporada."
          />
          <form className="admin-form" onSubmit={onSubmit}>
            <label>Nombre<input type="text" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Liga Timidina 2026" required /></label>
            <div className="admin-form-grid">
              <label>Fecha de inicio<input type="date" value={form.start_date} onChange={(event) => setForm({ ...form, start_date: event.target.value })} required /></label>
              <label>Fecha de fin<input type="date" value={form.end_date} onChange={(event) => setForm({ ...form, end_date: event.target.value })} /></label>
            </div>
            <label className="admin-checkbox"><input type="checkbox" checked={form.active} onChange={(event) => setForm({ ...form, active: event.target.checked })} />Activar esta temporada</label>
            <div className="admin-actions">
              <button className="admin-button primary" type="submit" disabled={saving}>{saving ? 'Guardando…' : editingSeasonId ? 'Guardar cambios' : 'Crear temporada'}</button>
              {editingSeasonId && <button className="admin-button secondary" type="button" onClick={onCancel} disabled={saving}>Cancelar</button>}
            </div>
          </form>
        </section>

        <section className="admin-card">
          <SectionHeader eyebrow="Histórico" title="Temporadas" description="Puedes corregir o borrar una temporada mientras no tenga partidas. Al finalizarla queda protegida como histórico." />
          {seasons.length === 0 ? <div className="admin-empty">No hay temporadas.</div> : (
            <div className="admin-list">
              {seasons.map((season) => (
                <div className="admin-list-item admin-season-item" key={season.id}>
                  <div>
                    <strong>{season.name}</strong>
                    <span>{formatDate(season.start_date)}{season.end_date ? ` → ${formatDate(season.end_date)}` : ''}</span>
                    {season.finalized_at && <small>Finalizada {formatDateTime(season.finalized_at)}</small>}
                  </div>
                  <div className="admin-actions">
                    {season.finalized_at ? <StatusBadge>Histórico</StatusBadge> : season.active ? <StatusBadge tone="success">Activa</StatusBadge> : <StatusBadge>Inactiva</StatusBadge>}
                    {!season.finalized_at && <button className="admin-button small secondary" type="button" onClick={() => onEdit(season)} disabled={saving}>Editar</button>}
                    {!season.finalized_at && <button className="admin-button small secondary" type="button" onClick={() => onDelete(season)} disabled={saving}>Eliminar</button>}
                    {!season.finalized_at && <button className="admin-button small danger" type="button" onClick={() => onFinalize(season)} disabled={saving}>Finalizar</button>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
      <div className="admin-info-strip">Al finalizar una temporada, sus puntuaciones, penalizaciones, bonificaciones y No te flipes permanecen en el histórico. La siguiente temporada activa comienza con clasificación y efectos a cero.</div>
    </div>
  )
}


function WeeksSection({
  weeks,
  seasons,
  events,
  form,
  setForm,
  onSubmit,
  saving,
  eventDrafts,
  onEventDraftChange,
  onSaveEvent,
  onCloseWeek,
}) {
  const activeEvents = events.filter((event) => event.active)
  function recommendedEventId(seasonId) {
    if (!seasonId || activeEvents.length === 0) return ''
    const counts = new Map(activeEvents.map((event) => [Number(event.id), 0]))
    weeks.filter((week) => Number(week.season) === Number(seasonId)).forEach((week) => {
      const id = Number(week.weekly_event)
      if (counts.has(id)) counts.set(id, counts.get(id) + 1)
    })
    const minimum = Math.min(...counts.values())
    return String(activeEvents.find((event) => counts.get(Number(event.id)) === minimum)?.id || '')
  }

  return (
    <div className="admin-content">
      <section className="admin-card">
        <SectionHeader
          eyebrow="Nueva jornada"
          title="Crear jornada"
          description="El número se asigna automáticamente. Al elegir temporada se propone el evento menos utilizado para mantener un reparto equilibrado."
        />

        <form
          className="admin-form"
          onSubmit={onSubmit}
        >
          <div className="admin-form-grid">
            <label>
              Temporada
              <select
                value={form.season}
                onChange={(event) => {
                  const season = event.target.value
                  setForm({ ...form, season, weekly_event: recommendedEventId(season) })
                }}
                required
              >
                <option value="">
                  Selecciona una temporada
                </option>
                {seasons.map((season) => (
                  <option
                    key={season.id}
                    value={season.id}
                  >
                    {season.name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Fecha
              <input
                type="date"
                value={form.date}
                onChange={(event) =>
                  setForm({
                    ...form,
                    date: event.target.value,
                  })
                }
                required
              />
            </label>

            <label>
              Evento
              <select
                value={form.weekly_event}
                onChange={(event) =>
                  setForm({
                    ...form,
                    weekly_event: event.target.value,
                  })
                }
              >
                <option value="">Sin evento</option>
                {activeEvents.map((event) => (
                    <option
                      key={event.id}
                      value={event.id}
                    >
                      {event.name}
                    </option>
                  ))}
              </select>
              <small>Propuesta automática: eventos con menos apariciones en esta temporada.</small>
            </label>
          </div>

          <button
            className="admin-button primary"
            type="submit"
            disabled={saving}
          >
            {saving ? 'Creando…' : 'Crear jornada'}
          </button>
        </form>
      </section>

      <section className="admin-card">
        <SectionHeader
          eyebrow="Gestión"
          title="Jornadas"
          description="Asigna eventos y cierra jornadas desde aquí."
        />

        {weeks.length === 0 ? (
          <div className="admin-empty">
            No hay jornadas registradas.
          </div>
        ) : (
          <div className="admin-week-list">
            {weeks.map((week) => {
              const draft =
                eventDrafts[week.id] !== undefined
                  ? eventDrafts[week.id]
                  : week.weekly_event || ''

              return (
                <article
                  className="admin-week-card"
                  key={week.id}
                >
                  <div className="admin-week-card-main">
                    <div className="admin-week-number">
                      <span>SEMANA</span>
                      <strong>{week.number}</strong>
                    </div>

                    <div>
                      <h3>
                        {week.season_name ||
                          `Temporada #${week.season}`}
                      </h3>
                      <p>{formatDate(week.date)}</p>
                    </div>

                    {week.closed ? (
                      <StatusBadge tone="success">
                        Cerrada
                      </StatusBadge>
                    ) : (
                      <StatusBadge tone="warning">
                        Abierta
                      </StatusBadge>
                    )}
                  </div>

                  <div className="admin-week-controls">
                    <label>
                      Evento semanal
                      <select
                        value={draft}
                        disabled={week.closed || saving}
                        onChange={(event) =>
                          onEventDraftChange(
                            week.id,
                            event.target.value,
                          )
                        }
                      >
                        <option value="">
                          Sin evento
                        </option>
                        {events.map((event) => (
                          <option
                            key={event.id}
                            value={event.id}
                          >
                            {event.name}
                          </option>
                        ))}
                      </select>
                    </label>

                    <div className="admin-actions">
                      <button
                        className="admin-button secondary small"
                        disabled={week.closed || saving}
                        onClick={() =>
                          onSaveEvent(week)
                        }
                      >
                        Guardar evento
                      </button>

                      {!week.closed && (
                        <button
                          className="admin-button danger small"
                          disabled={saving}
                          onClick={() =>
                            onCloseWeek(week)
                          }
                        >
                          Cerrar jornada
                        </button>
                      )}
                    </div>
                  </div>
                </article>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}

function EventsSection({
  events,
  form,
  setForm,
  onSubmit,
  saving,
  editingEventId,
  onEdit,
  onDelete,
  onCancel,
}) {
  return (
    <div className="admin-content">
      <div className="admin-two-column">
        <section className="admin-card">
          <SectionHeader
            eyebrow={editingEventId ? 'Corrección' : 'Nuevo evento'}
            title={editingEventId ? 'Editar evento semanal' : 'Crear evento semanal'}
            description="Los eventos futuros pueden corregirse o eliminarse. Los que ya estén en una jornada cerrada quedan protegidos como histórico."
          />

          <form
            className="admin-form"
            onSubmit={onSubmit}
          >
            <label>
              Nombre
              <input
                type="text"
                value={form.name}
                onChange={(event) =>
                  setForm({
                    ...form,
                    name: event.target.value,
                  })
                }
                placeholder="Archenemy"
                required
              />
            </label>

            <label>
              Descripción
              <textarea
                rows="3"
                value={form.description}
                onChange={(event) =>
                  setForm({
                    ...form,
                    description: event.target.value,
                  })
                }
                placeholder="Describe el evento…"
              />
            </label>

            <label>
              Reglas
              <textarea
                rows="6"
                value={form.rules}
                onChange={(event) =>
                  setForm({
                    ...form,
                    rules: event.target.value,
                  })
                }
                placeholder="Reglas específicas del evento…"
              />
            </label>

            <label>
              Puntos extra
              <input
                type="number"
                min="0"
                value={form.extra_points}
                onChange={(event) =>
                  setForm({
                    ...form,
                    extra_points: event.target.value,
                  })
                }
              />
            </label>

            <label className="admin-checkbox">
              <input
                type="checkbox"
                checked={form.active}
                onChange={(event) =>
                  setForm({
                    ...form,
                    active: event.target.checked,
                  })
                }
              />
              Evento activo
            </label>

            <button
              className="admin-button primary"
              type="submit"
              disabled={saving}
            >
              {saving ? 'Guardando…' : editingEventId ? 'Guardar cambios' : 'Crear evento'}
            </button>
            {editingEventId && <button className="admin-button secondary" type="button" onClick={onCancel} disabled={saving}>Cancelar</button>}
          </form>
        </section>

        <section className="admin-card">
          <SectionHeader
            eyebrow="Biblioteca"
            title="Eventos disponibles"
            description="Eventos que pueden asignarse a las jornadas."
          />

          {events.length === 0 ? (
            <div className="admin-empty">
              No hay eventos.
            </div>
          ) : (
            <div className="admin-event-list">
              {events.map((event) => (
                <article
                  className="admin-event-card"
                  key={event.id}
                >
                  <div className="admin-event-card-header">
                    <div>
                      <h3>{event.name}</h3>
                      <span>
                        +{event.extra_points || 0} puntos
                      </span>
                    </div>

                    {event.active ? (
                      <StatusBadge tone="success">
                        Activo
                      </StatusBadge>
                    ) : (
                      <StatusBadge>
                        Inactivo
                      </StatusBadge>
                    )}
                  </div>

                  {event.description && (
                    <p>{event.description}</p>
                  )}

                  {event.rules && (
                    <details>
                      <summary>Ver reglas</summary>
                      <div className="admin-event-rules">
                        {event.rules}
                      </div>
                    </details>
                  )}
                  <div className="admin-actions">
                    <button className="admin-button small secondary" type="button" onClick={() => onEdit(event)} disabled={saving}>Editar</button>
                    <button className="admin-button small danger" type="button" onClick={() => onDelete(event)} disabled={saving}>Eliminar</button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function MatchPlayerResultEditor({
  result,
  saving,
  onSave,
}) {
  const [finalPosition, setFinalPosition] = useState(
    result.final_position ?? '',
  )

  useEffect(() => {
    setFinalPosition(result.final_position ?? '')
  }, [result.final_position])

  async function handleSubmit(event) {
    event.preventDefault()

    await onSave(result.id, {
      final_position: finalPosition
        ? Number(finalPosition)
        : null,
    })
  }

  return (
    <form
      className="admin-form admin-subform"
      onSubmit={handleSubmit}
    >
      <div className="admin-form-grid">
        <label>
          Posición final
          <input
            type="number"
            min="1"
            value={finalPosition}
            onChange={(event) =>
              setFinalPosition(event.target.value)
            }
            placeholder="1"
            required
            disabled={saving}
          />
        </label>

        <div className="admin-actions">
          <button
            className="admin-button small secondary"
            type="submit"
            disabled={saving}
          >
            Guardar posición
          </button>
        </div>
      </div>
    </form>
  )
}

function ScoringSection({
  seasons,
  weeks,
  rules,
  form,
  editingRuleId,
  saving,
  onFieldChange,
  onSubmit,
  onEdit,
  onToggle,
  onDelete,
  onCancel,
}) {
  const selectedSeason = seasons.find(
    (season) => String(season.id) === String(form.season),
  )

  const selectedSeasonHasClosedWeeks = weeks.some(
    (week) =>
      String(week.season) === String(form.season) &&
      week.closed,
  )

  const editable = !selectedSeasonHasClosedWeeks

  return (
    <div className="admin-content">
      <div className="admin-two-column">
        <section className="admin-card">
          <SectionHeader
            eyebrow={editingRuleId ? 'Editar regla' : 'Nueva regla'}
            title={
              editingRuleId
                ? 'Modificar puntuación'
                : 'Crear regla de puntuación'
            }
            description="Configura los puntos que se aplican al cerrar una partida."
          />

          <form className="admin-form" onSubmit={onSubmit}>
            <label>
              Temporada
              <select
                name="season"
                value={form.season}
                onChange={onFieldChange}
                disabled={Boolean(editingRuleId) || saving}
                required
              >
                <option value="">Selecciona una temporada</option>
                {seasons.map((season) => (
                  <option key={season.id} value={season.id}>
                    {season.name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Tipo de regla
              <select
                name="code"
                value={form.code}
                onChange={onFieldChange}
                disabled={Boolean(editingRuleId) || saving}
                required
              >
                <option value="">Selecciona una regla</option>
                {SCORING_RULE_OPTIONS.map((option) => (
                  <option key={option.code} value={option.code}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Nombre visible
              <input
                type="text"
                name="name"
                value={form.name}
                onChange={onFieldChange}
                placeholder="Victoria"
                required
              />
            </label>

            <label>
              Puntos
              <input
                type="number"
                name="points"
                value={form.points}
                onChange={onFieldChange}
                placeholder="5"
                min="-100"
                max="100"
                required
              />
            </label>

            <label>
              Descripción
              <textarea
                name="description"
                rows="4"
                value={form.description}
                onChange={onFieldChange}
                placeholder="Explica cuándo se aplica esta puntuación…"
              />
            </label>

            <label className="admin-checkbox">
              <input
                type="checkbox"
                name="active"
                checked={form.active}
                onChange={onFieldChange}
              />
              Regla activa
            </label>

            {selectedSeason && selectedSeasonHasClosedWeeks && (
              <div className="admin-info-strip">
                Esta temporada ya tiene jornadas cerradas. Sus reglas de
                puntuación están protegidas para conservar el histórico.
              </div>
            )}

            <div className="admin-actions">
              <button
                className="admin-button primary"
                type="submit"
                disabled={
                  saving ||
                  !form.season ||
                  !form.code ||
                  !form.name.trim() ||
                  form.points === '' ||
                  !editable
                }
              >
                {saving
                  ? 'Guardando…'
                  : editingRuleId
                    ? 'Guardar cambios'
                    : 'Crear regla'}
              </button>

              {editingRuleId && (
                <button
                  className="admin-button secondary"
                  type="button"
                  onClick={onCancel}
                  disabled={saving}
                >
                  Cancelar
                </button>
              )}
            </div>
          </form>
        </section>

        <section className="admin-card">
          <SectionHeader
            eyebrow="Configuración"
            title="Reglas de puntuación"
            description="Valores activos e históricos de la temporada seleccionada."
          />

          {rules.length === 0 ? (
            <div className="admin-empty">
              No hay reglas de puntuación registradas.
            </div>
          ) : (
            <div className="admin-list">
              {rules.map((rule) => (
                <article className="admin-list-item" key={rule.id}>
                  <div>
                    <strong>
                      {rule.name || rule.code_display || rule.code}
                    </strong>
                    <span>
                      {rule.code_display || rule.code} ·{' '}
                      {rule.points > 0 ? '+' : ''}
                      {rule.points} puntos
                    </span>
                    {rule.description && <small>{rule.description}</small>}
                  </div>

                  <div className="admin-actions">
                    {rule.active ? (
                      <StatusBadge tone="success">Activa</StatusBadge>
                    ) : (
                      <StatusBadge>Inactiva</StatusBadge>
                    )}

                    <button
                      className="admin-button small secondary"
                      onClick={() => onEdit(rule)}
                      disabled={
                        saving ||
                        weeks.some(
                          (week) =>
                            Number(week.season) === Number(rule.season) &&
                            week.closed,
                        )
                      }
                    >
                      Editar
                    </button>

                    <button
                      className="admin-button small secondary"
                      onClick={() => onToggle(rule)}
                      disabled={
                        saving ||
                        weeks.some(
                          (week) =>
                            Number(week.season) === Number(rule.season) &&
                            week.closed,
                        )
                      }
                    >
                      {rule.active ? 'Desactivar' : 'Activar'}
                    </button>

                    <button
                      className="admin-button small danger"
                      onClick={() => onDelete(rule)}
                      disabled={saving || weeks.some((week) => Number(week.season) === Number(rule.season) && week.closed)}
                    >
                      Eliminar
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="admin-card">
        <SectionHeader
          eyebrow="Referencia"
          title="Cómo se calculan los puntos"
          description="Los puntos se aplican automáticamente al cerrar cada partida."
        />

        <div className="admin-info-strip">
          Victoria, puestos 2.º/3.º, primera partida con un mazo, mazo
          original validado, evento semanal, primera eliminación,
          eliminaciones y penalización por concesión se resuelven mediante sus
          códigos de regla correspondientes.
        </div>
      </section>
    </div>
  )
}

function HandicapsSection({
  categories,
  definitions,
  assignedHandicaps,
  handicapGrants,
  players,
  seasons,
  form,
  definitionForm,
  editingDefinitionId,
  saving,
  onFormChange,
  onDefinitionFieldChange,
  onAssign,
  onSaveDefinition,
  onEditDefinition,
  onDeleteDefinition,
  onCancelDefinition,
  onSaveCategory,
  onEditGrant,
  onDeleteGrant,
  onEditAssigned,
  onDeleteAssigned,
}) {
  const activeSeasons = seasons.filter((season) => season.active)
  const [categoryDrafts, setCategoryDrafts] = useState({})

  useEffect(() => {
    setCategoryDrafts(
      Object.fromEntries(
        categories.map((category) => [category.id, category.selection_weight]),
      ),
    )
  }, [categories])

  return (
    <div className="admin-content">
      <div className="admin-two-column">
        <section className="admin-card">
          <SectionHeader
            eyebrow="Asignación"
            title="Premiar con un No te flipes"
            description="El administrador concede a este jugador el poder de lanzar un No te flipes a otro jugador. No aplica ninguna penalización todavía."
          />

          <form className="admin-form" onSubmit={onAssign}>
            <label>
              Jugador premiado
              <select name="player" value={form.player} onChange={onFormChange} required>
                <option value="">Selecciona jugador</option>
                {players.map((player) => (
                  <option key={player.id} value={player.id}>
                    {player.display_name || player.username}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Temporada
              <select name="season" value={form.season} onChange={onFormChange} required>
                <option value="">Selecciona temporada</option>
                {activeSeasons.map((season) => (
                  <option key={season.id} value={season.id}>{season.name}</option>
                ))}
              </select>
            </label>

            <div className="admin-info-strip">
              <strong>✦ Penalización aleatoria</strong>
              <span>
                El poder no contiene una penalización concreta. Cuando el jugador lo lance,
                la ruleta sorteará una de las penalizaciones activas usando los pesos configurados.
              </span>
            </div>

            <label>
              Motivo del premio
              <textarea
                name="award_reason"
                rows="4"
                value={form.award_reason}
                onChange={onFormChange}
                placeholder="Describe qué hizo el jugador para ganarse este No te flipes…"
                required
              />
              <span className="admin-form-help">Queda guardado en el histórico del premio.</span>
            </label>

            <button className="admin-button primary" type="submit" disabled={saving || !form.player || !form.season || !form.award_reason.trim()}>
              {saving ? 'Concediendo…' : 'Conceder poder de No te flipes'}
            </button>
            <span className="admin-form-help">El jugador premiado podrá usar este poder más adelante para elegir a otro jugador como objetivo.</span>
          </form>
        </section>

        <section className="admin-card">
          <SectionHeader
            eyebrow="Categorías"
            title="Pesos de aparición"
            description="El peso de categoría se combina con el peso de cada definición para calcular las probabilidades."
          />

          <div className="admin-handicap-category-list">
            {categories.map((category) => (
              <div className="admin-handicap-category" key={category.id}>
                <div>
                  <strong>{category.category_display || category.category}</strong>
                  <span>{category.active ? 'Activa' : 'Inactiva'}</span>
                </div>
                <input
                  type="number"
                  min="0"
                  value={categoryDrafts[category.id] ?? category.selection_weight}
                  disabled={saving}
                  onChange={(event) =>
                    setCategoryDrafts((current) => ({
                      ...current,
                      [category.id]: event.target.value,
                    }))
                  }
                  onBlur={() =>
                    onSaveCategory({
                      ...category,
                      selection_weight: categoryDrafts[category.id] ?? category.selection_weight,
                    })
                  }
                />
              </div>
            ))}
          </div>
          <p className="admin-form-help">Los cambios se guardan al salir del campo.</p>
        </section>
      </div>

      <section className="admin-card">
        <SectionHeader
          eyebrow={editingDefinitionId ? 'Editar' : 'Catálogo'}
          title={editingDefinitionId ? 'Modificar handicap' : 'Crear handicap'}
          description="El código se genera automáticamente. Los valores quedan guardados en el histórico de cada asignación."
        />

        <form className="admin-form" onSubmit={onSaveDefinition}>
          <div className="admin-form-grid admin-form-grid-4">
            <label>
              Nombre
              <input name="name" value={definitionForm.name} onChange={onDefinitionFieldChange} disabled={saving} required />
            </label>
            <label>
              Categoría
              <select name="category" value={definitionForm.category} onChange={onDefinitionFieldChange} disabled={saving}>
                <option value="WEAK">Débil</option>
                <option value="MEDIUM">Medio</option>
                <option value="STRONG">Fuerte</option>
              </select>
            </label>
            <label>
              Peso
              <input type="number" min="0" name="selection_weight" value={definitionForm.selection_weight} onChange={onDefinitionFieldChange} disabled={saving} />
            </label>
          </div>

          <label>
            Descripción
            <textarea name="description" rows="2" value={definitionForm.description} onChange={onDefinitionFieldChange} disabled={saving} />
          </label>

          <div className="admin-form-grid admin-form-grid-4">
            <label>
              Partidas de gracia
              <input type="number" min="0" name="grace_games" value={definitionForm.grace_games} onChange={onDefinitionFieldChange} disabled={saving} />
            </label>
            <label>
              Penalización
              <input type="number" min="0" name="penalty_points" value={definitionForm.penalty_points} onChange={onDefinitionFieldChange} disabled={saving} />
            </label>
            <label>
              Prob. base reversión %
              <input type="number" min="0" max="100" step="0.01" name="reversal_base_percent" value={definitionForm.reversal_base_percent} onChange={onDefinitionFieldChange} disabled={saving} />
            </label>
            <label>
              Ajuste por puesto %
              <input type="number" min="0" max="100" step="0.01" name="reversal_rank_step_percent" value={definitionForm.reversal_rank_step_percent} onChange={onDefinitionFieldChange} disabled={saving} />
            </label>
          </div>

          <div className="admin-form-grid admin-form-grid-4">
            <label>
              Prob. mínima %
              <input type="number" min="0" max="100" step="0.01" name="reversal_min_percent" value={definitionForm.reversal_min_percent} onChange={onDefinitionFieldChange} disabled={saving} />
            </label>
            <label>
              Prob. máxima %
              <input type="number" min="0" max="100" step="0.01" name="reversal_max_percent" value={definitionForm.reversal_max_percent} onChange={onDefinitionFieldChange} disabled={saving} />
            </label>
            <label className="admin-checkbox">
              <input type="checkbox" name="active" checked={definitionForm.active} onChange={onDefinitionFieldChange} disabled={saving} />
              Handicap activo
            </label>
          </div>

          <div className="admin-actions">
            <button className="admin-button primary" type="submit" disabled={saving}>
              {saving ? 'Guardando…' : editingDefinitionId ? 'Guardar cambios' : 'Crear handicap'}
            </button>
            {editingDefinitionId && (
              <button className="admin-button secondary" type="button" onClick={onCancelDefinition} disabled={saving}>
                Cancelar
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="admin-card">
        <SectionHeader
          eyebrow="Catálogo"
          title="Definiciones y probabilidades"
          description="La probabilidad mostrada se obtiene a partir de los pesos configurados."
        />
        {definitions.length === 0 ? (
          <div className="admin-empty">No hay handicaps definidos.</div>
        ) : (
          <div className="admin-handicap-definition-grid">
            {definitions.map((definition) => (
              <article className="admin-handicap-definition" key={definition.id}>
                <div className="admin-handicap-definition-header">
                  <div>
                    <span className="admin-eyebrow">{definition.category_display}</span>
                    <h3>{definition.name}</h3>
                  </div>
                  <StatusBadge tone={definition.active ? 'success' : 'neutral'}>
                    {definition.active ? 'Activo' : 'Inactivo'}
                  </StatusBadge>
                </div>
                {definition.description && <p>{definition.description}</p>}
                <div className="admin-handicap-metrics">
                  <div><span>Probabilidad</span><strong>{definition.selection_percentage ?? 0}%</strong></div>
                  <div><span>Gracia</span><strong>{definition.grace_games}</strong></div>
                  <div><span>Penalización</span><strong>-{definition.penalty_points}</strong></div>
                  <div><span>Peso</span><strong>{definition.selection_weight}</strong></div>
                </div>
                <div className="admin-actions">
                  <button className="admin-button secondary small" type="button" onClick={() => onEditDefinition(definition)} disabled={saving}>Editar</button>
                  <button className="admin-button danger small" type="button" onClick={() => onDeleteDefinition(definition)} disabled={saving}>Eliminar</button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="admin-card">
        <SectionHeader
          eyebrow="Premios concedidos"
          title="Jugadores con poder de No te flipes"
          description="Aquí ves quién tiene un No te flipes disponible para lanzárselo a otro jugador."
        />
        {handicapGrants.length === 0 ? (
          <div className="admin-empty">Todavía no hay premios concedidos.</div>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table admin-handicap-table">
              <thead>
                <tr><th>Jugador premiado</th><th>Contenido</th><th>Concedido por</th><th>Motivo del premio</th><th>Estado</th><th>Objetivo</th><th>Fecha de uso</th><th>Acciones</th></tr>
              </thead>
              <tbody>
                {handicapGrants.map((grant) => (
                  <tr key={grant.id}>
                    <td>{grant.holder_name || `Jugador #${grant.holder}`}</td>
                    <td>{grant.definition_name}</td>
                    <td>{grant.awarded_by_name || '—'}</td>
                    <td className="admin-handicap-reason">{grant.award_reason || '—'}</td>
                    <td>{grant.used ? <StatusBadge tone="info">Lanzado</StatusBadge> : <StatusBadge tone="success">Disponible</StatusBadge>}</td>
                    <td>{grant.target_player_name || '—'}</td>
                    <td>{grant.used_at ? formatDateTime(grant.used_at) : '—'}</td>
                    <td><div className="admin-table-actions"><button className="admin-button small secondary" type="button" onClick={() => onEditGrant(grant)} disabled={saving}>Editar</button><button className="admin-button small danger" type="button" onClick={() => onDeleteGrant(grant)} disabled={saving}>Eliminar</button></div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="admin-card">
        <SectionHeader
          eyebrow="Penalizaciones activas"
          title="No te flipes lanzados"
          description="Solo aparecen aquí los No te flipes que un jugador ya ha lanzado contra otro."
        />
        {assignedHandicaps.length === 0 ? (
          <div className="admin-empty">Todavía no se ha lanzado ningún No te flipes.</div>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table admin-handicap-table">
              <thead>
                <tr>
                  <th>Jugador penalizado</th>
                  <th>No te flipes</th>
                  <th>Lanzado por</th>
                  <th>Concedido por</th>
                  <th>Motivo original</th>
                  <th>Gracia</th>
                  <th>Jugadas</th>
                  <th>Restantes</th>
                  <th>Canjeada</th>
                  <th>Partida canje</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {assignedHandicaps.map((handicap) => (
                  <tr key={handicap.id}>
                    <td>{handicap.player_name || `Jugador #${handicap.player}`}</td>
                    <td>{handicap.definition_name}</td>
                    <td>{handicap.assigned_by_player_name || '—'}</td>
                    <td>{handicap.awarded_by_name || '—'}</td>
                    <td className="admin-handicap-reason">{handicap.award_reason || '—'}</td>
                    <td>{handicap.grace_games_snapshot}</td>
                    <td>{handicap.games_played}</td>
                    <td>{handicap.remaining_games}</td>
                    <td>
                      {handicap.used ? (
                        <div className="admin-handicap-used-cell">
                          <StatusBadge tone="info">Sí</StatusBadge>
                          {handicap.used_at && (
                            <small>{formatDateTime(handicap.used_at)}</small>
                          )}
                        </div>
                      ) : (
                        <StatusBadge tone="neutral">No</StatusBadge>
                      )}
                    </td>
                    <td>{handicap.used_match_id ? `#${handicap.used_match_id}` : '—'}</td>
                    <td>
                      {handicap.used ? (
                        <StatusBadge tone="info">Canjeada</StatusBadge>
                      ) : handicap.expired ? (
                        <StatusBadge tone="danger">Penaliza</StatusBadge>
                      ) : (
                        <StatusBadge tone="success">En gracia</StatusBadge>
                      )}
                    </td>
                    <td><div className="admin-table-actions"><button className="admin-button small secondary" type="button" onClick={() => onEditAssigned(handicap)} disabled={saving}>Editar</button><button className="admin-button small danger" type="button" onClick={() => onDeleteAssigned(handicap)} disabled={saving || handicap.used}>Eliminar</button></div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

function MatchesSection({
  matches,
  weeks,
  players,
  selectedMatch,
  matchForm,
  playerForm,
  eliminationForm,
  selectedPlayerDecks,
  matchPlayerOptions,
  matchPlayerIds,
  saving,
  onMatchFieldChange,
  onPlayerFieldChange,
  onEliminationFieldChange,
  onCreateMatch,
  onOpenMatch,
  onAddPlayer,
  onUpdatePlayer,
  onAddElimination,
  onCloseMatch,
  onDeleteMatch,
}) {
  const openWeeks = weeks.filter((week) => !week.closed)
  const selectedWeek = selectedMatch
    ? weeks.find(
        (week) => Number(week.id) === Number(selectedMatch.league_week),
      )
    : null

  return (
    <div className="admin-content">
      <section className="admin-card">
        <SectionHeader
          eyebrow="Paso 1"
          title="Crear partida"
          description="Selecciona una jornada abierta y registra la hora real de la partida."
        />

        <form
          className="admin-form"
          onSubmit={onCreateMatch}
        >
          <div className="admin-form-grid">
            <label>
              Jornada
              <select
                name="league_week"
                value={matchForm.league_week}
                onChange={onMatchFieldChange}
                required
              >
                <option value="">
                  Selecciona una jornada abierta
                </option>
                {openWeeks.map((week) => (
                  <option
                    key={week.id}
                    value={week.id}
                  >
                    Semana {week.number} ·{' '}
                    {formatDate(week.date)}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Fecha y hora
              <input
                type="datetime-local"
                name="played_at"
                value={matchForm.played_at}
                onChange={onMatchFieldChange}
                required
              />
            </label>
          </div>

          <label>
            Notas
            <textarea
              name="notes"
              rows="3"
              value={matchForm.notes}
              onChange={onMatchFieldChange}
              placeholder="Notas generales de la partida…"
            />
          </label>

          <button
            className="admin-button primary"
            type="submit"
            disabled={saving || openWeeks.length === 0}
          >
            {saving ? 'Creando…' : 'Crear partida'}
          </button>

          {openWeeks.length === 0 && (
            <p className="admin-form-help">
              No hay jornadas abiertas disponibles.
            </p>
          )}
        </form>
      </section>

      <div className="admin-match-layout">
        <section className="admin-card">
          <SectionHeader
            eyebrow="Partidas"
            title="Partidas registradas"
            description="Selecciona una partida para introducir o revisar resultados."
          />

          {matches.length === 0 ? (
            <div className="admin-empty">
              No hay partidas registradas.
            </div>
          ) : (
            <div className="admin-match-list">
              {matches.map((match) => (
                <button
                  className={
                    selectedMatch?.id === match.id
                      ? 'admin-match-list-item active'
                      : 'admin-match-list-item'
                  }
                  key={match.id}
                  onClick={() => onOpenMatch(match.id)}
                >
                  <div>
                    <strong>Partida #{match.id}</strong>
                    <span>
                      Semana {match.league_week_number}
                    </span>
                  </div>

                  <div>
                    <span>
                      {formatDateTime(match.played_at)}
                    </span>

                    {match.closed ? (
                      <StatusBadge tone="success">
                        Cerrada
                      </StatusBadge>
                    ) : (
                      <StatusBadge tone="warning">
                        Abierta
                      </StatusBadge>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        {selectedMatch ? (
          <section className="admin-card admin-match-editor">
            <div className="admin-match-editor-header">
              <div>
                <span className="admin-eyebrow">
                  Partida #{selectedMatch.id}
                </span>
                <h2>
                  Semana {selectedMatch.league_week_number}
                </h2>
                <p>
                  {formatDateTime(
                    selectedMatch.played_at,
                  )}
                </p>
              </div>

              {selectedMatch.closed ? (
                <StatusBadge tone="success">
                  Cerrada
                </StatusBadge>
              ) : (
                <StatusBadge tone="warning">
                  Abierta
                </StatusBadge>
              )}
            </div>

            {selectedMatch.notes && (
              <div className="admin-match-note">
                <strong>Notas</strong>
                <p>{selectedMatch.notes}</p>
              </div>
            )}

            <div className="admin-match-section">
              <SectionHeader
                eyebrow="Paso 2"
                title="Jugadores"
                description="Añade cada jugador y su mazo utilizado."
              />

              {!selectedMatch.closed && (
                <form
                  className="admin-form admin-subform"
                  onSubmit={onAddPlayer}
                >
                  <div className="admin-form-grid">
                    <label>
                      Jugador
                      <select
                        name="player"
                        value={playerForm.player}
                        onChange={onPlayerFieldChange}
                        required
                      >
                        <option value="">
                          Selecciona jugador
                        </option>
                        {players
                          .filter(
                            (player) =>
                              !matchPlayerIds.includes(
                                Number(player.id),
                              ),
                          )
                          .map((player) => (
                            <option
                              key={player.id}
                              value={player.id}
                            >
                              {player.display_name ||
                                player.username}
                            </option>
                          ))}
                      </select>
                    </label>

                    <label>
                      Mazo
                      <select
                        name="deck"
                        value={playerForm.deck}
                        onChange={onPlayerFieldChange}
                        required
                        disabled={!playerForm.player}
                      >
                        <option value="">
                          {playerForm.player
                            ? 'Selecciona mazo'
                            : 'Selecciona primero un jugador'}
                        </option>
                        {selectedPlayerDecks.map(
                          (deck) => (
                            <option
                              key={deck.id}
                              value={deck.id}
                            >
                              {deck.name} ·{' '}
                              {deck.commander}
                            </option>
                          ),
                        )}
                      </select>
                    </label>
                  </div>

                  <div className="admin-form-grid admin-form-grid-4">
                    <label>
                      Posición inicial
                      <input
                        type="number"
                        min="1"
                        name="starting_position"
                        value={
                          playerForm.starting_position
                        }
                        onChange={
                          onPlayerFieldChange
                        }
                        placeholder="1"
                      />
                    </label>

                    <label>
                      Posición final
                      <input
                        type="number"
                        min="1"
                        name="final_position"
                        value={
                          playerForm.final_position
                        }
                        onChange={
                          onPlayerFieldChange
                        }
                        placeholder="1"
                      />
                    </label>

                    <label className="admin-checkbox">
                      <input
                        type="checkbox"
                        name="first_play_of_deck"
                        checked={
                          playerForm.first_play_of_deck
                        }
                        onChange={
                          onPlayerFieldChange
                        }
                      />
                      Primera vez con este mazo
                    </label>

                    <label className="admin-checkbox">
                      <input
                        type="checkbox"
                        name="completed_weekly_event"
                        checked={
                          playerForm.completed_weekly_event
                        }
                        onChange={
                          onPlayerFieldChange
                        }
                      />
                      Evento completado
                    </label>
                  </div>

                  <div className="admin-form-grid">
                    <label className="admin-checkbox">
                      <input
                        type="checkbox"
                        name="conceded"
                        checked={playerForm.conceded}
                        onChange={onPlayerFieldChange}
                      />
                      Concedió
                    </label>

                    <label className="admin-checkbox">
                      <input
                        type="checkbox"
                        name="concession_penalty"
                        checked={
                          playerForm.concession_penalty
                        }
                        onChange={
                          onPlayerFieldChange
                        }
                      />
                      Aplicar penalización por concesión
                    </label>
                  </div>

                  <label>
                    Notas del resultado
                    <textarea
                      name="notes"
                      rows="2"
                      value={playerForm.notes}
                      onChange={onPlayerFieldChange}
                    />
                  </label>

                  <button
                    className="admin-button secondary"
                    type="submit"
                    disabled={
                      saving ||
                      !playerForm.player ||
                      !playerForm.deck
                    }
                  >
                    Añadir jugador
                  </button>
                </form>
              )}

              {selectedMatch.players?.length > 0 ? (
                <div className="admin-player-results">
                  {selectedMatch.players.map(
                    (result) => (
                      <article
                        className="admin-player-result"
                        key={result.id}
                      >
                        <div className="admin-player-result-main">
                          <strong>
                            {result.player_name}
                          </strong>
                          <span>
                            {result.deck_name_snapshot ||
                              'Mazo sin nombre'}
                          </span>
                          <small>
                            {result.commander_name_snapshot ||
                              'Comandante no disponible'}
                          </small>
                        </div>

                        <div className="admin-player-result-meta">
                          <div>
                            <span>Posición</span>
                            <strong>
                              {result.final_position ??
                                '—'}
                            </strong>
                          </div>

                          <div>
                            <span>Puntos</span>
                            <strong>
                              {result.points ?? 0}
                            </strong>
                          </div>

                          {result.first_play_of_deck && (
                            <StatusBadge tone="info">
                              Primer uso
                            </StatusBadge>
                          )}

                          {result.completed_weekly_event && (
                            <StatusBadge tone="info">
                              Evento
                            </StatusBadge>
                          )}

                          {result.conceded && (
                            <StatusBadge tone="warning">
                              Concedió
                            </StatusBadge>
                          )}

                          {result.concession_penalty && (
                            <StatusBadge tone="danger">
                              Penalización
                            </StatusBadge>
                          )}
                        </div>

                        {!selectedMatch.closed && (
                          <MatchPlayerResultEditor
                            result={result}
                            saving={saving}
                            onSave={onUpdatePlayer}
                          />
                        )}
                      </article>
                    ),
                  )}
                </div>
              ) : (
                <div className="admin-empty">
                  Todavía no hay jugadores en esta partida.
                </div>
              )}
            </div>

            <div className="admin-match-section">
              <SectionHeader
                eyebrow="Paso 3"
                title="Eliminaciones"
                description="Registra quién elimina a quién y marca la primera eliminación."
              />

              {!selectedMatch.closed && (
                <form
                  className="admin-form admin-subform"
                  onSubmit={onAddElimination}
                >
                  <div className="admin-form-grid">
                    <label>
                      Killer
                      <select
                        name="killer"
                        value={
                          eliminationForm.killer
                        }
                        onChange={
                          onEliminationFieldChange
                        }
                        required
                      >
                        <option value="">
                          Selecciona jugador
                        </option>
                        {matchPlayerOptions.map(
                          (player) => (
                            <option
                              key={player.id}
                              value={player.id}
                            >
                              {player.name}
                            </option>
                          ),
                        )}
                      </select>
                    </label>

                    <label>
                      Víctima
                      <select
                        name="victim"
                        value={
                          eliminationForm.victim
                        }
                        onChange={
                          onEliminationFieldChange
                        }
                        required
                      >
                        <option value="">
                          Selecciona jugador
                        </option>
                        {matchPlayerOptions.map(
                          (player) => (
                            <option
                              key={player.id}
                              value={player.id}
                            >
                              {player.name}
                            </option>
                          ),
                        )}
                      </select>
                    </label>

                    <label>
                      Turno
                      <input
                        type="number"
                        min="1"
                        name="turn"
                        value={eliminationForm.turn}
                        onChange={
                          onEliminationFieldChange
                        }
                        placeholder="6"
                      />
                    </label>

                    <label className="admin-checkbox">
                      <input
                        type="checkbox"
                        name="first_elimination"
                        checked={
                          eliminationForm.first_elimination
                        }
                        onChange={
                          onEliminationFieldChange
                        }
                      />
                      Primera eliminación
                    </label>
                  </div>

                  <button
                    className="admin-button secondary"
                    type="submit"
                    disabled={
                      saving ||
                      !eliminationForm.killer ||
                      !eliminationForm.victim
                    }
                  >
                    Registrar eliminación
                  </button>
                </form>
              )}

              {selectedMatch.eliminations?.length > 0 ? (
                <div className="admin-elimination-list">
                  {selectedMatch.eliminations.map(
                    (elimination) => (
                      <div
                        className="admin-elimination"
                        key={elimination.id}
                      >
                        <strong>
                          {elimination.killer_name}
                        </strong>
                        <span>→</span>
                        <strong>
                          {elimination.victim_name}
                        </strong>

                        {elimination.turn && (
                          <small>
                            Turno {elimination.turn}
                          </small>
                        )}

                        {elimination.first_elimination && (
                          <StatusBadge tone="info">
                            Primera
                          </StatusBadge>
                        )}
                      </div>
                    ),
                  )}
                </div>
              ) : (
                <div className="admin-empty">
                  Todavía no hay eliminaciones registradas.
                </div>
              )}
            </div>

            <div className="admin-match-footer">
              {selectedMatch.closed ? (
                <div className="admin-closed-actions">
                  <div className="admin-closed-message">
                    <strong>Partida cerrada.</strong>
                    <span>
                      Los resultados quedan bloqueados por el
                      sistema.
                    </span>
                  </div>

                  {selectedWeek?.closed ? (
                    <p className="admin-form-help">
                      La jornada también está cerrada. Para eliminar
                      esta partida primero debe reabrirse la jornada.
                    </p>
                  ) : (
                    <div className="admin-destructive-action">
                      <p className="admin-form-help">
                        Eliminación histórica: reconstruye los anchors
                        de handicaps afectados y recalcula la temporada.
                      </p>
                      <button
                        className="admin-button danger"
                        type="button"
                        onClick={onDeleteMatch}
                        disabled={saving || !selectedWeek}
                      >
                        Eliminar partida cerrada
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                (() => {
                  const playersWithoutFinalPosition =
                    selectedMatch.players?.filter(
                      (player) => player.final_position == null,
                    ).length || 0

                  return (
                    <div>
                      {playersWithoutFinalPosition > 0 && (
                        <p className="admin-form-help">
                          Faltan posiciones finales para{' '}
                          {playersWithoutFinalPosition}{' '}
                          {playersWithoutFinalPosition === 1
                            ? 'jugador'
                            : 'jugadores'}. Guarda todas las
                          posiciones antes de cerrar la partida.
                        </p>
                      )}

                      <button
                        className="admin-button danger"
                        onClick={onCloseMatch}
                        disabled={
                          saving ||
                          playersWithoutFinalPosition > 0 ||
                          !selectedMatch.players?.length
                        }
                      >
                        Cerrar partida
                      </button>
                    </div>
                  )
                })()
              )}
            </div>
          </section>
        ) : (
          <section className="admin-card admin-empty-card">
            <div className="admin-empty-large">
              <span className="admin-empty-icon"><AdminNavIcon type="matches" /></span>
              <h2>Selecciona una partida</h2>
              <p>
                Crea una partida arriba o selecciona una de la
                lista para empezar a introducir resultados.
              </p>
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

export default AdminDashboard