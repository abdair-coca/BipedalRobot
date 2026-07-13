"""
Entrena PPO (stable-baselines3) sobre QuadrupedEnv.

Uso:
    python train.py                       # entrenamiento normal
    python train.py --timesteps 5000 --n-envs 2 --smoke-test   # smoke test rapido
    python train.py --resume checkpoints\ppo_quadruped_500000_steps.zip --timesteps 1000000
        # continua un entrenamiento cortado (Ctrl+C, corte de luz, etc). --timesteps
        # es la cantidad ADICIONAL de steps a correr desde donde quedo (no el total
        # absoluto). El contador de timesteps sigue acumulando (no vuelve a 0), pero
        # tensorboard abre una subcarpeta nueva de log para este tramo (mismo --run-name
        # => se numera solo, ej. ppo_quadruped_2) en vez de continuar la misma curva.

Vectorizacion: SubprocVecEnv (un proceso por entorno) por default, cae a
DummyVecEnv si se pide --n-envs 1 o con --no-subproc (mas facil de debuggear,
ej. si un error de PyBullet no muestra bien el traceback en subproceso).

IMPORTANTE (Windows): SubprocVecEnv necesita que la creacion de entornos este
protegida por `if __name__ == "__main__":`, si no cada subproceso reimporta
este archivo y vuelve a lanzar el entrenamiento entero (fork bomb). Por eso
todo el codigo ejecutable esta dentro de main().
"""

import argparse
import os

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv

import config as cfg
from quad_env import QuadrupedEnv


LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
CHECKPOINT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints")


def parse_args():
    p = argparse.ArgumentParser(description="Entrena PPO sobre el cuadrupedo simulado.")
    p.add_argument("--timesteps", type=int, default=2_000_000,
                    help="Total de timesteps de entrenamiento (default 2M, orden de magnitud "
                         "razonable para empezar a ver marcha; ver README).")
    p.add_argument("--n-envs", type=int, default=8, help="Entornos en paralelo (default 8).")
    p.add_argument("--no-subproc", action="store_true",
                    help="Usa DummyVecEnv (un solo proceso) en vez de SubprocVecEnv.")
    p.add_argument("--checkpoint-freq", type=int, default=100_000,
                    help="Cada cuantos timesteps (totales, se divide por n_envs internamente) "
                         "guardar checkpoint (default 100k).")
    p.add_argument("--run-name", type=str, default="ppo_quadruped",
                    help="Nombre del run, usado para logs/ y checkpoints/.")
    p.add_argument("--resume", type=str, default=None,
                    help="Ruta a un .zip de checkpoint para continuar entrenando en vez de "
                         "arrancar una politica nueva (ej. checkpoints/ppo_quadruped_500000_steps.zip).")
    p.add_argument("--smoke-test", action="store_true",
                    help="Reduce n_steps/batch_size para validar que todo corre sin errores "
                         "de shape/tipo en pocos miles de steps, sin esperar convergencia.")
    p.add_argument("--seed", type=int, default=0)
    return p.parse_args()


def make_env_fn(seed):
    def _init():
        env = QuadrupedEnv(render_mode=None)
        env.reset(seed=seed)
        return env
    return _init


def main():
    args = parse_args()
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    vec_env_cls = DummyVecEnv if (args.no_subproc or args.n_envs == 1) else SubprocVecEnv
    env_fns = [make_env_fn(args.seed + i) for i in range(args.n_envs)]
    vec_env = vec_env_cls(env_fns)

    # Hiperparametros PPO razonables para control continuo de 12D con
    # observacion chica (31,). No estan tuneados a fondo, son un punto de
    # partida estandar (similares a los usados en tareas tipo Ant/Walker2d
    # de PyBullet/MuJoCo con SB3) pensado para converger a "algo que camina",
    # no para ser optimo.
    n_steps = 32 if args.smoke_test else 2048
    batch_size = 32 if args.smoke_test else 64
    n_epochs = 4 if args.smoke_test else 10

    if args.resume:
        print(f"Resumiendo entrenamiento desde: {args.resume}")
        model = PPO.load(args.resume, env=vec_env, tensorboard_log=LOG_DIR)
    else:
        model = PPO(
            policy="MlpPolicy",
            env=vec_env,
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=n_epochs,
            learning_rate=3e-4,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.0,
            vf_coef=0.5,
            max_grad_norm=0.5,
            policy_kwargs=dict(net_arch=dict(pi=[256, 256], vf=[256, 256])),
            tensorboard_log=LOG_DIR,
            seed=args.seed,
            verbose=1,
        )

    checkpoint_callback = CheckpointCallback(
        save_freq=max(args.checkpoint_freq // args.n_envs, 1),
        save_path=CHECKPOINT_DIR,
        name_prefix=args.run_name,
    )

    total_timesteps = 4_000 if args.smoke_test else args.timesteps

    model.learn(
        total_timesteps=total_timesteps,
        callback=checkpoint_callback,
        tb_log_name=args.run_name,
        progress_bar=not args.smoke_test,
        reset_num_timesteps=not args.resume,
    )

    final_path = os.path.join(CHECKPOINT_DIR, f"{args.run_name}_final")
    model.save(final_path)
    print(f"Modelo final guardado en: {final_path}.zip")

    vec_env.close()


if __name__ == "__main__":
    main()
