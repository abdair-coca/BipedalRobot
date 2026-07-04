/*
 * Test 01 - MPU-6050 + balance sobre ruedas (TT motors via L298N)
 *
 * Ver README.md de esta carpeta: wiring completo, calibracion, tuning de PID,
 * criterio de exito y troubleshooting.
 *
 * Board: Wemos D1 mini (ESP8266), Arduino core. Solo depende de Wire.h -- el
 * MPU6050 se lee por registro crudo (sin libreria externa) para mantener el
 * test autocontenido.
 *
 * IMPORTANTE: este .ino es un flash TEMPORAL para el test. Si esta misma placa
 * normalmente corre el firmware de Head Node (OLED/mic/servos pan-tilt), hay
 * que reflashear ese firmware original al terminar -- los pines de este test
 * no son compatibles con esa asignacion (ver electronica/conexionado.md).
 */

#include <Wire.h>

// ---------- Pines (Wemos D1 mini) ----------
// Los 2 canales del L298N van cableados independientes (no atados entre si):
// se probo en esta placa que D0/D3/D4 (strapping pins en teoria sensibles al
// boot) funcionan sin problema como salidas digitales una vez arrancado el
// D1 mini. Dejar esto asi habilita un test futuro de giro/direccion sin
// recablear nada.
#define MPU_ADDR      0x68
#define SDA_PIN       D2   // GPIO4
#define SCL_PIN       D1   // GPIO5

#define ENA_PIN       D3   // GPIO0  -- PWM canal A (rueda izquierda)
#define IN1_PIN       D0   // GPIO16 -- direccion canal A (solo digitalWrite, GPIO16 no soporta PWM)
#define IN2_PIN       D5   // GPIO14 -- direccion canal A
#define ENB_PIN       D4   // GPIO2  -- PWM canal B (rueda derecha)
#define IN3_PIN       D6   // GPIO12 -- direccion canal B
#define IN4_PIN       D7   // GPIO13 -- direccion canal B

// ---------- Filtro complementario ----------
#define ALPHA         0.98f   // peso gyro vs accel; 0.98 es el valor tipico para MPU6050
#define LOOP_DT_MS    5       // 5ms -> ~200Hz, respuesta rapida necesaria para balance

// ---------- PID (arrancar todo en 0 y subir de a poco, ver README seccion "Tuning") ----------
float KP = 15.0f;
float KI = 0.0f;
float KD = 5.0f;

// Angulo real de equilibrio del robot. Depende de como quedo montado el MPU6050
// fisicamente -- rara vez es 0 exacto. Calibrar en campo (ver README "Calibracion").
float SETPOINT_ANGLE = 2.70f;

// Si se supera esta inclinacion respecto al setpoint, se asume caido: corta motores
// para no forzar los TT motors/engranajes contra el piso.
#define FALL_THRESHOLD_DEG 35.0f

// ---------- Estado global ----------
float pitch = 0.0f;
float gyroOffsetY = 0.0f;
float integral = 0.0f;
float lastError = 0.0f;
unsigned long lastLoopMs = 0;

// ---------- MPU6050: acceso por registro crudo ----------
void mpuWrite(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

void mpuInit() {
  mpuWrite(0x6B, 0x00); // PWR_MGMT_1: saca al MPU6050 de sleep mode (default al power-on)
}

// Lee accel(X,Y,Z) + gyro(X,Y,Z) crudos a partir de 0x3B (14 bytes, con temp en el medio)
void mpuReadRaw(int16_t &ax, int16_t &ay, int16_t &az, int16_t &gx, int16_t &gy, int16_t &gz) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);

  ax = (Wire.read() << 8) | Wire.read();
  ay = (Wire.read() << 8) | Wire.read();
  az = (Wire.read() << 8) | Wire.read();
  Wire.read(); Wire.read(); // temperatura, no se usa en este test
  gx = (Wire.read() << 8) | Wire.read();
  gy = (Wire.read() << 8) | Wire.read();
  gz = (Wire.read() << 8) | Wire.read();
}

