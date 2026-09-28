import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'

function asArray(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  return []
}

function playerName(player) {
  return player.display_name || player.username || `Jugador #${player.id}`
}

export default function NoTeFlipesCard({ currentUserId }) {
  const [grants, setGrants] = useState([])
  const [players, setPlayers] = useState([])
  const [targetPlayer, setTargetPlayer] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  async function load() {
    setLoading(true)
    setError('')

    try {
      const [grantsResponse, playersResponse] = await Promise.all([
        api.get('/handicaps/grants/mine/'),
        api.get('/accounts/players/'),
      ])

      setGrants(asArray(grantsResponse))
      setPlayers(asArray(playersResponse))
    } catch (requestError) {
      setError(
        requestError?.data?.detail ||
        'No se ha podido cargar tu No te flipes.',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const availableGrant = useMemo(
    () => grants.find((grant) => grant.available),
    [grants],
  )

  const targetOptions = useMemo(
    () =>
      players
        .filter((player) => Number(player.id) !== Number(currentUserId))
        .filter((player) => player.is_active !== false)
        .sort((a, b) =>
          playerName(a).localeCompare(playerName(b), 'es'),
        ),
    [players, currentUserId],
  )

  async function launch(event) {
    event.preventDefault()

    if (!availableGrant || !targetPlayer) return

    setSaving(true)
    setError('')
    setSuccess('')

    try {
      await api.post(
        `/handicaps/grants/${availableGrant.id}/use/`,
        { target_player: Number(targetPlayer) },
      )

      setTargetPlayer('')
      setSuccess('No te flipes lanzado correctamente.')
      await load()
    } catch (requestError) {
      setError(
        requestError?.data?.detail ||
        'No se ha podido lanzar el No te flipes.',
      )
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <section className="card"><p>Cargando tu No te flipes…</p></section>
  }

  return (
    <section className="card">
      <div className="card__eyebrow">No te flipes</div>
      <h2 className="card__title">Tu poder</h2>

      {availableGrant ? (
        <>
          <p>
            Tienes un No te flipes disponible. Tú eliges a quién lanzarlo,
            pero el tipo de penalización no se muestra aquí.
          </p>

          <form onSubmit={launch}>
            <label htmlFor="no-te-flipes-target">
              Jugador objetivo
            </label>
            <select
              id="no-te-flipes-target"
              value={targetPlayer}
              onChange={(event) => setTargetPlayer(event.target.value)}
              disabled={saving}
            >
              <option value="">Selecciona un jugador</option>
              {targetOptions.map((player) => (
                <option key={player.id} value={player.id}>
                  {playerName(player)}
                </option>
              ))}
            </select>

            <button
              type="submit"
              disabled={saving || !targetPlayer}
            >
              {saving ? 'Lanzando…' : 'Lanzar No te flipes'}
            </button>
          </form>
        </>
      ) : (
        <p>
          No tienes ningún No te flipes disponible ahora mismo.
        </p>
      )}

      {error && <p role="alert">{error}</p>}
      {success && <p role="status">{success}</p>}
    </section>
  )
}
