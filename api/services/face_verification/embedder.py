import logging
from typing import Optional
import torch
import torch.nn.functional as F
from facenet_pytorch import InceptionResnetV1

logger = logging.getLogger(__name__)


class FaceEmbedder:
    """Generates 512-dimensional facial identity embeddings using InceptionResnetV1 (VGGFace2)."""

    def __init__(self, device: Optional[torch.device] = None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Initializing InceptionResnetV1 FaceEmbedder on device: {self.device}")
        self.model = InceptionResnetV1(pretrained="vggface2").eval().to(self.device)

    def extract_embeddings(self, face_tensors: torch.Tensor) -> torch.Tensor:
        """
        Generates L2-normalized embedding vectors for a batch of face tensors.

        Args:
            face_tensors: Tensor of shape (N, 3, 160, 160)

        Returns:
            Tensor of shape (N, 512) normalized embeddings on self.device
        """
        if face_tensors.device != self.device:
            face_tensors = face_tensors.to(self.device)

        with torch.no_grad():
            raw_embeddings = self.model(face_tensors)
            normalized_embeddings = F.normalize(raw_embeddings, p=2, dim=1)

        return normalized_embeddings
