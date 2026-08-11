const { entrypoints, storage, shell } = require("uxp");

let app;
let indesign;
try {
  indesign = require("indesign");
  app = indesign.app;
} catch (error) {
  app = null;
  indesign = null;
}

const state = {
  assets: [],
  authenticated: false,
  userEmail: "",
  startedAt: null,
  timerId: null,
  dark: true,
  uploadedCount: 0,
  duplicateCount: 0,
  uploadErrorCount: 0,
  progressPercent: 0
};

const SUPPORTED_EXTENSIONS = new Set(["JPG", "JPEG", "PNG", "EPS", "AI", "SVG"]);
const PREVIEW_BATCH_SIZE = 2;
const PREVIEW_BATCH_DELAY_MS = 140;
const GENERATED_PREVIEW_BATCH_SIZE = 1;
const GENERATED_PREVIEW_DELAY_MS = 140;
const FIREBASE_PROJECT_ID = "uniasselvi-digital";
const FIREBASE_API_KEY = "AIzaSyBD6TkUg5F_j9C2_VK6pWf-z34Iyszp0LE";
const FIREBASE_STORAGE_BUCKET = "uniasselvi-digital.appspot.com";
const FIRESTORE_COLLECTION_PATH = "acervo-visual-unificado/default/images";
const STORAGE_ROOT = "acervo-visual-unificado";
const AUTH_SERVER_URL = "http://127.0.0.1:5055";
const AUTH_LOGIN_URL = `${AUTH_SERVER_URL}/`;
const OPENAI_MODEL = "gpt-4o-mini";
const OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions";
const AI_METADATA_PROMPT = `
Analise esta imagem e retorne APENAS um JSON valido com os seguintes campos:
{
  "tipo_imagem": "ex: fotografia, ilustracao, vetor, icone, mockup, textura",
  "elementos_visuais": "principais elementos visuais presentes",
  "estilo_tecnica": "ex: realista, abstrato, aquarela, 3D, flat, editorial",
  "formato": "ex: retrato, paisagem, quadrado, horizontal, vertical",
  "cores_predominantes": "3 a 5 cores principais em portugues",
  "area_conhecimento": "ex: educacao, saude, tecnologia, natureza, negocios",
  "caracteristicas": "caracteristicas marcantes e relevantes para busca",
  "palavras_chave_pt": ["palavra1", "palavra2", "palavra3", "palavra4", "palavra5", "palavra6", "palavra7", "palavra8", "palavra9", "palavra10"],
  "palavras_chave_en": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8", "keyword9", "keyword10"],
  "descricao_detalhada": "descricao rica e detalhada em portugues"
}
Inclua EXATAMENTE 10 palavras-chave em portugues e 10 em ingles.
Nao inclua markdown, comentario ou texto fora do JSON.
`;

entrypoints.setup({
  panels: {
    acervoPanel: {
      create(rootNode) {
        initializePanel();
        return Promise.resolve();
      },
      destroy(rootNode) {
        stopTimer();
        return Promise.resolve();
      }
    }
  }
});

function initializePanel() {
  restoreSavedLogin();
  document.body.classList.toggle("dark", state.dark);
  bind("loginButton", "click", loginViaShortcut);
  bind("logoutButton", "click", logout);
  bind("scanButton", "click", scanDocument);
  bind("selectAllButton", "click", () => setAllSelected(true));
  bind("clearSelectionButton", "click", () => setAllSelected(false));
  bind("themeToggle", "click", toggleTheme);
  bind("uploadButton", "click", uploadSelected);

  updateCounters();
  updateAuthUi();
  updateProgress(0);
  if (state.authenticated) {
    log(`Painel carregado. Login recuperado para: ${state.userEmail}`);
    log("Clique em “Varrer documento” para listar os links do InDesign.");
  } else {
    log("Painel carregado. Faça login para liberar a varredura do documento.");
  }

  restoreTokenLoginInBackground();
}

function bind(id, eventName, handler) {
  const el = document.getElementById(id);
  if (el) {
    el.addEventListener(eventName, (event) => {
      if (el.classList && el.classList.contains("disabled")) {
        event.preventDefault();
        return;
      }
      handler(event);
    });
    el.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        el.click();
      }
    });
  }
}

async function scanDocument() {
  if (!state.authenticated) {
    log("Login obrigatório: entre antes de varrer o documento.");
    return;
  }

  resetRun();

  if (!app) {
    log("Erro: API do InDesign não está disponível. Carregue o plug-in dentro do InDesign via UXP Developer Tool.");
    return;
  }

  let doc;
  try {
    doc = app.activeDocument;
  } catch (error) {
    log(`Erro ao acessar documento ativo: ${messageOf(error)}`);
    return;
  }

  if (!doc || !doc.isValid) {
    log("Nenhum documento ativo encontrado. Abra um arquivo .indd e tente novamente.");
    return;
  }

  const docName = safeRead(() => doc.name, "Documento sem nome");
  setText("documentName", docName);
  log(`Documento ativo: ${docName}`);

  const links = toArray(safeRead(() => doc.links, []));
  log(`Links encontrados pelo InDesign: ${formatNumber(links.length)}`);

  const readAssets = links.map((link, index) => readLink(link, index));
  state.assets = readAssets.filter(isSupportedAsset);
  const ignored = readAssets.length - state.assets.length;
  if (ignored > 0) {
    log(`Ignorados ${formatNumber(ignored)} link(s) fora dos formatos do acervo.`);
  }

  await preparePreviewsBeforeShowing();
  renderTable();
  updateCounters();

  const errors = state.assets.filter((asset) => asset.hasError).length;
  if (errors > 0) {
    log(`Varredura concluída com ${formatNumber(errors)} alerta(s)/erro(s).`);
  } else {
    log("Varredura concluída sem erros aparentes.");
  }
  stopTimer();
  updateProgress(100);
}

async function uploadSelected() {
  if (!state.authenticated) {
    log("Login obrigatório antes de enviar.");
    return;
  }

  const selected = state.assets.filter((asset) => asset.selected && !asset.hasError);
  if (!selected.length) {
    log("Nenhuma imagem selecionada para envio.");
    return;
  }

  let token;
  try {
    token = await loadFirebaseToken();
    await validateFirebaseToken(token);
  } catch (error) {
    log(`❌ Não foi possível usar o token Firebase: ${messageOf(error)}`);
    log("Clique em Login no plug-in, autentique pelo navegador e tente enviar novamente.");
    return;
  }

  let openAiApiKey;
  try {
    openAiApiKey = await loadOpenAiApiKey();
  } catch (error) {
    log(`OpenAI nao configurada: ${messageOf(error)}`);
    log("Nenhum arquivo sera enviado sem metadados preenchidos pela IA.");
    return;
  }

  state.startedAt = Date.now();
  startTimer();
  updateProgress(0);
  setActionDisabled(document.getElementById("uploadButton"), true);
  setActionDisabled(document.getElementById("scanButton"), true);

  let uploaded = 0;
  let duplicates = 0;
  let errors = 0;

  for (let index = 0; index < selected.length; index += 1) {
    const asset = selected[index];
    try {
      const result = await uploadAssetToFirebase(asset, token, openAiApiKey);
      if (result === "duplicate") {
        duplicates += 1;
        state.duplicateCount = duplicates;
        log(`⏭️ Duplicado: ${asset.displayName}`);
      } else {
        uploaded += 1;
        state.uploadedCount = uploaded;
        log(`✅ Enviado: ${asset.displayName}`);
      }
    } catch (error) {
      errors += 1;
      state.uploadErrorCount = errors;
      log(`❌ Falha ao enviar ${asset.displayName}: ${messageOf(error)}`);
    }
    updateProgress(Math.round(((index + 1) / selected.length) * 100));
    await sleep(80);
  }

  stopTimer();
  updateProgress(100);
  updateCounters();
  updateAuthUi();

  log(`🏁 Envio finalizado. Enviados: ${uploaded} | Duplicados: ${duplicates} | Erros: ${errors}`);
}

