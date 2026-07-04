/*
  AutoBob - Control PRO por WiFi
  Wemos D1 Mini (ESP8266) + L298N

  Features:
    - Interfaz moderna con panel de control tipo joystick
    - Control tactil continuo: mantener presionado = mueve, soltar = se detiene
    - Slider de velocidad en vivo
    - Boton TURBO (velocidad maxima mientras se mantiene presionado)
    - Modo DRIFT (toggle): al girar, hace un pulso de derrape antes de tomar la curva
    - Indicador de conexion (ping cada 2 segundos)

  Conexiones:
    L298N  ENA -> D1
    L298N  IN1 -> D0
    L298N  IN2 -> D5
    L298N  IN3 -> D6
    L298N  IN4 -> D7
    L298N  ENB -> D2
    L298N  GND -> GND (comun con el D1 Mini y la bateria de motores)
    L298N  12V -> (+) bateria de motores

  Requisitos en Arduino IDE:
    Tools > Board > Boards Manager > buscar "esp8266" (por ESP8266 Community)
    e instalar. Luego Tools > Board > ESP8266 Boards > LOLIN(WEMOS) D1 R2 & mini
*/

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

const char* ssid = "AutoBob";       // nombre de la red WiFi que crea el D1 Mini
const char* password = "12345678";  // minimo 8 caracteres

ESP8266WebServer server(80);

#define ENA D1
#define IN1 D0
#define IN2 D5
#define IN3 D6
#define IN4 D7
#define ENB D2

int velocidad = 200;      // velocidad base (0-255), controlada por el slider
bool turboActivo = false; // true mientras se mantiene presionado TURBO
bool driftActivo = false; // true si el modo drift esta encendido

int vel() {
  return turboActivo ? 255 : velocidad;
}

