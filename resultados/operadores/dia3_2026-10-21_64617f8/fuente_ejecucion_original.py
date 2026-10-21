"""Protocolo del Día 3 del Rol 3; reutiliza el ciclo y registro existentes.

Ejecutar: python -m src.comparacion_operadores --ejecutar RUTA
Consultar/verificar: python -m src.comparacion_operadores --resumir RUTA
Cada JSON terminado es un checkpoint. No se repiten corridas compatibles.
"""

import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
import soundfile as sf

from .algoritmo_genetico import ejecutar_ag, inicializar_poblacion
from .configuracion import ConfiguracionAG, SEMILLAS_EXPERIMENTALES
from .evaluacion import construir_registro_corrida, guardar_registros_csv, resumir_corridas
from .extraccion import cargar_melodia_csv
from .fitness import evaluar_individuo, N_FFT, SALTO, PISO_DB, ESCALA_ERROR_DB
from .representacion import validar_individuo
from .sintesis import FRECUENCIA_MUESTREO


RAIZ = Path(__file__).resolve().parents[1]
COMBINACIONES = {
    'A': dict(seleccion='torneo', cruce='blend', mutacion='gaussiana'),
    'B': dict(seleccion='torneo', cruce='uniforme', mutacion='gaussiana'),
    'C': dict(seleccion='sus', cruce='blend', mutacion='no_uniforme'),
}
PARAMETROS = dict(alpha=0.5, sigma=0.08, b=2.0)
BASE = ConfiguracionAG(tolerancia_mejora=0.0)