function readLink(link, index) {
  const name = safeRead(() => link.name, `link_${index + 1}`);
  const filePath = safeRead(() => link.filePath, "");
  const status = normalizeStatus(safeRead(() => link.status, "desconhecido"));
  const displayName = originalNameFromPath(filePath) || cleanLinkName(name) || `link_${index + 1}`;
  const extension = detectExtension(filePath || displayName || name);
  const page = resolvePage(link);
  const provider = detectProvider(name, filePath);
  const hasError = isMissingStatus(status) || !filePath;

  return {
    id: `asset_${index}`,
    selected: false,
    linkRef: link,
    name,
    displayName,
    filePath,
    previewUrl: previewUrlFromPath(filePath),
    extension,
    page,
    status,
    provider,
    hasError,
    metadata: {
      horizontalScale: safeRead(() => link.parent.horizontalScale, ""),
      verticalScale: safeRead(() => link.parent.verticalScale, ""),
      effectivePpi: safeRead(() => link.parent.effectivePpi, ""),
      actualPpi: safeRead(() => link.parent.actualPpi, ""),
      space: safeRead(() => link.parent.space, "")
    }
  };
}

function isSupportedAsset(asset) {
  if (!asset) return false;
  if (!SUPPORTED_EXTENSIONS.has(String(asset.extension || "").toUpperCase())) return false;
  if (/^QR\s*Code/i.test(String(asset.name || ""))) return false;
  if (/^QR\s*Code/i.test(String(asset.displayName || ""))) return false;
  return true;
}

function renderTable() {
  const body = document.getElementById("assetTableBody");
  if (!body) return;

  if (!state.assets.length) {
    body.innerHTML = `<tr class="empty-row"><td colspan="3">Nenhum link encontrado no documento.</td></tr>`;
    return;
  }

  body.innerHTML = "";
  for (const asset of state.assets) {
    const tr = document.createElement("tr");

    const checkboxTd = document.createElement("td");
    checkboxTd.className = "check-col";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.dataset.assetId = asset.id;
    checkbox.checked = asset.selected;
    checkbox.disabled = asset.hasError;
    checkbox.addEventListener("change", () => {
      asset.selected = checkbox.checked;
      updateCounters();
    });
    checkboxTd.appendChild(checkbox);

    tr.appendChild(checkboxTd);
    tr.appendChild(previewCell(asset));
    tr.appendChild(cell(asset.displayName || asset.name));

    body.appendChild(tr);
  }

  schedulePreviewLoading();
}

function previewCell(asset) {
  const td = document.createElement("td");
  td.className = "preview-col";

  const frame = document.createElement("div");
  frame.className = "thumb-frame";
  frame.dataset.previewFrame = asset.id;

  const directPreviewUrls = looksPreviewable(asset.extension) ? fileUrlCandidatesFromPath(asset.filePath) : [];
  const imageUrls = uniqueValues([asset.generatedPreviewUrl, ...directPreviewUrls]);

  if (imageUrls.length) {
    const img = document.createElement("img");
    img.alt = asset.displayName || asset.name || "Miniatura";
    img.loading = "lazy";
    img.decoding = "async";
    loadPreviewImageWithFallback(img, imageUrls, () => {
      frame.innerHTML = "";
      frame.appendChild(previewFallback(asset));
    });
    frame.appendChild(img);
  } else {
    frame.appendChild(previewFallback(asset));
  }

  td.appendChild(frame);
  return td;
}

function schedulePreviewLoading() {
  const body = document.getElementById("assetTableBody");
  if (!body) return;

  const images = Array.from(body.querySelectorAll("img[data-preview-src]"));
  let index = 0;

  function loadNextBatch() {
    const limit = Math.min(index + PREVIEW_BATCH_SIZE, images.length);
    for (; index < limit; index += 1) {
      const img = images[index];
      const previewSrc = img ? img.getAttribute("data-preview-src") : "";
      if (img && previewSrc) {
        img.src = previewSrc;
        img.removeAttribute("data-preview-src");
      }
    }
    if (index < images.length) {
      setTimeout(loadNextBatch, PREVIEW_BATCH_DELAY_MS);
    }
  }

  setTimeout(loadNextBatch, 0);
}

async function preparePreviewsBeforeShowing() {
  const tableScroll = document.querySelector(".table-scroll");
  setLoading(true, "Preparando miniaturas...", "A lista aparecerá assim que as imagens estiverem prontas.", 0);
  if (tableScroll) tableScroll.classList.add("hidden");

  const needsPreview = state.assets.filter((asset) => shouldGeneratePreview(asset));
  if (!needsPreview.length) {
    setLoading(false);
    if (tableScroll) tableScroll.classList.remove("hidden");
    return;
  }

  log(`Gerando miniaturas leves para ${formatNumber(needsPreview.length)} arquivo(s)...`);
  for (let index = 0; index < needsPreview.length; index += 1) {
    const asset = needsPreview[index];
    setLoading(
      true,
      `Preparando miniaturas ${index + 1}/${needsPreview.length}`,
      asset.displayName || asset.name || "Arquivo",
      Math.round((index / needsPreview.length) * 100)
    );
    try {
      await generatePreviewFromInDesign(asset);
    } catch (error) {
      log(`Aviso: não foi possível gerar miniatura de ${asset.displayName}: ${messageOf(error)}`);
    }
    await sleep(35);
  }

  setLoading(false);
  if (tableScroll) tableScroll.classList.remove("hidden");
}

function setLoading(visible, title = "", text = "", percent = 0) {
  const panel = document.getElementById("loadingPanel");
  if (!panel) return;
  panel.classList.toggle("hidden", !visible);
  setText("loadingTitle", title || "Preparando miniaturas...");
  setText("loadingText", text || "Aguarde um instante.");
  const fill = document.getElementById("loadingFill");
  if (fill) {
    const safePercent = visible ? Math.max(0, Math.min(100, Number(percent) || 0)) : 0;
    fill.style.width = `${safePercent}%`;
  }
}

