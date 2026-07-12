# Ticket Reservation API — Jacopo Bandinelli

**Tipo di progetto:** REST API
**Framework utilizzato:** Django REST Framework (Django 6.0, DRF 3.17)

## 1. Cos'è questo progetto

Un'API REST per sfogliare eventi e prenotare singoli posti a sedere per
essi — pensa a biglietti per concerti, partite o spettacoli teatrali.
Chiunque può sfogliare il programma e controllare la disponibilità dei
posti senza un account; creare un account permette di prenotare,
modificare o annullare un posto; un piccolo ruolo admin gestisce il
catalogo eventi. È stato realizzato come progetto per un corso
universitario per dimostrare un backend DRF completo e consapevole dei
permessi: modello utente personalizzato, autenticazione a token, risorse
correlate, viste basate su classi, serializer validati e un'API
completamente documentata e testabile.

## 2. Funzionalità implementate, per ruolo

### Anonimo (nessun account)
- Sfogliare il catalogo eventi: elenco, dettaglio, ricerca (`?search=`),
  filtro per categoria/stato attivo, e ordinamento dei risultati.
- Visualizzare la mappa dei posti e il conteggio in tempo reale dei posti
  disponibili per qualsiasi evento attivo.

### Utente registrato (ruolo "customer")
Tutto ciò che può fare un Anonimo, più:
- Registrare un account, effettuare login/logout, visualizzare e
  aggiornare il proprio profilo.
- **Creare** una prenotazione (prenotare un posto specifico e disponibile
  per un evento).
- **Aggiornare** la propria prenotazione (spostarsi su un altro posto
  disponibile dello stesso evento, o modificarne la nota).
- **Annullare** la propria prenotazione (annullamento soft — il record
  viene mantenuto per lo storico e il posto torna disponibile) oppure
  **eliminarla** definitivamente.
- Controllare lo **stato** in tempo reale di una specifica prenotazione.
- Elencare la propria cronologia di prenotazioni.
- Un cliente può vedere o modificare solo le **proprie** prenotazioni —
  vincolo imposto dalla classe di permesso `IsOwnerOrAdmin`, non solo
  nascosto nell'interfaccia.

### Admin (ruolo "admin" — `is_staff=True`)
Tutto ciò che può fare un utente registrato, più:
- **Creare, aggiornare ed eliminare eventi.** Creare un evento genera
  automaticamente la sua mappa dei posti (`001`, `002`, …); aumentare o
  diminuire `total_seats` in fase di aggiornamento fa crescere o
  restringere la mappa dei posti di conseguenza.
- Visualizzare e gestire **tutte** le prenotazioni di tutti gli utenti,
  non solo le proprie.
- Gestione completa dei dati tramite il sito di amministrazione Django su
  `/admin/`.

L'applicazione dei ruoli è implementata con due classi di permesso DRF
dedicate (`events.permissions.IsAdminOrReadOnly`,
`reservations.permissions.IsOwnerOrAdmin`) applicate direttamente sui
viewset — vedi la Sezione 8 per sapere esattamente quale endpoint
richiede quale ruolo.

## 3. Stack tecnologico & struttura del progetto

- **Django 6.0** + **Django REST Framework 3.17**
- **Autenticazione a token** (`rest_framework.authtoken`)
- **django-filter** per i parametri di query `?category=`, `?status=`,
  `?search=`, `?ordering=`
- **django-cors-headers**, **whitenoise**, **gunicorn** per una build
  distribuibile in produzione e compatibile con CORS

```
progetto-backend-ppm/
├── manage.py
├── requirements.txt
├── db.sqlite3                # database demo già popolato (vedi §5)
├── Procfile, render.yaml, build.sh   # configurazione di deployment (vedi §7)
├── config/                   # impostazioni del progetto, url principali
├── core/
│   └── exceptions.py         # formato JSON di errore coerente per ogni app
├── accounts/                 # modello utente personalizzato + endpoint di auth
│   ├── models.py             # CustomUser(AbstractUser)
│   ├── serializers.py        # registrazione / login / profilo
│   ├── views.py / urls.py
│   └── management/commands/seed_demo_data.py
├── events/                   # risorse Event + Seat
│   ├── models.py             # Event, Seat (FK -> Event)
│   ├── serializers.py, views.py, urls.py, permissions.py
├── reservations/             # risorsa Reservation
│   ├── models.py             # Reservation (FK -> User, Event, Seat)
│   ├── serializers.py, views.py, urls.py, permissions.py
└── client/
    └── index.html             # client di test HTML/JS incluso (vedi §10)
```

