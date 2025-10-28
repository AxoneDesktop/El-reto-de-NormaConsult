# 🏗️ NormaConsult - Sistema de Gestión de Consultas Técnicas

## 📋 Descripción

Sistema base para el **Reto NormaConsult**. Este sistema permite gestionar tickets de consultas técnicas y buscar información en documentos normativos de construcción.

## 🚀 Instalación y Despliegue

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Paso 1: Descomprimir el archivo

```bash
unzip reto_normaconsult.zip
cd reto_normaconsult
```

### Paso 2: Crear entorno virtual (recomendado)

**En Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: Ejecutar la aplicación

```bash
python app.py
```

La aplicación estará disponible en: **http://localhost:5000**

## 📂 Estructura del Proyecto

```
reto_normaconsult/
│
├── app.py                          # Aplicación Flask principal
├── requirements.txt                # Dependencias Python
├── ENUNCIADO_RETO.md              # Enunciado del reto para estudiantes
├── README.md                       # Este archivo
│
├── templates/                      # Plantillas HTML
│   ├── index.html                 # Página principal
│   ├── tickets.html               # Sistema de tickets
│   └── normativas.html            # Búsqueda de normativas
│
└── data/                           # Datos de la aplicación
    ├── tickets.json               # Base de datos de tickets (12 tickets sintéticos)
    └── normativas/                # Documentos normativos
        ├── CTE_DB-HE_Eficiencia_Energetica.txt
        ├── CTE_DB-SI_Seguridad_Incendios.txt
        ├── CTE_DB-HS_Salubridad.txt
        └── CTE_DB-SUA_Accesibilidad.txt
```

## 🎮 Uso de la Aplicación

### 1. Sistema de Tickets

- Accede desde la página principal o directamente en `/tickets`
- Visualiza tickets pendientes, en proceso y resueltos
- Haz clic en un ticket para ver detalles y responder
- Guarda respuestas que se almacenan automáticamente

**Funcionalidad actual:**
- CRUD simple de tickets
- Filtrado por estado
- Sin inteligencia artificial

### 2. Base de Conocimiento (Normativas)

- Accede desde la página principal o directamente en `/normativas`
- Busca por palabras clave en los documentos
- Descarga documentos completos
- Visualiza coincidencias con contexto

**Funcionalidad actual:**
- Búsqueda por palabra clave exacta (case-insensitive)
- Muestra contexto alrededor de las coincidencias
- No hay búsqueda semántica ni vectorial

## 📊 Datos Incluidos

### Tickets (12 ejemplos)

- 3 tickets resueltos (con respuesta)
- 2 tickets en proceso
- 7 tickets pendientes

Los tickets cubren consultas típicas sobre:
- Aislamiento térmico
- Resistencia al fuego
- Ventilación y salubridad
- Accesibilidad
- Certificación energética
- Instalaciones contra incendios

### Documentos Normativos (4 documentos)

1. **CTE DB-HE** - Eficiencia Energética (~100 líneas)
   - Transmitancia térmica
   - Zonas climáticas
   - Aislamiento
   - Certificación energética

2. **CTE DB-SI** - Seguridad Contra Incendios (~150 líneas)
   - Resistencia al fuego
   - Columna seca
   - Extintores y BIEs
   - Evacuación

3. **CTE DB-HS** - Salubridad (~130 líneas)
   - Ventilación
   - Suministro de agua
   - Evacuación de aguas
   - Calidad del aire interior

4. **CTE DB-SUA** - Accesibilidad (~150 líneas)
   - Rampas y escaleras
   - Itinerarios accesibles
   - Aseos adaptados
   - Plazas de aparcamiento PMR

## 📝 Notas Técnicas

### Base de Datos

Los tickets se almacenan en `data/tickets.json`. Es un archivo JSON simple que se lee/escribe con cada operación. Para un sistema real se recomienda usar una base de datos relacional (PostgreSQL, MySQL) o NoSQL (MongoDB).

### Búsqueda Actual

La búsqueda de normativas es muy básica:
- Lee cada archivo línea por línea
- Busca la palabra clave con `.lower()`
- Devuelve contexto (línea anterior, actual, siguiente)

### Escalabilidad

Este sistema NO está diseñado para producción:
- Sin autenticación
- Sin validación robusta
- Sin logging
- Sin pruebas
- Sin caché

## 🐛 Solución de Problemas

### Error: "Address already in use"

El puerto 5000 está ocupado. Cambia el puerto en `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Error: "Module not found"

Asegúrate de haber instalado las dependencias:
```bash
pip install -r requirements.txt
```

### Los archivos no se guardan

Verifica permisos de escritura en la carpeta `data/`:
```bash
chmod -R 755 data/
```