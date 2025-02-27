import os
import numpy as np
import subprocess

def read_binary_file(filename, dtype):
    """Read a binary file and return its contents as a numpy array."""
    with open(filename, 'rb') as f:
        data = f.read()
    return np.frombuffer(data, dtype=dtype)

def csr_to_wel(node_array, edge_array, edge_values, output_file):
    """Convert CSR format to a weighted edge list and write directly to .wel file."""
    num_nodes = len(node_array) - 1

    with open(output_file, 'w') as f:
        for src in range(num_nodes):
            start = node_array[src]
            end = node_array[src + 1]
            for dst_idx in range(start, end):
                dst = edge_array[dst_idx]
                weight = edge_values[dst_idx]
                f.write(f"{src} {dst} {weight}\n")

def convert_to_wsg(wel_file, wsg_file, converter_path):
    """Convert .wel file to .wsg file using GAPBS converter."""
    command = [converter_path, "-s", wel_file, wsg_file]
    subprocess.run(command, check=True)

def main():
    # Paths to your dataset files
    node_array_file = "node_array.bin"
    edge_array_file = "edge_array.bin"
    edge_values_file = "edge_values.bin"  # Edge weights file
    output_wel_file = "Kronecker_25.wel"
    output_wsg_file = "Kronecker_25.wsg"

    # Expand ~ to the full home directory path
    converter_path = os.path.expanduser("~/gapbs/converter")

    # Read binary files
    node_array = read_binary_file(node_array_file, dtype=np.uint32)
    edge_array = read_binary_file(edge_array_file, dtype=np.uint32)
    edge_values = read_binary_file(edge_values_file, dtype=np.float32)  # Assuming weights are float32

    # Convert CSR to weighted edge list and write directly to .wel file
    csr_to_wel(node_array, edge_array, edge_values, output_wel_file)
    print(f"Weighted edge list saved to {output_wel_file}")

    # Convert .wel to .wsg using GAPBS converter
    convert_to_wsg(output_wel_file, output_wsg_file, converter_path)
    print(f"Weighted graph binary saved to {output_wsg_file}")

if __name__ == "__main__":
    main()