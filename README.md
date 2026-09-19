# Bachelorarbeit-Anhang

Dieses Repository enthält die exportierten n8n-Workflows sowie das Docker-Compose-Setup zur Bachelorarbeit.

## Inhalt

| Datei / Ordner | Beschreibung |
| --- | --- |
| `Dateisuche_UC3` | n8n-Workflow-Export (JSON) für Anwendungsfall 3 (Dateisuche) |
| `Orchestrator_Agent` | n8n-Workflow-Export (JSON) für den Orchestrator-Agenten |
| `SQL_Agent_UC1_UC2` | n8n-Workflow-Export (JSON) für Anwendungsfälle 1 und 2 (SQL-Agent) |
| `docker-compose.yml` | Docker-Compose-Setup (n8n, Postgres, Ollama, Open WebUI, Recoll, QuickChart, Static-File-Server) |
| `.env` | Umgebungsvariablen für `docker-compose.yml` (Platzhalterwerte, keine echten Zugangsdaten) |
| `recoll/` | Recoll-Suchdienst (Dockerfile, Konfiguration, Cron-Job, Such-API) |
| `OpenWebUI_Funktion` | Open-WebUI-Pipe-Funktion ("Super Agent"), verbindet den Chat mit dem n8n-Orchestrator-Webhook |

## Workflows importieren

Die drei Workflow-Dateien sind n8n-Exporte im JSON-Format (ohne `.json`-Endung). Import in n8n:

1. n8n öffnen (siehe unten)
2. **Workflows → Create Workflow → Import from File**
3. Entsprechende Datei auswählen (ggf. vorher lokal in `*.json` umbenennen)
Alternativ: Inhalt der Datei (z. B. `SQL_Agent_UC1_UC2`) kopieren, in n8n einen leeren Workflow öffnen und mit **Strg + V** einfügen.

## Setup starten

Voraussetzung: Docker Desktop, Internetzugang (für Image-Pulls und den Recoll-Image-Build).

```bash
docker compose up
```

Erreichbare Dienste danach:

| Dienst | URL |
| --- | --- |
| n8n | http://localhost:5678 |
| Open WebUI | http://localhost:3000 |
| Recoll Such-API | http://localhost:8089 |
| Static-File-Server | http://localhost:8080 |
| QuickChart | http://localhost:3400 |
| Postgres | localhost:5432 |

Ollama läuft nur mit explizitem Profil, z. B.:

```bash
docker compose --profile cpu up
```

(alternativ `gpu-nvidia` oder `gpu-amd`, je nach Hardware)

## Einschränkungen in dieser Umgebung

- **LDAP-Login (Open WebUI):** ist an den internen Active-Directory-Server des Unternehmens gebunden und funktioniert außerhalb dieses Netzwerks nicht. Der Container startet trotzdem normal, nur der Login-Versuch schlägt fehl.
- **Geteilte Dateien (`./shared/...`):** Die referenzierten Ordner (Dateiablage für n8n, Recoll-Indexquelle, statische Dateien) sind nicht Teil dieses Repositories und werden beim ersten Start von Docker automatisch leer angelegt. Es gibt daher initial keine Beispieldateien zum Durchsuchen.
- **`.env`:** enthält ausschließlich Platzhalterwerte, keine produktiven Zugangsdaten.

## Open WebUI Funktion einrichten

Die Datei `OpenWebUI_Funktion` ist eine Pipe-Funktion für Open WebUI, die den Chat an den n8n-Orchestrator-Workflow weiterleitet.

1. Open WebUI öffnen (siehe unten)
2. **Admin Panel → Functions → "+" (neue Funktion erstellen)**
3. Inhalt von `OpenWebUI_Funktion` einfügen und speichern
4. In den Valves der Funktion mindestens `N8N_WEBHOOK_URL` (Webhook-URL des importierten `Orchestrator_Agent`-Workflows) setzen, optional `N8N_API_KEY`
5. Funktion aktivieren