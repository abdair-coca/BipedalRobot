# Test 01 — MPU-6050 + balance sobre ruedas (TT motors)

## Objetivo

Validar, de forma aislada y sin depender de la mecanica del bipedo (que aun no esta lista), el loop completo de:
1. Lectura de IMU (MPU-6050).
2. Filtro de angulo (complementario).
3. Control PID de balance.
4. Actuacion sobre motores (L298N + TT motors).

Se arma un robot de 2 ruedas tipo pendulo invertido (self-balancing robot) usando hardware que **ya esta disponible** y que **no se va a usar en las piernas del bipedo** (ver `docs/04-riesgos-decisiones.md`, decision #1). Es la forma mas rapida y barata de probar que el sensor y el algoritmo de balance funcionan antes de gastar tiempo/plata en piernas si el approach de control tiene problemas.

## Controlador de este test: ESP8266 (Wemos D1 mini), no el ESP32

Estado actual del hardware: el **ESP32 DevKit tiene MicroPython** cargado, y el **Wemos D1 mini (ESP8266) tiene Arduino (C++)**. Este test se implementa en el **ESP8266 con Arduino**, para no depender de reflashear el ESP32.

**Nota**: si esta misma placa D1 mini es la que normalmente corre el firmware de Head Node del proyecto principal (OLED + mic + amp + servos pan/tilt), este test es un flash **temporal** — hay que reflashear el firmware original del Head Node al terminar. Los pines usados aca no coinciden con los del Head Node (ver `electronica/conexionado.md`) porque no corren al mismo tiempo.

## Por que este test primero

Es el test de mayor riesgo tecnico del proyecto entero: si el MPU-6050 (clon barato) tiene demasiado ruido/drift, o si el PID no logra estabilizar nada, mejor descubrirlo ahora, en una plataforma simple de 2 ruedas, que despues de meses de imprimir/armar piernas.

La logica de sensado/control probada aca (IMU + filtro + PID) es conceptualmente la misma que se documenta en `firmware/arquitectura-firmware.md` para el Motion Controller final — cambia el actuador (motores DC en vez de servos) y el microcontrolador (ESP8266 en este test vs. ESP32 en el diseño final).

## Hardware requerido

| Componente | Origen | Notas |
|---|---|---|
| Wemos D1 mini (ESP8266) | Ya disponible (BOM) | Controlador de este test |
| MPU-6050 | Ya disponible (BOM) | Montado rigido, eje alineado con la inclinacion del chasis |
| L298N driver | Ya disponible (BOM) | Reservado para pruebas, no va en piernas |
| TT motors x4 | Ya disponible (BOM) | 2 en paralelo por lado (izq/der) para mas torque, o 1 por lado si alcanza |
| Ruedas x2 (o x4 si van pareadas) | A conseguir si no hay | Diametro grande ayuda a la estabilidad (mas facil de balancear) |
| Chasis simple (carton/MDF/impreso) | A armar | Alto y angosto favorece el efecto pendulo invertido, mas facil de controlar que uno bajo y ancho |
| Bateria motores (6-12V segun specs TT motors) | Ver `electronica/presupuesto-energia.md` | Rail separado de logica, mismo criterio que el proyecto principal |
| Bateria/regulador logica ~5V (D1 mini acepta 5V por su regulador a bordo, o 3.3V directo) | Ver `electronica/presupuesto-energia.md` | Alimenta el D1 mini y el MPU-6050 |

## Nota sobre los "strapping pins" (D0/D3/D4/D8)

En teoria D0(GPIO16), D3(GPIO0), D4(GPIO2) y D8(GPIO15) son sensibles al boot del ESP8266 (si algo externo los fuerza a cierto nivel durante el arranque, la placa puede no bootear bien). En la practica, en esta placa especifica, D0/D3/D4 conectados directo al L298N (como entradas del L298N, que son de alta impedancia) **funcionan sin problema** — confirmado en banco de pruebas. Por eso el wiring final usa los 2 canales del L298N **independientes** (sin atarlos entre si), dejando el robot listo para un futuro test de giro/direccion sin tener que recablear nada. D8 queda libre.

Si en otra placa/otro L298N esto llegara a causar boot loops, la alternativa segura es atar ENA-ENB y IN1-IN3/IN2-IN4 entre si y controlar todo con 3 pines (D1/D2 I2C + D5 PWM + D6/D7 direccion), sacrificando la capacidad de girar.

## Wiring

### MPU-6050 (I2C)
| MPU-6050 | Wemos D1 mini |
|---|---|
| VCC | 3.3V |
| GND | GND |
| SDA | D2 (GPIO4) |
| SCL | D1 (GPIO5) |
| INT | No usado en este test |

### L298N (canales A y B independientes)
| L298N | Wemos D1 mini | Rol |
|---|---|---|
| ENA | D3 (GPIO0) | PWM canal A (rueda izquierda) |
| IN1 | D0 (GPIO16) | Direccion canal A |
| IN2 | D5 (GPIO14) | Direccion canal A |
| ENB | D4 (GPIO2) | PWM canal B (rueda derecha) |
| IN3 | D6 (GPIO12) | Direccion canal B |
| IN4 | D7 (GPIO13) | Direccion canal B |
| GND | GND comun con el D1 mini y la bateria de motores | |
| +12V (o voltaje de los TT motors) | Bateria motores (rail separado) | |
| 5V salida logica L298N | **No usar** para alimentar el D1 mini directo — usar rail regulado propio (ver `electronica/presupuesto-energia.md`) | |
| OUT1 + OUT2 | 2x TT motors lado izquierdo, en paralelo | |
| OUT3 + OUT4 | 2x TT motors lado derecho, en paralelo | |

D8 (GPIO15) queda libre en este wiring.

**GND comun obligatorio** entre bateria motores, bateria/regulador logica y el D1 mini, o el I2C y las lecturas van a fallar / comportarse erratico.

## Montaje fisico

- MPU-6050 fijo rigido al chasis (sin holgura), con el eje que mide "inclinacion adelante/atras" alineado con la direccion de rodado.
- Centro de masa del chasis lo mas alto posible respecto al eje de las ruedas ayuda a que el sistema sea mas facil de balancear al principio (mas inercia, cae mas lento) — se puede afinar despues.
- Dejar acceso facil al puerto USB del D1 mini para iterar rapido en la calibracion del PID.

## Como correr el test

1. En Arduino IDE, seleccionar board **"LOLIN(WEMOS) D1 R2 & mini"** (o "WeMos D1 R1", segun version exacta de la placa).
2. Flashear `balance_ruedas.ino`.
3. Con el robot **apoyado sobre un soporte** (sin tocar el piso con las ruedas, ej. sostenido en el aire o sobre un caballete), abrir el Monitor Serial a 115200 baudios.
4. Confirmar que se leen angulos de pitch estables y que cambian correctamente al inclinar el chasis a mano (probar ambos sentidos).
5. Dejar el robot quieto y plano unos segundos al arrancar — el codigo calibra el offset del giroscopo en frio (ver seccion "Calibracion" abajo).
6. Recien con la lectura de angulo validada, apoyar el robot en el piso, sostenido a mano, y soltar de a poco viendo si los motores reaccionan en la direccion correcta (si se inclina adelante, las ruedas deben girar hacia adelante para "perseguir" la caida, no al reves — si reaccionan al reves, invertir el signo de la correccion o el cableado de IN1/IN2 e IN3/IN4).
7. Ajustar constantes `KP`, `KI`, `KD` del PID (al inicio del archivo) de forma iterativa (ver "Tuning" abajo).

## Calibracion

- **Offset de giroscopo**: el codigo promedia N lecturas al arrancar con el robot quieto y plano, y resta ese offset en cada lectura subsiguiente. Si el robot no arranca plano y quieto, el offset queda mal y el angulo va a driftear.
- **Angulo neutral (`SETPOINT_ANGLE`)**: el angulo de pitch en el que el robot esta perfectamente balanceado depende de donde quedo montado el MPU-6050 fisicamente (raramente es exactamente 0°). Ajustar esta constante hasta que el robot "quiera quedarse quieto" en su punto de equilibrio real.

## Tuning del PID (orden recomendado)

1. Empezar con `KI = 0` y `KD = 0`, subir `KP` de a poco hasta que el robot reaccione a la inclinacion (aunque oscile fuerte) — confirma que la direccion de correccion es correcta.
2. Agregar `KD` de a poco para amortiguar la oscilacion (reduce el "temblor" rapido).
3. Agregar `KI` de a poco solo si el robot se estabiliza pero queda inclinado hacia un lado de forma sostenida (compensa el offset residual).
4. Si en cualquier punto el robot se descontrola cada vez mas rapido (en vez de estabilizarse), el signo de la correccion esta invertido — revisar cableado de IN1/IN2 e IN3/IN4 o el signo en el codigo, no seguir subiendo ganancias.

## Criterio de exito

- El robot se mantiene parado sobre sus 2 ruedas sin caerse por >15-20 segundos en piso plano.
- Se recupera de un empujon leve (unos cm de desplazamiento del pendulo) sin caerse.
- Las lecturas de IMU no muestran drift visible en el Monitor Serial durante ~1 minuto quieto.

No hace falta que camine ni se desplace — este test es solo de **balance estatico en el lugar**, igual que el Milestone M2 del proyecto principal pero en ruedas en vez de piernas.

## Troubleshooting

| Sintoma | Causa probable |
|---|---|
| D1 mini se reinicia solo al mover motores | Falta rail de energia separado (logica vs motores) o falta capacitor, ver `electronica/presupuesto-energia.md` |
| Angulo lee valores absurdos o saltos bruscos | GND no comun entre bateria motores y logica, o cableado I2C flojo |
| Angulo driftea lento con el robot quieto | Calibracion de offset de giroscopo mala (robot no estaba quieto/plano al arrancar) o filtro complementario con `ALPHA` mal ajustado |
| Robot se cae siempre para el mismo lado | `SETPOINT_ANGLE` mal calibrado, o motor de un lado mas debil/lento que el otro (revisar mecanicamente, no solo en software) |
| Robot oscila cada vez mas fuerte hasta caerse | Signo de correccion invertido, o `KP`/`KD` demasiado altos — bajar ganancias y volver a subir de a poco |
| No compila / `analogWriteRange` no reconocido | Confirmar que el board seleccionado en Arduino IDE es un ESP8266 (no AVR/ESP32) — esa funcion es especifica del core ESP8266 |
| Motor zumba fuerte / chillido audible | Normal en PWM de baja frecuencia (~1kHz default de `analogWrite` en ESP8266); se puede subir con `analogWriteFreq()` si molesta, con cuidado de no perder resolucion de PWM |
| D1 mini no bootea o queda en loop de reset al conectar el L298N | En esta placa D0/D3/D4 se confirmaron sin problema; si en la tuya da bootloop, pasar a la alternativa segura (atar ENA-ENB e IN1-IN3/IN2-IN4), ver seccion "Nota sobre los strapping pins" |

## Registro de resultados

Completar despues de correr el test (agregar filas segun iteraciones de tuning):

| Fecha | KP | KI | KD | Resultado | Notas |
|---|---|---|---|---|---|
| - | - | - | - | - | - |
