(function () {
  const config = window.VB_WEB_CONFIG || {};
  const sessionStorageKey = config.sessionStorageKey || "vb-web-session";
  const sessionId = localStorage.getItem(sessionStorageKey) || `web-${crypto.randomUUID()}`;
  localStorage.setItem(sessionStorageKey, sessionId);

  const chatLog = document.getElementById("chatLog");
  const detailBody = document.getElementById("detailBody");
  const feedback = document.getElementById("feedback");
  const runButton = document.getElementById("runButton");
  const handoffButton = document.getElementById("handoffButton");
  const ideaInput = document.getElementById("ideaInput");
  const referenceInput = document.getElementById("referenceInput");
  const sessionMeta = document.getElementById("sessionMeta");

  let lastPanel = null;

  referenceInput.value = config.defaultReferenceFaceImageUrl || "";
  sessionMeta.textContent = `Sesión: ${sessionId}`;

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function createPills(items) {
    if (!items || !items.length) {
      return '<div class="meta">Sin datos</div>';
    }
    return `<div class="pill-list">${items.map((item) => `<span class="pill">${escapeHtml(item)}</span>`).join("")}</div>`;
  }

  function renderChatEntry(entry) {
    if (!entry) {
      return;
    }
    if (chatLog.querySelector(".empty-state")) {
      chatLog.innerHTML = "";
    }
    const userNode = document.createElement("article");
    userNode.className = "bubble user";
    userNode.innerHTML = `
      <div class="bubble-header">
        <span>Prompt</span>
        <span class="status ${escapeHtml(entry.status)}">${escapeHtml(entry.status)}</span>
      </div>
      <div>${escapeHtml(entry.user_message)}</div>
    `;
    const replyNode = document.createElement("article");
    replyNode.className = "bubble";
    replyNode.innerHTML = `
      <div class="bubble-header">
        <span>Resultado</span>
        <span>${entry.error ? "con error" : "ok"}</span>
      </div>
      <div>${escapeHtml(entry.assistant_message || "")}</div>
      ${entry.error ? `<p class="meta">Error: ${escapeHtml(entry.error)}</p>` : ""}
    `;
    chatLog.prepend(replyNode);
    chatLog.prepend(userNode);
  }

  function renderPanel(panel, handoff) {
    lastPanel = panel;
    if (!panel) {
      detailBody.innerHTML = '<div class="empty-state">El panel se completa después de la primera ejecución.</div>';
      handoffButton.disabled = true;
      return;
    }
    const identity = panel.identity || {};
    const visual = panel.visual_profile || {};
    const traceability = panel.traceability || {};
    const copilot = panel.copilot || {};
    const personalityPills = Object.entries(panel.personality_axes || {}).map(([key, value]) => `${key}=${value}`);
    const visualPills = [...(visual.must_haves || []), ...(visual.wardrobe_styles || [])];
    const handoffBlock = handoff
      ? `
        <div class="meta">
          Job creado: <strong>${escapeHtml(handoff.job.job_id)}</strong>
          ${handoff.job.result_url ? ` | <a href="${escapeHtml(handoff.job.result_url)}" target="_blank" rel="noreferrer">Abrir result_url</a>` : ""}
        </div>
      `
      : "";

    detailBody.innerHTML = `
      <div class="grid">
        <section class="card">
          <h3>Identidad base</h3>
          <dl class="kv">
            <div><dt>Nombre</dt><dd>${escapeHtml(identity.display_name || "-")}</dd></div>
            <div><dt>Vertical</dt><dd>${escapeHtml(identity.vertical || "-")}</dd></div>
            <div><dt>Categoría</dt><dd>${escapeHtml(identity.category || "-")}</dd></div>
            <div><dt>Style</dt><dd>${escapeHtml(identity.style || "-")}</dd></div>
            <div><dt>Arquetipo</dt><dd>${escapeHtml(identity.archetype || "-")}</dd></div>
          </dl>
        </section>
        <section class="card">
          <h3>Tono y comportamiento</h3>
          <dl class="kv">
            <div><dt>Voice tone</dt><dd>${escapeHtml(identity.voice_tone || "-")}</dd></div>
            <div><dt>Speech style</dt><dd>${escapeHtml(identity.speech_style || "-")}</dd></div>
          </dl>
          ${createPills(personalityPills)}
        </section>
      </div>
      <section class="section">
        <h3>Perfil visual</h3>
        <dl class="kv">
          <div><dt>Arquetipo visual</dt><dd>${escapeHtml(visual.archetype || "-")}</dd></div>
          <div><dt>Hair</dt><dd>${escapeHtml(visual.hair || "-")}</dd></div>
          <div><dt>Eyes</dt><dd>${escapeHtml(visual.eyes || "-")}</dd></div>
          <div><dt>Body type</dt><dd>${escapeHtml(visual.body_type || "-")}</dd></div>
        </dl>
        ${createPills(visualPills)}
      </section>
      <section class="section">
        <h3>Trazabilidad</h3>
        <p>Campos manuales e inferidos detectados por LangGraph para este draft.</p>
        <strong class="meta">Manuales</strong>
        ${createPills(traceability.manual_fields || [])}
        <strong class="meta">Inferidos</strong>
        ${createPills(traceability.inferred_fields || [])}
        ${(traceability.missing_fields || []).length ? `<strong class="meta">Faltantes</strong>${createPills(traceability.missing_fields || [])}` : ""}
      </section>
      <section class="section">
        <h3>Recomendación técnica</h3>
        <dl class="kv">
          <div><dt>Workflow</dt><dd>${escapeHtml(copilot.workflow_id || "-")}</dd></div>
          <div><dt>Version</dt><dd>${escapeHtml(copilot.workflow_version || "-")}</dd></div>
          <div><dt>Base model</dt><dd>${escapeHtml(copilot.base_model_id || "-")}</dd></div>
          <div><dt>Registry</dt><dd>${escapeHtml(copilot.registry_source || "-")}</dd></div>
        </dl>
        <p class="meta">${escapeHtml(copilot.reasoning_summary || "Sin reasoning_summary")}</p>
        <details>
          <summary>Prompt y negative prompt</summary>
          <pre>${escapeHtml(JSON.stringify({
            prompt_template: copilot.prompt_template,
            negative_prompt: copilot.negative_prompt,
            risk_flags: copilot.risk_flags
          }, null, 2))}</pre>
        </details>
      </section>
      <section class="section">
        <h3>Payload para S1</h3>
        <p>Preview del contexto de identidad y del job que se envía al runtime de S1 Image.</p>
        <details open>
          <summary>Identity context</summary>
          <pre>${escapeHtml(JSON.stringify(panel.identity_context || {}, null, 2))}</pre>
        </details>
        <details>
          <summary>Job payload</summary>
          <pre>${escapeHtml(JSON.stringify(panel.s1_payload_preview || {}, null, 2))}</pre>
        </details>
        ${handoffBlock}
      </section>
      <section class="section">
        <h3>JSON de debug</h3>
        <details>
          <summary>GraphState</summary>
          <pre>${escapeHtml(JSON.stringify(panel.graph_state_json || {}, null, 2))}</pre>
        </details>
      </section>
    `;
    handoffButton.disabled = !Boolean(panel.s1_payload_preview && Object.keys(panel.s1_payload_preview).length);
  }

  async function runLangGraph() {
    const idea = ideaInput.value.trim();
    if (!idea) {
      feedback.textContent = "Necesitás escribir una idea antes de correr LangGraph.";
      return;
    }
    feedback.textContent = "Ejecutando LangGraph...";
    runButton.disabled = true;
    handoffButton.disabled = true;
    try {
      const response = await fetch(config.langgraphEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, idea })
      });
      const payload = await response.json();
      renderChatEntry(payload.chat_entry);
      renderPanel(payload.panel, null);
      handoffButton.disabled = !payload.can_handoff;
      feedback.textContent = payload.can_handoff
        ? "LangGraph listo para handoff."
        : "LangGraph respondió, pero no quedó listo para S1.";
    } catch (error) {
      feedback.textContent = `No se pudo ejecutar LangGraph: ${error.message}`;
    } finally {
      runButton.disabled = false;
    }
  }

  async function runHandoff() {
    feedback.textContent = "Disparando handoff a S1 Image...";
    handoffButton.disabled = true;
    try {
      const response = await fetch(config.handoffEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          reference_face_image_url: referenceInput.value.trim()
        })
      });
      if (!response.ok) {
        const failure = await response.json();
        throw new Error(failure.detail || "No se pudo crear el job");
      }
      const payload = await response.json();
      renderPanel(payload.panel, payload.handoff);
      feedback.textContent = `Job creado: ${payload.handoff.job.job_id}`;
    } catch (error) {
      feedback.textContent = `No se pudo disparar S1 Image: ${error.message}`;
      handoffButton.disabled = !lastPanel;
    }
  }

  runButton.addEventListener("click", runLangGraph);
  handoffButton.addEventListener("click", runHandoff);
})();
