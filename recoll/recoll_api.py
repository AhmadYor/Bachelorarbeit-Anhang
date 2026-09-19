import base64
import hashlib
import os
import subprocess
import tempfile
import urllib.parse
from pathlib import Path

from fastapi import FastAPI, HTTPException
from recoll import recoll

CONFDIR = os.environ.get("RECOLL_CONFDIR", "/root/.recoll")
SHARE_ROOT = os.environ.get("SHARE_ROOT", "/data/share")

app = FastAPI(title="Recoll Search API")


def url_to_path(url: str) -> str:
    return urllib.parse.unquote(url[7:]) if url.startswith("file://") else url


def resolve_pdf(relpath: str) -> Path:
    """Loest relpath innerhalb des Shares auf und verhindert Ausbruch per '../'."""
    root = Path(SHARE_ROOT).resolve()
    pdf = (root / relpath).resolve()
    if not str(pdf).startswith(str(root)):
        raise HTTPException(status_code=400, detail="Pfad ausserhalb des Shares")
    if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="PDF nicht gefunden")
    # Leistungsnachweise laufen ueber den bestehenden Flow und brauchen kein Rendering.
    if "leistungsnachweis" in pdf.name.lower():
        raise HTTPException(status_code=400, detail="Kein Rendering fuer Leistungsnachweise")
    return pdf


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/search")
def search(
    q: str,
    n: int = 10,
):
    db = recoll.connect(confdir=CONFDIR)
    query = db.query()
    query.execute(q, stemming=1)

    results = []
    for doc in query:
        path = url_to_path(doc.url)
        rel = os.path.relpath(path, SHARE_ROOT)
        results.append(
            {
                "relpath": rel,
                "path": path,
                "title": doc.title or os.path.basename(path),
                "mtype": doc.mtype,
                "mtime": doc.mtime,
                "size": doc.fbytes,
                "score": getattr(doc, "relevancyrating", None),
                "snippet": (query.makedocabstract(doc) or "").replace("\n", " "),
            }
        )
        if len(results) >= n:
            break

    return {"query": q, "count": len(results), "results": results}


@app.get("/pages")
def pages(relpath: str):
    """Seitenzahl und Datei-Hash - n8n baut daraus die Render-Batches und den Cache-Key."""
    pdf = resolve_pdf(relpath)
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True)
    seiten = None
    for line in out.stdout.splitlines():
        if line.startswith("Pages:"):
            seiten = int(line.split(":", 1)[1].strip())
            break
    if seiten is None:
        raise HTTPException(status_code=500, detail="Seitenzahl nicht ermittelbar")

    h = hashlib.sha256()
    with pdf.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)

    return {"relpath": relpath, "pages": seiten, "sha256": h.hexdigest(),
            "size": pdf.stat().st_size}


@app.get("/render")
def render(relpath: str, first: int = 1, last: int = 5, dpi: int = 200):
    """Rendert einen Seitenbereich als Base64-JPEGs fuer das VLM.

    Bewusst in Bloecken: 60 Seiten auf einmal waeren als Base64-JSON zu gross fuer n8n.
    """
    pdf = resolve_pdf(relpath)
    if first < 1 or last < first:
        raise HTTPException(status_code=400, detail="Ungueltiger Seitenbereich")
    if last - first + 1 > 20:
        raise HTTPException(status_code=400, detail="Maximal 20 Seiten je Aufruf")

    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["pdftoppm", "-r", str(dpi), "-jpeg", "-jpegopt", "quality=85",
             "-f", str(first), "-l", str(last), str(pdf), f"{tmp}/p"],
            check=True, capture_output=True,
        )
        files = sorted(Path(tmp).glob("p-*.jpg"))
        return {
            "relpath": relpath,
            "first": first,
            "last": last,
            "pages": [
                {"page": first + i,
                 "b64": base64.b64encode(p.read_bytes()).decode()}
                for i, p in enumerate(files)
            ],
        }
