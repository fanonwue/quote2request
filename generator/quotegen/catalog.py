"""Product / service catalogs per vendor industry, plus units of measure.

Prices are net EUR per `price_unit` units (e.g. screws are priced per 100 pieces).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Final, Literal, NamedTuple, TypeAlias

from .schema import Industry, UnitKey

TaxRate: TypeAlias = Literal[7, 19]


class UnitDef(NamedTuple):
    code: str                       # UN/ECE Recommendation 20 code
    labels: tuple[str, str, str]    # label variants as printed; a vendor sticks to one index


UNITS: Final[Mapping[UnitKey, UnitDef]] = {
    "piece": UnitDef("H87", ("Stk.", "Stück", "St.")),
    "hour": UnitDef("HUR", ("Std.", "Stunde(n)", "h")),
    "meter": UnitDef("MTR", ("m", "lfm", "m")),
    "sqm": UnitDef("MTK", ("m²", "qm", "m2")),
    "cbm": UnitDef("MTQ", ("m³", "cbm", "m3")),
    "kg": UnitDef("KGM", ("kg", "kg", "kg")),
    "liter": UnitDef("LTR", ("l", "Liter", "ltr.")),
    "lump": UnitDef("LS", ("pauschal", "psch.", "pausch.")),
    "set": UnitDef("SET", ("Satz", "Set", "Satz")),
    "pack": UnitDef("PK", ("Pkg.", "Packung", "VE")),
    "carton": UnitDef("CT", ("Karton", "Krt.", "Ktn.")),
    "roll": UnitDef("RO", ("Rolle", "Rl.", "Rolle(n)")),
    "pair": UnitDef("PR", ("Paar", "Pa.", "Paar")),
    "month": UnitDef("MON", ("Monat", "Mon.", "Monat(e)")),
}

SERVICE_UNITS: Final[tuple[UnitKey, ...]] = ("hour", "lump", "month")


@dataclass(frozen=True)
class Item:
    desc: str                                   # may contain {var} placeholders
    unit: UnitKey
    price: tuple[float, float]                  # (min, max) net EUR per price_unit
    qty: tuple[float, float] = (1, 10)          # (min, max)
    step: str = "1"                             # quantity granularity, e.g. "0.25", "0.01", "100"
    tax: TaxRate = 19
    price_unit: int = 1
    vars: Mapping[str, Sequence[str | int]] = field(default_factory=dict)
    long: tuple[str, ...] = ()                  # candidate long texts (may use the same vars)
    qty_choices: tuple[int, ...] = ()           # if set, overrides qty/step


I: Final = Item  # short alias for the tables below

CATALOGS: Final[Mapping[Industry, tuple[Item, ...]]] = {
    "it": (
        I("Business-Notebook 14\" {cpu}, {ram} GB RAM, {ssd} GB SSD", "piece", (790, 1890), (1, 25),
          vars={"cpu": ["Intel Core Ultra 5", "Intel Core Ultra 7", "AMD Ryzen 7 PRO"], "ram": [16, 32], "ssd": [512, 1024]},
          long=("Betriebssystem Windows 11 Pro, Tastatur deutsch (QWERTZ)\ninkl. 3 Jahre Vor-Ort-Garantie",
                "inkl. USB-C-Netzteil 65 W, Fingerprint-Reader, Webcam mit Privacy Shutter")),
        I("Monitor {size}\" {res}, höhenverstellbar, USB-C", "piece", (149, 620), (1, 30),
          vars={"size": [24, 27, 32], "res": ["Full HD", "WQHD", "4K UHD"]}),
        I("USB-C Dockingstation, 100 W Power Delivery, 2x DisplayPort", "piece", (119, 289), (1, 25)),
        I("Headset {kind}", "piece", (39, 229), (1, 40),
          vars={"kind": ["Stereo, kabelgebunden USB-A", "Bluetooth mit aktiver Geräuschunterdrückung", "DECT, Mono"]}),
        I("Managed Switch {ports}-Port Gigabit PoE+, 4x SFP+", "piece", (279, 2490), (1, 6),
          vars={"ports": [8, 16, 24, 48]}),
        I("WLAN Access Point Wi-Fi {wifi}, Deckenmontage", "piece", (139, 690), (1, 20),
          vars={"wifi": ["6", "6E", "7"]}),
        I("Patchkabel Cat. 6A S/FTP, {len} m, {color}", "piece", (2, 15), (10, 200), step="10",
          vars={"len": ["0,5", "1", "2", "3", "5"], "color": ["grau", "blau", "gelb", "rot"]}),
        I("Netzwerkspeicher (NAS) {bays}-Bay inkl. {tb} TB Festplatten", "piece", (690, 4800), (1, 2),
          vars={"bays": [2, 4, 8], "tb": [8, 16, 32, 64]}),
        I("USV {va} VA Line-Interactive, 19\" Rackmontage 2 HE", "piece", (379, 1890), (1, 3),
          vars={"va": [1000, 1500, 2200, 3000]}),
        I("Serverschrank 19\" {he} HE, 800 x 1000 mm, Glastür", "piece", (790, 2390), (1, 2),
          vars={"he": [24, 32, 42, 47]}),
        I("Managed-Service-Pauschale je Arbeitsplatz (Monitoring, Patchmanagement)", "month", (12, 39),
          qty_choices=(12, 24, 36),
          long=("Mindestvertragslaufzeit 12 Monate, Abrechnung monatlich im Voraus.",)),
        I("Einrichtung und Konfiguration Arbeitsplatz-PC", "hour", (85, 145), (1, 40), step="0.25"),
        I("Technikerstunde vor Ort", "hour", (89, 155), (1, 24), step="0.5"),
        I("Anfahrtspauschale", "lump", (35, 95), (1, 1)),
        I("Projektierung und Dokumentation Netzwerkinfrastruktur", "lump", (450, 3500), (1, 1),
          long=("Bestandsaufnahme vor Ort, Erstellung Netzwerkplan, VLAN-Konzept und Übergabedokumentation.",)),
        I("Altgeräteentsorgung inkl. zertifizierter Datenlöschung", "piece", (15, 45), (1, 50)),
    ),
    "industrial": (
        I("Sechskantschraube DIN 933 M{d} x {l} mm, 8.8, galv. verzinkt", "piece", (4, 38), (100, 5000), step="100",
          price_unit=100, vars={"d": [6, 8, 10, 12, 16], "l": [16, 20, 25, 30, 40, 50, 60]}),
        I("Sechskantmutter DIN 934 M{d}, Festigkeitsklasse 8, galv. verzinkt", "piece", (2, 18), (100, 5000), step="100",
          price_unit=100, vars={"d": [6, 8, 10, 12, 16]}),
        I("Scheibe DIN 125 A {d}, Edelstahl A2", "piece", (3, 20), (100, 5000), step="100",
          price_unit=100, vars={"d": ["6,4", "8,4", "10,5", "13", "17"]}),
        I("Zylinderschraube DIN 912 M{d} x {l} mm, Edelstahl A4", "piece", (12, 95), (100, 2000), step="100",
          price_unit=100, vars={"d": [4, 5, 6, 8, 10], "l": [12, 16, 20, 25, 30]}),
        I("Rillenkugellager {code}-2RS, beidseitig abgedichtet", "piece", (3.5, 48), (2, 100),
          vars={"code": [6202, 6204, 6205, 6206, 6305]}),
        I("Hydraulikschlauch 2SN DN {dn}, Meterware", "meter", (9, 42), (5, 100), step="0.5",
          vars={"dn": [6, 8, 10, 12, 16]}),
        I("Druckluftschlauch PU {dim} mm, blau, Rolle 50 m", "roll", (28, 95), (1, 20),
          vars={"dim": ["6 x 4", "8 x 6", "10 x 8", "12 x 9"]}),
        I("Schutzhandschuhe Nitril beschichtet, Größe {size}, EN 388", "pair", (1.8, 7.5), (12, 480), step="12",
          vars={"size": [8, 9, 10, 11]}),
        I("MAG-Schweißdraht G3Si1, Ø {d} mm, Spule 15 kg", "kg", (2.4, 5.8), (15, 300), step="15",
          vars={"d": ["0,8", "1,0", "1,2"]}),
        I("Kühlschmierstoff wassermischbar, Kanister 20 l", "liter", (4.5, 12), (20, 400), step="20"),
        I("Rundstahl S235JR blank, Ø {d} mm, Abrechnung nach Gewicht", "kg", (1.4, 3.2), (10, 800), step="0.1",
          vars={"d": [10, 16, 20, 30, 40, 50]}),
        I("Aluminium-Konstruktionsprofil 40 x 40 Nut 8, Zuschnitt {len} mm", "piece", (6, 28), (2, 80),
          vars={"len": [250, 500, 750, 1000, 1500]}),
        I("Ratschenspanngurt 2-teilig, 50 mm, LC 2500 daN, 8 m", "piece", (9, 24), (4, 100)),
        I("Sägeschnitt / Zuschnittservice", "piece", (1.5, 4.5), (2, 120)),
        I("Mindermengenzuschlag", "lump", (15, 35), (1, 1)),
    ),
    "construction": (
        I("Baustelleneinrichtung", "lump", (250, 1800), (1, 1),
          long=("Einrichten, Vorhalten und Räumen der Baustelle einschl. aller erforderlichen Geräte, "
                "Werkzeuge und Sanitäreinrichtungen.",)),
        I("Abdeckarbeiten", "sqm", (1.8, 4.5), (20, 600), step="0.01",
          long=("Böden und Einrichtungsgegenstände mit Folie und Malervlies abdecken, "
                "nach Abschluss der Arbeiten entfernen und entsorgen.",)),
        I("Wandflächen spachteln, Qualitätsstufe Q{q}", "sqm", (4.5, 14), (10, 400), step="0.01",
          vars={"q": [2, 3, 4]},
          long=("Gipskartonflächen vollflächig spachteln und schleifen gemäß Merkblatt Nr. 2 "
                "des Bundesverbandes der Gipsindustrie, Qualitätsstufe Q{q}.",)),
        I("Dispersionsanstrich Wände und Decken, 2-fach", "sqm", (5.8, 12.5), (20, 900), step="0.01",
          vars={"color": ["weiß", "RAL 9010", "RAL 9016", "nach Bemusterung"]},
          long=("Untergrund prüfen, Grundierung auftragen, Zwischen- und Schlussanstrich mit "
                "Dispersionsfarbe Nassabriebklasse 2, Farbton {color}.",)),
        I("Gipskarton-Ständerwand CW/UW {w}, beidseitig {lay}-lagig beplankt", "sqm", (48, 110), (5, 250), step="0.01",
          vars={"w": [50, 75, 100], "lay": [1, 2]},
          long=("Metallständerwand nach DIN 18183, Beplankung GKB 12,5 mm, Hohlraumdämmung "
                "Mineralwolle 40 mm, Wandhöhe bis 3,00 m.",)),
        I("Abgehängte Decke, Gipskarton auf Metallunterkonstruktion", "sqm", (45, 85), (5, 300), step="0.01"),
        I("Bodenfliesen {f} cm verlegen, Dünnbettverfahren", "sqm", (38, 75), (5, 250), step="0.01",
          vars={"f": ["30 x 60", "60 x 60", "60 x 120"]},
          long=("Untergrund vorbereiten, Fliesen im Dünnbett verlegen, verfugen mit zementärem "
                "Fugenmörtel, Fugenfarbe nach Wahl des AG.",)),
        I("Fliesenmaterial lt. Bemusterung", "sqm", (25, 85), (5, 260), step="0.01"),
        I("Sockelleisten liefern und montieren", "meter", (9, 24), (10, 300), step="0.01"),
        I("Wärmedämmung Mineralwolle WLS 035, {t} mm", "sqm", (9, 28), (10, 600), step="0.01",
          vars={"t": [60, 80, 100, 120, 140]}),
        I("Bauschutt laden und entsorgen inkl. Deponiegebühren", "cbm", (45, 120), (1, 40), step="0.5"),
        I("Fassadengerüst stellen, 4 Wochen vorhalten und abbauen", "sqm", (8, 16), (50, 800), step="0.01"),
        I("Silikonfuge erneuern", "meter", (6, 14), (5, 120), step="0.1"),
        I("Facharbeiterstunde", "hour", (52, 72), (2, 120), step="0.5"),
        I("Helferstunde", "hour", (38, 52), (2, 120), step="0.5"),
    ),
    "office": (
        I("Kopierpapier A4, 80 g/m², weiß, Karton à 5 x 500 Blatt", "carton", (18, 32), (1, 80)),
        I("Ordner A4, Rückenbreite {w} mm, {color}", "piece", (1.9, 4.8), (5, 200), step="5",
          vars={"w": [50, 80], "color": ["blau", "schwarz", "rot", "grau"]}),
        I("Kugelschreiber mit Druckmechanik, blau, VE 10 Stück", "pack", (3.5, 14), (1, 50)),
        I("Haftnotizen 76 x 76 mm, gelb, 12 Blöcke à 100 Blatt", "pack", (6, 16), (1, 40)),
        I("Toner {color} für Laserdrucker, Reichweite ca. {pages} Seiten", "piece", (45, 189), (1, 20),
          vars={"color": ["schwarz", "cyan", "magenta", "gelb"], "pages": ["3.000", "5.000", "9.000"]}),
        I("Bürodrehstuhl mit Synchronmechanik und Lordosenstütze", "piece", (189, 690), (1, 30),
          vars={"color": ["anthrazit", "blau", "schwarz"]},
          long=("Sitzhöhe und Sitztiefe verstellbar, 3D-Armlehnen, Bezug Stoff {color}.",)),
        I("Schreibtisch elektrisch höhenverstellbar, {size} cm", "piece", (390, 980), (1, 30),
          vars={"size": ["140 x 80", "160 x 80", "180 x 80"]}),
        I("Rollcontainer mit 3 Schubladen, abschließbar", "piece", (139, 320), (1, 30)),
        I("Kaffee ganze Bohne, Packung 1 kg", "piece", (12.9, 24.9), (1, 40), tax=7),
        I("Fachbuch \"{title}\"", "piece", (24, 89), (1, 10), tax=7,
          vars={"title": ["Arbeitsrecht für die Praxis", "Handbuch Projektmanagement",
                          "Einführung in die Kostenrechnung", "Technisches Zeichnen kompakt"]}),
        I("Fachzeitschrift, Jahresabonnement", "piece", (89, 320), (1, 5), tax=7),
        I("Mineralwasser, Kasten 12 x 0,75 l", "piece", (6, 11), (2, 60)),
        I("Aktenvernichter Sicherheitsstufe P-4", "piece", (120, 480), (1, 5)),
        I("Lieferung und Montage Büromöbel", "hour", (45, 75), (1, 40), step="0.5"),
    ),
    "electrical": (
        I("Mantelleitung NYM-J {c} x {q} mm², grau", "meter", (45, 290), (50, 1000), step="50",
          price_unit=100, vars={"c": [3, 5], "q": ["1,5", "2,5"]}),
        I("Schutzkontakt-Steckdose 1-fach, reinweiß", "piece", (3.9, 12), (5, 120)),
        I("Lichtschalter Aus-/Wechselschaltung, reinweiß", "piece", (4.5, 14), (5, 80)),
        I("LED-Panel 62 x 62 cm, {lm} lm, {k} K, UGR < 19", "piece", (38, 140), (2, 120),
          vars={"lm": [3400, 4000, 4800], "k": [3000, 4000]}),
        I("Leitungsschutzschalter B{a}, 1-polig, 6 kA", "piece", (3.8, 12), (3, 60),
          vars={"a": [10, 13, 16, 20]}),
        I("Fehlerstrom-Schutzschalter 40 A / 30 mA, 4-polig, Typ A", "piece", (28, 95), (1, 12)),
        I("Unterverteilung {rows}-reihig, Aufputz, IP 65", "piece", (180, 890), (1, 4),
          vars={"rows": [2, 3, 4]}),
        I("Kabelkanal PVC 40 x 60 mm, reinweiß, inkl. Montage", "meter", (8, 22), (5, 200), step="0.5"),
        I("Elektroinstallation Gesellenstunde", "hour", (58, 78), (2, 160), step="0.5"),
        I("Elektroinstallation Meisterstunde", "hour", (72, 95), (1, 40), step="0.5"),
        I("Prüfung ortsveränderlicher Geräte nach DGUV Vorschrift 3", "piece", (3.5, 9), (20, 500),
          long=("inkl. Sichtprüfung, Messung, Prüfplakette und Prüfprotokoll je Gerät.",)),
        I("Erdungs- und Potentialausgleichsarbeiten", "lump", (180, 900), (1, 1)),
        I("Wallbox 11 kW inkl. Montage und Inbetriebnahme", "piece", (890, 1890), (1, 10),
          long=("Leitungslänge bis 15 m inklusive, Anmeldung beim Netzbetreiber.",)),
        I("Kleinmaterial (Dübel, Schrauben, Klemmen)", "lump", (25, 180), (1, 1)),
    ),
    "facility": (
        I("Unterhaltsreinigung Büroflächen gemäß Leistungsverzeichnis, {freq} x wöchentlich", "month", (380, 4200),
          qty_choices=(1, 6, 12, 24), vars={"freq": [1, 2, 3, 5]},
          long=("Reinigung von Arbeitsplätzen, Sanitärbereichen, Teeküchen und Verkehrsflächen "
                "gemäß beigefügtem Leistungsverzeichnis.",)),
        I("Glasreinigung Fensterflächen innen und außen", "sqm", (1.2, 3.8), (50, 2000), step="0.01"),
        I("Grundreinigung Bodenbelag inkl. Neueinpflege", "sqm", (2.5, 7.5), (50, 1500), step="0.01"),
        I("Teppichreinigung im Sprühextraktionsverfahren", "sqm", (2.8, 6.5), (20, 900), step="0.01"),
        I("Sonderreinigung nach Aufwand", "hour", (29, 45), (2, 60), step="0.5"),
        I("Sanitärverbrauchsmaterial (Seife, Papierhandtücher, Toilettenpapier)", "month", (45, 480),
          qty_choices=(1, 6, 12)),
        I("Winterdienst Saison 01.11. bis 31.03., Räum- und Streupflicht", "lump", (450, 3800), (1, 1)),
        I("Bauendreinigung", "sqm", (3.5, 8), (50, 1500), step="0.01"),
        I("Hausmeisterdienst", "hour", (32, 49), (4, 160), step="0.5"),
        I("Allzweckreiniger, Kanister 10 l", "piece", (18, 45), (1, 20)),
    ),
    "packaging": (
        I("Faltkarton 1-wellig, {dim} mm, braun", "piece", (35, 180), (100, 5000), step="100",
          price_unit=100, vars={"dim": ["305 x 215 x 140", "400 x 300 x 200", "600 x 400 x 400"]}),
        I("Stretchfolie Handrolle, 23 µm, 500 mm x 300 m, transparent", "roll", (6.5, 14), (6, 216), step="6"),
        I("Packband PP, 50 mm x 66 m, {color}, leise abrollend", "roll", (1.2, 3.9), (36, 720), step="36",
          vars={"color": ["braun", "transparent", "bedruckt \"Vorsicht Glas\""]}),
        I("Luftpolsterfolie 100 cm x 100 m, 2-lagig", "roll", (22, 49), (1, 30)),
        I("Europalette EPAL 1200 x 800 mm, neu", "piece", (14, 28), (10, 200), step="10"),
        I("Gitterbox-Palette, gebraucht, Klasse A", "piece", (75, 160), (1, 40)),
        I("Füllmaterial Papierpolster, Box 500 m", "carton", (29, 58), (1, 40)),
        I("Versandtasche Kraftpapier {size}, VE 250 Stück", "pack", (19, 65), (1, 40),
          vars={"size": ["C5", "C4", "B4"]}),
        I("Kantenschutzwinkel 35 x 35 x 3 mm, Länge 1.000 mm", "piece", (25, 60), (100, 2000), step="100",
          price_unit=100),
        I("Umreifungsband PET 12 x 0,6 mm, Rolle 2.500 m", "roll", (28, 55), (1, 24)),
        I("Versandetiketten 100 x 150 mm, Thermodirekt, Rolle à 1.000 Stück", "roll", (9, 24), (1, 50)),
        I("Druckvorlage / Klischee einmalig", "lump", (120, 450), (1, 1)),
    ),
}

INDUSTRY_NAME_WORDS: Final[Mapping[Industry, tuple[str, ...]]] = {
    "it": ("IT-Systemhaus", "IT-Services", "Computer", "Datentechnik", "Netzwerktechnik", "IT-Solutions"),
    "industrial": ("Industriebedarf", "Technischer Handel", "Industrietechnik", "Befestigungstechnik", "Werkzeughandel"),
    "construction": ("Bau", "Malerbetrieb", "Trockenbau", "Ausbau", "Innenausbau", "Bauunternehmung"),
    "office": ("Bürobedarf", "Büroeinrichtung", "Bürowelt", "Papier & Büro", "Office Supplies"),
    "electrical": ("Elektrotechnik", "Elektro", "Elektroinstallation", "Gebäudetechnik"),
    "facility": ("Gebäudereinigung", "Facility Services", "Gebäudeservice", "Reinigungsdienste"),
    "packaging": ("Verpackung", "Verpackungstechnik", "Packmittel", "Logistikbedarf"),
}

SUBJECTS: Final[Mapping[Industry, tuple[str | None, ...]]] = {
    "it": ("IT-Ausstattung Arbeitsplätze", "Erneuerung Netzwerkinfrastruktur", "Hardwarebeschaffung {year}",
           "Ausstattung Homeoffice-Arbeitsplätze", "Modernisierung Serverraum", None),
    "industrial": ("Ersatzteile Instandhaltung", "Verbrauchsmaterial Fertigung", "Rahmenbedarf {year}",
                   "Normteile laut Anfrage", None),
    "construction": ("Malerarbeiten BV {site}", "Trockenbauarbeiten BV {site}", "Fliesenarbeiten BV {site}",
                     "Sanierung Büroetage, {site}", "Innenausbau BV {site}"),
    "office": ("Büromaterial Quartalsbedarf", "Büroeinrichtung neue Arbeitsplätze", "Bürobedarf {year}", None),
    "electrical": ("Elektroinstallation BV {site}", "Beleuchtungssanierung {site}", "DGUV V3 Prüfung {year}",
                   "Erweiterung Unterverteilung", "Ladeinfrastruktur Mitarbeiterparkplatz"),
    "facility": ("Gebäudereinigung {site}", "Unterhaltsreinigung ab {year}", "Glas- und Sonderreinigung",
                 "Hausmeister- und Winterdienst {year}"),
    "packaging": ("Verpackungsmaterial Versand", "Packmittel Rahmenbedarf {year}", "Palettierung und Ladungssicherung", None),
}

# Industries whose quotes are services delivered on site (site address, no freight).
SITE_INDUSTRIES: Final[tuple[Industry, ...]] = ("construction", "electrical", "facility")
