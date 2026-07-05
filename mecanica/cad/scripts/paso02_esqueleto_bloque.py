# Paso 02 — Esqueleto cinematico en bloque (UNA pierna, sin espejar — espejado es Paso 7)
# Proyecto Genesis (bipedalrobot). Ejecutar dentro de FreeCAD tras paso01.
# Idempotente: re-correr tras ajustar celdas de ParametrosGenesis.
#
# Primitivas solamente: cajas placeholder (torso/muslo/pantorrilla/pie) + cilindros
# como MARCADORES de eje de articulacion (rojos). Sin encastres/horns/cables (Paso 3).
# Todas las longitudes/alturas vienen por expresion desde ParametrosGenesis.

import FreeCAD as App

DOC_NAME = "bipedalrobot_ensamble"
doc = App.listDocuments().get(DOC_NAME)
if doc is None:
    raise RuntimeError("Documento no abierto — correr paso01 primero")
sheet = doc.getObject("ParametrosGenesis")
if sheet is None:
    raise RuntimeError("Falta ParametrosGenesis — correr paso01 primero")

# Celda nueva: separacion vertical entre pivote cadera-pitch y cadera-roll
# (bracket compartido, pivotes casi coincidentes). Fila 19 (18 = celda derivada cabeza).
try:
    sheet.get("cadera_offset_roll_pitch")
except Exception:
    sheet.set("A19", "cadera_offset_roll_pitch")
    sheet.set("B19", "15")
    sheet.setAlias("B19", "cadera_offset_roll_pitch")
    sheet.set("C19", "mm — separacion vertical pivotes pitch/roll en bracket compartido")
    doc.recompute()

LEG_Y = -40.0   # pierna izquierda desplazada lateralmente; espejo (+40) es Paso 7
EJE_R = 8.0     # radio visual de los marcadores de eje
EJE_L = 60.0    # largo de los marcadores de eje

# Expresiones de altura acumulada (todas leen del spreadsheet)
Z_TOBILLO = "ParametrosGenesis.holgura_suelo + ParametrosGenesis.pie_alto"
Z_RODILLA = Z_TOBILLO + " + ParametrosGenesis.pantorrilla_largo"
Z_CADERA = Z_RODILLA + " + ParametrosGenesis.muslo_largo"
Z_TORSO_TOP = Z_CADERA + " + ParametrosGenesis.torso_alto"

NOMBRES = [
    "Pie_Izq", "Pantorrilla_Izq", "Muslo_Izq", "Torso",
    "Eje_Tobillo_Pitch_Izq", "Eje_Rodilla_Pitch_Izq",
    "Eje_Cadera_Pitch_Izq", "Eje_Cadera_Roll_Izq",
]
for n in NOMBRES:
    if doc.getObject(n):
        doc.removeObject(n)

def caja(nombre, largo, ancho, x, y, expr_alto, expr_z):
    b = doc.addObject("Part::Box", nombre)
    b.Length = largo
    b.Width = ancho
    b.Placement.Base.x = x
    b.Placement.Base.y = y
    b.setExpression("Height", expr_alto)
    b.setExpression("Placement.Base.z", expr_z)
    return b

def eje(nombre, orientacion, x, y, expr_z):
    """Cilindro marcador de eje. orientacion: 'Y' (pitch) o 'X' (roll)."""
    c = doc.addObject("Part::Cylinder", nombre)
    c.Radius = EJE_R
    c.Height = EJE_L
    if orientacion == "Y":
        c.Placement = App.Placement(
            App.Vector(x, y - EJE_L / 2, 0), App.Rotation(App.Vector(1, 0, 0), -90))
    else:  # X
        c.Placement = App.Placement(
            App.Vector(x - EJE_L / 2, y, 0), App.Rotation(App.Vector(0, 1, 0), 90))
    c.setExpression("Placement.Base.z", expr_z)
    try:
        c.ViewObject.ShapeColor = (1.0, 0.2, 0.2, 1.0)
    except Exception:
        pass
    return c

# Bloques placeholder
caja("Pie_Izq", 65, 40, -20, LEG_Y - 20,
     "ParametrosGenesis.pie_alto", "ParametrosGenesis.holgura_suelo")
caja("Pantorrilla_Izq", 30, 30, -15, LEG_Y - 15,
     "ParametrosGenesis.pantorrilla_largo", Z_TOBILLO)
caja("Muslo_Izq", 30, 30, -15, LEG_Y - 15,
     "ParametrosGenesis.muslo_largo", Z_RODILLA)
caja("Torso", 80, 120, -40, -60,
     "ParametrosGenesis.torso_alto", Z_CADERA)

# Marcadores de eje (pitch = lateral Y, roll = frontal X)
eje("Eje_Tobillo_Pitch_Izq", "Y", 0, LEG_Y, Z_TOBILLO)
eje("Eje_Rodilla_Pitch_Izq", "Y", 0, LEG_Y, Z_RODILLA)
eje("Eje_Cadera_Pitch_Izq", "Y", 0, LEG_Y, Z_CADERA)
# Roll casi coincidente con pitch: mismo punto XY, offset vertical chico (bracket compartido)
eje("Eje_Cadera_Roll_Izq", "X", 0, LEG_Y,
    Z_CADERA + " + ParametrosGenesis.cadera_offset_roll_pitch")

# Ajustar pie: expresion tambien para largo (viene del sheet)
doc.getObject("Pie_Izq").setExpression("Length", "ParametrosGenesis.pie_largo")

doc.recompute()
doc.save()

# --- Resumen: altura total + peso preliminar ---
zmax = max(o.Shape.BoundBox.ZMax for o in doc.Objects if hasattr(o, "Shape") and o.Shape.Volume > 0)
zmin = min(o.Shape.BoundBox.ZMin for o in doc.Objects if hasattr(o, "Shape") and o.Shape.Volume > 0)
print(f"Altura total sobre suelo (z=0 a tope): {zmax:.1f} mm")
print(f"ZMin geometria (holgura pie): {zmin:.1f} mm")
print(f"Objetivo 500-600mm -> {'DENTRO' if 500 <= zmax <= 600 else 'FUERA'} de rango")

# Peso: PLA 1.24 g/cm3 x 20% infill (SUPUESTO placeholder, no confirmado).
# Estimacion GRUESA desde primitivas macizas — recalcular en Paso 3+ con piezas reales.
DENS = 1.24 * 0.20  # g/cm3 efectivo
piezas_estructura = ["Pie_Izq", "Pantorrilla_Izq", "Muslo_Izq", "Torso"]
print("\nPeso preliminar (PLA 1.24 g/cm3 x 20% infill, supuesto):")
total_una_pierna = 0.0
for n in piezas_estructura:
    v_cm3 = doc.getObject(n).Shape.Volume / 1000.0
    g = v_cm3 * DENS
    total_una_pierna += g
    print(f"  {n:20s} {v_cm3:8.1f} cm3 -> {g:7.1f} g")
pierna = sum(doc.getObject(n).Shape.Volume / 1000.0 * DENS
             for n in ("Pie_Izq", "Pantorrilla_Izq", "Muslo_Izq"))
print(f"  Total (1 pierna + torso): {total_una_pierna:.1f} g")
print(f"  Total con 2 piernas:      {total_una_pierna + pierna:.1f} g")
print("  (stub cabeza y ejes excluidos: no son piezas imprimibles)")
print("\nObjetos en documento:")
for o in doc.Objects:
    print(f"  {o.Name} ({o.TypeId})")
