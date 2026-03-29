# 📊 Auditor Tracking Dashboard (AIG)

Este sistema es un monitor centralizado diseñado para validar la integridad de las bases de datos de auditoría cargadas en Google Sheets. Su objetivo es detectar inconsistencias automáticamente para asegurar que los reportes finales sean 100% veraces.

---

## 📋 Variables del Sistema (Columnas del Excel)

El Dashboard lee y analiza automáticamente las siguientes columnas de la hoja de cálculo:
- **Identificadores**: `ID`, `ID Observacion`, `ID Acción`, `ID Actividad`, `LLAVE`.
- **Información Base**: `Titulo del Trabajo`, `Proceso Origen`, `Tipo`, `Connotación Observacion`, `Dependencia`, `Acción`, `Descripción de la actividad`, `Entregable`.
- **Control de Cantidades**: `Cantidad de Entregables`, `Cantidad de Soportes cargados por la Dependencia`, `No. de entregables asociados a la Actividad`.
- **Tiempos y Avances**: `Periodo seguimiento`, `Fecha de seguimiento por parte del auditor`, `Porcentaje avance al corte`, `Porcentaje avance anterior`.
- **Lógica de Auditoría**: `¿La dependencia suministro información?`, `Fecha de Cargue de la evidencia`, `Comentarios del Auditor`, `Nombre Auditor (Iniciales)`.

---

## 🛠️ Reglas del Negocio (Validaciones Implementadas)

El motor de análisis busca activamente los siguientes 14 tipos de inconsistencias:

1.  **ID Duplicado**: La columna `LLAVE` debe ser única; no se permiten registros repetidos.
2.  **Celdas Vacías**: Detecta campos obligatorios sin diligenciar (Acción, Dependencia, etc.).
3.  **Tope de Avance**: Ningún proceso puede reportar un porcentaje de avance superior al **100%**.
4.  **Enlaces Dañados**: Las URLs de evidencia deben ser válidas y seguras (http/https).
5.  **Formato de Mes**: El "Periodo seguimiento" debe ser un mes completo (ej: "Enero", "Febrero").
6.  **Nombre Auditor**: El campo de auditor solo permite iniciales (entre 2 y 5 letras mayúsculas).
7.  **Año Vigente**: La fecha de seguimiento debe ser obligatoriamente del año actual.
8.  **Lógica de Suministros**:
    - Si se marcó **SÍ** suministró info, debe existir una fecha de cargue válida.
    - Si se marcó **NO** suministró info, la fecha de cargue debe ser "No aplica".
9.  **Evidencia vs Soportes**: Si suministró información, la cantidad de soportes debe ser mayor a 0.
10. **Soportes vs Entregables**: Los soportes cargados no pueden ser más que los entregables asociados.
11. **Consistencia de Calidad**: Si el reporte es "Insuficiente", debe marcarse también como "No Relevante" y "No Fiable".
12. **Meta de Entregables**: Los entregables asociados no pueden superar la cantidad total proyectada.
13. **Retroceso de Avance**: El avance anterior no puede ser mayor que el avance registrado actualmente.
14. **Coherencia de Comentarios**: El texto escrito por el auditor se valida contra los datos numéricos (ej: si hay 0 entregables, el comentario debe mencionar que no hubo evidencia).

---

## 🏗️ Sección Técnica (Para Desarrolladores)

### **Arquitectura**
- **Backend**: Python 3.9+ con **FastAPI**.
- **Paralelismo**: Uso de `asyncio.gather` para descargar las 10 pestañas del Excel simultáneamente (reducción de carga a ~1.2s).
- **Frontend**: **Jinja2 Templates**, **Tailwind CSS** y **Chart.js**.
- **Optimización UX**: Lazy/Batch loading de 25 registros en la tabla para manejar bases de datos extensas.

### **Instalación**
1. `pip install -r requirements.txt`
2. Configurar el archivo `.env` con el `GOOGLE_SHEET_ID`.
3. Ejecutar: `uvicorn app.main:app --reload`

---

> [!IMPORTANT]
> **Seguridad**: Los datos siempre se consultan en tiempo real desde Google Sheets. No se almacena información sensible de forma local.
