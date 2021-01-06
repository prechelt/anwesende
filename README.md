# a.nwesen.de: Ein Dienst für Anwesenheitslisten für Hochschulen

Lutz Prechelt, 2021-01-06

https://github.com/prechelt/anwesende

Simple attendance registration for universities having pandemics.
"anwesende" is German for "people that are being present".


**DE**: Eine sehr einfache Lösung für die Verfolgung von Infektionsketten,
die stark auf menschliche Urteilskraft und manuelle Schritte baut, 
um die Software einfach und den Gebrauch flexibel zu halten.

**EN**: A very simple web application to help tracing infection chains 
at universities.
Makes heavy use of human judgment and manual operations 
to keep the software simple and its use flexible.  
Designed for universities in the German-language area, so parts
of the application are German+English, parts are German-language only.
The code and technical documentation (Sections 4 and 5) are in English.

# 1. Abläufe / Business processes (German only)

## 1.1. Überblick

Rollen: 
- Dienst `a.nwesen.de` (kurz: Dienst): 
  Die hier web-basierte Funktionalität,
  die die hier beschriebene Software entfaltet, wenn man sie betreibt. 
- Teilnehmende Hochschule (kurz: Hochschule): 
  Eine Hochschule, die den Dienst betreibt oder mit nutzt.
- Besucher/in: Eine Person, deren Anwesenheit in einem Raum der Hochschule
  erfasst werden soll. 
- Datenverwalter/in: Die Person, die Lesezugriff auf die erfassten
  Anwesenheitsdaten hat und anderen Berechtigten selektiv Zugang verschafft.

Schritte des Gesamtablaufs:
1. Eine Einheit einer teilnehmenden Hochschule übermittelt der Datenverwalter/in 
   eine Liste von Räumen und Sitzplätzen, 
   siehe `Räume übermitteln` unten.
2. Sie erhält im Gegenzug eine PDF-Datei mit einem QR-Code für
   jeden Sitzplatz
   und klebt den QR-Code dauerhaft am zugehörigen Sitzplatz auf.
3. Ein/e Besucher/in scannt den QR-Code an ihrem Sitzplatz
   und gibt mininale Daten für die Verfolgung ein;
   siehe `Besucher/innen/sicht` unten.
4. Der Dienst speichert die Platzdaten, Personendaten und den Zeitpunkt.
5. Im Infektionsfall ruft die Datenverwalter/in die Anwesenheitsdaten für die
   Kontaktgruppen einer infizierten Person im passenden Zeitfenster 
   (z.B. 3 Tage) ab,
   um sie dem Gesundheitsamt zu übermitteln;
   siehe `Anwesenheitsdaten abrufen` unten.

Große Teile dieser Beschreibung sind auch in der Software selbst enthalten:
Der Überblick in 
[anwesende/templates/room/home.html](anwesende/templates/room/home.html)),
die Beschreibung der Schritte 1, 3 und 5 in 
[anwesende/templates/room/import.html](anwesende/templates/room/import.html),
[anwesende/templates/room/privacy.html](anwesende/templates/room/privacy.html) und
[anwesende/templates/room/search.html](anwesende/templates/room/search.html).

Weitere Informationen finden sich in den FAQs unter
[anwesende/templates/room/faq.html](anwesende/templates/room/faq.html)).


## 1.2 Besucher/innen/sicht

Rollen: 
- Dienst `a.nwesen.de`, 
- Besucher/in ('ich') einer teilnehmenden Hochschule.

1. Ich komme in einen offenen Raum der teilnehmenden Hochschule.
   An meinem Sitzplatz klebt ein QR-Code. Ich scanne ihn mit meinem
   Smartphone und lande in meinem Webbrowser auf einer Seite mit
   ungefähr so einem Namen: `https://a.nwesen.de/1234567890`.
2. Der Dienst zeigt mir Datenschutzhinweise.
3. Ich gebe meine Daten ein (Vorname, Name, Mobilfunknummer, Email,
   Straße/Hausnummer, PLZ, Ort)
   und sende das Formular ab.  
   Ab dem zweiten Aufruf ist das Formular wegen eines Cookies
   sogar schon vor-ausgefüllt und ich muss es nur absenden.

Anmerkungen: 
- Der Dienst registriert nur das **Kommen** in einen Raum,
  nicht das **Verlassen** (in der Annahme, dass das nicht gut klappen würde,
  aber die betroffenen Zeiträume trotzdem meist gut eingrenzbar sind).
