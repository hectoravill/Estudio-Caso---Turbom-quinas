"""Diseño de línea media de una turbina axial de vapor con etapas de reacción 50 %.

Ángulos medidos desde la dirección axial. Todo en SI (m/s, J/kg, m, Pa).
"""
import math

import pandas as pd
from CoolProp.CoolProp import PropsSI

from ciclo import FLUIDO, calcular_ciclo, es_bifasico, linea_recta_hs


def velocidad_sonido(estado):
    """Velocidad del sonido [m/s]. En vapor húmedo usa el exponente de Zeuner k = 1.035 + 0.1x."""
    if es_bifasico(estado):
        k_zeuner = 1.035 + 0.1 * estado['x']
        return math.sqrt(k_zeuner * estado['P'] / estado['rho'])
    return PropsSI('A', 'P', estado['P'], 'H', estado['h'], FLUIDO)


def triangulos_velocidad(w_etapa, u, phi, entrada_axial=False):
    """Triángulos de una etapa R = 0.5: c_θ2 + c_θ3 = u. Si no hay entrada axial, α1 = α3."""
    c_m = phi * u
    c_theta2 = (w_etapa + u**2) / (2 * u)
    c_theta3 = u - c_theta2
    c_theta1 = 0.0 if entrada_axial else c_theta3
    w_theta2, w_theta3 = c_theta2 - u, c_theta3 - u

    def angulo(componente_tangencial):
        return math.degrees(math.atan2(componente_tangencial, c_m))

    return {'u': u, 'c_m': c_m, 'c_theta1': c_theta1, 'c_theta2': c_theta2,
            'c_theta3': c_theta3, 'w_theta2': w_theta2, 'w_theta3': w_theta3,
            'c1': math.hypot(c_m, c_theta1), 'c2': math.hypot(c_m, c_theta2),
            'c3': math.hypot(c_m, c_theta3), 'w2': math.hypot(c_m, w_theta2),
            'w3': math.hypot(c_m, w_theta3), 'alpha1': angulo(c_theta1),
            'alpha2': angulo(c_theta2), 'alpha3': angulo(c_theta3),
            'beta2': angulo(w_theta2), 'beta3': angulo(w_theta3)}


def trabajo_euler(tri):
    """Ecuación de Euler: w = u (c_θ2 − c_θ3)."""
    return tri['u'] * (tri['c_theta2'] - tri['c_theta3'])


def grado_reaccion(tri):
    """R con velocidades relativas: no usa la condición de simetría con que se construyó."""
    return (tri['w3']**2 - tri['w2']**2) / (2 * trabajo_euler(tri))


def perdidas_etapa(tri, eta_alabe):
    """Modelo de eficiencia de álabe: Δh_pérdida = (1 − η_álabe)·Δh_cinético en estator y rotor."""
    w_etapa = trabajo_euler(tri)
    perdida_estator = (1 - eta_alabe) * (tri['c2']**2 - tri['c1']**2) / 2
    perdida_rotor = (1 - eta_alabe) * (tri['w3']**2 - tri['w2']**2) / 2
    return {'perdida_estator': perdida_estator, 'perdida_rotor': perdida_rotor,
            'eta_etapa': w_etapa / (w_etapa + perdida_estator + perdida_rotor)}


def humedad(estado):
    """Fracción de líquido y = 1 − x (cero fuera de la campana)."""
    return 1 - estado['x'] if es_bifasico(estado) else 0.0


def correccion_humedad(eta_seca, entrada, salida):
    """Regla de Baumann: −1 % de eficiencia por cada 1 % de humedad media en la etapa."""
    humedad_media = (humedad(entrada) + humedad(salida)) / 2
    return eta_seca * (1 - humedad_media)


def rotor_primo_relativo(z_toberas, z_rotor):
    """Sube z_rotor hasta que no comparta divisores con z_toberas (evita resonancias)."""
    while math.gcd(z_toberas, z_rotor) > 1:
        z_rotor += 1
    return z_rotor


