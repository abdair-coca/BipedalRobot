# Test 02 — Calibracion en vivo del PID de balance

## Objetivo

Ajustar `KP`, `KI`, `KD` y `SETPOINT_ANGLE` del balance sobre ruedas **sin reflashear** cada vez que se cambia un valor. Es la continuacion natural de [Test 01](../test-01-mpu6050-balance-ruedas/) una vez que el sentido de correccion ya esta confirmado — acá se hace el ajuste fino real.

Mismo hardware y mismo wiring que Test 01 (ver esa carpeta para wiring completo). Este test es **solo firmware distinto**: sirve una pagina web de control (sin cable) y ademas acepta los mismos comandos por Serial, mas persistencia en EEPROM para no perder los valores encontrados al reiniciar.

## Panel web (sin cable, recomendado para probar en el piso)

El cable USB tira del robot justo cuando mas molesta (mientras intenta corregir el balance). El D1 mini crea su propia red WiFi y sirve una pagina de control — no depende de un cable ni de la red de casa:

1. Conectate a la red WiFi `BalanceBot` (contraseña `equilibrio`, definidas al principio del `.ino`, cambialas si queres) desde el celular o la PC.
2. Abrí `http://192.168.4.1` en el navegador.
3. La pagina muestra en vivo el angulo, la salida al motor y el estado (armado/desarmado/caido), con campos para KP/KI/KD/Setpoint/Zona muerta/Filtro derivada y botones ARMAR / PARAR / Recalibrar / Guardar en EEPROM.
4. Cambiar un campo y tocar **APLICAR** manda todos los valores juntos. **PARAR** es el boton grande rojo — parada de emergencia, no corta la placa ni pierde valores.

El Monitor Serial sigue funcionando en paralelo con los mismos comandos de texto (`p6.5`, `e`, `x`, etc. — ver tabla abajo), util para debug con cable durante el desarrollo o para ver el arranque/IP antes de que el celular se conecte.

## Por que separado de Test 01

Test 01 sirve para confirmar que sensor+filtro+sentido de correccion funcionan (ya lo validaron). A partir de ahi, encontrar los valores finales de PID es un proceso iterativo de prueba y error — reflashear por cada cambio de un numero es lento y ademas cada reset reinicia el robot fisicamente (hay que levantarlo, sostenerlo, etc). Este test elimina esa friccion.

## Protocolo de comandos (Monitor Serial, 115200 baudios, terminar cada linea con Enter)

| Comando | Efecto |
|---|---|
| `p<valor>` | Setea KP. Ej: `p6.5` |
| `i<valor>` | Setea KI. Ej: `i0.1` |
| `d<valor>` | Setea KD. Ej: `d0.3` |
| `s<valor>` | Setea SETPOINT_ANGLE. Ej: `s-1.2` |
| `e` | **Arma** los motores (empiezan a corregir con los gains actuales) |
| `x` | **Desarma** los motores — parada de emergencia, no corta la placa ni pierde los valores |
| `c` | Recalibra el offset del giroscopo (robot quieto y plano en ese momento) |
| `z<valor>` | Setea la zona muerta del motor (PWM minimo para que la rueda gire). Ej: `z60` |
| `f<valor>` | Setea el suavizado de la derivada, 0-0.99 (mas alto = mas suave/lento). Ej: `f0.7` |
| `w` | Guarda KP/KI/KD/SETPOINT_ANGLE/DEADZONE actuales en EEPROM (sobreviven a reinicios/reflasheos) |
| `g` | Imprime estado actual: gains, deadzone, angulo, armado/desarmado |
| `h` o `?` | Imprime esta ayuda |

El robot **arranca siempre desarmado** (motores quietos) al bootear, aunque haya valores guardados en EEPROM — hay que mandar `e` a proposito cada vez para que empiece a corregir. Esto es intencional: evita que el robot salga andando solo apenas se le da alimentacion.

## Como correr el test

