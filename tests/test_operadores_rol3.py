"""Propiedades de los operadores continuos y comprobación con audio real."""

import json
from pathlib import Path
import unittest
from unittest.mock import Mock

import numpy as np

from src.operadores import (
    seleccion_torneo, seleccion_sus, cruce_blend, cruce_uniforme,
    mutacion_gaussiana, mutacion_no_uniforme,
)
from src.representacion import num_genes, generar_poblacion_inicial, validar_individuo


class TestOperadoresRol3(unittest.TestCase):
    def setUp(self):
        self.d = num_genes()
        self.p = np.array([np.full(self.d, x) for x in (0.2, 0.5, 0.8)])

    def comprobar_hijo(self, hijo):
        self.assertEqual(hijo.shape, (self.d,))
        self.assertEqual(hijo.dtype, np.float64)
        valido, mensaje = validar_individuo(hijo)
        self.assertTrue(valido, mensaje)

    def test_torneo_maximo_empate_y_copia(self):
        original = self.p.copy()
        fits = np.array([-3.0, 2.0, -1.0])
        ganador = seleccion_torneo(self.p, fits, rng=np.random.default_rng(7))
        np.testing.assert_array_equal(ganador, self.p[1])
        ganador[0] = 0
        np.testing.assert_array_equal(self.p, original)
        np.testing.assert_array_equal(fits, [-3, 2, -1])
        indices = np.random.default_rng(42).choice(3, 3, replace=False)
        empate = seleccion_torneo(self.p, [1, 1, 1], rng=np.random.default_rng(42))
        np.testing.assert_array_equal(empate, self.p[indices[0]])

    def test_torneo_reproducible_y_rechaza_entradas_invalidas(self):
        a, b = np.random.default_rng(9), np.random.default_rng(9)
        for _ in range(5):
            np.testing.assert_array_equal(
                seleccion_torneo(self.p, [1, 2, 3], k=2, rng=a),
                seleccion_torneo(self.p, [1, 2, 3], k=2, rng=b),
            )
        for pob, fits, k in [(self.p[:2], [1, 2], 3), (self.p, [1], 3),
                             (self.p, [1, np.inf, 3], 3), (self.p, [1, 2, 3], True)]:
            with self.subTest(k=k, fits=fits), self.assertRaises(ValueError):
                seleccion_torneo(pob, fits, k)

    def test_sus_un_inicio_punteros_y_copias_repetidas(self):
        rng = Mock()
        rng.random.return_value = 0.5
        fits = np.array([1.0, 2.0, 1.0])
        lote = seleccion_sus(self.p, fits, 4, rng)
        # Punteros 0.125, 0.375, 0.625, 0.875: no cuatro ruletas.
        np.testing.assert_array_equal(lote, self.p[[0, 1, 1, 2]])
        rng.random.assert_called_once_with()
        self.assertFalse(np.shares_memory(lote, self.p))
        self.assertFalse(np.shares_memory(lote[1], lote[2]))
        lote[1, 0] = 0
        self.assertEqual(lote[2, 0], 0.5)
        np.testing.assert_array_equal(fits, [1, 2, 1])

    def test_sus_ceros_y_pesos_extremos(self):
        rng = Mock()
        rng.random.return_value = 0.0
        np.testing.assert_array_equal(seleccion_sus(self.p, [0, 0, 0], 3, rng), self.p)
        # Los intervalos de peso cero no deben ganar ni con puntero inicial 0.
        lote = seleccion_sus(self.p, [0, 1, 0], 5, rng)
        np.testing.assert_array_equal(lote, np.repeat(self.p[1:2], 5, axis=0))
        with np.errstate(over="raise", invalid="raise"):
            lote = seleccion_sus(self.p, [1e308, 1e308, 0], 4, rng)
        np.testing.assert_array_equal(lote, self.p[[0, 0, 1, 1]])

    def test_sus_reproducibilidad_y_validacion(self):
        for fits in ([1, 2, 3], [0, 0, 0]):
            np.testing.assert_array_equal(
                seleccion_sus(self.p, fits, 9, np.random.default_rng(42)),
                seleccion_sus(self.p, fits, 9, np.random.default_rng(42)),
            )
        for cantidad in (0, -1, 1.2, True, np.bool_(False)):
            with self.subTest(cantidad=cantidad), self.assertRaises(ValueError):
                seleccion_sus(self.p, [1, 2, 3], cantidad)
        for fits in ([-1, 2, 3], [1, np.nan, 3], [1, np.inf, 3], [1], [[1, 2, 3]]):
            with self.subTest(fits=fits), self.assertRaises(ValueError):
                seleccion_sus(self.p, fits, 2)

    def test_cruces_validos_independientes_y_padres_intactos(self):
        original = self.p.copy()
        for cruzar in (cruce_blend, cruce_uniforme):
            hijos = cruzar(self.p[0], self.p[2], rng=np.random.default_rng(7))
            self.assertIsInstance(hijos, tuple)
            self.assertEqual(len(hijos), 2)
            for hijo in hijos:
                self.comprobar_hijo(hijo)
                self.assertFalse(np.shares_memory(hijo, self.p))
            self.assertFalse(np.shares_memory(*hijos))
            hijos[0][0] = 0
            np.testing.assert_array_equal(self.p, original)

    def test_uniforme_herencia_complementaria_mascara_por_gen(self):
        rng = Mock()
        valores = np.linspace(0, 0.99, self.d)
        rng.random.return_value = valores
        a, b = cruce_uniforme(self.p[0], self.p[2], rng=rng)
        np.testing.assert_array_equal(a, np.where(valores < 0.5, self.p[2], self.p[0]))
        np.testing.assert_array_equal(b, np.where(valores < 0.5, self.p[0], self.p[2]))
        rng.random.assert_called_once_with(self.d)

    def test_blend_intervalo_y_clipping(self):
        rng = Mock()
        rng.uniform.side_effect = [np.full(self.d, -0.1), np.full(self.d, 1.1)]
        a, b = cruce_blend(self.p[0], self.p[2], alpha=0.5, rng=rng)
        for llamada in rng.uniform.call_args_list:
            np.testing.assert_allclose(llamada.args[0], -0.1)
            np.testing.assert_allclose(llamada.args[1], 1.1)
        np.testing.assert_array_equal(a, np.zeros(self.d))
        np.testing.assert_array_equal(b, np.ones(self.d))
        a, b = cruce_blend(self.p[0], self.p[0], rng=np.random.default_rng(42))
        np.testing.assert_array_equal(a, self.p[0])
        np.testing.assert_array_equal(b, self.p[0])

    def test_mutaciones_probabilidad_cero_y_copias(self):
        for mutar in (
            lambda x: mutacion_gaussiana(x, p_mut=0, rng=np.random.default_rng(7)),
            lambda x: mutacion_no_uniforme(x, 0, 50, p_mut=0, rng=np.random.default_rng(7)),
        ):
            hijo = mutar(self.p[1])
            np.testing.assert_array_equal(hijo, self.p[1])
            self.assertFalse(np.shares_memory(hijo, self.p))

    def test_gaussiana_selecciona_todos_y_respeta_mascara(self):
        rng = Mock()
        rng.random.return_value = np.full(self.d, 0.9)
        rng.normal.return_value = np.full(self.d, 0.1)
        hijo = mutacion_gaussiana(self.p[1], p_mut=1, sigma=0.08, rng=rng)
        np.testing.assert_allclose(hijo, 0.6)
        rng.normal.assert_called_once_with(0.0, 0.08, size=self.d)
        rng.reset_mock()
        valores = np.linspace(0, 0.99, self.d)
        rng.random.return_value = valores
        rng.normal.return_value = np.full(np.count_nonzero(valores < 0.5), 0.1)
        hijo = mutacion_gaussiana(self.p[1], p_mut=0.5, rng=rng)
        np.testing.assert_allclose(hijo, np.where(valores < 0.5, 0.6, 0.5))
        np.testing.assert_array_equal(self.p[1], np.full(self.d, 0.5))

    def test_no_uniforme_formula_direcciones_y_todos_los_genes(self):
        rng = Mock()
        direcciones = np.linspace(0, 0.99, self.d)
        rng.random.side_effect = [np.full(self.d, 0.9), direcciones, np.full(self.d, 0.25)]
        hijo = mutacion_no_uniforme(self.p[1], 0, 50, p_mut=1, rng=rng)
        np.testing.assert_allclose(hijo, np.where(direcciones < 0.5, 0.875, 0.125))
        self.assertEqual([c.args for c in rng.random.call_args_list], [(self.d,)] * 3)
        np.testing.assert_array_equal(self.p[1], np.full(self.d, 0.5))

    def test_no_uniforme_final_y_reduccion_temporal(self):
        rng = Mock()
        final = mutacion_no_uniforme(self.p[1], 50, 50, p_mut=1, rng=rng)
        np.testing.assert_array_equal(final, self.p[1])
        self.assertFalse(np.shares_memory(final, self.p))
        rng.random.assert_not_called()
        temprano = mutacion_no_uniforme(self.p[1], 0, 50, p_mut=1, rng=np.random.default_rng(7))
        tarde = mutacion_no_uniforme(self.p[1], 40, 50, p_mut=1, rng=np.random.default_rng(7))
        self.assertTrue(np.all(np.abs(temprano - 0.5) >= np.abs(tarde - 0.5)))
        self.assertTrue(np.any(np.abs(temprano - 0.5) > np.abs(tarde - 0.5)))

    def test_variantes_reproducibles(self):
        operaciones = [
            lambda r: cruce_blend(self.p[0], self.p[2], rng=r),
            lambda r: cruce_uniforme(self.p[0], self.p[2], rng=r),
            lambda r: mutacion_gaussiana(self.p[1], p_mut=1, rng=r),
            lambda r: mutacion_no_uniforme(self.p[1], 5, 50, p_mut=1, rng=r),
        ]
        for operar in operaciones:
            a, b = np.random.default_rng(42), np.random.default_rng(42)
            for _ in range(3):
                np.testing.assert_array_equal(operar(a), operar(b))

    def test_rechazo_parametros_invalidos(self):
        for valor in (np.nan, np.inf, -np.inf, -0.1, True, "0.5"):
            for operar in (
                lambda: cruce_blend(self.p[0], self.p[1], alpha=valor),
                lambda: mutacion_gaussiana(self.p[0], sigma=valor),
                lambda: mutacion_gaussiana(self.p[0], p_mut=valor),
                lambda: mutacion_no_uniforme(self.p[0], 0, 50, p_mut=valor),
                lambda: mutacion_no_uniforme(self.p[0], 0, 50, b=valor),
            ):
                with self.subTest(valor=valor), self.assertRaises(ValueError):
                    operar()
        for mutar in (mutacion_gaussiana, lambda x, **kw: mutacion_no_uniforme(x, 0, 50, **kw)):
            with self.assertRaises(ValueError):
                mutar(self.p[0], p_mut=1.1)
        for t, total in ((-1, 50), (51, 50), (0, 0), (1.5, 50), (True, 50),
                         (0, np.inf), (np.nan, 50), (0, False)):
            with self.subTest(t=t, total=total), self.assertRaises(ValueError):
                mutacion_no_uniforme(self.p[0], t, total)
        with self.assertRaises(ValueError):
            mutacion_no_uniforme(self.p[0], 0, 50, b=0)

    def test_rechazo_formas_genes_no_finitos_y_fuera_de_rango(self):
        invalidos = [np.zeros(self.d + 1), np.zeros((self.d, 1))]
        for valor in (np.nan, np.inf, -np.inf, -0.01, 1.01):
            x = self.p[0].copy()
            x[0] = valor
            invalidos.append(x)
        for x in invalidos:
            for operar in (
                lambda: cruce_blend(x, self.p[1]),
                lambda: cruce_uniforme(self.p[1], x),
                lambda: mutacion_gaussiana(x),
                lambda: mutacion_no_uniforme(x, 50, 50),
                lambda: seleccion_sus(np.array([x]), [1], 1),
            ):
                with self.subTest(forma=x.shape), self.assertRaises(ValueError):
                    operar()
        for pob in (np.empty((0, self.d)), np.zeros(self.d), np.zeros((3, self.d+1))):
            with self.assertRaises(ValueError):
                seleccion_sus(pob, [1, 2, 3], 3)

    def test_hijos_evaluables_con_referencia_real(self):
        # Sin sustitutos ni resultados guardados: falla si faltan datos/dependencias.
        import soundfile as sf
        from src.extraccion import cargar_melodia_csv
        from src.fitness import evaluar_individuo
        from src.algoritmo_genetico import evaluar_poblacion

        raiz = Path(__file__).resolve().parents[1]
        notas, duraciones = cargar_melodia_csv(raiz / 'datos/procesados/melodia_01.csv')
        ruta = raiz / 'datos/audio/referencias/flauta_referencia_01.wav'
        ref, sr = sf.read(ruta, dtype='float32')
        meta = json.loads(ruta.with_suffix('.json').read_text(encoding='utf-8'))
        np.testing.assert_array_equal(notas, meta['notas'])
        np.testing.assert_array_equal(duraciones, meta['duraciones_s'])
        self.assertEqual(sr, 22050)
        self.assertEqual(len(ref), round(duraciones.sum() * sr))
        rng = np.random.default_rng(2026)
        padres = generar_poblacion_inicial(2, rng=rng)
        hijos = cruce_blend(*padres, rng=rng) + cruce_uniforme(*padres, rng=rng)
        descendientes = np.array([
            mutacion_gaussiana(hijos[0], p_mut=1, rng=rng),
            mutacion_no_uniforme(hijos[1], 0, 50, p_mut=1, rng=rng),
            *hijos[2:],
        ])
        for hijo in descendientes:
            self.comprobar_hijo(hijo)
        aptitudes = evaluar_poblacion(descendientes, lambda g: evaluar_individuo(
            g, notas, duraciones, ref, metrica='stft'))
        self.assertEqual(aptitudes.shape, (4,))
        self.assertTrue(np.all(np.isfinite(aptitudes)))
        self.assertTrue(np.all((aptitudes > 0) & (aptitudes <= 1)))


if __name__ == '__main__':
    unittest.main()