- Zum Scannen von QR-Codes gibt es zahllose Apps.
  Einfach im PlayStore/AppStore nach `QR Code` suchen.


## 1.3 Räume übermitteln

Rollen: 
Mitarbeiter/in einer teilnehmenden Hochschule,
Datenverwalter/in.

1. Die Mitarbeiter/in lädt sich die 
   [Excel-Vorlage zur Raumübermittlung](anwesende/static/xlsx/roomdata-example.xlsx)
   und füllt sie aus:
   - Die Überschriftzeile und die Zellenformate keinesfalls ändern!
   - Jeder Raum bekommt eine Zeile.
   - Für alle Einträge bitte genau die nachfolgenden Hinweise beachten:
   - `organization`: Domainname der teilnehmenden Hochschule, z.B.
     `fu-berlin.de` für die Freie Universität Berlin.  
     Dieser Wert ist in allen Zeilen der Datei gleich.
   - `department`: Intern gebräuchlicher (Kurz)Name der Hochschuleinheit, z.B.
     `MathInf` für den Fachbereich Mathematik und Informatik.  
     Auch dieser Wert ist in der Regel in allen Zeilen der Datei gleich,
     weil die Mitarbeiter/in nur zu diesem einem Bereich gehört.
   - `building`: Gebäudebezeichnung, meist Straße und Hausnummer, z.B.
     `Takustr. 9` für das Informatik-Hauptgebäude in der Takustraße 9.  
     Diesen Wert sollte man (genau wie alle anderen) am besten kurz halten,
     da er auf dem QR-Code-Schild mit ausgedruckt wird und dort
     die verfügbare Breite nicht überschreiten sollte.  
     Der Name muss nicht unbedingt exakt zum Straßenschild passen.
     Wenn es also von einem langen Straßennamen eine in dieser
     Hochschuleinheit allgemein gebräuchliche Abkürzung gibt,
     könnte man auch die verwenden.
   - `room`: Raumbezeichnung, in der Regel eine Raumnummer, z.B.
     `055` für den Seminarraum 055 im Erdgeschoss.  
     Dies sollte zur Beschriftung an der Eingangstür des Raums passen.
   - `seat_last`: Letzter Sitz, z.B. `r2s7` für Reihe 2, Sitz 7 in einem
     Raum mit 14 Sitzen in zwei Reihen. Der erste Sitz ist immer `r1s1`.  
     Diese Sitznamen werden auf den QR-Code-Schildern
     gut lesbar mit ausgedruckt.
     Wenn Reihen unterschiedlich viele Sitze haben, muss die maximale Anzahl
     auch für die letzte Reihe angegeben werden (selbst wenn die in Wirklichkeit
     kürzer sein sollte) und manche QR-Codes werden dann
     nicht mit aufgeklebt; hier ein 
     [Beispiel mit `seat_last` r5s4](anwesende/static/images/seatname-example.png).  
     Die Software nimmt je 1,4m Sitzabstand an und gibt 
     im Schritt "Anwesenheitsdaten abrufen" resultierende Abstände mit aus.
2. Die Mitarbeiter/in schickt die Excel-Datei per Email an
   die Datenverwalter/in.
3. Die Datenverwalter/in prüft die Daten auf Plausibilität,
   liest die Datei in den Dienst ein
   und erhält eine Seite mit QR-Codes als Ergebnis.
   Sie enthält für jeden Sitzplatz einen QR-Code mit beschreibender Beschriftung
   wie es in der Excel-Datei deklariert war.
5. Die Datenverwalter/in druckt diese Webseite in eine PDF-Datei
   und schickt sie der Mitarbeiter/in per Email.  
6. Die Mitarbeiter/in druckt die QR-Codes aus und klebt jeden davon
   auf den entsprechenden Sitzplatz im entsprechenden Raum.  
   Der QR-Code sollte vollständig mit mattem transparentem Klebeband
   bedeckt sein, damit er lange lesbar bleibt.

Varianten:

Schritt 3b: Ist die Datei fehlerhaft und lässt sich nicht einlesen,
korrigiert die Datenverwalter/in offensichtliche Fehler selbst
und klärt andernfalls die Korrekturen mit der Mitarbeiter/in.

Anmerkungen:

