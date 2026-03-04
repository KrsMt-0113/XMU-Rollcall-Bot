/* XMU TronClass Client — renderer/app.js */

const API = window.BRIDGE?.url ?? 'http://127.0.0.1:47325'

// ── Utility ──────────────────────────────────────────────────────────────────

async function apiFetch(path, opts = {}) {
  const resp = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  return resp.json()
}

function toast(msg, type = 'info') {
  const el = document.createElement('div')
  el.className = 'toast'
  if (type === 'ok')   el.style.borderLeft = '3px solid #1a7a1a'
  if (type === 'err')  el.style.borderLeft = '3px solid #b00000'
  if (type === 'warn') el.style.borderLeft = '3px solid #7a5a00'
  el.textContent = msg
  document.getElementById('toast-container').appendChild(el)
  setTimeout(() => el.remove(), 3500)
}

function setStatus(msg, type = '') {
  const el = document.getElementById('status-msg')
  el.textContent = msg
  el.className = type === 'err' ? 'text-err' : type === 'ok' ? 'text-ok' : 'text-dim'
}

function escHtml(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
}

function relativeTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d)) return iso
  const diff = Date.now() - d.getTime()
  if (diff < 60000)    return 'just now'
  if (diff < 3600000)  return `${Math.floor(diff/60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff/3600000)}h ago`
  return `${Math.floor(diff/86400000)}d ago`
}

// ── Login ─────────────────────────────────────────────────────────────────────

const loginScreen = document.getElementById('login-screen')
const appShell    = document.getElementById('app')

document.getElementById('login-btn').addEventListener('click', doLogin)
document.getElementById('login-password').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin()
})

async function doLogin() {
  const btn      = document.getElementById('login-btn')
  const errEl    = document.getElementById('login-error')
  const username = document.getElementById('login-username').value.trim()
  const password = document.getElementById('login-password').value
  const baseUrl  = document.getElementById('login-base-url').value.trim()

  errEl.textContent = ''
  btn.disabled = true
  btn.textContent = 'LOGGING IN…'

  try {
    const res = await apiFetch('/login', {
      method: 'POST',
      body: JSON.stringify({ username, password, base_url: baseUrl }),
    })
    if (!res.ok) throw new Error(res.error || 'Unknown error')
    document.getElementById('username-display').textContent = res.data.name || username
    loginScreen.style.display = 'none'
    appShell.style.display = 'flex'
    onAppReady()
  } catch (e) {
    errEl.textContent = e.message
  } finally {
    btn.disabled = false
    btn.textContent = 'LOGIN'
  }
}

// ── Logout ────────────────────────────────────────────────────────────────────

document.getElementById('logout-btn').addEventListener('click', async () => {
  await apiFetch('/logout', { method: 'POST' })
  stopPushPoll()
  _semestersLoaded = false
  document.getElementById('semester-select').innerHTML = '<option value="">Loading semesters…</option>'
  appShell.style.display = 'none'
  loginScreen.style.display = 'flex'
  document.getElementById('login-password').value = ''
  document.getElementById('login-error').textContent = ''
})

// ── Tabs ──────────────────────────────────────────────────────────────────────

const TAB_ORDER = ['courses', 'rollcall', 'notifications']

document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => switchTab(tab.dataset.tab))
})

function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name))
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.id === `view-${name}`))
  lazyLoad(name)
}

// ── Keyboard shortcuts ────────────────────────────────────────────────────────

document.addEventListener('keydown', e => {
  if (appShell.style.display === 'none') return
  if (e.key === 'F5') { refreshCurrentTab(); return }
  if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '4') {
    e.preventDefault()
    switchTab(TAB_ORDER[parseInt(e.key) - 1])
  }
})

function refreshCurrentTab() {
  const active = document.querySelector('.tab.active')?.dataset.tab
  if (active) loadTab(active)
}

// ── Lazy load on first visit ──────────────────────────────────────────────────

const _loaded = new Set()
function lazyLoad(name) {
  if (!_loaded.has(name)) { _loaded.add(name); loadTab(name) }
}

