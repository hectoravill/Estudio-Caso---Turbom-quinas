"""Pruebas unitarias. Se corren con:  python -m pytest

Los triángulos se prueban con un caso de valores redondos que se puede verificar a mano:
u = 200 m/s, c_m = 150 m/s, w = 80 kJ/kg → c_θ2 = (w + u²)/(2u) = 300 m/s, c_θ3 = −100 m/s.
"""
import math

import pytest

from ciclo import calcular_ciclo, propiedades
from datos import CRITERIOS, DATOS_CICLO, DISENO_ORIGINAL, ETA_ALABE_ORIGINAL, ETA_TURBINA_INICIAL
from turbina import (cerrar_lazo, correccion_humedad, evaluar_turbina, grado_reaccion,
                     perdidas_etapa, rotor_primo_relativo, trabajo_euler, triangulos_velocidad)


@pytest.fixture
def triangulos_redondos():
    return triangulos_velocidad(80e3, 200.0, 0.75, entrada_axial=True)


def test_triangulos_con_valores_redondos(triangulos_redondos):
    t = triangulos_redondos
    assert t['c_theta2'] == pytest.approx(300.0)
    assert t['c_theta3'] == pytest.approx(-100.0)
    assert t['c2'] == pytest.approx(335.4, abs=0.05)
    assert t['w2'] == pytest.approx(180.3, abs=0.05)
    assert t['alpha2'] == pytest.approx(63.43, abs=0.01)
    assert t['beta3'] == pytest.approx(-63.43, abs=0.01)


def test_euler_y_reaccion(triangulos_redondos):
    assert trabajo_euler(triangulos_redondos) == pytest.approx(80e3)
    assert grado_reaccion(triangulos_redondos) == pytest.approx(0.50, abs=1e-3)


def test_eficiencia_de_etapa(triangulos_redondos):
    perdidas = perdidas_etapa(triangulos_redondos, 0.92)
    assert perdidas['perdida_estator'] == pytest.approx(3.60e3, abs=10)
    assert perdidas['perdida_rotor'] == pytest.approx(3.20e3, abs=10)
    assert perdidas['eta_etapa'] == pytest.approx(0.922, abs=1e-3)


def test_etapa_repetida_tiene_alpha1_igual_a_alpha3():
    t = triangulos_velocidad(80e3, 200.0, 0.75)
    assert t['alpha1'] == pytest.approx(t['alpha3'])
    assert t['c1'] == pytest.approx(t['c3'])


def test_propiedades_coinciden_con_tablas_de_vapor():
    liquido_saturado = propiedades('P', 15e3, 'Q', 0)
    assert liquido_saturado['h'] / 1e3 == pytest.approx(225.94, abs=0.05)
    assert liquido_saturado['T'] - 273.15 == pytest.approx(53.97, abs=0.02)


def test_balance_de_energia_del_ciclo():
    d = calcular_ciclo(DATOS_CICLO, ETA_TURBINA_INICIAL)['desempeno']
    assert d['q_entrada'] - d['q_salida'] == pytest.approx(d['w_neto'])
    assert d['flujo_masico'] * d['w_neto'] == pytest.approx(DATOS_CICLO['potencia_neta'])


def test_rotor_primo_relativo():
    z_rotor = rotor_primo_relativo(100, 150)
    assert math.gcd(100, z_rotor) == 1
    assert z_rotor == 151


def test_regla_de_baumann():
    vapor_seco, vapor_humedo = {'x': -1.0}, {'x': 0.90}
    assert correccion_humedad(0.90, vapor_seco, vapor_seco) == pytest.approx(0.90)
    assert correccion_humedad(0.90, vapor_humedo, vapor_humedo) == pytest.approx(0.81)


def test_diseno_original_presenta_los_problemas_detectados():
    ciclo = calcular_ciclo(DATOS_CICLO, ETA_TURBINA_INICIAL)
    criterios = {**CRITERIOS, 'eta_alabe': ETA_ALABE_ORIGINAL}
    tabla = evaluar_turbina(ciclo, DISENO_ORIGINAL, criterios)['tabla']
    assert tabla['Mach'].max() > CRITERIOS['mach_max']
    assert tabla['h_teorica [mm]'].min() < CRITERIOS['h_min'] * 1e3


def test_diseno_corregido_converge_y_cumple_criterios():
    resultado = cerrar_lazo(DATOS_CICLO, CRITERIOS, ETA_TURBINA_INICIAL)
    tabla = resultado['turbina']['tabla']
    assert resultado['convergio']
    assert tabla['Mach'].max() < CRITERIOS['mach_max']
    assert tabla['h [mm]'].min() >= CRITERIOS['h_min'] * 1e3 - 1e-9
    assert resultado['ciclo']['estados']['4']['x'] >= CRITERIOS['x_min']
    assert 0.8 <= resultado['turbina']['psi'] <= 1.5
