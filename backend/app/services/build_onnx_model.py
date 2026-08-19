import os
import torch
import torchvision.models as models

def export_standalone_onnx():
    model_dir = os.path.dirname(os.path.abspath(__file__))
    onnx_path = os.path.join(model_dir, "image_fraud_model.onnx")

    print("Building MobileNetV3 model for 3-class fraud detection...")
    model = models.mobilenet_v3_small(weights=None)
    model.classifier[3] = torch.nn.Linear(model.classifier[3].in_features, 3)
    model.eval()

    dummy_input = torch.randn(1, 3, 224, 224)

    print(f"Exporting standalone ONNX model to: {onnx_path}")
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
        dynamo=False
    )
    print(f"SUCCESS: Model saved to {onnx_path} (Size: {os.path.getsize(onnx_path)} bytes)")

if __name__ == "__main__":
    export_standalone_onnx()