function onAppReady() {
  _loaded.clear()
  loadTab('courses')
  loadTab('rollcall')
  checkPushStatus()
  startPushPoll()
}

async function loadTab(name) {
  if (name === 'courses')       return loadCourses()
  if (name === 'rollcall')      return loadRollcall()
  if (name === 'notifications') return loadNotifications()
}

// ── Courses ───────────────────────────────────────────────────────────────────

document.getElementById('courses-refresh').addEventListener('click', () => loadCourses())
document.getElementById('course-back').addEventListener('click', showCourseList)
document.getElementById('course-detail-refresh').addEventListener('click', () => {
  const id = document.getElementById('course-detail-pane').dataset.courseId
  if (id) loadCourseDetail(parseInt(id), _currentDetailTab)
})
document.getElementById('semester-select').addEventListener('change', e => {
  const opt = e.target.selectedOptions[0]
  const sid = opt.value ? parseInt(opt.value) : null
  const ayid = opt.dataset.academicYearId ? parseInt(opt.dataset.academicYearId) : null
  loadCourses(sid, ayid)
})

document.querySelectorAll('.detail-tab').forEach(t => {
  t.addEventListener('click', () => {
    document.querySelectorAll('.detail-tab').forEach(x => x.classList.remove('active'))
    t.classList.add('active')
    _currentDetailTab = t.dataset.detailTab
    const id = parseInt(document.getElementById('course-detail-pane').dataset.courseId)
    if (id) loadCourseDetail(id, _currentDetailTab)
  })
})

let _currentDetailTab = 'activities'
let _semestersLoaded = false

function showCourseList() {
  document.getElementById('courses-pane').style.display = ''
  document.getElementById('course-detail-pane').style.display = 'none'
}

async function loadSemesters() {
  if (_semestersLoaded) return null
  const sel = document.getElementById('semester-select')
  try {
    const res = await apiFetch('/semesters')
    if (!res.ok || !res.data?.length) {
      sel.innerHTML = '<option value="">All semesters</option>'
      return null
    }
    const items = res.data
    items.sort((a, b) => {
      // Active semester first
      if (!!b.is_active !== !!a.is_active) return b.is_active ? 1 : -1
      // Then by sort field desc (higher = newer), fallback to id
      return (b.sort ?? b.id ?? 0) - (a.sort ?? a.id ?? 0)
    })
    sel.innerHTML = items.map((s, i) =>
      `<option value="${s.id}" data-academic-year-id="${s.academic_year_id ?? ''}"${i === 0 ? ' selected' : ''}>${escHtml(s.name || `Semester ${s.id}`)}</option>`
    ).join('') + '<option value="">All semesters</option>'
    _semestersLoaded = true
    const latest = items[0]
    return latest ? { sid: latest.id, ayid: latest.academic_year_id ?? null } : null
  } catch (_) {
    sel.innerHTML = '<option value="">All semesters</option>'
  }
  return null
}

async function loadCourses(semesterId = undefined, academicYearId = undefined) {
  const list = document.getElementById('courses-list')
  list.innerHTML = '<li class="loading"><span class="spinner"></span>Loading…</li>'
  showCourseList()

  let sid = semesterId
  let ayid = academicYearId
  if (sid === undefined) {
    const latest = await loadSemesters()
    sid = latest?.sid ?? null
    ayid = latest?.ayid ?? null
  }

  const params = new URLSearchParams()
  if (sid) params.set('semester_id', sid)
  if (ayid) params.set('academic_year_id', ayid)
  const qs = params.toString() ? `?${params}` : ''
  try {
    const res = await apiFetch(`/courses${qs}`)
    if (!res.ok) throw new Error(res.error)
    const items = res.data
    if (!items.length) {
      list.innerHTML = '<li class="loading text-dim">No courses found.</li>'
      return
    }
    list.innerHTML = items.map((c, i) => `
      <li class="list-item course-row" style="cursor:pointer;" data-id="${c.id}" data-title="${escHtml(c.title).replace(/"/g, '&quot;')}">
        <span class="item-index">${String(i + 1).padStart(2, '0')}</span>
        <div class="item-body">
          <div class="item-title ellipsis">${escHtml(c.title)}</div>
          <div class="item-meta">
            <span>${escHtml(c.teacher || '—')}</span>
            ${c.semester ? `<span class="text-dim">${escHtml(c.semester)}</span>` : ''}
            ${c.code ? `<span class="text-dim">${escHtml(c.code)}</span>` : ''}
          </div>
        </div>
        <span class="text-dim" style="font-size:11px;align-self:center;">›</span>
      </li>`).join('')

    list.querySelectorAll('.course-row').forEach(row => {
      row.addEventListener('click', () => openCourse(parseInt(row.dataset.id), row.dataset.title))
    })
  } catch (e) {
    list.innerHTML = `<li class="loading text-err">Error: ${escHtml(e.message)}</li>`
    setStatus(e.message, 'err')
  }
}

