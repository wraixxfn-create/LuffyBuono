# Rufy Studio

Una pagina web interattiva per esplorare il modello 3D di Rufy nel browser.
Puoi ruotare e ingrandire la scultura, usare **Volto** per osservare da vicino
il nuovo viso stilizzato, ripristinare l'inquadratura, attivare o disattivare
la rotazione automatica e scaricare il file 3D. L'inquadratura del volto mette
in pausa la rotazione automatica; puoi riattivarla con l'apposito pulsante.

## Avvio

Apri un terminale nella cartella del progetto ed esegui:

```bash
py -m http.server 8000
```

Visita <http://localhost:8000>. Su Windows puoi usare `py -m http.server 8000`.
Il modello e i moduli Three.js sono inclusi nel progetto: non è necessaria una
connessione a un CDN. Three.js 0.180.0 è distribuito con licenza MIT, inclusa in
`vendor/three/LICENSE`.

## Aggiornamento del modello

La pagina carica `assets/rufy.glb`, esportato dal file sorgente
`Rufy_Blender.blend`. Il volto è stato ricostruito con una superficie 3D
continua, lineamenti ridisegnati e ciocche sulla fronte. Nel file Blender il
volto e le ciocche restano oggetti modificabili, collegati alla scultura;
tutte le texture sono incorporate. Per ricreare il modello web dopo una
modifica, usa Blender 5.0 o successivo:

```bash
blender --background Rufy_Blender.blend --python tools/export_model.py
```

Lo script esporta la scultura e tutti i suoi oggetti mesh figli, compresi volto
e ciocche. Semplifica solo la mesh originale per il browser, mantiene le texture
colore fino a 4K e ridimensiona le mappe normali e dei materiali a 2K.

Per verificare il modello esportato e i moduli locali del visualizzatore:

```bash
python3 -m unittest discover -s tests
```
