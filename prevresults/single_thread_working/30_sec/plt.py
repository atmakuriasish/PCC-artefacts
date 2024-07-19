import os
import re
import matplotlib.pyplot as plt

# Function to extract the required data from results.txt
def extract_tlb_miss_rate(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        match = re.search(r'TLB Miss Rate:\s*([\d.]+)', content)
        if match:
            return float(match.group(1))
    return None

# Get the current directory
current_dir = os.getcwd()

# Initialize lists to store the x and y values
x_values = []
y_values = []

# Iterate through all folders in the current directory
for folder_name in os.listdir(current_dir):
    folder_path = os.path.join(current_dir, folder_name)
    if os.path.isdir(folder_path):
        # Extract the number from the folder name
        if folder_name == 'none':
            x_value = 0
        else:
            match = re.search(r'pcc_128_(\d+)', folder_name)
            if match:
                x_value = int(match.group(1))
            else:
                continue

        # Path to the results.txt file
        results_file_path = os.path.join(folder_path, 'bfs_Kronecker_25/results.txt')

        # Extract the TLB Miss Rate from results.txt
        tlb_miss_rate = extract_tlb_miss_rate(results_file_path)
        if tlb_miss_rate is not None:
            x_values.append(x_value)
            y_values.append(round(tlb_miss_rate, 2))

# Sort the values based on the x_values
x_values, y_values = zip(*sorted(zip(x_values, y_values)))

# Plot the graph
plt.figure(figsize=(10, 6))
plt.plot(x_values, y_values, marker='o', linestyle='-', color='b')
plt.xlabel('Percentage of Hugepages')
plt.ylabel('TLB Miss Rate (%)')
plt.title('TLB Miss Rate vs Percentage of Hugepages')
plt.grid(True)
plt.savefig('res.png')
plt.show()
