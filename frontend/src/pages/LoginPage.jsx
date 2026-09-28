import { useEffect, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    setError('')
  }, [username, password])

  if (isAuthenticated) {
    const destination = location.state?.from?.pathname || '/'
    return <Navigate to={destination} replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()

    if (!username.trim() || !password) {
      setError('Introduce usuario y contraseña.')
      return
    }

    setSubmitting(true)
    setError('')

    try {
      await login(username.trim(), password)
      navigate(location.state?.from?.pathname || '/', {
        replace: true,
      })
    } catch (loginError) {
      setError(
        loginError.data?.detail ||
        'No se ha podido iniciar sesión. Comprueba tus credenciales.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-page__card card">
        <div className="auth-page__header">
          <div className="brand-mark brand-mark--large">LT</div>

          <div>
            <div className="card__eyebrow">Liga Timidina</div>
            <h1>Iniciar sesión</h1>
          </div>
        </div>

        <p className="auth-page__intro">
          Accede para consultar tu perfil, tus mazos y toda la información
          de la liga.
        </p>

        {error && (
          <div className="alert alert--error">
            {error}
          </div>
        )}

        <form className="form" onSubmit={handleSubmit}>
          <label className="form__field">
            <span>Usuario</span>

            <input
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              placeholder="Tu usuario"
            />
          </label>

          <label className="form__field">
            <span>Contraseña</span>

            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              placeholder="Tu contraseña"
            />
          </label>

          <button
            type="submit"
            className="button button--primary button--full"
            disabled={submitting}
          >
            {submitting ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}