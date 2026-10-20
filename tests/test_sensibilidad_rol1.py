"""Pruebas unitarias para el análisis de sensibilidad 1D del Rol 1 (Día 3)."""

from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from src.extraccion import cargar_melodia_csv
from src.representacion import num_genes, obtener_valores_default
from src.sensibilidad import (
    barrido_sensibilidad_gen,
    barrido_sensibilidad_todos,
    calcular_ranking_sensibilidad,
    generar_figura_curvas_1d,
    generar_figura_tornado,
)


class TestSensibilidadRol1(unittest.TestCase):
    """Verifica el arnés de análisis de sensibilidad 1D sobre funciones de aptitud."""

    @classmethod
    def setUpClass(cls):
        ruta_csv = Path("datos/procesados/melodia_01.csv")
        cls.notas, cls.duraciones = cargar_melodia_csv(ruta_csv)

        # Referencia sintética controlada para asegurar pruebas deterministas y rápidas
        # Se genera un audio sintético válido con el genoma de referencia
        from src.sintesis import sintetizar_instrumento
        gen_default = obtener_valores_default(normalizado=True)
        cls.ref_audio = sintetizar_instrumento(cls.notas, cls.duraciones, gen_default)

    def test_barrido_gen_valida_entradas(self):
        """Rechaza índices fuera de rango o cantidad de puntos insuficiente."""
        with self.assertRaises(ValueError):
            barrido_sensibilidad_gen(-1, self.notas, self.duraciones, self.ref_audio)

        with self.assertRaises(ValueError):
            barrido_sensibilidad_gen(8, self.notas, self.duraciones, self.ref_audio)

        with self.assertRaises(ValueError):
            barrido_sensibilidad_gen(0, self.notas, self.duraciones, self.ref_audio, num_puntos=1)

        with self.assertRaises(ValueError):
            gen_invalido = np.array([0.5] * 7)  # Dimensión incorrecta
            barrido_sensibilidad_gen(0, self.notas, self.duraciones, self.ref_audio, gen_base=gen_invalido)

    def test_barrido_gen_retorna_dataframe_valido(self):
        """Verifica que el barrido genere un DataFrame con las columnas y tipos correctos."""
        num_puntos = 5
        df = barrido_sensibilidad_gen(
            indice_gen=0,
            notas=self.notas,
            duraciones=self.duraciones,
            referencia_audio=self.ref_audio,
            num_puntos=num_puntos,
        )

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), num_puntos)

        columnas_esperadas = {
            "gen_indice", "gen_nombre", "valor_normalizado", "valor_fisico",
            "error_stft_db", "fitness_stft", "fitness_croma"
        }
        self.assertTrue(columnas_esperadas.issubset(df.columns))

        # Extremos normalizados
        self.assertAlmostEqual(df["valor_normalizado"].iloc[0], 0.0)
        self.assertAlmostEqual(df["valor_normalizado"].iloc[-1], 1.0)

        # Finitud de métricas
        self.assertTrue(np.all(np.isfinite(df["fitness_stft"])))
        self.assertTrue(np.all(np.isfinite(df["fitness_croma"])))

    def test_barrido_todos_y_ranking(self):
        """Verifica la ejecución sobre todos los genes y el cálculo ordenado de rankings."""
        num_puntos = 3  # Rápido para tests unitarios
        df_todos = barrido_sensibilidad_todos(
            notas=self.notas,
            duraciones=self.duraciones,
            referencia_audio=self.ref_audio,
            num_puntos=num_puntos,
        )

        self.assertEqual(len(df_todos), num_genes() * num_puntos)

        df_rank = calcular_ranking_sensibilidad(df_todos)
        self.assertEqual(len(df_rank), num_genes())
        self.assertIn("ranking_stft", df_rank.columns)
        self.assertIn("categoria_stft", df_rank.columns)

        # El ranking debe estar ordenado de mayor a menor delta
        deltas = df_rank["delta_fitness_stft"].to_numpy()
        self.assertTrue(np.all(np.diff(deltas) <= 1e-9))

    def test_generacion_de_figuras(self):
        """Verifica que la generación de gráficos no lance excepciones."""
        df_demo = barrido_sensibilidad_todos(
            notas=self.notas,
            duraciones=self.duraciones,
            referencia_audio=self.ref_audio,
            num_puntos=3,
        )
        df_rank = calcular_ranking_sensibilidad(df_demo)

        fig1 = generar_figura_curvas_1d(df_demo)
        self.assertIsNotNone(fig1)

        fig2 = generar_figura_tornado(df_rank)
        self.assertIsNotNone(fig2)


if __name__ == "__main__":
    unittest.main()
