/*
 * Test 02 - Calibracion en vivo del PID de balance (web, sin cable)
 *
 * Ver README.md de esta carpeta para instrucciones de conexion, ejemplos de
 * sesion de tuning y notas de seguridad.
 *
 * Mismo hardware que Test 01 (tests/test-01-mpu6050-balance-ruedas/):
 * Wemos D1 mini + MPU-6050 + L298N + TT motors, mismo wiring.
 *
 * El D1 mini crea su propia red WiFi (ver WIFI_SSID/WIFI_PASSWORD abajo) y
 * sirve una pagina web de control en http://192.168.4.1 -- conectate a esa
 * red desde el celular o la PC y abrila en el navegador. El Monitor Serial
 * (USB, 115200 baudios) sigue funcionando en paralelo con los mismos
 * comandos de texto, util para debug con cable durante el desarrollo:
 *   p<valor>  i<valor>  d<valor>  s<valor>  z<valor>  f<valor>
 *   e (armar)  x (parar)  c (recalibrar)  w (guardar EEPROM)  g (estado)  h (ayuda)
 */

#include <Wire.h>
#include <EEPROM.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

// ---------- Pines (Wemos D1 mini) -- identico a Test 01 ----------
#define MPU_ADDR      0x68
#define SDA_PIN       D2   // GPIO4
#define SCL_PIN       D1   // GPIO5

#define ENA_PIN       D3   // GPIO0  -- PWM canal A (rueda izquierda)
#define IN1_PIN       D0   // GPIO16 -- direccion canal A
#define IN2_PIN       D5   // GPIO14 -- direccion canal A
#define ENB_PIN       D4   // GPIO2  -- PWM canal B (rueda derecha)
#define IN3_PIN       D6   // GPIO12 -- direccion canal B
#define IN4_PIN       D7   // GPIO13 -- direccion canal B

// ---------- WiFi (AP propio -- no depende de router de casa) ----------
const char* WIFI_SSID     = "BalanceBot";
const char* WIFI_PASSWORD = "equilibrio"; // minimo 8 caracteres

ESP8266WebServer server(80);
String serialLineBuffer = "";

// ---------- Filtro complementario ----------
#define ALPHA         0.98f
#define LOOP_DT_MS    5

// ---------- EEPROM ----------
// Direcciones: 0=KP, 4=KI, 8=KD, 12=SETPOINT_ANGLE, 20=MOTOR_DEADZONE (floats, 4 bytes c/u), 16=magic byte
#define EEPROM_SIZE   32
#define EEPROM_MAGIC  0xA5

// ---------- PID (defaults del codigo -- se pisan si hay valores guardados en EEPROM) ----------
float KP = 0.0f;
float KI = 0.0f;
float KD = 1.0f;
float SETPOINT_ANGLE = 2.75f;

#define FALL_THRESHOLD_DEG 35.0f

// ---------- Estado global ----------
float pitch = 0.0f;
float lastOutput = 0.0f;
float gyroOffsetY = 0.0f;
float integral = 0.0f;
float lastError = 0.0f;
float filteredDerivative = 0.0f;
float DERIV_FILTER = 0.7f; // 0-1: mas alto = mas suave/lento, menos ruido pero mas retraso
unsigned long lastLoopMs = 0;
bool motorsEnabled = false; // arranca DESARMADO por seguridad

// ---------- MPU6050: acceso por registro crudo ----------
void mpuWrite(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

void mpuInit() {
  mpuWrite(0x6B, 0x00);
}

void mpuReadRaw(int16_t &ax, int16_t &ay, int16_t &az, int16_t &gx, int16_t &gy, int16_t &gz) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);

  ax = (Wire.read() << 8) | Wire.read();
  ay = (Wire.read() << 8) | Wire.read();
  az = (Wire.read() << 8) | Wire.read();
  Wire.read(); Wire.read();
  gx = (Wire.read() << 8) | Wire.read();
  gy = (Wire.read() << 8) | Wire.read();
  gz = (Wire.read() << 8) | Wire.read();
}

