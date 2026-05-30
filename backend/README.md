# PokeSearch — Backend (microservicios + logging)

Buscador de Pokémon compuesto por **4 microservicios HTTP**. El Search API
(gateway) recibe un nombre, llama en paralelo a los 3 servicios downstream y
compone una respuesta parcial. Cada servicio emite **logs JSONL estructurados**
que son la fuente de verdad para el bot de análisis (parte 2) y para los perf
tests con JMeter.

## Arquitectura

| Servicio      | Puerto | Endpoint principal        | Fuente de datos              |
|---------------|:------:|---------------------------|------------------------------|
| **search_api**| 8000   | `POST /poke/search`       | orquesta los otros 3         |
| **poke_api**  | 8001   | `GET /pokemon/{name}`     | proxy a `pokeapi.co`         |
| **poke_stats**| 8002   | `GET /stats/{name}`       | Turso (libSQL) compartido    |
| **poke_images**| 8003  | `GET /images/{name}`      | archivos `data/images/*.jpg` |

Todos exponen además `GET /health`.

---

## 1. Setup (una sola vez)

Desde la carpeta `backend/`:

```bash
# 1. Crear e instalar el entorno virtual (la convención del equipo es env/)
python3 -m venv env
env/bin/pip install -r requirements.txt

# 2. Credenciales de la base Turso (la usa poke_stats)
cp services/poke_stats/.env.example services/poke_stats/.env
# editar services/poke_stats/.env y poner TURSO_DATABASE_URL y TURSO_AUTH_TOKEN
# (pedir el token al equipo — no está en git)
```

Los demás servicios funcionan con sus valores por defecto; no necesitan `.env`.

> **Requisito previo (solo si la BD/imagenes están vacías):** los datos ya
> fueron cargados una vez con `scripts/ingest_stats.py` (→ Turso) y
> `scripts/ingest_images.py` (→ `data/images/`). No hace falta repetirlo para
> correr los servicios.

---

## 2. Levantar los 4 servicios

```bash
./scripts/start_all.sh
```

Arranca los 4 en background, espera a que respondan `/health` e imprime las
URLs y PIDs. Logs de proceso en `.run/<servicio>.log`.

Para detenerlos:

```bash
./scripts/stop_all.sh
```

**Arranque manual** (si prefieres una terminal por servicio, útil para ver el
log en consola en vivo):

```bash
env/bin/uvicorn poke_api.main:app     --app-dir services --port 8001
env/bin/uvicorn poke_stats.main:app   --app-dir services --port 8002
env/bin/uvicorn poke_images.main:app  --app-dir services --port 8003
env/bin/uvicorn search_api.main:app   --app-dir services --port 8000
```

> El flag `--app-dir services` es **obligatorio**: pone `services/` en el path
> para que resuelvan `from poke_api…`, `from commons…`, etc.

Verificar que todo está arriba:

```bash
for p in 8000 8001 8002 8003; do curl -s localhost:$p/health; echo; done
```

---

## 3. Cómo generar logs (llamadas)

Cada request HTTP a cualquier servicio produce logs automáticamente. La forma
más completa es pegarle al **gateway**, porque una sola llamada genera logs en
los 4 servicios, todos correlacionados por el mismo `request_id`:

```bash
# Caso válido — devuelve name, stats[], img y errors:{}
curl -X POST http://localhost:8000/poke/search \
     -H 'Content-Type: application/json' \
     -d '{"pokemon_name":"charizard"}'

# Caso inexistente — respuesta parcial (stats:[], img:null, errors con 404)
curl -X POST http://localhost:8000/poke/search \
     -H 'Content-Type: application/json' \
     -d '{"pokemon_name":"noexiste999"}'
```

Respuesta del gateway:

```json
{
  "name": "charizard",
  "stats": [{"name":"hp","value":78}, {"name":"attack","value":84}, ...],
  "img": "http://localhost:8003/images/charizard",
  "errors": {}
}
```

También puedes pegarle a cada downstream por separado (genera logs solo en ese
módulo):

```bash
curl http://localhost:8001/pokemon/charizard     # poke-api
curl http://localhost:8002/stats/charizard        # poke-stats
curl http://localhost:8003/images/charizard -o /tmp/x.jpg   # poke-images
```

### Cómo generar errores (HTTP 500) para los logs

La fórmula de disponibilidad del bot usa `200 / (200 + 500)`, así que conviene
generar 500s reales:

