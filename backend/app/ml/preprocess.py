from pathlib import Path

from PIL import Image
from torchvision import transforms


_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


def preprocess_image(image_path: Path):
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        return _TRANSFORM(rgb).unsqueeze(0)