void calibrateGyro() {
  const int N = 500;
  long sum = 0;
  int16_t ax, ay, az, gx, gy, gz;
  for (int i = 0; i < N; i++) {
    mpuReadRaw(ax, ay, az, gx, gy, gz);
    sum += gy;
    delay(2);
  }
  gyroOffsetY = (sum / (float)N) / 131.0f;
}

// ---------- Motores ----------
void setupMotors() {
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);
  pinMode(IN3_PIN, OUTPUT);
  pinMode(IN4_PIN, OUTPUT);
  analogWriteRange(255);
}

// Por debajo de MOTOR_DEADZONE el TT motor no vence su friccion estatica y
// no gira nada -- un error chico produce un PWM chico que se pierde sin
// mover la rueda, dejando el robot caer libre hasta que el error crece
// demasiado. Compensamos: cualquier salida distinta de cero se "levanta"
// al minimo necesario para que la rueda efectivamente gire.
float MOTOR_DEADZONE = 60.0f;

void setMotorChannel(int enaPin, int in1Pin, int in2Pin, float speed) {
  bool forward = speed >= 0;
  digitalWrite(in1Pin, forward ? HIGH : LOW);
  digitalWrite(in2Pin, forward ? LOW : HIGH);

  int duty = (int)fabs(speed);
  if (duty > 0 && duty < MOTOR_DEADZONE) duty = (int)MOTOR_DEADZONE;
  analogWrite(enaPin, duty);
}

void setMotors(float speed) {
  speed = constrain(speed, -255.0f, 255.0f);
  setMotorChannel(ENA_PIN, IN1_PIN, IN2_PIN, speed);
  setMotorChannel(ENB_PIN, IN3_PIN, IN4_PIN, speed);
}

void stopMotors() {
  analogWrite(ENA_PIN, 0);
  analogWrite(ENB_PIN, 0);
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  digitalWrite(IN3_PIN, LOW);
  digitalWrite(IN4_PIN, LOW);
}

// ---------- EEPROM ----------
void saveToEEPROM() {
  EEPROM.put(0, KP);
  EEPROM.put(4, KI);
  EEPROM.put(8, KD);
  EEPROM.put(12, SETPOINT_ANGLE);
  EEPROM.put(20, MOTOR_DEADZONE);
  EEPROM.write(16, EEPROM_MAGIC);
  EEPROM.commit();
}

void loadFromEEPROMIfPresent() {
  if (EEPROM.read(16) != EEPROM_MAGIC) {
    Serial.println(F("EEPROM vacia -- usando valores default del codigo."));
    return;
  }
  EEPROM.get(0, KP);
  EEPROM.get(4, KI);
  EEPROM.get(8, KD);
  EEPROM.get(12, SETPOINT_ANGLE);
  EEPROM.get(20, MOTOR_DEADZONE);
  Serial.println(F("Valores cargados desde EEPROM."));
}

// ---------- Comandos por Serial (texto, igual que antes -- util con cable) ----------
void printHelp(Print &out) {
  out.println(F("--- Comandos ---"));
  out.println(F("p<val>  setear KP     (ej. p6.5)"));
  out.println(F("i<val>  setear KI     (ej. i0.1)"));
  out.println(F("d<val>  setear KD     (ej. d0.3)"));
  out.println(F("s<val>  setear SETPOINT_ANGLE (ej. s-1.2)"));
  out.println(F("e       armar motores"));
  out.println(F("x       desarmar motores (parada de emergencia)"));
  out.println(F("c       recalibrar giroscopo (robot quieto y plano)"));
  out.println(F("w       guardar gains actuales en EEPROM"));
  out.println(F("z<val>  setear zona muerta del motor (ej. z60)"));
  out.println(F("f<val>  setear suavizado de la derivada, 0-0.99 (ej. f0.7)"));
  out.println(F("g       imprimir estado actual"));
  out.println(F("h / ?   esta ayuda"));
}

void printStatus(Print &out) {
  out.print(F("KP=")); out.print(KP);
  out.print(F(" KI=")); out.print(KI);
  out.print(F(" KD=")); out.print(KD);
  out.print(F(" SETPOINT=")); out.print(SETPOINT_ANGLE);
  out.print(F(" DEADZONE=")); out.print(MOTOR_DEADZONE);
  out.print(F(" DERIV_FILTER=")); out.print(DERIV_FILTER);
  out.print(F(" pitch=")); out.print(pitch);
  out.print(F(" motores=")); out.println(motorsEnabled ? "ARMADOS" : "desarmados");
}