function scheduleGeneratedPreviews() {
  const needsGeneratedPreview = state.assets.filter((asset) => shouldGeneratePreview(asset));
  let index = 0;

  async function loadNextGeneratedBatch() {
    const limit = Math.min(index + GENERATED_PREVIEW_BATCH_SIZE, needsGeneratedPreview.length);
    for (; index < limit; index += 1) {
      const asset = needsGeneratedPreview[index];
      try {
        await generatePreviewFromInDesign(asset);
      } catch (error) {
        log(`Aviso: não foi possível gerar miniatura de ${asset.displayName}: ${messageOf(error)}`);
      }
    }
    if (index < needsGeneratedPreview.length) {
      setTimeout(loadNextGeneratedBatch, GENERATED_PREVIEW_DELAY_MS);
    }
  }

  if (needsGeneratedPreview.length) {
    log(`Gerando miniaturas leves para ${formatNumber(needsGeneratedPreview.length)} arquivo(s)...`);
    setTimeout(loadNextGeneratedBatch, GENERATED_PREVIEW_DELAY_MS);
  }
}

function shouldGeneratePreview(asset) {
  if (!asset || !asset.linkRef || asset.hasError) return false;
  const extension = String(asset.extension || "").toUpperCase();
  return SUPPORTED_EXTENSIONS.has(extension);
}

async function generatePreviewFromInDesign(asset) {
  if (!storage || !storage.localFileSystem || !asset.linkRef) return;

  const fsProvider = storage.localFileSystem;
  const tempFolder = await fsProvider.getTemporaryFolder();
  const safeName = asset.id.replace(/[^a-z0-9_-]/gi, "_");
  const previewFile = await tempFolder.createFile(`acervo_preview_${safeName}.jpg`, { overwrite: true });

  const exportTarget = safeRead(() => asset.linkRef.parent, null);
  if (!exportTarget || typeof exportTarget.exportFile !== "function") {
    throw new Error("objeto do InDesign não possui exportFile");
  }

  const exportFormat = indesign && indesign.ExportFormat ? indesign.ExportFormat.JPG : "JPG";
  exportTarget.exportFile(exportFormat, previewFile, false);

  const previewUrl = fsProvider.getFsUrl(previewFile);
  asset.generatedPreviewEntry = previewFile;
  asset.generatedPreviewUrl = previewUrl;
  updatePreviewImage(asset, previewUrl);
}

function updatePreviewImage(asset, previewUrl) {
  const frame = document.querySelector(`[data-preview-frame="${asset.id}"]`);
  if (!frame || !previewUrl) return;

  frame.innerHTML = "";
  const img = document.createElement("img");
  img.alt = asset.displayName || asset.name || "Miniatura";
  img.loading = "lazy";
  const directPreviewUrls = looksPreviewable(asset.extension) ? fileUrlCandidatesFromPath(asset.filePath) : [];
  loadPreviewImageWithFallback(img, uniqueValues([previewUrl, ...directPreviewUrls]), () => {
    frame.innerHTML = "";
    frame.appendChild(previewFallback(asset));
  });
  frame.appendChild(img);
}

function loadPreviewImageWithFallback(img, urls, onFail) {
  const candidates = uniqueValues(urls);
  let index = 0;

  function tryNext() {
    if (index >= candidates.length) {
      if (typeof onFail === "function") onFail();
      return;
    }

    img.src = candidates[index];
    index += 1;
  }

  img.addEventListener("error", tryNext);
  tryNext();
}

async function loadFirebaseToken() {
  if (!storage || !storage.localFileSystem) {
    throw new Error("sistema de arquivos do UXP indisponível");
  }

  const loaded = await readPluginRuntimeJson("token.json");
  const data = loaded.data;
  const token = data.token || data.idToken || data.id_token || "";

  if (!token) {
    throw new Error(`token vazio em ${loaded.path}`);
  }

  return token;
}

async function readPluginRuntimeJson(fileName) {
  const fsProvider = storage.localFileSystem;
  const pluginFolder = await fsProvider.getPluginFolder();
  const pluginPath = String(pluginFolder.nativePath || "");
  const expectedPath = `${pluginPath}\\runtime\\${fileName}`;

  try {
    const runtimeFolder = await pluginFolder.getEntry("runtime");
    const fileEntry = await runtimeFolder.getEntry(fileName);
    const raw = await fileEntry.read();
    return { path: expectedPath, data: parseJsonFileText(raw, expectedPath) };
  } catch (folderError) {
    try {
      const entry = await fsProvider.getEntryWithUrl(pathToFileUrl(expectedPath));
      const raw = await entry.read();
      return { path: expectedPath, data: parseJsonFileText(raw, expectedPath) };
    } catch (urlError) {
      throw new Error(`nenhum token encontrado em ${expectedPath}. Pasta: ${messageOf(folderError)} | URL: ${messageOf(urlError)}`);
    }
  }
}

async function loadOpenAiApiKey() {
  if (!storage || !storage.localFileSystem) {
    throw new Error("sistema de arquivos do UXP indisponivel");
  }

  const candidates = [
    { folderName: "runtime", fileName: "openai.config.json" },
    { folderName: "config", fileName: "openai.config.json" },
    { folderName: "config", fileName: "acervo.config.json" }
  ];
  const errors = [];

  for (const candidate of candidates) {
    try {
      const loaded = await readPluginJson(candidate.folderName, candidate.fileName);
      const data = loaded.data || {};
      const key = firstNonEmptyString(
        data.openai_api_key,
        data.OPENAI_API_KEY,
        data.openaiApiKey,
        data.openai && data.openai.apiKey,
        data.openai && data.openai.api_key
      );
      if (key) return key;
      errors.push(`${loaded.path}: chave nao encontrada no JSON`);
    } catch (error) {
      errors.push(`${candidate.folderName}\\${candidate.fileName}: ${messageOf(error)}`);
    }
  }

  throw new Error(`crie Plugin ID\\runtime\\openai.config.json com {"openai_api_key":"SUA_CHAVE"}. Tentativas: ${errors.join(" | ")}`);
}

async function readPluginJson(folderName, fileName) {
  const fsProvider = storage.localFileSystem;
  const pluginFolder = await fsProvider.getPluginFolder();
  const pluginPath = String(pluginFolder.nativePath || "");
  const expectedPath = `${pluginPath}\\${folderName}\\${fileName}`;

  try {
    const childFolder = await pluginFolder.getEntry(folderName);
    const fileEntry = await childFolder.getEntry(fileName);
    const raw = await fileEntry.read();
    return { path: expectedPath, data: parseJsonFileText(raw, expectedPath) };
  } catch (folderError) {
    try {
      const entry = await fsProvider.getEntryWithUrl(pathToFileUrl(expectedPath));
      const raw = await entry.read();
      return { path: expectedPath, data: parseJsonFileText(raw, expectedPath) };
    } catch (urlError) {
      throw new Error(`arquivo nao encontrado em ${expectedPath}. Pasta: ${messageOf(folderError)} | URL: ${messageOf(urlError)}`);
    }
  }
}

