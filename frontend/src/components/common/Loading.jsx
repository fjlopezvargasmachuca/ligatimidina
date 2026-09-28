export default function Loading({ message = 'Cargando...' }) {
  return (
    <div className="loading">
      <div className="loading__spinner" />
      <span>{message}</span>
    </div>
  )
}