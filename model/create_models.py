"""
create_models.py
Builds and saves untrained (randomly-initialized) model files so the app
can load them without requiring a full training run.

These models produce random predictions until you train them on real data
(e.g. PlantVillage dataset).  The colour-analysis and severity-grading
pipeline works correctly with or without trained weights.

Usage:
    python model/create_models.py
"""

import os
import sys
import logging
from pathlib import Path

# Make sure parent dir is on path so imports work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_models():
    try:
        import tensorflow as tf
        # Suppress verbose TF output
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
        tf.get_logger().setLevel("ERROR")
    except ImportError:
        logger.error(
            "TensorFlow is not installed. "
            "Run:  pip install tensorflow  (or tensorflow-cpu)"
        )
        sys.exit(1)

    from model.train import PlantDiseaseModel

    model_dir = Path(__file__).parent
    model_dir.mkdir(exist_ok=True)

    logger.info("Building disease classification model (EfficientNetB0)...")
    trainer = PlantDiseaseModel(architecture="efficientnet")

    disease_model = trainer.build_disease_model()
    disease_path = model_dir / "leaf_disease_model.h5"
    disease_model.save(str(disease_path))
    logger.info(f"✅ Disease model saved → {disease_path}")

    logger.info("Building plant species classification model (EfficientNetB0)...")
    plant_model = trainer.build_plant_model()
    plant_path = model_dir / "plant_species_model.h5"
    plant_model.save(str(plant_path))
    logger.info(f"✅ Plant model saved  → {plant_path}")

    logger.info(
        "\nModels created successfully!\n"
        "Note: These models have RANDOM weights and will give random predictions.\n"
        "To get accurate results, train the models on the PlantVillage dataset.\n"
        "See TRAINING.md for details."
    )


if __name__ == "__main__":
    create_models()
