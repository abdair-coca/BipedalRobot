# Paso 04 — Bracket de cadera (roll + pitch), pierna izquierda. **WIP**
# Proyecto Genesis (bipedalrobot). Ejecutar dentro de FreeCAD tras paso03. Idempotente.
#
# Dos sub-piezas independientes (rotan entre si, NO fusionar):
#  - Bracket_Cadera_Roll_Izq: fijo al torso. Yugo con servo de roll (eje X, z=370)
#    + rodamiento pasivo simetrico + flange de montaje al torso (patron FIJO
#    CADERA_TORSO_MOUNT_PATTERN, celdas cadera_mount_* — Paso 5 lo hereda).
#  - Bracket_Cadera_Pitch_Izq: rota con el roll. Recibe horn de roll (+X) y perno
#    M8 a rodamiento (-X); aloja servo de pitch (eje Y, z=355) con cuerpo hacia
#    afuera; su horn calza EXACTO en la interfaz que Muslo_Izq trae del Paso 3.
#
# ESTADO WIP: validacion de colision pitch +-40 muslo vs Bracket_Roll da residuos
# (max ~98 mm3 a -20; esquinas combinadas roll+-20/pitch+-40 ~387-447 mm3): el
# barrido del muslo POR ENCIMA del eje de pitch (r~24mm) pellizca las paredes del
# yugo, y con roll el canal actual (y -52..-28) queda corto. Fix pendiente antes
# de cerrar Paso 4 (ampliar despeje de paredes sin perder union flange-pared).

import FreeCAD as App
import Part
from FreeCAD import Vector

doc = App.listDocuments().get("bipedalrobot_ensamble")
if doc is None:
    raise RuntimeError("Documento no abierto — correr paso01..03 primero")
sheet = doc.getObject("ParametrosGenesis")

# --- Celdas del patron de montaje al torso (GEOMETRIA FIJA, no placeholder) ---
CELLS = [
    (28, "cadera_mount_z", "=holgura_suelo + pie_alto + pantorrilla_largo + muslo_largo",
     "mm plano de montaje bracket-torso (cara inferior torso) — FIJA, derivada"),
    (29, "cadera_mount_esp", "6", "mm espesor de la placa/flange de montaje — FIJA"),
    (30, "cadera_mount_dx", "31", "mm +-X de cada tornillo respecto al centro del bracket — FIJA"),
    (31, "cadera_mount_dy", "14", "mm +-Y de cada tornillo respecto al centro de pierna (y=-40) — FIJA"),
    (32, "cadera_mount_tornillo_d", "3.4", "mm agujero pasante M3 (holgura) — FIJA"),
    (33, "cadera_mount_cabeza_d", "6.0", "mm asiento cabeza M3 — FIJA"),
]
for fila, alias, val, comment in CELLS:
    try:
        sheet.get(alias)
    except Exception:
        sheet.set(f"A{fila}", alias)
        sheet.set(f"B{fila}", str(val))
        sheet.setAlias(f"B{fila}", alias)
        sheet.set(f"C{fila}", comment)
doc.recompute()

TOL = float(sheet.get("ENCASTRE_TOLERANCIA_PROVISIONAL"))
SV_L = float(sheet.get("servo_mg996r_largo")); SV_W = float(sheet.get("servo_mg996r_ancho"))
SV_OFF = float(sheet.get("servo_eje_offset_PROV"))
HORN_D = float(sheet.get("horn_disco_diam_PROV")); HORN_HOLE = float(sheet.get("HORN_MG996R_PLACEHOLDER"))
ROD_OD = float(sheet.get("rodamiento_od_PROV")); ROD_W = float(sheet.get("rodamiento_ancho_PROV"))
ROD_BORE = float(sheet.get("RODAMIENTO_BORE_PLACEHOLDER"))
MZ = float(sheet.get("cadera_mount_z"))
ESP = float(sheet.get("cadera_mount_esp"))
DX = float(sheet.get("cadera_mount_dx")); DY = float(sheet.get("cadera_mount_dy"))
TD = float(sheet.get("cadera_mount_tornillo_d")); HD = float(sheet.get("cadera_mount_cabeza_d"))
ZROLL = MZ + float(sheet.get("cadera_offset_roll_pitch"))
LEG_Y = -40.0
PK, PKL = SV_W + 2*TOL, SV_L + 2*TOL
HR_R = (HORN_D + 2*TOL)/2; HH_R = (HORN_HOLE + 2*TOL)/2
ST_R = (ROD_OD + 2*TOL)/2; BO_R = (ROD_BORE + 2*TOL)/2

