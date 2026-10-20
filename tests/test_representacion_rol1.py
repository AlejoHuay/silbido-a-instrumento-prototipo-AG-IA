"""Pruebas unitarias y de integración para el Rol 1 (Representación y Extracción).

Verifica formalmente:
1. Reversibilidad e invertibilidad de decodificar(codificar(x)) == x y viceversa.
2. Manejo estricto de límites, clipping defensivo y rechazo de individuos inválidos.
3. Invariantes del espacio de búsqueda y combinatoria (criterio de discretización física).
4. Relaciones acústicas temperadas (Hz <-> MIDI) y persistencia reversible de melodías CSV.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.extraccion import (
    cargar_melodia_csv,
    guardar_melodia_csv,
    hz_a_midi,
    midi_a_hz,
    nombre_nota_midi,
)
from src.representacion import (
    GENES_SCHEMA,
    calcular_tamano_espacio_busqueda,
    codificar,
    decodificar,
    decodificar_a_array,
    generar_individuo_aleatorio,
    generar_poblacion_inicial,
    num_genes,
    obtener_limites_fisicos,
    obtener_nombres_genes,
    obtener_valores_default,
    probar_inversion_codificacion,
    restringir_limites,
    validar_individuo,
)


class TestBiyeccionEInvertibilidad(unittest.TestCase):
    """Pruebas de round-trip y fidelidad entre genotipo [0,1]^8 y fenotipo físico."""

    def test_inversion_valores_default_flauta(self) -> None:
        """El fenotipo por defecto debe reconstruirse con precisión de máquina."""
        self.assertTrue(
            probar_inversion_codificacion(tolerancia=1e-12),
            "Fallo en la prueba de invertibilidad del fenotipo por defecto.",
        )

        fenotipo_default = obtener_valores_default(normalizado=False)
        crom_norm = codificar(fenotipo_default)
        fenotipo_recuperado = decodificar(crom_norm)

        for gen_nombre, valor_esperado in fenotipo_default.items():
            self.assertAlmostEqual(
                valor_esperado,
                fenotipo_recuperado[gen_nombre],
                places=10,
                msg=f"Discrepancia en gen '{gen_nombre}' tras decodificar(codificar(x)).",
            )

    def test_inversion_genotipo_a_fenotipo_y_retorno(self) -> None:
        """codificar(decodificar(g)) debe ser idéntico a g para cualquier g en [0,1]^8."""
        rng = np.random.default_rng(42)
        for _ in range(50):
            genotipo_orig = rng.uniform(0.0, 1.0, size=num_genes())
            fenotipo = decodificar(genotipo_orig)
            genotipo_recodificado = codificar(fenotipo)
            np.testing.assert_allclose(
                genotipo_orig,
                genotipo_recodificado,
                atol=1e-12,
                err_msg="Fallo en la biyección codificar(decodificar(g)) == g.",
            )

    def test_inversion_masiva_1000_individuos(self) -> None:
        """Verifica la propiedad de invertibilidad sobre 1,000 muestras aleatorias."""
        rng = np.random.default_rng(2026)
        errores_maximos = []
        mins, maxs = obtener_limites_fisicos()

        for _ in range(1000):
            # Generar fenotipo físico aleatorio dentro de límites
            valores_fisicos = mins + rng.uniform(0.0, 1.0, size=num_genes()) * (maxs - mins)
            crom_norm = codificar(valores_fisicos)
            fenotipo_dict = decodificar(crom_norm)
            valores_recuperados = np.array([fenotipo_dict[g.nombre] for g in GENES_SCHEMA])

            err = np.max(np.abs(valores_fisicos - valores_recuperados))
            errores_maximos.append(err)

        self.assertLess(
            max(errores_maximos),
            1e-12,
            f"Error de reconstrucción numérico excesivo: {max(errores_maximos):.2e} > 1e-12",
        )

    def test_decodificar_a_array_coincide_con_dict(self) -> None:
        """decodificar_a_array debe coincidir exactamente con el diccionario de decodificar."""
        rng = np.random.default_rng(101)
        crom = rng.uniform(0.0, 1.0, size=num_genes())

        array_fisico = decodificar_a_array(crom)
        dict_fisico = decodificar(crom)
        nombres = obtener_nombres_genes()

        for idx, nombre in enumerate(nombres):
            self.assertEqual(array_fisico[idx], dict_fisico[nombre])


class TestLimitesYRobustez(unittest.TestCase):
    """Pruebas defensivas: clipping, validación de restricciones y anomalías."""

    def test_mapeo_limites_extremos(self) -> None:
        """Los extremos físicos min y max deben mapear estrictamente a 0.0 y 1.0."""
        mins, maxs = obtener_limites_fisicos()

        genotipo_mins = codificar(mins)
        np.testing.assert_array_equal(
            genotipo_mins,
            np.zeros(num_genes()),
            err_msg="El límite físico inferior no mapea a 0.0.",
        )

        genotipo_maxs = codificar(maxs)
        np.testing.assert_array_equal(
            genotipo_maxs,
            np.ones(num_genes()),
            err_msg="El límite físico superior no mapea a 1.0.",
        )

    def test_restringir_limites_aplica_clipping_defensivo(self) -> None:
        """restringir_limites debe recortar mutaciones o cruces desbordados a [0.0, 1.0]."""
        crom_desbordado = np.array([-0.50, 1.30, 0.50, -0.01, 1.05, 0.80, 0.20, 0.04])
        crom_recortado = restringir_limites(crom_desbordado, normalizado=True)

        self.assertTrue(np.all(crom_recortado >= 0.0), "Valores negativos no recortados.")
        self.assertTrue(np.all(crom_recortado <= 1.0), "Valores > 1.0 no recortados.")
        self.assertEqual(crom_recortado[0], 0.0)
        self.assertEqual(crom_recortado[1], 1.0)
        self.assertEqual(crom_recortado[4], 1.0)

    def test_validar_individuo_rechaza_dimensiones_invalidas(self) -> None:
        """validar_individuo debe rechazar vectores con longitud distinta a num_genes()."""
        valido_7, _ = validar_individuo(np.zeros(7))
        self.assertFalse(valido_7, "Aceptó erróneamente un cromosoma de 7 genes.")

        valido_9, _ = validar_individuo(np.zeros(9))
        self.assertFalse(valido_9, "Aceptó erróneamente un cromosoma de 9 genes.")

    def test_validar_individuo_rechaza_nan_e_infinito(self) -> None:
        """validar_individuo debe rechazar cromosomas con NaN o Infinitos."""
        crom_nan = np.full(num_genes(), 0.5)
        crom_nan[2] = np.nan
        valido, msg = validar_individuo(crom_nan)
        self.assertFalse(valido)
        self.assertIn("NaN", msg)

        crom_inf = np.full(num_genes(), 0.5)
        crom_inf[0] = np.inf
        valido, _ = validar_individuo(crom_inf)
        self.assertFalse(valido)

    def test_poblacion_inicial_generada_es_valida(self) -> None:
        """generar_poblacion_inicial debe producir matrices (N, 8) válidas."""
        rng = np.random.default_rng(777)
        N = 25
        poblacion = generar_poblacion_inicial(N, normalizado=True, rng=rng)

        self.assertEqual(poblacion.shape, (N, num_genes()))
        self.assertTrue(np.all(poblacion >= 0.0))
        self.assertTrue(np.all(poblacion <= 1.0))

        for ind in poblacion:
            valido, msg = validar_individuo(ind)
            self.assertTrue(valido, f"Individuo generado inválido: {msg}")


class TestEspacioCombinatorio(unittest.TestCase):
    """Verificación de las cifras matemáticas exactas del espacio de búsqueda."""

    def test_niveles_por_gen_y_combinatoria_exacta(self) -> None:
        """Ratifica los niveles, combinaciones y bits acordados con resolución 0.001."""
        res = calcular_tamano_espacio_busqueda(resolucion=0.001)

        self.assertEqual(res["num_genes"], 8)
        self.assertEqual(res["resolucion_utilizada"], 0.001)

        # Niveles esperados con paso físico 0.001: floor((max - min)/0.001) + 1
        niveles_esperados = {
            "amp_arm1": 901,
            "amp_arm2": 801,
            "amp_arm3": 501,
            "ataque_s": 246,
            "decaimiento_s": 296,
            "sostenido_rel": 901,
            "relajacion_s": 296,
            "ruido_soplo": 251,
        }
        self.assertEqual(res["estados_por_gen"], niveles_esperados)

        # Total combinatorio exacto
        combinatoria_esperada = 1762430802969797099136
        self.assertEqual(res["estados_totales"], combinatoria_esperada)
        self.assertEqual(res["estados_totales_notacion_cientifica"], "1.76e+21")

        # Bits de información: ~70.58 bits
        self.assertAlmostEqual(res["bits_equivalentes"], 70.578, places=2)

        # Años estimados (> 5.5e10 años)
        self.assertGreater(res["tiempo_estimado_anos"], 5.0e10)


class TestExtraccionAcustica(unittest.TestCase):
    """Pruebas del dominio acústico: conversión Hz <-> MIDI y persistencia CSV."""

    def test_conversion_temperada_hz_y_midi(self) -> None:
        """Verifica la relación biunívoca en notas de afinación de concierto."""
        # La4 = 440 Hz = MIDI 69
        self.assertEqual(hz_a_midi(440.0), 69)
        self.assertAlmostEqual(float(midi_a_hz(69)), 440.0, places=2)

        # Sol5 = 783.99 Hz = MIDI 79
        self.assertEqual(hz_a_midi(783.99), 79)
        self.assertAlmostEqual(float(midi_a_hz(79)), 783.99, places=1)

        # Do7 = 2093.00 Hz = MIDI 96
        self.assertEqual(hz_a_midi(2093.0), 96)

        # Silencios (<= 0 o NaN deben ser -1)
        self.assertEqual(hz_a_midi(0.0), -1)
        self.assertEqual(hz_a_midi(-10.0), -1)
        self.assertEqual(hz_a_midi(np.nan), -1)
        self.assertEqual(float(midi_a_hz(-1)), 0.0)

    def test_nombre_nota_midi(self) -> None:
        """Verifica la nomenclatura musical legible."""
        self.assertIn("La4", nombre_nota_midi(69))
        self.assertIn("Sol5", nombre_nota_midi(79))
        self.assertIn("Silencio", nombre_nota_midi(-1))

    def test_persistencia_csv_roundtrip(self) -> None:
        """guardar_melodia_csv y cargar_melodia_csv deben ser perfectamente reversibles."""
        notas_orig = np.array([-1, 93, 96, -1, 92, 95], dtype=np.int32)
        duraciones_orig = np.array([0.128, 0.244, 0.104, 0.139, 0.244, 0.255], dtype=np.float64)

        with tempfile.TemporaryDirectory() as tmpdir:
            ruta_csv = Path(tmpdir) / "test_melodia.csv"
            guardar_melodia_csv(notas_orig, duraciones_orig, ruta_csv)

            self.assertTrue(ruta_csv.is_file(), "El archivo CSV no fue creado.")

            notas_leidas, duraciones_leidas = cargar_melodia_csv(ruta_csv)

            np.testing.assert_array_equal(notas_orig, notas_leidas)
            np.testing.assert_allclose(duraciones_orig, duraciones_leidas, atol=1e-3)


if __name__ == "__main__":
    unittest.main()