- Obige Beschreibung gilt für den Bereich der Lehre. 
  Im Bürobereich wird hingegen grober erfasst:
  Ein Bereich, in dem sich Beschäftigte vermutlich gelegentlich auch 
  länger begegnen (Korridor, Küche, Besprechungsraum, Bürobesuche), 
  wird zu einem "Raum" zusammengefasst, z.B. ein ganzer Flur.  
  Dadurch muss jede/r nur einmal pro Tag eine Eingabe machen und die 
  Kontaktgruppen fallen eher zu groß aus als zu klein. 
  Das ist deshalb sinnvoll, weil es wesentlich einfacher ist, 
  eine zu lange Liste möglicher Kontakte zu bereinigen, 
  als fehlende Kontakte aufzuspüren.
- Innerhalb eines solchen "Raums" kann man dann Räume (oder
  Teile davon) als Sitzplätze interpretieren und die
  Beschäftigten anhalten, sich ggf. mehrfach anzumelden,
  wenn sie länger an einem anderen "Sitzplatz" (z.B. der Küche)
  als ihrem üblichen eigenen sind,
  damit bei der Nachverfolgung das Sortieren in Kontakte
  und Nichtkontakte von den Anmeldedaten besser unterstützt wird.  
- Beispiel: A und B arbeiten gleichzeitig am "Sitzplatz" 1 
  (tatsächlich Raum 33).
  C, D, E, F, G, H arbeiten zur selben Zeit an den "Sitzplätzen" 
  2, 2, 3, 4, 5, 5, 
  (tatsächlich den Räumen 34, 34, 35, 36, 37, 37).  
  Die Küche ist als "Sitzplatz" 7 registriert.  
  Wenn sich A infiziert, ist sofort B als Kontakt klar.
  Aber was ist mit B bis H?  
  A, C und F haben sich am fraglichen Tag auch mal am Sitzplatz
  7 angemeldet. C zu einer anderen Zeit als A, aber F zu einer überlappenden.   
  Bei der Abfrage würden also B bis H alle in der Kontakteliste
  aufgeführt, aber B und F sind als wahrscheinlichste Kontakte
  leicht erkennbar, denn B hat den gleichen "Sitzplatz" 1 wie A
  und F hat den gleichen "Sitzplatz" 7 wie A.
  Den hat auch C, wird aber mangels Zeitüberlappung nur auf der
  gleichen mäßigen Risikostufe geführt wie die übrigen.


## 1.4 Anwesenheitsdaten abrufen

Rollen:
Infiziertes Mitglied der Hochschule,
Mitarbeiter/in der Hochschuleinheit,
Datenverwalter/in

1. 1. Ist ein Mitglied (oder ein/e Besucher/in) der Hochschule infiziert, 
   so informiert es die betreffenden Hochschuleinheit(en) darüber,
   an welchen Tagen eine Infektiösität bestanden haben kann.
2. Die Mitarbeiter/in der Hochschuleinheit, die bei der Datenverwalter/in
   als abrufberechtigt bekannt ist, übermittelt diesen Zeitraum und
   die Personendaten (Name, Telefon, Email) der infizierten Person per
   Email an die Datenverwalterin.  
3. Die Datenverwalter/in ruft die zugehörigen Kontaktpersonen ab und übermittelt
   sie an die Mitarbeiter/in.
   Als Kontaktpersonen gelten alle, die Einträge im selben Raum haben,
   die sich zeitlich mindestens 15 Minuten mit der Anwesenheit der
   infizierten Person überlappen.
4. Die Mitarbeiter/in bereinigt die Daten per Augenschein und Rückfragen 
   und entfernt ggf. überzählige Einträge.
5. Die Mitarbeiter/in übermittelt die bereinigten Daten dem
   Gesundheitsamt.
   

# 2. Vor- und Nachteile / Pros and cons (German only)

im Vergleich zu papierbasierter Erfassung der Anwesenheit

Vorteile:
- Zeitersparnis Erfassung: 
  Die Erfassung geschieht mit viel weniger Zeit- und Arbeitsaufwand.
- Zeitersparnis Kontaktverfolgung:
  Im Infektionsfall kann dem Gesundheitsamt innerhalb von
  Minuten eine vollständige _elektronische_ Liste der möglichen
  Kontaktpersonen übermittelt werden.
- Ressourcenersparnis: 
  Spart erhebliche Mengen an Papier ein.
- Hygiene: 
  Es müssen keine Papiere von Hand zu Hand weitergegeben werden.
- Datenschutz 1: 
  Nur eine Person hat anlasslos Zugang zu den erfassten Daten.
  Im Papierfall sind dies viele und es ist schwierig zu überschauen, welche.
- Datenschutz 2:
  Die Daten können am Ende der Aufbewahrungsfrist vollautomatisch und
  somit verlässlich gelöscht werden.