function parseJsonFileText(raw, pathLabel) {
  const originalText = String(raw ?? "");
  const cleanText = originalText
    .replace(/^\uFEFF/, "")
    .replace(/^\u00EF\u00BB\u00BF/, "")
    .replace(/[\u0000-\u001F\u007F]/g, (char) => {
      return char === "\n" || char === "\r" || char === "\t" ? char : "";
    })
    .trim();

  try {
    return JSON.parse(cleanText);
  } catch (firstError) {
    const repairedOpenAiConfig = cleanText.replace(
      /("openai_api_key"\s*:\s*)(sk-[A-Za-z0-9_\-]+)/,
      '$1"$2"'
    );

    if (repairedOpenAiConfig !== cleanText) {
      try {
        return JSON.parse(repairedOpenAiConfig);
      } catch (secondError) {
        throw new Error(`JSON invalido em ${pathLabel}: ${messageOf(secondError)}`);
      }
    }

    throw new Error(`JSON invalido em ${pathLabel}: ${messageOf(firstError)}`);
  }
}

function firstNonEmptyString(...values) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
}

async function ensureAuthServerReady() {
  if (await isAuthServerReady()) return;

  await openAuthLauncherIfPossible();
  for (let attempt = 0; attempt < 20; attempt += 1) {
    await sleep(500);
    if (await isAuthServerReady()) return;
  }

  if (await isAuthServerReady()) return;

  throw new Error("servidor de login local não está ativo");
}

async function isAuthServerReady() {
  try {
    const response = await fetch(`${AUTH_SERVER_URL}/health`, { method: "GET" });
    return response.ok;
  } catch (error) {
    return false;
  }
}

async function openAuthLauncherIfPossible() {
  if (!shell || typeof shell.openPath !== "function" || !storage || !storage.localFileSystem) {
    throw new Error("UXP shell.openPath indisponível");
  }

  const pluginFolder = await storage.localFileSystem.getPluginFolder();
  const pluginPath = String(pluginFolder.nativePath || "");
  const launcherNames = ["ABRIR_LOGIN_NAVEGADOR.vbs", "ABRIR_LOGIN_NAVEGADOR.cmd"];
  const errors = [];

  for (const launcherName of launcherNames) {
    try {
      const result = await shell.openPath(
        `${pluginPath}\\${launcherName}`,
        "Abrir o navegador para login no Acervo de Imagens"
      );

      if (!result) return;
      errors.push(`${launcherName}: ${result}`);
    } catch (error) {
      errors.push(`${launcherName}: ${messageOf(error)}`);
    }
  }

  throw new Error(`InDesign bloqueou o login pelo navegador. ${errors.join(" | ")}`);
}

async function openExternalBrowser(url) {
  const errors = [];

  if (shell && typeof shell.openPath === "function" && storage && storage.localFileSystem) {
    try {
      const pluginFolder = await storage.localFileSystem.getPluginFolder();
      const pluginPath = String(pluginFolder.nativePath || "");
      const result = await shell.openPath(
        `${pluginPath}\\ABRIR_LOGIN_PLUGIN.url`,
        "Abrir o navegador para login no Acervo de Imagens"
      );
      if (result) throw new Error(result);
      return;
    } catch (error) {
      errors.push(messageOf(error));
    }
  }

  if (shell && typeof shell.openExternal === "function") {
    try {
      await shell.openExternal(url);
      return;
    } catch (error) {
      errors.push(messageOf(error));
    }
  }

  if (typeof window !== "undefined" && typeof window.open === "function") {
    try {
      window.open(url);
      return;
    } catch (error) {
      errors.push(messageOf(error));
    }
  }

  throw new Error(errors.join(" | ") || "não foi possível abrir o navegador automaticamente");
}

function showInternalLoginBrowser() {
  const panel = document.getElementById("loginBrowserPanel");
  const frame = document.getElementById("loginBrowserFrame");
  if (!panel || !frame) {
    throw new Error("painel de login interno não encontrado");
  }

  panel.classList.remove("hidden");
  frame.src = `${AUTH_LOGIN_URL}?t=${Date.now()}`;
}

function hideInternalLoginBrowser() {
  const panel = document.getElementById("loginBrowserPanel");
  const frame = document.getElementById("loginBrowserFrame");
  if (frame) frame.src = "about:blank";
  if (panel) panel.classList.add("hidden");
}

async function waitForFirebaseLoginToken(timeoutMs = 120000) {
  const started = Date.now();
  let lastError = "";

  while (Date.now() - started < timeoutMs) {
    try {
      const tokenPayload = await readAuthServerToken();
      const token = tokenPayload.token || tokenPayload.idToken || tokenPayload.id_token || "";
      const user = await validateFirebaseToken(token);
      return { token, user };
    } catch (error) {
      lastError = messageOf(error);
    }
    await sleep(1500);
  }

  throw new Error(`tempo limite aguardando login. Último retorno: ${lastError}`);
}

async function readAuthServerToken() {
  const response = await fetch(`${AUTH_SERVER_URL}/token`, { method: "GET" });
  if (!response.ok) {
    throw new Error(`token ainda não disponível (${response.status})`);
  }
  return await response.json();
}

async function readFirstJsonFile(paths) {
  const fsProvider = storage.localFileSystem;
  const errors = [];

  for (const pathValue of paths) {
    try {
      const entry = await fsProvider.getEntryWithUrl(pathToFileUrl(pathValue));
      const raw = await entry.read();
      return { path: pathValue, data: parseJsonFileText(raw, pathValue) };
    } catch (error) {
      errors.push(`${pathValue}: ${messageOf(error)}`);
    }
  }

  throw new Error(`nenhum token encontrado. Tentativas: ${errors.join(" | ")}`);
}

