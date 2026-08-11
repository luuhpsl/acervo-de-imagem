from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import threading
import time
import webbrowser


BASE_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = BASE_DIR / "runtime"
TOKEN_FILE = RUNTIME_DIR / "token.json"
HOST = "127.0.0.1"
PORT = 5055


LOGIN_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Login Firebase - Acervo de Imagens</title>
  <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js"></script>
  <style>
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #171717;
      color: #eeeeee;
      font-family: Arial, Helvetica, sans-serif;
    }
    main {
      width: min(560px, calc(100vw - 40px));
      padding: 32px;
      border: 1px solid #666666;
      background: #222222;
      box-shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
    }
    h1 {
      margin: 0 0 8px;
      font-size: 28px;
    }
    p {
      color: #b5b5b5;
      line-height: 1.5;
    }
    .actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 22px;
    }
    button {
      min-height: 42px;
      padding: 0 18px;
      border: 1px solid #666666;
      background: #2d2d2d;
      color: #eeeeee;
      cursor: pointer;
      font-weight: 700;
    }
    button.primary {
      color: #00cc66;
    }
    #status {
      margin-top: 22px;
      color: #9b51e0;
      font-weight: 700;
    }
  </style>
</head>
<body>
  <main>
    <h1>Acervo de Imagens</h1>
    <p>Faça login com sua conta corporativa para liberar o envio pelo plug-in do InDesign.</p>
    <div class="actions">
      <button id="login-microsoft" class="primary">Entrar com Microsoft</button>
      <button id="login-google">Entrar com Google</button>
    </div>
    <div id="status">Aguardando login...</div>
  </main>

  <script>
    const firebaseConfig = {
      apiKey: "AIzaSyBD6TkUg5F_j9C2_VK6pWf-z34Iyszp0LE",
      authDomain: "uniasselvi-digital.firebaseapp.com",
      databaseURL: "https://uniasselvi-digital.firebaseio.com",
      projectId: "uniasselvi-digital",
      storageBucket: "uniasselvi-digital.appspot.com",
      messagingSenderId: "540573107988",
      appId: "1:540573107988:web:59af50ad04f91284fb2401",
      measurementId: "G-BYSN6ETYMV"
    };

    firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();

    const microsoftProvider = new firebase.auth.OAuthProvider("microsoft.com");
    microsoftProvider.setCustomParameters({
      tenant: "b0e7335f-fd1f-46ad-98c7-55e6e4e222ea"
    });

    function setStatus(message, error = false) {
      const el = document.getElementById("status");
      el.textContent = message;
      el.style.color = error ? "#dc2626" : "#00cc66";
    }

    async function sendToken(user) {
      const idToken = await user.getIdToken();
      const response = await fetch("/callback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: idToken,
          email: user.email || "",
          uid: user.uid || ""
        })
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      setStatus("Login concluído. Você pode voltar para o InDesign.");
    }

    document.getElementById("login-microsoft").onclick = async () => {
      try {
        setStatus("Abrindo login Microsoft...");
        const result = await auth.signInWithPopup(microsoftProvider);
        await sendToken(result.user);
      } catch (error) {
        setStatus("Erro: " + error.message, true);
      }
    };

    document.getElementById("login-google").onclick = async () => {
      try {
        setStatus("Abrindo login Google...");
        const provider = new firebase.auth.GoogleAuthProvider();
        const result = await auth.signInWithPopup(provider);
        await sendToken(result.user);
      } catch (error) {
        setStatus("Erro: " + error.message, true);
      }
    };
  </script>
</body>
</html>
"""


class AuthHandler(BaseHTTPRequestHandler):
    def _send(self, status, content, content_type="text/plain; charset=utf-8"):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, "OK")
            return

        if self.path == "/token":
            if not TOKEN_FILE.exists():
                self._send(404, "Token ainda nao encontrado")
                return
            self._send(200, TOKEN_FILE.read_text(encoding="utf-8"), "application/json; charset=utf-8")
            return

        self._send(200, LOGIN_PAGE, "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/callback":
            self._send(404, "Nao encontrado")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self._send(400, "JSON invalido")
            return

        token = payload.get("token")
        if not token:
            self._send(400, "Token nao recebido")
            return

        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        temp_file = TOKEN_FILE.with_suffix(".json.tmp")
        temp_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_file.replace(TOKEN_FILE)
        self._send(200, "OK")

    def log_message(self, format, *args):
        return


def open_browser_later(url):
    time.sleep(0.8)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    url = f"http://{HOST}:{PORT}/"
    print(f"Servidor de login do plug-in ativo em {url}")
    print(f"Token sera salvo em: {TOKEN_FILE}")
    server = ThreadingHTTPServer((HOST, PORT), AuthHandler)
    threading.Thread(target=open_browser_later, args=(url,), daemon=True).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