void armMotors() {
  motorsEnabled = true;
  integral = 0; lastError = 0; // arranca limpio, sin arrastrar error de cuando estaba desarmado
}

void processLine(const String &line, Print &out) {
  if (line.length() == 0) return;

  char cmd = line.charAt(0);
  float val = line.substring(1).toFloat();

  switch (cmd) {
    case 'p': KP = val; out.print(F("KP=")); out.println(KP); break;
    case 'i': KI = val; out.print(F("KI=")); out.println(KI); break;
    case 'd': KD = val; out.print(F("KD=")); out.println(KD); break;
    case 's': SETPOINT_ANGLE = val; out.print(F("SETPOINT_ANGLE=")); out.println(SETPOINT_ANGLE); break;
    case 'z': MOTOR_DEADZONE = val; out.print(F("MOTOR_DEADZONE=")); out.println(MOTOR_DEADZONE); break;
    case 'f': DERIV_FILTER = constrain(val, 0.0f, 0.99f); out.print(F("DERIV_FILTER=")); out.println(DERIV_FILTER); break;
    case 'e': armMotors(); out.println(F("Motores ARMADOS")); break;
    case 'x': motorsEnabled = false; stopMotors(); out.println(F("Motores DETENIDOS")); break;
    case 'c':
      out.println(F("Recalibrando giroscopo -- mantener quieto y plano..."));
      calibrateGyro();
      out.println(F("Listo."));
      break;
    case 'w': saveToEEPROM(); out.println(F("Guardado en EEPROM.")); break;
    case 'g': printStatus(out); break;
    case 'h':
    case '?': printHelp(out); break;
    default: out.println(F("Comando desconocido. Mandar 'h' para ayuda.")); break;
  }
}

// Lectura no bloqueante byte a byte: una lectura bloqueante (readStringUntil)
// congelaria el loop de balance de 200Hz mientras espera el resto de la linea.
void pollSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      serialLineBuffer.trim();
      processLine(serialLineBuffer, Serial);
      serialLineBuffer = "";
    } else if (c != '\r') {
      serialLineBuffer += c;
    }
  }
}

