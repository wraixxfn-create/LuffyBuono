# Rufy Studio

Una pagina web interattiva per esplorare il modello 3D di Rufy nel browser.
Puoi ruotare e ingrandire la scultura, ripristinare l'inquadratura, attivare o
disattivare la rotazione automatica e scaricare il file 3D.

## Avvio

Apri un terminale nella cartella del progetto ed esegui:

```bash
py -m http.server 8000
```

Visita <http://localhost:8000>. La pagina usa Three.js dal CDN jsDelivr;
per caricarla occorre una connessione internet. Il file `.glb` e la pagina
restano ospitati localmente.

## Aggiornamento del modello

La pagina carica `assets/rufy.glb`, esportato dal file sorgente
`Rufy_Blender.blend`. Per ricrearlo dopo aver aggiornato il modello, usa Blender
5.2 o successivo:

```bash
blender --background Rufy_Blender.blend --python tools/export_model.py
```

Lo script esporta solo la scultura, ridimensiona le texture a 2K e semplifica
la geometria per favorire tempi di caricamento e prestazioni nel browser.