Risiken:
- Datenschutz:
  Ein gegebenenfalls erfolgreicher Einbruch in die Datenbank des Servers
  beträfe mehr Daten als
  ein Diebstahl papierner Erfassungsbögen.  
  (Das Risiko ist klein, denn die Datenbank ist für Angreifer nicht attraktiv,
   weil sie keine wertvollen Daten wie Bankdaten oder Passwörter enthält.)
- Vollständigkeit:
  Der Erfassungsvorgang ist für die anderen Anwesenden weniger anschaulich
  und kann deshalb möglicherweise leichter vergessen werden. 
- Richtigkeit:
  Unsinnige Eingaben von Besuchern ("Donald Duck") sind kaum mehr 
  an Ort und Stelle zu entdecken.


# 3. Der/Die Datenverwalter/in / The main administrator role (German only)

- Benötigt eine Einweisung (ca. 1 Stunde).
- Muss Mitglied einer teilnehmenden Hochschule sein.
  Alle anderen teilnehmenden Hochschulen müssen mit dieser Hochschule
  einen Auftragsdatenverarbeitungsvertrag schließen.
- Sollte bei jeder Meldung von Räumen aus einer Hochschuleinheit
  die Excel-Datei durchsehen und nötigenfalls die Schreibweisen
  (insbesondere von Hochschuleinheiten) vereinheitlichen.
- Muss bei jeder Meldung von Räumen aus einer Hochschuleinheit klären,
  wer für diese Einheit berechtigt ist, Anwesenheitsdaten abzurufen,
  und dann den Datenzugang auf diesen Personenkreis beschränken.
  

# 4. Deployment and operation

Everything beyond this point is technical information, therefore in English.

The application is meant to be deployed locally in most organizations
(to simplify the situation regarding privacy protection)
and allows some configuration to adopt to local needs.  
It is designed such that one installation can serve several smaller
organizations together, though.


## 4.1 Architecture

