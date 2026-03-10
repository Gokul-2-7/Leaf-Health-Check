"""
Gemini AI Integration Module
Provides AI-powered plant disease explanations and personalized tips.
Falls back gracefully when API key is not configured.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class GeminiAIEngine:
    """Wraps Google Gemini API for plant health AI features."""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOOGLE_GEMINI_API_KEY", "")
        self.model = None
        self.chat_session = None
        self.history = []
        self._initialized = False

        if self.api_key and self.api_key not in ("", "YOUR_API_KEY_HERE"):
            self._initialize()

    def _initialize(self):
        """Try to initialize Gemini SDK."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-pro")
            self.chat_session = self.model.start_chat(history=[])
            self._initialized = True
            logger.info("Gemini AI initialized successfully.")
        except ImportError:
            logger.warning("google-generativeai package not installed. AI features disabled.")
        except Exception as e:
            logger.warning(f"Could not initialize Gemini AI: {e}. AI features disabled.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_disease_explanation(self, disease_name, plant_name, severity, affected_percentage):
        """
        Generate a plain-language explanation of the detected disease.

        Returns:
            str: Explanation text
        """
        if not self._initialized:
            return self._fallback_explanation(disease_name, plant_name, severity, affected_percentage)

        try:
            prompt = (
                f"Explain the plant disease '{disease_name}' detected on a {plant_name} plant. "
                f"The severity is '{severity}' with {affected_percentage:.1f}% of the leaf affected. "
                "Provide a clear, concise explanation in 2-3 sentences suitable for a home gardener. "
                "Include what causes it and what typically happens if untreated."
            )
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini explain error: {e}")
            return self._fallback_explanation(disease_name, plant_name, severity, affected_percentage)

    def generate_personalized_tips(self, disease_name, plant_name, severity,
                                   affected_percentage, default_tips=None):
        """
        Generate AI-personalized rescue tips.

        Returns:
            dict: {'status': 'success'|'fallback', 'enhanced_tips': str}
        """
        if not self._initialized:
            tips_text = "\n".join(f"• {t}" for t in (default_tips or []))
            return {'status': 'fallback', 'enhanced_tips': tips_text}

        try:
            base = "\n".join(default_tips or [])
            prompt = (
                f"A {plant_name} plant has been diagnosed with '{disease_name}' "
                f"at '{severity}' severity ({affected_percentage:.1f}% affected). "
                f"Here are the standard tips:\n{base}\n\n"
                "Enhance these tips with specific product names, timing, and quantities where helpful. "
                "Format the output as a numbered list of 3 actionable steps."
            )
            response = self.model.generate_content(prompt)
            return {'status': 'success', 'enhanced_tips': response.text.strip()}
        except Exception as e:
            logger.error(f"Gemini tips error: {e}")
            tips_text = "\n".join(f"• {t}" for t in (default_tips or []))
            return {'status': 'fallback', 'enhanced_tips': tips_text}

    def identify_preventive_measures(self, plant_name, disease_name, climate_zone="Temperate"):
        """
        Return preventive care measures for the plant/disease combination.

        Returns:
            list: List of preventive measure strings
        """
        if not self._initialized:
            return self._fallback_preventive(plant_name, disease_name)

        try:
            prompt = (
                f"List 4 preventive measures to stop '{disease_name}' from occurring on {plant_name} "
                f"in a {climate_zone} climate. Be specific and practical. "
                "Return each measure on a new line starting with a dash '-'."
            )
            response = self.model.generate_content(prompt)
            lines = [l.lstrip("- ").strip() for l in response.text.strip().splitlines() if l.strip()]
            return lines[:4]
        except Exception as e:
            logger.error(f"Gemini preventive error: {e}")
            return self._fallback_preventive(plant_name, disease_name)

    def generate_care_plan(self, plant_name, disease_name, severity):
        """
        Generate a multi-week care plan.

        Returns:
            str: Formatted care plan text
        """
        if not self._initialized:
            return self._fallback_care_plan(plant_name, disease_name, severity)

        try:
            prompt = (
                f"Create a 4-week care plan for a {plant_name} diagnosed with '{disease_name}' "
                f"at '{severity}' severity. Include weekly actions, treatments, and monitoring steps. "
                "Format it clearly with Week 1, Week 2, Week 3, Week 4 headings."
            )
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini care plan error: {e}")
            return self._fallback_care_plan(plant_name, disease_name, severity)

    def chat(self, user_message):
        """
        Send a message in an ongoing chat session.

        Returns:
            str: AI response text
        """
        if not self._initialized:
            return (
                "AI Assistant is currently unavailable. "
                "Please add a valid GOOGLE_GEMINI_API_KEY to your .env file to enable this feature.\n\n"
                f"Your question was: '{user_message}'\n\n"
                "In the meantime, check the Analyze Leaf tab for disease diagnosis and recommendations."
            )

        try:
            system_context = (
                "You are a helpful plant health assistant. "
                "Answer questions about plant diseases, treatments, and care. "
                "Be concise, practical, and friendly."
            )
            full_message = f"{system_context}\n\nUser: {user_message}"
            response = self.chat_session.send_message(full_message)
            self.history.append({'role': 'user', 'content': user_message})
            self.history.append({'role': 'assistant', 'content': response.text})
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            return f"Sorry, I encountered an error. Please try again. (Error: {e})"

    def clear_history(self):
        """Clear chat history and start a new session."""
        self.history = []
        if self._initialized and self.model:
            try:
                import google.generativeai as genai
                self.chat_session = self.model.start_chat(history=[])
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Fallback responses (no API key needed)
    # ------------------------------------------------------------------

    def _fallback_explanation(self, disease_name, plant_name, severity, affected_percentage):
        disease_display = disease_name.replace('_', ' ').title()
        return (
            f"{disease_display} is a common disease affecting {plant_name} plants. "
            f"Currently at '{severity}' severity with {affected_percentage:.1f}% of the leaf affected. "
            "Follow the rescue tips below and monitor daily for changes. "
            "To get AI-powered explanations, add your GOOGLE_GEMINI_API_KEY to the .env file."
        )

    def _fallback_preventive(self, plant_name, disease_name):
        return [
            f"Inspect {plant_name} plants weekly for early signs of disease.",
            "Maintain good air circulation by spacing plants appropriately.",
            "Water at the base — avoid wetting foliage.",
            "Remove and dispose of infected plant material promptly."
        ]

    def _fallback_care_plan(self, plant_name, disease_name, severity):
        disease_display = disease_name.replace('_', ' ').title()
        return (
            f"Care Plan: {plant_name} — {disease_display} ({severity.title()} Severity)\n\n"
            "Week 1: Remove all visibly infected leaves. Apply appropriate fungicide.\n"
            "Week 2: Re-inspect and reapply treatment if new symptoms appear.\n"
            "Week 3: Monitor recovery. Ensure proper watering and nutrition.\n"
            "Week 4: Assess overall plant health and decide on continued treatment.\n\n"
            "Tip: Add a GOOGLE_GEMINI_API_KEY to .env for a fully personalized AI care plan."
        )


def get_gemini_engine():
    """
    Factory function — returns a GeminiAIEngine instance.
    Always returns an object (never None); falls back gracefully if API key missing.
    """
    return GeminiAIEngine()