function openCourse(id, title) {
  const pane = document.getElementById('course-detail-pane')
  pane.dataset.courseId = id
  document.getElementById('course-detail-title').textContent = title
  document.getElementById('courses-pane').style.display = 'none'
  pane.style.display = ''
  _currentDetailTab = 'activities'
  document.querySelectorAll('.detail-tab').forEach(t => t.classList.toggle('active', t.dataset.detailTab === 'activities'))
  loadCourseDetail(id, 'activities')
}

async function loadCourseDetail(courseId, tab) {
  const list = document.getElementById('course-detail-list')
  const meta = document.getElementById('course-detail-meta')
  list.innerHTML = '<li class="loading"><span class="spinner"></span>Loading…</li>'

  const endpoint = tab === 'bulletins'
    ? `/courses/${courseId}/bulletins`
    : tab === 'coursewares'
    ? `/courses/${courseId}/coursewares`
    : `/courses/${courseId}/activities`

  try {
    const res = await apiFetch(endpoint)
    if (!res.ok) throw new Error(res.error)
    const items = res.data
    if (!items.length) {
      list.innerHTML = `<li class="loading text-dim">No ${tab} found.</li>`
      return
    }
    if (tab === 'activities') {
      list.innerHTML = items.map((a, i) => {
        const typeLabel = (a.type || 'activity').toUpperCase()
        const typeColors = {
          HOMEWORK: '#005fa3', EXAM: '#b00000', VIDEO: '#6b006b',
          LIVE: '#006b2f', QUIZ: '#7a5a00', MATERIAL: '#7a4000',
        }
        const color = typeColors[typeLabel] || 'var(--dim)'
        const isMaterial = typeLabel === 'MATERIAL'
        return `
          <li class="list-item" ${isMaterial ? `style="cursor:pointer;" data-activity-id="${a.id}" data-material="1"` : ''}>
            <span class="item-index">${String(i + 1).padStart(2, '0')}</span>
            <div class="item-body">
              <div class="item-title ellipsis">${escHtml(a.title)}</div>
              <div class="item-meta">
                <span class="tag" style="color:${color};border-color:${color};">${typeLabel}</span>
                ${isMaterial ? '<span class="text-dim">click to view attachments</span>' : ''}
                ${a.is_published === false ? '<span class="text-dim">unpublished</span>' : ''}
              </div>
            </div>
          </li>`
      }).join('')

      // Wire up material items to show attachments
      list.querySelectorAll('[data-material="1"]').forEach(row => {
        row.addEventListener('click', () => openActivityAttachments(parseInt(row.dataset.activityId), row))
      })
    } else if (tab === 'coursewares') {
      list.innerHTML = items.map((cw, i) => {
        const ext = (cw.file_name || cw.title || '').split('.').pop().toUpperCase()
        const size = cw.file_size ? `${(cw.file_size / 1024 / 1024).toFixed(1)} MB` : ''
        return `
          <li class="list-item">
            <span class="item-index">${String(i + 1).padStart(2, '0')}</span>
            <div class="item-body">
              <div class="item-title ellipsis">${escHtml(cw.title || cw.name || cw.file_name || '(unnamed)')}</div>
              <div class="item-meta">
                ${ext ? `<span class="tag text-dim">${ext}</span>` : ''}
                ${size ? `<span class="text-dim">${size}</span>` : ''}
                <span class="text-dim">${relativeTime(cw.created_at || cw.updated_at)}</span>
              </div>
            </div>
          </li>`
      }).join('')
    } else {
      list.innerHTML = items.map((b, i) => `
        <li class="list-item">
          <span class="item-index">${String(i + 1).padStart(2, '0')}</span>
          <div class="item-body">
            <div class="item-title ellipsis">${escHtml(b.title || b.content || '(no title)')}</div>
            <div class="item-meta">
              <span class="text-dim">${relativeTime(b.created_at || b.publish_at)}</span>
            </div>
          </div>
        </li>`).join('')
    }
  } catch (e) {
    list.innerHTML = `<li class="loading text-err">Error: ${escHtml(e.message)}</li>`
  }
}