async function validateFirebaseToken(token) {
  const response = await fetch(`https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=${FIREBASE_API_KEY}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idToken: token })
  });

  if (!response.ok) {
    throw new Error(`token inválido ou expirado (${response.status})`);
  }

  const data = await response.json();
  return data && Array.isArray(data.users) && data.users.length ? data.users[0] : {};
}

async function getFileEntryFromPath(filePath) {
  if (!storage || !storage.localFileSystem) {
    throw new Error("sistema de arquivos do UXP indisponível");
  }

  const fsProvider = storage.localFileSystem;
  const candidates = fileUrlCandidatesFromPath(filePath);
  const errors = [];

  for (const candidate of candidates) {
    try {
      return await fsProvider.getEntryWithUrl(candidate);
    } catch (error) {
      errors.push(`${candidate}: ${messageOf(error)}`);
    }
  }

  throw new Error(`arquivo original não encontrado pelo UXP. Tentativas: ${errors.join(" | ")}`);
}

async function uploadAssetToFirebase(asset, token, openAiApiKey) {
  const fileEntry = await getFileEntryFromPath(asset.filePath);
  const originalBuffer = await readBinary(fileEntry);
  const sha256 = await sha256Hex(originalBuffer);
  const duplicated = await firestoreHasSha256(sha256, token);
  if (duplicated) return "duplicate";

  const extension = String(asset.extension || detectExtension(asset.filePath)).toLowerCase();
  const isVector = isVectorExtension(extension);

  let previewBuffer;
  if (asset.generatedPreviewEntry) {
    previewBuffer = await readBinary(asset.generatedPreviewEntry);
  } else if (isVector) {
    await generatePreviewFromInDesign(asset);
    const previewEntry = asset.generatedPreviewEntry || await storage.localFileSystem.getEntryWithUrl(asset.generatedPreviewUrl);
    previewBuffer = await readBinary(previewEntry);
  } else {
    previewBuffer = await createRasterThumbnailBuffer(asset, originalBuffer);
  }

  log(`   Analisando com IA: ${asset.displayName}`);
  const aiMetadata = await analyzeImageWithOpenAI(previewBuffer, asset, openAiApiKey);
  log("   Analise OpenAI concluida.");

  const year = String(new Date().getFullYear());
  const uuid = createUuid();
  const provider = asset.provider || detectProvider(asset.name, asset.filePath);
  const typeFolder = isVector ? "vector" : "raster";
  const baseName = `IMG-${year}-${uuid.slice(0, 8)}`;
  const originalPath = `${STORAGE_ROOT}/originals/${typeFolder}/${provider}/${year}/${baseName}.${extension}`;
  const thumbnailPath = `${STORAGE_ROOT}/thumbnails/${provider}/${year}/${baseName}.jpg`;

  const originalUrl = await uploadStorageObject(originalPath, originalBuffer, mimeTypeForExtension(extension), token);
  const thumbnailUrl = await uploadStorageObject(thumbnailPath, previewBuffer, "image/jpeg", token);

  await createFirestoreDocument(uuid, buildAssetDocument({
    asset,
    uuid,
    baseName,
    provider,
    extension,
    sha256,
    originalPath,
    thumbnailPath,
    originalUrl,
    thumbnailUrl,
    originalSizeBytes: byteLengthOf(originalBuffer),
    aiMetadata
  }), token);

  return "uploaded";
}

async function firestoreHasSha256(sha256, token) {
  const url = `https://firestore.googleapis.com/v1/projects/${FIREBASE_PROJECT_ID}/databases/(default)/documents/acervo-visual-unificado/default:runQuery`;
  const response = await fetch(url, {
    method: "POST",
    headers: authJsonHeaders(token),
    body: JSON.stringify({
      structuredQuery: {
        from: [{ collectionId: "images" }],
        where: {
          fieldFilter: {
            field: { fieldPath: "sha256" },
            op: "EQUAL",
            value: { stringValue: sha256 }
          }
        },
        limit: 1
      }
    })
  });

  if (!response.ok) {
    throw new Error(`consulta Firestore falhou (${response.status})`);
  }

  const result = await response.json();
  return Array.isArray(result) && result.some((item) => item.document);
}

async function createFirestoreDocument(documentId, fields, token) {
  const url = `https://firestore.googleapis.com/v1/projects/${FIREBASE_PROJECT_ID}/databases/(default)/documents/${FIRESTORE_COLLECTION_PATH}?documentId=${encodeURIComponent(documentId)}`;
  const response = await fetch(url, {
    method: "POST",
    headers: authJsonHeaders(token),
    body: JSON.stringify({ fields: toFirestoreFields(fields) })
  });

  if (!response.ok) {
    throw new Error(`gravação Firestore falhou (${response.status})`);
  }
}

async function uploadStorageObject(storagePath, body, contentType, token) {
  const url = `https://firebasestorage.googleapis.com/v0/b/${FIREBASE_STORAGE_BUCKET}/o?uploadType=media&name=${encodeURIComponent(storagePath)}`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": contentType || "application/octet-stream"
    },
    body
  });

  if (!response.ok) {
    throw new Error(`upload falhou (${response.status}) em ${storagePath}`);
  }

  return storageDownloadUrl(storagePath);
}

async function createRasterThumbnailBuffer(asset, fallbackBuffer) {
  if (!asset.previewUrl || typeof Image === "undefined") {
    return fallbackBuffer;
  }

  try {
    const blob = await renderImageUrlToJpegBlob(asset.previewUrl, 220, 0.65);
    return await blob.arrayBuffer();
  } catch (error) {
    log(`Aviso: miniatura otimizada indisponível para ${asset.displayName}. Usando arquivo original como visualização.`);
    return fallbackBuffer;
  }
}

function renderImageUrlToJpegBlob(imageUrl, maxSize, quality) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      try {
        const width = Number(img.naturalWidth || img.width || 1);
        const height = Number(img.naturalHeight || img.height || 1);
        const scale = Math.min(1, maxSize / Math.max(width, height));
        const canvas = document.createElement("canvas");
        canvas.width = Math.max(1, Math.round(width * scale));
        canvas.height = Math.max(1, Math.round(height * scale));
        const context = canvas.getContext("2d");
        context.drawImage(img, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error("canvas não gerou blob"));
          }
        }, "image/jpeg", quality);
      } catch (error) {
        reject(error);
      }
    };
    img.onerror = () => reject(new Error("não foi possível carregar imagem local"));
    img.src = imageUrl;
  });
}

async function analyzeImageWithOpenAI(imageBuffer, asset, apiKey) {
  if (!apiKey) {
    throw new Error("chave OpenAI vazia");
  }

  const imageBase64 = arrayBufferToBase64(imageBuffer);
  const response = await fetch(OPENAI_CHAT_COMPLETIONS_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: OPENAI_MODEL,
      response_format: { type: "json_object" },
      max_tokens: 700,
      temperature: 0.2,
      messages: [
        {
          role: "user",
          content: [
            { type: "text", text: `${AI_METADATA_PROMPT}\nNome do arquivo: ${asset.displayName || asset.name || ""}` },
            {
              type: "image_url",
              image_url: {
                url: `data:image/jpeg;base64,${imageBase64}`,
                detail: "low"
              }
            }
          ]
        }
      ]
    })
  });

  if (!response.ok) {
    const detail = await safeReadResponseText(response);
    throw new Error(`analise OpenAI falhou (${response.status})${detail ? `: ${detail}` : ""}`);
  }

  const payload = await response.json();
  const content = payload && payload.choices && payload.choices[0] && payload.choices[0].message
    ? payload.choices[0].message.content
    : "";
  if (!content) {
    throw new Error("analise OpenAI sem conteudo de resposta");
  }

  let parsed;
  try {
    parsed = JSON.parse(content);
  } catch (error) {
    throw new Error(`OpenAI retornou JSON invalido: ${messageOf(error)}`);
  }

  return normalizeAiMetadata(parsed);
}

function normalizeAiMetadata(metadata) {
  const normalized = {
    tipo_imagem: requiredText(metadata.tipo_imagem, "tipo_imagem"),
    elementos_visuais: requiredText(metadata.elementos_visuais, "elementos_visuais"),
    estilo_tecnica: requiredText(metadata.estilo_tecnica, "estilo_tecnica"),
    formato: requiredText(metadata.formato, "formato"),
    cores_predominantes: requiredText(metadata.cores_predominantes, "cores_predominantes"),
    area_conhecimento: requiredText(metadata.area_conhecimento, "area_conhecimento"),
    caracteristicas: requiredText(metadata.caracteristicas, "caracteristicas"),
    palavras_chave_pt: normalizeKeywords(metadata.palavras_chave_pt, "palavras_chave_pt"),
    palavras_chave_en: normalizeKeywords(metadata.palavras_chave_en, "palavras_chave_en"),
    descricao_detalhada: requiredText(metadata.descricao_detalhada, "descricao_detalhada")
  };

  return normalized;
}

