"""Figuras del estudio de caso: diagramas T–s y h–s, triángulos y resultados por etapa."""
import matplotlib.pyplot as plt
import numpy as np
from CoolProp.CoolProp import PropsSI

from ciclo import FLUIDO, linea_recta_hs, propiedades

SERIE = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4']   # orden fijo de colores
TINTA, TINTA_SECUNDARIA, REJILLA = '#0b0b0b', '#52514e', '#dcdbd7'
ETIQUETA_S = r'Entropía $s$ [kJ/(kg$\cdot$K)]'
ETIQUETA_Y = {'T': r'Temperatura $T$ [°C]', 'h': r'Entalpía $h$ [kJ/kg]'}


def configurar_estilo():
    """Estilo común: ejes y rejilla discretos, líneas de 2 px, texto en tinta neutra."""
    plt.rcParams.update({
        'figure.facecolor': 'white', 'axes.facecolor': 'white', 'savefig.dpi': 300,
        'axes.edgecolor': TINTA_SECUNDARIA, 'axes.labelcolor': TINTA, 'text.color': TINTA,
        'xtick.color': TINTA_SECUNDARIA, 'ytick.color': TINTA_SECUNDARIA,
        'axes.grid': True, 'grid.color': REJILLA, 'grid.linewidth': 0.6,
        'axes.spines.top': False, 'axes.spines.right': False,
        'lines.linewidth': 2, 'font.size': 10, 'legend.fontsize': 9,
        'legend.framealpha': 0.95, 'legend.edgecolor': REJILLA})


def coordenadas(estados, eje_y):
    """Listas (s [kJ/kg·K], T [°C] o h [kJ/kg]) para graficar una serie de estados."""
    s = [e['s'] / 1e3 for e in estados]
    y = [e['T'] - 273.15 if eje_y == 'T' else e['h'] / 1e3 for e in estados]
    return s, y


def campana(eje_y, puntos=120):
    """Campana de saturación cerrada: líquido hasta casi el punto crítico y vuelta por vapor."""
    temperaturas = np.linspace(273.16, PropsSI('Tcrit', FLUIDO) - 0.05, puntos)
    liquido = [propiedades('T', T, 'Q', 0) for T in temperaturas]
    vapor = [propiedades('T', T, 'Q', 1) for T in temperaturas[::-1]]
    return coordenadas(liquido + vapor, eje_y)


def trayectorias_ciclo(estados, puntos=60):
    """Estados a lo largo de cada proceso (la caldera es isobárica, la turbina recta en h–s)."""
    e = estados
    h_caldera = np.linspace(e['2']['h'], e['3']['h'], puntos)
    return {'bomba': [e['1'], e['2']],
            'caldera': [propiedades('P', e['2']['P'], 'H', h) for h in h_caldera],
            'turbina': linea_recta_hs(e['3'], e['4'], puntos),
            'condensador': [e['4'], e['1']],
            'isentropica': [e['3'], e['4s']]}


def marcar_estados(ax, estados, eje_y):
    """Puntos y números de los estados, con desplazamientos para que no se tapen."""
    desplazamientos = {'1': (-12, -12), '2': (-12, 6), '3': (6, 4), '4': (6, -12), '4s': (-20, -12)}
    for nombre, (dx, dy) in desplazamientos.items():
        s, y = coordenadas([estados[nombre]], eje_y)
        ax.scatter(s, y, s=30, color=TINTA, zorder=5)
        ax.annotate(nombre, (s[0], y[0]), xytext=(dx, dy), textcoords='offset points',
                    fontweight='bold')


def anotar_bomba(ax, estados):
    """En T–s la bomba sube la temperatura menos de 1 °C: se indica con una nota."""
    dT = estados['2']['T'] - estados['1']['T']
    s1, T1 = coordenadas([estados['1']], 'T')
    ax.annotate(f'1–2: bomba, ΔT = {dT:.2f} °C\n(no visible a esta escala)', (s1[0], T1[0]),
                xytext=(s1[0] + 1.6, T1[0] + 25), color=TINTA_SECUNDARIA, fontsize=9,
                arrowprops={'arrowstyle': '->', 'color': TINTA_SECUNDARIA})


