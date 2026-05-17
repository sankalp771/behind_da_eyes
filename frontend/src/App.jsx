import { useState, useEffect } from 'react'
import './App.css'

// ── Top Bar ──────────────────────────────────────────────────────────────────
function TopBar({ status }) {
  const labels = { idle: 'ready', modal: 'paused', processing: 'thinking...', playing: 'response ready' }
  return (
    <header className="topbar">
      <div className="topbar-logo">
        <span className={`topbar-dot ${status === 'processing' ? 'processing' : ''}`} />
        CharacterOS
      </div>
      <span className="topbar-status">{labels[status] || status}</span>
    </header>
  )
}

// ── Processing Overlay ───────────────────────────────────────────────────────
function ProcessingOverlay({ label }) {
  return (
    <div className="processing-overlay">
      <div className="processing-ring" />
      <p className="processing-label"><span>{label}</span> is thinking...</p>
    </div>
  )
}

// ── Response Card ────────────────────────────────────────────────────────────
function ResponseCard({ responder, mode, response, onDismiss }) {
  return (
    <div className={`response-card ${mode === 'scene' ? 'response-card--scene' : ''}`}>
      <div className="response-header">
        <div className="response-meta">
          <span className="response-name">{responder}</span>
          <span className="response-mode-badge">{mode === 'scene' ? 'scene analysis' : 'in character'}</span>
        </div>
        <button className="response-close" onClick={onDismiss}>×</button>
      </div>
      <p className="response-text">{response}</p>
    </div>
  )
}

