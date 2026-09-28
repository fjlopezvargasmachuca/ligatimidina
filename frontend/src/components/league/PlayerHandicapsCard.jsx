import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import './PlayerHandicapsCard.css'

function getErrorMessage(error) {
  return (
    error?.data?.detail ||
    error?.message ||
    'No se han podido cargar tus penalizaciones de No te flipes.'
  )
}

function formatDateTime(value) {
  if (!value) return '—'

  return new Intl.DateTimeFormat('es-ES', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export default function PlayerHandicapsCard({ playerId }) {
  const [handicaps, setHandicaps] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError('')

      try {
        const response = await api.get(
          `/handicaps/players/${playerId}/`,
        )

        if (!cancelled) {
          setHandicaps(Array.isArray(response) ? response : [])
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(getErrorMessage(requestError))
          setHandicaps([])
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    if (playerId) {
      load()
    }

    return () => {
      cancelled = true
    }
  }, [playerId])

  const pending = useMemo(
    () => handicaps.filter((handicap) => !handicap.used),
    [handicaps],
  )

  const used = useMemo(
    () => handicaps.filter((handicap) => handicap.used),
    [handicaps],
  )

  if (loading) {
    return (
      <section className="league-card profile-handicaps-card">
        <div className="section-title">
          <span>No te flipes</span>
          <h2>Penalizaciones que debes canjear</h2>
        </div>
        <div className="profile-handicaps-muted">
          Cargando tus penalizaciones…
        </div>
      </section>
    )
  }

  return (
    <section className="league-card profile-handicaps-card">
      <div className="profile-handicaps-header">
        <div className="section-title">
          <span>No te flipes</span>
          <h2>Penalizaciones que debes canjear</h2>
        </div>
        {pending.length > 0 && (
          <span className="profile-handicaps-count">
            {pending.length === 1
              ? '1 pendiente'
              : `${pending.length} pendientes`}
          </span>
        )}
      </div>

      {error ? (
        <div className="app-alert error">
          {error}
        </div>
      ) : pending.length === 0 ? (
        <div className="profile-handicaps-empty">
          <strong>No tienes ninguna penalización pendiente.</strong>
          <span>
            Cuando te lancen un No te flipes aparecerá aquí con sus
            condiciones.
          </span>
        </div>
      ) : (
        <div className="profile-handicaps-list">
          {pending.map((handicap) => (
            <article
              className="profile-handicap-item"
              key={handicap.id}
            >
              <div className="profile-handicap-icon" aria-hidden="true">
                ⛓
              </div>

              <div className="profile-handicap-main">
                <div className="profile-handicap-title-row">
                  <div>
                    <strong>{handicap.name || handicap.definition_name}</strong>
                    {handicap.category_display && (
                      <span>{handicap.category_display}</span>
                    )}
                  </div>

                  <span className="profile-handicap-status">
                    Pendiente
                  </span>
                </div>

                {handicap.description && (
                  <p>{handicap.description}</p>
                )}

                {handicap.award_reason && (
                  <div className="profile-handicap-reason">
                    <span>Motivo</span>
                    <strong>{handicap.award_reason}</strong>
                  </div>
                )}

                <div className="profile-handicap-metrics">
                  <div>
                    <span>Gracia restante</span>
                    <strong>
                      {handicap.remaining_games ?? 0}
                    </strong>
                  </div>
                  <div>
                    <span>Partidas jugadas</span>
                    <strong>
                      {handicap.games_played ?? 0}
                    </strong>
                  </div>
                  <div>
                    <span>Penalización</span>
                    <strong>
                      -{handicap.penalty_points ?? handicap.penalty_points_snapshot ?? 0}
                    </strong>
                  </div>
                </div>

                <small className="profile-handicap-help">
                  El administrador registra el canje al introducir la partida.
                </small>
              </div>
            </article>
          ))}
        </div>
      )}

      {used.length > 0 && (
        <details className="profile-handicaps-history">
          <summary>
            Ver penalizaciones ya canjeadas ({used.length})
          </summary>
          <div className="profile-handicaps-used-list">
            {used.map((handicap) => (
              <div className="profile-handicap-used" key={handicap.id}>
                <div>
                  <strong>{handicap.name || handicap.definition_name}</strong>
                  <span>
                    Canjeada{handicap.used_at ? ` · ${formatDateTime(handicap.used_at)}` : ''}
                  </span>
                </div>
                <span>
                  {handicap.games_played ?? 0} partidas registradas
                </span>
              </div>
            ))}
          </div>
        </details>
      )}
    </section>
  )
}
