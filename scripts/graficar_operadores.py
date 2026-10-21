"""Figuras SVG de las corridas guardadas, sin reevaluar fitness.

Usa la biblioteca estándar porque Matplotlib no está instalado en el entorno
de ejecución. Los puntos provienen de los 51 registros reales de cada corrida.
"""

import argparse
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
from src.comparacion_operadores import validar_resultados, COMBINACIONES


def crear_figura(corridas, campo, titulo, etiqueta, destino):
    svg = ET.Element('svg', xmlns='http://www.w3.org/2000/svg',
                     width='1000', height='620', viewBox='0 0 1000 620', role='img')
    ET.SubElement(svg, 'title').text = titulo
    ET.SubElement(svg, 'desc').text = (
        'Dos curvas individuales por combinación y su media entre corridas. '
        'Generaciones 0 a 50; 2550 evaluaciones por corrida. STFT provisional.')

    def texto(x, y, contenido, **atributos):
        ET.SubElement(svg, 'text', x=str(x), y=str(y),
                      attrib={'font-family': 'sans-serif', 'font-size': '15',
                              'fill': '#182b3a', **atributos}).text = contenido

    ET.SubElement(svg, 'rect', width='1000', height='620', fill='white')
    texto(85, 35, titulo, **{'font-size': '23', 'font-weight': 'bold'})
    texto(85, 62, 'N=50 · 50 reemplazos · semillas 42 y 101 · STFT provisional')
    valores = np.array([[f[campo] for f in c['historial']] for c in corridas])
    minimo = 0.0 if campo == 'diversidad_genetica' else float(valores.min()) - 0.005
    maximo = float(valores.max()) + 0.01
    def px(g): return 90 + 860 * g / 50
    def py(v): return 485 - 360 * (v - minimo) / (maximo - minimo)
    for y in np.linspace(minimo, maximo, 6):
        ET.SubElement(svg, 'line', x1='90', x2='950', y1=str(py(y)), y2=str(py(y)), stroke='#d9e0e6')
        texto(78, py(y)+5, f'{y:.3f}', **{'text-anchor': 'end'})
    for g in range(0, 51, 10):
        texto(px(g), 510, str(g), **{'text-anchor': 'middle'})
    texto(520, 539, 'Generación (0 = población inicial)', **{'text-anchor': 'middle'})
    texto(90, 106, etiqueta)
    colores = {'A': '#1468a0', 'B': '#c55a11', 'C': '#22804c'}
    for indice, combinacion in enumerate(COMBINACIONES):
        grupo = [c for c in corridas if c['registro']['combinacion'] == combinacion]
        series = np.array([[f[campo] for f in c['historial']] for c in grupo])
        for serie in [*series, series.mean(axis=0)]:
            puntos = ' '.join(f'{px(g):.2f},{py(v):.2f}' for g, v in enumerate(serie))
            ET.SubElement(svg, 'polyline', points=puntos, fill='none',
                          stroke=colores[combinacion], **{'stroke-width': '1', 'opacity': '0.25'})
        # La última línea es la media: destacarla sin ocultar las réplicas.
        svg[-1].set('stroke-width', '3')
        svg[-1].set('opacity', '1')
        x = 90 + indice * 290
        ET.SubElement(svg, 'line', x1=str(x), x2=str(x+28), y1='568', y2='568',
                      stroke=colores[combinacion], **{'stroke-width': '3'})
        texto(x+36, 573, {'A': 'A: torneo / BLX / gauss.',
                          'B': 'B: torneo / uniforme / gauss.',
                          'C': 'C: SUS / BLX / no uniforme'}[combinacion], **{'font-size': '13'})
    texto(90, 605, 'Líneas finas: réplicas individuales. Gruesas: media entre corridas; no intervalo de confianza.',
          **{'font-size': '13'})
    destino = Path(destino)
    if destino.exists():
        raise FileExistsError(destino)
    ET.ElementTree(svg).write(destino, encoding='utf-8', xml_declaration=True)


def generar_figuras(carpeta):
    carpeta = Path(carpeta)
    corridas = validar_resultados(carpeta)
    for campo, titulo, etiqueta, archivo in (
        ('mejor_global', 'Mejor fitness STFT por generación', 'Fitness STFT (mayor es mejor)', 'fitness.svg'),
        ('diversidad_genetica', 'Diversidad genética por generación',
         'Media de las desviaciones por gen normalizado (ddof=0)', 'diversidad.svg'),
    ):
        crear_figura(corridas, campo, titulo, etiqueta, carpeta / archivo)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('carpeta', type=Path)
    generar_figuras(parser.parse_args().carpeta)