// ── Attachments modal ─────────────────────────────────────────────────────────

async function openActivityAttachments(activityId, sourceRow) {
  const modal = document.getElementById('attach-modal')
  const title = document.getElementById('attach-modal-title')
  const list  = document.getElementById('attach-modal-list')
  title.textContent = sourceRow?.querySelector('.item-title')?.textContent || 'Attachments'
  list.innerHTML = '<li class="loading"><span class="spinner"></span>Loading…</li>'
  modal.style.display = 'flex'

  try {
    const res = await apiFetch(`/activities/${activityId}/attachments`)
    if (!res.ok) throw new Error(res.error)
    if (!res.data.length) {
      list.innerHTML = '<li class="loading text-dim">No attachments found.</li>'
      return
    }
    list.innerHTML = res.data.map((f, i) => `
      <li class="list-item" style="align-items:center;">
        <span class="item-index">${String(i + 1).padStart(2, '0')}</span>
        <div class="item-body"><div class="item-title ellipsis">${escHtml(f.name)}</div></div>
        <button class="btn-small" data-file-id="${f.id}" data-file-name="${escHtml(f.name).replace(/"/g,'&quot;')}">↓ Download</button>
      </li>`).join('')

    list.querySelectorAll('button[data-file-id]').forEach(btn => {
      btn.addEventListener('click', async () => {
        btn.disabled = true; btn.textContent = '…'
        try {
          const r = await apiFetch(`/attachments/${btn.dataset.fileId}/url`)
          if (!r.ok) throw new Error(r.error)
          window.open(r.data.url, '_blank')
          btn.textContent = '✓'
        } catch (e) {
          btn.textContent = 'Err'; btn.disabled = false
          setStatus(e.message, 'err')
        }
      })
    })
  } catch (e) {
    list.innerHTML = `<li class="loading text-err">Error: ${escHtml(e.message)}</li>`
  }
}

document.getElementById('attach-modal-close').addEventListener('click', () => {
  document.getElementById('attach-modal').style.display = 'none'
})

// ── Rollcall ──────────────────────────────────────────────────────────────────
document.getElementById('rc-answer-all').addEventListener('click', answerAll)

async function loadRollcall() {
  const list = document.getElementById('rollcall-list')
  list.innerHTML = '<li class="loading"><span class="spinner"></span>Loading…</li>'
  try {
    const res = await apiFetch('/rollcall/active')
    if (!res.ok) throw new Error(res.error)
    renderRollcallList(res.data)
  } catch (e) {
    list.innerHTML = `<li class="loading text-err">Error: ${escHtml(e.message)}</li>`
    setStatus(e.message, 'err')
  }
}

function rollcallTypeTag(rc) {
  const map = {
    NUMBER_ROLLCALL: ['number', 'NUMBER'],
    RADAR_ROLLCALL:  ['radar',  'RADAR'],
    QRCODE_ROLLCALL: ['qrcode', 'QRCODE'],
    SELF_REGISTRATION_ROLLCALL: ['self', 'SELF-REG'],
  }
  const t = rc.is_number ? 'NUMBER_ROLLCALL'
          : rc.is_radar  ? 'RADAR_ROLLCALL'
          : rc.is_qrcode ? 'QRCODE_ROLLCALL'
          : 'UNKNOWN'
  const [cls, label] = map[t] ?? ['unknown', t]
  return `<span class="tag tag-type-${cls}">${label}</span>`
}

