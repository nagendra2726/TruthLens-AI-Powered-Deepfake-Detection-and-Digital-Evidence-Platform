import logging
from typing import Optional, Tuple
from PIL import Image
import torch
from facenet_pytorch import MTCNN

logger = logging.getLogger(__name__)


class FaceDetector:
    """Detects, aligns, and crops faces from image inputs using MTCNN."""

    def __init__(self, device: Optional[torch.device] = None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Initializing MTCNN FaceDetector on device: {self.device}")
        self.mtcnn = MTCNN(
            image_size=160,
            margin=14,
            min_face_size=32,
            thresholds=[0.6, 0.7, 0.7],
            factor=0.709,
            post_process=True,
            keep_all=True,
            device=self.device,
        )

    def detect_and_crop(self, image: Image.Image) -> Tuple[Optional[torch.Tensor], int]:
        """
        Detects faces in a PIL Image and returns preprocessed 160x160 face tensors.

        Returns:
            Tuple of:
              - Tensor of shape (N, 3, 160, 160) on self.device, or None if 0 faces.
              - Count of detected faces (int).
        """
        if image.mode != "RGB":
            image = image.convert("RGB")

        try:
            # mtcnn returns a tensor of cropped and standardized face images
            face_tensors = self.mtcnn(image)
            if face_tensors is None:
                return None, 0

            # If a single face was detected, mtcnn returns (3, 160, 160) or (1, 3, 160, 160)
            if face_tensors.ndim == 3:
                face_tensors = face_tensors.unsqueeze(0)

            face_count = face_tensors.shape[0]
            logger.info(f"Detected {face_count} face(s) in image (size: {image.size})")
            return face_tensors.to(self.device), face_count
        except Exception as e:
            logger.warning(f"Error during face detection: {e}")
            return None, 0

    def analyze_faces(self, image: Image.Image) -> dict:
        """
        Detects faces in a PIL Image and returns structured face metadata:
        - face_detected: bool
        - face_count: int
        - bounding_boxes: list of [x1, y1, x2, y2]
        - detection_confidences: list of float confidences
        - message: explanatory string regarding human-face context
        """
        if image.mode != "RGB":
            image = image.convert("RGB")

        try:
            boxes, probs = self.mtcnn.detect(image)
            if boxes is None or len(boxes) == 0:
                return {
                    "face_detected": False,
                    "face_count": 0,
                    "bounding_boxes": [],
                    "detection_confidences": [],
                    "message": "No human face was detected in this image. TruthLens is calibrated specifically for human facial deepfake and synthetic media analysis; assessments on non-facial media should not be treated as human deepfake evidence.",
                }

            valid_boxes = []
            valid_probs = []
            for i, box in enumerate(boxes):
                if box is not None:
                    prob = float(probs[i]) if probs is not None and probs[i] is not None else 0.0
                    valid_boxes.append([round(float(c), 1) for c in box])
                    valid_probs.append(round(prob, 4))

            count = len(valid_boxes)
            if count == 0:
                return {
                    "face_detected": False,
                    "face_count": 0,
                    "bounding_boxes": [],
                    "detection_confidences": [],
                    "message": "No human face was detected in this image. TruthLens is calibrated specifically for human facial deepfake and synthetic media analysis; assessments on non-facial media should not be treated as human deepfake evidence.",
                }

            return {
                "face_detected": True,
                "face_count": count,
                "bounding_boxes": valid_boxes,
                "detection_confidences": valid_probs,
                "message": f"{count} human face(s) detected and analyzed.",
            }
        except Exception as e:
            logger.warning(f"Error during face analysis: {e}")
            return {
                "face_detected": False,
                "face_count": 0,
                "bounding_boxes": [],
                "detection_confidences": [],
                "message": f"Face detection encountered an issue: {str(e)}",
            }