**Relazioni tra risorse esposte tramite l'API:**
`Event 1─N Seat`, `Event 1─N Reservation`, `Seat 1─N Reservation` (una
prenotazione attiva per posto alla volta), `CustomUser 1─N Reservation`.
Gli endpoint di dettaglio evento e prenotazione espongono campi
nidificati/derivati per queste relazioni (`available_seats`,
`event_title`, `seat_number`, …) invece di richiedere ulteriori
chiamate.

## 4. Installazione in locale

```bash
# 1. Clona il repository
git clone <repository-url>
cd progetto-backend-ppm

# 2. Crea e attiva un ambiente virtuale
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Installa le dipendenze
pip install -r requirements.txt

# 4. Applica le migrazioni (il db.sqlite3 incluso è già migrato e
#    popolato, quindi questo passaggio è innocuo — diventa importante se
#    parti da un database vuoto/nuovo, vedi §5)
python manage.py migrate

# 5. Avvia il server di sviluppo
python manage.py runserver
```

Poi apri:
- `http://127.0.0.1:8000/` — indice JSON dell'API
- `http://127.0.0.1:8000/client/` — client di test HTML/JS incluso
- `http://127.0.0.1:8000/admin/` — sito di amministrazione Django

> Nota: al primo avvio potresti vedere un `RuntimeWarning` su
> `DJANGO_SECRET_KEY`. È innocuo per l'uso locale/demo (viene comunque
> usata una chiave di sviluppo funzionante) - è solo un avviso ben
> visibile che ricorda di impostare una vera `DJANGO_SECRET_KEY` prima
> di un deployment reale, invece di lasciarlo passare inosservato.

## 5. Database

Il repository include **`db.sqlite3`** nella cartella principale del
progetto, già migrato e popolato con:
- 4 account utente demo (1 admin, 3 clienti — vedi §6)
- 5 eventi demo in ogni categoria, con mappe dei posti completamente
  generate (105 posti in totale)
- 5 prenotazioni di esempio già effettuate, così gli endpoint di lista/
  dettaglio/stato hanno subito dati reali da restituire

Per riportarlo esattamente a questo stato in qualsiasi momento (es. dopo
aver testato scritture/cancellazioni), o per ricostruirlo da zero:

```bash
rm db.sqlite3
python manage.py migrate
python manage.py seed_demo_data
```

`seed_demo_data` è idempotente — eseguirlo di nuovo su un database già
esistente non crea duplicati.

## 6. Account demo

| Username | Password      | Ruolo    | Note                                |
|----------|---------------|----------|--------------------------------------|
| `admin`  | `admin123`    | admin    | staff + superuser, gestisce gli eventi |
| `alice`  | `demopass123` | customer | ha 2 prenotazioni attive             |
| `bob`    | `demopass123` | customer | ha 2 prenotazioni attive             |
| `carol`  | `demopass123` | customer | ha 1 prenotazione annullata          |

## 7. Deployment online

**URL live: [AGGIUNGI QUI IL TUO URL DI DEPLOYMENT UNA VOLTA PUBBLICATO]**

> Questo repository è pronto per il deployment (`Procfile`, `render.yaml`,
> `build.sh`, impostazioni basate su variabili d'ambiente, WhiteNoise per i
> file statici, CORS abilitato) ma non è stato distribuito automaticamente
> durante la generazione di questo progetto. Scegli una delle opzioni qui
> sotto — tutte e tre richiedono meno di dieci minuti — poi incolla l'URL
> risultante qui sopra.

