# Plan de diseño 3D

Plan para modelar el bipedo completo en CAD 3D y validarlo (proporciones, rango de movimiento, colisiones, peso) **antes** de imprimir/cortar piezas reales. Complementa [diseno-estructural.md](diseno-estructural.md) (decisiones ya tomadas: DOF, materiales, ROM) con el flujo concreto de modelado.

## 1. Análisis de referencias (`docs/3dImages/`)

| Imagen | Qué es | Qué tomar de ella |
|---|---|---|
| `propuesta.png` | Bipedo impreso real, mismo enfoque de hardware que el nuestro (servos visibles tipo MG996R azules, cableado señal/potencia separado, cabeza con cámara+anillo LED, display frontal) | **Referencia principal de proporciones y solución de pie**: doble punto de apoyo (talón+punta) para ampliar área de sustentación sin sumar DOF. Bracket de cadera visible (2 servos casi coincidentes en el mismo punto pivote) — usar como referencia de ensamble cadera pitch+roll. |
| `bipedalrobot.png` | Render CAD de pierna con mecanismo de barras paralelas (four-bar linkage) y actuadores concentrados en la cadera, sin motor en rodilla/tobillo | **Solo inspiración mecánica avanzada, NO objetivo de v1.** Nuestra decisión ya tomada es servo directo en cada articulación vía PCA9685 (más simple y barato). No replicar el mecanismo de transmisión — dejarlo como posible upgrade de fase futura si el torque/inercia de v1 no alcanza (ver `docs/03-roadmap-fases.md` fase 3+). |
| `bipedalrobot1.jpg` | Render estético (carcasa curva, franjas de color) | **Solo referencia cosmética** para Fase 5 (pulido/carcasa). No afecta esqueleto, DOF ni ROM. |

**Importante**: no mezclar las tres referencias en un solo objetivo. El esqueleto cinemático sale de `propuesta.png` + `diseno-estructural.md`; el mecanismo de barras de `bipedalrobot.png` queda fuera de alcance de v1; la estética de `bipedalrobot1.jpg` es opcional y posterior.

## 2. Herramienta de CAD

