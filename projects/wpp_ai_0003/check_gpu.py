# Conteúdo de check_gpu.py
import onnxruntime as ort
print(f"ONNX Runtime device: {ort.get_device()}")
print(f"Available providers: {ort.get_available_providers()}")