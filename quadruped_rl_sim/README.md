# quadruped_rl_sim

Simulacion PyBullet + Gymnasium + PPO (stable-baselines3) para entrenar la
marcha hacia adelante de un cuadrupedo generico de 12 DOF (3 por pata:
abduccion de cadera, pitch de cadera, rodilla).

**Este es un experimento aislado**, independiente del robot bipedo real del
resto del repo (`mecanica/`, `electronica/`, `firmware/`, etc.). Sirve como
banco de pruebas de RL con servos de posicion antes de portar el enfoque al
hardware bipedo. No comparte codigo ni archivos con esas carpetas.

## Por que cuadrupedo y no bipedo, para este experimento

Un cuadrupedo de 12 DOF es mas facil de estabilizar que un bipedo (mas puntos
de apoyo, menos sensible al balance), asi que sirve para validar primero la
mecanica de RL + control por posicion (URDF, entorno Gymnasium, PPO,
pipeline sim-to-real) con un problema mas simple, antes de pelear ademas con
el balance dificil de un bipedo.

## Instalacion

Requiere Python 3.11 (probado en Windows).

```bash
cd quadruped_rl_sim
python -m venv .venv
.venv\Scripts\activate         # cmd.exe
.venv\Scripts\Activate.ps1     # PowerShell
pip install -r requirements.txt
```

**Nota Windows importante**: `pybullet` no publica wheels precompilados para Windows
en PyPI (ninguna version) — `pip install` lo compila desde source, lo que requiere
**Microsoft C++ Build Tools** (workload "Desktop development with C++"). Si no los
tenes instalados, `pip install` va a fallar con `error: Microsoft Visual C++ 14.0 or
greater is required`. Instalar con:
```powershell
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --override "--wait --quiet --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```
Alternativa sin compilar: instalar Miniconda y `conda install -c conda-forge pybullet`
(conda-forge si publica wheel `win-64`), el resto de las libs via pip igual.

## Archivos

| Archivo | Que hace |
|---|---|
| `config.py` | Todos los parametros fisicos del robot (dimensiones, masas, limites de joint en grados, altura de reposo). **Unico lugar a tocar cuando calibres el robot real.** |
| `generate_urdf.py` | Lee `config.py` y genera `quadruped.urdf` (torso + 4 patas x 3 joints revolute, colision con primitivas). Correr manualmente para regenerar, o se genera solo la primera vez que se instancia el entorno. |
| `quad_env.py` | `QuadrupedEnv(gymnasium.Env)`: observacion (31,), accion (12,) normalizada [-1,1] mapeada a angulos reales, reward, terminacion. Control por posicion (`POSITION_CONTROL`), no por torque. |
| `train.py` | Entrena PPO con `stable_baselines3`, entornos en paralelo (`SubprocVecEnv`), checkpoints periodicos, logging a `logs/` (tensorboard). |
| `enjoy.py` | Carga un `.zip` de SB3 y corre la politica en GUI, en tiempo real. |
| `requirements.txt` | Versiones pineadas, probadas juntas. |
| `colab_train.ipynb` | Entrena en Google Colab (gratis) en vez de tu laptop. Auto-resume, checkpoints persistidos en Drive, video del gait sin GUI. Ver seccion "Entrenar en la nube" abajo. |

## Uso

Generar el URDF (opcional, `quad_env.py` lo hace solo si falta):
```bash
python generate_urdf.py
```

Entrenar:
```bash
python train.py --n-envs 8 --timesteps 2000000
```

Continuar un entrenamiento que se corto (Ctrl+C, cierre de terminal, corte de luz):
```bash
python train.py --resume checkpoints\ppo_quadruped_400000_steps.zip --timesteps 1600000
```
`--timesteps` acá es la cantidad ADICIONAL a correr desde donde quedo (no el total
absoluto), el contador de steps sigue sumando desde el checkpoint. Tensorboard va a
abrir una subcarpeta de log nueva para este tramo (mismo `--run-name` => se numera
sola, ej. `ppo_quadruped_2`) en vez de continuar literalmente la misma curva, pero el
eje de timesteps es continuo entre tramos.

Ver progreso en tensorboard:
```bash
tensorboard --logdir logs
```

## Entrenar en la nube (sin depender de la laptop)

