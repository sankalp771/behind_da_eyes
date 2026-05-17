import { useState, useEffect, useCallback } from 'react'
import './App.css'

function normalizeVideoSource(url) {
  const trimmed = url.trim()
  if (!trimmed) return { kind: 'empty', src: '' }

  try {
    const parsed = new URL(trimmed)
    const host = parsed.hostname.replace(/^www\./, '')

    if (host === 'youtube.com' || host === 'm.youtube.com') {
      const id = parsed.searchParams.get('v')
      if (id) return { kind: 'iframe', src: `https://www.youtube.com/embed/${id}?rel=0&playsinline=1` }
    }

    if (host === 'youtu.be') {
      const id = parsed.pathname.split('/').filter(Boolean)[0]
      if (id) return { kind: 'iframe', src: `https://www.youtube.com/embed/${id}?rel=0&playsinline=1` }
    }

    if (/\.(mp4|webm|ogg|mov|m4v)(\?.*)?$/i.test(parsed.pathname)) {
      return { kind: 'video', src: trimmed }
    }
  } catch {
    return { kind: 'iframe', src: trimmed }
  }

  return { kind: 'iframe', src: trimmed }
}

// ── Top Bar ──────────────────────────────────────────────────────────────────
function TopBar({ status }) {
  const labels = { idle: 'ready', modal: 'paused', processing: 'thinking...', playing: 'response ready' }
  return (
    <header className="topbar">
      <div className="topbar-logo">
        <span className={`topbar-dot ${status === 'processing' ? 'processing' : ''}`} />
        BehindTheEyes
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
          <span className="response-mode-badge">{mode === 'scene' ? 'scene' : 'in character'}</span>
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
  characters, charsLoading, selectedChar, onCharChange,
  timestamp, onTimestampChange,
  question, onQuestionChange,
  onSubmit, onClose
}) {
  const toStr = (sec) => `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`
  const parseTs = (str) => {
    const p = str.split(':').map(Number)
    return p.length === 2 ? (p[0] || 0) * 60 + (p[1] || 0) : (p[0] || 0) * 3600 + (p[1] || 0) * 60 + (p[2] || 0)
  }

  const activeName = mode === 'scene'
    ? 'Scene Companion'
    : (characters.find(c => c.name === selectedChar)?.name || selectedChar || 'Character')

  return (
    <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-card">
        <div className="modal-header">
          <span className="modal-title">Ask {activeName}</span>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        {/* Mode toggle */}
        <div className="mode-toggle">
          <button className={`mode-btn ${mode === 'character' ? 'active' : ''}`} onClick={() => onModeChange('character')}>
            Character
          </button>
          <button className={`mode-btn ${mode === 'scene' ? 'active' : ''}`} onClick={() => onModeChange('scene')}>
            Scene
          </button>
        </div>

        {/* Character selector */}
        {mode === 'character' && (
          <div className="modal-char-row">
            {charsLoading ? (
              <div className="chars-loading">Finding characters from Wikipedia and model knowledge...</div>
            ) : characters.length === 0 ? (
              <input
                className="char-edit-input"
                placeholder="Type a character name..."
                value={selectedChar}
                onChange={e => onCharChange(e.target.value)}
              />
            ) : (
              <select
                className="char-select"
                value={selectedChar}
                onChange={e => onCharChange(e.target.value)}
              >
                {characters.filter(c => c.key !== '__scene__').map(c => (
                  <option key={c.key} value={c.name}>{c.name} — {c.role}</option>
                ))}
              </select>
            )}
          </div>
        )}

        {/* Scene mode hint */}
        {mode === 'scene' && (
          <p className="scene-hint">
            Ask anything — what's happening, what you missed, character motivations, themes, foreshadowing.
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
        </div>

        {/* Question */}
        <textarea
          className="modal-input"
          placeholder={mode === 'scene' ? "What's happening here?" : `Ask ${activeName} anything...`}
          value={question}
          onChange={e => onQuestionChange(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && question.trim() && (e.preventDefault(), onSubmit())}
          autoFocus
        />
        <div className="modal-footer">
          <button className="modal-submit" onClick={onSubmit} disabled={!question.trim()}>Ask →</button>
        </div>
      </div>
    </div>
  )
}

// ── Player Wrapper ────────────────────────────────────────────────────────────
function PlayerWrapper({ source, status, processingLabel, onAskClick, responseReady }) {
  const hasSource = Boolean(source?.src)

  return (
    <div className={`player-wrapper${responseReady ? ' response-ready' : ''}`}>
      {hasSource && source.kind === 'video' ? (
        <video className="player-iframe" src={source.src} controls playsInline title="BehindTheEyes Player" />
      ) : hasSource ? (
        <iframe className="player-iframe" src={source.src} allow="autoplay; fullscreen; picture-in-picture" allowFullScreen title="BehindTheEyes Player" />
      ) : (
        <div className="player-empty">
          <span className="player-empty-icon">▶</span>
          <span>Paste a video URL above to begin</span>
        </div>
      )}
      <div className="player-controls-overlay">
        {status === 'processing' ? (
          <ProcessingOverlay label={processingLabel} />
        ) : (
          <button className="ask-btn" onClick={onAskClick} disabled={!hasSource} title="Ask about this moment">?</button>
        )}
      </div>
    </div>
  )
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  // Video
  const [inputUrl, setInputUrl]       = useState('')
  const [playerSource, setPlayerSource] = useState({ kind: 'empty', src: '' })
  const [fileName, setFileName]       = useState('')

  // Show title — drives the whole engine
  const [showTitle, setShowTitle]     = useState('')

  // Characters (dynamically generated)
  const [characters, setCharacters]   = useState([])
  const [charsLoading, setCharsLoading] = useState(false)
  const [selectedChar, setSelectedChar] = useState('')

  // Mode
  const [mode, setMode]               = useState('character')

  // Player state
  const [pausedAt, setPausedAt]       = useState(0)
  const [showModal, setShowModal]     = useState(false)
  const [question, setQuestion]       = useState('')
  const [status, setStatus]           = useState('idle')
  const [error, setError]             = useState(null)
  const [responseData, setResponseData] = useState(null)

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

  useEffect(() => {
    return () => {
      if (playerSource.kind === 'video' && playerSource.src.startsWith('blob:')) {
        URL.revokeObjectURL(playerSource.src)
      }
    }
  }, [playerSource])

  // Fetch characters dynamically when show title changes
  const fetchCharacters = useCallback(async (title) => {
    if (!title.trim()) { setCharacters([]); return }
    setCharsLoading(true)
    setCharacters([])
    try {
      const res = await fetch(`/api/characters?show_title=${encodeURIComponent(title.trim())}`)
      if (!res.ok) throw new Error('Failed to fetch')
      const data = await res.json()
      setCharacters(data.characters || [])
      // Auto-select first real character
      const first = (data.characters || []).find(c => c.key !== '__scene__')
      if (first) setSelectedChar(first.name)
    } catch {
      setCharacters([])
    } finally {
      setCharsLoading(false)
    }
  }, [])

  const handleLoadUrl = () => {
    if (inputUrl.trim()) {
      setPlayerSource(normalizeVideoSource(inputUrl))
      setFileName('')
      setResponseData(null)
      setStatus('idle')
    }
  }

  const handleFileSelect = (file) => {
    if (!file) return
    if (playerSource.kind === 'video' && playerSource.src.startsWith('blob:')) {
      URL.revokeObjectURL(playerSource.src)
    }
    setPlayerSource({ kind: 'video', src: URL.createObjectURL(file) })
    setFileName(file.name)
    setInputUrl('')
    setResponseData(null)
    setStatus('idle')
  }

  const handleSetShow = () => {
    if (showTitle.trim()) fetchCharacters(showTitle.trim())
  }

  const onAskClick = () => { setShowModal(true); setStatus('modal') }
  const onClose    = () => { setShowModal(false); setStatus('idle'); setQuestion('') }

  const getProcessingLabel = () => {
    if (mode === 'scene') return `${showTitle || 'Scene'}`
    return selectedChar || 'Character'
  }

  const onSubmit = async () => {
    if (!question.trim()) return
    if (!showTitle.trim()) { setError('Enter the show/series title first.'); return }

    setStatus('processing')
    setShowModal(false)
    setResponseData(null)
    setError(null)

    const body = {
      timestamp:  pausedAt,
      question:   question.trim(),
      show_title: showTitle.trim(),
      mode,
    }
    if (mode === 'character') {
      body.character_name = selectedChar || null
    }

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const d = await res.json().catch(() => ({}))
        throw new Error(d.detail || `Error ${res.status}`)
      }
      const data = await res.json()
      setResponseData(data)
      setStatus('playing')
    } catch (err) {
      setError(err.message || 'Something went wrong')
      setStatus('idle')
    } finally {
      setQuestion('')
    }
  }

  return (
    <div className="screen">
      <TopBar status={status} />

      <main className="player-area">
        {/* URL + Show Title row */}
        <div className="config-row">
          <div className="config-field">
            <label className="config-label">Video URL</label>
            <div className="config-input-row">
              <input
                className="url-input"
                type="text"
                placeholder="Paste any video URL..."
                value={inputUrl}
                onChange={e => setInputUrl(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleLoadUrl()}
              />
              <button className="url-load-btn" onClick={handleLoadUrl}>Load</button>
              <label className="file-load-btn">
                File
                <input
                  type="file"
                  accept="video/*"
                  onChange={e => handleFileSelect(e.target.files?.[0])}
                />
              </label>
            </div>
          </div>
          <div className="config-field">
            <label className="config-label">Show / Series</label>
            <div className="config-input-row">
              <input
                className="url-input"
                type="text"
                placeholder="e.g. Death Note, Mirzapur, Young Sheldon..."
                value={showTitle}
                onChange={e => setShowTitle(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSetShow()}
              />
              <button
                className="url-load-btn"
                onClick={handleSetShow}
                disabled={charsLoading}
              >
                {charsLoading ? '...' : 'Set'}
              </button>
            </div>
          </div>
        </div>

        {/* Character chips (dynamic) */}
        {characters.length > 0 && (
          <div className="char-chips">
            {characters.filter(c => c.key !== '__scene__').map(c => (
              <button
                key={c.key}
                className={`char-chip ${selectedChar === c.name ? 'active' : ''}`}
                onClick={() => setSelectedChar(c.name)}
                title={c.role}
              >
                {c.name}
              </button>
            ))}
          </div>
        )}

        {error && <p className="error-msg">{error}</p>}
        {fileName && <p className="source-note">Loaded local file: {fileName}</p>}

        {/* Response */}
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
          source={playerSource}
          status={status}
          processingLabel={getProcessingLabel()}
          onAskClick={onAskClick}
          responseReady={status === 'playing'}
        />
      </main>

      {showModal && (
        <AskModal
          mode={mode}                     onModeChange={setMode}
          characters={characters}         charsLoading={charsLoading}
          selectedChar={selectedChar}     onCharChange={setSelectedChar}
          timestamp={pausedAt}            onTimestampChange={setPausedAt}
          question={question}             onQuestionChange={setQuestion}
          onSubmit={onSubmit}             onClose={onClose}
        />
      )}
    </div>
  )
}
