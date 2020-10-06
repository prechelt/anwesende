# anwesende: Ein Dienst für Anwesenheitslisten für Hochschulen

Simple attendance registration for universities having pandemics.

Lutz Prechelt, 2020-10-05

**DE**: Eine sehr einfache Lösung für die Verfolgung von Infektionsketten,
die stark auf menschliche Urteilskraft und manuelle Schritte baut, 
um die Software einfach und den Gebrauch flexibel zu halten.

**EN**: A very simple application to help tracing infection chains 
at universities.
Makes heavy use of human judgment and manual operations 
to keep the software simple and its use flexible.  
Alas, the remainder of the documentation is available in German only (so far).


# 1. Anforderungsbeschreibung

## 1.1. Überblick

Rollen: 
Dienst `anwesende`, 
Teilnehmende Hochschule,
Besucher/in,
Datenverwalter/in

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
Dienst `anwesende`, 
Besucher/in ('ich') einer teilnehmenden Hochschule.

1. Ich komme in einen offenen Raum der teilnehmenden Hochschule.
   An meinem Sitzplatz klebt ein QR-Code. Ich scanne ihn mit meinem
   Smartphone und lande in meinem Webbrowser auf einer Seite mit
   ungefähr so einem Namen: https://a.nwesen.de/1234567890.
2. Der Dienst zeigt mir Datenschutzhinweise.
3. Ich gebe ein Vorname, Name, Mobilfunknummer, Email
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
   - Die Überschriftzeile keinesfalls ändern!
   - Jeder Raum bekommt eine Zeile.
   - Für alle Einträge genau die nachfolgenden Hinweise beachten:
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
   und erhält eine Webadresse!!! zurück.
4. Die Datenverwalter/in öffnet diese Webseite.
   Sie enthält einen QR-Code (mit beschreibender Beschriftung)
   für jeden Sitzplatz, der in der Excel-Datei deklariert war.
5. Die Datenverwalter/in druckt diese Webseite in eine PDF-Datei
   und schickt sie der Mitarbeiter/in per Email.  
   (Ggf. könnte sie statt dessen auch die Webadresse schicken).
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
   


