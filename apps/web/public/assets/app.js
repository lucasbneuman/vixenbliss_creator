(function () {
  const config = window.VB_WEB_CONFIG || {};
  const sessionStorageKey = config.sessionStorageKey || "vb-web-session";
  const sessionId = localStorage.getItem(sessionStorageKey) || `web-${buildSessionId()}`;
  localStorage.setItem(sessionStorageKey, sessionId);

  const loginView = document.getElementById("loginView");
  const appView = document.getElementById("appView");
  const loginForm = document.getElementById("loginForm");
  const loginEmail = document.getElementById("loginEmail");
  const loginPassword = document.getElementById("loginPassword");
  const loginFeedback = document.getElementById("loginFeedback");
  const logoutButton = document.getElementById("logoutButton");
  const sessionMeta = document.getElementById("sessionMeta");
  const userMeta = document.getElementById("userMeta");
  const chatLog = document.getElementById("chatLog");
  const detailBody = document.getElementById("detailBody");
  const messageInput = document.getElementById("messageInput");
  const referenceUrlInput = document.getElementById("referenceUrlInput");
  const referenceFileInput = document.getElementById("referenceFileInput");
  const referenceMeta = document.getElementById("referenceMeta");
  const feedback = document.getElementById("feedback");
  const sendButton = document.getElementById("sendButton");
  const handoffButton = document.getElementById("handoffButton");

  let uploadedReference = null;
  let lastPanel = null;

  referenceUrlInput.value = config.defaultReferenceFaceImageUrl || "";

  function buildSessionId() {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      return crypto.randomUUID();
    }
    return `${Date.now().toString(16)}-${Math.random().toString(16).slice(2, 10)}`;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function isAuthenticated() {
    return Boolean(config.authenticated);
  }

  function setViewMode() {
    loginView.hidden = isAuthenticated();
    appView.hidden = !isAuthenticated();
    sessionMeta.textContent = isAuthenticated() ? `Sesion: ${sessionId}` : "";
    userMeta.textContent = config.user && config.user.display_name ? `Usuario: ${config.user.display_name}` : "";
  }

  function currentReferenceLabel() {
    if (uploadedReference && uploadedReference.source === "file") {
      return `Referencia activa: archivo ${uploadedReference.filename || uploadedReference.label}.`;
    }
    const url = referenceUrlInput.value.trim();
    if (url) {
      return `Referencia activa: URL ${url}.`;
    }
    return "Referencia activa: sin referencia.";
  }

  function updateReferenceMeta() {
    referenceMeta.textContent = currentReferenceLabel();
  }

  function renderHistory(history) {
    if (!history || !history.length) {
      chatLog.innerHTML = '<div class="empty-state">Todavia no hay mensajes. Empeza explicando el avatar que queres construir o refinando uno ya iniciado.</div>';
      return;
    }
    chatLog.innerHTML = history
      .map((entry) => {
        const status = escapeHtml(entry.status || "pending");
        return `
          <article class="turn">
            <div class="bubble user">
              <div class="bubble-header">
                <span>Operador</span>
                <span class="status ${status}">${status}</span>
              </div>
              <div>${escapeHtml(entry.user_message || "")}</div>
            </div>
            <div class="bubble assistant">
              <div class="bubble-header">
                <span>Asistente</span>
                <span>${entry.error ? "error" : "ok"}</span>
              </div>
              <div>${escapeHtml(entry.assistant_message || "")}</div>
              ${entry.error ? `<p class="meta">Error: ${escapeHtml(entry.error)}</p>` : ""}
            </div>
          </article>
        `;
      })
      .join("");
  }

  function pillList(items) {
    if (!items || !items.length) {
      return '<div class="meta">Sin datos</div>';
    }
    return `<div class="pill-list">${items.map((item) => `<span class="pill">${escapeHtml(item)}</span>`).join("")}</div>`;
  }

  function renderPanel(panel) {
    lastPanel = panel;
    if (!panel) {
      detailBody.innerHTML = '<div class="empty-state">El panel se llena a medida que avanza la conversacion.</div>';
      handoffButton.disabled = true;
      return;
    }

    const identity = panel.identity || {};
    const traceability = panel.traceability || {};
    const visual = panel.visual_profile || {};
    const readiness = panel.readiness || {};
    const reference = panel.reference_face || {};
    const conversation = panel.conversation || {};
    const copilot = panel.copilot || {};

    detailBody.innerHTML = `
      <section class="info-card">
        <h3>Identidad</h3>
        <dl class="kv">
          <div><dt>Nombre</dt><dd>${escapeHtml(identity.display_name || "-")}</dd></div>
          <div><dt>Vertical</dt><dd>${escapeHtml(identity.vertical || "-")}</dd></div>
          <div><dt>Categoria</dt><dd>${escapeHtml(identity.category || "-")}</dd></div>
          <div><dt>Style</dt><dd>${escapeHtml(identity.style || "-")}</dd></div>
          <div><dt>Arquetipo</dt><dd>${escapeHtml(identity.archetype || "-")}</dd></div>
          <div><dt>Tono</dt><dd>${escapeHtml(identity.voice_tone || "-")}</dd></div>
        </dl>
      </section>

      <section class="info-card">
        <h3>Readiness</h3>
        <dl class="kv">
          <div><dt>Listo para S1</dt><dd>${readiness.can_handoff ? "Si" : "No"}</dd></div>
          <div><dt>Referencia</dt><dd>${escapeHtml(reference.source || "none")}</dd></div>
          <div><dt>Turnos</dt><dd>${escapeHtml(conversation.turn_count || 0)}</dd></div>
          <div><dt>Workflow</dt><dd>${escapeHtml(copilot.workflow_id || "-")}</dd></div>
        </dl>
        <p class="meta">${escapeHtml(reference.label || "Sin referencia")}</p>
      </section>

      <section class="info-card">
        <h3>Trazabilidad</h3>
        <strong class="meta">Manuales</strong>
        ${pillList(traceability.manual_fields || [])}
        <strong class="meta">Inferidos</strong>
        ${pillList(traceability.inferred_fields || [])}
        <strong class="meta">Faltantes</strong>
        ${pillList(traceability.missing_fields || [])}
      </section>

      <section class="info-card">
        <h3>Perfil visual</h3>
        <dl class="kv">
          <div><dt>Hair</dt><dd>${escapeHtml(visual.hair || "-")}</dd></div>
          <div><dt>Eyes</dt><dd>${escapeHtml(visual.eyes || "-")}</dd></div>
          <div><dt>Body type</dt><dd>${escapeHtml(visual.body_type || "-")}</dd></div>
        </dl>
        ${pillList([...(visual.must_haves || []), ...(visual.wardrobe_styles || [])])}
      </section>

      <section class="info-card">
        <h3>Contexto conversacional</h3>
        <p class="meta">${escapeHtml(conversation.operator_brief || "Sin brief acumulado todavia.")}</p>
      </section>

      <section class="info-card">
        <h3>Payload tecnico</h3>
        <details open>
          <summary>S1 payload preview</summary>
          <pre>${escapeHtml(JSON.stringify(panel.s1_payload_preview || {}, null, 2))}</pre>
        </details>
        <details>
          <summary>GraphState</summary>
          <pre>${escapeHtml(JSON.stringify(panel.graph_state_json || {}, null, 2))}</pre>
        </details>
      </section>
    `;

    handoffButton.disabled = !Boolean(readiness.can_handoff);
  }

  async function postJson(url, payload) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "same-origin"
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(body.detail || "Request failed");
    }
    return body;
  }

  async function handleLogin(event) {
    event.preventDefault();
    loginFeedback.textContent = "Validando credenciales...";
    try {
      await postJson(config.loginEndpoint, {
        email: loginEmail.value.trim(),
        password: loginPassword.value
      });
      window.location.href = "/app";
    } catch (error) {
      loginFeedback.textContent = `No se pudo iniciar sesion: ${error.message}`;
    }
  }

  async function handleLogout() {
    try {
      await postJson(config.logoutEndpoint, {});
    } finally {
      window.location.href = "/login";
    }
  }

  async function handleSend() {
    const message = messageInput.value.trim();
    if (!message) {
      feedback.textContent = "Escribi un mensaje antes de continuar.";
      return;
    }
    feedback.textContent = "Actualizando draft conversacional...";
    sendButton.disabled = true;
    try {
      const payload = await postJson(config.chatEndpoint, {
        session_id: sessionId,
        message,
        reference_face_image_url: referenceUrlInput.value.trim()
      });
      renderHistory(payload.history || [payload.chat_entry]);
      renderPanel(payload.panel || null);
      messageInput.value = "";
      feedback.textContent = payload.can_handoff
        ? "Draft listo para S1 Image."
        : "Draft actualizado. Segui ajustando si hace falta.";
    } catch (error) {
      feedback.textContent = `No se pudo actualizar el draft: ${error.message}`;
    } finally {
      sendButton.disabled = false;
    }
  }

  async function handleReferenceUpload(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) {
      uploadedReference = null;
      updateReferenceMeta();
      return;
    }
    feedback.textContent = "Subiendo referencia...";
    try {
      const dataBase64 = await readFileAsBase64(file);
      const payload = await postJson(config.referenceUploadEndpoint, {
        session_id: sessionId,
        filename: file.name,
        content_type: file.type || "application/octet-stream",
        data_base64: dataBase64
      });
      uploadedReference = payload.reference || null;
      updateReferenceMeta();
      if (lastPanel) {
        lastPanel.reference_face = payload.reference || lastPanel.reference_face;
        renderPanel(lastPanel);
      }
      feedback.textContent = "Referencia subida y disponible para el handoff.";
    } catch (error) {
      feedback.textContent = `No se pudo subir la referencia: ${error.message}`;
    }
  }

  async function handleHandoff() {
    if (!lastPanel || !lastPanel.readiness || !lastPanel.readiness.can_handoff) {
      feedback.textContent = "El draft todavia no esta listo para enviar a S1 Image.";
      return;
    }
    feedback.textContent = "Enviando a S1 Image...";
    handoffButton.disabled = true;
    try {
      const payload = await postJson(config.handoffEndpoint, {
        session_id: sessionId,
        reference_face_image_url: referenceUrlInput.value.trim()
      });
      renderPanel(payload.panel || null);
      feedback.textContent = `Job creado: ${payload.handoff.job.job_id}`;
    } catch (error) {
      feedback.textContent = `No se pudo enviar a S1 Image: ${error.message}`;
      handoffButton.disabled = !lastPanel || !lastPanel.readiness || !lastPanel.readiness.can_handoff;
    }
  }

  function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = String(reader.result || "");
        const marker = "base64,";
        const index = result.indexOf(marker);
        resolve(index >= 0 ? result.slice(index + marker.length) : result);
      };
      reader.onerror = () => reject(new Error("No se pudo leer el archivo"));
      reader.readAsDataURL(file);
    });
  }

  loginForm.addEventListener("submit", handleLogin);
  logoutButton.addEventListener("click", handleLogout);
  sendButton.addEventListener("click", handleSend);
  handoffButton.addEventListener("click", handleHandoff);
  referenceFileInput.addEventListener("change", handleReferenceUpload);
  referenceUrlInput.addEventListener("input", updateReferenceMeta);

  setViewMode();
  updateReferenceMeta();
})();