// ---------- Pagina web ----------
const char PAGINA[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Balance PID Tuner</title>
<style>
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  body {
    margin: 0; padding: 16px;
    font-family: 'Segoe UI', Arial, sans-serif;
    background: radial-gradient(circle at top, #1e2530, #0d1117);
    color: #fff;
    display: flex; flex-direction: column; align-items: center;
  }
  h1 { font-size: 20px; letter-spacing: 1px; margin: 4px 0 16px;
       background: linear-gradient(90deg, #4CAF50, #2196F3);
       -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .panel { background: #161b22; border-radius: 16px; padding: 18px;
           box-shadow: 0 8px 24px rgba(0,0,0,0.5); width: 100%; max-width: 380px; margin-bottom: 14px; }
  .status-row { display: flex; justify-content: space-between; font-size: 14px; color: #ccc; padding: 4px 0; }
  .status-row span.val { color: #fff; font-weight: 600; }
  #estadoTxt.armado { color: #4CAF50; }
  #estadoTxt.desarmado { color: #ffa726; }
  #estadoTxt.caido { color: #e53935; }
  .campo { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  .campo label { font-size: 13px; color: #ccc; }
  .campo input { width: 100px; padding: 6px; border-radius: 8px; border: 1px solid #333;
                 background: #0d1117; color: #fff; font-size: 14px; text-align: right; }
  button { border: none; border-radius: 12px; padding: 12px; font-size: 14px; font-weight: 600;
           color: #fff; width: 100%; margin-bottom: 8px; cursor: pointer;
           background: linear-gradient(145deg, #2b3542, #1c232c);
           box-shadow: 0 4px 10px rgba(0,0,0,0.4); }
  button:active { transform: scale(0.97); }
  #btnAplicar { background: linear-gradient(145deg, #2196F3, #1565C0); }
  #btnArmar { background: linear-gradient(145deg, #4CAF50, #2e7d32); }
  #btnParar { background: linear-gradient(145deg, #e53935, #b71c1c); font-size: 16px; }
  .fila2 { display: flex; gap: 8px; }
  .fila2 button { flex: 1; }
</style>
</head>
<body>

<h1>BALANCE PID TUNER</h1>

<div class="panel">
  <div class="status-row"><span>Angulo</span><span class="val" id="pitchTxt">--</span></div>
  <div class="status-row"><span>Output motor</span><span class="val" id="outputTxt">--</span></div>
  <div class="status-row"><span>Estado</span><span class="val" id="estadoTxt">--</span></div>
</div>

<div class="panel">
  <div class="campo"><label>KP</label><input id="p" type="number" step="0.1"></div>
  <div class="campo"><label>KI</label><input id="i" type="number" step="0.01"></div>
  <div class="campo"><label>KD</label><input id="d" type="number" step="0.1"></div>
  <div class="campo"><label>Setpoint (grados)</label><input id="s" type="number" step="0.1"></div>
  <div class="campo"><label>Zona muerta motor</label><input id="z" type="number" step="1"></div>
  <div class="campo"><label>Filtro derivada</label><input id="f" type="number" step="0.05" min="0" max="0.99"></div>
  <button id="btnAplicar" onclick="aplicar()">APLICAR</button>
</div>

<div class="panel">
  <button id="btnParar" onclick="accion('/stop')">PARAR (emergencia)</button>
  <div class="fila2">
    <button id="btnArmar" onclick="accion('/arm')">ARMAR</button>
    <button onclick="accion('/calibrate')">Recalibrar</button>
  </div>
  <button onclick="accion('/save')">Guardar en EEPROM</button>
</div>

<script>
function aplicar() {
  var ids = ['p','i','d','s','z','f'];
  var qs = ids.map(function(k){ return k + '=' + document.getElementById(k).value; }).join('&');
  fetch('/set?' + qs).catch(function(){});
}
function accion(path) {
  fetch(path).catch(function(){});
}

var camposCargados = false;

function actualizar() {
  fetch('/status').then(function(r){ return r.json(); }).then(function(j){
    document.getElementById('pitchTxt').textContent = j.pitch.toFixed(2) + '°';
    document.getElementById('outputTxt').textContent = j.output.toFixed(0);
    var estado = document.getElementById('estadoTxt');
    if (j.fallen) { estado.textContent = 'CAIDO'; estado.className = 'caido'; }
    else if (j.armed) { estado.textContent = 'ARMADO'; estado.className = 'armado'; }
    else { estado.textContent = 'desarmado'; estado.className = 'desarmado'; }

    // Los inputs solo se sincronizan una vez al cargar, para no pisar
    // mientras el usuario esta escribiendo un valor nuevo.
    if (!camposCargados) {
      document.getElementById('p').value = j.kp;
      document.getElementById('i').value = j.ki;
      document.getElementById('d').value = j.kd;
      document.getElementById('s').value = j.setpoint;
      document.getElementById('z').value = j.deadzone;
      document.getElementById('f').value = j.derivFilter;
      camposCargados = true;
    }
  }).catch(function(){});
}
actualizar();
setInterval(actualizar, 250);
</script>
</body>
</html>
)rawliteral";

// ---------- Handlers web ----------
void handleRoot() {
  server.send(200, "text/html", PAGINA);
}

void handleSet() {
  if (server.hasArg("p")) KP = server.arg("p").toFloat();
  if (server.hasArg("i")) KI = server.arg("i").toFloat();
  if (server.hasArg("d")) KD = server.arg("d").toFloat();
  if (server.hasArg("s")) SETPOINT_ANGLE = server.arg("s").toFloat();
  if (server.hasArg("z")) MOTOR_DEADZONE = server.arg("z").toFloat();
  if (server.hasArg("f")) DERIV_FILTER = constrain(server.arg("f").toFloat(), 0.0f, 0.99f);
  server.send(200, "text/plain", "OK");
}

void handleArm() {
  armMotors();
  server.send(200, "text/plain", "OK");
}

void handleStop() {
  motorsEnabled = false;
  stopMotors();
  server.send(200, "text/plain", "OK");
}

void handleCalibrate() {
  calibrateGyro();
  server.send(200, "text/plain", "OK");
}

void handleSave() {
  saveToEEPROM();
  server.send(200, "text/plain", "OK");
}

void handleStatus() {
  bool fallen = fabs(pitch - SETPOINT_ANGLE) > FALL_THRESHOLD_DEG;
  String json = "{";
  json += "\"pitch\":" + String(pitch, 2) + ",";
  json += "\"output\":" + String(lastOutput, 1) + ",";
  json += "\"armed\":" + String(motorsEnabled ? "true" : "false") + ",";
  json += "\"fallen\":" + String(fallen ? "true" : "false") + ",";
  json += "\"kp\":" + String(KP, 3) + ",";
  json += "\"ki\":" + String(KI, 3) + ",";
  json += "\"kd\":" + String(KD, 3) + ",";
  json += "\"setpoint\":" + String(SETPOINT_ANGLE, 2) + ",";
  json += "\"deadzone\":" + String(MOTOR_DEADZONE, 0) + ",";
  json += "\"derivFilter\":" + String(DERIV_FILTER, 2);
  json += "}";
  server.send(200, "application/json", json);
}

// ---------- Setup ----------
void setup() {
  Serial.begin(115200);
  delay(200);
  EEPROM.begin(EEPROM_SIZE);

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);

  mpuInit();
  setupMotors();
  stopMotors();

  loadFromEEPROMIfPresent();

  Serial.println(F("Calibrando giroscopo -- mantener el robot quieto y plano..."));
  calibrateGyro();
  Serial.println(F("Listo. Motores DESARMADOS."));
  printStatus(Serial);

  WiFi.mode(WIFI_AP);
  WiFi.softAP(WIFI_SSID, WIFI_PASSWORD);
  Serial.print(F("WiFi AP '")); Serial.print(WIFI_SSID); Serial.println(F("' activa."));
  Serial.print(F("Abrir en el navegador: http://")); Serial.println(WiFi.softAPIP());

  server.on("/", handleRoot);
  server.on("/status", handleStatus);
  server.on("/set", handleSet);
  server.on("/arm", handleArm);
  server.on("/stop", handleStop);
  server.on("/calibrate", handleCalibrate);
  server.on("/save", handleSave);
  server.begin();

  lastLoopMs = millis();
}

// ---------- Loop ----------
void loop() {
  pollSerial();
  server.handleClient();

  unsigned long now = millis();
  if (now - lastLoopMs < LOOP_DT_MS) return;
  float dt = (now - lastLoopMs) / 1000.0f;
  lastLoopMs = now;

  int16_t ax, ay, az, gx, gy, gz;
  mpuReadRaw(ax, ay, az, gx, gy, gz);

  float accelPitch = atan2((float)ax, sqrt((float)ay * ay + (float)az * az)) * 180.0f / PI;
  float gyroRateY = (gy / 131.0f) - gyroOffsetY;
  pitch = ALPHA * (pitch + gyroRateY * dt) + (1.0f - ALPHA) * accelPitch;

  bool fallen = fabs(pitch - SETPOINT_ANGLE) > FALL_THRESHOLD_DEG;
  float output = 0.0f;

  if (fallen) {
    stopMotors();
    integral = 0;
    lastError = 0;
  } else if (motorsEnabled) {
    float error = pitch - SETPOINT_ANGLE;
    integral += error * dt;
    integral = constrain(integral, -255.0f, 255.0f);
    float rawDerivative = (error - lastError) / dt;
    lastError = error;
    // Derivada cruda amplifica ruido del sensor -- eso hace que KD reaccione
    // de forma erratica y empeora el rebote en vez de amortiguarlo. Se suaviza
    // con un filtro exponencial simple antes de usarla.
    filteredDerivative = DERIV_FILTER * filteredDerivative + (1.0f - DERIV_FILTER) * rawDerivative;

    output = constrain(KP * error + KI * integral + KD * filteredDerivative, -255.0f, 255.0f);
    setMotors(output);
  } else {
    stopMotors();
  }

  lastOutput = output;
}
