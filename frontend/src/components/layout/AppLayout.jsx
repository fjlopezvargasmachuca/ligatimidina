import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'

export default function AppLayout() {
  return (
    <div className="app">
      <Navbar />

      <main className="main-content">
        <Outlet />
      </main>

      <footer className="footer">
        <div className="container footer__inner">
          <span>Liga Timidina</span>
          <span>Commander League</span>
        </div>
      </footer>
    </div>
  )
}