// ── Ask Modal ────────────────────────────────────────────────────────────────
function AskModal({
  mode, onModeChange,
  characters, selectedChar, onCharChange,
  customName, onCustomName,
  customDesc, onCustomDesc,
  timestamp, onTimestampChange,
  question, onQuestionChange,
  onSubmit, onClose
}) {
  const toStr = (sec) => `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`
  const parseTs = (str) => {
    const p = str.split(':').map(Number)
    return p.length === 2 ? (p[0] || 0) * 60 + (p[1] || 0) : (p[0] || 0) * 3600 + (p[1] || 0) * 60 + (p[2] || 0)
  }

  const isCustom = selectedChar === '__custom__'
  const activeName = mode === 'scene'
    ? 'Scene Companion'
    : (isCustom ? (customName || 'Character') : (characters.find(c => c.key === selectedChar)?.name || 'Character'))

  return (
    <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-card">
        <div className="modal-header">
          <span className="modal-title">Ask {activeName}</span>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        {/* Mode toggle */}
        <div className="mode-toggle">
          <button
            className={`mode-btn ${mode === 'character' ? 'active' : ''}`}
            onClick={() => onModeChange('character')}
          >Character</button>
          <button
            className={`mode-btn ${mode === 'scene' ? 'active' : ''}`}
            onClick={() => onModeChange('scene')}
          >Scene</button>
        </div>

        {/* Character selector (hidden in scene mode) */}
        {mode === 'character' && (
          <div className="modal-char-row">
            <select
              className="char-select"
              value={selectedChar}
              onChange={e => onCharChange(e.target.value)}
            >
              {characters.map(c => (
                <option key={c.key} value={c.key}>{c.name} — {c.role}</option>
              ))}
              <option value="__custom__">+ Custom character...</option>
            </select>
          </div>
        )}

        {/* Custom character fields */}
        {mode === 'character' && isCustom && (
          <div className="custom-char-fields">
            <input
              className="char-edit-input"
              placeholder="Character name"
              value={customName}
              onChange={e => onCustomName(e.target.value)}
            />
            <textarea
              className="char-edit-desc"
              placeholder="Who are they? Personality, backstory, relationships — the more detail the better."
              value={customDesc}
              onChange={e => onCustomDesc(e.target.value)}
              rows={3}
            />
          </div>
        )}

        {/* Scene mode hint */}
        {mode === 'scene' && (
          <p className="scene-hint">
            Ask anything about what's happening — context, character motivations, themes, what you might have missed.
          </p>
        )}

        {/* Timestamp */}
        <div className="modal-ts-row">
          <span className="modal-ts-label">At</span>
          <input
            className="modal-ts-input"
            defaultValue={toStr(timestamp)}
            placeholder="mm:ss"
            onBlur={e => onTimestampChange(parseTs(e.target.value))}
            onKeyDown={e => e.key === 'Enter' && onTimestampChange(parseTs(e.target.value))}
          />
          <span className="modal-ts-hint">(edit if needed)</span>
        </div>

        {/* Question */}
        <textarea
          className="modal-input"
          placeholder={
            mode === 'scene'
              ? "What's happening here? Why did that just happen? What am I missing?"
              : `Ask ${activeName} anything...`
          }
          value={question}
          onChange={e => onQuestionChange(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && question.trim() && (e.preventDefault(), onSubmit())}
          autoFocus
        />

        <div className="modal-footer">
          <button className="modal-submit" onClick={onSubmit} disabled={!question.trim()}>
            Ask →
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Player Wrapper ────────────────────────────────────────────────────────────
function PlayerWrapper({ url, status, processingLabel, onAskClick, responseReady }) {
  return (
    <div className={`player-wrapper${responseReady ? ' response-ready' : ''}`}>
      {url ? (
        <iframe className="player-iframe" src={url} allow="autoplay; fullscreen" allowFullScreen title="CharacterOS Player" />
      ) : (
        <div className="player-empty">
          <span className="player-empty-icon">▶</span>
          <span>Paste a stream URL above to begin</span>
        </div>
      )}
      <div className="player-controls-overlay">
        {status === 'processing' ? (
          <ProcessingOverlay label={processingLabel} />
        ) : (
          <button className="ask-btn" onClick={onAskClick} disabled={!url} title="Ask about this moment">?</button>
        )}
      </div>
    </div>
  )
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const DEFAULT_PLAYER_URL = import.meta.env.VITE_PLAYER_URL || ''
  const DEFAULT_SERIES     = 'death_note'

  const [inputUrl, setInputUrl]       = useState(DEFAULT_PLAYER_URL)
  const [playerUrl, setPlayerUrl]     = useState(DEFAULT_PLAYER_URL)

  // Character state
  const [characters, setCharacters]   = useState([])
  const [selectedChar, setSelectedChar] = useState('light_yagami')
  const [customName, setCustomName]   = useState('')
  const [customDesc, setCustomDesc]   = useState('')

  // Mode: 'character' | 'scene'
  const [mode, setMode]               = useState('character')

  // Player state
  const [pausedAt, setPausedAt]       = useState(0)
  const [showModal, setShowModal]     = useState(false)
  const [question, setQuestion]       = useState('')
  const [status, setStatus]           = useState('idle')
  const [error, setError]             = useState(null)
  const [responseData, setResponseData] = useState(null)

  // Fetch character list on mount
  useEffect(() => {
    fetch(`/api/characters?series_key=${DEFAULT_SERIES}`)
      .then(r => r.json())
      .then(data => { if (data.characters) setCharacters(data.characters) })
      .catch(() => {
        // fallback if backend not up yet
        setCharacters([{ key: 'light_yagami', name: 'Light Yagami', role: 'Protagonist / Kira' }])
      })
  }, [])

  // Listen for postMessage from VideoDB player
  useEffect(() => {
    const handler = (e) => {
      if (e.data?.type === 'videodb:pause' || e.data?.type === 'player:pause') {
        setPausedAt(Math.floor(e.data.currentTime || 0))
      }
    }
    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [])

  const handleLoadUrl = () => {
    if (inputUrl.trim()) { setPlayerUrl(inputUrl.trim()); setResponseData(null); setStatus('idle') }
  }

  const onAskClick = () => { setShowModal(true); setStatus('modal') }
  const onClose    = () => { setShowModal(false); setStatus('idle'); setQuestion('') }

  const getProcessingLabel = () => {
    if (mode === 'scene') return 'Scene Companion'
    if (selectedChar === '__custom__') return customName || 'Character'
    return characters.find(c => c.key === selectedChar)?.name || 'Character'
  }

  const onSubmit = async () => {
    if (!question.trim()) return
    setStatus('processing')
    setShowModal(false)
    setResponseData(null)
    setError(null)

    const body = {
      timestamp:   pausedAt,
      question:    question.trim(),
      mode,
      series_key:  DEFAULT_SERIES,
    }

    if (mode === 'character') {
      if (selectedChar === '__custom__') {
        body.character_key = null
        body.custom_character_name = customName
        body.custom_character_description = customDesc
      } else {
        body.character_key = selectedChar
      }
    }

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}))
        throw new Error(detail.detail || `Server error ${res.status}`)
      }
      const data = await res.json()
      setResponseData(data)
      if (data.player_url) setPlayerUrl(data.player_url)
      setStatus('playing')
    } catch (err) {
      setError(err.message || 'Something went wrong — try a different moment')
      setStatus('idle')
    } finally {
      setQuestion('')
    }
  }

  return (
    <div className="screen">
      <TopBar status={status} />

      <main className="player-area">
        {/* URL row */}
        <div className="url-row">
          <input
            className="url-input"
            type="text"
            placeholder="Paste a VideoDB player URL or stream URL..."
            value={inputUrl}
            onChange={e => setInputUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleLoadUrl()}
          />
          <button className="url-load-btn" onClick={handleLoadUrl}>Load →</button>
        </div>

        {error && <p className="error-msg">{error}</p>}

        {/* Response card */}
        {responseData && status === 'playing' && (
          <ResponseCard
            responder={responseData.responder}
            mode={responseData.mode}
            response={responseData.response}
            onDismiss={() => { setResponseData(null); setStatus('idle') }}
          />
        )}

        {/* Player */}
        <PlayerWrapper
          url={playerUrl}
          status={status}
          processingLabel={getProcessingLabel()}
          onAskClick={onAskClick}
          responseReady={status === 'playing'}
        />
      </main>

      {showModal && (
        <AskModal
          mode={mode}                     onModeChange={setMode}
          characters={characters}         selectedChar={selectedChar}    onCharChange={setSelectedChar}
          customName={customName}         onCustomName={setCustomName}
          customDesc={customDesc}         onCustomDesc={setCustomDesc}
          timestamp={pausedAt}            onTimestampChange={setPausedAt}
          question={question}             onQuestionChange={setQuestion}
          onSubmit={onSubmit}             onClose={onClose}
        />
      )}
    </div>
  )
}
