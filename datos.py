"""Datos de entrada del estudio de caso. Todo en unidades SI (Pa, K, W, m)."""

DATOS_CICLO = {
    'potencia_neta': 3500e3,              # W   (3.5 MW netos)
    'P_condensador': 15e3,                # Pa  (15 kPa)
    'P_caldera': 3500e3,                  # Pa  (35 bar)
    'T_entrada_turbina': 420 + 273.15,    # K   (420 °C)
    'eta_bomba': 0.80,                    # eficiencia isentrópica de la bomba
}

# Estimación preliminar de la turbina (paso 2 del enunciado, antes de seleccionarla)
ETA_TURBINA_INICIAL = 0.82

# Criterios de diseño de línea media de la turbina
CRITERIOS = {
    'phi': 0.50,               # coeficiente de caudal c_m/u
    'psi_max': 1.40,           # coeficiente de carga w/u² (rango aceptado 0.8–1.5)
    'mach_max': 0.80,          # sin ondas de choque en ninguna etapa
    'h_min': 0.010,            # m: con h < 10 mm la teoría 2D no aplica → admisión parcial
    'h_sobre_D_max': 0.30,     # última etapa: validez del análisis de línea media
    'x_min': 0.88,             # título mínimo a la salida (erosión de álabes)
    'eta_alabe': 0.92,         # eficiencia de álabe de estator y rotor
    'factor_fugas': 0.96,      # fugas en sellos de laberinto y pérdidas de escape
    'relacion_aspecto': 2.0,   # AR = h/c
    'solidez': 1.5,            # σ = c/s
    'cuerda_min': 0.020,       # m: cuerda mínima fabricable
}

# Diseño preliminar de la primera versión del trabajo (se conserva para el diagnóstico)
DISENO_ORIGINAL = {'N_rpm': 11500.0, 'D_medio': 0.52, 'phi': 0.65, 'etapas': 6}
ETA_ALABE_ORIGINAL = 0.87

# Envolvente de catálogo de la Siemens SST-110 (turbina de doble carcasa).
# P y T máximas: folleto "Pre-designed steam turbines" de Siemens.
# N_max y P_escape_min: de la primera versión del trabajo, POR CONFIRMAR con el datasheet.
CATALOGO_SST110 = {
    'P_admision_max': 131e5,              # Pa
    'T_admision_max': 530 + 273.15,       # K
    'P_escape_min': 0.035e5,              # Pa
    'N_max_rpm': 13200.0,                 # rpm
}
