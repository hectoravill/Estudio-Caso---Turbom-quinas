"""Ciclo Rankine simple con propiedades del agua calculadas con CoolProp.

Ecuación de estado: IAPWS-95 (backend HEOS de CoolProp, el de defecto para 'Water').
Internamente todo está en SI: Pa, K, J/kg, J/(kg·K), kg/m³.
"""
import numpy as np
import pandas as pd
from CoolProp.CoolProp import PropsSI

FLUIDO = 'Water'


def propiedades(entrada1, valor1, entrada2, valor2):
    """Estado termodinámico completo a partir de dos propiedades independientes."""
    def prop(salida):
        return PropsSI(salida, entrada1, valor1, entrada2, valor2, FLUIDO)
    return {'P': prop('P'), 'T': prop('T'), 'h': prop('H'), 's': prop('S'),
            'rho': prop('D'), 'x': prop('Q')}


def es_bifasico(estado):
    """CoolProp devuelve Q = -1 fuera de la campana; dentro, 0 ≤ x ≤ 1."""
    return 0 <= estado['x'] <= 1


def linea_recta_hs(inicio, fin, puntos):
    """Estados igualmente espaciados sobre la recta inicio→fin del diagrama h–s."""
    return [propiedades('H', inicio['h'] + f * (fin['h'] - inicio['h']),
                        'S', inicio['s'] + f * (fin['s'] - inicio['s']))
            for f in np.linspace(0, 1, puntos)]


def calcular_estados(datos, eta_turbina):
    """Estados 1, 2s, 2, 3, 4s y 4 del ciclo."""
    P_baja, P_alta = datos['P_condensador'], datos['P_caldera']
    e1 = propiedades('P', P_baja, 'Q', 0)
    e2s = propiedades('P', P_alta, 'S', e1['s'])
    h2 = e1['h'] + (e2s['h'] - e1['h']) / datos['eta_bomba']
    e3 = propiedades('P', P_alta, 'T', datos['T_entrada_turbina'])
    e4s = propiedades('P', P_baja, 'S', e3['s'])
    h4 = e3['h'] - eta_turbina * (e3['h'] - e4s['h'])
    return {'1': e1, '2s': e2s, '2': propiedades('P', P_alta, 'H', h2),
            '3': e3, '4s': e4s, '4': propiedades('P', P_baja, 'H', h4)}


def desempeno_ciclo(estados, potencia_neta):
    """Trabajos, calores, eficiencia térmica, caudal másico y potencias."""
    e = estados
    w_bomba = e['2']['h'] - e['1']['h']
    w_turbina = e['3']['h'] - e['4']['h']
    w_neto = w_turbina - w_bomba
    q_entrada = e['3']['h'] - e['2']['h']
    flujo_masico = potencia_neta / w_neto
    return {'w_bomba': w_bomba, 'w_turbina_ideal': e['3']['h'] - e['4s']['h'],
            'w_turbina': w_turbina, 'w_neto': w_neto, 'q_entrada': q_entrada,
            'q_salida': e['4']['h'] - e['1']['h'], 'eta_termica': w_neto / q_entrada,
            'flujo_masico': flujo_masico, 'potencia_turbina': flujo_masico * w_turbina,
            'potencia_bomba': flujo_masico * w_bomba}


def calcular_ciclo(datos, eta_turbina):
    """Estados y desempeño del ciclo para una eficiencia de turbina dada."""
    estados = calcular_estados(datos, eta_turbina)
    return {'eta_turbina': eta_turbina, 'estados': estados,
            'desempeno': desempeno_ciclo(estados, datos['potencia_neta'])}


def tabla_estados(estados):
    """Estados en unidades de ingeniería; x solo se muestra dentro de la campana."""
    filas = {nombre: {'P [kPa]': e['P'] / 1e3, 'T [°C]': e['T'] - 273.15,
                      'h [kJ/kg]': e['h'] / 1e3, 's [kJ/(kg·K)]': e['s'] / 1e3,
                      'ρ [kg/m³]': e['rho'], 'x [-]': e['x'] if es_bifasico(e) else np.nan}
             for nombre, e in estados.items()}
    return pd.DataFrame(filas).T


def tabla_desempeno(desempeno):
    """Resultados del ciclo en kJ/kg, kW y %."""
    d = desempeno
    filas = [('Salto entálpico isentrópico de turbina', d['w_turbina_ideal'] / 1e3, 'kJ/kg'),
             ('Trabajo real de turbina', d['w_turbina'] / 1e3, 'kJ/kg'),
             ('Trabajo de bomba', d['w_bomba'] / 1e3, 'kJ/kg'),
             ('Trabajo neto', d['w_neto'] / 1e3, 'kJ/kg'),
             ('Calor añadido en caldera', d['q_entrada'] / 1e3, 'kJ/kg'),
             ('Calor rechazado en condensador', d['q_salida'] / 1e3, 'kJ/kg'),
             ('Eficiencia térmica', d['eta_termica'] * 100, '%'),
             ('Caudal másico de vapor', d['flujo_masico'], 'kg/s'),
             ('Potencia de turbina', d['potencia_turbina'] / 1e3, 'kW'),
             ('Potencia de bomba', d['potencia_bomba'] / 1e3, 'kW')]
    return pd.DataFrame(filas, columns=['Magnitud', 'Valor', 'Unidad']).set_index('Magnitud')


def tabla_comparacion(ciclo_preliminar, ciclo_final):
    """Resultados del ciclo preliminar y del recalculado, lado a lado."""
    antes = tabla_desempeno(ciclo_preliminar['desempeno'])
    despues = tabla_desempeno(ciclo_final['desempeno'])
    return pd.DataFrame({'Preliminar': antes['Valor'], 'Recalculado': despues['Valor'],
                         'Cambio': despues['Valor'] - antes['Valor'], 'Unidad': antes['Unidad']})