function renderRollcallList(items) {
  const list = document.getElementById('rollcall-list')
  const badge = document.getElementById('rc-badge')
  if (!items.length) {
    badge.style.display = 'none'
    list.innerHTML = `
      <li style="padding:48px 16px; text-align:center; color:var(--dim);">
        <div style="font-size:28px; margin-bottom:12px; opacity:.25;">✓</div>
        <div class="text-sm">No active rollcalls.</div>
      </li>`
    setStatus('No active rollcalls', 'ok')
    return
  }
  badge.style.display = ''
  badge.textContent = items.length
  list.innerHTML = items.map((rc, i) => `
    <li class="list-item">
      <span class="item-index">${String(i + 1).padStart(2, '0')}</span>
      <div class="item-body">
        <div class="item-title ellipsis">${escHtml(rc.course_title || 'Unknown course')}</div>
        <div class="item-meta">
          ${rollcallTypeTag(rc)}
          <span>${escHtml(rc.created_by_name || '')}</span>
          <span class="text-dim">id:${rc.rollcall_id}</span>
        </div>
      </div>
      <div class="item-actions">
        <button class="btn btn-sm" onclick="answerOne(${rc.rollcall_id}, this)">Answer</button>
      </div>
    </li>`).join('')
  setStatus(`${items.length} active rollcall${items.length > 1 ? 's' : ''}`, 'warn')
}

async function answerOne(rollcallId, btn) {
  btn.disabled = true
  btn.textContent = '…'
  try {
    const res = await apiFetch('/rollcall/answer', {
      method: 'POST',
      body: JSON.stringify({ rollcall_id: rollcallId }),
    })
    if (!res.ok) throw new Error(res.error)
    btn.textContent = '✓'
    btn.style.color = 'var(--success)'
    toast(`Answered rollcall ${rollcallId}`, 'ok')
    setTimeout(loadRollcall, 1000)
  } catch (e) {
    btn.textContent = '✗'
    btn.style.color = 'var(--error)'
    btn.disabled = false
    toast(`Failed: ${e.message}`, 'err')
  }
}

async function answerAll() {
  const btn = document.getElementById('rc-answer-all')
  btn.disabled = true
  try {
    const res = await apiFetch('/rollcall/answer_all', { method: 'POST' })
    if (!res.ok) throw new Error(res.error)
    toast('All rollcalls answered', 'ok')
    setTimeout(loadRollcall, 800)
  } catch (e) {
    toast(`Error: ${e.message}`, 'err')
  } finally {
    btn.disabled = false
  }
}

// ── Notifications ─────────────────────────────────────────────────────────────

document.getElementById('ntf-refresh').addEventListener('click', loadNotifications)

async function loadNotifications() {
  const list = document.getElementById('notifications-list')
  list.innerHTML = '<li class="loading"><span class="spinner"></span>Loading…</li>'
  try {
    const res = await apiFetch('/notifications')
    if (!res.ok) throw new Error(res.error)
    const items = res.data
    if (!items.length) {
      list.innerHTML = '<li class="loading text-dim">No notifications.</li>'
      return
    }
    list.innerHTML = items.map((n, i) => `
      <li class="list-item" style="cursor:pointer;" data-idx="${i}">
        <span class="item-index">${String(i + 1).padStart(2, '0')}</span>
        <div class="item-body">
          <div class="item-title ellipsis">${escHtml(n.message || '(no message)')}</div>
          <div class="item-meta">
            <span class="text-dim">${relativeTime(n.created_at)}</span>
          </div>
        </div>
      </li>`).join('')

    list.querySelectorAll('.list-item').forEach(row => {
      const n = items[parseInt(row.dataset.idx)]
      row.addEventListener('click', () => openNtfDetail(n))
    })
  } catch (e) {
    list.innerHTML = `<li class="loading text-err">Error: ${escHtml(e.message)}</li>`
  }
}

