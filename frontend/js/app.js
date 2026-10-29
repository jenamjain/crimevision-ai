/**
 * CrimeVision AI - Frontend Controller
 * Manages evidence ingestion, interactive visualization, bounding box rendering,
 * multimodal fusion, timeline reconstruction, and conversational AI forensics.
 */

// Global State
const state = {
  evidence: [],
  selectedId: null,
  filter: 'all',
  fusedCases: [],
  reports: []
};

// DOM References
const elements = {
  statEvidence: document.getElementById('stat-total-evidence'),
  statThreats: document.getElementById('stat-threats'),
  statPersons: document.getElementById('stat-persons'),
  statCases: document.getElementById('stat-cases'),
  evidenceCounter: document.getElementById('evidence-counter'),
  dropzone: document.getElementById('dropzone'),
  fileInput: document.getElementById('file-input'),
  evidenceList: document.getElementById('evidence-list-container'),
  btnAnalyzeAll: document.getElementById('btn-analyze-all'),
  btnFuseEvidence: document.getElementById('btn-fuse-evidence'),
  btnGeneratePdf: document.getElementById('btn-generate-pdf'),
  // Workspace views
  tabs: document.querySelectorAll('.ws-tab'),
  views: document.querySelectorAll('.ws-view'),
  // Inspector
  inspectorEmpty: document.getElementById('inspector-empty'),
  inspectorContent: document.getElementById('inspector-content'),
  inspectorFilename: document.getElementById('inspector-filename'),
  inspectorMeta: document.getElementById('inspector-meta'),
  inspectorBtnAnalyze: document.getElementById('inspector-btn-analyze'),
  inspectorBtnDelete: document.getElementById('inspector-btn-delete'),
  inspectorImage: document.getElementById('inspector-image'),
  inspectorCanvas: document.getElementById('inspector-canvas'),
  inspectorAudio: document.getElementById('inspector-audio'),
  inspectorVideo: document.getElementById('inspector-video'),
  detectionsPills: document.getElementById('detections-pills'),
  inspectorDescription: document.getElementById('inspector-description'),
  inspectorNotesList: document.getElementById('inspector-notes-list'),
  // Timeline
  timelineContainer: document.getElementById('timeline-events-container'),
  // Fusion
  fusionContainer: document.getElementById('fusion-container'),
  // Reports
  reportsContainer: document.getElementById('reports-container'),
  // Chat
  chatHistory: document.getElementById('chat-history'),
  chatInput: document.getElementById('chat-input'),
  chatSendBtn: document.getElementById('chat-send-btn'),
  chatSuggestions: document.getElementById('chat-suggestions')
};

// ─── Initialization ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  refreshAll();
});

function setupEventListeners() {
  // Tabs Navigation
  elements.tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      elements.tabs.forEach(t => t.classList.remove('active'));
      elements.views.forEach(v => v.classList.remove('active'));
      tab.classList.add('active');
      const targetView = document.getElementById(`view-${tab.dataset.view}`);
      if (targetView) targetView.classList.add('active');
    });
  });

  // Filter Buttons
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.filter = btn.dataset.filter;
      renderEvidenceList();
    });
  });

  // File Upload Handlers
  elements.dropzone.addEventListener('click', () => elements.fileInput.click());
  elements.fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  });

  elements.dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.dropzone.classList.add('dragover');
  });

  elements.dropzone.addEventListener('dragleave', () => {
    elements.dropzone.classList.remove('dragover');
  });

  elements.dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });

  // Actions
  elements.btnAnalyzeAll.addEventListener('click', runAnalyzeAll);
  elements.btnFuseEvidence.addEventListener('click', runFuseEvidence);
  elements.btnGeneratePdf.addEventListener('click', runGeneratePdf);

  // Inspector Buttons
  elements.inspectorBtnAnalyze.addEventListener('click', () => {
    if (state.selectedId) analyzeEvidence(state.selectedId);
  });
  elements.inspectorBtnDelete.addEventListener('click', () => {
    if (state.selectedId) deleteEvidence(state.selectedId);
  });

  // Chat
  elements.chatSendBtn.addEventListener('click', handleChatSubmit);
  elements.chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleChatSubmit();
  });

  elements.chatSuggestions.addEventListener('click', (e) => {
    const chip = e.target.closest('.suggestion-chip');
    if (chip && chip.dataset.prompt) {
      elements.chatInput.value = chip.dataset.prompt;
      handleChatSubmit();
    }
  });

  // Window resize re-renders canvas overlay
  window.addEventListener('resize', () => {
    if (state.selectedId) {
      const item = state.evidence.find(e => e.evidence_id === state.selectedId);
      if (item && item.evidence_type === 'image' && item.analysis_result) {
        drawBoundingBoxes(item.analysis_result.detected_objects);
      }
    }
  });
}

