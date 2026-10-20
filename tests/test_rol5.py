import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.configuracion import ConfiguracionAG
from src.evaluacion import (
    construir_registro_corrida,
    guardar_registros_csv,
    resumir_corridas,
)
from src.experimentos import (
    ejecutar_busqueda_aleatoria,
    ejecutar_baselines_pareados,
    ejecutar_corridas_busqueda_aleatoria,
    ejecutar_corridas_ag,
)


class TestBusquedaAleatoria(unittest.TestCase):
    def test_presupuesto_y_semilla_reproducibles(self):
        aptitud = lambda individuo: float(np.mean(individuo))
        primero = ejecutar_busqueda_aleatoria(
            aptitud,
            num_evaluaciones=12,
            semilla=7,
        )
        segundo = ejecutar_busqueda_aleatoria(
            aptitud,
            num_evaluaciones=12,
            semilla=7,
        )
        self.assertEqual(primero["evaluaciones"], 12)
        self.assertEqual(primero["mejor_fitness"], segundo["mejor_fitness"])
        np.testing.assert_array_equal(
            primero["mejor_individuo"],
            segundo["mejor_individuo"],
        )

    def test_rechaza_presupuesto_invalido_o_fitness_no_finito(self):
        with self.assertRaises(ValueError):
            ejecutar_busqueda_aleatoria(
                lambda _: 1.0,
                num_evaluaciones=0,
                semilla=1,
            )
        with self.assertRaises(ValueError):
            ejecutar_busqueda_aleatoria(
                lambda _: float("nan"),
                num_evaluaciones=1,
                semilla=1,
            )

    def test_corridas_baseline_comparten_esquema_y_presupuesto(self):
        registros = ejecutar_corridas_busqueda_aleatoria(
            lambda individuo: float(np.mean(individuo)),
            num_evaluaciones=4,
            semillas=[3, 5],
            metrica="fitness_stft",
        )
        self.assertEqual([fila["metodo"] for fila in registros], [
            "busqueda_aleatoria",
            "busqueda_aleatoria",
        ])
        self.assertEqual([fila["semilla"] for fila in registros], [3, 5])
        self.assertEqual([fila["evaluaciones"] for fila in registros], [4, 4])
        self.assertEqual(
            set(registros[0]),
            set(
                construir_registro_corrida(
                    metodo="test",
                    semilla=0,
                    configuracion={},
                    resultado={"mejor_fitness": 0.0},
                    tiempo_s=0.0,
                    metrica="fitness_stft",
                )
            ),
        )


class TestRegistroYEvaluacion(unittest.TestCase):
    def test_registro_resumen_append_y_no_sobrescritura(self):
        config = ConfiguracionAG(tam_poblacion=3, elitismo=1)
        registro_a = construir_registro_corrida(
            metodo="prueba_unitaria",
            semilla=1,
            configuracion=config,
            resultado={
                "mejor_fitness": 0.5,
                "evaluaciones": 3,
                "generaciones_ejecutadas": 1,
                "mejor_individuo": np.zeros(8),
            },
            tiempo_s=0.25,
            metrica="fitness_stft",
        )
        registro_b = dict(registro_a, semilla=2, mejor_fitness=0.7)
        resumen = resumir_corridas(
            [registro_a, registro_b],
            agrupar_por=("metodo",),
        )
        self.assertEqual(resumen[0]["n"], 2)
        self.assertAlmostEqual(resumen[0]["media"], 0.6)
        self.assertAlmostEqual(
            resumen[0]["desviacion_estandar"],
            np.std([0.5, 0.7], ddof=1),
        )

        with tempfile.TemporaryDirectory() as temporal:
            destino = Path(temporal) / "corridas.csv"
            guardar_registros_csv([registro_a], destino)
            with self.assertRaises(FileExistsError):
                guardar_registros_csv([registro_b], destino)
            guardar_registros_csv([registro_b], destino, anexar=True)
            with destino.open(encoding="utf-8", newline="") as archivo:
                filas = list(csv.DictReader(archivo))
            self.assertEqual(len(filas), 2)
            self.assertEqual(filas[1]["semilla"], "2")

class TestPlanificacionRol5(unittest.TestCase):
    def setUp(self):
        self.config = ConfiguracionAG(
            tam_poblacion=5,
            elitismo=1,
            max_generaciones=2,
        )

    def test_corridas_ag_inyectan_semillas_sin_implementar_ciclo(self):
        recibidas = []

        def runner(config):
            recibidas.append(config.semilla)
            return {
                "mejor_fitness": float(config.semilla),
                "evaluaciones": config.tam_poblacion,
                "generaciones_ejecutadas": 0,
            }

        filas = ejecutar_corridas_ag(
            runner,
            [self.config],
            [11, 12],
            metrica="fitness_stft",
        )
        self.assertEqual(recibidas, [11, 12])
        self.assertEqual([fila["semilla"] for fila in filas], [11, 12])
        self.assertEqual(
            [fila["mejor_fitness"] for fila in filas],
            [11.0, 12.0],
        )

    def test_baseline_rechaza_metrica_distinta_antes_de_evaluar(self):
        fila = {
            "metodo": "algoritmo_genetico", "metrica": "fitness_croma",
            "semilla": 42, "evaluaciones": 3, "configuracion_json": "{}",
        }
        llamadas = []
        with self.assertRaises(ValueError):
            ejecutar_baselines_pareados(
                lambda individuo: llamadas.append(individuo) or 0.5,
                [fila], metrica="fitness_stft",
            )
        self.assertEqual(llamadas, [])

    def test_baseline_cuenta_llamadas_reales_con_presupuestos_distintos(self):
        # Registros de prueba; representan presupuestos tras paradas distintas.
        filas = [
            {"metodo": "algoritmo_genetico", "metrica": "fitness_stft",
             "semilla": 42, "evaluaciones": n, "configuracion_json": "{}"}
            for n in (3, 7)
        ]
        llamadas = []
        resultados = ejecutar_baselines_pareados(
            lambda individuo: llamadas.append(individuo.copy()) or 0.5,
            filas, metrica="fitness_stft",
        )
        self.assertEqual(len(llamadas), 10)
        self.assertEqual([r["evaluaciones"] for r in resultados], [3, 7])

    def test_baseline_pareado_iguala_evaluaciones_semilla_y_configuracion(self):
        corridas_ag = ejecutar_corridas_ag(
            lambda config: {
                "mejor_fitness": 0.5,
                "evaluaciones": config.tam_poblacion * 2,
            },
            [self.config],
            [11, 12],
            metrica="fitness_stft",
        )
        baseline = ejecutar_baselines_pareados(
            lambda individuo: float(np.mean(individuo)),
            corridas_ag,
            metrica="fitness_stft",
        )
        self.assertEqual(
            [fila["evaluaciones"] for fila in baseline],
            [10, 10],
        )
        self.assertEqual(
            [fila["semilla"] for fila in baseline],
            [fila["semilla"] for fila in corridas_ag],
        )
        self.assertEqual(
            [fila["configuracion_json"] for fila in baseline],
            [fila["configuracion_json"] for fila in corridas_ag],
        )
        self.assertEqual(
            [fila["metrica"] for fila in baseline],
            [fila["metrica"] for fila in corridas_ag],
        )

if __name__ == "__main__":
    unittest.main()