**Opzione A — Render (la più veloce, Blueprint con un clic)**
1. Carica questo repository su GitHub.
2. Su [render.com](https://render.com), scegli *New → Blueprint* e punta
   al tuo repository. Render legge automaticamente `render.yaml` e
   configura il web service, il comando di build e le variabili
   d'ambiente.
3. Clicca su *Apply*. `build.sh` installa le dipendenze, esegue le
   migrazioni e ripopola i dati demo a ogni deploy, così gli account demo
   funzionano sempre.

**Opzione B — Railway**
1. Carica questo repository su GitHub, crea un nuovo progetto Railway a
   partire da esso.
2. Imposta il comando di avvio su
   `python manage.py migrate && python manage.py seed_demo_data && gunicorn config.wsgi --log-file -`.
3. Imposta le variabili d'ambiente `DJANGO_DEBUG=False` e
   `DJANGO_ALLOWED_HOSTS=<il-tuo-dominio-railway>`.

**Opzione C — PythonAnywhere (la scelta migliore per un SQLite persistente)**
1. Carica/clona il repository in una console PythonAnywhere, crea un
   virtualenv, esegui `pip install -r requirements.txt`.
2. Configura una nuova Web app (configurazione manuale, Django), punta il
   file WSGI a `config.wsgi.application`, imposta la working directory
   sulla cartella principale del progetto.
3. Esegui `python manage.py migrate` una volta dalla console
   PythonAnywhere (evita `seed_demo_data` nei reload successivi se vuoi
   preservare eventuali modifiche fatte dai tester — il `db.sqlite3`
   incluso è già popolato).

Nota: su piattaforme con filesystem effimero (piani gratuiti di
Render/Railway), `db.sqlite3` può azzerarsi a ogni redeploy — `build.sh`
lo ripopola automaticamente, così gli account demo e gli eventi di
partenza sono sempre presenti dopo un deploy, anche se non in modo
permanente a ogni riavvio del dyno. Per un database realmente persistente
tra un riavvio e l'altro, PythonAnywhere o un volume Postgres gestito e
collegato sono scelte più sicure.

## 8. Riferimento agli endpoint dell'API

URL base (locale): `http://127.0.0.1:8000` · URL base (online): vedi §7.
Tutti i corpi di richiesta/risposta sono JSON. Invia
`Content-Type: application/json`.

### Autenticazione (app `accounts`)

| Metodo | URL | Auth richiesta | Ruolo | Corpo della richiesta | Risposta | Descrizione |
|---|---|---|---|---|---|---|
| POST | `/api/auth/register/` | No | Anonimo | `{"username","email","password","password_confirm","first_name","last_name","phone_number"}` | `201` `{"token","user"}` | Crea un nuovo account cliente, restituisce subito un token |
| POST | `/api/auth/login/` | No | Anonimo | `{"username","password"}` | `200` `{"token","user"}` | Scambia le credenziali con un token di autenticazione |
| POST | `/api/auth/logout/` | Sì | Qualsiasi autenticato | — | `204` | Invalida il token attuale dell'utente chiamante |
| GET | `/api/auth/profile/` | Sì | Qualsiasi autenticato | — | `200` oggetto utente | Recupera il profilo dell'utente chiamante |
| PATCH | `/api/auth/profile/` | Sì | Qualsiasi autenticato | qualsiasi sottoinsieme dei campi profilo | `200` oggetto utente | Aggiorna il profilo dell'utente chiamante |

### Eventi (app `events`)

| Metodo | URL | Auth richiesta | Ruolo | Corpo della richiesta | Risposta | Descrizione |
|---|---|---|---|---|---|---|
| GET | `/api/events/` | No | Anonimo | — | `200` lista paginata | Elenca gli eventi attivi (`?category=`, `?search=`, `?ordering=`) |
| POST | `/api/events/` | Sì | **Solo admin** | `{"title","description","category","venue","event_date","price","total_seats","is_active"}` | `201` oggetto evento | Crea un evento; i posti `001..total_seats` sono generati automaticamente |
| GET | `/api/events/{id}/` | No | Anonimo | — | `200` dettaglio evento | Recupera un evento, incl. `available_seats`/`reserved_seats` |
| PUT/PATCH | `/api/events/{id}/` | Sì | **Solo admin** | qualsiasi sottoinsieme dei campi modificabili | `200` oggetto evento | Aggiorna un evento; cambiare `total_seats` amplia/riduce la mappa dei posti |
| DELETE | `/api/events/{id}/` | Sì | **Solo admin** | — | `204` | Elimina un evento (a cascata su posti/prenotazioni) |
| GET | `/api/events/{id}/seats/` | No | Anonimo | — | `200` lista di posti | Mappa completa dei posti, opzionale `?status=available|reserved` |
| GET | `/api/events/{id}/availability/` | No | Anonimo | — | `200` `{"event_id","total_seats","available_seats","reserved_seats"}` | Riepilogo leggero del conteggio dei posti |

### Prenotazioni (app `reservations`) — tutte richiedono autenticazione

| Metodo | URL | Auth richiesta | Ruolo | Corpo della richiesta | Risposta | Descrizione |
|---|---|---|---|---|---|---|
| GET | `/api/reservations/` | Sì | Proprietario (Admin: tutte) | — | `200` lista paginata | Elenca le proprie prenotazioni (`?status=`, `?event=`); gli admin vedono quelle di tutti |
| POST | `/api/reservations/` | Sì | Proprietario | `{"event","seat","notes"}` | `201` oggetto prenotazione | Prenota un posto specifico e disponibile per un evento |
| GET | `/api/reservations/{id}/` | Sì | Proprietario o Admin | — | `200` oggetto prenotazione | Recupera una prenotazione |
| PUT/PATCH | `/api/reservations/{id}/` | Sì | Proprietario o Admin | `{"seat","notes"}` | `200` oggetto prenotazione | Sposta su un altro posto disponibile e/o modifica la nota |
| DELETE | `/api/reservations/{id}/` | Sì | Proprietario o Admin | — | `204` | Elimina definitivamente la prenotazione e libera il posto |
| POST | `/api/reservations/{id}/cancel/` | Sì | Proprietario o Admin | — | `200` oggetto prenotazione | Annullamento soft: mantiene il record, libera il posto (endpoint di ruolo/azione) |
| GET | `/api/reservations/{id}/status/` | Sì | Proprietario o Admin | — | `200` `{"id","status","event_title","seat_number",...}` | Verifica leggera e dedicata dello stato |

Tutti gli errori di validazione restituiscono `400` con un formato
coerente, ad esempio prenotando un posto già riservato:
```json
{
  "error": true,
  "status_code": 400,
  "detail": "One or more fields failed validation.",
  "fields": { "seat": ["This seat is already reserved."] }
}
```
(i messaggi restituiti dall'API restano in inglese per coerenza con il
contratto dati testato sopra — vedi anche la Sezione 11.)

## 9. Test con HTTPie

Installa HTTPie: <https://httpie.io/docs/cli/installation> (oppure più
semplicemente `python -m pip install httpie`).

