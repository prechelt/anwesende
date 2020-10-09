# a.nwesen.de: Ein Dienst für Anwesenheitslisten für Hochschulen

Lutz Prechelt, 2020-10-09  (see "Implementation status" at the bottom)

Simple attendance registration for universities having pandemics.
"anwesende" is German for "people that are being present".


**DE**: Eine sehr einfache Lösung für die Verfolgung von Infektionsketten,
die stark auf menschliche Urteilskraft und manuelle Schritte baut, 
um die Software einfach und den Gebrauch flexibel zu halten.

**EN**: A very simple web application to help tracing infection chains 
at universities.
Makes heavy use of human judgment and manual operations 
to keep the software simple and its use flexible.  
Alas, the remainder of the documentation is available in German only (so far).


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
   siehe `Räume übermitteln`.
2. Sie erhält im Gegenzug eine PDF-Datei mit einem QR-Code für
   jeden Sitzplatz
   und klebt den QR-Code dauerhaft am zugehörigen Sitzplatz auf.
3. Ein/e Besucher/in scannt den QR-Code an ihrem Sitzplatz
   und gibt mininale Daten für die Verfolgung ein;
   siehe `Besucher/innen/sicht`
4. Der Dienst speichert die Platzdaten, Personendaten und den Zeitpunkt.
5. Im Infektionsfall ruft die Datenverwalter/in die Anwesenheitsdaten für jeden
   betreffenden Raum im passenden Zeitfenster (z.B. 2 Stunden) ab,
   um sie dem Gesundheitsamt zu übermitteln;
   siehe `Anwesenheitsdaten abrufen`.


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
   [Excel-Vorlage zur Raumübermittlung](!!!)
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
   - `contactemail`: Emailadresse einer Ansprechperson für Rückfragen 
     der Datenverwalter/in oder des Gesundheitsamts zur Raumsituation, z.B.
     `vorname.nachname@mi.fu-berlin.de`
2. Die Mitarbeiter/in schickt die Excel-Datei per Email an
   die Datenverwalter/in.
3. Die Datenverwalter/in prüft die Daten auf Plausibilität,
   liest die Datei in den Dienst ein
   und erhält einen Link zurück.
4. Die Datenverwalter/in öffnet diese Webseite.
   Sie enthält für jeden Sitzplatz einen QR-Code mit beschreibender Beschriftung
   wie es in der Excel-Datei deklariert war.
5. Die Datenverwalter/in druckt diese Webseite in eine PDF-Datei
   und schickt sie der Mitarbeiter/in per Email.  
6. Die Mitarbeiter/in druckt die QR-Codes aus und klebt jeden davon
   auf den entsprechenden Sitzplatz im entsprechenden Raum.  
   Der QR-Code muss vollständig mit mattem transparentem Klebeband
   bedeckt sein, damit er lange lesbar bleibt.

Varianten:

Schritt 3b: Ist die Datei fehlerhaft und lässt sich nicht einlesen,
korrigiert die Datenverwalter/in offensichtliche Fehler selbst
und klärt andernfalls die Korrekturen mit der Mitarbeiter/in.


## 1.4 Anwesenheitsdaten abrufen

Rollen:
Infiziertes Mitglied der Hochschule,
Mitarbeiter/in der Hochschuleinheit,
Datenverwalter/in

1. Ist ein Mitglied einer teilnehmenden Hochschule infiziert,
   so informiert er seine Hochschuleinheit(en) darüber,
   zu welchen Zeiten ersie sich in welchen Räumen aufgehalten hat
   oder beschreibt ersatzweise, in welchen Lehrveranstaltungen bei
   welchen Lehrpersonen an welchen Tagen.
2. Die Mitarbeiter/in der Hochschuleinheit, die bei der Datenverwalter/in
   als abrufberechtigt bekannt ist, übermittelt die Rauminformationen per
   Email an die Datenverwalterin und gibt dabei jeweils genau
   den gewünschten Zeitraum für den Abruf an, der sich aus den örtlichen
   Gegebenheiten der Raumnutzung ergibt.  
   Beispiel: 
   - Jemand infiziertes war in einer Lehrveranstaltung im Raum `X`, 
     die von "12-14 Uhr" stattfindet, 
     was an dieser Hochschule bedeutet: 12:15 Uhr bis 13:45 Uhr.
   - Ersie hatte sich um 12:11 Uhr registriert.
   - Die Mitarbeiter/in weiß aber, dass erstens der betreffende Raum `X`
     davor seit 9:45 leer war und zweitens schon ab 13:45 die Teilnehmenden der 
     nachfolgenden Lehrveranstaltung sich in dem Raum angemeldet haben
     könnten.
   - Sie bittet deshalb um einen Datenabruf für Raum `X`
     für den Zeitraum 9:40 Uhr bis 13:40 Uhr.
