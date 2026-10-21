import unittest

import numpy as np

from src.algoritmo_genetico import (
    calcular_estadisticas,
    detectar_estancamiento,
    ejecutar_ag,
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

    def test_rechaza_tolerancias_no_finitas_y_torneo_incompatible(self):
        for valor in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    ConfiguracionAG(tolerancia_mejora=valor)
                with self.assertRaises(ValueError):
                    detectar_estancamiento([0.5] * 11, tolerancia=valor)
        with self.assertRaises(ValueError):
            ConfiguracionAG(tam_poblacion=3, tam_torneo=4)


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

    def test_estancamiento_mide_mejora_acumulada_no_individual(self):
        # Cada mejora es menor que 1e-4, pero la suma en diez pasos no lo es.
        historial = [0.5 + i * 0.00002 for i in range(11)]
        self.assertFalse(detectar_estancamiento(historial))
        self.assertTrue(detectar_estancamiento(historial + [historial[-1]] * 10))
        # Igualdad exacta con un umbral representable: no se detiene.
        self.assertFalse(detectar_estancamiento([0.0, 0.125], 1, 0.125))


class TestCicloCompletoAG(unittest.TestCase):
    def setUp(self):
        self.config = ConfiguracionAG(
            tam_poblacion=6,
            max_generaciones=3,
            elitismo=2,
            paciencia_estancamiento=10,
            tolerancia_mejora=0.0,
            semilla=17,
        )

    def test_corrida_es_reproducible_y_cuenta_evaluaciones_reales(self):
        llamadas = []

        def aptitud(individuo):
            llamadas.append(individuo.copy())
            return float(np.mean(individuo))

        primero = ejecutar_ag(aptitud, self.config)
        segundo = ejecutar_ag(lambda ind: float(np.mean(ind)), self.config)

        self.assertEqual(len(llamadas), 6 * 4)
        self.assertEqual(primero["evaluaciones"], 6 * 4)
        self.assertEqual(primero["generaciones_ejecutadas"], 3)
        self.assertEqual(primero["motivo_parada"], "max_generaciones")
        self.assertEqual(len(primero["historial"]), 4)
        self.assertEqual(primero["mejor_fitness"], segundo["mejor_fitness"])
        np.testing.assert_array_equal(
            primero["mejor_individuo"], segundo["mejor_individuo"]
        )
        np.testing.assert_array_equal(
            primero["poblacion_final"], segundo["poblacion_final"]
        )
        self.assertTrue(np.all(np.diff(primero["historial_mejor_fitness"]) >= 0))

    def test_estancamiento_detiene_en_ventana_completa(self):
        config = ConfiguracionAG(
            tam_poblacion=5,
            max_generaciones=20,
            elitismo=1,
            paciencia_estancamiento=2,
            tolerancia_mejora=1e-4,
        )
        resultado = ejecutar_ag(lambda _: 0.5, config)
        self.assertEqual(resultado["motivo_parada"], "estancamiento")
        self.assertEqual(resultado["generaciones_ejecutadas"], 2)
        self.assertEqual(resultado["evaluaciones"], 5 * 3)

    def test_admite_las_ocho_combinaciones_de_operadores(self):
        config = ConfiguracionAG(
            tam_poblacion=5,
            max_generaciones=1,
            elitismo=1,
            semilla=9,
        )
        for seleccion in ("torneo", "sus"):
            for cruce in ("blend", "uniforme"):
                for mutacion in ("gaussiana", "no_uniforme"):
                    with self.subTest(
                        seleccion=seleccion,
                        cruce=cruce,
                        mutacion=mutacion,
                    ):
                        resultado = ejecutar_ag(
                            lambda ind: float(np.mean(ind)),
                            config,
                            seleccion=seleccion,
                            cruce=cruce,
                            mutacion=mutacion,
                        )
                        self.assertEqual(resultado["poblacion_final"].shape, (5, 8))
                        self.assertTrue(np.all(
                            (resultado["poblacion_final"] >= 0.0)
                            & (resultado["poblacion_final"] <= 1.0)
                        ))

    def test_rechaza_dependencias_y_opciones_invalidas(self):
        with self.assertRaises(ValueError):
            ejecutar_ag(None, self.config)
        with self.assertRaises(ValueError):
            ejecutar_ag(lambda _: 0.0, object())
        for argumento, valor in (
            ("seleccion", "ruleta"),
            ("cruce", "ox"),
            ("mutacion", "swap"),
        ):
            with self.subTest(argumento=argumento):
                with self.assertRaises(ValueError):
                    ejecutar_ag(
                        lambda _: 0.0,
                        self.config,
                        **{argumento: valor},
                    )
        for argumento, valor in (
            ("alpha", -0.1),
            ("sigma", float("nan")),
            ("b", 0.0),
        ):
            with self.subTest(argumento=argumento):
                with self.assertRaises(ValueError):
                    ejecutar_ag(
                        lambda _: 0.0,
                        self.config,
                        **{argumento: valor},
                    )


if __name__ == "__main__":
    unittest.main()