// ─── API Requests ────────────────────────────────────────────────

async function refreshAll() {
  await Promise.all([
    fetchStats(),
    fetchEvidence(),
    fetchFusedCases()
  ]);
}

async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const json = await res.json();
    if (json.success && json.data) {
      elements.statEvidence.textContent = json.data.total_evidence;
      elements.statThreats.textContent = json.data.threats_detected;
      elements.statPersons.textContent = json.data.persons_identified;
      elements.statCases.textContent = json.data.fused_cases_count;
    }
  } catch (err) {
    console.error('Stats fetch error:', err);
  }
}

async function fetchEvidence() {
  try {
    const res = await fetch('/api/evidence');
    const json = await res.json();
    if (json.success) {
      state.evidence = json.data;
      elements.evidenceCounter.textContent = `${state.evidence.length} Items`;
      renderEvidenceList();
      renderTimeline();

      // If an item was selected, re-select to refresh its UI
      if (state.selectedId) {
        const current = state.evidence.find(e => e.evidence_id === state.selectedId);
        if (current) selectEvidence(current.evidence_id);
      } else if (state.evidence.length > 0) {
        selectEvidence(state.evidence[0].evidence_id);
      }
    }
  } catch (err) {
    console.error('Evidence fetch error:', err);
  }
}

async function fetchFusedCases() {
  try {
    const res = await fetch('/api/fusion/cases');
    const json = await res.json();
    if (json.success) {
      state.fusedCases = json.data;
      renderFusionCases();
    }
  } catch (err) {
    console.error('Fused cases fetch error:', err);
  }
}

async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('notes', 'Uploaded from CrimeVision Web Console');

  try {
    const res = await fetch('/api/evidence/upload', {
      method: 'POST',
      body: formData
    });
    const json = await res.json();
    if (json.success) {
      await refreshAll();
      selectEvidence(json.data.evidence_id);
      // Auto-trigger analysis for seamless UX
      analyzeEvidence(json.data.evidence_id);
    } else {
      alert(`Upload failed: ${json.detail || json.message}`);
    }
  } catch (err) {
    console.error('Upload error:', err);
    alert('Failed to upload file.');
  }
}

async function analyzeEvidence(evidenceId) {
  const item = state.evidence.find(e => e.evidence_id === evidenceId);
  if (item) {
    item.status = 'processing';
    renderEvidenceList();
  }

  try {
    const res = await fetch(`/api/analyze/${evidenceId}`, { method: 'POST' });
    const json = await res.json();
    if (json.success) {
      await refreshAll();
      selectEvidence(evidenceId);
    } else {
      alert(`Analysis failed: ${json.detail || json.message}`);
      await refreshAll();
    }
  } catch (err) {
    console.error('Analyze error:', err);
    await refreshAll();
  }
}

