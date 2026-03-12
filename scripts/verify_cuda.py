import torch
import sys

print("Python version:", sys.version)
print("PyTorch version:", torch.__version__)

print("\n--- CUDA CHECK ---")

cuda_available = torch.cuda.is_available()
print("CUDA available:", cuda_available)

if cuda_available:
    device_count = torch.cuda.device_count()
    print("GPU count:", device_count)

    for i in range(device_count):
        print(f"\nGPU {i}:")
        print("Name:", torch.cuda.get_device_name(i))
        print("Compute capability:", torch.cuda.get_device_capability(i))

        props = torch.cuda.get_device_properties(i)
        print("Total memory:", round(props.total_memory / 1024**3, 2), "GB")

    print("\nCurrent device:", torch.cuda.current_device())
    print("CUDA version (torch):", torch.version.cuda)

    # Test GPU tensor
    print("\n--- GPU TEST ---")
    x = torch.rand(3, 3).cuda()
    print("Tensor on GPU:\n", x)

else:
    print("CUDA not available. Using CPU.")