from whitenoise.storage import CompressedManifestStaticFilesStorage


class LenientManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """
    Identica alla CompressedManifestStaticFilesStorage di WhiteNoise, ma
    non fa mai fallire una richiesta se un asset non è (ancora) presente
    nel manifest hashato.

    Perché serve: il tag template {% static %} chiama sempre lo storage
    configurato in STORAGES["staticfiles"], indipendentemente da DEBUG.
    Con DEBUG=False (default dopo la correzione di ISS-008) e senza aver
    eseguito prima `collectstatic`, lo storage "strict" di Django prova a
    risolvere il nome hashato del file (dal manifest, o calcolandolo al
    volo dal file sorgente) e solleva ValueError se non ci riesce in
    nessuno dei due modi - il che rompeva del tutto pagine come
    /admin/login/ su un clone locale appena fatto, senza collectstatic.

    Qui si intercetta quel ValueError e si ricade sul nome file così
    com'è (non hashato), così la pagina si carica comunque - abbinato a
    WHITENOISE_USE_FINDERS=True in settings.py, che permette a WhiteNoise
    di servire quel file anche senza STATIC_ROOT popolato. In produzione,
    dove build.sh esegue sempre collectstatic prima dell'avvio, il
    manifest esiste regolarmente e si ottengono comunque tutti i vantaggi
    di hashing/compressione: questo fallback scatta solo quando manca.
    """

    def stored_name(self, name):
        try:
            return super().stored_name(name)
        except ValueError:
            return name
