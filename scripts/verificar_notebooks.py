"""Ejecuta todos los notebooks en kernels nuevos y en una copia aislada.

El proceso se lanza desde el intérprete del entorno que se desea verificar.
Cada notebook recibe un kernel nuevo. La copia temporal evita que las celdas
que generan WAV, CSV, figuras o metadatos modifiquen el árbol de trabajo real.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError


if sys.platform == "win32":
    # pyzmq requiere add_reader/add_writer; el bucle Proactor puede ejecutar
    # todas las celdas y fallar después al cerrar el kernel en Windows.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


NOTEBOOKS = (
    "00_integracion.ipynb",
    "01_rol1_representacion.ipynb",
    "02_rol2_sintesis_fitness.ipynb",
    "03_rol3_operadores.ipynb",
    "04_rol4_dinamica.ipynb",
)


@dataclass(frozen=True)
class ResultadoNotebook:
    nombre: str
    celdas_codigo: int
    segundos: float
    correcto: bool
    detalle: str = ""


def _ignorar_copia(_carpeta: str, nombres: list[str]) -> set[str]:
    excluidos = {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".ipynb_checkpoints",
        ".pytest_cache",
        "temp",
        "tmp",
    }
    return set(nombres) & excluidos


def _version(modulo) -> str:
    return str(getattr(modulo, "__version__", "desconocida"))


def _comprobar_dependencias() -> None:
    import IPython
    import matplotlib
    import numpy
    import pandas
    import scipy
    import soundfile

    print(f"Python: {sys.version.split()[0]}")
    print(f"Ejecutable: {sys.executable}")
    print(
        "Dependencias: "
        f"numpy={_version(numpy)}, "
        f"scipy={_version(scipy)}, "
        f"pandas={_version(pandas)}, "
        f"matplotlib={_version(matplotlib)}, "
        f"soundfile={_version(soundfile)}, "
        f"IPython={_version(IPython)}, "
        f"nbformat={_version(nbformat)}"
    )


def _ejecutar_notebook(
    raiz_copia: Path,
    nombre: str,
    kernel: str,
    timeout: int,
) -> ResultadoNotebook:
    ruta = raiz_copia / "notebooks" / nombre
    notebook = nbformat.read(ruta, as_version=4)
    celdas_codigo = sum(
        celda.cell_type == "code" for celda in notebook.cells
    )
    inicio = time.perf_counter()

    try:
        NotebookClient(
            notebook,
            timeout=timeout,
            kernel_name=kernel,
            resources={"metadata": {"path": str(raiz_copia)}},
        ).execute()
    except CellExecutionError as error:
        transcurrido = time.perf_counter() - inicio
        return ResultadoNotebook(
            nombre=nombre,
            celdas_codigo=celdas_codigo,
            segundos=transcurrido,
            correcto=False,
            detalle=str(error),
        )

    errores = [
        salida
        for celda in notebook.cells
        if celda.cell_type == "code"
        for salida in celda.get("outputs", [])
        if salida.get("output_type") == "error"
    ]
    ejecutadas = sum(
        celda.cell_type == "code" and celda.execution_count is not None
        for celda in notebook.cells
    )
    transcurrido = time.perf_counter() - inicio

    if errores or ejecutadas != celdas_codigo:
        return ResultadoNotebook(
            nombre=nombre,
            celdas_codigo=celdas_codigo,
            segundos=transcurrido,
            correcto=False,
            detalle=(
                f"celdas ejecutadas={ejecutadas}/{celdas_codigo}, "
                f"salidas de error={len(errores)}"
            ),
        )

    return ResultadoNotebook(
        nombre=nombre,
        celdas_codigo=celdas_codigo,
        segundos=transcurrido,
        correcto=True,
    )


def _argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verifica los notebooks en kernels nuevos sin modificar el repo."
        )
    )
    parser.add_argument(
        "--kernel",
        default="python3",
        help="Nombre del kernelspec de Jupyter (por defecto: python3).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Tiempo máximo por celda en segundos (por defecto: 300).",
    )
    parser.add_argument(
        "--solo",
        choices=NOTEBOOKS,
        action="append",
        help="Notebook a ejecutar; puede repetirse. Por defecto ejecuta todos.",
    )
    return parser.parse_args()


def main() -> int:
    argumentos = _argumentos()
    raiz = Path(__file__).resolve().parents[1]
    seleccionados = tuple(argumentos.solo or NOTEBOOKS)

    if argumentos.timeout < 1:
        raise ValueError("--timeout debe ser un entero positivo.")

    _comprobar_dependencias()
    print(f"Kernel solicitado: {argumentos.kernel}")
    print("Cada notebook se ejecutará en un kernel nuevo.")

    # IPython y Jupyter necesitan directorios locales escribibles en entornos
    # restringidos. Se crean dentro del temporal y no contaminan el usuario.
    with tempfile.TemporaryDirectory(prefix="silbido-notebooks-") as temporal:
        temporal = Path(temporal)
        os.environ["IPYTHONDIR"] = str(temporal / "ipython")
        os.environ["JUPYTER_RUNTIME_DIR"] = str(temporal / "jupyter-runtime")

        resultados = []
        for indice, nombre in enumerate(seleccionados, start=1):
            # Una copia por notebook evita que los archivos producidos por uno
            # oculten una dependencia accidental del siguiente.
            raiz_copia = temporal / f"repo-{indice}"
            shutil.copytree(raiz, raiz_copia, ignore=_ignorar_copia)
            print(f"\n[INICIO] {nombre}")
            resultado = _ejecutar_notebook(
                raiz_copia,
                nombre,
                argumentos.kernel,
                argumentos.timeout,
            )
            resultados.append(resultado)
            estado = "OK" if resultado.correcto else "FALLO"
            print(
                f"[{estado}] {nombre}: {resultado.celdas_codigo} celdas "
                f"de código, {resultado.segundos:.2f} s"
            )
            if resultado.detalle:
                print(resultado.detalle)

    correctos = sum(resultado.correcto for resultado in resultados)
    print(f"\nResumen: {correctos}/{len(resultados)} notebooks correctos.")
    return 0 if correctos == len(resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