def figura_ciclo(ciclo, titulo, eje_y='T'):
    """Diagrama T–s (eje_y='T') o h–s (eje_y='h') del ciclo completo."""
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(*campana(eje_y), color=TINTA_SECUNDARIA, lw=1.2, ls='--', label='Campana de saturación')
    etiquetas = {'bomba': '1–2: Bomba', 'caldera': '2–3: Caldera',
                 'turbina': rf'3–4: Turbina ($\eta_t$ = {ciclo["eta_turbina"] * 100:.1f} %)',
                 'condensador': '4–1: Condensador'}
    trayectorias = trayectorias_ciclo(ciclo['estados'])
    for (proceso, texto), color in zip(etiquetas.items(), SERIE):
        ax.plot(*coordenadas(trayectorias[proceso], eje_y), color=color, label=texto)
    ax.plot(*coordenadas(trayectorias['isentropica'], eje_y), color=SERIE[2], lw=1.2, ls=':',
            label='3–4s: Expansión isentrópica')
    marcar_estados(ax, ciclo['estados'], eje_y)
    if eje_y == 'T':
        anotar_bomba(ax, ciclo['estados'])
    ax.set(title=titulo, xlabel=ETIQUETA_S, ylabel=ETIQUETA_Y[eje_y])
    ax.legend(loc='upper left')
    fig.tight_layout()
    return fig


def isobara(presion, s_min, s_max, puntos=40):
    """Estados a presión constante en un rango de entropías (para el diagrama de Mollier)."""
    return [propiedades('P', presion, 'S', s) for s in np.linspace(s_min, s_max, puntos)]


def figura_expansion_hs(ciclo_inicial, resultado):
    """Mollier: expansión preliminar vs. final, con las fronteras de cada etapa diseñada."""
    final = resultado['ciclo']['estados']
    fronteras = linea_recta_hs(final['3'], final['4'], resultado['diseno']['etapas'] + 1)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(*campana('h'), color=TINTA_SECUNDARIA, lw=1.2, ls='--', label='Campana de saturación')
    for P, s_min, s_max, s_texto in ((final['3']['P'], 6.2e3, 7.5e3, 6.55e3),
                                     (final['4']['P'], 6.4e3, 8.3e3, 8.0e3)):
        ax.plot(*coordenadas(isobara(P, s_min, s_max), 'h'), color=REJILLA, lw=1.5)
        texto = propiedades('P', P, 'S', s_texto)
        ax.annotate(f'P = {P / 1e3:g} kPa', (texto['s'] / 1e3, texto['h'] / 1e3), xytext=(4, 4),
                    textcoords='offset points', color=TINTA_SECUNDARIA, fontsize=9)
    ax.plot(*coordenadas([final['3'], final['4s']], 'h'), color=TINTA_SECUNDARIA, lw=1.2, ls=':',
            label='3–4s: isentrópica')
    ax.plot(*coordenadas(linea_recta_hs(final['3'], ciclo_inicial['estados']['4'], 2), 'h'),
            color=SERIE[1], ls='--', label=rf'Preliminar ($\eta_t$ = {ciclo_inicial["eta_turbina"]:.3f})')
    ax.plot(*coordenadas(fronteras, 'h'), color=SERIE[0], marker='o', markersize=5,
            label=rf'Final, {len(fronteras) - 1} etapas ($\eta_t$ = {resultado["ciclo"]["eta_turbina"]:.3f})')
    marcar_estados(ax, final, 'h')
    ax.set(title='Expansión en la turbina (diagrama de Mollier)', xlabel=ETIQUETA_S,
           ylabel=ETIQUETA_Y['h'], xlim=(6.4, 8.4), ylim=(2100, 3400))
    ax.legend(loc='lower right')
    fig.tight_layout()
    return fig


def dibujar_triangulo(ax, c_theta, w_theta, tri, estacion):
    """Vectores c (absoluta), w (relativa) y u (arrastre) de una estación, con c = w + u."""
    flecha = {'angles': 'xy', 'scale_units': 'xy', 'scale': 1, 'width': 0.006}
    c, w = np.hypot(tri['c_m'], c_theta), np.hypot(tri['c_m'], w_theta)
    ax.quiver(0, 0, c_theta, -tri['c_m'], color=SERIE[0], label=f'$c_{estacion}$ = {c:.1f} m/s', **flecha)
    ax.quiver(0, 0, w_theta, -tri['c_m'], color=SERIE[1], label=f'$w_{estacion}$ = {w:.1f} m/s', **flecha)
    ax.quiver(w_theta, -tri['c_m'], tri['u'], 0, color=TINTA_SECUNDARIA,
              label=f'$u$ = {tri["u"]:.1f} m/s', **flecha)
    extremos = [0, c_theta, w_theta]
    ax.set_xlim(min(extremos) - 40, max(extremos) + 40)
    ax.set_ylim(-tri['c_m'] - 40, 40)
    ax.set_aspect('equal')
    ax.set(xlabel=r'Componente tangencial [m/s]', ylabel=r'Componente axial [m/s]')
    ax.legend(loc='upper right' if c_theta > 0 else 'upper left')


