"""
Recommendation Engine Module
Generates personalised rescue tips based on disease type, severity level,
and plant species. Falls back gracefully when the SQLite database is unavailable.

Coverage:
  - 8 disease classes (healthy + 7 diseases)
  - 5 severity levels per disease (healthy / mild / moderate / severe / dying)
  - General plant-care advice per species
  - Organic treatment alternatives
  - Emergency triage tips for severe/dying plants
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Severity-level action urgency messages ────────────────────────────────────
SEVERITY_URGENCY = {
    "mild":     "⏰ Act within 3–5 days. Early treatment is most effective and can fully reverse damage.",
    "moderate": "⚠️ Act within 24–48 hours. The disease is actively spreading — do not delay.",
    "severe":   "🚨 URGENT. Remove heavily infected plants immediately to protect neighbouring plants.",
    "dying":    "🆘 CRITICAL. Isolate this plant NOW. Consider full removal to prevent epidemic spread.",
}

# ── Organic / low-chemical alternatives ──────────────────────────────────────
ORGANIC_ALTERNATIVES = {
    "early_blight":       "Organic: spray a diluted baking soda solution (1 tsp per litre) or neem oil weekly.",
    "late_blight":        "Organic: copper sulphate spray is effective; remove and burn all infected tissue.",
    "septoria_leaf_spot": "Organic: neem oil or diluted hydrogen peroxide (3%) spray every 5–7 days.",
    "powdery_mildew":     "Organic: potassium bicarbonate or diluted milk spray (1:10) applied twice weekly.",
    "rust":               "Organic: sulfur-based spray or garlic extract solution applied at first sign.",
    "gray_leaf_spot":     "Organic: compost tea foliar spray to boost plant immune response.",
    "leaf_scab":          "Organic: lime sulfur dormant spray before bud break; neem oil during season.",
    "healthy":            "Organic maintenance: compost tea spray, balanced organic fertiliser monthly.",
}

# ── Per-plant general care tips ───────────────────────────────────────────────
PLANT_CARE_TIPS = {
    "tomato": [
        "Water deeply 2–3 times per week at the base; avoid wetting foliage.",
        "Feed with a balanced fertiliser (5-10-10) every 2 weeks during fruiting.",
        "Prune suckers regularly and stake tall varieties for support.",
        "Mulch with straw to retain moisture and prevent soil splash onto leaves.",
    ],
    "potato": [
        "Hill soil around stems every 2 weeks as plants grow to prevent greening.",
        "Reduce watering 2 weeks before harvest to allow skins to toughen.",
        "Inspect for Colorado beetles weekly — handpick and destroy egg clusters.",
        "Ensure excellent drainage; waterlogged soil promotes Late Blight and rot.",
    ],
    "apple": [
        "Prune to an open-centre shape each winter to improve air circulation.",
        "Apply dormant oil spray in late winter before buds swell to kill overwintering pests.",
        "Thin fruit clusters to 1–2 per spur in early summer for larger fruit.",
        "Rake and destroy all fallen leaves in autumn to break fungal disease cycles.",
    ],
    "corn": [
        "Plant in blocks rather than rows for better wind pollination.",
        "Side-dress with nitrogen fertiliser when plants are knee-high.",
        "Monitor for corn earworm: apply Bt (Bacillus thuringiensis) to silk.",
        "Irrigate deeply 1–2 times per week during tasselling and silking stages.",
    ],
    "wheat": [
        "Sow certified disease-free seed; treat seed with fungicide before planting.",
        "Monitor for aphids from tillering onwards — they spread barley yellow dwarf virus.",
        "Apply nitrogen in split doses: half at planting, half at tillering.",
        "Harvest promptly when grain moisture reaches 14% to avoid weather damage.",
    ],
}

# ── Comprehensive disease-specific tips by severity ───────────────────────────
DISEASE_TIPS: dict[str, dict[str, list[str]]] = {
    "healthy": {
        "healthy": [
            "✅ Your plant is in excellent health! Keep up the good care routine.",
            "💧 Continue regular deep watering at the base; avoid overhead irrigation.",
            "🌱 Apply a light balanced fertiliser monthly during the growing season.",
            "🔍 Inspect plants weekly for early signs of pests or disease.",
            "🍃 Remove any yellowing or damaged leaves promptly to maintain vigour.",
            "🌬️ Ensure 15–30 cm spacing between plants for healthy air circulation.",
        ],
    },

    "early_blight": {
        "mild": [
            "🍂 Remove all visibly spotted leaves — place in a sealed bag, do NOT compost.",
            "🧴 Apply copper-based fungicide spray (e.g., Bordeaux mixture) every 7–10 days.",
            "💧 Water at soil level only; wet foliage dramatically accelerates fungal spread.",
            "🌿 Mulch the base with straw or wood chips to prevent soil-splash reinfection.",
            "✂️ Improve air circulation by removing lower leaves touching the soil.",
        ],
        "moderate": [
            "🚨 Remove all infected leaves immediately; sterilise pruning shears with 70% alcohol.",
            "🧴 Switch to a systemic fungicide (e.g., azoxystrobin) for faster knockdown.",
            "🌬️ Thin the plant canopy aggressively to reduce humidity in the leaf zone.",
            "🚿 Stop ALL overhead watering — switch to drip or manual base watering.",
            "📸 Photograph the plant daily to monitor whether spread is accelerating.",
            "🌱 Apply a phosphorus-rich fertiliser (e.g., 0-20-0) to boost plant defence.",
        ],
        "severe": [
            "⚡ Strip all infected leaves immediately and dispose of in sealed rubbish bags.",
            "💊 Apply a dual-action systemic + contact fungicide (mancozeb + azoxystrobin mix).",
            "🔄 Remove heavily infected plants entirely if >70% of foliage is affected.",
            "🧹 Sanitise all tools, cages, and stakes with diluted bleach solution (1:9).",
            "🚫 Do NOT save seed from infected plants — spores survive on seed coats.",
            "📋 Document the outbreak for crop rotation planning next season.",
        ],
        "dying": [
            "🆘 EMERGENCY: Remove and bag the entire plant immediately — burn if possible.",
            "🧹 Sanitise the planting area with copper sulphate soil drench.",
            "⚠️ Inspect all neighbouring plants — Early Blight spreads via wind and tools.",
            "🔄 Do NOT replant Solanaceae (tomato, potato, pepper) in this spot for 3 years.",
            "📝 Record GPS location and date of outbreak for farm management records.",
        ],
    },

    "late_blight": {
        "mild": [
            "⚡ Act immediately — Late Blight (Phytophthora) can destroy a plant in 48 hours.",
            "🍂 Remove and seal ALL infected leaves and stems; dispose of off-site.",
            "💊 Apply mancozeb or chlorothalonil fungicide immediately; reapply every 5–7 days.",
            "🚿 Stop all overhead irrigation — high humidity is the primary driver of spread.",
            "🌡️ Monitor weather forecasts — cool, wet conditions accelerate Late Blight rapidly.",
        ],
        "moderate": [
            "🚨 URGENT: Remove all symptomatic tissue and destroy immediately — do not compost.",
            "💊 Apply systemic fungicide with metalaxyl (e.g., Ridomil Gold) — most effective.",
            "🏥 Treat ALL neighbouring plants preventively even if no symptoms are visible yet.",
            "🌬️ Improve drainage and air circulation around the entire planting area.",
            "📞 Consult your local agricultural extension office — this disease is notifiable.",
            "📸 Document spread rate with photos every 12 hours to gauge treatment response.",
        ],
        "severe": [
            "💥 Remove the entire plant and all debris immediately — bag and remove from site.",
            "🧹 Treat the soil with a copper-based drench to reduce spore load in the ground.",
            "⚠️ Inspect every plant in the field within a 50-metre radius.",
            "🔄 Consider emergency harvest of any uninfected tubers/fruit before spread worsens.",
            "🚫 Absolutely NO composting — spores survive in compost and reinfect next season.",
        ],
        "dying": [
            "🆘 CRITICAL EMERGENCY: Remove and destroy the entire plant — burn on-site if permitted.",
            "☠️ Assume all nearby plants are exposed — apply protective fungicide to all of them now.",
            "🔄 Full crop isolation: net or fence off the infected area to prevent movement of spores.",
            "🧹 Perform a full field sanitation — till under all debris and apply lime.",
            "📞 Report to local agriculture authority if this is a commercial planting.",
        ],
    },

    "septoria_leaf_spot": {
        "mild": [
            "✂️ Prune all lower leaves touching the soil — this is the primary infection route.",
            "🧴 Apply chlorothalonil or copper-based fungicide to all leaf surfaces.",
            "💧 Mulch around the base to prevent rain splash carrying spores upward.",
            "🌬️ Ensure adequate plant spacing (45–60 cm for tomatoes) for air circulation.",
            "🔍 Inspect plants twice weekly — Septoria spreads rapidly in warm, wet weather.",
        ],
        "moderate": [
            "🍂 Remove and destroy all spotted leaves — even partially affected ones.",
            "💊 Spray a systemic fungicide; cover leaf undersides thoroughly where spores form.",
            "🔄 Rotate crops — do not grow tomatoes or wheat in this spot for 2 years.",
            "🚿 Water only at the base; switch to early morning watering so plants dry by noon.",
            "🌱 Apply potassium-rich fertiliser (0-0-50) to toughen plant cell walls.",
        ],
        "severe": [
            "🚨 Strip the lower 50% of foliage and dispose of in sealed bags off-site.",
            "💊 Apply dual-mode fungicide (contact + systemic) on a 5-day spray schedule.",
            "🏥 Treat all plants in the bed, not just visibly infected ones.",
            "📊 Track infected leaf percentage — if >60%, consider removing the plant entirely.",
            "🧹 Sanitise all tools and stakes that have touched infected plants.",
        ],
        "dying": [
            "🆘 Remove the plant entirely and dispose of off-site in sealed bags.",
            "🧹 Sanitise the planting hole with copper sulphate solution.",
            "⚠️ Do not replant Solanaceae in this spot for at least 2 seasons.",
            "🔍 Inspect all tomato/wheat plants in the same bed for early symptoms.",
        ],
    },

    "powdery_mildew": {
        "mild": [
            "🌿 Apply neem oil spray (2 tsp neem oil + 1 tsp dish soap per litre) every 5 days.",
            "✂️ Prune crowded inner branches to improve air flow through the canopy.",
            "🚫 Avoid overhead watering — mildew thrives in humid, stagnant air.",
            "🌱 Reduce nitrogen fertilisation — lush soft growth is highly susceptible.",
            "☀️ Move potted plants to a sunnier, more airy location if possible.",
        ],
        "moderate": [
            "💊 Apply potassium bicarbonate or sulfur-based fungicide — the most effective contact killers.",
            "✂️ Prune and remove all heavily coated leaves and stems.",
            "🌬️ Drastically improve air circulation — thin the canopy by 30–40%.",
            "🧪 Spray a diluted milk solution (30% milk, 70% water) on affected areas as organic option.",
            "🌡️ Avoid temperature stress — plants stressed by heat or drought are more susceptible.",
        ],
        "severe": [
            "🚨 Apply systemic fungicide (trifloxystrobin or myclobutanil) on a 7-day schedule.",
            "✂️ Remove all heavily infected branches immediately.",
            "🌿 Do not compost infected clippings — spores survive and spread.",
            "🔄 Evaluate whether to replace severely infected specimens with resistant varieties.",
            "💧 Maintain consistent soil moisture — irregular watering stresses plants and worsens mildew.",
        ],
        "dying": [
            "🆘 Remove the entire plant to prevent mildew spore cloud from spreading further.",
            "🧹 Thoroughly clean the area with diluted bleach spray.",
            "🔄 Replace with known mildew-resistant varieties next season.",
            "📝 Note environmental conditions (humidity, spacing, watering) that contributed to outbreak.",
        ],
    },

    "rust": {
        "mild": [
            "🍂 Remove and immediately destroy all leaves showing orange/rust pustules.",
            "🧴 Apply triazole fungicide (tebuconazole or propiconazole) — most effective on rust.",
            "🌬️ Ensure good air circulation; rust spreads fastest in warm, humid, still air.",
            "🔍 Inspect leaf undersides daily — early pustules appear on undersides first.",
            "🌱 Avoid high-nitrogen fertiliser which promotes susceptible lush growth.",
        ],
        "moderate": [
            "🚨 Spray all plants in the area with a protective triazole fungicide.",
            "🍂 Strip all infected leaves; dispose of in sealed bags off-site.",
            "💊 Apply a second fungicide application 7–10 days after the first.",
            "🌱 Apply a balanced NPK fertiliser to help the plant recover and regenerate leaves.",
            "🔄 Plan to use rust-resistant varieties for replanting next season.",
        ],
        "severe": [
            "⚡ Remove all infected leaf material immediately — every infected leaf is a spore factory.",
            "💊 Use a systemic + contact fungicide combination for fastest knockdown.",
            "🏥 Treat ALL surrounding plants preventively — rust spreads very quickly by wind.",
            "📊 If >50% of plant is infected, evaluate full removal to protect the rest of the crop.",
        ],
        "dying": [
            "🆘 Remove and destroy the entire plant — rust spores are airborne and extremely mobile.",
            "🧹 Thoroughly clean the planting area; remove all leaf litter and debris.",
            "⚠️ Apply a preventive fungicide drench to all neighbouring plants immediately.",
            "🔄 Switch to rust-resistant varieties — check local agricultural extension recommendations.",
        ],
    },

    "gray_leaf_spot": {
        "mild": [
            "💊 Apply foliar fungicide containing strobilurin (azoxystrobin) at first symptoms.",
            "🌬️ Improve air circulation by thinning the plant canopy.",
            "💧 Avoid evening irrigation — wet foliage overnight dramatically accelerates spread.",
            "🌱 Do not apply late-season nitrogen — delays maturity and extends disease window.",
            "🔍 Monitor weather closely — gray leaf spot accelerates sharply in humid, cloudy conditions.",
        ],
        "moderate": [
            "🚨 Apply triazole fungicide (propiconazole) on a 10-day spray schedule.",
            "✂️ Remove heavily infected lower leaves to reduce the source of spore production.",
            "🌬️ Improve drainage around the planting area — waterlogged soil worsens the disease.",
            "📸 Track disease progression with daily photos to assess treatment response.",
        ],
        "severe": [
            "⚡ Apply dual-mode fungicide (strobilurin + triazole mixture) immediately.",
            "🔄 Consider early harvest of any partially mature crop to limit losses.",
            "🧹 After harvest, till under all crop debris deeply to reduce overwintering spore load.",
            "📋 Switch to resistant corn hybrids for the next planting cycle.",
        ],
        "dying": [
            "🆘 Perform emergency harvest of any salvageable crop immediately.",
            "🧹 Destroy all plant debris on-site; do NOT leave residue standing.",
            "🔄 Deep till the soil after removal and apply lime to reduce fungal survival.",
            "📝 Plan for resistant hybrid varieties and crop rotation next season.",
        ],
    },

    "leaf_scab": {
        "mild": [
            "🍂 Rake and remove all fallen leaves immediately — they harbour overwintering spores.",
            "🧴 Apply a protective fungicide (myclobutanil or captan) before the next rain event.",
            "✂️ Prune to open the canopy and improve air movement through the tree.",
            "💧 Use drip irrigation; avoid wetting foliage when watering.",
            "🔍 Inspect new growth every 3–4 days during wet spring weather.",
        ],
        "moderate": [
            "🚨 Apply fungicide spray immediately; cover entire tree including undersides of leaves.",
            "✂️ Prune out heavily infected branches; sterilise tools between cuts.",
            "🍂 Collect and destroy all infected leaf litter and fallen fruit.",
            "💊 Apply a follow-up fungicide spray 7–10 days after the first.",
            "🌬️ Thin the canopy by 25–30% to improve light penetration and air circulation.",
        ],
        "severe": [
            "⚡ Apply systemic fungicide (trifloxystrobin) for deep tissue penetration.",
            "✂️ Remove all heavily infected branches back to healthy wood.",
            "🏥 Treat every apple tree in the orchard preventively.",
            "🔄 Plan to replace severely infected trees with scab-resistant apple varieties.",
            "📋 Maintain a spray log — regular protective sprays are key to scab management.",
        ],
        "dying": [
            "🆘 Remove the tree or severely prune it back to healthy wood only.",
            "🧹 Thoroughly clean the area; remove all leaf litter, fallen fruit, and debris.",
            "🔄 Replant with certified scab-resistant apple varieties (e.g., Liberty, Redfree).",
            "💊 Apply dormant copper spray to the planting area before next season.",
        ],
    },
}

# ── Utility: get severity-aware card style ────────────────────────────────────
SEVERITY_CSS_CLASS = {
    "healthy":  "disease-card",
    "mild":     "disease-card",
    "moderate": "warning-card",
    "severe":   "danger-card",
    "dying":    "danger-card",
}


class RecommendationEngine:
    """
    Generates rescue tips and saves analysis history to the SQLite database.

    Tip priority order:
        1. Disease-specific tips for the given severity level (from DISEASE_TIPS dict)
        2. Severity urgency message prepended when severity >= mild
        3. Organic alternative tip appended
        4. Fallback: generic healthy tips if disease not recognised
        5. Database tips (if DB available and populated)
    """

    # ── Public API ────────────────────────────────────────────────────────────
    @staticmethod
    def get_recommendations(
        disease_name:   str,
        severity_level: str,
        plant_name:     str,
        db_path:        str | None = None,
    ) -> list[str]:
        """
        Return a list of up to 5 rescue tips for the given disease & severity.

        Args:
            disease_name:   Model output class string, e.g. 'early_blight'
            severity_level: Severity string, e.g. 'moderate'
            plant_name:     Plant species string, e.g. 'tomato'
            db_path:        Path to SQLite database (optional)

        Returns:
            list[str]: Ordered list of actionable tip strings (max 5)
        """
        # 1. Try the rich built-in tip dictionary first
        tips = RecommendationEngine._get_builtin_tips(disease_name, severity_level)

        # 2. If built-in tips missing, try database
        if not tips and db_path and Path(db_path).exists():
            try:
                tips = RecommendationEngine._get_tips_from_db(disease_name, severity_level, db_path)
            except Exception as exc:
                logger.warning(f"DB tip lookup failed: {exc}")

        # 3. Ultimate fallback: generic healthy-plant advice
        if not tips:
            tips = DISEASE_TIPS.get("healthy", {}).get("healthy", [
                "Monitor the plant closely and maintain regular care.",
                "Ensure adequate watering, fertilisation, and air circulation.",
                "Consult a local plant pathologist for a definitive diagnosis.",
            ])

        # 4. Prepend urgency message for non-healthy plants
        if severity_level != "healthy" and severity_level in SEVERITY_URGENCY:
            tips = [SEVERITY_URGENCY[severity_level]] + tips

        # 5. Append organic alternative tip
        organic = ORGANIC_ALTERNATIVES.get(disease_name)
        if organic and organic not in tips:
            tips.append(organic)

        # 6. Append a plant-specific care reminder
        plant_key = plant_name.lower()
        plant_tips = PLANT_CARE_TIPS.get(plant_key, [])
        if plant_tips and plant_tips[0] not in tips:
            tips.append(f"🌿 {plant_name.title()} care reminder: {plant_tips[0]}")

        return tips[:5]  # Return top 5

    @staticmethod
    def get_all_plant_tips(plant_name: str) -> list[str]:
        """Return all general care tips for a plant species."""
        return PLANT_CARE_TIPS.get(plant_name.lower(), [
            "Follow standard care guidelines for this species.",
            "Water regularly, fertilise monthly, and monitor for disease.",
        ])

    @staticmethod
    def get_organic_alternative(disease_name: str) -> str:
        """Return the organic treatment alternative for a disease."""
        return ORGANIC_ALTERNATIVES.get(
            disease_name, "Use compost tea spray as a general immune booster."
        )

    @staticmethod
    def get_urgency_message(severity_level: str) -> str | None:
        """Return the urgency action message for a severity level."""
        return SEVERITY_URGENCY.get(severity_level)

    @staticmethod
    def save_analysis_history(analysis_data: dict, db_path: str) -> bool:
        """
        Persist an analysis result to the SQLite analysis_history table.

        Args:
            analysis_data: dict with keys plant_name, disease_name, severity,
                           confidence, discoloration_percent, image_filename
            db_path: path to SQLite database file

        Returns:
            bool: True on success, False on failure
        """
        try:
            conn   = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analysis_history
                    (plant_name, disease_name, severity, confidence,
                     discoloration_percent, image_filename)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                analysis_data.get("plant_name",            "unknown"),
                analysis_data.get("disease_name",          "unknown"),
                analysis_data.get("severity",              "unknown"),
                float(analysis_data.get("confidence",      0.0)),
                float(analysis_data.get("discoloration_percent", 0.0)),
                analysis_data.get("image_filename",        ""),
            ))
            conn.commit()
            conn.close()
            logger.info("Analysis history saved to database.")
            return True
        except Exception as exc:
            logger.error(f"Failed to save analysis history: {exc}")
            return False

    @staticmethod
    def load_history_from_db(db_path: str, limit: int = 100) -> list[dict]:
        """
        Load recent analysis history records from the database.

        Args:
            db_path: path to SQLite database
            limit:   maximum number of records to return

        Returns:
            list[dict]: list of history record dicts ordered by most recent first
        """
        try:
            conn   = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT plant_name, disease_name, severity, confidence,
                       discoloration_percent, image_filename, created_at
                FROM analysis_history
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            conn.close()
            return [
                {
                    "plant_name":           row[0],
                    "disease_name":         row[1],
                    "severity":             row[2],
                    "confidence":           row[3],
                    "discoloration_percent": row[4],
                    "image_filename":       row[5],
                    "created_at":           row[6],
                }
                for row in rows
            ]
        except Exception as exc:
            logger.error(f"Failed to load history from DB: {exc}")
            return []

    # ── Private helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _get_builtin_tips(disease_name: str, severity_level: str) -> list[str]:
        """Look up tips from the DISEASE_TIPS dictionary."""
        disease_key  = disease_name.lower()
        severity_key = severity_level.lower()

        disease_entry = DISEASE_TIPS.get(disease_key)
        if not disease_entry:
            return []

        # Exact match first, then fall back to nearest severity
        tips = disease_entry.get(severity_key, [])
        if not tips:
            # Try fallback order: moderate → mild → healthy
            for fallback in ("moderate", "mild", "healthy"):
                tips = disease_entry.get(fallback, [])
                if tips:
                    break

        return list(tips)  # Return a copy

    @staticmethod
    def _get_tips_from_db(disease_name: str, severity_level: str, db_path: str) -> list[str]:
        """Query the SQLite database for disease-specific tips."""
        conn   = sqlite3.connect(db_path)
        cursor = conn.cursor()

        disease_display  = disease_name.replace("_", " ").title()
        severity_display = severity_level.title()

        cursor.execute("""
            SELECT t.tip FROM tips t
            JOIN diseases d ON t.disease_id = d.id
            WHERE d.name LIKE ? AND t.severity = ?
            ORDER BY t.order_index
            LIMIT 5
        """, (f"%{disease_display}%", severity_display))

        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