async function runAnalyzeAll() {
  try {
    elements.btnAnalyzeAll.textContent = '⏳ Processing...';
    elements.btnAnalyzeAll.disabled = true;
    const res = await fetch('/api/analyze/all', { method: 'POST' });
    const json = await res.json();
    if (json.success) {
      await refreshAll();
    }
  } catch (err) {
    console.error('Analyze all error:', err);
  } finally {
    elements.btnAnalyzeAll.textContent = '⚡ Run All Pending';
    elements.btnAnalyzeAll.disabled = false;
  }
}

async function runFuseEvidence() {
  try {
    elements.btnFuseEvidence.textContent = '🧠 Fusing...';
    elements.btnFuseEvidence.disabled = true;
    const res = await fetch('/api/fusion/fuse', { method: 'POST' });
    const json = await res.json();
    if (json.success) {
      await refreshAll();
      // Switch to Fusion Tab
      const fusionTab = document.querySelector('[data-view="fusion"]');
      if (fusionTab) fusionTab.click();
    } else {
      alert(json.detail || json.message || 'Unable to fuse evidence.');
    }
  } catch (err) {
    console.error('Fusion error:', err);
    alert('Please ensure you have analyzed at least one image, audio, or video item.');
  } finally {
    elements.btnFuseEvidence.textContent = '🔗 Fuse Multimodal';
    elements.btnFuseEvidence.disabled = false;
  }
}

async function runGeneratePdf() {
  try {
    elements.btnGeneratePdf.textContent = '📄 Compiling...';
    elements.btnGeneratePdf.disabled = true;
    const res = await fetch('/api/reports/generate', { method: 'POST' });
    const json = await res.json();
    if (json.success && json.data) {
      state.reports.unshift(json.data);
      renderReports();
      // Switch to Reports tab
      const reportsTab = document.querySelector('[data-view="reports"]');
      if (reportsTab) reportsTab.click();
    } else {
      alert(json.detail || 'Could not compile report.');
    }
  } catch (err) {
    console.error('Report error:', err);
    alert('Upload and analyze evidence before generating a report.');
  } finally {
    elements.btnGeneratePdf.textContent = '📄 Export PDF Report';
    elements.btnGeneratePdf.disabled = false;
  }
}

async function deleteEvidence(evidenceId) {
  if (!confirm('Are you sure you want to delete this piece of evidence?')) return;
  try {
    const res = await fetch(`/api/evidence/${evidenceId}`, { method: 'DELETE' });
    const json = await res.json();
    if (json.success) {
      state.selectedId = null;
      await refreshAll();
      if (state.evidence.length > 0) {
        selectEvidence(state.evidence[0].evidence_id);
      } else {
        elements.inspectorContent.style.display = 'none';
        elements.inspectorEmpty.style.display = 'block';
      }
    }
  } catch (err) {
    console.error('Delete error:', err);
  }
}

// ─── Rendering Methods ───────────────────────────────────────────