def sha256(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def huella_poblacion(poblacion):
    return hashlib.sha256(np.asarray(poblacion, dtype='<f8').tobytes()).hexdigest()


def cargar_datos():
    """Comprueba montaje por eventos y silencios; no modifica ni regenera datos."""
    csv = RAIZ / 'datos/procesados/melodia_01.csv'
    wav = RAIZ / 'datos/audio/referencias/flauta_referencia_01.wav'
    meta = json.loads(wav.with_suffix('.json').read_text(encoding='utf-8'))
    notas, duraciones = cargar_melodia_csv(csv)
    referencia, sr = sf.read(wav, dtype='float32')
    info = sf.info(wav)
    np.testing.assert_array_equal(notas, meta['notas'])
    np.testing.assert_array_equal(duraciones, meta['duraciones_s'])
    assert sr == FRECUENCIA_MUESTREO == meta['frecuencia_muestreo']
    assert info.format == 'WAV' and info.subtype == 'PCM_16' and info.channels == 1
    assert np.all(np.isfinite(referencia)) and 1e-8 < np.max(np.abs(referencia)) <= 1
    fronteras = np.rint(np.r_[0, np.cumsum(duraciones)] * sr).astype(int)
    assert len(referencia) == fronteras[-1]
    for i, nota in enumerate(notas):
        evento = referencia[fronteras[i]:fronteras[i+1]]
        assert len(evento) >= 4
        assert np.all(evento == 0) if nota == -1 else np.any(evento != 0)
    datos = {str(p.relative_to(RAIZ)).replace('\\', '/'): sha256(p)
             for p in (csv, wav, wav.with_suffix('.json'))}
    return notas, duraciones, referencia, datos


def protocolo(datos):
    """Identifica también código local, sin atribuirlo al commit base."""
    return {
        'configuracion_base': asdict(BASE), 'semillas': list(SEMILLAS_EXPERIMENTALES),
        'combinaciones': COMBINACIONES, 'parametros': PARAMETROS,
        'metrica': 'stft', 'estado_metrica': 'provisional; no ratificación colectiva',
        'politica': '50 reemplazos, tolerancia_mejora=0; reevaluación completa',
        'desempate': 'media descendente; igualdad exacta: menor DE muestral, menor tiempo medio',
        'datos_sha256': datos,
        'fitness': dict(n_fft=N_FFT, salto=SALTO, piso_db=PISO_DB,
                        escala_error_db=ESCALA_ERROR_DB, ventana='hann',
                        boundary='zeros', padded=True, frecuencia_muestreo=FRECUENCIA_MUESTREO,
                        semilla_sintesis=2026),
        'codigo_sha256': {p.relative_to(RAIZ).as_posix(): sha256(p)
                          for p in sorted((RAIZ / 'src').glob('*.py'))},
        'versiones': {'python': platform.python_version(),
                     **{p: version(p) for p in ('numpy', 'scipy', 'soundfile')}},
    }


def escribir_json(ruta, contenido):
    """Publica el checkpoint al terminar; nunca reemplaza uno existente."""
    ruta = Path(ruta)
    if ruta.exists():
        raise FileExistsError(ruta)
    temporal = ruta.with_suffix('.tmp')
    temporal.write_text(json.dumps(contenido, ensure_ascii=False, indent=2,
                                   allow_nan=False)+'\n', encoding='utf-8')
    temporal.rename(ruta)


def ejecutar_una(combinacion, config, datos, identificador):
    notas, duraciones, referencia, _ = datos
    # RNG independiente de comprobación: no toca el generador interno de ejecutar_ag.
    inicial_esperada = inicializar_poblacion(config, np.random.default_rng(config.semilla))
    inicial_observada = []
    llamadas = 0

    def aptitud(gen):
        nonlocal llamadas
        if llamadas < config.tam_poblacion:
            inicial_observada.append(gen.copy())
        llamadas += 1
        return evaluar_individuo(gen, notas, duraciones, referencia, metrica='stft')

    inicio = time.perf_counter()
    resultado = ejecutar_ag(aptitud, config, **COMBINACIONES[combinacion], **PARAMETROS)
    tiempo = time.perf_counter() - inicio
    np.testing.assert_array_equal(inicial_observada, inicial_esperada)
    assert llamadas == resultado['evaluaciones'] == config.tam_poblacion * (config.max_generaciones + 1)
    assert resultado['motivo_parada'] == 'max_generaciones'
    assert validar_individuo(resultado['mejor_individuo'])[0]
    registro = construir_registro_corrida(
        metodo='algoritmo_genetico', semilla=config.semilla,
        configuracion=config, resultado=resultado, tiempo_s=tiempo, metrica='stft')
    historial = [{**asdict(fila), 'evaluaciones': (i+1)*config.tam_poblacion,
                  'mejor_global': resultado['historial_mejor_fitness'][i]}
                 for i, fila in enumerate(resultado['historial'])]
    registro.update(combinacion=combinacion, llamadas_observadas=llamadas,
                    fitness_inicial=historial[0]['mejor_global'],
                    mejora=resultado['mejor_fitness']-historial[0]['mejor_global'],
                    diversidad_inicial=historial[0]['diversidad_genetica'],
                    diversidad_final=historial[-1]['diversidad_genetica'])
    return dict(protocolo_id=identificador, registro=registro, historial=historial,
                poblacion_inicial_sha256=huella_poblacion(inicial_observada),
                operadores=resultado['operadores'],
                terminado_utc=datetime.now(timezone.utc).isoformat())


def ejecutar_experimento(carpeta):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    datos = cargar_datos()
    reglas = protocolo(datos[3])
    identificador = hashlib.sha256(json.dumps(reglas, sort_keys=True).encode()).hexdigest()
    manifiesto = carpeta / 'manifiesto.json'
    if manifiesto.exists():
        anterior = json.loads(manifiesto.read_text(encoding='utf-8'))
        if anterior['protocolo_id'] != identificador:
            raise ValueError('Cambió código, entorno o datos: usar otra carpeta; no mezclar corridas.')
    else:
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=RAIZ).decode('utf-8').strip()
        escribir_json(manifiesto, dict(
            protocolo_id=identificador, protocolo=reglas,
            commit_base=git('rev-parse', 'HEAD'), rama=git('branch', '--show-current'),
            cambios_locales=git('status', '--short'),
            creado_utc=datetime.now(timezone.utc).isoformat(),
            plataforma=platform.platform(),
            requisitos_examen='tres combinaciones, tabla, diversidad, exploración/explotación y recomendación',
            protocolo_solicitado='N=50, G=50, cinco semillas y presupuesto igual; no atribuido al examen'))
    # Integración corta, separada de las réplicas oficiales.
    prueba = carpeta / 'comprobacion_corta.json'
    if not prueba.exists():
        config = replace(BASE, tam_poblacion=5, max_generaciones=2, semilla=123)
        escribir_json(prueba, [ejecutar_una(c, config, datos, identificador) for c in COMBINACIONES])
        print('Comprobación corta: 3 variantes, 15 evaluaciones cada una; OK', flush=True)
    # Orden rotado por semilla para no ejecutar siempre una variante al final.
    for i, semilla in enumerate(SEMILLAS_EXPERIMENTALES):
        orden = list(COMBINACIONES)
        orden = orden[i % 3:] + orden[:i % 3]
        for combinacion in orden:
            ruta = carpeta / f'corrida_{combinacion}_{semilla}.json'
            if ruta.exists():
                existente = json.loads(ruta.read_text(encoding='utf-8'))
                assert existente['protocolo_id'] == identificador
                print(f'Conservada {combinacion}/{semilla}', flush=True)
                continue
            print(f'Iniciando {combinacion}/{semilla}', flush=True)
            try:
                corrida = ejecutar_una(combinacion, replace(BASE, semilla=semilla), datos, identificador)
                escribir_json(ruta, corrida)
            except Exception as error:
                fallo = carpeta / f'fallo_{combinacion}_{semilla}_{time.time_ns()}.json'
                escribir_json(fallo, dict(error=repr(error), protocolo_id=identificador))
                raise
            r = corrida['registro']
            print(f"Terminada {combinacion}/{semilla}: {r['mejor_fitness']:.9f}; "
                  f"{r['evaluaciones']} evaluaciones; {r['tiempo_s']:.2f} s", flush=True)
    assert cargar_datos()[3] == datos[3], 'Los datos cambiaron durante la ejecución'
    return validar_resultados(carpeta)