1. Flashear `calibracion_pid.ino` (una sola vez — de ahi en mas no hace falta volver a subir nada para tunear). Necesita las librerias `ESP8266WiFi` y `ESP8266WebServer` (vienen incluidas con el core ESP8266 de Arduino, no hay que instalar nada aparte).
2. Abrir Monitor Serial a 115200 baudios (con cable, para ver el arranque) — ahi aparece la IP para el panel web.
3. Al bootear, el sketch calibra el giroscopo (robot quieto y plano) e imprime el estado inicial.
4. Conectate a la red `BalanceBot` desde el celular/PC y abrí `http://192.168.4.1` — de ahi en mas ya podes desconectar el cable USB.
5. Con el robot **sostenido en un soporte** (no en el piso todavia), tocar **ARMAR** y probar el sentido de correccion (ya validado en Test 01, pero confirmar de nuevo si cambiaron algo del hardware).
6. Ir ajustando los campos y tocando **APLICAR**, observando angulo/output que se actualiza en vivo.
7. Recien cuando el robot se sostenga bien sostenido/soltado con cuidado en la mano, probar en el piso — ahora sin cable de por medio.
8. Cuando encuentres valores que funcionan, tocar **Guardar en EEPROM**.

## Ejemplo de sesion de tuning

```
> g
KP=6.00 KI=0.00 KD=0.00 SETPOINT=0.00 pitch=0.42 motores=desarmados

> e
Motores ARMADOS

(se prueba, tiembla mucho con KP=6, se baja)
> p4.0
KP=4.00

(se prueba, reacciona pero lento, se sube un poco)
> p5.0
KP=5.00

(se agrega amortiguacion)
> d0.2
KD=0.20

(se calibra el punto de equilibrio real sosteniendolo derecho a mano y mirando el angulo que marca ahi)
> s-1.35
SETPOINT_ANGLE=-1.35

(se prueba en el piso, se banca solo unos segundos pero se va inclinando de a poco para un lado)
> i0.08
KI=0.08

(anda bien, se guarda)
> w
Guardado en EEPROM.
```

## Notas de seguridad

- El robot arranca **desarmado**: siempre `e` antes de esperar reaccion.
- `x` corta motores al instante sin resetear la placa ni perder los valores probados — usarlo como boton de panico si algo se descontrola.
- Deteccion de caida (>35° de inclinacion respecto al setpoint) sigue activa igual que en Test 01, corta motores automaticamente sin importar el estado de armado.
- Si el robot arranca con valores guardados en EEPROM que resultan ser malos (oscila fuerte apenas armas), mandar `x` inmediatamente y volver a ajustar antes de rearmar.

## Zona muerta del motor (MOTOR_DEADZONE)

Los TT motors (gearbox + friccion estatica) no giran con cualquier PWM chico — por debajo de cierto valor el motor recibe señal pero no se mueve. Si el PID pide una correccion menor a ese umbral, el robot cae libre sin que el motor reaccione, hasta que el error crece lo suficiente — ahi el motor arranca de golpe con overshoot. Esto produce oscilaciones grandes en vez de correcciones finas.

El firmware compensa esto: cualquier salida de PID distinta de cero se "levanta" como minimo a `MOTOR_DEADZONE` antes de mandarla al motor.

### Como calibrar MOTOR_DEADZONE

1. Con el robot desarmado (`x`) y las ruedas en el aire (sin tocar el piso), mandar `p0 i0 d0` para anular el PID.
2. Inclinar el chasis un poco para generar un error chico y armar (`e`) — o mas simple, subir manualmente el valor con pruebas de `p` bajito.
3. Alternativa directa: usar el codigo de Test 01 o un sketch chico aparte para probar `analogWrite` directo en un canal con valores crecientes (30, 40, 50, 60...) y ver a partir de cual valor la rueda arranca a girar de forma visible. Ese valor (con un margen, +10) es tu `MOTOR_DEADZONE`.
4. Setealo con `z<valor>` (default en el codigo: 60) y ajustar por prueba y error si las ruedas siguen sin reaccionar a errores chicos, o si arrancan demasiado bruscas.

