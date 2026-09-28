import { useCallback, useEffect, useState } from 'react'
import { getCurrentWeek, getStandings } from '../api/league'
import ErrorMessage from '../components/common/ErrorMessage'
import Loading from '../components/common/Loading'
import NoTeFlipesCard from '../components/league/NoTeFlipesCard'
import StandingRow from '../components/league/StandingRow'
import WeeklyEventCard from '../components/league/WeeklyEventCard'

export default function StandingsPage() {
  const [standings, setStandings] = useState([])
  const [week, setWeek] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadPage = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [standingsData, weekData] = await Promise.all([
        getStandings(),
        getCurrentWeek(),
      ])
      setStandings(
        standingsData?.standings ||
        standingsData?.results ||
        standingsData ||
        [],
      )
      setWeek(weekData)
    } catch (pageError) {
      console.error(pageError)
      setError(
        pageError.data?.detail ||
        'No se ha podido cargar la clasificación.',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadPage()
  }, [loadPage])

  if (loading) {
    return (
      <div className="container page">
        <Loading message="Cargando clasificación..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="container page">
        <ErrorMessage
          message={error}
          onRetry={loadPage}
        />
      </div>
    )
  }

  return (
    <div className="container page">
      <section className="page-header">
        <div>
          <div className="card__eyebrow">Liga Timidina</div>
          <h1 className="page-header__title">Clasificación</h1>
          <p className="page-header__description">
            La clasificación de la temporada actual.
          </p>
        </div>
        {week && (
          <div className="week-badge">
            <span>Jornada</span>
            <strong>{week.number}</strong>
          </div>
        )}
      </section>

      <div className="page-grid">
        <section className="card standings-card">
          <div className="card__header">
            <div>
              <div className="card__eyebrow">Temporada actual</div>
              <h2 className="card__title">Clasificación</h2>
            </div>
            <span className="card__count">
              {standings.length} jugadores
            </span>
          </div>

          {standings.length === 0 ? (
            <div className="empty-state">
              <strong>Aún no hay clasificación</strong>
              <span>
                Cuando se registren partidas aparecerán aquí los jugadores.
              </span>
            </div>
          ) : (
            <div className="standings-list">
              {standings.map((standing, index) => (
                <StandingRow
                  key={
                    standing.player?.id ||
                    standing.player_id ||
                    standing.id ||
                    index
                  }
                  standing={{
                    ...standing,
                    position:
                      standing.position ||
                      index + 1,
                  }}
                />
              ))}
            </div>
          )}
        </section>

        <aside className="standings-sidebar">
          <NoTeFlipesCard />
          <WeeklyEventCard week={week} />
        </aside>
      </div>
    </div>
  )
}
