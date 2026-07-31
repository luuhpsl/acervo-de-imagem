from flask import Flask, request, render_template_string
import threading
import json
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
FIREBASE_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY", ""),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", "uniasselvi-digital.firebaseapp.com"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL", "https://uniasselvi-digital.firebaseio.com"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", "uniasselvi-digital"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "uniasselvi-digital.appspot.com"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "540573107988"),
    "appId": os.getenv("FIREBASE_APP_ID", ""),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID", ""),
}

# --- PÁGINA HTML QUE SERÁ ABERTA NO NAVEGADOR ---
LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js"></script>
</head>
<body style="font-family: Arial; text-align: center; padding-top: 50px;">
  <h1>🔐 Autenticação para o Catálogo</h1>
  <p>Clique no botão abaixo para fazer login com sua conta corporativa:</p>
  <button id="login-microsoft" style="padding: 12px 30px; font-size: 16px; cursor: pointer;">Entrar com Microsoft</button>
  <button id="login-google" style="padding: 12px 30px; font-size: 16px; cursor: pointer; margin-left: 10px;">Entrar com Google</button>
  <div id="status" style="margin-top: 20px; color: green; font-weight: bold;"></div>

  <script>
    // Configuração do Firebase (a mesma que você forneceu)
    const firebaseConfig = {{ firebase_config_json | safe }};
    firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();

    // Provider para Microsoft (com tenant específico)
    const microsoftProvider = new firebase.auth.OAuthProvider('microsoft.com');
    microsoftProvider.setCustomParameters({
      tenant: 'b0e7335f-fd1f-46ad-98c7-55e6e4e222ea'
    });

    // Função que envia o token para o nosso servidor local
    function sendToken(user) {
      user.getIdToken().then(idToken => {
        fetch('/callback', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ token: idToken })
        }).then(res => {
          if (res.ok) {
            document.getElementById('status').innerHTML = '✅ Login concluído! Você pode fechar esta janela.';
          }
        });
      });
    }

    // Botão Microsoft
    document.getElementById('login-microsoft').onclick = () => {
      auth.signInWithPopup(microsoftProvider)
        .then(result => sendToken(result.user))
        .catch(error => alert('Erro: ' + error.message));
    };

    // Botão Google
    document.getElementById('login-google').onclick = () => {
      const provider = new firebase.auth.GoogleAuthProvider();
      auth.signInWithPopup(provider)
        .then(result => sendToken(result.user))
        .catch(error => alert('Erro: ' + error.message));
    };
  </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(LOGIN_PAGE, firebase_config_json=json.dumps(FIREBASE_CONFIG))

@app.route('/callback', methods=['POST'])
def callback():
    data = request.json
    token = data.get('token')
    if token:
        # Salva o token em um arquivo para o programa principal ler
        temp_token_file = TOKEN_FILE + ".tmp"
        try:
            with open(temp_token_file, 'w') as f:
                json.dump({'token': token}, f)
            os.replace(temp_token_file, TOKEN_FILE)
        except PermissionError as e:
            return f'Permissao negada ao salvar token em {TOKEN_FILE}: {e}', 500
        return 'OK', 200
    return 'Token não recebido', 400

def iniciar_servidor():
    """Inicia o servidor Flask em uma thread separada."""
    threading.Thread(target=lambda: app.run(port=5000, debug=False, use_reloader=False), daemon=True).start()
