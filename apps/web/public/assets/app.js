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
  let deploymentStatus = null;

  const locale = (navigator.language || navigator.userLanguage || "en").toLowerCase().startsWith("es") ? "es" : "en";
  const translations = {
    en: {
      pageSubtitle: "Conversational chat to define an identity, review the draft, and send it to S1 Image when it is ready.",
      loginTitle: "Internal access",
      loginSubtitle: "Access for internal users managed from Directus.",
      loginButton: "Sign in",
      logoutButton: "Sign out",
      messageLabel: "Message",
      messagePlaceholder: "Example: I want a premium, confident lifestyle identity with less sarcasm and an elegant visual profile.",
      referenceUrlLabel: "Optional face reference URL",
      referenceFileLabel: "Optional reference file",
      sendButton: "Send message",
      handoffButton: "Send to S1 Image",
      inspectionEyebrow: "Inspection",
      draftTitle: "Current draft",
      draftSubtitle: "Status, traceability, and technical payload.",
      detailEmptyState: "This panel fills in as the conversation progresses.",
      operator: "Operator",
      assistant: "Assistant",
      errorLabel: "Error",
      noReference: "No reference",
      name: "Name",
      statusLabels: {
        pending: "pending",
        succeeded: "succeeded",
        failed: "failed",
        ok: "ok",
        error: "error"
      },
      session: "Session",
      user: "User",
      activeReferenceFile: "Active reference: file",
      activeReferenceUrl: "Active reference: URL",
      activeReferenceNone: "Active reference: none.",
      emptyChat: "There are no messages yet. Start by describing the avatar you want to build or refining one already in progress.",
      noData: "No data",
      identity: "Identity",
      contentType: "Content type",
      category: "Commercial category",
      style: "Style",
      archetype: "Archetype",
      tone: "Voice tone",
      readiness: "Draft readiness",
      readyForS1: "Ready for S1",
      yes: "Yes",
      no: "No",
      reference: "Reference",
      turns: "Turns",
      workflow: "Workflow",
      missingComplete: "Still missing",
      traceability: "Traceability",
      manual: "Manual",
      inferred: "Inferred",
      missing: "Missing",
      visualProfile: "Visual profile",
      hair: "Hair",
      eyes: "Eyes",
      bodyType: "Body type",
      conversationContext: "Conversation context",
      noBrief: "No brief accumulated yet.",
      technicalPayload: "Technical payload",
      s1Preview: "S1 handoff preview",
      graphState: "Technical state",
      runtimeStatus: "Runtime deploy status",
      runtimeBackend: "Execution backend",
      runtimeAlignment: "Deploy alignment",
      runtimeLocalFingerprint: "Local fingerprint",
      runtimeRemoteFingerprint: "Remote fingerprint",
      runtimeMessage: "Deploy note",
      validatingCredentials: "Validating credentials...",
      loginFailed: "Could not sign in",
      messageRequired: "Write a message before continuing.",
      updatingDraft: "Updating conversational draft...",
      draftReady: "Draft ready for S1 Image.",
      draftUpdated: "Draft updated. Keep refining it if needed.",
      draftUpdateFailed: "Could not update the draft",
      uploadingReference: "Uploading reference...",
      referenceAvailable: "Reference uploaded and available for handoff.",
      referenceUploadFailed: "Could not upload the reference",
      draftNotReady: "The draft is not ready to send to S1 Image yet.",
      sendingToS1: "Sending to S1 Image...",
      handoffFailed: "Could not send to S1 Image",
      jobCreated: "Job created",
      readFileFailed: "Could not read the file",
      fieldLabels: {
        "identity_core.fictional_age_years": "Fictional age",
        "metadata.category": "Commercial category",
        "metadata.vertical": "Content type",
        "metadata.occupation_or_content_basis": "Profession or content basis",
        "voice_tone": "Voice tone",
        "communication_style.speech_style": "Speech style",
        "visual_profile.eye_color": "Eye color",
        "visual_profile.hair_color": "Hair color",
        "conversation.scene_context": "Main setting or scene"
      }
    },
    es: {
      pageSubtitle: "Chat conversacional para definir identidad, revisar el draft y enviarlo a S1 Image cuando este listo.",
      loginTitle: "Ingreso interno",
      loginSubtitle: "Acceso para usuarios internos administrados desde Directus.",
      loginButton: "Ingresar",
      logoutButton: "Salir",
      messageLabel: "Mensaje",
      messagePlaceholder: "Ejemplo: Quiero una identidad premium, segura, lifestyle, con menos sarcasmo y un perfil visual elegante.",
      referenceUrlLabel: "URL de referencia facial opcional",
      referenceFileLabel: "Archivo de referencia opcional",
      sendButton: "Enviar mensaje",
      handoffButton: "Enviar a S1 Image",
      inspectionEyebrow: "Inspeccion",
      draftTitle: "Draft actual",
      draftSubtitle: "Estado, trazabilidad y payload tecnico.",
      detailEmptyState: "El panel se llena a medida que avanza la conversacion.",
      operator: "Operador",
      assistant: "Asistente",
      errorLabel: "Error",
      noReference: "Sin referencia",
      name: "Nombre",
      statusLabels: {
        pending: "pendiente",
        succeeded: "listo",
        failed: "fallido",
        ok: "ok",
        error: "error"
      },
      session: "Sesion",
      user: "Usuario",
      activeReferenceFile: "Referencia activa: archivo",
      activeReferenceUrl: "Referencia activa: URL",
      activeReferenceNone: "Referencia activa: sin referencia.",
      emptyChat: "Todavia no hay mensajes. Empeza explicando el avatar que queres construir o refinando uno ya iniciado.",
      noData: "Sin datos",
      identity: "Identidad",
      contentType: "Tipo de contenido",
      category: "Categoria comercial",
      style: "Estilo",
      archetype: "Arquetipo",
      tone: "Tono de voz",
      readiness: "Estado de la ficha",
      readyForS1: "Listo para S1",
      yes: "Si",
      no: "No",
      reference: "Referencia",
      turns: "Turnos",
      workflow: "Flujo",
      missingComplete: "Falta completar",
      traceability: "Trazabilidad",
      manual: "Manuales",
      inferred: "Inferidos",
      missing: "Faltantes",
      visualProfile: "Perfil visual",
      hair: "Pelo",
      eyes: "Ojos",
      bodyType: "Tipo de cuerpo",
      conversationContext: "Contexto conversacional",
      noBrief: "Sin brief acumulado todavia.",
      technicalPayload: "Payload tecnico",
      s1Preview: "Vista previa del envio a S1",
      graphState: "Estado tecnico",
      runtimeStatus: "Estado de deploy del runtime",
      runtimeBackend: "Backend de ejecucion",
      runtimeAlignment: "Alineacion de deploy",
      runtimeLocalFingerprint: "Fingerprint local",
      runtimeRemoteFingerprint: "Fingerprint remoto",
      runtimeMessage: "Nota de deploy",
      validatingCredentials: "Validando credenciales...",
      loginFailed: "No se pudo iniciar sesion",
      messageRequired: "Escribi un mensaje antes de continuar.",
      updatingDraft: "Actualizando draft conversacional...",
      draftReady: "Draft listo para S1 Image.",
      draftUpdated: "Draft actualizado. Segui ajustando si hace falta.",
      draftUpdateFailed: "No se pudo actualizar el draft",
      uploadingReference: "Subiendo referencia...",
      referenceAvailable: "Referencia subida y disponible para el handoff.",
      referenceUploadFailed: "No se pudo subir la referencia",
      draftNotReady: "El draft todavia no esta listo para enviar a S1 Image.",
      sendingToS1: "Enviando a S1 Image...",
      handoffFailed: "No se pudo enviar a S1 Image",
      jobCreated: "Job creado",
      readFileFailed: "No se pudo leer el archivo",
      fieldLabels: {
        "identity_core.fictional_age_years": "Edad ficticia",
        "metadata.category": "Categoria comercial",
        "metadata.vertical": "Tipo de contenido",
        "metadata.occupation_or_content_basis": "Profesion o base de contenido",
        "voice_tone": "Tono de voz",
        "communication_style.speech_style": "Estilo de habla",
        "visual_profile.eye_color": "Color de ojos",
        "visual_profile.hair_color": "Color de pelo",
        "conversation.scene_context": "Contexto o escena principal"
      }
    }
  };
  const t = translations[locale];

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
    sessionMeta.textContent = isAuthenticated() ? `${t.session}: ${sessionId}` : "";
    userMeta.textContent = config.user && config.user.display_name ? `${t.user}: ${config.user.display_name}` : "";
  }

  function currentReferenceLabel() {
    if (uploadedReference && uploadedReference.source === "file") {
      return `${t.activeReferenceFile} ${uploadedReference.filename || uploadedReference.label}.`;
    }
    const url = referenceUrlInput.value.trim();
    if (url) {
      return `${t.activeReferenceUrl} ${url}.`;
    }
    return t.activeReferenceNone;
  }

  function updateReferenceMeta() {
    referenceMeta.textContent = currentReferenceLabel();
  }

  function formatFieldLabel(value) {
    return t.fieldLabels[value] || value;
  }

  function applyStaticTranslations() {
    document.documentElement.lang = locale;
    chatLog.innerHTML = `<div class="empty-state">${escapeHtml(t.emptyChat)}</div>`;
    document.getElementById("pageSubtitle").textContent = t.pageSubtitle;
    document.getElementById("loginTitle").textContent = t.loginTitle;
    document.getElementById("loginSubtitle").textContent = t.loginSubtitle;
    document.getElementById("loginButton").textContent = t.loginButton;
    document.getElementById("logoutButton").textContent = t.logoutButton;
    document.getElementById("messageLabel").textContent = t.messageLabel;
    messageInput.placeholder = t.messagePlaceholder;
    document.getElementById("referenceUrlLabel").textContent = t.referenceUrlLabel;
    document.getElementById("referenceFileLabel").textContent = t.referenceFileLabel;
    document.getElementById("sendButton").textContent = t.sendButton;
    document.getElementById("handoffButton").textContent = t.handoffButton;
    document.getElementById("inspectionEyebrow").textContent = t.inspectionEyebrow;
    document.getElementById("draftTitle").textContent = t.draftTitle;
    document.getElementById("draftSubtitle").textContent = t.draftSubtitle;
    document.getElementById("detailEmptyState").textContent = t.detailEmptyState;
  }

  function renderHistory(history) {
    if (!history || !history.length) {
      chatLog.innerHTML = `<div class="empty-state">${escapeHtml(t.emptyChat)}</div>`;
      chatLog.scrollTop = chatLog.scrollHeight;
      return;
    }
    chatLog.innerHTML = history
      .map((entry) => {
        const statusKey = String(entry.status || "pending");
        const status = escapeHtml(statusKey);
        const statusLabel = escapeHtml(t.statusLabels[statusKey] || statusKey);
        const assistantStatusKey = entry.error ? "error" : "ok";
        const assistantStatusLabel = escapeHtml(t.statusLabels[assistantStatusKey] || assistantStatusKey);
        return `
          <article class="turn">
            <div class="bubble user">
              <div class="bubble-header">
                <span>${escapeHtml(t.operator)}</span>
                <span class="status ${status}">${statusLabel}</span>
              </div>
              <div>${escapeHtml(entry.user_message || "")}</div>
            </div>
            <div class="bubble assistant">
              <div class="bubble-header">
                <span>${escapeHtml(t.assistant)}</span>
                <span>${assistantStatusLabel}</span>
              </div>
              <div class="bubble-copy assistant-copy">${escapeHtml(entry.assistant_message || "")}</div>
              ${entry.error ? `<p class="meta">${escapeHtml(t.errorLabel)}: ${escapeHtml(entry.error)}</p>` : ""}
            </div>
          </article>
        `;
      })
      .join("");
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function pillList(items) {
    if (!items || !items.length) {
      return `<div class="meta">${escapeHtml(t.noData)}</div>`;
    }
    return `<div class="pill-list">${items.map((item) => `<span class="pill">${escapeHtml(formatFieldLabel(item))}</span>`).join("")}</div>`;
  }

  function renderPanel(panel) {
    lastPanel = panel;
    if (!panel) {
      detailBody.innerHTML = `<div class="empty-state">${escapeHtml(t.detailEmptyState)}</div>`;
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
    const missingLabels = traceability.missing_field_labels || readiness.missing_field_labels || traceability.missing_fields || [];
    const localFingerprint = deploymentStatus && deploymentStatus.deployment_fingerprint
      ? deploymentStatus.deployment_fingerprint
      : null;
    const remoteFingerprint = deploymentStatus && deploymentStatus.remote_deployment_fingerprint
      ? deploymentStatus.remote_deployment_fingerprint
      : null;
    const backend = deploymentStatus && deploymentStatus.deployment_fingerprint
      ? deploymentStatus.deployment_fingerprint.execution_backend
      : config.executionBackend || "unknown";
    const alignment = deploymentStatus && deploymentStatus.deployment_alignment
      ? deploymentStatus.deployment_alignment
      : "unknown";
    const alignmentMessage = deploymentStatus && deploymentStatus.deployment_alignment_message
      ? deploymentStatus.deployment_alignment_message
      : "Deployment fingerprint is not available yet.";

    detailBody.innerHTML = `
      <section class="info-card">
        <h3>${escapeHtml(t.identity)}</h3>
        <dl class="kv">
          <div><dt>${escapeHtml(t.name)}</dt><dd>${escapeHtml(identity.display_name || "-")}</dd></div>
          <div><dt>${escapeHtml(t.contentType)}</dt><dd>${escapeHtml(identity.vertical || "-")}</dd></div>
          <div><dt>${escapeHtml(t.category)}</dt><dd>${escapeHtml(identity.category || "-")}</dd></div>
          <div><dt>${escapeHtml(t.style)}</dt><dd>${escapeHtml(identity.style || "-")}</dd></div>
          <div><dt>${escapeHtml(t.archetype)}</dt><dd>${escapeHtml(identity.archetype || "-")}</dd></div>
          <div><dt>${escapeHtml(t.tone)}</dt><dd>${escapeHtml(identity.voice_tone || "-")}</dd></div>
        </dl>
      </section>

      <section class="info-card">
        <h3>${escapeHtml(t.readiness)}</h3>
        <dl class="kv">
          <div><dt>${escapeHtml(t.readyForS1)}</dt><dd>${readiness.can_handoff ? t.yes : t.no}</dd></div>
          <div><dt>${escapeHtml(t.reference)}</dt><dd>${escapeHtml(reference.source || "none")}</dd></div>
          <div><dt>${escapeHtml(t.turns)}</dt><dd>${escapeHtml(conversation.turn_count || 0)}</dd></div>
          <div><dt>${escapeHtml(t.workflow)}</dt><dd>${escapeHtml(copilot.workflow_id || "-")}</dd></div>
        </dl>
        <p class="meta">${escapeHtml(reference.label || t.noReference)}</p>
        ${missingLabels.length ? `<p class="meta">${escapeHtml(t.missingComplete)}: ${escapeHtml(missingLabels.map(formatFieldLabel).join(", "))}</p>` : ""}
      </section>

      <section class="info-card">
        <h3>${escapeHtml(t.traceability)}</h3>
        <strong class="meta">${escapeHtml(t.manual)}</strong>
        ${pillList(traceability.manual_fields || [])}
        <strong class="meta">${escapeHtml(t.inferred)}</strong>
        ${pillList(traceability.inferred_fields || [])}
        <strong class="meta">${escapeHtml(t.missing)}</strong>
        ${pillList(missingLabels)}
      </section>

      <section class="info-card">
        <h3>${escapeHtml(t.visualProfile)}</h3>
        <dl class="kv">
          <div><dt>${escapeHtml(t.hair)}</dt><dd>${escapeHtml(visual.hair || "-")}</dd></div>
          <div><dt>${escapeHtml(t.eyes)}</dt><dd>${escapeHtml(visual.eyes || "-")}</dd></div>
          <div><dt>${escapeHtml(t.bodyType)}</dt><dd>${escapeHtml(visual.body_type || "-")}</dd></div>
        </dl>
        ${pillList([...(visual.must_haves || []), ...(visual.wardrobe_styles || [])])}
      </section>

      <section class="info-card">
        <h3>${escapeHtml(t.conversationContext)}</h3>
        <p class="meta">${escapeHtml(conversation.operator_brief || t.noBrief)}</p>
      </section>

      <section class="info-card">
        <h3>${escapeHtml(t.runtimeStatus)}</h3>
        <dl class="kv">
          <div><dt>${escapeHtml(t.runtimeBackend)}</dt><dd>${escapeHtml(backend || "-")}</dd></div>
          <div><dt>${escapeHtml(t.runtimeAlignment)}</dt><dd>${escapeHtml(alignment || "unknown")}</dd></div>
        </dl>
        <p class="meta">${escapeHtml(alignmentMessage)}</p>
        <details>
          <summary>${escapeHtml(t.runtimeLocalFingerprint)}</summary>
          <pre>${escapeHtml(JSON.stringify(localFingerprint || {}, null, 2))}</pre>
        </details>
        <details>
          <summary>${escapeHtml(t.runtimeRemoteFingerprint)}</summary>
          <pre>${escapeHtml(JSON.stringify(remoteFingerprint || {}, null, 2))}</pre>
        </details>
      </section>

      <section class="info-card">
        <h3>${escapeHtml(t.technicalPayload)}</h3>
        <details open>
          <summary>${escapeHtml(t.s1Preview)}</summary>
          <pre>${escapeHtml(JSON.stringify(panel.s1_payload_preview || {}, null, 2))}</pre>
        </details>
        <details>
          <summary>${escapeHtml(t.graphState)}</summary>
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

  async function loadDeploymentStatus(options = {}) {
    if (!config.healthcheckEndpoint || !isAuthenticated()) {
      return;
    }
    const timeoutMs = Number(options.timeoutMs || 4000);
    const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    const timeoutId = controller
      ? setTimeout(() => controller.abort(), timeoutMs)
      : null;
    try {
      const response = await fetch(config.healthcheckEndpoint, {
        method: "GET",
        credentials: "same-origin",
        signal: controller ? controller.signal : undefined
      });
      deploymentStatus = await response.json().catch(() => null);
      if (lastPanel) {
        renderPanel(lastPanel);
      }
    } catch (_error) {
      deploymentStatus = {
        deployment_alignment: "unknown",
        deployment_alignment_message: "Could not load runtime healthcheck.",
        deployment_fingerprint: null,
        remote_deployment_fingerprint: null
      };
      if (lastPanel) {
        renderPanel(lastPanel);
      }
    } finally {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    }
  }

  async function handleLogin(event) {
    event.preventDefault();
    loginFeedback.textContent = t.validatingCredentials;
    try {
      await postJson(config.loginEndpoint, {
        email: loginEmail.value.trim(),
        password: loginPassword.value
      });
      window.location.href = "/app";
    } catch (error) {
      loginFeedback.textContent = `${t.loginFailed}: ${error.message}`;
    }
  }

  async function handleLogout() {
    try {
      await postJson(config.logoutEndpoint, {});
    } finally {
      localStorage.removeItem(sessionStorageKey);
      window.location.href = "/login";
    }
  }

  async function handleSend() {
    const message = messageInput.value.trim();
    if (!message) {
      feedback.textContent = t.messageRequired;
      return;
    }
    feedback.textContent = t.updatingDraft;
    sendButton.disabled = true;
    try {
      const payload = await postJson(config.chatEndpoint, {
        session_id: sessionId,
        message,
        reference_face_image_url: referenceUrlInput.value.trim(),
        locale
      });
      renderHistory(payload.history || [payload.chat_entry]);
      renderPanel(payload.panel || null);
      messageInput.value = "";
      feedback.textContent = payload.can_handoff
        ? t.draftReady
        : t.draftUpdated;
    } catch (error) {
      feedback.textContent = `${t.draftUpdateFailed}: ${error.message}`;
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
    feedback.textContent = t.uploadingReference;
    try {
      const dataBase64 = await readFileAsBase64(file);
      const payload = await postJson(config.referenceUploadEndpoint, {
        session_id: sessionId,
        filename: file.name,
        content_type: file.type || "application/octet-stream",
        data_base64: dataBase64,
        locale
      });
      uploadedReference = payload.reference || null;
      updateReferenceMeta();
      if (lastPanel) {
        lastPanel.reference_face = payload.reference || lastPanel.reference_face;
        renderPanel(lastPanel);
      }
      feedback.textContent = t.referenceAvailable;
    } catch (error) {
      feedback.textContent = `${t.referenceUploadFailed}: ${error.message}`;
    }
  }

  async function handleHandoff() {
    if (!lastPanel || !lastPanel.readiness || !lastPanel.readiness.can_handoff) {
      feedback.textContent = t.draftNotReady;
      return;
    }
    feedback.textContent = t.sendingToS1;
    handoffButton.disabled = true;
    try {
      const payload = await postJson(config.handoffEndpoint, {
        session_id: sessionId,
        reference_face_image_url: referenceUrlInput.value.trim(),
        locale
      });
      renderPanel(payload.panel || null);
      feedback.textContent = `${t.jobCreated}: ${payload.handoff.job.job_id}`;
      Promise.resolve(loadDeploymentStatus()).catch(() => {});
    } catch (error) {
      feedback.textContent = `${t.handoffFailed}: ${error.message}`;
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
      reader.onerror = () => reject(new Error(t.readFileFailed));
      reader.readAsDataURL(file);
    });
  }

  loginForm.addEventListener("submit", handleLogin);
  logoutButton.addEventListener("click", handleLogout);
  sendButton.addEventListener("click", handleSend);
  handoffButton.addEventListener("click", handleHandoff);
  referenceFileInput.addEventListener("change", handleReferenceUpload);
  referenceUrlInput.addEventListener("input", updateReferenceMeta);

  applyStaticTranslations();
  setViewMode();
  updateReferenceMeta();
  loadDeploymentStatus();
})();
