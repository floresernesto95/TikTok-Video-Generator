# 🎬 TikTok Video Generator

Un sistema automatizado de extremo a extremo ("end-to-end") diseñado para la creación masiva de contenido de video vertical (formato TikTok/Reels/Shorts). Este proyecto integra Inteligencia Artificial Generativa, síntesis de voz y procesamiento multimedia para transformar simples ideas de texto en producciones audiovisuales completas sin intervención humana.

## 🚀 Características principales

* **Guionizado inteligente (GenAI):** Integración con **Google Gemini 2.5 Flash** para generar guiones estructurados, optimizados para la retención de audiencia.
* **Narración realista (TTS):** Implementación de **Edge TTS** para generar voces en off naturales y emotivas en español neutro.
* **Selección dinámica de recursos:** Búsqueda y descarga automática de material de stock (Pexels API) basada en el análisis semántico del guion.
* **Edición automatizada (FFmpeg):** Renderizado de video mediante `subprocess`, incluyendo corte, redimensionado a 9:16, sincronización de audio/video y mezcla de música de fondo (ducking automático).
* **Procesamiento por lotes (Batch Processing):** Sistema de colas robusto capaz de procesar múltiples temas secuencialmente, gestionando estados (pendientes vs. procesados).
* **Arquitectura asíncrona:** Uso de `asyncio` para optimizar operaciones de E/S bloqueantes como la generación de audio.

## 🛠️ Stack tecnológico

Este proyecto demuestra competencias en las siguientes tecnologías y librerías:

* **Lenguaje:** Python 3
* **APIs Externas:** Google GenAI SDK, Pexels API.
* **Multimedia:** FFmpeg (manipulación avanzada de A/V), Mutagen (análisis de metadatos de audio).
* **Concurrencia:** AsyncIO (programación asíncrona).
* **Gestión de archivos:** JSON, OS, Glob.

## ⚙️ Arquitectura del flujo de trabajo

El script sigue un patrón de tubería (pipeline) lineal con manejo de excepciones:

1. **Ingesta:** 
* Lee un tema desde `pending_topics.txt`.
2. **Generación de contenido:**
* Consulta a la API de Gemini para obtener un guion JSON con segmentos temporales y descripciones visuales.


3. **Síntesis de audio:** 
* Convierte el texto de cada segmento en archivos `.mp3` individuales.
4. **Adquisición de medios:**
* Itera sobre cada segmento de audio.
* Busca en Pexels videos verticales que coincidan con la "descripción visual" sugerida por la IA.
* Filtra resultados por duración y calidad (mínimo 1080p).


5. **Ensamblaje (Rendering):**
* Concatena pares de Audio+Video usando FFmpeg.
* Aplica filtros de recorte para asegurar el aspecto 9:16.


6. **Post-producción:**
* Añade una pista de música aleatoria desde la biblioteca local.
* Ajusta los niveles de volumen (mezcla de voz y fondo).


7. **Finalización:** 
* Mueve el video renderizado a la carpeta de salida y actualiza los registros de temas procesados.

## 📋 Requisitos previos

Para ejecutar este proyecto localmente, necesitas:

1. **Python 3.8+** instalado.
2. **FFmpeg** instalado y agregado al PATH del sistema.
3. Variables de entorno configuradas:
* `GEMINI_API_KEY`: Tu llave de API de Google AI Studio.
* `PEXELS_API_KEY`: Tu llave de API de Pexels.



### Instalación de dependencias

```bash
pip install google-genai edge-tts requests mutagen

```

## 📂 Estructura del proyecto

```text
├── background_music/      # Biblioteca de pistas de audio .mp3
├── final_videos/          # Salida de videos renderizados
├── prompt.txt             # Plantilla de ingeniería de prompts para la IA
├── pending_topics.txt     # Lista de entrada (temas a generar)
├── processed_topics.txt   # Registro de trabajos completados
├── main.py                # Script principal de orquestación
└── README.md              # Documentación

```

## 💡 Retos superados y aprendizajes

Durante el desarrollo de esta herramienta, se resolvieron desafíos técnicos clave:

* **Sincronización A/V:** Se implementó una lógica para asegurar que la duración del clip de video coincida o supere la duración del audio narrativo antes de la concatenación.
* **Manejo de errores en APIs:** Implementación de mecanismos de "fallback" (respaldo) cuando la API de Pexels no encuentra coincidencias exactas para términos complejos.
* **Optimización de FFmpeg:** Construcción de comandos complejos de filtrado (`filter_complex`) para realizar la mezcla de audio y video en una sola pasada de renderizado, reduciendo el tiempo de procesamiento.

## 🔮 Futuras mejoras

* Implementación de subtítulos automáticos (burn-in subtitles) sincronizados con el audio.
* Integración con la API de YouTube Data para la subida automática de los videos generados.
* Dockerización del entorno para facilitar el despliegue en la nube.