**URL base:** sostituisci `$BASE` qui sotto con `http://127.0.0.1:8000`
in locale, oppure con il tuo URL di deployment dalla §7.

```bash
# Effettua il login e ottieni un token (oppure usa il flag --auth di httpie
# come mostrato più sotto)
http POST $BASE/api/auth/login/ username=alice password=demopass123

# -> copia il campo "token" dalla risposta, poi usalo così:
export TOKEN=f56390b7507499897e25648cfd62e7ee89e7be1   # solo un esempio

# Ripeti lo stesso login con altri account demo per ottenere gli altri
# token usati più sotto (stessa richiesta, cambiano solo le credenziali):
#   http POST $BASE/api/auth/login/ username=admin password=admin123   -> copia in $ADMIN_TOKEN
#   http POST $BASE/api/auth/login/ username=bob   password=demopass123 -> copia in $BOB_TOKEN
export ADMIN_TOKEN=...   # token ottenuto effettuando il login come "admin"
export BOB_TOKEN=...     # token ottenuto effettuando il login come "bob"

# Tutto ciò che segue il login usa:  Authorization:"Token $TOKEN"

# Registra un nuovo account cliente
http POST $BASE/api/auth/register/ \
  username=newuser email=newuser@example.com \
  password=Sup3rSecure!9 password_confirm=Sup3rSecure!9 \
  first_name=New last_name=User

# Sfoglia gli eventi (nessuna autenticazione richiesta)
http GET $BASE/api/events/
http GET "$BASE/api/events/?category=concert&search=jazz"
http GET $BASE/api/events/1/
http GET "$BASE/api/events/1/seats/?status=available"
http GET $BASE/api/events/1/availability/

# Crea una prenotazione (prenota il posto con id 3 per l'evento con id 1)
http POST $BASE/api/reservations/ Authorization:"Token $TOKEN" \
  event:=1 seat:=3 notes="posto lato corridoio per favore"

# Elenca le mie prenotazioni
http GET $BASE/api/reservations/ Authorization:"Token $TOKEN"

# Controlla lo stato di una prenotazione
http GET $BASE/api/reservations/6/status/ Authorization:"Token $TOKEN"

# Aggiorna la nota di una prenotazione
http PATCH $BASE/api/reservations/6/ Authorization:"Token $TOKEN" \
  notes="nota aggiornata"

# Annulla una prenotazione (annullamento soft, libera il posto)
http POST $BASE/api/reservations/6/cancel/ Authorization:"Token $TOKEN"

# Elimina definitivamente una prenotazione
http DELETE $BASE/api/reservations/6/ Authorization:"Token $TOKEN"

# Solo admin: crea un nuovo evento
http POST $BASE/api/events/ Authorization:"Token $ADMIN_TOKEN" \
  title="Test Expo" venue="Fortezza da Basso" \
  event_date="2027-01-15T10:00:00Z" total_seats:=40 price:=3.00 \
  category=other

# Azione vietata: alice (customer) prova a creare un evento -> 403 Forbidden
# (dimostra che il controllo dei permessi è applicato lato server, non solo
# nascosto nell'interfaccia)
http POST $BASE/api/events/ Authorization:"Token $TOKEN" \
  title="Non dovrebbe funzionare" venue="X" \
  event_date="2027-01-15T10:00:00Z" total_seats:=10

# Azione vietata: bob prova a vedere una prenotazione di alice -> 404 Not Found
# (un cliente non vede/non può agire sulle prenotazioni altrui)
http GET $BASE/api/reservations/1/ Authorization:"Token $BOB_TOKEN"

# Logout (invalida il token)
http POST $BASE/api/auth/logout/ Authorization:"Token $TOKEN"
```

