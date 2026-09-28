export default function ErrorMessage({
  message = 'Ha ocurrido un error.',
  onRetry,
}) {
  return (
    <div className="alert alert--error">
      <div>
        <strong>Algo ha salido mal</strong>
        <p>{message}</p>
      </div>

      {onRetry && (
        <button
          type="button"
          className="button button--secondary button--small"
          onClick={onRetry}
        >
          Reintentar
        </button>
      )}
    </div>
  )
}