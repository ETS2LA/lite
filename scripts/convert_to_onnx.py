import torch
import timm

checkpoint_path = r"C:\GitHub\ETS2LA-Lite\scripts\models\Model-2026-03-16-20-25-03.pt"

model = timm.create_model(
    "vit_small_patch16_224",
    pretrained=True,
    num_classes=1,
    img_size=(224, 224),
)

checkpoint = torch.load(
    checkpoint_path,
    map_location="cpu",
    weights_only=False,
)

if isinstance(checkpoint, torch.nn.Module):
    state_dict = checkpoint.state_dict()
elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
    state_dict = checkpoint["state_dict"]
else:
    state_dict = checkpoint

model.load_state_dict(state_dict)
model.eval()

example_input = torch.randn(1, 3, 224, 224)

onnx_program = torch.onnx.export(
    model,
    (example_input,),
    dynamo=True
)
onnx_program.save(checkpoint_path.replace(".pt", ".onnx"))