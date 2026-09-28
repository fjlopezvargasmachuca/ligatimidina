export default function WeeklyEventCard({ week }) {
  const event = week?.weekly_event

  if (!event) {
    return (
      <section className="card weekly-event">
        <div className="card__eyebrow">Jornada actual</div>
        <h2 className="card__title">
          {week ? `Jornada ${week.number}` : 'Sin jornada activa'}
        </h2>

        <p className="card__muted">
          Esta jornada todavía no tiene un evento semanal asignado.
        </p>
      </section>
    )
  }

  return (
    <section className="card weekly-event">
      <div className="card__eyebrow">
        Jornada {week.number}
      </div>

      <h2 className="card__title">{event.name}</h2>

      {event.description && (
        <p className="weekly-event__description">
          {event.description}
        </p>
      )}

      {event.rules && (
        <div className="weekly-event__rules">
          <h3>Reglas especiales</h3>
          <p>{event.rules}</p>
        </div>
      )}

      {event.extra_points > 0 && (
        <div className="weekly-event__points">
          +{event.extra_points} puntos
        </div>
      )}
    </section>
  )
}