def validar_resultados(carpeta):
    """Lee corridas reales y comprueba comparabilidad, sin ejecutar fitness."""
    carpeta = Path(carpeta)
    manifiesto = json.loads((carpeta / 'manifiesto.json').read_text(encoding='utf-8'))
    reglas = manifiesto['protocolo']
    assert reglas['combinaciones'] == COMBINACIONES
    assert reglas['semillas'] == list(SEMILLAS_EXPERIMENTALES)
    assert reglas['configuracion_base'] == asdict(BASE)
    assert reglas['parametros'] == PARAMETROS and reglas['metrica'] == 'stft'
    for ruta, huella in reglas['datos_sha256'].items():
        assert sha256(RAIZ / ruta) == huella, f'Datos distintos: {ruta}'
    corridas = [json.loads(p.read_text(encoding='utf-8'))
                for p in sorted(carpeta.glob('corrida_*.json'))]
    esperados = {(c, s) for c in COMBINACIONES for s in SEMILLAS_EXPERIMENTALES}
    pares = [(x['registro']['combinacion'], x['registro']['semilla']) for x in corridas]
    assert len(pares) == len(set(pares)) == 15 and set(pares) == esperados
    for x in corridas:
        r, h = x['registro'], x['historial']
        assert x['protocolo_id'] == manifiesto['protocolo_id']
        assert json.loads(r['configuracion_json']) == asdict(replace(BASE, semilla=r['semilla']))
        assert x['operadores'] == {**COMBINACIONES[r['combinacion']], **PARAMETROS}
        assert r['metrica'] == 'stft' and r['motivo_parada'] == 'max_generaciones'
        assert r['generaciones_ejecutadas'] == 50 and len(h) == 51
        assert r['llamadas_observadas'] == r['evaluaciones'] == 2550
        assert [f['generacion'] for f in h] == list(range(51))
        assert [f['evaluaciones'] for f in h] == list(range(50, 2551, 50))
        assert np.isfinite([v for f in h for v in f.values()]).all()
        assert np.isfinite([r[k] for k in ('mejor_fitness', 'tiempo_s', 'mejora',
                                         'fitness_inicial', 'diversidad_inicial', 'diversidad_final')]).all()
        mejor = np.array([f['mejor_global'] for f in h])
        assert np.all(np.diff(mejor) >= 0)
        np.testing.assert_array_equal(mejor, [f['fitness_maximo'] for f in h])
        assert r['mejor_fitness'] == mejor[-1] and r['fitness_inicial'] == mejor[0]
        assert r['mejora'] == mejor[-1] - mejor[0]
        assert r['diversidad_final'] == h[-1]['diversidad_genetica']
        assert validar_individuo(json.loads(r['mejor_individuo_json']))[0]
    for s in SEMILLAS_EXPERIMENTALES:
        grupo = [x for x in corridas if x['registro']['semilla'] == s]
        assert len({x['poblacion_inicial_sha256'] for x in grupo}) == 1
        assert len({x['registro']['fitness_inicial'] for x in grupo}) == 1
        assert len({x['registro']['diversidad_inicial'] for x in grupo}) == 1
    return corridas


def resumir_resultados(corridas):
    registros = [c['registro'] for c in corridas]
    resumen = resumir_corridas(registros, agrupar_por=('combinacion',))
    for fila in resumen:
        grupo = [r for r in registros if r['combinacion'] == fila['combinacion']]
        valores = [r['mejor_fitness'] for r in grupo]
        fila.update(mediana=float(np.median(valores)), minimo=min(valores), maximo=max(valores))
        for campo in ('evaluaciones', 'tiempo_s', 'diversidad_inicial', 'diversidad_final', 'mejora'):
            valores = [r[campo] for r in grupo]
            fila[campo+'_media'] = float(np.mean(valores))
            fila[campo+'_de'] = float(np.std(valores, ddof=1))
    return sorted(resumen, key=lambda r: (-r['media'], r['desviacion_estandar'], r['tiempo_s_media']))


def exportar_tablas(carpeta):
    carpeta = Path(carpeta)
    corridas = validar_resultados(carpeta)
    resumen = resumir_resultados(corridas)
    historial = [{ 'combinacion': c['registro']['combinacion'], 'semilla': c['registro']['semilla'], **f}
                 for c in corridas for f in c['historial']]
    for nombre, filas in [('corridas.csv', [c['registro'] for c in corridas]),
                          ('historial.csv', historial), ('resumen.csv', resumen)]:
        ruta = carpeta / nombre
        if not ruta.exists():
            guardar_registros_csv(filas, ruta)
    return resumen


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument('--ejecutar', type=Path)
    grupo.add_argument('--resumir', type=Path)
    args = parser.parse_args()
    if args.ejecutar:
        ejecutar_experimento(args.ejecutar)
    print(json.dumps(exportar_tablas(args.ejecutar or args.resumir), indent=2))
