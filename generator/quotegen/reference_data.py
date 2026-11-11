"""Static reference data (names, places, company name parts).

All collections are tuples or read-only mappings (never sets) so iteration order is fixed.
"""

from collections.abc import Mapping
from typing import Final, NamedTuple

from .schema import Industry, RegisterType


class City(NamedTuple):
    name: str
    postal_code: str
    area_code: str  # phone area code incl. leading 0


class LegalForm(NamedTuple):
    name: str
    weight: int
    register_type: RegisterType


CITIES: Final[tuple[City, ...]] = (
    City("Berlin", "10115", "030"),
    City("Hamburg", "20095", "040"),
    City("München", "80331", "089"),
    City("Köln", "50667", "0221"),
    City("Frankfurt am Main", "60311", "069"),
    City("Stuttgart", "70173", "0711"),
    City("Düsseldorf", "40213", "0211"),
    City("Leipzig", "04109", "0341"),
    City("Dortmund", "44135", "0231"),
    City("Essen", "45127", "0201"),
    City("Bremen", "28195", "0421"),
    City("Dresden", "01067", "0351"),
    City("Hannover", "30159", "0511"),
    City("Nürnberg", "90402", "0911"),
    City("Duisburg", "47051", "0203"),
    City("Bochum", "44787", "0234"),
    City("Wuppertal", "42103", "0202"),
    City("Bielefeld", "33602", "0521"),
    City("Bonn", "53111", "0228"),
    City("Münster", "48143", "0251"),
    City("Mannheim", "68159", "0621"),
    City("Karlsruhe", "76133", "0721"),
    City("Augsburg", "86150", "0821"),
    City("Wiesbaden", "65183", "0611"),
    City("Mönchengladbach", "41061", "02161"),
    City("Aachen", "52062", "0241"),
    City("Braunschweig", "38100", "0531"),
    City("Kiel", "24103", "0431"),
    City("Chemnitz", "09111", "0371"),
    City("Halle (Saale)", "06108", "0345"),
    City("Magdeburg", "39104", "0391"),
    City("Freiburg im Breisgau", "79098", "0761"),
    City("Krefeld", "47798", "02151"),
    City("Mainz", "55116", "06131"),
    City("Lübeck", "23552", "0451"),
    City("Erfurt", "99084", "0361"),
    City("Rostock", "18055", "0381"),
    City("Kassel", "34117", "0561"),
    City("Saarbrücken", "66111", "0681"),
    City("Potsdam", "14467", "0331"),
    City("Ulm", "89073", "0731"),
    City("Regensburg", "93047", "0941"),
    City("Ingolstadt", "85049", "0841"),
    City("Würzburg", "97070", "0931"),
    City("Heilbronn", "74072", "07131"),
    City("Wolfsburg", "38440", "05361"),
    City("Göttingen", "37073", "0551"),
    City("Paderborn", "33098", "05251"),
    City("Osnabrück", "49074", "0541"),
    City("Oldenburg", "26122", "0441"),
    City("Darmstadt", "64283", "06151"),
    City("Jena", "07743", "03641"),
    City("Trier", "54290", "0651"),
    City("Siegen", "57072", "0271"),
    City("Gütersloh", "33330", "05241"),
    City("Reutlingen", "72764", "07121"),
    City("Pforzheim", "75175", "07231"),
    City("Bamberg", "96047", "0951"),
    City("Passau", "94032", "0851"),
    City("Rosenheim", "83022", "08031"),
    City("Kempten (Allgäu)", "87435", "0831"),
    City("Schweinfurt", "97421", "09721"),
    City("Lüneburg", "21335", "04131"),
    City("Flensburg", "24937", "0461"),
    City("Konstanz", "78462", "07531"),
)

# Register courts that differ from the city name.
REGISTER_COURT_OVERRIDES: Final[Mapping[str, str]] = {
    "Berlin": "Amtsgericht Charlottenburg",
}

