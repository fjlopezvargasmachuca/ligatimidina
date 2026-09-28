import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="container page">
      <div className="card empty-page">
        <div className="brand-mark brand-mark--large">404</div>

        <h1>Página no encontrada</h1>

        <p>
          La página que buscas no existe o ha cambiado de ubicación.
        </p>

        <Link to="/" className="button button--primary">
          Volver a la clasificación
        </Link>
      </div>
    </div>
  )
}