# Despliegue en Render

El proyecto tiene dos aplicaciones FastAPI y requiere dos servicios web:

| Aplicación | Módulo ASGI | Uso |
| --- | --- | --- |
| API principal (local: 8000) | `backend.app.main:app` | Zonas, resumen, segmentación y planeación |
| Generador de imágenes (local: 8001) | `ml.image_generation.app:app` | Imágenes conceptuales mediante OpenAI |

La raíz del repositorio contiene `render.yaml` con ambos servicios. En Render,
crea un **Blueprint Instance** conectado al repositorio para configurar los dos.
Cada servicio usa su propia variable `PORT`; no se debe fijar 8000 ni 8001 en
producción.

Para iniciarlos localmente desde la raíz del repositorio:

```powershell
uvicorn backend.app.main:app --reload --port 8000
uvicorn ml.image_generation.app:app --reload --port 8001
```

## Antes del primer deploy

1. Conserva en Git `data/processed/modeling/urban_ai_master_intervention.gpkg`.
   La API lo lee en las rutas geográficas. El archivo local pesa 360 KB y ahora
   tiene una excepción específica en `.gitignore`; si no se incluye en el commit,
   las rutas de zonas no encontrarán los datos.
2. Verifica que estén incluidos los tres archivos del modelo en
   `ml/segmentation/outputs/training/best_model/`. La API carga ese modelo al
   recibir la primera solicitud de segmentación.
3. Configura `OPENAI_API_KEY` para ambos servicios en Render. Sin esa clave, la
   API arranca, pero la planeación y generación de imágenes no estarán disponibles.
4. Usa `CORS_ORIGINS` con el origen exacto del frontend publicado. Si cambia el
   dominio de Vercel, actualízalo en ambos servicios; admite una lista separada
   por comas.

## Frontend

En el servicio de Vercel, define `VITE_API_BASE_URL` y
`VITE_IMAGE_GENERATION_URL` con las URLs asignadas por Render y vuelve a generar
el frontend. Son variables de compilación de Vite, no variables del backend.
`frontend/.env.example` muestra los nombres y valores de ejemplo.

## Límites operativos a tener en cuenta

- La segmentación corre con PyTorch CPU y carga el modelo al primer uso. El plan
  Free de Render tiene 512 MB de RAM y 0.1 CPU; no doy por garantizado que pueda
  procesar la segmentación. Prueba ese endpoint después del deploy y aumenta los
  recursos si se queda sin memoria o expira. El Blueprint omite el plan para no
  seleccionar una instancia de pago sin que la elijas.
- Las imágenes generadas se guardan en `data/generated`. El sistema de archivos
  de Render es efímero por defecto, así que los enlaces a imágenes previas dejan
  de funcionar tras un reinicio o nuevo deploy. Para conservarlas, configura un
  disco persistente o almacenamiento externo.
- El plan del interventor llama a OpenAI y el generador también usa OpenAI, pero
  son procesos y servicios distintos. Una sola instancia Render recibe tráfico
  público en un puerto; el Blueprint los mantiene separados.