Recomendado: **Fusion 360** (licencia personal/hobby gratuita) o **FreeCAD** (open source, sin cuenta). Ambas soportan:
- Modelado paramétrico (ajustar una medida sin rehacer la pieza)
- Ensamble con *joints*/*mates* que simulan el rango de movimiento real (clave para validar ROM sin imprimir)
- Detección de colisiones entre piezas en el ensamble
- Export a STEP (editable) y STL (impresión)

Tinkercad no alcanza para simular articulaciones — usar como mucho para bocetos rápidos, no para el ensamble final.

## 3. Especificación cinemática a modelar

8 DOF total (4 por pierna), heredado de `diseno-estructural.md`:

| Articulación | Eje | ROM | Servo |
|---|---|---|---|
| Cadera pitch | adelante/atrás | ±40° | MG996R |
| Cadera roll | lateral | ±20° | MG996R |
| Rodilla pitch | flexión | 0° a 90° | MG996R |
| Tobillo pitch | adelante/atrás | ±30° | MG996R |

Cadera pitch y cadera roll deben modelarse con pivotes lo más cercanos posible entre sí (bracket compartido, ver `propuesta.png`) para no alargar innecesariamente la pierna.

**Presupuesto de altura** (objetivo total 50-60cm):
1. Medir la cabeza existente físicamente (alto real, no asumido) — ya está construida, no se rediseña, solo se modela el bracket de unión cuello-torso.
2. Restar esa altura del objetivo total.
3. Repartir el resto entre torso (~12-15cm), muslo (~15-18cm), pantorrilla (~15-18cm) y pie (~5-8cm de largo), ajustando en el paso 2 del flujo (esqueleto en bloque) antes de detallar geometría.

## 4. Inventario de componentes a modelar

### Torso
- Chasis/caja principal (imprimir), con tapa desmontable para acceso a cableado.
- Aloja: ESP32 DevKit v1, PCA9685, MPU-6050, regulador buck 5V/3A, capacitor 1000-2200µF, batería (2S LiFePO4 o pack 4xAA NiMH).
- Reservar volumen para batería/PCA9685/capacitor en la parte **más baja** del torso (baja centro de masa, ya decidido en `diseno-estructural.md`).
- Puntos de anclaje para los 4 servos de cadera (2 por pierna).
- Canales separados para cable de señal (naranja) y potencia (negro) — ver `electronica/conexionado.md`.

### Cadera (x2, espejo izq/der)
- Bracket que combina servo roll + servo pitch cerca del mismo pivote.

### Muslo (x2, espejo)
- Eslabón rígido cadera→rodilla.
- Aloja 1x servo MG996R (rodilla) + horn + buje/rodamiento opcional en extremo superior.

### Pantorrilla (x2, espejo)
- Eslabón rígido rodilla→tobillo.
- Aloja 1x servo MG996R (tobillo).

### Pie (x2, espejo)
- Placa de apoyo con doble punto de contacto (talón+punta, referencia `propuesta.png`).
- Anclaje al horn del servo de tobillo.

### Cabeza
- No se remodela (ya existe físicamente). Solo modelar el bracket de unión al primer eslabón del torso.

## 5. Consideraciones de diseño

- **Tolerancias de impresión**: medir el horn del MG996R físico (no solo datasheet) y dejar 0.1-0.2mm de holgura en encastres.
- **Peso**: estimar peso por pieza en el slicer (volumen x densidad de infill) y sumarlo; comparar contra torque real de MG996R (riesgo ya documentado en `docs/04-riesgos-decisiones.md`).
- **Simetría**: modelar 1 pierna completa paramétrica y espejar para la otra — evita duplicar trabajo y asimetrías por error.
- **Validar ROM en CAD antes de imprimir**: simular los 4 extremos de movimiento (cadera pitch ±40°, cadera roll ±20°, rodilla 0-90°, tobillo ±30°) en el ensamble y confirmar que ninguna pieza choca con otra.

## 6. Flujo de modelado (orden sugerido)

1. Medir cabeza existente (alto, ancho, peso real).
2. Bloquear **esqueleto cinemático** en CAD: solo ejes/pivotes con formas primitivas (cilindros), respetando la tabla de DOF+ROM+presupuesto de altura — valida proporciones antes de detallar geometría.
3. Modelar 1 muslo + 1 pantorrilla + 1 pie con detalle real (encastres, horns, canales de cable).
4. Modelar bracket de cadera + unión a torso.
5. Modelar torso con volúmenes reservados por componente electrónico.
6. Ensamblar cadena completa (torso + 2 caderas + 2 muslos + 2 pantorrillas + 2 pies), simular ROM extremos, revisar colisiones.
7. Espejar la pierna validada para el lado restante.
8. Exportar STEP (backup editable) + STL (impresión), un archivo por pieza.
9. Imprimir **1 pierna de prueba primero** (no las 2 en paralelo) para validar ajuste real de servo/tornillería antes de comprometer todo el filamento.

## 7. Estructura de archivos propuesta

```
mecanica/cad/
  piezas/
    torso_chasis.step / .stl
    cadera_bracket_izq.step / .stl
    muslo_izq.step / .stl
    pantorrilla_izq.step / .stl
    pie_izq.step / .stl
    (piezas _der = espejo de _izq, no duplicar archivo fuente si la herramienta soporta mirror)
  ensamble/
    bipedalrobot_ensamble.step (o extensión nativa del software elegido)
```

Crear esta carpeta recién al empezar el modelado real (no antes, para no dejar carpetas vacías sin contenido).

## 8. Checklist antes de imprimir

- [ ] Esqueleto cinemático valida altura total dentro de 50-60cm
- [ ] Simulación de ROM sin colisiones en los 4 extremos por pierna
- [ ] Encastres de servo verificados contra medidas reales del MG996R físico
- [ ] Espacio interno del torso valida que entran todos los componentes con margen de cableado
- [ ] Peso estimado por pieza sumado y comparado contra torque disponible de servos

## 9. Checklist antes de pasar a fabricación real (Fase 1 del roadmap)

- [ ] Modelo 3D completo aprobado (visual + ROM + peso)
- [ ] 1 pierna impresa de prueba, servo montado, rango de movimiento a mano confirmado sin choques
- [ ] Ajuste de tornillería/horn probado en pieza real (no solo en CAD)
- [ ] Iterar CAD si hay diferencia entre simulación y pieza real, antes de imprimir el resto

## 10. Referencias cruzadas

- [diseno-estructural.md](diseno-estructural.md) — DOF, materiales, ROM, distribución de peso
- [docs/04-riesgos-decisiones.md](../docs/04-riesgos-decisiones.md) — riesgo de torque insuficiente
- [electronica/BOM.md](../electronica/BOM.md) — componentes a comprar/reusar
- [electronica/conexionado.md](../electronica/conexionado.md) — separación cables señal/potencia
- [docs/03-roadmap-fases.md](../docs/03-roadmap-fases.md) — Fase 1 (mecánica de piernas)
