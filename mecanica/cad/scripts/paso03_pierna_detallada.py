# Paso 03 — Muslo + Pantorrilla + Pie con detalle real (pierna izquierda, y=-40)
# Proyecto Genesis (bipedalrobot). Ejecutar dentro de FreeCAD tras paso02. Idempotente.
#
# Reemplaza los placeholders de Paso 2 por geometria real (mismos nombres):
# bolsillos pasantes de servo MG996R, interfaces de horn, asiento de rodamiento
# en cadera, canales de cable senal/potencia, pie con doble apoyo talon+punta.
# Medidas de horn/rodamiento/tolerancia son PROVISIONALES (celdas *_PROV /
# *_PLACEHOLDER en ParametrosGenesis) — verificar contra pieza fisica antes de
# imprimir (checklist Paso 8/9 del plan). Sin orejas de montaje del servo (tabs):
# fijacion por tornillos pendiente de verificacion fisica.
#
# Incluye validacion de colision local por booleano:
#   rodilla 0/45/90 grados, tobillo -30/0/+30 grados.

import FreeCAD as App
import Part
from FreeCAD import Vector

doc = App.listDocuments().get("bipedalrobot_ensamble")
if doc is None:
    raise RuntimeError("Documento no abierto — correr paso01/paso02 primero")
sheet = doc.getObject("ParametrosGenesis")

# --- Celdas provisionales de Paso 3 (solo si faltan) ---
NUEVAS = [
    (20, "ENCASTRE_TOLERANCIA_PROVISIONAL", 0.15,
     "mm holgura bolsillo servo (rango plan 0.1-0.2) — PROVISIONAL, verificar contra MG996R fisico antes de imprimir"),
    (21, "HORN_MG996R_PLACEHOLDER", 6.0,
     "mm diam salida spline 25T (spec publica MG996R) — PROVISIONAL, horn real sin medir"),
    (22, "horn_disco_diam_PROV", 21.0, "mm diam disco horn redondo tipico — PROVISIONAL"),
    (23, "horn_alto_PROV", 7.0, "mm alto total horn sobre cara servo (boss+disco) — PROVISIONAL"),
    (24, "RODAMIENTO_BORE_PLACEHOLDER", 8.0,
     "mm bore rodamiento con brida tipo F688ZZ (8x16x5, brida 18) — PROVISIONAL, modelo sin elegir"),
    (25, "rodamiento_od_PROV", 16.0, "mm diametro exterior F688ZZ — PROVISIONAL"),
    (26, "rodamiento_ancho_PROV", 5.0, "mm ancho F688ZZ (brida 18mm no incluida) — PROVISIONAL"),
    (27, "servo_eje_offset_PROV", 10.5,
     "mm del borde corto del cuerpo al eje spline (datasheet aprox) — PROVISIONAL"),
]
for fila, alias, val, comment in NUEVAS:
    try:
        sheet.get(alias)
    except Exception:
        sheet.set(f"A{fila}", alias)
        sheet.set(f"B{fila}", str(val))
        sheet.setAlias(f"B{fila}", alias)
        sheet.set(f"C{fila}", comment)
doc.recompute()

# --- Parametros ---
TOL  = float(sheet.get("ENCASTRE_TOLERANCIA_PROVISIONAL"))
SV_L = float(sheet.get("servo_mg996r_largo"))
SV_W = float(sheet.get("servo_mg996r_ancho"))
SV_OFF = float(sheet.get("servo_eje_offset_PROV"))
HORN_D = float(sheet.get("horn_disco_diam_PROV"))
HORN_HOLE = float(sheet.get("HORN_MG996R_PLACEHOLDER"))
ROD_OD = float(sheet.get("rodamiento_od_PROV"))
ROD_W  = float(sheet.get("rodamiento_ancho_PROV"))
ROD_BORE = float(sheet.get("RODAMIENTO_BORE_PLACEHOLDER"))
HS = float(sheet.get("holgura_suelo")); PA = float(sheet.get("pie_alto"))
PL = float(sheet.get("pantorrilla_largo")); ML = float(sheet.get("muslo_largo"))
ZT, ZR, ZC = HS + PA, HS + PA + PL, HS + PA + PL + ML   # 35 / 195 / 355

PK_X, PK_Z = SV_W + 2*TOL, SV_L + 2*TOL
HR_R = (HORN_D + 2*TOL)/2
HH_R = (HORN_HOLE + 2*TOL)/2
ST_R = (ROD_OD + 2*TOL)/2
BO_R = (ROD_BORE + 2*TOL)/2

