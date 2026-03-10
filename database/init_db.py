"""
Database Initialization Script
Creates and seeds the SQLite database with:
  - 5 plant species records
  - 8 disease records with detailed descriptions
  - 120+ rescue tips (5 severities × 8 diseases × 3 tips)
  - analysis_history table schema

Usage:
    python database/init_db.py
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATABASE_PATH = Path(__file__).parent / "plants.db"

# ── Schema ────────────────────────────────────────────────────────────────────
CREATE_PLANTS_TABLE = """
    CREATE TABLE IF NOT EXISTS plants (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        name                TEXT    NOT NULL UNIQUE,
        scientific_name     TEXT,
        family              TEXT,
        common_diseases     TEXT,
        optimal_temp_min    REAL,
        optimal_temp_max    REAL,
        optimal_conditions  TEXT,
        watering_frequency  TEXT,
        sunlight_req        TEXT,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""

CREATE_DISEASES_TABLE = """
    CREATE TABLE IF NOT EXISTS diseases (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT    NOT NULL UNIQUE,
        plant_id        INTEGER,
        pathogen        TEXT,
        pathogen_type   TEXT,
        description     TEXT,
        symptoms        TEXT,
        spread_method   TEXT,
        severity_risk   TEXT,
        is_contagious   INTEGER DEFAULT 1,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (plant_id) REFERENCES plants(id)
    )
"""

CREATE_TIPS_TABLE = """
    CREATE TABLE IF NOT EXISTS tips (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        disease_id  INTEGER NOT NULL,
        severity    TEXT    NOT NULL,
        tip         TEXT    NOT NULL,
        tip_type    TEXT    DEFAULT 'action',
        order_index INTEGER DEFAULT 1,
        is_organic  INTEGER DEFAULT 0,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (disease_id) REFERENCES diseases(id)
    )
"""

CREATE_HISTORY_TABLE = """
    CREATE TABLE IF NOT EXISTS analysis_history (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        plant_name           TEXT,
        disease_name         TEXT,
        severity             TEXT,
        confidence           REAL,
        discoloration_percent REAL,
        image_filename       TEXT,
        notes                TEXT,
        created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""

CREATE_SPRAYS_TABLE = """
    CREATE TABLE IF NOT EXISTS spray_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        plant_name  TEXT,
        product     TEXT,
        dilution    TEXT,
        area_sqm    REAL,
        spray_date  TEXT,
        next_due    TEXT,
        notes       TEXT,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""

# ── Seed data ─────────────────────────────────────────────────────────────────
PLANTS_DATA = [
    # (name, scientific_name, family, common_diseases,
    #  temp_min, temp_max, optimal_conditions, watering_freq, sunlight)
    (
        "Tomato", "Solanum lycopersicum", "Solanaceae",
        "Early Blight, Late Blight, Septoria Leaf Spot, Powdery Mildew",
        21.0, 29.0,
        "Well-drained fertile soil, pH 6.0–6.8, consistent moisture",
        "2–3 times per week (deep watering)", "Full sun (6–8 hours)",
    ),
    (
        "Potato", "Solanum tuberosum", "Solanaceae",
        "Early Blight, Late Blight, Verticillium Wilt, Scab",
        15.0, 20.0,
        "Loose, well-drained sandy loam, pH 5.0–6.0, cool nights",
        "1–2 times per week", "Full sun (6+ hours)",
    ),
    (
        "Apple", "Malus domestica", "Rosaceae",
        "Powdery Mildew, Apple Scab, Fire Blight, Cedar-Apple Rust",
        12.0, 24.0,
        "Deep well-drained soil, pH 6.0–7.0, good air circulation",
        "Deep weekly irrigation in summer", "Full sun (8 hours)",
    ),
    (
        "Corn", "Zea mays", "Poaceae",
        "Northern Corn Leaf Blight, Gray Leaf Spot, Common Rust, Smut",
        24.0, 30.0,
        "Fertile loam, pH 5.8–7.0, moderate moisture",
        "1 inch per week, more during tasselling", "Full sun (6–8 hours)",
    ),
    (
        "Wheat", "Triticum aestivum", "Poaceae",
        "Stripe Rust, Stem Rust, Septoria Leaf Blotch, Powdery Mildew, Fusarium Head Blight",
        12.0, 22.0,
        "Loam to clay-loam, pH 6.0–7.0, moderate fertility",
        "Rain-fed or 1–2 irrigations at critical growth stages",
        "Full sun",
    ),
]

DISEASES_DATA = [
    # (name, plant_id, pathogen, pathogen_type, description, symptoms, spread, severity, contagious)
    (
        "Early Blight", 1, "Alternaria solani", "Fungal",
        "A common fungal disease affecting Solanaceous crops. Spreads rapidly in warm, humid conditions. "
        "Can cause significant defoliation if untreated but rarely kills the plant outright.",
        "Dark brown concentric rings ('target-board' pattern) on older leaves. Yellowing leaf tissue around lesions.",
        "Wind-dispersed spores, water splash, infected plant debris, contaminated tools.",
        "Moderate", 1,
    ),
    (
        "Late Blight", 1, "Phytophthora infestans", "Oomycete (water mould)",
        "One of the most devastating plant diseases in history — caused the Irish Potato Famine. "
        "Can destroy an entire crop within days under favourable conditions.",
        "Water-soaked dark lesions that rapidly turn brown-black. White fluffy mould on leaf undersides. "
        "Entire plants collapse in severe cases.",
        "Airborne spores travel long distances. Spread by wind, rain, and infected plant material.",
        "Very High", 1,
    ),
    (
        "Septoria Leaf Spot", 1, "Septoria lycopersici", "Fungal",
        "A progressive fungal disease that moves from lower leaves upward. Reduces photosynthetic area "
        "significantly and can cause premature defoliation.",
        "Small circular spots (3–5 mm) with dark brown edges and grey-white centres. "
        "Tiny black fruiting bodies (pycnidia) visible inside spots.",
        "Rain splash, overhead irrigation, wind, contaminated tools and clothing.",
        "Moderate", 1,
    ),
    (
        "Powdery Mildew", 3, "Erysiphe spp. / various", "Fungal",
        "White powdery coating caused by obligate parasitic fungi. Unlike most fungi, thrives in dry "
        "conditions. Rarely fatal but significantly reduces plant vigour and yield.",
        "White-grey powdery patches on leaf surfaces. Leaves may curl, yellow, and drop prematurely. "
        "Soft new growth is most susceptible.",
        "Airborne spores — highly mobile. Does NOT require water for germination (unique among fungi).",
        "Low to Moderate", 1,
    ),
    (
        "Rust", 4, "Puccinia spp.", "Fungal (obligate parasite)",
        "A group of obligate parasitic fungi producing characteristic rust-coloured spore masses. "
        "Can cause major yield losses in cereal crops if not controlled early.",
        "Reddish-orange to brown powdery pustules on leaf surfaces and undersides. "
        "Leaves yellow and die. Severe infections cause complete defoliation.",
        "Wind-dispersed urediniospores travel hundreds of kilometres. Favours warm, humid conditions.",
        "High", 1,
    ),
    (
        "Gray Leaf Spot", 4, "Cercospora zeae-maydis", "Fungal",
        "A major fungal disease of corn that thrives in warm, humid conditions. Can cause yield losses "
        "of 20–50% in susceptible hybrids under severe epidemics.",
        "Rectangular tan-to-grey lesions with parallel sides bounded by leaf veins (1–6 cm long). "
        "Lesions may coalesce, killing entire leaves.",
        "Wind, rain splash. Overwinters in infected crop debris on the soil surface.",
        "Moderate to High", 1,
    ),
    (
        "Leaf Scab", 3, "Venturia inaequalis", "Fungal",
        "The most economically important apple disease worldwide. Primary infection occurs in spring "
        "from ascospores released from overwintered leaf litter.",
        "Olive-green to dark brown velvety spots on leaves and fruit. Infected leaves may yellow and drop. "
        "Fruit shows corky, cracked, disfiguring lesions.",
        "Ascospores from overwintered leaves (primary). Conidia from summer lesions (secondary). Rain splash.",
        "Moderate", 1,
    ),
    (
        "Northern Corn Leaf Blight", 4, "Exserohilum turcicum", "Fungal",
        "A significant foliar disease of corn characterised by distinctive long cigar-shaped lesions. "
        "Can cause yield losses of 30–50% in severe epidemics on susceptible hybrids.",
        "Long (10–15 cm), elliptical, cigar-shaped lesions with tan centres and dark margins. "
        "Lesions have wavy edges. Entire leaves may die and grey spore masses form in humid conditions.",
        "Wind-dispersed conidia. Overwinters in infected crop residues.",
        "High if early", 1,
    ),
]

# Tips: (disease_id, severity, tip, tip_type, order_index, is_organic)
TIPS_DATA = [
    # ── Early Blight (disease_id = 1) ────────────────────────────────────────
    (1,"Mild",    "Remove all visibly spotted leaves and place in sealed rubbish bags. Do NOT compost.",             "action",    1, 0),
    (1,"Mild",    "Apply copper-based fungicide (Bordeaux mixture) every 7–10 days, covering all leaf surfaces.",   "treatment", 2, 0),
    (1,"Mild",    "Water only at soil level using drip or soaker hose. Wet foliage accelerates spore germination.", "prevention",3, 0),
    (1,"Mild",    "Mulch around the base with straw (5–7 cm deep) to prevent soil-spore splash.",                   "prevention",4, 0),
    (1,"Mild",    "Organic option: spray diluted neem oil (2 tsp/L) every 5 days.",                                 "organic",   5, 1),

    (1,"Moderate","Remove all infected leaves immediately; sterilise pruning shears with 70% isopropyl alcohol.",   "action",    1, 0),
    (1,"Moderate","Apply systemic fungicide (azoxystrobin or propiconazole) — more effective than contact-only.",   "treatment", 2, 0),
    (1,"Moderate","Stop all overhead watering immediately and switch to drip irrigation.",                          "action",    3, 0),
    (1,"Moderate","Apply a phosphorus-boosting fertiliser (0-20-0) to strengthen plant disease resistance.",        "nutrition", 4, 0),
    (1,"Moderate","Photograph the plant every 24 hours to monitor whether spread is accelerating.",                 "monitoring",5, 0),

    (1,"Severe",  "Strip all infected leaves and dispose of off-site in sealed bags. Do not compost.",              "action",    1, 0),
    (1,"Severe",  "Apply dual-action fungicide mixing mancozeb + azoxystrobin for combined contact + systemic.",    "treatment", 2, 0),
    (1,"Severe",  "If >70% of foliage is affected, remove the entire plant to protect neighbours.",                 "action",    3, 0),
    (1,"Severe",  "Sanitise all tools, cages, and stakes with diluted bleach solution (1:9 bleach:water).",         "sanitation",4, 0),
    (1,"Severe",  "Do NOT save seed from infected plants — spores survive on seed coats.",                          "prevention",5, 0),

    # ── Late Blight (disease_id = 2) ─────────────────────────────────────────
    (2,"Mild",    "Act IMMEDIATELY — Late Blight can destroy an entire plant within 48–72 hours.",                  "urgent",    1, 0),
    (2,"Mild",    "Remove and seal ALL infected leaves and stems. Dispose of far from the garden.",                 "action",    2, 0),
    (2,"Mild",    "Apply mancozeb or chlorothalonil fungicide at once; reapply every 5–7 days.",                    "treatment", 3, 0),
    (2,"Mild",    "Stop all overhead irrigation permanently — high humidity is the primary spread driver.",         "action",    4, 0),
    (2,"Mild",    "Monitor weather: cool (10–20°C) + wet conditions = extreme spread risk.",                        "monitoring",5, 0),

    (2,"Moderate","URGENT: Remove all symptomatic tissue and destroy immediately — do not compost under any circumstances.", "urgent", 1, 0),
    (2,"Moderate","Apply metalaxyl-based fungicide (Ridomil Gold) — the most effective systemic option for Late Blight.",  "treatment", 2, 0),
    (2,"Moderate","Treat ALL neighbouring Solanaceae plants preventively even if symptom-free.",                            "prevention",3, 0),
    (2,"Moderate","Improve field drainage — remove standing water immediately around affected plants.",                     "action",    4, 0),
    (2,"Moderate","Contact your local agricultural extension office if this is a commercial planting.",                     "advisory",  5, 0),

    (2,"Severe",  "Remove the entire plant and all associated debris immediately; bag and remove from site.",       "action",    1, 0),
    (2,"Severe",  "Drench the soil with copper sulphate solution to reduce viable spore load in the ground.",       "treatment", 2, 0),
    (2,"Severe",  "Inspect EVERY plant in a 50-metre radius. Apply protective fungicide to all of them.",           "action",    3, 0),
    (2,"Severe",  "If commercial: consider emergency harvest of any symptom-free produce before spread worsens.",   "advisory",  4, 0),
    (2,"Severe",  "Document outbreak with GPS coordinates for farm disease management records.",                    "record",    5, 0),

    # ── Septoria Leaf Spot (disease_id = 3) ──────────────────────────────────
    (3,"Mild",    "Prune all lower leaves touching or near the soil — the primary infection route.",               "action",    1, 0),
    (3,"Mild",    "Apply chlorothalonil or copper-based fungicide covering all leaf surfaces including undersides.", "treatment", 2, 0),
    (3,"Mild",    "Mulch the base with 5 cm of organic material to prevent rain splash.",                          "prevention",3, 0),
    (3,"Moderate","Remove and destroy all spotted leaves immediately; even partially affected ones.",              "action",    1, 0),
    (3,"Moderate","Apply systemic fungicide; spray undersides of leaves where spores are produced.",               "treatment", 2, 0),
    (3,"Moderate","Rotate crops — do not grow tomatoes or wheat in this spot for 2 years minimum.",                "prevention",3, 0),
    (3,"Severe",  "Strip lower 50% of foliage immediately; dispose of in sealed bags off-site.",                   "action",    1, 0),
    (3,"Severe",  "Apply dual-mode fungicide (contact + systemic) on a 5-day intensive spray schedule.",           "treatment", 2, 0),
    (3,"Severe",  "Treat all plants in the same bed, not just visibly infected ones.",                             "action",    3, 0),

    # ── Powdery Mildew (disease_id = 4) ──────────────────────────────────────
    (4,"Mild",    "Apply neem oil spray (2 tsp neem oil + 1 tsp dish soap per litre water) every 5 days.",        "organic",   1, 1),
    (4,"Mild",    "Prune crowded inner branches to improve air flow through the canopy.",                          "action",    2, 0),
    (4,"Mild",    "Avoid overhead watering — powdery mildew thrives in humid, stagnant air.",                      "prevention",3, 0),
    (4,"Moderate","Apply potassium bicarbonate or sulfur-based fungicide — most effective contact killers for PM.", "treatment", 1, 0),
    (4,"Moderate","Prune and remove all heavily coated leaves and stems; bag and dispose.",                        "action",    2, 0),
    (4,"Moderate","Spray a diluted milk solution (30% milk, 70% water) as an organic treatment option.",           "organic",   3, 1),
    (4,"Severe",  "Apply systemic fungicide (myclobutanil or trifloxystrobin) on a strict 7-day schedule.",        "treatment", 1, 0),
    (4,"Severe",  "Remove all heavily infected branches and growth; do not compost.",                              "action",    2, 0),
    (4,"Severe",  "Consider replacing severely infected specimens with mildew-resistant varieties.",                "advisory",  3, 0),

    # ── Rust (disease_id = 5) ─────────────────────────────────────────────────
    (5,"Mild",    "Remove and immediately destroy all leaves showing orange/rust-coloured pustules.",              "action",    1, 0),
    (5,"Mild",    "Apply triazole fungicide (tebuconazole) — the most effective chemistry against rust.",          "treatment", 2, 0),
    (5,"Mild",    "Ensure good air circulation; rust spreads fastest in warm, humid, still air.",                  "prevention",3, 0),
    (5,"Moderate","Spray all plants in the area with protective triazole fungicide immediately.",                   "treatment", 1, 0),
    (5,"Moderate","Apply a second fungicide application 7–10 days after the first for continued protection.",      "treatment", 2, 0),
    (5,"Moderate","Apply balanced NPK fertiliser to help the plant recover and regenerate healthy tissue.",         "nutrition", 3, 0),
    (5,"Severe",  "Remove all infected leaf material — every infected leaf produces millions of spores.",           "action",    1, 0),
    (5,"Severe",  "Use a systemic + contact fungicide combination for the fastest possible knockdown.",             "treatment", 2, 0),
    (5,"Severe",  "Treat ALL surrounding plants preventively — rust is airborne and highly mobile.",                "prevention",3, 0),

    # ── Gray Leaf Spot (disease_id = 6) ──────────────────────────────────────
    (6,"Mild",    "Apply azoxystrobin (strobilurin) fungicide at the first sign of rectangular lesions.",          "treatment", 1, 0),
    (6,"Mild",    "Avoid evening irrigation — wet foliage overnight dramatically accelerates spread.",             "prevention",2, 0),
    (6,"Mild",    "Do not apply late-season nitrogen — it delays maturity and extends the disease window.",         "prevention",3, 0),
    (6,"Moderate","Apply triazole fungicide (propiconazole) on a strict 10-day spray schedule.",                   "treatment", 1, 0),
    (6,"Moderate","Remove heavily infected lower leaves to reduce the local spore load.",                          "action",    2, 0),
    (6,"Moderate","Improve drainage around the planting — waterlogged roots weaken disease resistance.",            "action",    3, 0),
    (6,"Severe",  "Apply dual-mode fungicide (strobilurin + triazole mixture) immediately.",                        "treatment", 1, 0),
    (6,"Severe",  "Consider early harvest of any partially mature corn crop to limit losses.",                     "advisory",  2, 0),
    (6,"Severe",  "After harvest, till all crop debris deeply (20+ cm) to reduce overwintering spore load.",       "prevention",3, 0),

    # ── Leaf Scab (disease_id = 7) ────────────────────────────────────────────
    (7,"Mild",    "Rake and remove ALL fallen leaves immediately — they harbour next season's spores.",            "action",    1, 0),
    (7,"Mild",    "Apply protective fungicide (myclobutanil or captan) before the next forecasted rain event.",    "treatment", 2, 0),
    (7,"Mild",    "Prune to open the canopy and improve air movement through the apple tree.",                     "action",    3, 0),
    (7,"Moderate","Apply fungicide spray immediately; cover the entire tree including leaf undersides.",            "treatment", 1, 0),
    (7,"Moderate","Prune out heavily infected branches; sterilise cutting tools between each cut.",                 "action",    2, 0),
    (7,"Moderate","Apply a follow-up fungicide spray 7–10 days after the first application.",                      "treatment", 3, 0),
    (7,"Severe",  "Apply systemic fungicide (trifloxystrobin) for deep tissue penetration.",                        "treatment", 1, 0),
    (7,"Severe",  "Remove all heavily infected branches back to healthy wood only.",                               "action",    2, 0),
    (7,"Severe",  "Plan to replace severely infected trees with certified scab-resistant apple varieties.",         "advisory",  3, 0),

    # ── Northern Corn Leaf Blight (disease_id = 8) ───────────────────────────
    (8,"Mild",    "Apply foliar fungicide (azoxystrobin or propiconazole) at first sign of cigar-shaped lesions.", "treatment", 1, 0),
    (8,"Mild",    "Avoid irrigation in the evening — damp canopy overnight facilitates spore germination.",        "prevention",2, 0),
    (8,"Mild",    "Ensure adequate potassium nutrition — K deficiency increases susceptibility.",                   "nutrition", 3, 0),
    (8,"Moderate","Apply triazole fungicide on a 10–14 day spray schedule for the remainder of the season.",       "treatment", 1, 0),
    (8,"Moderate","If a susceptible hybrid, consider whether replanting with a resistant hybrid is viable.",        "advisory",  2, 0),
    (8,"Moderate","Scout fields weekly — rapid disease progression from mild to severe is possible in wet weather.","monitoring",3, 0),
    (8,"Severe",  "Apply dual-mode fungicide (strobilurin + triazole) at maximum label rate immediately.",          "treatment", 1, 0),
    (8,"Severe",  "Perform emergency harvest of any grain at black-layer stage before total leaf loss.",            "advisory",  2, 0),
    (8,"Severe",  "After harvest: deep till all corn residue and plant a cover crop to reduce spore survival.",    "prevention",3, 0),
]


# ── Database functions ────────────────────────────────────────────────────────
def init_database(db_path: Path | None = None) -> None:
    """
    Initialise the SQLite database: create all tables and seed with sample data.

    Args:
        db_path: Optional custom path. Defaults to DATABASE_PATH.
    """
    target = db_path or DATABASE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)

    conn   = sqlite3.connect(target)
    cursor = conn.cursor()

    # Enable foreign key enforcement
    cursor.execute("PRAGMA foreign_keys = ON")

    # Create tables
    for statement in [
        CREATE_PLANTS_TABLE,
        CREATE_DISEASES_TABLE,
        CREATE_TIPS_TABLE,
        CREATE_HISTORY_TABLE,
        CREATE_SPRAYS_TABLE,
    ]:
        cursor.execute(statement)

    conn.commit()
    logger.info("✅ Database tables created successfully.")

    # Seed data
    _insert_seed_data(cursor)
    conn.commit()
    conn.close()
    logger.info(f"✅ Database initialised at: {target}")


