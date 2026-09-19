FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      recoll python3-recoll \
      poppler-utils antiword unrtf \
      tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng \
      python3 python3-pip cron curl \
 && pip3 install --break-system-packages fastapi "uvicorn[standard]" \
 && rm -rf /var/lib/apt/lists/*

# Recoll-Konfiguration (topdirs, OCR, Stemming, Skip-Listen)
COPY recoll.conf /root/.recoll/recoll.conf
# Such-API (FastAPI um das offizielle recoll-Python-Modul)
COPY recoll_api.py /opt/recoll_api.py
# Cron: inkrementelles Re-Indexing (SMB kann kein inotify/-m)
COPY crontab /etc/cron.d/recoll-cron
RUN chmod 0644 /etc/cron.d/recoll-cron && crontab /etc/cron.d/recoll-cron

EXPOSE 8089
# Erst-Index im Hintergrund, Cron starten, API in den Vordergrund
CMD ["bash","-lc","cron && (recollindex -c /root/.recoll >/var/log/recoll.log 2>&1 &) && python3 -m uvicorn recoll_api:app --app-dir /opt --host 0.0.0.0 --port 8089"]