def geometria_alabes(salida, tri, contexto):
    """Altura (con admisión parcial si h < h_min), cuerda, paso y número de álabes."""
    D, crit = contexto['D_medio'], contexto['criterios']
    h_teorica = contexto['flujo_masico'] / (salida['rho'] * tri['c_m'] * math.pi * D)
    admision = min(1.0, h_teorica / crit['h_min'])
    altura = h_teorica / admision
    cuerda = max(altura / crit['relacion_aspecto'], crit['cuerda_min'])
    z_rotor = round(math.pi * D / (cuerda / crit['solidez']))
    z_toberas = round(admision * z_rotor)
    return {'h_teorica [mm]': h_teorica * 1e3, 'admision': admision, 'h [mm]': altura * 1e3,
            'h/D': altura / D, 'cuerda [mm]': cuerda * 1e3, 'AR': altura / cuerda,
            'z_toberas': z_toberas, 'z_rotor': rotor_primo_relativo(z_toberas, z_rotor)}


def evaluar_etapa(entrada, salida, tri, contexto):
    """Resultados de una etapa: estado de salida, Mach, eficiencia y geometría."""
    eta_seca = perdidas_etapa(tri, contexto['criterios']['eta_alabe'])['eta_etapa']
    return {'P_salida [kPa]': salida['P'] / 1e3,
            'x_salida': salida['x'] if es_bifasico(salida) else float('nan'),
            'rho_salida [kg/m³]': salida['rho'],
            'Mach': max(tri['c2'], tri['w3']) / velocidad_sonido(salida),
            'eta_etapa': correccion_humedad(eta_seca, entrada, salida),
            **geometria_alabes(salida, tri, contexto)}


def evaluar_turbina(ciclo, diseno, criterios):
    """Evalúa etapa por etapa un diseño (N, D, φ, Z) sobre la línea de expansión del ciclo."""
    u = math.pi * diseno['D_medio'] * diseno['N_rpm'] / 60
    w_etapa = ciclo['desempeno']['w_turbina'] / diseno['etapas']
    e3, e4 = ciclo['estados']['3'], ciclo['estados']['4']
    fronteras = linea_recta_hs(e3, e4, diseno['etapas'] + 1)
    contexto = {'D_medio': diseno['D_medio'], 'criterios': criterios,
                'flujo_masico': ciclo['desempeno']['flujo_masico']}
    filas = []
    for i in range(1, diseno['etapas'] + 1):
        tri = triangulos_velocidad(w_etapa, u, diseno['phi'], entrada_axial=(i == 1))
        filas.append({'etapa': i, **evaluar_etapa(fronteras[i - 1], fronteras[i], tri, contexto)})
    tabla = pd.DataFrame(filas).set_index('etapa')
    # Media armónica: Z·w / Σ(w/η_i). Se desprecia el factor de recalentamiento (conservador).
    eta_turbina = criterios['factor_fugas'] * len(tabla) / (1 / tabla['eta_etapa']).sum()
    return {'u': u, 'w_etapa': w_etapa, 'psi': w_etapa / u**2, 'tabla': tabla,
            'triangulos': triangulos_velocidad(w_etapa, u, diseno['phi']),
            'eta_turbina': eta_turbina}


def disenar_por_restricciones(ciclo, criterios):
    """u por Mach a la salida, Z por ψ_max y D por h/D en la última etapa."""
    phi, psi_max = criterios['phi'], criterios['psi_max']
    e4 = ciclo['estados']['4']
    # c2/u = sqrt(φ² + ((1 + ψ)/2)²) en una etapa simétrica de reacción 50 %
    u = criterios['mach_max'] * velocidad_sonido(e4) / math.hypot(phi, (1 + psi_max) / 2)
    etapas = math.ceil(ciclo['desempeno']['w_turbina'] / (psi_max * u**2))
    flujo = ciclo['desempeno']['flujo_masico']
    D = math.sqrt(flujo / (criterios['h_sobre_D_max'] * e4['rho'] * phi * u * math.pi))
    return {'N_rpm': 60 * u / (math.pi * D), 'D_medio': D, 'phi': phi, 'etapas': etapas}