STREETS: Final[tuple[str, ...]] = (
    "Hauptstraße", "Bahnhofstraße", "Gartenstraße", "Schulstraße", "Bergstraße",
    "Lindenstraße", "Kirchstraße", "Waldstraße", "Ringstraße", "Industriestraße",
    "Gewerbestraße", "Am Gewerbepark", "Im Technologiepark", "Carl-Benz-Straße",
    "Robert-Bosch-Straße", "Max-Planck-Straße", "Gutenbergstraße", "Industriering",
    "Siemensstraße", "Daimlerstraße", "Otto-Hahn-Straße", "Kantstraße",
    "Goethestraße", "Schillerstraße", "Mozartstraße", "Beethovenstraße",
    "Friedrich-Ebert-Straße", "Konrad-Adenauer-Allee", "Rosenweg", "Birkenweg",
    "Ahornweg", "Eichenallee", "Mühlenweg", "Am Markt", "Marktplatz", "Lange Reihe",
    "Hafenstraße", "Feldstraße", "Wiesenweg", "Rheinallee", "Kaiserstraße",
    "Leipziger Straße", "Münchner Straße", "Frankfurter Ring", "Werkstraße",
    "Fabrikstraße", "Kanalstraße", "Brückenstraße", "Talstraße", "Sonnenstraße",
    "Uferstraße", "Steinweg", "Weidenkamp", "An der Autobahn", "Zum Handwerkerhof",
    "Albert-Einstein-Ring", "Rudolf-Diesel-Straße", "Heinrich-Hertz-Straße",
    "Am Alten Güterbahnhof", "Neue Straße", "Alte Landstraße", "Dieselstraße",
)

FIRST_NAMES_MALE: Final[tuple[str, ...]] = (
    "Alexander", "Andreas", "Benjamin", "Björn", "Christian", "Daniel", "David",
    "Dennis", "Dirk", "Elias", "Felix", "Florian", "Frank", "Jan", "Jens", "Jörg",
    "Jürgen", "Kai", "Klaus", "Lukas", "Marc", "Markus", "Martin", "Matthias",
    "Michael", "Niklas", "Oliver", "Patrick", "Peter", "Ralf", "René", "Sebastian",
    "Stefan", "Sven", "Thomas", "Tim", "Tobias", "Uwe", "Wolfgang", "Mehmet",
    "Emre", "Piotr", "Luca", "Ahmet", "Nikolai", "Hans-Peter", "Karl-Heinz",
)

FIRST_NAMES_FEMALE: Final[tuple[str, ...]] = (
    "Andrea", "Anja", "Anna", "Birgit", "Carina", "Christina", "Claudia", "Daniela",
    "Elena", "Franziska", "Gabriele", "Hannah", "Ines", "Jana", "Jasmin", "Julia",
    "Katharina", "Kerstin", "Laura", "Lea", "Lena", "Lisa", "Maria", "Marie",
    "Melanie", "Monika", "Nadine", "Nicole", "Petra", "Sabine", "Sandra", "Sarah",
    "Silke", "Simone", "Sophie", "Stefanie", "Susanne", "Tanja", "Ursula", "Vanessa",
    "Zeynep", "Agnieszka", "Ayşe", "Chiara", "Natalia", "Anne-Kathrin",
)

SURNAMES: Final[tuple[str, ...]] = (
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
    "Schulz", "Hoffmann", "Schäfer", "Koch", "Bauer", "Richter", "Klein", "Wolf",
    "Schröder", "Neumann", "Schwarz", "Zimmermann", "Braun", "Krüger", "Hofmann",
    "Hartmann", "Lange", "Schmitt", "Werner", "Schmitz", "Krause", "Meier", "Lehmann",
    "Schmid", "Schulze", "Maier", "Köhler", "Herrmann", "König", "Walter", "Mayer",
    "Huber", "Kaiser", "Fuchs", "Peters", "Lang", "Scholz", "Möller", "Weiß", "Jung",
    "Hahn", "Schubert", "Vogel", "Friedrich", "Keller", "Günther", "Frank", "Berger",
    "Winkler", "Roth", "Beck", "Lorenz", "Baumann", "Franke", "Albrecht", "Schuster",
    "Simon", "Ludwig", "Böhm", "Winter", "Kraus", "Martin", "Schumacher", "Krämer",
    "Vogt", "Stein", "Jäger", "Otto", "Sommer", "Groß", "Seidel", "Heinrich",
    "Brandt", "Haas", "Schreiber", "Graf", "Dietrich", "Ziegler", "Kuhn", "Kühn",
    "Pohl", "Engel", "Horn", "Busch", "Bergmann", "Voigt", "Sauer", "Arnold",
    "Wolff", "Pfeiffer", "Yılmaz", "Kaya", "Nowak", "Kowalski", "Popescu", "Nguyen",
    "Rossi", "Petrović", "Ivanov", "Demir", "von Bergen", "Meyer-Lindemann",
)