function requiredText(value, fieldName) {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  throw new Error(`campo de IA ausente: ${fieldName}`);
}

function normalizeKeywords(value, fieldName) {
  if (!Array.isArray(value)) {
    throw new Error(`campo de IA ausente: ${fieldName}`);
  }

  const keywords = value
    .map((item) => String(item || "").trim())
    .filter(Boolean)
    .slice(0, 10);

  if (keywords.length < 10) {
    throw new Error(`${fieldName} retornou ${keywords.length} palavra(s), esperado 10`);
  }

  return keywords;
}

function arrayBufferToBase64(buffer) {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 0x8000;

  for (let index = 0; index < bytes.length; index += chunkSize) {
    const chunk = bytes.subarray(index, index + chunkSize);
    binary += String.fromCharCode.apply(null, chunk);
  }

  return btoa(binary);
}

async function safeReadResponseText(response) {
  try {
    const text = await response.text();
    return text ? text.slice(0, 400) : "";
  } catch (error) {
    return "";
  }
}

function buildAssetDocument(data) {
  const { asset, uuid, baseName, provider, extension, sha256, originalPath, thumbnailPath, originalUrl, thumbnailUrl, originalSizeBytes, aiMetadata } = data;
  const sizeMb = Math.round((originalSizeBytes / 1024 / 1024) * 100) / 100;
  const ai = aiMetadata || {};
  return {
    uuid,
    codigo: uuid,
    nome_amigavel: baseName,
    nome_original: asset.displayName || asset.name || "",
    url_thumbnail: thumbnailUrl,
    url_original: originalUrl,
    storage_thumbnail: thumbnailPath,
    storage_original: originalPath,
    caminho_arquivo_original: asset.filePath || "",
    origem: provider,
    chave_numeracao: "",
    caracteristica_cor: "",
    eh_preto_e_branco: false,
    sha256,
    phash: "",
    extensao: `.${extension}`,
    tamanho_mb: sizeMb,
    resolucao: "",
    data_processamento: new Date().toISOString(),
    tipo_imagem: ai.tipo_imagem || "",
    elementos_visuais: ai.elementos_visuais || "",
    estilo_tecnica: ai.estilo_tecnica || "",
    formato: ai.formato || "",
    cores_predominantes: ai.cores_predominantes || "",
    area_conhecimento: ai.area_conhecimento || "",
    caracteristicas: ai.caracteristicas || "",
    palavras_chave_pt: ai.palavras_chave_pt || [],
    palavras_chave_en: ai.palavras_chave_en || [],
    descricao_detalhada: ai.descricao_detalhada || "",
    sheet_synced: false
  };
}

function toFirestoreFields(fields) {
  const converted = {};
  for (const [key, value] of Object.entries(fields)) {
    converted[key] = toFirestoreValue(value);
  }
  return converted;
}

function toFirestoreValue(value) {
  if (Array.isArray(value)) {
    return { arrayValue: { values: value.map(toFirestoreValue) } };
  }
  if (typeof value === "boolean") {
    return { booleanValue: value };
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? { integerValue: String(value) } : { doubleValue: value };
  }
  return { stringValue: String(value ?? "") };
}

function authJsonHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json"
  };
}

async function readBinary(entry) {
  const data = await entry.read({ format: storage.formats.binary });
  if (data instanceof ArrayBuffer) return data;
  if (data && data.buffer instanceof ArrayBuffer) {
    return data.buffer.slice(data.byteOffset || 0, (data.byteOffset || 0) + data.byteLength);
  }
  if (typeof data === "string") {
    return new TextEncoder().encode(data).buffer;
  }
  throw new Error("não foi possível ler arquivo binário");
}

async function sha256Hex(buffer) {
  const cryptoProvider = globalThis.crypto;
  if (cryptoProvider && cryptoProvider.subtle) {
    const digest = await cryptoProvider.subtle.digest("SHA-256", buffer);
    return bytesToHex(new Uint8Array(digest));
  }

  return sha256HexFallback(buffer);
}

function sha256HexFallback(buffer) {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
  const words = [];
  const bitLength = bytes.length * 8;

  for (let i = 0; i < bytes.length; i += 1) {
    words[i >> 2] |= bytes[i] << (24 - (i % 4) * 8);
  }

  words[bitLength >> 5] |= 0x80 << (24 - bitLength % 32);
  words[((bitLength + 64 >> 9) << 4) + 15] = bitLength;

  const constants = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];

  let h0 = 0x6a09e667;
  let h1 = 0xbb67ae85;
  let h2 = 0x3c6ef372;
  let h3 = 0xa54ff53a;
  let h4 = 0x510e527f;
  let h5 = 0x9b05688c;
  let h6 = 0x1f83d9ab;
  let h7 = 0x5be0cd19;
  const schedule = new Array(64);

  for (let i = 0; i < words.length; i += 16) {
    let a = h0;
    let b = h1;
    let c = h2;
    let d = h3;
    let e = h4;
    let f = h5;
    let g = h6;
    let h = h7;

    for (let j = 0; j < 64; j += 1) {
      if (j < 16) {
        schedule[j] = words[i + j] | 0;
      } else {
        const s0 = rightRotate(schedule[j - 15], 7) ^ rightRotate(schedule[j - 15], 18) ^ (schedule[j - 15] >>> 3);
        const s1 = rightRotate(schedule[j - 2], 17) ^ rightRotate(schedule[j - 2], 19) ^ (schedule[j - 2] >>> 10);
        schedule[j] = (schedule[j - 16] + s0 + schedule[j - 7] + s1) | 0;
      }

      const bigS1 = rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25);
      const ch = (e & f) ^ (~e & g);
      const temp1 = (h + bigS1 + ch + constants[j] + schedule[j]) | 0;
      const bigS0 = rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22);
      const maj = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = (bigS0 + maj) | 0;

      h = g;
      g = f;
      f = e;
      e = (d + temp1) | 0;
      d = c;
      c = b;
      b = a;
      a = (temp1 + temp2) | 0;
    }

    h0 = (h0 + a) | 0;
    h1 = (h1 + b) | 0;
    h2 = (h2 + c) | 0;
    h3 = (h3 + d) | 0;
    h4 = (h4 + e) | 0;
    h5 = (h5 + f) | 0;
    h6 = (h6 + g) | 0;
    h7 = (h7 + h) | 0;
  }

  return [h0, h1, h2, h3, h4, h5, h6, h7]
    .map((value) => (value >>> 0).toString(16).padStart(8, "0"))
    .join("");
}

function rightRotate(value, amount) {
  return (value >>> amount) | (value << (32 - amount));
}

