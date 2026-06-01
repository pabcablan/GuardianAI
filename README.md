# Sistema Bastión

Sistema Bastión orientado a la anonimización de información sensible antes de su envío a servicios externos de inteligencia artificial (En el caso de este sistema OpenAI).

La aplicación está formada por distintos módulos independientes. La mayoría se despliegan mediante Docker Compose, mientras que el módulo proveedor de modelos se ejecuta por separado para poder ejecutarse en un equipo a parte por la necesidad de más requisitos de hardware.

## Requisitos previos

Para ejecutar el sistema principal se necesita:

* Docker
* Docker Compose
* Una clave válida para acceder a la API de OpenAI
* Acceso al servidor donde se ejecutará el proveedor de modelos

Para ejecutar el proveedor de modelos se necesita además:

* Python
* Las dependencias indicadas en el módulo `model-provider`
* Un equipo con recursos suficientes para cargar el modelo local seleccionado
* Preferiblemente, una GPU compatible

## Arquitectura del despliegue

El sistema principal está formado por los siguientes servicios:

| Servicio                 |  Puerto |
| ------------------------ | ------: |
| Interfaz web backend     |  `8000` |
| Procesador de documentos |  `8001` |
| Módulo de privacidad     |  `8002` |
| Orquestador              |  `8003` |
| Pasarela de IA           |  `8005` |
| MongoDB                  | `27017` |
| Frontend                 |  `5173` |

El proveedor de modelos se ejecuta de forma independiente:

| Servicio             | Puerto |
| -------------------- | -----: |
| Proveedor de modelos | `8010` |

## 1. Configuración del sistema principal

Antes de levantar los contenedores, se deben configurar las variables de entorno necesarias.

Crear o modificar el fichero `.env` correspondiente.

Las variables recomendadas para el despliegue actual son:

```env
OPENAI_API_KEY=<clave_de_openai>
ORCHESTRATOR_ASSISTANT_MODE=real

LLM_BASE_URL=http://<ip_del_servidor_de_modelos>:8010
MODEL_PROVIDER_BASE_URL=http://<ip_del_servidor_de_modelos>:8010
MODEL_PROVIDER_URL=http://<ip_del_servidor_de_modelos>:8010/generate_response

PRIVACY_MODEL_NAME=<modelo_para_anonimizacion>
DOCUMENT_MODEL_NAME=<modelo_para_extraccion_documental>
```

Significado de cada variable:

* `OPENAI_API_KEY`: clave utilizada por `ai-gateway` para llamar a OpenAI.
* `ORCHESTRATOR_ASSISTANT_MODE`: modo del orquestador. Para funcionamiento real debe ser `real` (el modo fake es para hacer pruebas sin llamadas a la IA externa).
* `LLM_BASE_URL`: URL base del proveedor de modelos usada por `document-processor`.
* `MODEL_PROVIDER_BASE_URL`: URL base del proveedor de modelos usada por `privacy-shield` y `web-ui-backend`.
* `MODEL_PROVIDER_URL`: endpoint concreto de generación usado por `privacy-shield`.
* `PRIVACY_MODEL_NAME`: nombre del modelo local usado para anonimizar.
* `DOCUMENT_MODEL_NAME`: nombre del modelo local usado para extracción o lectura documental.

Lo normal es que todos los modulos apunten al mismo proveedor de modelos `LLM_BASE_URL`, `MODEL_PROVIDER_BASE_URL` y `MODEL_PROVIDER_URL`.

Si no se definen algunas de estas variables, `docker-compose.yml` aplicará valores por defecto orientados a un proveedor accesible en `http://host.docker.internal:8010`.

## 2. Despliegue del proveedor de modelos

El proveedor de modelos se arrancará antes que el resto del sistema, ya que otros módulos realizan llamadas a este servicio durante el procesamiento de documentos y la anonimización.

Acceda al servidor donde se ejecutará el modelo local y entra en la carpeta correspondiente:

```bash
cd <ruta_del_proyecto>/model-provider
```

Instale las dependencias necesarias siguiendo el sistema de gestión utilizado en el proyecto.

```bash
uv sync
```

Después, arranque el proveedor de modelos:

```bash
uv run main.py
```

El módulo debe quedar accesible mediante el puerto `8010`.


### Selección del modelo local

El modelo utilizado puede modificarse desde el fichero de configuración correspondiente del módulo `model-provider`.

Si el equipo disponible cuenta con pocos recursos hardware, se recomienda seleccionar un modelo de menor tamaño para reducir el consumo de memoria y facilitar su ejecución.

## 3. Despliegue del sistema Bastión con Docker

Una vez arrancado el proveedor de modelos, vuelva a la carpeta raíz del proyecto:

```bash
cd <ruta_del_proyecto>
```

Construya y levante los contenedores mediante Docker Compose:

```bash
docker compose up --build
```

Docker Compose se encargará de iniciar los módulos principales, la base de datos MongoDB y el frontend.

## 4. Acceso a la aplicación

Una vez levantados todos los servicios, abra la aplicación desde el navegador:

```text
http://localhost:5173
```

Desde la interfaz será posible:

* Crear y gestionar conversaciones
* Seleccionar el modelo externo de OpenAI
* Configurar los tipos de información que deben anonimizarse
* Enviar consultas
* Adjuntar documentos PDF
* Revisar el contenido anonimizado antes de enviarlo
* Recibir la respuesta desanonimizada

## 5. Comprobación del estado de los contenedores

Para comprobar que los servicios se han iniciado correctamente:

```bash
docker compose ps
```

Para consultar los logs del sistema:

```bash
docker compose logs
```

## 6. Detención del sistema

Para detener todos los contenedores:

```bash
docker compose down
```

La información almacenada en MongoDB se mantiene gracias al volumen persistente definido en Docker Compose.

Si también se desea detener el proveedor de modelos, debe finalizarse manualmente el proceso `uv run main.py` en el servidor correspondiente.

## 7. Orden recomendado de arranque

El orden recomendado para levantar el sistema es el siguiente:

1. Acceder al servidor donde se encuentra el proveedor de modelos.
2. Iniciar el módulo `model-provider`.
3. Esperar a que el modelo local termine de cargarse.
4. Configurar el fichero `.env` del sistema principal.
5. Ejecutar `docker compose up --build -d` desde la carpeta raíz.
6. Comprobar el estado de los contenedores con `docker compose ps`.
7. Acceder a `http://localhost:5173` desde el navegador.
