# Vision y alcance

## Que es

Robot bipedo mediano (40-80cm de alto) que camina, balancea y hereda las capacidades de interaccion (vision, voz, cara) del proyecto robotCreeper existente. Es el "cuerpo" nuevo para la "mente/cabeza" ya construida.

## Objetivo

Portfolio/demo tecnico: debe quedar bien documentado, con hitos demostrables (parado estatico -> balance dinamico -> caminata) y presentable (video, fotos, repo ordenado).

## Alcance cubierto por esta organizacion

- **Mecanico**: estructura de piernas/torso, DOF, materiales, impresion 3D o corte.
- **Electronico**: BOM completo, presupuesto energetico, conexionado.
- **Firmware/software**: control de balance (IMU), cinematica de piernas, gestion de marcha, integracion con nodos de robotCreeper.
- **Gestion**: backlog, fases, milestones, riesgos.

## Fuera de alcance (por ahora)

- Manipulacion (brazos) — puede ser fase futura, no bloquea el proyecto actual.
- Marcha dinamica avanzada (ZMP completo, control por RL) — se empieza con marcha estatica/cuasi-estatica.

## Relacion con robotCreeper

robotCreeper ya tiene resuelto: vision (ESP32-CAM), voz (mic MAX9814 + amp PAM8403), cara (OLED SH1106), movimiento de cabeza (2 servos pan/tilt), y una base rodante (TT motors + L298N + Wemos D1 mini/ESP8266).

Este proyecto bipedo:
- **Reutiliza** el subsistema de cabeza (camara, voz, cara, pan/tilt) tal cual, montado en la parte superior del nuevo cuerpo.
- **Reemplaza** la base rodante (TT motors + L298N) por piernas motorizadas con servos — la base rodante NO sirve para bipedo, ver [decisiones](04-riesgos-decisiones.md).
- **Agrega** un controlador principal nuevo (ESP32 DevKit) dedicado a balance y locomocion, usando el MPU-6050 ya disponible.
- Detalle de integracion en [02-arquitectura-sistema.md](02-arquitectura-sistema.md).

## Criterio de exito (portfolio)

1. Robot se para solo y mantiene balance estatico.
2. Robot camina unos pasos en linea recta (marcha estatica).
3. Cabeza (vision+voz+cara) sigue funcionando integrada en el cuerpo nuevo.
4. Documentacion + video demo presentables.