function bytesToHex(bytes) {
  return Array.from(bytes).map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function byteLengthOf(buffer) {
  if (buffer instanceof ArrayBuffer) return buffer.byteLength;
  if (buffer && typeof buffer.byteLength === "number") return buffer.byteLength;
  return 0;
}

function pathToFileUrl(pathValue) {
  const candidates = fileUrlCandidatesFromPath(pathValue);
  return candidates[0] || "";
}

function fileUrlCandidatesFromPath(pathValue) {
  const value = String(pathValue || "").trim();
  if (!value) return [];
  const normalized = value.replace(/\\/g, "/");
  const encoded = normalized
    .split("/")
    .map((part, index) => index === 0 && /^[A-Za-z]:$/.test(part) ? part : encodeURIComponent(part))
    .join("/");
  return uniqueValues([
    `file:///${encoded}`,
    `file:/${encoded}`,
    `file:///${normalized}`,
    `file:/${normalized}`
  ]);
}

function uniqueValues(values) {
  return Array.from(new Set(values.filter(Boolean)));
}

function storageDownloadUrl(storagePath) {
  return `https://firebasestorage.googleapis.com/v0/b/${FIREBASE_STORAGE_BUCKET}/o/${encodeURIComponent(storagePath)}?alt=media`;
}

function mimeTypeForExtension(extension) {
  const normalized = String(extension || "").replace(".", "").toLowerCase();
  if (normalized === "jpg" || normalized === "jpeg") return "image/jpeg";
  if (normalized === "png") return "image/png";
  if (normalized === "svg") return "image/svg+xml";
  if (normalized === "eps") return "application/postscript";
  if (normalized === "ai") return "application/postscript";
  return "application/octet-stream";
}

function isVectorExtension(extension) {
  return /^(eps|ai|svg)$/i.test(String(extension || "").replace(".", ""));
}

function createUuid() {
  const cryptoProvider = globalThis.crypto;
  if (cryptoProvider && typeof cryptoProvider.randomUUID === "function") {
    return cryptoProvider.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const value = Math.random() * 16 | 0;
    const safeValue = char === "x" ? value : (value & 0x3 | 0x8);
    return safeValue.toString(16);
  });
}

function previewFallback(asset) {
  const fallback = document.createElement("div");
  fallback.className = "thumb-fallback";
  fallback.textContent = asset.extension || "IMG";
  return fallback;
}

function cell(text, className = "") {
  const td = document.createElement("td");
  td.textContent = String(text ?? "");
  if (className) td.className = className;
  return td;
}

function statusCell(status, hasError) {
  const td = cell(status || "desconhecido");
  td.className = hasError ? "status-error" : statusLooksModified(status) ? "status-warning" : "status-ok";
  return td;
}

function setAllSelected(selected) {
  for (const asset of state.assets) {
    if (!asset.hasError) {
      asset.selected = selected;
    }
  }
  const body = document.getElementById("assetTableBody");
  if (body) {
    const checkboxes = body.querySelectorAll("input[type='checkbox']");
    for (const checkbox of checkboxes) {
      if (!checkbox.disabled) {
        checkbox.checked = selected;
      }
    }
  }
  updateCounters();
}

function updateCounters() {
  const found = state.assets.length;
  const selected = state.assets.filter((asset) => asset.selected).length;
  const errors = state.assets.filter((asset) => asset.hasError).length + state.uploadErrorCount;

  setText("foundCount", formatNumber(found));
  setText("selectedCount", formatNumber(selected));
  setText("duplicateCount", formatNumber(state.duplicateCount));
  setText("errorCount", formatNumber(errors));

  const uploadButton = document.getElementById("uploadButton");
  setActionDisabled(uploadButton, !state.authenticated || selected === 0);
}

async function loginViaShortcut() {
  const loginButton = document.getElementById("loginButton");
  setActionDisabled(loginButton, true);
  log("Abrindo login pelo atalho do navegador...");

  try {
    const existingLogin = await tryReadValidLoginToken();
    if (existingLogin) {
      finishLogin(existingLogin.user);
      log("Token salvo encontrado. Login liberado sem abrir o navegador.");
      return;
    }

    await ensureAuthServerReady();
    log("Faça login no navegador. O plug-in aguardará a autenticação automaticamente.");

    const result = await waitForFirebaseLoginToken();
    finishLogin(result.user);
    log("Agora você pode clicar em “Varrer documento”.");
  } catch (error) {
    state.authenticated = false;
    updateAuthUi();
    updateCounters();
    log(`Login não concluído: ${messageOf(error)}`);
    log("Não foi possível abrir o atalho do navegador pelo plug-in.");
  } finally {
    if (!state.authenticated) {
      setActionDisabled(loginButton, false);
    }
  }
}

async function login() {
  const loginButton = document.getElementById("loginButton");
  setActionDisabled(loginButton, true);
  log("Abrindo login pelo atalho do navegador...");

  try {
    await ensureAuthServerReady();
    await openExternalBrowser(AUTH_LOGIN_URL);
    log("Faça login no navegador interno. O plug-in aguardará a autenticação automaticamente.");
    if (false) {
      log(`Aviso: o InDesign não conseguiu abrir o navegador automaticamente (${messageOf(openError)}).`);
      log(`Se a janela de login já estiver aberta, conclua o login nela. URL: ${AUTH_LOGIN_URL}`);
    }
    log("Faça login no navegador. O plug-in aguardará a autenticação automaticamente.");

    const result = await waitForFirebaseLoginToken();
    const email = result.user && result.user.email ? result.user.email : "usuario autenticado";

    state.authenticated = true;
    state.userEmail = email;
    saveLogin(email);
    updateAuthUi();
    updateCounters();
    log(`Login concluído para: ${email}`);
    log("Agora você pode clicar em “Varrer documento”.");
  } catch (error) {
    state.authenticated = false;
    updateAuthUi();
    updateCounters();
    log(`Login não concluído: ${messageOf(error)}`);
    log("O login precisa abrir pelo navegador. Recarregue o plug-in e clique em Login novamente.");
  } finally {
    if (!state.authenticated) {
      setActionDisabled(loginButton, false);
    }
  }
}

async function tryReadValidLoginToken() {
  try {
    const token = await loadFirebaseToken();
    const user = await validateFirebaseToken(token);
    return { token, user };
  } catch (error) {
    return null;
  }
}

function finishLogin(user) {
  const email = user && user.email ? user.email : "usuario autenticado";
  state.authenticated = true;
  state.userEmail = email;
  saveLogin(email);
  updateAuthUi();
  updateCounters();
  log(`Login concluído para: ${email}`);
}

function logout() {
  state.authenticated = false;
  state.userEmail = "";
  clearSavedLogin();
  hideInternalLoginBrowser();
  state.assets = [];
  renderTable();
  updateAuthUi();
  updateCounters();
  updateProgress(0);
  log("Usuário saiu. Varredura e envio bloqueados.");
}