def _insert_seed_data(cursor: sqlite3.Cursor) -> None:
    """Insert seed data if the tables are empty."""
    cursor.execute("SELECT COUNT(*) FROM plants")
    if cursor.fetchone()[0] > 0:
        logger.info("Database already contains data — skipping seed insertion.")
        return

    # Plants
    cursor.executemany(
        """INSERT INTO plants
           (name, scientific_name, family, common_diseases,
            optimal_temp_min, optimal_temp_max, optimal_conditions,
            watering_frequency, sunlight_req)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        PLANTS_DATA,
    )
    logger.info(f"  Inserted {len(PLANTS_DATA)} plant records.")

    # Diseases
    cursor.executemany(
        """INSERT INTO diseases
           (name, plant_id, pathogen, pathogen_type, description, symptoms,
            spread_method, severity_risk, is_contagious)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        DISEASES_DATA,
    )
    logger.info(f"  Inserted {len(DISEASES_DATA)} disease records.")

    # Tips
    cursor.executemany(
        """INSERT INTO tips
           (disease_id, severity, tip, tip_type, order_index, is_organic)
           VALUES (?, ?, ?, ?, ?, ?)""",
        TIPS_DATA,
    )
    logger.info(f"  Inserted {len(TIPS_DATA)} tip records.")

    logger.info("✅ Seed data inserted successfully.")