Le versioni equivalenti con `curl` di ogni comando sopra funzionano
altrettanto bene, ad esempio:
```bash
curl -X POST $BASE/api/auth/login/ -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"demopass123"}'
```

## 10. Client di test incluso

Un client HTML/JS a file singolo viene servito direttamente dall'app su
**`/client/`** (es. `http://127.0.0.1:8000/client/`, oppure
`<il-tuo-url-di-deployment>/client/`). Non richiede alcuna build o
installazione — apri l'URL in un browser e comunicherà con qualsiasi URL
base dell'API configurato in cima alla pagina (di default l'origine della
pagina stessa). Supporta l'intero flusso: registrazione/login (inclusi
pulsanti di login rapido per gli account demo), navigazione degli eventi,
visualizzazione di una mappa dei posti in tempo reale, prenotazione di un
posto, ed elenco/aggiornamento/annullamento/eliminazione/verifica dello
stato delle proprie prenotazioni, con un log delle risposte JSON grezze
per trasparenza durante i test.

## 11. Note di progettazione

- **Annullamento soft vs. eliminazione:** `POST /cancel/` imposta
  `status=cancelled` e libera il posto mantenendo comunque la riga della
  prenotazione (utile per storico/controllo); `DELETE` rimuove la riga
  del tutto. Entrambi liberano il posto.
- **Protezione dal doppio-booking:** creazione/aggiornamento di una
  prenotazione tentano di bloccare la riga del posto (`select_for_update`)
  dentro una transazione, ma su **SQLite questo lock è un no-op** (il
  backend non supporta `SELECT ... FOR UPDATE`: Django lo ignora
  silenziosamente senza sollevare errori). La vera garanzia,
  indipendente dal backend, è un **vincolo di unicità a livello di
  database** (`unique_confirmed_reservation_per_seat` su `Reservation`):
  al massimo una prenotazione `confirmed` per posto. Se due richieste
  concorrenti superano entrambe il controllo Python "check-then-write",
  il database rifiuta la seconda scrittura con un `IntegrityError`, che
  i serializer intercettano e traducono in un normale `400` con
  `{"seat": ["This seat is already reserved."]}` invece di un errore
  `500`. Su PostgreSQL il lock di riga funzionerebbe davvero e
  ridurrebbe ulteriormente il tempo in cui due richieste possono
  competere per lo stesso posto, ma il vincolo DB resta comunque la
  rete di sicurezza effettiva su qualunque backend.
- **La registrazione non concede mai l'accesso staff** — il ruolo `admin`
  viene assegnato solo tramite il comando di seed o l'admin di Django,
  così il confine dei permessi non può essere aggirato semplicemente
  registrando un account.
- **Lingua:** i commenti nel codice e questo README sono in italiano; i
  nomi dei campi/endpoint JSON e i messaggi di errore restituiti dall'API
  restano in inglese, per corrispondere esattamente agli esempi di
  richiesta/risposta documentati sopra ed essere coerenti con le
  convenzioni REST internazionali.