3. Die Datenverwalter/in ruft diese Daten ab und übermittelt
   sie an die Mitarbeiter/in.
4. Die Mitarbeiterin bereinigt ggf. die Daten wie folgt
   (Fortsetzung des Beispiels von oben):
   - Von den Personen in diesem Abruf, die sich vor der infizierten Person
     und vor 12:15 Uhr angemeldet hatten, haben plausiblerweise manche
     die infizierte Person gar nicht getroffen, weil sie den Raum vor
     Beginn der Lehrveranstaltung wieder verlassen haben.
   - Die Mitarbeiter/in zieht deshalb falls verfügbar eine allgemeine
     Teilnehmendenliste der Lehrveranstaltung heran und entfernt
     Personen, die im Datenabrauf auftauchen, aber nicht in der
     Lehrveranstaltung sind.
   - Oder sie fragt die vor 12:00 Uhr registrierten einzeln an,
     ob sie in dieser Lehrveranstaltung gewesen sind.
5. Die Mitarbeiter/in übermittelt die bereinigten Daten dem
   Gesundheitsamt.
   

# 2. Vor- und Nachteile

im Vergleich zu papierbasierter Erfassung der Anwesenheit

Vorteile:
- Zeitersparnis: 
  Die Erfassung geschieht mit viel weniger Zeitaufwand.
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
  Ein Einbruch in die Datenbank des Servers kann aus der Ferne
  erfolgen und betrifft mehr Daten als ein Diebstahl papierner
  Erfassungsbögen.
- Vollständigkeit:
  Der Erfassungsvorgang ist für die anderen Anwesenden weniger anschaulich
  und kann deshalb möglicherweise leichter vergessen werden. 
- Richtigkeit:
  Unsinnige Eingaben von Besuchern ("Donald Duck") sind kaum mehr 
  an Ort und Stelle zu entdecken.


# 3. Der/Die Datenverwalter/in

- Muss Englisch können (denn die Dialoge in diesem technischeren Bereich
  der Anwendung sind auf Englisch gehalten).
- Benötigt eine Einweisung (ca. 1 Stunde).
- Muss Mitglied einer teilnehmenden Hochschule sein.
  Alle anderen teilnehmenden Hochschulen müssen mit dieser Hochschule
  einen Auftragsdatenverarbeitungsvertrag schließen.
- Muss bei jeder Meldung von Räumen aus einer Hochschuleinheit klären,
  wer für diese Einheit berechtigt ist, Anwesenheitsdaten abzurufen,
  und dann den Datenzugang auf diesen Personenkreis beschränken.
   

# 4. Deployment and operation

This is technical information, therefore in English.

The application is meant to be deployed in many places
(to simplify the situation regarding privacy protection)
and allows some configuration to adopt to local needs.

## 4.1 Environment variables

- `DATA_CONTACT_EMAIL`: Email address of the Datenverwalter/in
- `DATA_RETENTION_DAYS`: Number of days after which an 
   attendance event record will be deleted.
- `IMPRINT_URL`: Web address of the Imprint/Impressum page
  that legally identifies the service's operator.
- `TECH_CONTACT_EMAIL`: Email address of the server operator.
- !!!

## 4.2 Deployment

t.b.d. !!!

## 4.3 Initiating operation

- Determine Datenverwalter/in and create account


# 5. Implementation status

The application is **not complete and not ready for use!**

The application is written in Python using the Django framework
and a PostgreSQL database. 
It is open-source (with an MIT license) in order to
provide maximal transparency.

- DONE 2020-10-06: Use case descriptions (will need update later)
- DONE 2020-10-08: Reading Excel files and creating master data
- TODO: Generating QR codes 
- TODO: Visitor input form and writing visit data
- TODO: Login for Datenverwalter/in
- TODO: Retrieving visit data
- TODO: Writing Excel file
- TODO: Automatic purging of visit data after retention time
- TODO: Pilot deployment
- TODO: Pilot testing
- TODO: Deployment