function updateAuthUi() {
  const scanButton = document.getElementById("scanButton");
  const loginButton = document.getElementById("loginButton");
  const logoutButton = document.getElementById("logoutButton");
  const status = document.getElementById("loginStatus");
  const emailText = document.getElementById("userEmailText");

  setActionDisabled(scanButton, !state.authenticated);
  setActionDisabled(loginButton, state.authenticated);
  setActionDisabled(logoutButton, !state.authenticated);
  if (status) {
    status.textContent = state.authenticated ? "✓ Autenticado" : "Não autenticado";
    status.className = `login-status ${state.authenticated ? "unlocked" : "locked"}`;
  }
  if (emailText) {
    emailText.textContent = state.authenticated && state.userEmail ? state.userEmail : "";
  }
}

function setActionDisabled(el, disabled) {
  if (!el) return;
  el.classList.toggle("disabled", Boolean(disabled));
  el.setAttribute("aria-disabled", disabled ? "true" : "false");
}

async function restoreTokenLoginInBackground() {
  if (state.authenticated) return;

  try {
    const token = await loadFirebaseToken();
    const payload = decodeJwtPayload(token);
    const email = payload && payload.email ? payload.email : "";
    const expiresAt = Number(payload && payload.exp ? payload.exp : 0);
    const isExpired = expiresAt && Math.floor(Date.now() / 1000) >= expiresAt;

    if (!email || isExpired) return;

    state.authenticated = true;
    state.userEmail = email;
    saveLogin(email);
    updateAuthUi();
    updateCounters();
    log(`Login recuperado pelo token salvo: ${email}`);
  } catch (error) {
    // Sem token salvo ou token ilegível: segue aguardando login manual pelo botão.
  }
}

function decodeJwtPayload(token) {
  try {
    const parts = String(token || "").split(".");
    if (parts.length < 2 || typeof atob !== "function") return null;
    let base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    while (base64.length % 4) base64 += "=";
    return JSON.parse(atob(base64));
  } catch (error) {
    return null;
  }
}

function restoreSavedLogin() {
  try {
    const saved = localStorage.getItem("acervo_indesign_user_email");
    if (saved && saved.includes("@")) {
      state.authenticated = true;
      state.userEmail = saved;
    }
  } catch (error) {
    // localStorage pode falhar em ambientes restritos. Nesse caso, segue sem login salvo.
  }
}

function saveLogin(email) {
  try {
    localStorage.setItem("acervo_indesign_user_email", email);
  } catch (error) {
    log("Aviso: não foi possível salvar o login permanente neste ambiente.");
  }
}

function clearSavedLogin() {
  try {
    localStorage.removeItem("acervo_indesign_user_email");
  } catch (error) {
    // Sem ação necessária.
  }
}

function updateProgress(percent) {
  const safePercent = Math.max(0, Math.min(100, Number(percent) || 0));
  state.progressPercent = safePercent;
  const fill = document.getElementById("progressFill");
  if (fill) {
    fill.style.width = `${safePercent}%`;
  }
  setText("progressText", `Progresso: ${safePercent}% | Tempo: ${elapsedTime()}`);
}

function resetRun() {
  state.startedAt = Date.now();
  startTimer();
  state.assets = [];
  state.uploadedCount = 0;
  state.duplicateCount = 0;
  state.uploadErrorCount = 0;
  state.progressPercent = 0;
  renderTable();
  updateCounters();
  updateProgress(0);
  clearLog();
  log("Varredura iniciada...");
}

function startTimer() {
  stopTimer();
  state.timerId = setInterval(() => updateProgress(state.progressPercent), 1000);
}

function stopTimer() {
  if (state.timerId) {
    clearInterval(state.timerId);
    state.timerId = null;
  }
}

function elapsedTime() {
  if (!state.startedAt) return "00:00:00";
  const seconds = Math.floor((Date.now() - state.startedAt) / 1000);
  const hh = String(Math.floor(seconds / 3600)).padStart(2, "0");
  const mm = String(Math.floor((seconds % 3600) / 60)).padStart(2, "0");
  const ss = String(seconds % 60).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}

function log(message) {
  const panel = document.getElementById("logPanel");
  if (!panel) return;
  const line = document.createElement("div");
  line.className = "log-line";
  line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  panel.appendChild(line);
  panel.scrollTop = panel.scrollHeight;
}

function clearLog() {
  const panel = document.getElementById("logPanel");
  if (panel) panel.innerHTML = "";
}

function toggleTheme() {
  state.dark = !state.dark;
  document.body.classList.toggle("dark", state.dark);
  setText("themeToggle", state.dark ? "☀" : "☾");
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = value;
  }
}

function toArray(collection) {
  if (!collection) return [];
  if (Array.isArray(collection)) return collection;

  try {
    if (typeof collection.everyItem === "function") {
      const items = collection.everyItem().getElements();
      if (Array.isArray(items)) return items;
    }
  } catch (error) {
    // Segue para fallback por índice.
  }

  const result = [];
  const length = Number(collection.length || 0);
  for (let i = 0; i < length; i += 1) {
    try {
      result.push(typeof collection.item === "function" ? collection.item(i) : collection[i]);
    } catch (error) {
      log(`Aviso: não foi possível ler o link ${i + 1}: ${messageOf(error)}`);
    }
  }
  return result.filter(Boolean);
}

function resolvePage(link) {
  const attempts = [
    () => link.parent.parentPage.name,
    () => link.parent.parent.parentPage.name,
    () => link.parent.parent.parent.parentPage.name
  ];
  for (const attempt of attempts) {
    const value = safeRead(attempt, "");
    if (value) return value;
  }
  return "";
}

function normalizeStatus(status) {
  if (status === null || status === undefined) return "desconhecido";
  if (typeof status === "string") return status;
  if (typeof status.toString === "function") return status.toString();
  return String(status);
}

function isMissingStatus(status) {
  return /missing|faltante|not\s*found|ausente/i.test(String(status || ""));
}

function statusLooksModified(status) {
  return /modified|modificado|out\s*of\s*date/i.test(String(status || ""));
}

function detectExtension(value) {
  const match = String(value || "").match(/\.([a-z0-9]+)$/i);
  return match ? match[1].toUpperCase() : "";
}

function originalNameFromPath(filePath) {
  const value = String(filePath || "").replace(/\\/g, "/");
  const parts = value.split("/");
  const last = parts[parts.length - 1] || "";
  return last.trim();
}

function cleanLinkName(name) {
  const value = String(name || "").trim();
  if (/^QR\s*Code/i.test(value)) return "";
  return value;
}

function previewUrlFromPath(filePath) {
  return pathToFileUrl(filePath);
}

function looksPreviewable(extension) {
  return /^(JPG|JPEG|PNG|GIF|WEBP|BMP)$/i.test(String(extension || ""));
}

function detectProvider(name, filePath) {
  const value = `${name || ""} ${filePath || ""}`.toLowerCase();
  if (value.includes("shutterstock")) return "shutterstock";
  if (value.includes("envato")) return "envato";
  if (value.includes("pexels")) return "pexels";
  if (value.includes("freepik")) return "freepik";
  return "outros";
}

function safeRead(reader, fallback) {
  try {
    const value = reader();
    return value === undefined || value === null ? fallback : value;
  } catch (error) {
    return fallback;
  }
}

function messageOf(error) {
  return error && error.message ? error.message : String(error);
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString("pt-BR");
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
