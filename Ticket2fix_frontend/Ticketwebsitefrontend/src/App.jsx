import { useEffect, useState } from 'react'
import { Routes, Route, NavLink, Link, useLocation, useNavigate } from 'react-router-dom'
import Home from './pages/Home.jsx'
import Guide from './pages/Guide.jsx'
import Dashboard from './pages/Dashboard.jsx'
import SubmitTicket from './pages/SubmitTicket.jsx'
import TicketDetail from './pages/TicketDetail.jsx'
import Approval from './pages/Approval.jsx'
import { IMG } from './content/assets.js'

const SPLASH_MS = 3000   // how long the logo popup stays (3 seconds)

const link = ({ isActive }) =>
  `font-display text-base font-medium hover:opacity-80 ${isActive ? 'underline decoration-2 underline-offset-8' : ''}`

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return null
}

// Big logo popup on a dark see-through backdrop. Always opens the home page behind it,
// then fades away after 3 seconds. Uses logo.png.
function Splash() {
  const [phase, setPhase] = useState('show')   // show -> fade -> gone
  const [failed, setFailed] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    navigate('/', { replace: true })   // always start on the home page
    const fade = setTimeout(() => setPhase('fade'), SPLASH_MS - 500)
    const done = setTimeout(() => setPhase('gone'), SPLASH_MS)
    return () => { clearTimeout(fade); clearTimeout(done) }
  }, [])

  if (phase === 'gone') return null

  return (
    <div
      className={`fixed inset-0 z-[100] flex items-center justify-center bg-[#1c1030]/70 backdrop-blur-sm transition-opacity duration-500 ${phase === 'fade' ? 'opacity-0' : 'opacity-100'}`}
    >
      {failed
        ? <span className="splash-pop font-display text-6xl font-bold text-white">Ticket2fix</span>
        : <img
            src={IMG.logo}
            alt="Ticket2fix"
            className="splash-pop h-48 w-auto max-w-[85vw] object-contain drop-shadow-[0_10px_40px_rgba(0,0,0,.55)] md:h-72"
            onError={() => setFailed(true)}
          />}
    </div>
  )
}

// Logo in the middle of the top bar (uses logo1.png). Falls back to text if the file is missing.
function Logo() {
  const [failed, setFailed] = useState(false)
  return (
    <Link to="/" aria-label="Ticket2fix home" className="justify-self-center">
      {failed
        ? <span className="font-display text-2xl font-bold">Ticket2fix</span>
        : <img src={IMG.logo1} alt="Ticket2fix" className="h-20 w-auto" onError={() => setFailed(true)} />}
    </Link>
  )
}

export default function App() {
  const { pathname } = useLocation()
  const home = pathname === '/'

  return (
    <div className="relative flex min-h-screen flex-col">
      <Splash />
      <ScrollToTop />

      {/* transparent top bar: floats over the main image on the home page */}
      <header
        className={`z-30 ${home
          ? 'absolute inset-x-0 top-0 text-white [text-shadow:0_1px_8px_rgba(40,20,60,.75)]'
          : 'relative text-ink'}`}
      >
        <div className="mx-auto grid max-w-6xl grid-cols-[1fr_auto_1fr] items-center px-4 py-3">
          <nav className="flex gap-5 justify-self-start">
            <NavLink to="/" end className={link}>Home</NavLink>
            <NavLink to="/guide" className={link}>Guide</NavLink>
          </nav>
          <Logo />
          <nav className="flex gap-5 justify-self-end">
            <NavLink to="/tickets" end className={link}>Tickets</NavLink>
            <NavLink to="/submit" className={link}>New ticket</NavLink>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/guide" element={<Guide />} />
          <Route path="/tickets" element={<Page><Dashboard /></Page>} />
          <Route path="/submit" element={<Page><SubmitTicket /></Page>} />
          <Route path="/tickets/:id" element={<Page><TicketDetail /></Page>} />
          <Route path="/tickets/:id/approve" element={<Page><Approval /></Page>} />
        </Routes>
      </main>

      <footer className="on-dark bg-ink py-5 text-center text-xs text-white/70">
        Ticket2fix · Built for the Switch hackathon · Agents propose, humans approve
      </footer>
    </div>
  )
}

// Cream card with space above and below (mb-16 = gap before the footer)
const Page = ({ children }) => (
  <div className="mx-auto mb-16 mt-8 max-w-5xl rounded-3xl border-4 border-[#e2c39a] bg-[#fffaf2] px-6 py-8 shadow-lg">
    {children}
  </div>
)