function renderEvidenceList() {
  const filtered = state.evidence.filter(item => {
    if (state.filter === 'all') return true;
    return item.evidence_type === state.filter;
  });

  if (filtered.length === 0) {
    elements.evidenceList.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <div class="empty-state-title">No ${state.filter === 'all' ? '' : state.filter} Evidence</div>
        <div class="empty-state-desc">Upload files to begin analysis.</div>
      </div>
    `;
    return;
  }

  const icons = { image: '📷', audio: '🎙️', video: '🎬' };

  elements.evidenceList.innerHTML = filtered.map(item => {
    const isThreat = item.analysis_result && (
      (item.analysis_result.weapons_detected && item.analysis_result.weapons_detected.length > 0) ||
      (item.analysis_result.scene && item.analysis_result.scene.risk_level === 'critical')
    );

    const activeClass = item.evidence_id === state.selectedId ? 'active' : '';
    const statusClass = `status-${item.status}`;
    const icon = icons[item.evidence_type] || '📁';

    return `
      <div class="evidence-card ${activeClass}" onclick="selectEvidence('${item.evidence_id}')">
        <div class="card-top">
          <div class="card-title-group">
            <span class="card-type-icon">${icon}</span>
            <span class="card-filename" title="${item.filename}">${item.filename}</span>
          </div>
          <span class="status-badge ${statusClass}">${item.status}</span>
        </div>
        <div class="card-meta">
          <span>${formatBytes(item.file_size)}</span>
          ${isThreat ? '<span class="card-threat">⚠️ THREAT DETECTED</span>' : '<span>Verified</span>'}
        </div>
      </div>
    `;
  }).join('');
}

function selectEvidence(evidenceId) {
  state.selectedId = evidenceId;
  const item = state.evidence.find(e => e.evidence_id === evidenceId);
  if (!item) return;

  renderEvidenceList();

  elements.inspectorEmpty.style.display = 'none';
  elements.inspectorContent.style.display = 'block';

  elements.inspectorFilename.textContent = item.filename;
  elements.inspectorMeta.textContent = `Type: ${item.evidence_type.toUpperCase()} • Size: ${formatBytes(item.file_size)} • Uploaded: ${new Date(item.uploaded_at).toLocaleTimeString()}`;

  // Reset Viewports
  elements.inspectorImage.style.display = 'none';
  elements.inspectorCanvas.style.display = 'none';
  elements.inspectorAudio.style.display = 'none';
  elements.inspectorVideo.style.display = 'none';

  const fileUrl = `/api/evidence/file/${item.evidence_id}`;

  if (item.evidence_type === 'image') {
    elements.inspectorImage.src = fileUrl;
    elements.inspectorImage.style.display = 'block';
    elements.inspectorCanvas.style.display = 'block';

    elements.inspectorImage.onload = () => {
      if (item.analysis_result && item.analysis_result.detected_objects) {
        drawBoundingBoxes(item.analysis_result.detected_objects);
      } else {
        clearCanvas();
      }
    };
  } else if (item.evidence_type === 'audio') {
    elements.inspectorAudio.src = fileUrl;
    elements.inspectorAudio.style.display = 'block';
  } else if (item.evidence_type === 'video') {
    elements.inspectorVideo.src = fileUrl;
    elements.inspectorVideo.style.display = 'block';
  }

  // Detections & Notes
  renderInspectorDetails(item);
}

function renderInspectorDetails(item) {
  const result = item.analysis_result;
  elements.detectionsPills.innerHTML = '';
  elements.inspectorNotesList.innerHTML = '';

  if (!result) {
    elements.inspectorDescription.textContent = 'Evidence has not been analyzed yet. Click "Analyze" to run AI detection models.';
    return;
  }

  if (item.evidence_type === 'image') {
    elements.inspectorDescription.textContent = result.scene ? result.scene.description : 'Scene analysis complete.';
    
    // Render detections
    if (result.detected_objects && result.detected_objects.length > 0) {
      elements.detectionsPills.innerHTML = result.detected_objects.map(det => {
        const catClass = det.category === 'weapon' ? 'weapon' : det.category === 'person' ? 'person' : det.category === 'vehicle' ? 'vehicle' : '';
        return `
          <div class="det-tag ${catClass}">
            <span>${det.label}</span>
            <span style="opacity:0.75; font-size:0.7rem;">${Math.round(det.confidence * 100)}%</span>
          </div>
        `;
      }).join('');
    } else {
      elements.detectionsPills.innerHTML = '<span style="color:var(--text-dim); font-size:0.8rem;">No objects detected</span>';
    }

    if (result.forensic_notes) {
      elements.inspectorNotesList.innerHTML = result.forensic_notes.map(n => `<div>• ${n}</div>`).join('');
    }

  } else if (item.evidence_type === 'audio') {
    elements.inspectorDescription.textContent = result.full_transcript 
      ? `Full Transcript: "${result.full_transcript}"` 
      : 'Audio processing completed.';

    const pillItems = [];
    if (result.key_phrases) {
      result.key_phrases.forEach(kp => pillItems.push(`<div class="det-tag">💬 "${kp}"</div>`));
    }
    if (result.entities) {
      result.entities.forEach(ent => pillItems.push(`<div class="det-tag weapon">[${ent.type}] ${ent.value}</div>`));
    }
    elements.detectionsPills.innerHTML = pillItems.length > 0 ? pillItems.join('') : '<span style="color:var(--text-dim);">No key entities identified</span>';

    if (result.sentiment_summary) {
      elements.inspectorNotesList.innerHTML = `
        <div>• Speakers Identified: ${result.speakers_count}</div>
        <div>• Sentiment Analysis: Positive ${Math.round(result.sentiment_summary.positive * 100)}% | Negative ${Math.round(result.sentiment_summary.negative * 100)}% | Neutral ${Math.round(result.sentiment_summary.neutral * 100)}%</div>
      `;
    }

  } else if (item.evidence_type === 'video') {
    elements.inspectorDescription.textContent = `Analyzed ${result.keyframes ? result.keyframes.length : 0} keyframes across ${result.duration}s footage. Tracked ${result.persons_tracked} person(s).`;

    const pillItems = [];
    if (result.actions_detected) {
      result.actions_detected.forEach(act => pillItems.push(`<div class="det-tag person">🎬 ${act}</div>`));
    }
    if (result.objects_summary) {
      Object.entries(result.objects_summary).forEach(([label, count]) => {
        pillItems.push(`<div class="det-tag">${label}: ${count}x</div>`);
      });
    }
    elements.detectionsPills.innerHTML = pillItems.length > 0 ? pillItems.join('') : '<span style="color:var(--text-dim);">No significant actions detected</span>';

    if (result.timeline) {
      elements.inspectorNotesList.innerHTML = result.timeline.slice(0, 5).map(ev => `<div>• [${ev.time_label}] ${ev.description}</div>`).join('');
    }
  }
}

// ─── Interactive Canvas Bounding Boxes ───────────────────────────

function drawBoundingBoxes(detections) {
  const img = elements.inspectorImage;
  const canvas = elements.inspectorCanvas;
  if (!img || !canvas) return;

  const rect = img.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `${rect.height}px`;

  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const naturalW = img.naturalWidth || rect.width;
  const naturalH = img.naturalHeight || rect.height;
  const scaleX = rect.width / naturalW;
  const scaleY = rect.height / naturalH;

  detections.forEach(det => {
    const box = det.bbox;
    const x = box.x1 * scaleX;
    const y = box.y1 * scaleY;
    const w = (box.x2 - box.x1) * scaleX;
    const h = (box.y2 - box.y1) * scaleY;

    let strokeColor = '#06b6d4'; // default cyan
    let bgColor = 'rgba(6, 182, 212, 0.2)';
    let textBg = '#06b6d4';

    if (det.category === 'weapon') {
      strokeColor = '#ef4444';
      bgColor = 'rgba(239, 68, 68, 0.25)';
      textBg = '#ef4444';
    } else if (det.category === 'person') {
      strokeColor = '#3b82f6';
      bgColor = 'rgba(59, 130, 246, 0.2)';
      textBg = '#3b82f6';
    } else if (det.category === 'vehicle') {
      strokeColor = '#f59e0b';
      bgColor = 'rgba(245, 158, 11, 0.2)';
      textBg = '#f59e0b';
    }

    // Box fill & stroke
    ctx.fillStyle = bgColor;
    ctx.fillRect(x, y, w, h);

    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, w, h);

    // Label badge
    const label = `${det.label.toUpperCase()} ${Math.round(det.confidence * 100)}%`;
    ctx.font = 'bold 11px Inter, sans-serif';
    const textWidth = ctx.measureText(label).width;

    ctx.fillStyle = textBg;
    ctx.fillRect(x, Math.max(0, y - 18), textWidth + 10, 18);

    ctx.fillStyle = '#ffffff';
    ctx.fillText(label, x + 5, Math.max(13, y - 5));
  });
}

function clearCanvas() {
  const canvas = elements.inspectorCanvas;
  if (canvas) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
}

// ─── Timeline View ───────────────────────────────────────────────

function renderTimeline() {
  const events = [];

  state.evidence.forEach(item => {
    if (!item.analysis_result) return;
    const res = item.analysis_result;

    if (item.evidence_type === 'video' && res.timeline) {
      res.timeline.forEach(ev => events.push(ev));
    } else if (item.evidence_type === 'audio' && res.segments) {
      res.segments.forEach(seg => {
        events.push({
          timestamp: seg.start_time,
          time_label: `${Math.floor(seg.start_time / 60).toString().padStart(2, '0')}:${Math.floor(seg.start_time % 60).toString().padStart(2, '0')}`,
          event_type: 'speech',
          description: `[${seg.speaker_id}] "${seg.text}"`,
          source: 'audio'
        });
      });
    } else if (item.evidence_type === 'image' && res.scene) {
      events.push({
        timestamp: 0,
        time_label: new Date(item.uploaded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        event_type: res.weapons_detected && res.weapons_detected.length > 0 ? 'weapon_detection' : 'image_capture',
        description: `${item.filename}: ${res.scene.description}`,
        source: 'image'
      });
    }
  });

  if (events.length === 0) {
    elements.timelineContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">⏳</div>
        <div class="empty-state-title">No Timeline Reconstructed</div>
        <div class="empty-state-desc">Upload audio or video footage and run analysis to populate the chronological timeline.</div>
      </div>
    `;
    return;
  }

  // Sort chronological
  events.sort((a, b) => a.timestamp - b.timestamp);

  elements.timelineContainer.innerHTML = events.map(ev => {
    const isThreat = ev.event_type.toLowerCase().includes('weapon');
    return `
      <div class="timeline-node ${isThreat ? 'threat' : ''}">
        <div class="timeline-header">
          <span class="timeline-time">${ev.time_label}</span>
          <span class="timeline-source">${ev.source}</span>
        </div>
        <div class="timeline-desc">${ev.description}</div>
      </div>
    `;
  }).join('');
}