const char PAGINA[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<title>AutoBob Control</title>
<style>
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; user-select: none; }
  body {
    margin: 0;
    font-family: 'Segoe UI', Arial, sans-serif;
    background: radial-gradient(circle at top, #1e2530, #0d1117);
    color: #fff;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px;
    touch-action: manipulation;
  }
  h1 {
    font-size: 20px;
    letter-spacing: 2px;
    margin: 8px 0 4px;
    background: linear-gradient(90deg, #4CAF50, #2196F3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  #estado {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: #aaa;
    margin-bottom: 16px;
  }
  #dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: #e53935;
    box-shadow: 0 0 8px #e53935;
    transition: 0.3s;
  }
  #dot.on {
    background: #4CAF50;
    box-shadow: 0 0 8px #4CAF50;
  }
  .panel {
    background: #161b22;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    width: 100%;
    max-width: 340px;
  }
  .dpad {
    display: grid;
    grid-template-columns: 80px 80px 80px;
    grid-template-rows: 80px 80px 80px;
    gap: 8px;
    justify-content: center;
    margin-bottom: 20px;
  }
  .btn {
    border: none;
    border-radius: 16px;
    font-size: 15px;
    font-weight: 600;
    color: #fff;
    background: linear-gradient(145deg, #2b3542, #1c232c);
    box-shadow: 0 4px 10px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.08s, background 0.15s;
  }
  .btn:active, .btn.pressed {
    transform: scale(0.93);
    background: linear-gradient(145deg, #4CAF50, #2e7d32);
  }
  #adelante { grid-column: 2; grid-row: 1; }
  #izquierda { grid-column: 1; grid-row: 2; }
  #alto { grid-column: 2; grid-row: 2; background: linear-gradient(145deg, #e53935, #b71c1c); }
  #derecha { grid-column: 3; grid-row: 2; }
  #atras { grid-column: 2; grid-row: 3; }

  .slider-box {
    margin-bottom: 18px;
  }
  .slider-box label {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    color: #ccc;
    margin-bottom: 6px;
  }
  input[type=range] {
    width: 100%;
    -webkit-appearance: none;
    height: 8px;
    border-radius: 4px;
    background: #2b3542;
    outline: none;
  }
  input[type=range]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 22px; height: 22px;
    border-radius: 50%;
    background: linear-gradient(145deg, #2196F3, #1565C0);
    box-shadow: 0 2px 6px rgba(0,0,0,0.5);
    cursor: pointer;
  }
  .extra {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
  .extra .btn {
    height: 54px;
    border-radius: 14px;
    font-size: 14px;
  }
  #turbo {
    background: linear-gradient(145deg, #ff9800, #e65100);
  }
  #turbo.pressed {
    background: linear-gradient(145deg, #ffca28, #ff6f00);
    box-shadow: 0 0 16px #ff9800;
  }
  #drift {
    background: linear-gradient(145deg, #7e57c2, #4527a0);
  }
  #drift.pressed {
    background: linear-gradient(145deg, #b39ddb, #5e35b1);
    box-shadow: 0 0 16px #7e57c2;
  }
</style>
</head>
<body>

<h1>AUTOBOB</h1>
<div id="estado"><div id="dot"></div><span id="estadoTexto">Conectando...</span></div>

<div class="panel">

  <div class="dpad">
    <button class="btn" id="adelante">&#9650;</button>
    <button class="btn" id="izquierda">&#9664;</button>
    <button class="btn" id="alto">&#9632;</button>
    <button class="btn" id="derecha">&#9654;</button>
    <button class="btn" id="atras">&#9660;</button>
  </div>

  <div class="slider-box">
    <label>Velocidad <span id="velVal">200</span></label>
    <input type="range" id="slider" min="60" max="255" value="200">
  </div>

  <div class="extra">
    <button class="btn" id="turbo">TURBO</button>
    <button class="btn" id="drift">DRIFT</button>
  </div>

</div>

<script>
function cmd(c) {
  fetch('/' + c).catch(function(){});
}

function bindHold(id, downCmd, upCmd) {
  var el = document.getElementById(id);
  function start(e) { e.preventDefault(); el.classList.add('pressed'); cmd(downCmd); }
  function end(e) { e.preventDefault(); el.classList.remove('pressed'); cmd(upCmd); }
  el.addEventListener('touchstart', start);
  el.addEventListener('touchend', end);
  el.addEventListener('touchcancel', end);
  el.addEventListener('mousedown', start);
  el.addEventListener('mouseup', end);
  el.addEventListener('mouseleave', end);
}

bindHold('adelante', 'F', 'S');
bindHold('atras', 'B', 'S');
bindHold('izquierda', 'L', 'S');
bindHold('derecha', 'R', 'S');
bindHold('turbo', 'T1', 'T0');

document.getElementById('alto').addEventListener('click', function() { cmd('S'); });

var driftOn = false;
document.getElementById('drift').addEventListener('click', function(e) {
  driftOn = !driftOn;
  e.currentTarget.classList.toggle('pressed', driftOn);
  cmd(driftOn ? 'D1' : 'D0');
});

var slider = document.getElementById('slider');
var velVal = document.getElementById('velVal');
slider.addEventListener('input', function() {
  velVal.textContent = slider.value;
  fetch('/V?val=' + slider.value).catch(function(){});
});

function chequearConexion() {
  fetch('/ping', { cache: 'no-store' })
    .then(function() {
      document.getElementById('dot').classList.add('on');
      document.getElementById('estadoTexto').textContent = 'Conectado';
    })
    .catch(function() {
      document.getElementById('dot').classList.remove('on');
      document.getElementById('estadoTexto').textContent = 'Sin conexion';
    });
}
chequearConexion();
setInterval(chequearConexion, 2000);
</script>
</body>
</html>
)rawliteral";

void setup() {
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENB, OUTPUT);

  analogWriteRange(255); // rango de PWM 0-255

  detener();

  Serial.begin(115200);

  WiFi.softAP(ssid, password);
  Serial.print("Conectate a la red WiFi: ");
  Serial.println(ssid);
  Serial.print("Luego abre en el navegador: http://");
  Serial.println(WiFi.softAPIP());

  server.on("/", []() { server.send(200, "text/html", PAGINA); });
  server.on("/F", []() { adelante(); server.send(200, "text/plain", "OK"); });
  server.on("/B", []() { atras(); server.send(200, "text/plain", "OK"); });
  server.on("/L", []() { izquierda(); server.send(200, "text/plain", "OK"); });
  server.on("/R", []() { derecha(); server.send(200, "text/plain", "OK"); });
  server.on("/S", []() { detener(); server.send(200, "text/plain", "OK"); });

  server.on("/V", []() {
    if (server.hasArg("val")) {
      velocidad = constrain(server.arg("val").toInt(), 0, 255);
      if (!turboActivo) {
        analogWrite(ENA, velocidad);
        analogWrite(ENB, velocidad);
      }
    }
    server.send(200, "text/plain", "OK");
  });

  server.on("/T1", []() {
    turboActivo = true;
    analogWrite(ENA, vel());
    analogWrite(ENB, vel());
    server.send(200, "text/plain", "OK");
  });

  server.on("/T0", []() {
    turboActivo = false;
    analogWrite(ENA, vel());
    analogWrite(ENB, vel());
    server.send(200, "text/plain", "OK");
  });

  server.on("/D1", []() { driftActivo = true;  server.send(200, "text/plain", "OK"); });
  server.on("/D0", []() { driftActivo = false; server.send(200, "text/plain", "OK"); });

  server.on("/ping", []() { server.send(200, "text/plain", "pong"); });

  server.begin();
}

void loop() {
  server.handleClient();
}

void adelante() {
  int v = vel();
  analogWrite(ENA, v);
  analogWrite(ENB, v);
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void atras() {
  int v = vel();
  analogWrite(ENA, v);
  analogWrite(ENB, v);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void izquierda() {
  int v = vel();
  if (driftActivo) {
    // pulso de derrape: rueda izquierda en reversa breve, luego arco de giro
    analogWrite(ENA, v);
    analogWrite(ENB, v);
    digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH);
    digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
    delay(180);
    analogWrite(ENA, (int)(v * 0.4));
    digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  } else {
    analogWrite(ENA, v);
    analogWrite(ENB, v);
    digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH);
    digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
  }
}

void derecha() {
  int v = vel();
  if (driftActivo) {
    // pulso de derrape: rueda derecha en reversa breve, luego arco de giro
    analogWrite(ENA, v);
    analogWrite(ENB, v);
    digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH);
    delay(180);
    analogWrite(ENB, (int)(v * 0.4));
    digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
  } else {
    analogWrite(ENA, v);
    analogWrite(ENB, v);
    digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH);
  }
}

void detener() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}
