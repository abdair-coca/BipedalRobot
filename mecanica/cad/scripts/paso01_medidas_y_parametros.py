# Paso 01 — Registro parametrico + stub de reserva cabeza-torso
# Proyecto Genesis (bipedalrobot). Ejecutar dentro de FreeCAD (via freecad-mcp execute_code
# o consola Python de FreeCAD). Idempotente: se puede re-correr tras ajustar valores.
#
# La cabeza NO existe fisicamente todavia — su presupuesto de altura es una celda
# DERIVADA (altura objetivo menos suma de segmentos), placeholder no comprometido.

import FreeCAD as App

DOC_NAME = "bipedalrobot_ensamble"
SAVE_PATH = r"C:\Users\abdai\desktop\robotcreeper\bipedalrobot\mecanica\cad\ensamble\bipedalrobot_ensamble.FCStd"

doc = App.listDocuments().get(DOC_NAME)
if doc is None:
    doc = App.newDocument(DOC_NAME)

# Idempotencia: borrar stub antes que spreadsheet (el stub referencia celdas del sheet)
for name in ("Stub_Reserva_Cabeza", "ParametrosGenesis"):
    if doc.getObject(name):
        doc.removeObject(name)

sheet = doc.addObject("Spreadsheet::Sheet", "ParametrosGenesis")

# (alias, valor, comentario)  — valores en mm / grados
PARAMS = [
    ("altura_total_min",      500,  "mm — objetivo minimo (plan: 50-60cm)"),
    ("altura_total_max",      600,  "mm — objetivo maximo"),
    ("altura_total_objetivo", 550,  "mm — target de trabajo, editable"),
    ("torso_alto",            130,  "mm (rango plan 120-150)"),
    ("muslo_largo",           160,  "mm (rango plan 150-180)"),
    ("pantorrilla_largo",     160,  "mm (rango plan 150-180)"),
    ("pie_largo",             65,   "mm horizontal (rango plan 50-80) — NO suma altura"),
    ("pie_alto",              30,   "mm — altura pivote tobillo sobre suelo, placeholder"),
    ("holgura_suelo",         5,    "mm — margen pie/suelo"),
    ("cadera_pitch_rom_deg",  40,   "± grados (tabla DOF, no modificar)"),
    ("cadera_roll_rom_deg",   20,   "± grados"),
    ("rodilla_rom_min_deg",   0,    "grados (no hiperextender)"),
    ("rodilla_rom_max_deg",   90,   "grados"),
    ("tobillo_pitch_rom_deg", 30,   "± grados"),
    ("servo_mg996r_largo",    40.7, "mm cuerpo (referencia datasheet, validar fisico en Paso 3)"),
    ("servo_mg996r_ancho",    19.7, "mm"),
    ("servo_mg996r_alto",     42.9, "mm sin horn"),
]

row = 1
for alias, val, comment in PARAMS:
    sheet.set(f"A{row}", alias)
    sheet.set(f"B{row}", str(val))
    sheet.setAlias(f"B{row}", alias)
    sheet.set(f"C{row}", comment)
    row += 1

# Celda DERIVADA: presupuesto de cabeza = objetivo - stack de segmentos
sheet.set(f"A{row}", "presupuesto_cabeza_placeholder")
sheet.set(
    f"B{row}",
    "=altura_total_objetivo - (torso_alto + muslo_largo + pantorrilla_largo + pie_alto + holgura_suelo)",
)
sheet.setAlias(f"B{row}", "presupuesto_cabeza_placeholder")
sheet.set(f"C{row}", "mm DERIVADA — placeholder NO comprometido, cabeza aun no disenada")

doc.recompute()

# Stub de reserva de espacio cabeza (NO es bracket real): caja centrada en XY,
# apoyada sobre el tope del torso, altura = presupuesto derivado.
stub = doc.addObject("Part::Box", "Stub_Reserva_Cabeza")
stub.Length = 60
stub.Width = 60
stub.Placement.Base.x = -30
stub.Placement.Base.y = -30
stub.setExpression("Height", "ParametrosGenesis.presupuesto_cabeza_placeholder")
stub.setExpression(
    "Placement.Base.z",
    "ParametrosGenesis.holgura_suelo + ParametrosGenesis.pie_alto"
    " + ParametrosGenesis.pantorrilla_largo + ParametrosGenesis.muslo_largo"
    " + ParametrosGenesis.torso_alto",
)
doc.recompute()

doc.saveAs(SAVE_PATH)

# Resumen para checkpoint
cab = float(sheet.get("presupuesto_cabeza_placeholder"))
stack = sum(float(sheet.get(a)) for a in
            ("holgura_suelo", "pie_alto", "pantorrilla_largo", "muslo_largo", "torso_alto"))
print("=== ParametrosGenesis ===")
for alias, _, _ in PARAMS:
    print(f"{alias:26s} = {float(sheet.get(alias))}")
print(f"{'stack_sin_cabeza':26s} = {stack}")
print(f"{'presupuesto_cabeza_placeholder':26s} = {cab}  (DERIVADA, placeholder)")
print(f"OK presupuesto cabeza >= 50mm: {cab >= 50}")
print(f"Documento guardado en: {SAVE_PATH}")