// ─── Multimodal Fusion View ──────────────────────────────────────

function renderFusionCases() {
  if (state.fusedCases.length === 0) {
    elements.fusionContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🧠</div>
        <div class="empty-state-title">No Fused Cases Synthesized</div>
        <div class="empty-state-desc">Click "Fuse Multimodal" in the top bar to correlate all evidence items.</div>
      </div>
    `;
    return;
  }

  const latest = state.fusedCases[state.fusedCases.length - 1];
  const riskColors = {
    critical: 'var(--threat-red)',
    high: 'var(--warning-amber)',
    medium: 'var(--accent-cyan)',
    low: 'var(--success-emerald)'
  };
  const riskColor = riskColors[latest.risk_assessment] || 'var(--accent-blue)';

  elements.fusionContainer.innerHTML = `
    <div style="display: flex; gap: 16px; margin-bottom: 20px;">
      <div class="intel-card" style="flex: 1; border-color: ${riskColor};">
        <div class="intel-card-title">🚨 Threat Level Assessment</div>
        <div style="font-size: 1.6rem; font-weight: 800; color: ${riskColor}; font-family: var(--font-mono);">
          ${latest.risk_assessment.toUpperCase()}
        </div>
        <p style="margin-top: 6px;">Synthesized from cross-modal weapon detections and transcript sentiments.</p>
      </div>

      <div class="intel-card" style="flex: 1;">
        <div class="intel-card-title">📁 Case Identifier</div>
        <div style="font-size: 1.4rem; font-weight: 700; color: var(--accent-cyan); font-family: var(--font-mono);">
          ${latest.case_id}
        </div>
        <p style="margin-top: 6px;">Correlating ${latest.evidence_items.length} evidence pieces.</p>
      </div>
    </div>

    <!-- Key Findings -->
    <div class="intel-card">
      <div class="intel-card-title">🔍 Key Forensic Findings</div>
      ${latest.key_findings.map(f => `<div style="margin-bottom: 8px;">• ${f}</div>`).join('')}
    </div>

    <!-- Cross-Modal Correlations -->
    <div class="intel-card">
      <div class="intel-card-title">🔗 Cross-Modal Corroborations</div>
      ${latest.cross_modal_correlations.length > 0 ? latest.cross_modal_correlations.map(c => `
        <div style="margin-bottom: 10px; padding: 8px 12px; background: rgba(255,255,255,0.02); border-radius: 6px;">
          <div style="font-weight: 600; color: #fff;">${c.description}</div>
          <div style="font-size: 0.72rem; color: var(--accent-cyan); margin-top: 4px;">Confidence: ${Math.round(c.confidence * 100)}% • Modalities: ${c.modalities.join(' + ')}</div>
        </div>
      `).join('') : '<p>No cross-modal overlaps detected yet.</p>'}
    </div>

    <!-- Recommendations -->
    <div class="intel-card">
      <div class="intel-card-title">📋 Investigative Recommendations</div>
      ${latest.recommendations.map(r => `<div style="margin-bottom: 6px;">💡 ${r}</div>`).join('')}
    </div>
  `;
}

// ─── Reports View ────────────────────────────────────────────────

function renderReports() {
  if (state.reports.length === 0) {
    elements.reportsContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📑</div>
        <div class="empty-state-title">No Reports Generated Yet</div>
        <div class="empty-state-desc">Click "Export PDF Report" in the header to compile an official investigation report.</div>
      </div>
    `;
    return;
  }

  elements.reportsContainer.innerHTML = state.reports.map(rep => `
    <div class="intel-card" style="display: flex; justify-content: space-between; align-items: center;">
      <div>
        <div style="font-weight: 700; font-size: 0.95rem; color: #fff;">📄 ${rep.filename}</div>
        <div style="font-size: 0.75rem; color: var(--text-dim); margin-top: 4px;">Forensic Case Intelligence Dossier • Court-Ready</div>
      </div>
      <a href="${rep.download_url}" target="_blank" class="btn btn-primary" download>
        ⬇️ Download PDF
      </a>
    </div>
  `).join('');
}