def figura_triangulos(tri, titulo):
    """Triángulos a la entrada (2) y salida (3) del rotor, a escala (aspecto 1:1)."""
    fig, (ax2, ax3) = plt.subplots(1, 2, figsize=(12, 5))
    dibujar_triangulo(ax2, tri['c_theta2'], tri['w_theta2'], tri, 2)
    dibujar_triangulo(ax3, tri['c_theta3'], tri['w_theta3'], tri, 3)
    ax2.set_title(rf'Entrada al rotor: $\alpha_2$ = {tri["alpha2"]:.1f}°, $\beta_2$ = {tri["beta2"]:.1f}°')
    ax3.set_title(rf'Salida del rotor: $\alpha_3$ = {tri["alpha3"]:.1f}°, $\beta_3$ = {tri["beta3"]:.1f}°')
    fig.suptitle(titulo, fontweight='bold')
    fig.tight_layout()
    return fig


def barras_altura(ax, tabla, h_min_mm):
    """Altura teórica por etapa (escala log); las que no llegan a h_min van con admisión parcial."""
    parcial = tabla['h_teorica [mm]'] < h_min_mm
    for mascara, color, trama, texto in ((~parcial, SERIE[0], None, 'Admisión total'),
                                         (parcial, SERIE[1], '//', 'Admisión parcial')):
        grupo = tabla[mascara]
        if len(grupo) > 0:
            ax.bar(grupo.index, grupo['h_teorica [mm]'], width=0.65, color=color, hatch=trama,
                   edgecolor='white', linewidth=1, label=texto)
    for etapa, fila in tabla[parcial].iterrows():
        ax.annotate(f'{fila["admision"]:.0%}', (etapa, fila['h_teorica [mm]']), xytext=(0, 3),
                    textcoords='offset points', ha='center', fontsize=8, color=TINTA_SECUNDARIA)
    ax.axhline(h_min_mm, color=TINTA_SECUNDARIA, ls='--', lw=1.2, label=f'$h_{{min}}$ = {h_min_mm:g} mm')
    ax.set(yscale='log', xlabel='Etapa', ylabel='Altura teórica de álabe [mm]',
           title='Altura de álabe (admisión total)', xticks=tabla.index)
    ax.legend(loc='upper left')


def barras_mach(ax, tabla, mach_max):
    """Mach máximo por etapa; las que superan el límite llevan trama."""
    excede = tabla['Mach'] >= mach_max
    for mascara, trama, texto in ((~excede, None, 'Dentro del límite'), (excede, 'xx', 'Supera el límite')):
        grupo = tabla[mascara]
        if len(grupo) > 0:
            ax.bar(grupo.index, grupo['Mach'], width=0.65, color=SERIE[0], hatch=trama,
                   edgecolor='white', linewidth=1, label=texto)
    ax.axhline(mach_max, color=TINTA_SECUNDARIA, ls='--', lw=1.2, label=f'$M_{{max}}$ = {mach_max}')
    ax.set(xlabel='Etapa', ylabel=r'Mach $= \max(c_2, w_3)/a$', title='Número de Mach por etapa',
           xticks=tabla.index, ylim=(0, max(1.15, tabla['Mach'].max() * 1.1)))
    ax.legend(loc='upper left')


def figura_etapas(tabla, criterios, titulo):
    """Dos gráficos separados (sin doble eje): altura de álabe y Mach por etapa."""
    fig, (ax_h, ax_m) = plt.subplots(1, 2, figsize=(12, 4.5))
    barras_altura(ax_h, tabla, criterios['h_min'] * 1e3)
    barras_mach(ax_m, tabla, criterios['mach_max'])
    fig.suptitle(titulo, fontweight='bold')
    fig.tight_layout()
    return fig