def cerrar_lazo(datos, criterios, eta_inicial, tolerancia=1e-5, max_iter=20):
    """Itera ciclo ↔ turbina hasta que la eficiencia de la turbina deja de cambiar."""
    eta, historial = eta_inicial, []
    for iteracion in range(1, max_iter + 1):
        ciclo = calcular_ciclo(datos, eta)
        diseno = disenar_por_restricciones(ciclo, criterios)
        turbina = evaluar_turbina(ciclo, diseno, criterios)
        historial.append({'iteración': iteracion, 'η_t supuesta': eta,
                          'η_t calculada': turbina['eta_turbina'], 'Z': diseno['etapas'],
                          'N [rpm]': diseno['N_rpm'], 'D [m]': diseno['D_medio'],
                          'ṁ [kg/s]': ciclo['desempeno']['flujo_masico']})
        convergio = abs(turbina['eta_turbina'] - eta) < tolerancia
        if convergio:
            break
        eta = turbina['eta_turbina']
    return {'ciclo': ciclo, 'diseno': diseno, 'turbina': turbina, 'convergio': convergio,
            'historial': pd.DataFrame(historial).set_index('iteración')}


def tabla_resumen_diseno(diseno, turbina):
    """Parámetros principales de un diseño de turbina."""
    filas = [('Número de etapas Z', diseno['etapas'], '—'),
             ('Velocidad de giro N', diseno['N_rpm'], 'rpm'),
             ('Diámetro medio D_m', diseno['D_medio'], 'm'),
             ('Velocidad periférica u', turbina['u'], 'm/s'),
             ('Trabajo por etapa w', turbina['w_etapa'] / 1e3, 'kJ/kg'),
             ('Coeficiente de carga ψ', turbina['psi'], '—'),
             ('Coeficiente de caudal φ', diseno['phi'], '—'),
             ('Eficiencia de la turbina η_t', turbina['eta_turbina'], '—')]
    return pd.DataFrame(filas, columns=['Parámetro', 'Valor', 'Unidad']).set_index('Parámetro')


def verificar_criterios(ciclo, turbina, criterios):
    """Chequeos de los criterios de diseño: valor obtenido, límite y si se cumple."""
    tabla, x4 = turbina['tabla'], ciclo['estados']['4']['x']
    R = grado_reaccion(turbina['triangulos'])
    parcial = tabla[tabla['admision'] < 1]
    filas = [('Título a la salida x₄', x4, f"≥ {criterios['x_min']}", x4 >= criterios['x_min']),
             ('Coeficiente de carga ψ', turbina['psi'], '0.8 – 1.5', 0.8 <= turbina['psi'] <= 1.5),
             ('Mach máximo', tabla['Mach'].max(), f"< {criterios['mach_max']}",
              tabla['Mach'].max() < criterios['mach_max']),
             ('Altura de álabe mínima [mm]', tabla['h [mm]'].min(),
              f"≥ {criterios['h_min'] * 1e3:.0f}", tabla['h [mm]'].min() >= criterios['h_min'] * 1e3 - 1e-9),
             ('h/D última etapa', tabla['h/D'].iloc[-1], f"≤ {criterios['h_sobre_D_max']}",
              tabla['h/D'].iloc[-1] <= criterios['h_sobre_D_max'] + 1e-9),
             ('Grado de reacción R', R, '0.50', abs(R - 0.5) < 1e-3),
             ('Etapas con admisión parcial', len(parcial), 'informativo', '—'),
             ('Admisión parcial mínima', tabla['admision'].min(), 'informativo (típico ≈ 0.25)', '—')]
    return pd.DataFrame(filas, columns=['Criterio', 'Valor', 'Límite', 'Cumple'])


def verificar_catalogo(ciclo, diseno, catalogo):
    """Comprueba que el punto de operación cae dentro de la envolvente de catálogo."""
    e3, e4 = ciclo['estados']['3'], ciclo['estados']['4']
    filas = [('Presión de admisión [bar]', e3['P'] / 1e5, catalogo['P_admision_max'] / 1e5,
              e3['P'] <= catalogo['P_admision_max']),
             ('Temperatura de admisión [°C]', e3['T'] - 273.15,
              catalogo['T_admision_max'] - 273.15, e3['T'] <= catalogo['T_admision_max']),
             ('Presión de escape [bar] (mínimo)', e4['P'] / 1e5, catalogo['P_escape_min'] / 1e5,
              e4['P'] >= catalogo['P_escape_min']),
             ('Velocidad de giro [rpm]', diseno['N_rpm'], catalogo['N_max_rpm'],
              diseno['N_rpm'] <= catalogo['N_max_rpm'])]
    return pd.DataFrame(filas, columns=['Condición', 'Diseño', 'Límite de catálogo', 'Cumple'])