# --- MUSLO: viga 34x22 y[-51,-29], z[179,372] ---
beam = Part.makeBox(34, 22, 193, Vector(-17, -51, 179))
pocket = Part.makeBox(PK_X, 24, PK_Z, Vector(-PK_X/2, -52, ZR - SV_OFF))
horn_rec  = Part.makeCylinder(HR_R, 3,  Vector(0, -51, ZC), Vector(0, 1, 0))
horn_hole = Part.makeCylinder(HH_R, 24, Vector(0, -52, ZC), Vector(0, 1, 0))
seat      = Part.makeCylinder(ST_R, ROD_W, Vector(0, -29, ZC), Vector(0, -1, 0))
seat_hole = Part.makeCylinder(BO_R, 10,   Vector(0, -29, ZC), Vector(0, -1, 0))
g1 = Part.makeBox(3.2, 4, 150, Vector(14, -48, 200))
g2 = Part.makeBox(3.2, 4, 150, Vector(14, -36, 200))
muslo = beam.cut(pocket).cut(horn_rec).cut(horn_hole).cut(seat).cut(seat_hole).cut(g1).cut(g2)

# --- PANTORRILLA: placa horn y[-64,-58] arriba + viga y[-66,-44] abajo ---
plate = Part.makeBox(34, 6, 52, Vector(-17, -64, ZR - 35))
prec  = Part.makeCylinder(HR_R, 3, Vector(0, -58, ZR), Vector(0, -1, 0))
phole = Part.makeCylinder(HH_R, 8, Vector(0, -65, ZR), Vector(0, 1, 0))
pbeam = Part.makeBox(34, 22, 145, Vector(-17, -66, 20))
ppocket = Part.makeBox(PK_X, 24, PK_Z, Vector(-PK_X/2, -67, ZT - SV_OFF))
pg1 = Part.makeBox(3.2, 4, 80, Vector(14, -63, 75))
pg2 = Part.makeBox(3.2, 4, 80, Vector(14, -51, 75))
pant = pbeam.fuse(plate).cut(ppocket).cut(prec).cut(phole).cut(pg1).cut(pg2)

# --- PIE: placa vertical tobillo + suela puente + doble apoyo ---
placa = Part.makeBox(34, 6, 58, Vector(-17, -79, 8))
fprec  = Part.makeCylinder(HR_R, 3, Vector(0, -73, ZT), Vector(0, -1, 0))
fphole = Part.makeCylinder(HH_R, 8, Vector(0, -80, ZT), Vector(0, 1, 0))
suela  = Part.makeBox(65, 40, 3, Vector(-20, -75, 8))
talon  = Part.makeBox(14, 40, 3, Vector(-20, -75, 5))
punta  = Part.makeBox(14, 40, 3, Vector(31, -75, 5))
pie = placa.fuse(suela).fuse(talon).fuse(punta).cut(fprec).cut(fphole)

# --- Validaciones de colision local ---
def colision(a, b, centro, eje, ang):
    s = b.copy()
    s.rotate(centro, eje, ang)
    return a.common(s).Volume

print("Rodilla (pantorrilla rota alrededor de eje y=-55,z=%g):" % ZR)
for a in (0, 45, 90):
    v = colision(muslo, pant, Vector(0, -55, ZR), Vector(0, 1, 0), a)
    print(f"  {a:3d} grados: {v:.3f} mm3 {'OK' if v < 1e-6 else 'COLISION'}")
print("Tobillo (pie rota alrededor de z=%g):" % ZT)
for a in (-30, 0, 30):
    v = colision(pant, pie, Vector(0, -55, ZT), Vector(0, 1, 0), a)
    print(f"  {a:+3d} grados: {v:.3f} mm3 {'OK' if v < 1e-6 else 'COLISION'}")

# --- Reemplazar placeholders (mismos nombres) ---
for n, sh in (("Muslo_Izq", muslo), ("Pantorrilla_Izq", pant), ("Pie_Izq", pie)):
    if doc.getObject(n):
        doc.removeObject(n)
    o = doc.addObject("Part::Feature", n)
    o.Shape = sh
doc.recompute()
doc.save()

# --- Peso (geometria real) ---
DENS = 1.24 * 0.20  # PLA x 20% infill (supuesto)
print("\nPeso piezas impresas (PLA 1.24 x 20% infill, supuesto):")
for n in ("Muslo_Izq", "Pantorrilla_Izq", "Pie_Izq"):
    v = doc.getObject(n).Shape.Volume / 1000.0
    print(f"  {n:18s} {v:7.1f} cm3 -> {v*DENS:6.1f} g")
print("Torque estatico: ver reporte de sesion (supuestos de masa total ~1.09 kg,")
print("rodilla cargada limitada a ~30 grados, squat 90 prohibido por software).")