Abrí `colab_train.ipynb` en [Google Colab](https://colab.research.google.com) (`Archivo >
Subir notebook`, o directo desde GitHub apuntando a este repo). Corre el mismo `train.py`
pero en los servidores de Colab: monta tu Google Drive, clona el repo ahí (así los
checkpoints sobreviven a que Colab te desconecte solo, cosa que hace cada rato), instala
`requirements.txt` (en Linux `pybullet` sí tiene wheel, no hace falta compilar como en
Windows), y entrena en tandas con auto-resume -- cada vez que volvés a correr la celda de
entrenamiento, sea el mismo día o diez días después, sigue desde el último checkpoint
guardado en Drive, no arranca de cero.

**Importante**: esto es CPU-bound (la física de PyBullet, no la red), la GPU gratis de
Colab no acelera nada acá -- dejá el runtime en CPU. Lo que sí importa es la cantidad de
vCPUs (gratis suele ser 2, similar o menos que una laptop, así que la ventaja no es
velocidad sino no tener que dejar la laptop prendida).

Como Colab no tiene pantalla, `enjoy.py` (que abre GUI) no sirve ahí -- el notebook
incluye una celda que graba la política en un `.mp4` en modo headless para verla inline
o bajarla de Drive.

Ver la politica entrenada:
```bash
python enjoy.py checkpoints/ppo_quadruped_final.zip
```

Smoke test rapido (pocos miles de steps, valida que todo el pipeline corre
sin errores de shape/tipo, no espera que camine bien):
```bash
python train.py --smoke-test --n-envs 2 --no-subproc
```

## Que esperar en el entrenamiento

Ordenes de magnitud, no numeros exactos (dependen de la semilla y de que
tan bien terminen quedando los parametros de `config.py`):

- **Primeros ~100k-300k timesteps**: la politica basicamente aprende a no
  caerse de inmediato. El reward promedio por episodio deberia subir desde
  muy negativo (cae casi enseguida, `REWARD_FALL_PENALTY` domina) hacia
  valores cercanos a 0 o levemente positivos.
- **~500k-1.5M timesteps**: empieza a aparecer movimiento hacia adelante
  consistente, aunque torpe/asimetrico. `ep_len_mean` (duracion de episodio)
  deberia acercarse a `MAX_EPISODE_STEPS` (1000) la mayor parte del tiempo.
- **2M+ timesteps**: marcha mas fluida y con mayor velocidad hacia adelante,
  si el reward shaping y los limites de joint son razonables. No hay
  garantia de una marcha "bonita" sin iterar sobre pesos de reward — el
  objetivo de esta base es que el pipeline funcione, no que el gait sea
  optimo en la primera corrida.

**Que mirar en tensorboard** (`tensorboard --logdir logs`):
- `rollout/ep_rew_mean`: debe tender a subir de forma sostenida (con ruido).
  Si se queda plano en un valor muy negativo por millones de steps, revisar
  pesos de reward o limites de joint (puede que el robot no tenga forma
  fisica de pararse con la pose de reposo configurada).
- `rollout/ep_len_mean`: debe subir hacia `MAX_EPISODE_STEPS`. Si se queda
  bajo (se cae siempre rapido), el problema esta antes de aprender a
  caminar: revisar altura/pose inicial en `config.py`.
- `train/explained_variance`: valores muy cercanos a 0 o negativos
  sostenidos indican que la funcion de valor no esta aprendiendo bien
  (puede necesitar mas `n_steps` o ajustar `learning_rate`).
- `train/approx_kl` y `train/clip_fraction`: si se disparan muy alto,
  la politica esta cambiando demasiado rapido entre updates (bajar
  `learning_rate` o `clip_range`).

## Proximos pasos

### Cuando tengas las medidas reales del robot

Editar **solo `config.py`**:
- `BODY_LENGTH` / `BODY_WIDTH` / `BODY_HEIGHT` / `BODY_MASS`: medidas y peso
  real del chasis (con bateria/electronica puesta, no solo la carcasa vacia).
- `FEMUR_LENGTH` / `TIBIA_LENGTH` / sus masas: largo real de los eslabones.
- `HIP_ABDUCTION_MIN/MAX_DEG`, `HIP_PITCH_MIN/MAX_DEG`, `KNEE_MIN/MAX_DEG`:
  rango mecanico real de cada servo/bracket (con margen de seguridad, no el
  limite fisico absoluto, para no forzar el servo).
- `JOINT_MAX_TORQUE` / `JOINT_MAX_VELOCITY`: de la hoja de datos del servo
  elegido, ya convertido a N*m y rad/s.
- `TARGET_STANDING_HEIGHT` y `STANDING_POSE_DEG`: pose de reposo real medida
  en el robot fisico (o la que quieras usar como punto de partida).

Despues de editar, correr `python generate_urdf.py` y volver a entrenar
desde cero (los limites de joint cambian el espacio de accion, un modelo
viejo no es directamente reusable si cambian mucho los limites).

### Transferencia sim-to-real

Con servos de posicion (no torque), el camino mas directo es:

1. **Extraer trayectorias, no correr la politica en vivo primero.** Cargar
   el modelo entrenado con `enjoy.py` (o un script similar sin GUI), correr
   varios episodios, y loguear la secuencia de 12 angulos objetivo por paso
   (`target_angles` en `quad_env.py`, ya en grados/radianes reales gracias
   al mapeo de `config.py`). Esto da una trayectoria "offline" que se puede
   inspeccionar, suavizar (filtro pasa-bajos entre steps consecutivos para
   no pedirle saltos bruscos al servo) y reproducir en el hardware real via
   PCA9685/servos sin que la laptop tenga que correr inferencia en el loop
   de control critico.
2. Validar esa trayectoria en el robot real con el torso sostenido/en un
   soporte (sin peso completo en las patas) para chequear que los angulos
   son alcanzables y no chocan mecanicamente antes de soltarlo al piso.
3. Recien despues, si hace falta reactividad (no solo replay de trayectoria
   fija), correr inferencia en vivo desde la laptop: leer sensores reales
   (por ahora ninguno mas que lo que ya tengas), construir la observacion
   (angulos/velocidades de los servos + IMU cuando este disponible) en el
   mismo formato que `quad_env.py`, llamar `model.predict()`, y mandar los
   angulos resultantes por el mismo canal de control que uses para los
   servos (igual patron que tu otro proyecto: control desde laptop, no
   on-board).
4. Cuando agregues el sensor de distancia, IMU y camara reales, extender
   `_get_obs()` en `quad_env.py` (y el `observation_space`) para que la
   politica los use durante el entrenamiento, no solo en inferencia —
   entrenar con la misma observacion que vas a tener disponible en runtime
   real evita el gap sim-to-real mas comun (politica que depende de datos
   que en el robot real no existen, ej. posicion absoluta global).

## Validado en esta sesion

- **pybullet en Windows**: no tiene wheel en PyPI (ninguna version) -- hubo que instalar
  Visual C++ Build Tools (`Microsoft.VisualStudio.2022.BuildTools`, workload C++) para que
  `pip install pybullet==3.2.7` compile desde source. Compila y funciona bien una vez
  instalados los Build Tools (~1-2 min de build). Ver nota en "Instalacion" arriba.
- **`requirements.txt`** actualizado a versiones actuales estables verificadas mutuamente
  compatibles contra el indice real de PyPI para Python 3.11 / win_amd64: numpy 2.3.5,
  torch 2.8.0, gymnasium 1.3.0, stable-baselines3 2.9.0, pybullet 3.2.7, tensorboard 2.20.0,
  tqdm 4.67.1, rich 14.2.0. Instalacion completa corrida de punta a punta sin errores.
- **URDF**: `generate_urdf.py` genero `quadruped.urdf` y cargo en PyBullet sin error.
  Confirmado: 16 joints (12 revolute + 4 fixed de pie), nombres y jerarquia correctos
  (`{pata}_hip_abduction_joint` -> `{pata}_hip_pitch_joint` -> `{pata}_knee_joint` -> `{pata}_foot_joint`).
- **`QuadrupedEnv`**: `reset()` + 500 `step()` con acciones aleatorias corridos sin crashear,
  observacion siempre shape `(31,)` y valores finitos, reward finito en cada step.
- **`train.py`** (smoke test, `--smoke-test`, ~4000 timesteps): corrido OK con `DummyVecEnv`
  (`--no-subproc`) y con `SubprocVecEnv` real (default, valida el guard `if __name__ ==
  "__main__":` necesario en Windows para multiprocessing) -- ambos terminaron sin errores de
  shape/tipo y guardaron el `.zip` final. Como es solo un smoke test (no entrenamiento real),
  los checkpoints/logs de esa corrida se borraron despues de validar (estan gitignored:
  `checkpoints/`, `logs/`, `quadruped.urdf` se regeneran solos).
