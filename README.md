# a.nwesen.de: Ein Dienst für Anwesenheitslisten für Hochschulen

Lutz Prechelt, 2020-11-29  (see "Implementation status" at the bottom)

[![coverage report](https://git.imp.fu-berlin.de/anwesende/anwesende/badges/master/coverage.svg)](https://git.imp.fu-berlin.de/anwesende/anwesende/-/commits/master)

Simple attendance registration for universities having pandemics.
"anwesende" is German for "people that are being present".


**DE**: Eine sehr einfache Lösung für die Verfolgung von Infektionsketten,
die stark auf menschliche Urteilskraft und manuelle Schritte baut, 
um die Software einfach und den Gebrauch flexibel zu halten.

**EN**: A very simple web application to help tracing infection chains 
at universities.
Makes heavy use of human judgment and manual operations 
to keep the software simple and its use flexible.  
Alas, the remainder of the documentation is mostly German only.


# 1. Abläufe

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
1. Eine teilnehmende Hochschule übermittelt der Datenverwalter/in 
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
   - `seat_min`: Kleinste Sitznummer, in aller Regel `1`.
   - `seat_max`: Größte Sitznummer, z.B. `14`.  
     Diese Sitznummern sind fortlaufend und werden auf den QR-Code-Schildern
     gut lesbar mit ausgedruckt.  
     In diesem beiden Feldern sind nur ganze Zahlen möglich.
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
   

# 2. Vor- und Nachteile

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


# 3. Der/Die Datenverwalter/in

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

The application is meant to be deployed separately in many organizations
(to simplify the situation regarding privacy protection)
and allows some configuration to adopt to local needs.

## 4.1 Deployment

(These instructions have not yet been tested. If you find errors, please speak up!)

The service is build using Python, Django, PostgreSQL, Gunicorn, and Traefik.
The deployment procedure described below will obtain these pieces
and configure them.
The code organization follows the
[cookiecutter-django](https://cookiecutter-django.readthedocs.io) template.

The deployment procedure assumes an existing infrastructure of
Linux, bash, and Docker 18.09 or younger (with docker-compose 1.21 or younger).
There are three possible configurations:
- Case CERT: a stand-alone configuration that brings its own Traefik web server
  and relies on a manually created certificate for https. The default.
  This configuration uses three docker containers: traefik, django, postgres.
- Case LETS: a variant of the above that
  relies on Let's Encrypt to generate the certificates for https.
- Case NOWS: a configuration meant to run behind an existing webserver
  that is capable of https. 
  This configuration uses only two docker containers: django, postgres.

Some of the deployment steps will be case-specific.

Deployment procedure:
1. Create a working directory anywhere on your Linux server.
   The instructions assume you will take care of appropriate
   access rights for all directories involved.  
   Perform
   `git clone https://git.imp.fu-berlin.de/anwesende/anwesende.git`.  
   And go there: `cd anwesende` (you can rename the directory if you prefer).
   This working directory is the reference for all commands.
2. Do `mkdir .envs; cp config/env-template .envs/.production`.
   and set the environment variables in `.envs/.production`
   as described in that file.  
   Note this is an extremely limited file format: No blanks are allowed
   around the `=` and all values are used verbatim 
   (including the quotes if you use any!)  
   The handling of SHORTURL_PREFIX will be described in section 4.2 below.  
   For `PRIVACYINFO_DE` and `_EN`, the URL path prefix `/static` refers to
   the directory `anwesende/static`. 
3. Optional: Review `anwesende/templates/room/privacy.html` and decide 
   whether you need to modify it.
   If so, either change it directly (make sure you keep a copy in case of 
   later software updates) or fork
   [https://github.com/prechelt/anwesende](https://github.com/prechelt/anwesende),
   a release-versions-only copy of the above development repository,
   put your modification on a branch of your fork, and use the fork in step 1.
   (If that Github repo does not yet exist, holler.)
4. For case NOWS only:
   - In file `production.yml`, 
     remove or comment the whole `traefik` configuration block. 
   - The django container runs the Gunicorn application server, which will
     expect requests via http (and only http) on port GUNICORN_PORT as
     defined in `.envs/.production`.
   - Define a name prefix on your webserver, for which it will 
     remove the name prefix from the request and then forward the rewritten
     request to `yourserverhost:$(GUNICORN_PORT)` (e.g. `localhost:5000`).  
     For instance, for Apache, this might mean adding the file
     `/etc/apache2/conf-available/anwesende_proxy.conf` containing
     ````
     ProxyRequests Off
     ProxyPass "/anw"  "http://localhost:5000"
     ProxyPassReverse "/anw"  "http://localhost:5000"
     ````
     and then perform
     `a2enconf anwesende_proxy; systemctl reload apache2`.
5. For case LETS only: 
   modify `compose/production/traefik/traefik.yml` as follows in the 
   http / routers / web-secure-router / tls block:
   - comment the `certificates` block (3 lines),
   - uncomment the whole `certificatesResolvers` block (~9 lines)
   - uncomment the `certResolver` line next to the `certificates` block.
6. Define the environment by (in bash)
   `set -a; source .envs/.production`
   and perform `docker-compose -f production.yml build`.
   This will create three docker images:
   `anwesende_production_django`, `anwesende_production_postgres`, and
   `anwesende_production_traefik`.
   (The first name part is the directory name, different if you renamed it.)
7. If your target server is in a DMZ (de-militarized zone), you will have to
   perform the above steps on a build machine that is connected
   to the target server via a docker registry that both can access.
   In that case, you need to do the following additional steps
   (I will now assume you have basic docker knowledge, have heard of
    `docker login` etc.):
   - `docker push` the three docker images to the registry on the build server,
   - switch to the target server, and `docker pull` the three images there
   - The standard setup assumes the server files to lie in various subdirectories
     of path `/srv/docker/anwesende`.
     You can use a different path as you prefer.
   - Copy the build server working dir to `/srv/docker/anwesende/src`.
     I use something along the lines of  
     `rsync --exclude .git --exclude .*cache . targethost:/srv/docker/anwesende/src`
8. For case CERT only:
   Put your certificate at 
   `$ANW_HOSTDIR_TRAEFIK_SSL/certs/anwesende.pem`
   and your private key at 
   `ANW_HOSTDIR_TRAEFIK_SSL/private/anwesende-key.pem`.
   (For good order's sake, directory `private` should be readable for root only.)
9. Do `docker-compose -f production.yml up -d`.
   If all went well, your anwesende server should now be reachable.
   Let's assume it is called `anwesende.some-university.de`.
   Start a web browser and visit `https://anwesende.some-university.de`.  
   Works?  
   Then now set `DJANGO_HTTPS_INSIST=True` in `.envs/.production` and
   re-deploy (that is, repeat steps 6, 7, and 9). Congratulations!  
   Does not work?  
   Then have a look at the SECURITY block in the 
   `config/settings/production.py` configuration file (in particular the
   `SECURE_HSTS_SECONDS` setting) in order to understand what you are working
   with during https debugging.
10. Create a cronjob for continuous database health:  
    ```
    cd $reference_dir  # where the source code is (we need two config files)
    set -a; source .envs/.production; 
    docker-compose -f production.yml run --rm django python manage.py delete_outdated_data
    docker-compose -f production.yml exec postgres backup
    ```
11. Purely optional:
    There is a simple, stand-alone load testing script in
    `anwesende/room/tests/loadtest.py`
    with which you can optionalle get a rough estimate of 
    your server's performance.

   
## 4.2 Short-URL service

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
  `https://anwesende.some-university.de` and ask me for a 
  SHORTURL_PREFIX.
- I assign a prefix, such as `http://a.nwesen.de/z`,
  enter it into the configuration of the central installation,
  and tell you about it. (Don't get confused by the contents of
  `compose/production/traefik/traefik.yml`: All parts talking about
  `a.nwesen.de` are relevant only for the host that actually serves
  that hostname, not for yours. 
  They are present in the public repository for transparency only.)
- You enter it into your settings file at `anwesende/.envs/.production`
  (for instance `SHORTURL_PREFIX=http://a.nwesen.de/z`) and
  restart your server:  
  Do a `docker-compose -f production down` (which stops the server)
  and repeat the above steps 6, 7, and 9.

If you do not want to use the short URL service,
simply set SHORTURL_PREFIX to your installation URL instead,
e.g. `https://anwesende.some-university.de`

Your service is now ready to be used.
Time to create the Datenverwalter accounts!

## 4.3 Initiating operation

Once the server is running and you can retrieve the homepage properly,
perform the following steps once:

- Log in to the server and perform  
  `set -a; source .envs/.production` to define the environment
  (modern versions of docker-compose allow `--env-file` instead)
  and then
  `docker-compose -f production.yml run --rm django python manage.py createsuperuser --username superuser`.
  You can use a different username if you prefer.
- In a browser, visit
  `https://anwesende.some-university.de/admin`, 
  log in as the superuser, and create two-or-so personal accounts for the
  Datenverwalters at `https://anwesende.some-university.de/admin/users/user/`.  
  Enter strings for name (fullname), firstname, lastname, email.  
  Do not change any of the checkboxes.  
  Under "Groups:" pick group "datenverwalter" and add it to "Chosen groups".  
  Save.  
  This group membership is what gives an account the Datenverwalter
  privilege. The superuser account does not (and should not) have that privilege.
  
Done!

Note that by default, no email sending is configured, so the password reset
function (which is available on the web pages) is not going to work.
The superuser must tell the 


# 5. Implementation status

The application is **complete, but not yet field-tested: ready for pilot use only!**

The application is written in Python using the Django framework
and a PostgreSQL database. 
It is open-source (with an MIT license) in order to
provide maximal transparency.

- DONE 2020-10-06: Use case descriptions (will need update later)
- DONE 2020-10-08: Reading Excel files and creating master data
- DONE 2020-10-09: Generating QR codes 
- DONE 2020-10-12: Visitor input form and writing visit data
- DONE 2020-10-13: Retrieving visit data by person
- DONE 2020-10-15: Retrieving visit groups (contact groups)
- DONE 2020-10-15: Writing Excel file
- DONE 2020-10-19: Cleaning up code structure
- DONE 2020-10-21: homepage, privacy info
- DONE 2020-10-21: login, datenverwalter group, authorization checks
- DONE 2020-10-26: User-visible process documentation, DUMMY_ORG for demo mode.
- DONE 2020-10-28: Automatic purging of visit data after retention time
- DONE 2020-10-29: Pilot deployment
- DONE 2020-11-04: Automated system test of the whole workflow
- DONE 2020-11-05: Load testing (about 1000 visits/minute: fast enough)
- DONE 2020-11-06: Added logging
- DONE 2020-11-06: Deployment description
- TODO: Pilot testing