# ---------- Bracket_Cadera_Roll_Izq ----------
s1 = Part.makeBox(15, 40, ESP + 1, Vector(20, -60, MZ - ESP))
s2 = Part.makeBox(15, 40, ESP + 1, Vector(-35, -60, MZ - ESP))
w1 = Part.makeBox(6, 40, 51, Vector(20, -60, MZ))
w2 = Part.makeBox(6, 40, 51, Vector(-26, -60, MZ))
web = Part.makeBox(52, 40, 5.5, Vector(-26, -60, ZROLL - SV_OFF + PKL))
roll = s1.fuse(s2).fuse(w1).fuse(w2).fuse(web)
roll = roll.cut(Part.makeBox(8, PK, PKL, Vector(19, LEG_Y - PK/2, ZROLL - SV_OFF)))
roll = roll.cut(Part.makeCylinder(ST_R, ROD_W, Vector(-26, LEG_Y, ZROLL), Vector(1, 0, 0)))
roll = roll.cut(Part.makeCylinder(BO_R, 8, Vector(-27, LEG_Y, ZROLL), Vector(1, 0, 0)))
for sx in (1, -1):
    for sy in (1, -1):
        x, y = sx*DX, LEG_Y + sy*DY
        roll = roll.cut(Part.makeCylinder(TD/2, 10, Vector(x, y, MZ - ESP - 1), Vector(0, 0, 1)))
        roll = roll.cut(Part.makeCylinder(HD/2, 3, Vector(x, y, MZ - ESP), Vector(0, 0, 1)))
# Canal de holgura para el barrido bajo del muslo (WIP: insuficiente arriba, ver cabecera)
roll = roll.cut(Part.makeBox(17, 24, 12, Vector(19, -52, 348)))
roll = roll.cut(Part.makeBox(17, 24, 12, Vector(-36, -52, 348)))

# ---------- Bracket_Cadera_Pitch_Izq ----------
railA = Part.makeBox(84, 7, 7, Vector(-42, -61, 340))
railB = Part.makeBox(84, 6, 7, Vector(-42, -26, 340))
xh = Part.makeBox(6, 39, 50, Vector(36, -60, 340))
xb = Part.makeBox(6, 39, 50, Vector(-42, -60, 340))
pad_h = Part.makeCylinder(12, 6, Vector(30, LEG_Y, ZROLL), Vector(1, 0, 0))
pad_b = Part.makeCylinder(12, 6, Vector(-36, LEG_Y, ZROLL), Vector(1, 0, 0))
yout = Part.makeBox(38, 6, 46, Vector(-19, -61, 322))
yin  = Part.makeBox(38, 6, 28, Vector(-19, -27, 340))
pitch = railA.fuse(railB).fuse(xh).fuse(xb).fuse(pad_h).fuse(pad_b).fuse(yout).fuse(yin)
pitch = pitch.cut(Part.makeCylinder(HR_R, 3, Vector(30, LEG_Y, ZROLL), Vector(1, 0, 0)))
pitch = pitch.cut(Part.makeCylinder(HH_R, 14, Vector(29, LEG_Y, ZROLL), Vector(1, 0, 0)))
pitch = pitch.cut(Part.makeCylinder(BO_R, 15, Vector(-43, LEG_Y, ZROLL), Vector(1, 0, 0)))
pitch = pitch.cut(Part.makeBox(PK, 8, PKL, Vector(-PK/2, -62, MZ - (PKL - SV_OFF))))
pitch = pitch.cut(Part.makeCylinder(BO_R, 8, Vector(0, -28, MZ), Vector(0, 1, 0)))

for n, sh in (("Bracket_Cadera_Roll_Izq", roll), ("Bracket_Cadera_Pitch_Izq", pitch)):
    if doc.getObject(n):
        doc.removeObject(n)
    o = doc.addObject("Part::Feature", n)
    o.Shape = sh

# Marcadores de eje de cadera (Paso 2) reemplazados por geometria real
for n in ("Eje_Cadera_Pitch_Izq", "Eje_Cadera_Roll_Izq"):
    if doc.getObject(n):
        doc.removeObject(n)
doc.recompute()
doc.save()

# ---------- Validaciones ----------
muslo = doc.getObject("Muslo_Izq").Shape
torso = doc.getObject("Torso").Shape
print("Roll +-20 ([pitch+muslo] vs roll bracket / vs torso placeholder):")
for ang in (-20, 0, 20):
    p = pitch.copy(); m = muslo.copy()
    for s in (p, m):
        s.rotate(Vector(0, LEG_Y, ZROLL), Vector(1, 0, 0), ang)
    vr = roll.common(p).Volume + roll.common(m).Volume
    vt = torso.common(p).Volume + torso.common(m).Volume
    print(f"  {ang:+3d}: roll={vr:.3f} mm3 | torso={vt:.1f} mm3 (esperada, grueso)")
print("Pitch +-40 (muslo vs roll bracket) — WIP, residuos conocidos:")
for ang in (-40, -20, 0, 20, 40):
    m = muslo.copy()
    m.rotate(Vector(0, LEG_Y, MZ), Vector(0, 1, 0), ang)
    print(f"  {ang:+3d}: roll={roll.common(m).Volume:.3f} mm3 | pitch={pitch.common(m).Volume:.3f} mm3")

DENS = 1.24 * 0.20
for n in ("Bracket_Cadera_Roll_Izq", "Bracket_Cadera_Pitch_Izq"):
    v = doc.getObject(n).Shape.Volume / 1000.0
    print(f"{n:26s} {v:6.1f} cm3 -> {v*DENS:5.1f} g (PLA 20% infill, supuesto)")