## Si el robot sobrecorrige (rebota de un lado al otro sin asentarse)

Sintoma: las ruedas reaccionan muy fuerte/rapido, se pasa de largo, corrige para el otro lado con la misma fuerza, nunca se estabiliza. Esto es sobrecorreccion clasica (KP efectivo demasiado alto para el sistema), no limite fisico — si viste proyectos con el mismo hardware que si balancean, confirma que es de tuning.

**Reiniciar el tuning desde abajo, no seguir desde 25-35:**

1. `x` para desarmar. `p2 i0 d0` — volver a empezar bajo, ganancias que ya probaste (20-35) muy probablemente ya estan en zona de divergencia (los valores crudos de output que viste, cientos por encima de 255, confirman que el error se estaba amplificando demasiado).
2. Recalibrar `MOTOR_DEADZONE` al minimo real: probar con `p0 i0 d0` y subir `z` de a poco (`z20`, `z30`, `z40`...) hasta que la rueda arranque a girar de forma visible con el robot inclinado apenas. Un deadzone mas alto de lo necesario ya empuja una correccion mas fuerte de lo que el error amerita — es probable que z60 este sobrecorrigiendo errores chicos.
3. Con deadzone real seteado, subir `p` de a 1 en 1 (no de a 5 o 10) sosteniendo el robot cerca de su equilibrio, buscando el punto donde reacciona proporcional a la inclinacion (poco angulo = correccion suave, harto angulo = correccion fuerte) sin ya estar a maxima velocidad para inclinaciones chicas.
4. Ahi sumar `d` de a poco (`d0.1`, `d0.3`...) para amortiguar el resto del rebote.
5. Si el rebote sigue siendo erratico/nervioso (no un rebote lento y amplio, sino algo tembloroso), bajar `f` (mas cerca de 0.9, por defecto 0.7) para suavizar mas la derivada, o subirlo si la correccion se siente con mucho retraso.

## Checklist mecanico si el PID solo no alcanza

Si con deadzone compensada + KP/KD razonables el robot sigue sin sostenerse, el problema es fisico, no de software. Probar en este orden (de mayor a menor impacto esperado con motores TT lentos):

1. **Subir el centro de masa** (chasis mas alto, peso concentrado arriba): esto hace que el robot caiga mas lento (aumenta el periodo natural del pendulo invertido), dando mas tiempo a un motor lento para reaccionar. Es el cambio de mayor impacto para motores TT.
2. **Aligerar el chasis**: menos masa total = menos torque necesario para corregir.
3. **Ruedas mas grandes**: mas desplazamiento lineal por vuelta de motor, ayuda a que la correccion "alcance" mas rapido en términos de distancia recorrida.
4. **Mejor agarre de rueda** (goma en vez de plastico liso): evita patinar, que desperdicia el torque justo cuando mas se necesita.
5. **Revisar la bateria de motores bajo carga**: medir el voltaje real mientras los motores estan exigidos (no en reposo) — si cae mucho, el motor pierde torque justo en el momento critico. Bateria debil se siente identico a "motor debil" aunque el motor este bien.
6. Si despues de todo esto sigue sin sostenerse: es limite fisico real de los TT motors para esta dinamica especifica (gearbox+RPM insuficiente) — el objetivo de validar sensor+filtro+PID ya esta cumplido igual, ver `docs/04-riesgos-decisiones.md`.

## Relacion con el resto del proyecto

Una vez encontrados los valores finales de `KP`/`KI`/`KD`/`SETPOINT_ANGLE` en este test, esos mismos valores (ajustados por la diferencia de actuador) son el punto de partida para el PID de balance del Motion Controller final del bipedo (ver `firmware/arquitectura-firmware.md` y `software/control-marcha.md`) — la ganancia exacta va a variar porque el actuador cambia de ruedas a servos, pero el orden de magnitud y el proceso de tuning es el mismo.