// ─── AI Conversational Chat ──────────────────────────────────────

async function handleChatSubmit() {
  const query = elements.chatInput.value.trim();
  if (!query) return;

  elements.chatInput.value = '';

  // Append user bubble
  appendChatBubble('user', query);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: query })
    });
    const json = await res.json();
    if (json.success && json.data) {
      appendChatBubble('assistant', json.data.response);
      // Update suggestions if provided
      if (json.data.suggestions && json.data.suggestions.length > 0) {
        updateSuggestions(json.data.suggestions);
      }
    }
  } catch (err) {
    console.error('Chat error:', err);
    appendChatBubble('assistant', '⚠️ Unable to process forensic query at this time.');
  }
}

function appendChatBubble(role, content) {
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;
  bubble.innerHTML = formatMarkdown(content);
  elements.chatHistory.appendChild(bubble);
  elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
}

function updateSuggestions(suggestions) {
  elements.chatSuggestions.innerHTML = suggestions.map(s => `
    <button class="suggestion-chip" data-prompt="${s}">${s}</button>
  `).join('');
}

// ─── Helpers ─────────────────────────────────────────────────────

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code style="background:rgba(255,255,255,0.1); padding:2px 4px; border-radius:4px; font-family:var(--font-mono); font-size:0.8rem;">$1</code>')
    .replace(/\n/g, '<br>');
}