The service is build using Python, Django, PostgreSQL, Gunicorn, and Traefik.
The deployment procedure described below will obtain these pieces
and configure them.
The code organization roughly follows the
[cookiecutter-django](https://cookiecutter-django.readthedocs.io) template
and the Python code is structured Django-style.


## 4.2 Deployment overview

(If you find errors anywhere, please speak up!)

The deployment procedure assumes an existing infrastructure of
Linux, bash, ssh, rsync, and Docker 18.09 or younger 
(with docker-compose 1.21 or younger).
The deploying user must be a member of the `docker` group.

There are six possible styles of deployment:
- `DEPLOYMODE=CERTS`: a stand-alone configuration that brings its own Traefik web server
  and relies on a manually created certificate for https.
  This configuration uses three docker containers: traefik, django, postgres.
- `DEPLOYMODE=LETSENCRYPT`: a variant of the above that
  relies on Let's Encrypt to generate the certificates for https.
- `DEPLOYMODE=GUNICORN`: a configuration without webserver that exposes the
  service port of the Gunicorn application server to be used by 
  an existing webserver that is capable of https. 
  This configuration uses only two docker containers: django, postgres.

All three of these can be deployed locally on a single server (`REMOTE=0`)
or have their docker images build on a local machine
and deployed onto a remote server via a docker registry 
(`REMOTE=1`, resulting in another three styles of the same three DEPLOYMODEs).
In any case, there are only few manual steps; most work is done by a 
few calls to a script called `anw.sh`.


## 4.3 Deployment procedure

1. Create a working directory anywhere on a Linux machine 
   (called the 'source machine').
   If your server is in a DMZ and cannot connect to other servers itself,
   this must be a separate machine (`REMOTE=1`). 
   Perform
   `git clone https://git.imp.fu-berlin.de/anwesende/anwesende.git`.
   Rename the directory if you want, e.g.: `mv anwesende anw`,  
   and go there: `cd anw`.  
   This working directory is the reference for all subsequent commands.
2. Do `./anw.sh - prepare_envs`.
   This creates two new files:
   - `.envs/myenv.env` is a docker environment file containing various
     application settings. Carefully review the comments in that file and insert
     appropriate values for each setting.
   - `.envs/production.sh` is a shell environment file containing various
     deployment settings. Carefully set appropriate values here, too.
3. If `REMOTE=1`, call `./anw.sh production docker_login` and type
   your password twice to log into the docker registry locally and on the server.
   (If `REMOTE=0`, skip this step.)
4. Do `./anw.sh production install`.
   If all goes well, this command will
   - build the docker images on the source machine
   - if `REMOTE=1`, transfer them to the server's docker service via the registry
     and copy a handful of configuration files to the server's `~/anw` directory. 
   - create and start the docker containers on the server.
   Carefully review the output for error messages. 
   Repair those problems and repeat the command.
5. For `DEPLOYMODE=CERTS` only:  
   Put your certificate at 
   `$VOLUME_SERVERDIR_TRAEFIK_SSL/certs/anwesende.pem`
   and your private key at 
   `$VOLUME_SERVERDIR_TRAEFIK_SSL/private/anwesende-key.pem`.
   Make directory `private` readable for root only.  
   (Alternatively, you can pre-create these directories yourself before
   you start the traefik container. Anybody can be the owner then; traefik does
   not care.)
6. For `DEPLOYMODE=GUNICORN` only:
   - The django container runs the Gunicorn application server, which will
     expect requests via http (and only http) on port GUNICORN_PORT as
     defined in `.envs/production.sh`.
   - Define a name prefix on your webserver, for which it will 
     remove the name prefix from the request and then forward the rewritten
     request to `yourserverhost:${GUNICORN_PORT}` (e.g. `localhost:5000`).  
     For instance, for Apache (if running on the same server), 
     this might mean adding the file
     `/etc/apache2/conf-available/anwesende_proxy.conf` containing
     ````
     ProxyRequests Off
     ProxyPass "/anw"  "http://localhost:5000"
     ProxyPassReverse "/anw"  "http://localhost:5000"
     ````
     and then perform
     `a2enconf anwesende_proxy; systemctl reload apache2`.

Steps 3 to 6 can be repeated as needed with no harm. 
To start over from step 1, remove the reference directory (and beware
that this will delete your settings in `.envs` as well).


## 4.4 Debugging

- If all went well, your anwesende server should now be reachable.  
  Let's assume it is called `anwesende.some-university.de`.
  Start a web browser and visit `https://anwesende.some-university.de`.  
- Works?    
  Then now set `PATCH_DJANGO_HTTPS_INSIST=True` in `.envs/production.sh` and
  repeat step 4 above. Congratulations!  
- Does not work?  
  Then consider the following ideas for your debugging:
- Step 4 has substep commands that you can call independently.
  - Execute `./anw.sh - help` to see them.  
  - Look into the file `anw.sh` how they are used in `install()`.
  - You can teach your bash autocompletion of these command names by executing
    `./anw.sh - completions` (which prints a long command) 
    and then executing the command that it printed.
    (Backticks do not work properly for this for some reason.)
  - In a `REMOTE=1` setting, be aware that you can thoroughly confuse yourself
    with these commands if you fail to include `onserver` with 
    `docker-compose` or `docker`, because your local docker will comply with
    them gladly, but not change anything on the server. 
- In `DEPLOYMODE=LETSENCRYPT`, you may have to wait 2 minutes for
  the certificates to arrive.
- Consult the logs, either from remote (if `REMOTE=1`) by 
   `./anw.sh production.sh onserver docker-compose logs`
   or right on the server by `dcoker-compose logs`.
- In `DEPLOYMODE=CERTS`, traefik will ignore your certificate if it does
  not match the request (different fully-qualified domain name).
  No log entry is created if this happens.
- For https trouble, study the SECURITY block in the 
  `config/settings/production.py` configuration file (in particular the
  `SECURE_HSTS_SECONDS` setting) in order to understand what you are working
  with during https debugging.
- The simplest setup is using `DEPLOYMODE=GUNICORN` and then contacting
  gunicorn on the `GUNICORN_PORT` directly.
  If you have fundamental doubts whether the postgres and django containers
  work, try that.
   
   
## 4.5 Cronjob, DB-Backup/Restore, Identify, Load test

1. Create a cronjob with the following script (insert the proper directory name).
   It serves two purposes: Delete data after the retention period and
   make database backups.
   ```
   #!/bin/bash
   cd /home/thedeployer/anw/prod  # adjust this! We need docker-compose.yml
   set -a; source .envs/production.sh; 
   docker-compose run --rm django python manage.py delete_outdated_data  # to obey DATA_RETENTION_DAYS
   docker-compose exec postgres backup
   ```
   Add a suitable `logrotate` call to avoid accumulating too many backups.
2. If you ever need to restore a backup:
   - Copy the backup file to directory `$VOLUME_SERVERDIR_POSTGRES_BACKUP`.
     Let us assume it is called `mybackup.sql.gz`.
   - Go to the directory where your `docker-compose.yml` is and perform 
     ```
     docker-compose kill django
     docker-compose exec postgres restore mybackup.sql.gz
     docker-compose restart django
     ```
3. If you ever wonder what version you are running, try this:  
   `docker inspect anw_prod_django | grep anwesende.build`
4. Purely optional:
   There is a simple, stand-alone load testing script in
   `anwesende/room/tests/loadtest.py`
   with which you can get a rough estimate of 
   your server's performance.


## 4.6 Short-URL service

There is one installation of anwesende that is special:
The one at `http://a.nwesen.de` (no https here!). 
It can be used by all other installations for creating short URLs.
(The shorter the URLs specified by the QR codes, the more robust these
codes can be against scratching, chocolate taints etc.)  
So instead of seat URLs like `https://anwesende.some-university.de/S12345abcde`
your installation can use URLs like `http://a.nwesen.de/z/S12345abcde`
which will simply redirect to the corresponding one above.  
How? 
- You send me your installation URL such as 
  `https://anwesende.some-university.de` or
  `https://www.some-university.de/services/anwesende` 
  or whatever it may be and ask me for a 
  `SHORTURL_PREFIX`.
- I assign a prefix, such as `http://a.nwesen.de/p`,
  enter it into the configuration of the central installation,
  and tell you about it. 
- You enter it into your settings file at `.envs/myenv.env`
  (for instance `SHORTURL_PREFIX=http://a.nwesen.de/p`) and
  repeat `./anw.sh production install`.

If you do not want to use the short URL service,
simply set SHORTURL_PREFIX to your installation URL instead,
e.g. `https://anwesende.some-university.de`.

If you have created QR codes previously, make sure the URLs they
show continue to work.
(Please do not try to guess what `SHORTURL_PREFIX` you are going
to get; race conditions may occur.)

Your service is now ready to be used.
Time to create the Datenverwalter accounts!


## 4.7 Initiating operation

Once the server is running and you can retrieve the homepage properly,
perform the following steps once:

- Perform  
  `./anw.sh production.sh onserver docker-compose run --rm django python manage.py createsuperuser --username superuser`.
  You could use a different username if you prefer.
  Enter a (near-irrelevant) email address and password for the superuser.
- In a browser, visit
  `https://anwesende.some-university.de/admin`, 
  log in as the superuser, and create two-or-so personal accounts for the
  Datenverwalters at `https://anwesende.some-university.de/admin/users/user/`.  
  - Enter strings for name (fullname), firstname, lastname, email.  
  - Do not change any of the checkboxes.  
  - Under "Groups:" pick group "datenverwalter" and add it to "Chosen groups".  
    Save.  
    This group membership is what gives an account the Datenverwalter
    privilege. The superuser account does not (and should not) have that privilege.
  
Done!


# 5. Release versions

<b>
The application is complete and tested (with 95% code coverage), 
but not yet field-tested: ready for pilot use only!
</b>

The application is written in Python using the Django framework
and a PostgreSQL database. 
It is open-source (with an MIT license) in order to
provide maximal transparency.

- 2020-10-06, Version 0.1: 
  - Started development: Use case descriptions
- 2020-10-21, Version 0.6: 
  - Basic functionality is complete:
    Login, reading Excel files, generating QR codes, visitor registration form,
    retrieving visit groups and writing Excel file
- 2020-10-28, Versison 0.7: 
  - User-visible process documentation
  - Demo mode
  - Automatic purging of visit data after retention time
- 2020-11-06, Version 0.8: 
  - Pilot deployment, deployment description
  - Load testing (about 1000 visits/minute: fast enough)
  - Logging
- 2020-12-29, Version 1.0: 
  - `anw.sh` install script for mostly automated deployment
- 2021-01-02, Version 2.0:
  - introduced 2-dimensional seat numbering and distance calculation
  - This is a semi-incompatible change: Existing pasted QR codes
    will show e.g. seat 14, but will in fact now refer to seat r1s14;
    existing importstep objects will lose their seats.
- 2021-01-05, Version 2.1:
  - added FAQ page
  - updated `/import` (which had outdated documentation in version 2.0)
  - more info on the QR code snippets: URL, instruction
  - published at GitHub
- 2021-01-06, Version 2.2:
  - README now also describes DB restore and deployment identification


TO DO:
- introduce `DEPLOYMODE=DEV` for development
- remove outdated deployment-related stuff