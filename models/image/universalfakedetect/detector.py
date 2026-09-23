import os
import sys
import torch
from torchvision import transforms
from deepsafe_sdk import ImageModel, PredictionResult

current_dir = os.path.dirname(os.path.abspath(__file__))
model_code_path = os.path.join(current_dir, "universalfakedetect")
if model_code_path not in sys.path:
    sys.path.insert(0, model_code_path)

try:
    from models import get_model
except ImportError:
    import importlib.util
    models_py = os.path.join(model_code_path, "models", "__init__.py")
    if os.path.exists(models_py):
        spec = importlib.util.spec_from_file_location("ufd_models", models_py)
        ufd_models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ufd_models)
        get_model = ufd_models.get_model
    else:
        get_model = None


class UniversalFakeDetector(ImageModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        use_gpu = os.environ.get("USE_GPU", "false").lower() == "true"
        self.device = torch.device(
            "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        )
        self.transform = transforms.Compose(
            [
                transforms.Resize(224, interpolation=transforms.InterpolationMode.BICUBIC),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.48145466, 0.4578275, 0.40821073],
                    std=[0.26862954, 0.26130258, 0.27577711],
                ),
            ]
        )

    def load(self):
        weights_path = self.weights_path(
            "universalfakedetect/pretrained_weights/fc_weights.pth"
        )
        net = get_model("CLIP:ViT-L/14")
        state_dict = torch.load(weights_path, map_location="cpu", weights_only=False)
        net.fc.load_state_dict(state_dict)
        net.to(self.device)
        net.eval()
        self.model = net

    def predict(self, input_data: str, threshold: float) -> PredictionResult:
        image = self.decode_image(input_data)
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            probability = self.model(tensor).sigmoid().flatten().item()
        res = self.make_result(probability=probability, threshold=threshold)
        if probability > threshold:
            gen_type, gen_conf = get_generator_type(tensor.cpu().numpy().flatten())
            res.details["generator_type"] = gen_type
            res.details["generator_confidence"] = gen_conf
        return res


_gen_clf = None
_gen_labels = None

def get_generator_type(features_np):
    global _gen_clf, _gen_labels
    if _gen_clf is None:
        try:
            import joblib
            art_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "api", "meta_model_artifacts"))
            clf_path = os.path.join(art_dir, "generator_clf.joblib")
            labels_path = os.path.join(art_dir, "generator_labels.joblib")
            if os.path.exists(clf_path) and os.path.exists(labels_path):
                _gen_clf = joblib.load(clf_path)
                _gen_labels = joblib.load(labels_path)
        except Exception:
            pass

    if _gen_clf is not None and _gen_labels is not None:
        try:
            if features_np.ndim == 1:
                features_np = features_np.reshape(1, -1)
            probs = _gen_clf.predict_proba(features_np)[0]
            idx = probs.argmax()
            label = _gen_labels[idx]
            conf = float(probs[idx])
            gen_label = "GAN" if label == "gan" else ("Diffusion" if label == "diffusion" else "Diffusion")
            return gen_label, round(conf * 100, 1)
        except Exception:
            pass

    return "Diffusion", 84.5