function openNtfDetail(n) {
  document.getElementById('ntf-modal-title').textContent = n.message || '(no message)'
  document.getElementById('ntf-modal-body').textContent = JSON.stringify(n.raw, null, 2)
  document.getElementById('ntf-modal').style.display = 'flex'
}

document.getElementById('ntf-modal-close').addEventListener('click', () => {
  document.getElementById('ntf-modal').style.display = 'none'
})

// ── Push listener ─────────────────────────────────────────────────────────────

let _pushPollInterval = null
let _pushOn = false
let _knownEventCount = 0

document.getElementById('push-toggle').addEventListener('click', togglePush)

async function togglePush() {
  if (_pushOn) {
    await apiFetch('/push/stop', { method: 'POST' })
    setPushState(false)
  } else {
    const res = await apiFetch('/push/start', { method: 'POST' })
    if (res.ok) setPushState(true)
    else toast(`Push start failed: ${res.error}`, 'err')
  }
}

function setPushState(on) {
  _pushOn = on
  const ind   = document.getElementById('push-indicator')
  const label = document.getElementById('push-label')
  ind.className = on ? 'on pulse' : ''
  label.textContent = on ? 'PUSH: ON' : 'PUSH: OFF'
}

async function checkPushStatus() {
  try {
    const res = await apiFetch('/push/status')
    if (res.ok) {
      setPushState(res.data.running)
      renderPushEvents(res.data.events || [])
    }
  } catch (_) {}
}

function startPushPoll() {
  _pushPollInterval = setInterval(async () => {
    try {
      const res = await apiFetch('/push/status')
      if (!res.ok) return
      setPushState(res.data.running)
      const events = res.data.events || []
      if (events.length !== _knownEventCount) {
        _knownEventCount = events.length
        renderPushEvents(events)
        // If new rollcall event arrived, refresh rollcall tab
        const lastEv = events[events.length - 1]
        if (lastEv?.type === 'rollcall' || lastEv?.type === 'answered') {
          loadRollcall()
          if (lastEv.type === 'answered') {
            toast(`Auto-answered rollcall ${lastEv.rollcall_id}`, 'ok')
          }
        }
      }
    } catch (_) {}
  }, 2000)
}

function stopPushPoll() {
  if (_pushPollInterval) clearInterval(_pushPollInterval)
  _pushPollInterval = null
}

document.getElementById('push-events-clear').addEventListener('click', async () => {
  await apiFetch('/push/events/clear', { method: 'POST' })
  _knownEventCount = 0
  renderPushEvents([])
})

function renderPushEvents(events) {
  const list = document.getElementById('push-event-list')
  if (!events.length) {
    list.innerHTML = '<li class="text-dim text-sm" style="padding:12px 16px;">No push events yet.</li>'
    return
  }
  list.innerHTML = [...events].reverse().map(ev => {
    let icon = '●', cls = 'text-dim', text = ''
    if (ev.type === 'rollcall') {
      const d = ev.data || {}
      icon = '▶'; cls = 'text-warn'
      const t = d.is_number ? 'NUMBER' : d.is_radar ? 'RADAR' : d.is_qrcode ? 'QRCODE' : '?'
      text = `Rollcall push: [${t}] ${escHtml(d.course_title || d.rollcall_id || '')}`
    } else if (ev.type === 'answered') {
      icon = '✓'; cls = 'text-ok'
      text = `Auto-answered rollcall #${ev.rollcall_id}`
    } else if (ev.type === 'answer_failed') {
      icon = '✗'; cls = 'text-err'
      text = `Answer failed #${ev.rollcall_id}: ${escHtml(ev.error || '')}`
    } else if (ev.type === 'notification') {
      icon = '◌'; cls = 'text-dim'
      text = `Notification: ${escHtml(JSON.stringify(ev.data).slice(0, 80))}`
    } else {
      text = escHtml(JSON.stringify(ev).slice(0, 100))
    }
    return `<li style="padding:6px 16px; border-bottom:1px solid var(--border-dim); font-size:11px;" class="${cls}">${icon} ${text}</li>`
  }).join('')
}