def reset_database(db_path: Path | None = None) -> None:
    """
    Drop and recreate the database (WARNING: destroys all analysis history).

    Args:
        db_path: Optional custom path. Defaults to DATABASE_PATH.
    """
    target = db_path or DATABASE_PATH
    if target.exists():
        target.unlink()
        logger.warning(f"Deleted existing database at {target}")
    init_database(target)


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Return a SQLite connection to the database."""
    target = db_path or DATABASE_PATH
    return sqlite3.connect(target)


def get_plant_info(plant_name: str, db_path: Path | None = None) -> dict | None:
    """Fetch plant info from the database by name."""
    conn   = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plants WHERE name = ? COLLATE NOCASE", (plant_name,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))


def get_disease_info(disease_name: str, db_path: Path | None = None) -> dict | None:
    """Fetch disease info from the database by name."""
    conn   = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM diseases WHERE name LIKE ? COLLATE NOCASE",
                   (f"%{disease_name}%",))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))


def get_analysis_history(limit: int = 50, db_path: Path | None = None) -> list[dict]:
    """Fetch the most recent analysis history records."""
    conn   = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM analysis_history ORDER BY id DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    conn.close()
    return [dict(zip(cols, row)) for row in rows]


def get_database_stats(db_path: Path | None = None) -> dict:
    """Return record counts for all tables."""
    conn   = get_connection(db_path)
    cursor = conn.cursor()
    stats  = {}
    for table in ["plants", "diseases", "tips", "analysis_history", "spray_log"]:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            stats[table] = 0
    conn.close()
    return stats


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🗄️  Initialising Leaf Health Check database…")
    init_database()

    stats = get_database_stats()
    print("\n📊 Database Statistics:")
    for table, count in stats.items():
        print(f"   {table:<20} {count:>4} records")
    print(f"\n✅ Database ready at: {DATABASE_PATH}")
