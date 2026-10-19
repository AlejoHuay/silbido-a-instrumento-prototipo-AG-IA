import unittest

import numpy as np

from src.algoritmo_genetico import (
    calcular_estadisticas,
    detectar_estancamiento,
    evaluar_poblacion,
    inicializar_poblacion,
    seleccionar_elites,
)
from src.configuracion import ConfiguracionAG, crear_plan_experimental


class TestConfiguracionAG(unittest.TestCase):
    def test_valores_acordados(self):
        config = ConfiguracionAG()
        self.assertEqual(config.tam_poblacion, 50)
        self.assertEqual(config.elitismo, 2)
        self.assertEqual(config.tam_torneo, 3)
        self.assertEqual(config.max_generaciones, 50)

    def test_rechaza_configuracion_invalida(self):
        with self.assertRaises(ValueError):
            ConfiguracionAG(tam_poblacion=2)
        with self.assertRaises(ValueError):
            ConfiguracionAG(tam_poblacion=3, elitismo=3)
        with self.assertRaises(ValueError):
            ConfiguracionAG(probabilidad_mutacion=1.1)

    def test_plan_tiene_doce_configuraciones_unicas(self):
        plan = crear_plan_experimental()
        claves = {
            (
                c.tam_poblacion,
                c.elitismo,
                c.probabilidad_mutacion,
            )
            for c in plan
        }
        self.assertEqual(len(plan), 12)
        self.assertEqual(len(claves), 12)


class TestDinamicaPoblacional(unittest.TestCase):
    def setUp(self):
        self.config = ConfiguracionAG(tam_poblacion=5, elitismo=2)

    def test_inicializacion_es_reproducible_y_valida(self):
        pob_a = inicializar_poblacion(self.config)
        pob_b = inicializar_poblacion(self.config)
        np.testing.assert_array_equal(pob_a, pob_b)
        self.assertEqual(pob_a.shape, (5, 8))
        self.assertTrue(np.all((0.0 <= pob_a) & (pob_a <= 1.0)))

    def test_evaluacion_conserva_orden_y_entradas(self):
        poblacion = inicializar_poblacion(self.config)
        original = poblacion.copy()
        fitness = evaluar_poblacion(poblacion, lambda ind: ind[0])
        np.testing.assert_allclose(fitness, poblacion[:, 0])
        np.testing.assert_array_equal(poblacion, original)

    def test_elitismo_maximiza_desempata_estable_y_copia(self):
        poblacion = inicializar_poblacion(self.config)
        fitness = np.array([0.8, 0.9, 0.9, 0.1, 0.7])
        elites = seleccionar_elites(poblacion, fitness, cantidad=2)
        np.testing.assert_array_equal(elites, poblacion[[1, 2]])
        self.assertFalse(np.shares_memory(elites, poblacion))

    def test_estadisticas(self):
        poblacion = inicializar_poblacion(self.config)
        fitness = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        resumen = calcular_estadisticas(poblacion, fitness, generacion=0)
        self.assertAlmostEqual(resumen.fitness_maximo, 0.9)
        self.assertAlmostEqual(resumen.fitness_medio, 0.5)
        self.assertGreater(resumen.diversidad_genetica, 0.0)

    def test_estancamiento_exige_ventana_completa(self):
        self.assertFalse(
            detectar_estancamiento([0.5] * 10, paciencia=10)
        )
        self.assertTrue(
            detectar_estancamiento([0.5] * 11, paciencia=10)
        )
        self.assertFalse(
            detectar_estancamiento(
                [0.5] * 10 + [0.5002],
                paciencia=10,
                tolerancia=1e-4,
            )
        )


if __name__ == "__main__":
    unittest.main()