- **Tumbar un downstream y pegarle al gateway:** `./scripts/stop_all.sh` de uno,
  o matar su PID, y mandar requests a `/poke/search` → el gateway responde 200
  parcial, pero `poke_stats`/`poke_api` dejan de loguear (servicio caído).
- **Forzar 500 en poke_stats:** poner un token Turso inválido en su `.env` y
  reiniciarlo → cada `GET /stats/{name}` lanza excepción → log con
  `http_status: 500`.

(Un nombre inexistente produce **404**, no 500 — el 404 no cuenta como error en
la fórmula de disponibilidad.)

---

## 4. Dónde quedan los logs

```
logs/
├── search-api/2026-05-30.jsonl
├── poke-api/2026-05-30.jsonl
├── poke-stats/2026-05-30.jsonl
└── poke-images/2026-05-30.jsonl
```

Un archivo **por servicio por día**, una entrada JSON por línea. Contrato:

```json
{
  "timestamp": "2026-05-30T18:11:24.711-05:00",
  "module": "poke-stats",
  "api": "/stats/{name}",
  "function": "get_stats",
  "level": "INFO",
  "message": "Request completed",
  "request_id": "1e6e583c-5e3f-4708-96f6-b896d9cbccf3",
  "http_status": 200,
  "duration_ms": 661.15,
  "event_type": "request"
}
```

- `event_type: "request"` → un log por request HTTP, con `http_status` y
  `duration_ms` totales. **Esto es lo que consume el bot.**
- `event_type: "block"` → bloques internos medidos (llamada externa, query a
  Turso, etc.); `http_status` es `null`. Sirve para el análisis de bottleneck.
- `request_id` correlaciona las entradas de un mismo request en los 4 servicios:

```bash
grep -h "<request_id>" logs/*/$(date +%F).jsonl
```

---

## 5. Perf test con JMeter

Objetivo: disparar muchos requests para llenar los `.jsonl` con datos que el
bot pueda analizar (latencia, disponibilidad, throughput).

**HTTP Request Sampler (recomendado — pega al gateway):**

| Campo        | Valor                       |
|--------------|-----------------------------|
| Method       | `POST`                      |
| Server Name  | `localhost`                 |
| Port         | `8000`                      |
| Path         | `/poke/search`              |
| Body Data    | `{"pokemon_name":"${name}"}`|

- Añadir un **HTTP Header Manager** con `Content-Type: application/json`.
- Usar un **CSV Data Set Config** con una columna `name` para variar el pokémon
  en cada request (incluye nombres válidos e inexistentes para mezclar 200/404).
  Ejemplo de `names.csv`:

  ```
  charizard
  pikachu
  bulbasaur
  mewtwo
  ho-oh
  noexiste999
  porygon-z
  nidoran-f
  ```

- Configurar el **Thread Group** (p. ej. 20 threads, ramp-up 5s, loop 50) según
  la carga que quieras.

**Pegarle a un downstream directo** (para logs de un solo módulo): cambia
Method a `GET` y Path a `/stats/${name}`, `/pokemon/${name}` o `/images/${name}`
en el puerto correspondiente (8002 / 8001 / 8003).

Tras la corrida, los logs nuevos están en `logs/<modulo>/<fecha>.jsonl`, listos
para el bot.

> **Nota sobre latencia:** `poke-api` y `poke-stats` llaman a servicios externos
> por red (pokeapi.co y Turso), así que su latencia depende de tu conexión.
> `poke-images` lee de disco local y es ~instantáneo. La primera request a cada
> servicio es más lenta (cold start del cliente httpx).

---

## Estructura del proyecto

```
backend/
├── services/
│   ├── commons/        # logging compartido (middleware, logger JSONL, latency, tracing)
│   ├── search_api/     # gateway  (POST /poke/search)
│   ├── poke_api/       # wrapper pokeapi.co (GET /pokemon/{name})
│   ├── poke_stats/     # stats desde Turso  (GET /stats/{name})
│   └── poke_images/    # imágenes locales   (GET /images/{name})
├── scripts/
│   ├── start_all.sh / stop_all.sh
│   ├── ingest_stats.py     # Kaggle CSV -> Turso (one-time)
│   └── ingest_images.py    # Kaggle images -> data/images/ (one-time)
├── data/               # pokemon_stats en Turso (remoto) + images/ local
├── logs/               # JSONL por servicio por día (gitignored)
└── requirements.txt
```
