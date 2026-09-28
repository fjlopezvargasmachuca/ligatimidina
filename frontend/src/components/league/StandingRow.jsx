function getStatusClass(type) {
  switch (type) {
    case 'NO_TE_FLIPES_AVAILABLE':
      return 'standing-status-icon--power'
    case 'HANDICAP_ACTIVE':
      return 'standing-status-icon--handicap'
    case 'PENALTY_ACTIVE':
      return 'standing-status-icon--penalty'
    default:
      return ''
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

function StatusIcon({ status }) {
  const count = Number(status?.count || 0)

  return (
    <span
      className={`standing-status-icon ${getStatusClass(status?.type)}`}
      tabIndex={0}
      aria-label={status?.label || 'Estado del jugador'}
    >
      {getStatusIcon(status?.type)}

      {count > 1 && <small>{count}</small>}

      <span className="standing-status-tooltip" role="tooltip">
        <strong>{status?.label || 'Estado'}</strong>

        {status?.description && (
          <span>{status.description}</span>
        )}

        {status?.remaining_games != null && (
          <em>
            {status.remaining_games === 1
              ? 'Queda 1 partida de gracia.'
              : `Quedan ${status.remaining_games} partidas de gracia.`}
          </em>
        )}
      </span>
    </span>
  )
}

export default function StandingRow({ standing }) {
  const statusIcons = Array.isArray(standing?.status_icons)
    ? standing.status_icons
    : []

  return (
    <div className="standing-row">
      <div className="standing-row__position">{standing.position}</div>

      <div className="standing-row__player">
        <div className="standing-row__player-main">
          <strong>
            {standing.display_name || standing.username}
          </strong>

          {statusIcons.length > 0 && (
            <span
              className="standing-status-icons"
              aria-label="Estados del jugador"
            >
              {statusIcons.map((status, index) => (
                <StatusIcon
                  key={`${status.type || 'status'}-${index}`}
                  status={status}
                />
              ))}
            </span>
          )}
        </div>

        <span>@{standing.username}</span>
      </div>

      <div className="standing-row__stat standing-row__stat--points">
        <strong>{standing.points ?? 0}</strong>
      </div>
      <div className="standing-row__stat">{standing.wins ?? 0}</div>
      <div className="standing-row__stat">{standing.games ?? 0}</div>
      <div className="standing-row__stat">
        {standing.eliminations ?? 0}
      </div>
      <div className="standing-row__stat">{standing.weeks ?? 0}</div>
    </div>
  )
}
