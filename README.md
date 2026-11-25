# Estudio-Caso---Turbomaquinas
Héctor Villalobos
Luis Tinoco

Estudio de caso de Turbomáquinas (UNIMET, trimestre 2627-1): ciclo Rankine de 3.5 MW netos,
selección y diseño de línea media de una turbina de vapor comercial (Siemens SST-110) y
recálculo del ciclo con la eficiencia de la turbina diseñada.

## Qué hace falta para correrlo

- **Python 3.10 o superior** (probado con Python 3.13).
- Los paquetes de `requirements.txt`:

| Paquete | Para qué se usa |
|---|---|
| `CoolProp` | Propiedades del agua con la ecuación de estado IAPWS-95 |
| `numpy`, `pandas` | Cálculo y tablas de resultados |
| `matplotlib` | Diagramas T–s, h–s, triángulos de velocidades y gráficos por etapa |
| `jupyter` | Abrir y ejecutar el notebook |
| `pytest` | Pruebas unitarias |

Se instalan todos con:

```bash
python3 -m pip install -r requirements.txt
```

Usen el mismo `python3` para instalar y para correr: si en la máquina hay varias versiones de
Python, los paquetes quedan instalados solo en la que ejecutó `pip`.

Todos los comandos se ejecutan **desde la carpeta del proyecto**, porque el notebook y las pruebas
importan los módulos `datos.py`, `ciclo.py`, `turbina.py` y `graficas.py`.

## Cómo correrlo

### Notebook (informe técnico, con las ecuaciones en LaTeX)

```bash
python3 -m jupyter notebook estudio_caso_turbomaquinas.ipynb
```

Al ejecutar todas las celdas se imprimen las tablas y se guardan las figuras en PNG.

### Pruebas

```bash
python3 -m pytest
```

### Exportar el notebook a PDF (opcional)

```bash
python3 -m jupyter nbconvert --to pdf estudio_caso_turbomaquinas.ipynb
```

Requiere además una distribución de LaTeX (MacTeX en macOS o TeX Live en Linux).

## Estructura

| Archivo | Contenido |
|---|---|
| `estudio_caso_turbomaquinas.ipynb` | Informe técnico ejecutable: ciclo preliminar, diseño de la turbina y ciclo recalculado |
| `datos.py` | Datos de entrada del ciclo, criterios de diseño y envolvente de catálogo (única fuente de datos) |
| `ciclo.py` | Estados y desempeño del ciclo Rankine |
| `turbina.py` | Triángulos de velocidades, pérdidas, geometría por etapa, diseño por restricciones y lazo ciclo ↔ turbina |
| `graficas.py` | Todas las figuras |
| `tests/` | Pruebas unitarias |
| `Estudio_de_caso_Turbomaquinas_2627_1.pdf` | Enunciado del estudio de caso |

## Ecuación de estado

CoolProp usa por defecto, para `Water`, la formulación **IAPWS-95** (backend HEOS). El notebook
la compara con la formulación industrial IAPWS-IF97: la diferencia es menor a 0.2 kJ/kg.

## Figuras generadas por el notebook

`diagrama_Ts_rankine.png`, `diagrama_Ts_rankine_recalculado.png`, `diagrama_hs_expansion.png`,
`triangulos_turbina.png`, `etapas_diseno_original.png`, `etapas_diseno_corregido.png`.