// Promedia el giroscopo con el robot quieto y plano para restar su offset de reposo
// (todo MPU6050, sobre todo los clones baratos, tiene un offset de fabrica distinto de cero).
void calibrateGyro() {
  const int N = 500;
  long sum = 0;
  int16_t ax, ay, az, gx, gy, gz;
  for (int i = 0; i < N; i++) {
    mpuReadRaw(ax, ay, az, gx, gy, gz);
    sum += gy;
    delay(2);
  }
  gyroOffsetY = (sum / (float)N) / 131.0f; // 131 LSB/(deg/s), rango default +-250 deg/s
}

// ---------- Motores ----------
void setupMotors() {
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);
  pinMode(IN3_PIN, OUTPUT);
  pinMode(IN4_PIN, OUTPUT);
  analogWriteRange(255); // ESP8266 usa 0-1023 por default; lo bajamos a 0-255
                         // para que coincida con las constantes del PID/anti-windup.
}

// Controla un canal del L298N (izquierda o derecha) de forma independiente.
void setMotorChannel(int enaPin, int in1Pin, int in2Pin, float speed) {
  bool forward = speed >= 0;
  digitalWrite(in1Pin, forward ? HIGH : LOW);
  digitalWrite(in2Pin, forward ? LOW : HIGH);
  analogWrite(enaPin, (int)fabs(speed));
}

// speed: -255..255. Signo = direccion, magnitud = PWM.
// Ambos canales reciben el mismo valor: este test es solo balance en el lugar.
// Como los canales estan cableados independientes, un test futuro de giro
// puede mandarles valores distintos sin tocar el hardware.
void setMotors(float speed) {
  speed = constrain(speed, -255.0f, 255.0f);
  setMotorChannel(ENA_PIN, IN1_PIN, IN2_PIN, speed); // izquierda
  setMotorChannel(ENB_PIN, IN3_PIN, IN4_PIN, speed); // derecha
}

void stopMotors() {
  analogWrite(ENA_PIN, 0);
  analogWrite(ENB_PIN, 0);
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  digitalWrite(IN3_PIN, LOW);
  digitalWrite(IN4_PIN, LOW);
}

// ---------- Setup ----------
void setup() {
  Serial.begin(115200);
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);

  mpuInit();
  setupMotors();
  stopMotors();

  Serial.println("Calibrando giroscopo -- mantener el robot quieto y plano...");
  calibrateGyro();
  Serial.println("Calibracion lista. Arrancando loop de balance.");

  lastLoopMs = millis();
}

// ---------- Loop ----------
void loop() {
  unsigned long now = millis();
  if (now - lastLoopMs < LOOP_DT_MS) return;
  float dt = (now - lastLoopMs) / 1000.0f;
  lastLoopMs = now;

  int16_t ax, ay, az, gx, gy, gz;
  mpuReadRaw(ax, ay, az, gx, gy, gz);

  // Angulo desde el acelerometro: referencia absoluta (no driftea) pero ruidosa
  // por vibracion de motores. Formula asume el MPU6050 montado con Z hacia arriba;
  // si la inclinacion sale invertida, revisar orientacion fisica del sensor.
  float accelPitch = atan2((float)ax, sqrt((float)ay * ay + (float)az * az)) * 180.0f / PI;

  // Velocidad angular desde el giroscopo: rapida y sin ruido, pero acumula drift.
  float gyroRateY = (gy / 131.0f) - gyroOffsetY;

  // Filtro complementario: fusiona ambas fuentes para el mejor de los dos mundos.
  pitch = ALPHA * (pitch + gyroRateY * dt) + (1.0f - ALPHA) * accelPitch;

  // Seguridad: si se paso de angulo, esta caido -> corta motores y resetea el PID
  // para no arrancar de un integral acumulado cuando se lo vuelva a parar.
  if (fabs(pitch - SETPOINT_ANGLE) > FALL_THRESHOLD_DEG) {
    stopMotors();
    integral = 0;
    lastError = 0;
    Serial.println("CAIDO - motores cortados");
    return;
  }

  // PID de balance
  float error = pitch - SETPOINT_ANGLE;
  integral += error * dt;
  integral = constrain(integral, -255.0f, 255.0f); // anti-windup simple
  float derivative = (error - lastError) / dt;
  lastError = error;

  float output = KP * error + KI * integral + KD * derivative;
  setMotors(output);

  // Debug: angulo y salida PID -- abrir con Serial Plotter para ver las curvas en vivo
  Serial.print(pitch);
  Serial.print("\t");
  Serial.println(output);
}