# (title, weight)
PERSON_TITLES: Final[tuple[tuple[str | None, int], ...]] = (
    (None, 90), ("Dr.", 6), ("Dipl.-Ing.", 3), ("Prof. Dr.", 1),
)

COMPANY_PREFIXES: Final[tuple[str, ...]] = (
    "Nord", "Süd", "West", "Ost", "Rhein", "Elb", "Alpen", "Main", "Isar", "Spree",
    "Weser", "Hansa", "Prima", "Delta", "Proto", "Opti", "Tekno", "Vita", "Kon",
    "Inno", "Uni", "Multi", "Pro", "Euro", "Terra", "Aqua", "Lumo", "Sigma",
)
COMPANY_SUFFIXES: Final[tuple[str, ...]] = (
    "tec", "werk", "tronic", "form", "plan", "line", "data", "logic", "max",
    "con", "sys", "nova", "point", "flex", "pack", "bau", "star", "mark",
)

LEGAL_FORMS: Final[tuple[LegalForm, ...]] = (
    LegalForm("GmbH", 45, "HRB"),
    LegalForm("GmbH & Co. KG", 15, "HRA"),
    LegalForm("AG", 5, "HRB"),
    LegalForm("e.K.", 10, "HRA"),
    LegalForm("KG", 5, "HRA"),
    LegalForm("UG (haftungsbeschränkt)", 8, "HRB"),
    LegalForm("OHG", 4, "HRA"),
)

MANAGEMENT_TITLES: Final[Mapping[str, str]] = {
    "GmbH": "Geschäftsführer",
    "GmbH & Co. KG": "Geschäftsführer",
    "UG (haftungsbeschränkt)": "Geschäftsführer",
    "AG": "Vorstand",
    "e.K.": "Inhaber",
    "KG": "Persönlich haftender Gesellschafter",
    "OHG": "Gesellschafter",
}

CUSTOMER_INDUSTRY_WORDS: Final[tuple[str, ...]] = (
    "Maschinenbau", "Logistik", "Automotive", "Kunststofftechnik", "Lebensmittel",
    "Immobilien", "Hausverwaltung", "Metallbau", "Medizintechnik", "Software",
    "Spedition", "Druckerei", "Möbelwerk", "Energietechnik", "Feinmechanik",
    "Holding", "Handelsgesellschaft", "Anlagenbau", "Elektronik", "Textil",
)

CUSTOMER_DEPARTMENTS: Final[tuple[str, ...]] = (
    "Einkauf", "Zentraler Einkauf", "Technischer Einkauf", "Facility Management",
    "IT-Abteilung", "Verwaltung", "Materialwirtschaft", "Instandhaltung",
)

DELIVERY_ADDRESS_LINES: Final[tuple[str, ...]] = ("Wareneingang Tor {n}", "Lager {n}", "Werk {n}", "Halle {n}")

SALES_ROLES_DEFAULT: Final[tuple[str, ...]] = (
    "Vertrieb Innendienst", "Kundenberatung", "Key Account Manager", "Verkauf",
    "Technischer Vertrieb", "Teamleitung Vertrieb", "Auftragsbearbeitung",
)
SALES_ROLES_BY_INDUSTRY: Final[Mapping[Industry, tuple[str, ...]]] = {
    "construction": ("Bauleitung", "Projektleitung", "Kalkulation"),
    "electrical": ("Projektleitung", "Kalkulation", "Kundendienst"),
    "facility": ("Objektleitung", "Vertrieb", "Kundenbetreuung", "Niederlassungsleitung"),
}

CUSTOMER_ROLES: Final[tuple[str | None, ...]] = (
    "Einkäufer", "Leitung Einkauf", "Projektleitung", "Facility Manager",
    "IT-Leitung", "Assistenz der Geschäftsführung", "Office Management",
    "Technische Leitung", None,
)

BANK_NAMES: Final[tuple[str, ...]] = (
    "Sparkasse {city}", "Volksbank {city} eG", "Commerzbank", "Deutsche Bank",
    "Postbank", "Raiffeisenbank {city} eG", "HypoVereinsbank", "Sparda-Bank",
    "GLS Bank", "Targobank",
)

MOBILE_PREFIXES: Final[tuple[str, ...]] = (
    "151", "152", "157", "160", "162", "170", "171", "172", "175", "176", "177", "178", "179",
)
