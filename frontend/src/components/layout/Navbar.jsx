import { Link, NavLink } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  function closeMenu() {
    setMenuOpen(false)
  }

  async function handleLogout() {
    await logout()
    closeMenu()
  }

  return (
    <header className="navbar">
      <div className="container navbar__inner">
        <Link to="/" className="navbar__brand" onClick={closeMenu}>
          <span className="navbar__brand-mark">LT</span>

          <span className="navbar__brand-text">
            <strong>Liga</strong>
            <span>Timidina</span>
          </span>
        </Link>

        <button
          type="button"
          className="navbar__menu-button"
          aria-label="Abrir menú"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((value) => !value)}
        >
          <span />
          <span />
          <span />
        </button>

        <nav className={`navbar__nav ${menuOpen ? 'navbar__nav--open' : ''}`}>
          <NavLink
            to="/"
            className={({ isActive }) =>
              `navbar__link ${isActive ? 'navbar__link--active' : ''}`
            }
            onClick={closeMenu}
          >
            Clasificación
          </NavLink>

          {isAuthenticated && (
            <NavLink
              to="/perfil"
              className={({ isActive }) =>
                `navbar__link ${isActive ? 'navbar__link--active' : ''}`
              }
              onClick={closeMenu}
            >
              Mi perfil
            </NavLink>
          )}

          {user?.is_staff && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `navbar__link ${isActive ? 'navbar__link--active' : ''}`
              }
              onClick={closeMenu}
            >
              Administración
            </NavLink>
          )}

          <div className="navbar__account">
            {isAuthenticated ? (
              <>
                <span className="navbar__user">
                  {user.display_name || user.username}
                </span>

                <button
                  type="button"
                  className="button button--secondary button--small"
                  onClick={handleLogout}
                >
                  Salir
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="button button--primary button--small"
                onClick={closeMenu}
              >
                Iniciar sesión
              </Link>
            )}
          </div>
        </nav>
      </div>
    </header>
  )
}