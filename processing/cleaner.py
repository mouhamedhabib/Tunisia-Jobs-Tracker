import sqlite3
import pandas as pd
import os
import re
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "./data/jobs.db")

# Mapping of 24 Tunisian governorates - all variants to standard name
CITY_NORMALIZATION = {
    # Tunis
    "tunis": "Tunis", "تونس": "Tunis", "tunis centre ville": "Tunis",
    "centre ville": "Tunis", "montplaisir": "Tunis", "montplaisir tunis": "Tunis",
    "lafayette": "Tunis", "lac 2": "Tunis", "lac 2 tunis": "Tunis",
    "les berges du lac": "Tunis", "centre urbain nord": "Tunis",
    "cite el khadra": "Tunis", "cité el khadra": "Tunis",
    "el menzah": "Tunis", "el omrane": "Tunis", "bardo": "Tunis",
    "grand-tunis": "Tunis", "grand tunis": "Tunis",

    # Ariana
    "ariana": "Ariana", "أريانة": "Ariana", "cite ennasr": "Ariana",
    "cité ennasr": "Ariana", "technopark el ghazala": "Ariana",
    "el ghazala": "Ariana", "raoued": "Ariana", "la soukra": "Ariana",

    # Ben Arous
    "ben arous": "Ben Arous", "بن عروس": "Ben Arous",
    "megrine": "Ben Arous", "mégrine": "Ben Arous",
    "el mourouj": "Ben Arous", "el mourouj 1": "Ben Arous",
    "rades": "Ben Arous", "radès": "Ben Arous",
    "zone industrielle sidi daoud la marsa": "Ben Arous",
    "hammam lif": "Ben Arous", "hammam-lif": "Ben Arous",
    "ezzahra": "Ben Arous", "fouchana": "Ben Arous",
    "mohamedia": "Ben Arous", "new gabes": "Ben Arous",

    # Manouba
    "manouba": "Manouba", "la manouba": "Manouba", "منوبة": "Manouba",
    "mannouba": "Manouba", "oued ellil": "Manouba",
    "douar hicher": "Manouba", "tebourba": "Manouba",

    # Nabeul
    "nabeul": "Nabeul", "نابل": "Nabeul", "hammamet": "Nabeul",
    "kelibia": "Nabeul", "grombalia": "Nabeul", "menzel temime": "Nabeul",

    # Zaghouan
    "zaghouan": "Zaghouan", "زغوان": "Zaghouan",

    # Bizerte
    "bizerte": "Bizerte", "بنزرت": "Bizerte", "menzel bourguiba": "Bizerte",
    "mateur": "Bizerte",

    # Beja
    "beja": "Beja", "béja": "Beja", "باجة": "Beja",

    # Jendouba
    "jendouba": "Jendouba", "جندوبة": "Jendouba",

    # Kef
    "kef": "Kef", "le kef": "Kef", "الكاف": "Kef",

    # Siliana
    "siliana": "Siliana", "سليانة": "Siliana",

    # Sousse
    "sousse": "Sousse", "سوسة": "Sousse", "سوسة‎": "Sousse",
    "gouvernorat de sousse": "Sousse", "hammam sousse": "Sousse",
    "sahloul": "Sousse", "khzema": "Sousse", "khzema ouest": "Sousse",
    "chott meriem": "Sousse",

    # Monastir
    "monastir": "Monastir", "المنستير": "Monastir",
    "moknine": "Monastir", "ksar hellal": "Monastir",

    # Mahdia
    "mahdia": "Mahdia", "المهدية": "Mahdia",

    # Sfax
    "sfax": "Sfax", "صفاقس": "Sfax", "sfax ville": "Sfax",
    "sakiet ezzit": "Sfax", "sakiet eddaier": "Sfax",

    # Kairouan
    "kairouan": "Kairouan", "القيروان": "Kairouan",

    # Kasserine
    "kasserine": "Kasserine", "القصرين": "Kasserine",

    # Sidi Bouzid
    "sidi bouzid": "Sidi Bouzid", "سيدي بوزيد": "Sidi Bouzid",

    # Gabes
    "gabes": "Gabes", "gabès": "Gabes", "قابس": "Gabes",

    # Medenine
    "medenine": "Medenine", "médenine": "Medenine", "مدنين": "Medenine",
    "zarzis": "Medenine", "djerba": "Medenine",

    # Tataouine
    "tataouine": "Tataouine", "تطاوين": "Tataouine",

    # Kebili
    "kebili": "Kebili", "kébili": "Kebili", "قبلي": "Kebili",

    # Tozeur
    "tozeur": "Tozeur", "توزر": "Tozeur",

    # Gafsa
    "gafsa": "Gafsa", "قفصة": "Gafsa",
}

VALID_GOVERNORATES = set(CITY_NORMALIZATION.values())


def normalize_city(raw: str) -> str | None:
    """
    Normalize a raw city string to one of the 24 Tunisian governorates.
    Returns None if city cannot be mapped.
    """
    if not raw or not isinstance(raw, str):
        return None

    # Clean: lowercase, strip whitespace and invisible chars
    cleaned = raw.lower().strip()
    cleaned = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Direct match
    if cleaned in CITY_NORMALIZATION:
        return CITY_NORMALIZATION[cleaned]

    # Partial match — check if any key is contained in the string
    for key, value in CITY_NORMALIZATION.items():
        if key in cleaned:
            return value

    return None


def load_jobs() -> pd.DataFrame:
    """Load all jobs from database into a DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM jobs", conn)
    conn.close()
    return df


def clean_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize job data."""

    # Replace "--", "-", empty strings with None
    df.replace(["--", "-", "", " ", "#NOM?"], None, inplace=True)

    # Clean title and company
    df["title"]   = df["title"].str.strip()
    df["company"] = df["company"].str.strip()

    # Normalize city to 24 governorates
    df["city"] = df["city"].apply(normalize_city)

    # Normalize region
    df["region"] = df["region"].str.strip() if "region" in df.columns else None

    # Normalize contract types
    contract_map = {
        "Secteur privé":        "secteur_prive",
        "Secteur public":       "secteur_public",
        "Travail à l'étranger": "etranger",
        "Stage":                "stage",
        "Freelance":            "freelance",
        "Concours Tunisie":     "concours",
        "CDI":                  "CDI",
        "CDD":                  "CDD",
        "SIVP":                 "SIVP",
    }
    df["contract"] = df["contract"].map(contract_map).fillna(df["contract"])

    return df


def save_cleaned(df: pd.DataFrame) -> int:
    """Write cleaned data back to database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute("""
            UPDATE jobs
            SET title    = ?,
                company  = ?,
                city     = ?,
                region   = ?,
                contract = ?
            WHERE id = ?
        """, (row["title"], row["company"], row["city"], row["region"],
              row["contract"], row["id"]))

    conn.commit()
    conn.close()
    return len(df)


def export_csv():
    """Export cleaned data to CSV."""
    df = load_jobs()
    output_path = "./data/jobs_cleaned.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Exported {len(df)} jobs to {output_path}")


if __name__ == "__main__":
    print("Loading jobs...")
    df = load_jobs()
    print(f"Loaded {len(df)} jobs")

    print("Cleaning...")
    df = clean_jobs(df)

    # Stats
    mapped   = df["city"].notna().sum()
    unmapped = df["city"].isna().sum()
    print(f"Cities mapped: {mapped} | Unmapped (set to NULL): {unmapped}")

    print("Saving...")
    save_cleaned(df)

    print("Exporting CSV...")
    export_csv()

    print("\nCity distribution:")
    print(df["city"].value_counts().head(10))
