This repository has been created by me to make changes to an existing repository. I do not claim it to be my own work.

# Architectural Support for Optimizing Huge Page Selection Within the OS

To alleviate address translation overheads that memory-intensive irregular applications incur, we introduce a hardware-OS co-design to manage huge pages, which can effectively eliminate TLB misses when used efficiently. We design a novel hardware promotion candidate cache (PCC) to track huge page (2MB)-aligned regions that collectively incur the most page table walks from constituent base page accesses. We then decouple OS page promotion decisions from page data tracking performed by the PCC to alleviate the OS from scanning overheads and enable quicker promotion of candidates, especially when the system is under memory pressure and huge page resources are limited. This repository provides the workflow to evaluate this proposal. For further details, please refer to our manuscript referenced below.

**Reference:**
Aninda Manocha, Zi Yan, Esin Tureci, Juan Luis Aragón, David Nellans, Margaret Martonosi. Architectural Support for Optimizing Huge Page Selection Within the OS. In *Proceedings of the 56th International Symposium on Microarchitecture (MICRO)*. IEEE, 2023.

## Graph Applications

 1. **Breadth First Search (BFS)** - Given a starting (root) vertex, determine the minimum number of hops to all vertices. 

	In addition to its direct use in network analysis, e.g. LinkedIn degree separation, this algorithm also forms the basic building block of many other graph applications such as Graph Neural Networks, Connected Components, and Betweenness Centrality.
 2. **Single-Source Shortest Paths (SSSP)** - Given a starting (root) vertex, determine the minimum distance (sum of edge weights) to all vertices. 

	This algorithm is utilized in navigation and transportation problems as well as network utilization and its more general form is the $k$-shortest paths algorithm. 
 3. **PageRank (PR)** - Determine the "rank" or importance of all vertices (e.g. pages), where vertex scores are distributed to outgoing neighbors and updated until all scores converge, i.e. change by less than a threshold $\epsilon$. 

	Variants of this algorithm are used in ranking algorithms, e.g. of webpages, keywords, etc. 

The source codes for these applications are located in `launch/[APP NAME]`. These implementations are based on those from the [GraphIt framework](https://graphit-lang.org/).

## Datasets
We used the following datasets and their reordered variants:
1. **Kronecker_25** - synthetic power-law network
2. **Twitter** - real social network
3. **Sd1_Arc** - real web network

These datasets are stored in [Compressed Sparse Row (CSR) Format](https://en.wikipedia.org/wiki/Sparse_matrix) as binary files. Each dataset has the following files:

 - `num_nodes_edges.text` stores the number of vertices and edges in the network, which is used to determine the amount of data to dynamically allocate for the graph application before it is populated with values
 - `node_array.bin` stores values in the *vertex array*, which are the cumulative number of neighbors each vertex has
 - `edge_array.bin` stores values in the *edge array*, which are the neighbor IDs for each vertex (this array is indexed by the vertex array) 
 - `edge_values.bin` stores values in the *values array*, which are edge weights for the path to each vertex's neighbor, if such weights exist

We use the Kronecker network generator from the [GAP Benchmark Suite](http://gap.cs.berkeley.edu/benchmark.html) and the real-world networks are from [SuiteSparse](https://sparse.tamu.edu/) and [SNAP](http://snap.stanford.edu/).

All dataset files are available [here](https://decades.cs.princeton.edu/datasets/big/). They can be downloaded via `wget`. See instructions below ("Data Setup") on how to set up data. 

### Degree-Based Grouping (DBG)

We perform dataset preprocessing as a standalone, separate step and store the preprocessed datasets as binary files as well. The code to perform the preprocessing and generate the dataset files is available at `utils/dbg.cpp`. It takes in a dataset folder (storing the 4 files described above) and outputs a file `dbg.txt` storing the preprocessed dataset in edgelist format:

    cd utils
    make
    ./dbg [PATH_TO_DATASET_FOLDER]

`PATH_TO_DATASET_FOLDER` is the path to the original dataset to be preprocessed. The edgelist file `dbg.txt` then needs to be converted to a binary file. This can be achieved with the following commands:

    cd graph_conversion
    make
    mkdir [PREPROCESSED_DATASET_FOLDER]
    ./edgelist_to_binary ../dbg.txt [PREPROCESSED_DATASET_FOLDER]

`PREPROCESSED_DATASET_FOLDER` is the name of the preprocessed dataset where the 4 dataset files, `num_nodes_edges.text`, `node_array.bin`, `edge_array.bin`, and `edge_values.bin`, for the resulting preprocessed CSR will be created. Once the creation of this new dataset folder is complete, `dbg.txt` can be removed and the folder can be moved to the `data/` folder (after performing data setup) where all other datasets are stored.

For details on the DBG algorithm, see the reference below.

**Reference:**
Priyank Faldu, Jeff Diamond, and Boris Grot. [A Closer Look at Lightweight Graph Reordering](https://doi.org/10.1109/IISWC47752.2019.9041948). In *Proceedings of the 19th IEEE International Symposium on Workload Characterization (IISWC)*. IEEE, 2020, pages 1–13. 

## Other Applications

We also use memory-intensive applications *canneal* and *dedup* from the [PARSEC](https://parsec.cs.princeton.edu/) benchmark suite and *mcf*, *omnetpp*, and *xalancbmk* from the [SPEC2017](https://www.spec.org/cpu2017/) benchmark suite. For the PARSEC benchmarks, we use the *native* inputs and for the SPEC2017 benchmarks, we use the workload-specific datasets provided to measure runtime speed. We made modest modifications, e.g. argument parsing, to these applications to fit our workflow. If you would like these modified workloads to use with our workflow, please contact us.

## Experiments

### Prerequisites
 - Bash
 - C++ Boost libraries
 - Python3, matplotlib, and numpy
 - Linux v5.15
 - Linux Perf
 - numactl (and NUMA support)
 - Root access

### Linux Environment

You will need to build, install, and use a version of Linux kernel v5.15 we have modified to support support synchronous huge page promotion after pages fault in. The system call we introduced takes as input a range of data (formatted as a base address and offset) to synchronously promote, i.e. try to promote immediately. This is invoked in a similar fashion to madvise(), but is distinct in how the kernel operates; the kernel asynchronously scans ranges of data provided by madvise() and may not attempt to promote the data immediately after the system call is invoked. This new support is similar to a [recent kernel patchset from Google](https://lore.kernel.org/linux-mm/d098c392-273a-36a4-1a29-59731cdf5d3d@google.com/) allowing userspace promotions for experimental purposes.

First, clone the following repository:
`git clone https://github.com/amanocha/graphs_thp_linux.git`

Then compile and install the code:

```
cd graphs_thp_linux
cp config .config
sudo yum group install " Development Tools "
sudo yum install ncurses-devel bison flex elfutils-libelf-devel openssl-devel
make -j $ ( num_cores )
sudo make modules_install
sudo make install
sudo reboot
```

After reboot, verify that the code was installed correctly (you should see `5.15.0-rc6+`` as the kernel version):

```
uname -r
    5.15.0-rc6+
```

Linux’s perf tool is needed to measure TLB miss and page table walk rates. To install it, run the following commands:

```
cd graphs_thp_linux/tools/perf/
make -j $ ( num_cores )
cp perf /usr/bin/perf
```

### NUMA Effects

In order to avoid NUMA latency effects, e.g. a combination of local and remote access latencies interfere with experiments, our experimental methodology is designed such that all application memory is allocated and used from one NUMA node, while all data is stored on another. Therefore, one node must be reserved for data storage. We used node 0 and  recommend using a node such that the applications can run on another node that is not node 0. Another separate node must be reserved for application execution.

### Data Setup

All data must be stored in tmpfs to eliminate page cache effects. We have provided a script to automate the process of downloading the data and setting it up accordingly. To configure the tmpfs data to be pinned on a NUMA node other than node 0, edit line 4 in `setup.sh`:

    NUMA_NODE=0 # EDIT THIS VALUE (NUMA NODE) 

Then execute `sudo bash setup.sh`.

### Characterizing Reuse Distance

To perform characterizations of page data and determine which are best served by huge pages, navigate to `applications/reuse/`. To match the characterization to your machine (to approximate which data would incur TLB misses), you can run `cpuid | grep -i tlb` to determine the number of L2 TLB entries. You can then configure the L2 TLB size (number of entries) by modifying line 4 in `run.sh`:

`TLB_SIZE=1024`

Then execute `bash run.sh`. This will generate a `data/` folder within each graph application folder, which will store data tracking reuse distance at the 4KB, 2MB, and 1GB page granularities for each application/dataset configuration. There will also be a `figs/` folder generated for each graph application, which will store figures illustrating the categorization of page data for each application/dataset configuration overall and by data structure.

### Performance Evaluation

To accurately capture PCC hardware behavior, our evaluation is a two-step process consisting of first, offline hardware simulation to capture the 4KB virtual address regions that incur the most page table walks and model promotion of these regions, and second, online real-system performance evaluation that includes OS behavior and overheads. We compare our PCC proposal to an existing, software-based huge page management scheme, HawkEye. We model this scheme in our simulation framework and measure its performance in a similar two-step process. 

For more details on HawkEye, see the reference below.

**Reference:**
Ashish Panwar, Sorav Bansal, and K. Gopinath. [HawkEye: Efficient Fine-grained OS Support for Huge Pages](https://doi.org/10.1145/3297858.3304064). In *Proceedings of the 24th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS)*. ACM, 2019, pages 347–360.

#### Simulation

In the first step, we model and simulate the behavior of the CPU’s data TLB hierarchy (L1 and L2 TLBs), so that the PCC receives all page table walk information. We use [Intel’s Pin tool](TODO) to extract memory accesses during application execution and input these accesses into the simulated TLBs. The PCC tracks 2MB-aligned regions (where the tags are 2MB virtual address prefixes) that miss in the last-level TLB. Within the simulation, a periodic “promotion” process takes place every 30 seconds (calibrated based on the number of memory accesses per second observed in each application), extracting promotion candidates from the PCC and removing them as if they have been promoted. During TLB+PCC simulation, the PCC candidates are recorded. 

To run simulations independently, execute `sudo bash pin3.7/source/tools/run.sh [MODE] [CONFIG]` where `MODE` is either `pcc` or `hawkeye` and `CONFIG` is either `single_thread`, `sensitivity`, or `multithread` (we describe these configurations in more detail later).

#### Real-System Execution

In the second step, the promotion candidate addresses identified by the PCC are provided to the OS promotion logic at the correct time during workload execution. A low-overhead background thread performs userspace promotion system calls. We then measure the wall clock time of the application execution. This two-step process emulates a system setup with a hardware PCC identifying profitable promotion candidates and the OS periodically consuming the candidate information to perform promotions. This therefore demonstrates the real-system effect of these promotions, including all page promotion overheads.

To run real-system executions independently (assuming you have already collected the appropriate simulation data), execute `sudo python applications/go.py -x [CONFIG]` where `CONFIG` is either `hawkeye`, `single_thread_pcc`, `sensitivity`, or `multithread` (we describe these configurations in more detail later).

### Single-Thread Performance 

For all real-system experiments, navigate to the `applications/` folder. To run single-thread experiments, execute `sudo bash single_thread.sh`. This will perform all experiments to measure huge page utility for the PCC and HawkEye as well as performance when memory is fragmented.

#### Huge Page Utility
 
To measure how well the PCC approach optimizes huge page selection across different huge page availability in a system, we provide infrastructure to evaluate performance while limiting the number of huge pages used to back *N*% of the total application memory footprint, where *N* ranges from 0 (baseline), 1, 2, 4, ..., 64, ~100%, totaling 9 data points per utility curve. The ~100% configuration represents promotions occurring until 100% of all huge page candidates tracked in the PCC are promoted (the most aggressive case for our approach) yet the PCC might not have visibility of 100% of the total application footprint since TLB-friendly accesses may never experience page table walks. The utility curve demonstrates the effect of memory pressure or fragmentation limiting huge page resources and shows the effective utility of promoting additional huge pages in each application.

To gather simulation data for the PCC, execute the following:

`sudo bash ../pin3.7/source/tools/run.sh pcc single_thread`

And to gather simulation data for HawkEye, execute the following:

`sudo bash ../pin3.7/source/tools/run.sh hawkeye single_thread`

These will collect PCC and HawkEye data for each of the 9 huge page percentages for each application/dataset configuration. 

To measure real-system performance for the PCC, execute the following:

`sudo python go.py -x single_thread_pcc`

And to measure real-system performance for HawkEye, execute the following:

`sudo python go.py -x hawkeye`

These real-system performance runs need to be repeated with Linux THP enabled. To enable this policy, execute the following commands:

```
echo always > /sys/kernel/mm/transparent_hugepage/enabled
echo always > /sys/kernel/mm/transparent_hugepage/defrag
```

Once those experiments complete, Linux THP needs to be disabled, which can be done using the following commands:

```
echo madvise > /sys/kernel/mm/transparent_hugepage/enabled
echo madvise > /sys/kernel/mm/transparent_hugepage/defrag
```

Running `single_thread.sh` will automate the process of running all of these commands.

#### Realistic Scenario: Fragmented Memory

To demonstrate how the utility curves translate to a realistic scenario, e.g. where memory compaction often takes place to form contiguous physical memory regions for promotions, we evaluate the PCC approach when system memory is 50% and 90% fragmented and compare it to HawkEye and Linux. We provide infrastructure to fragment memory by allocating one non-movable page in every 2MB-aligned region. To run fragmented memory experiments, execute `sudo bash run_frag.sh`.

#### Sensitivity Analysis: PCC Size

We provide infrastructure to investigate the impact of the PCC size (4-1024 entries) on application performance.
To gather simulation data, execute the following:

`sudo bash ../pin3.7/source/tools/run.sh pcc sensitivity`

This will collect PCC promotion data for PCCs with 4, 8, 16, ..., 1024 entries for each of the three graph applications executing on each of the six datasets. If executed serially, these simulations can take a few weeks to complete. We suggest you launch this script multiple times on multiple cores to parallelize simulations (the script checks for duplicate simulations of the same configuration). If you would like to reduce the scope of this analysis, you can add a new, shortened dataset list (with the appropriate dataset data) after line 29 in `run.sh`, following the example in lines 31-34:

```
datasets=(Kronecker_25)
dataset_names=(kron25)
start_seeds=(0)
intervals=(732856447)
```

To measure real-system performance, execute the following:

`sudo python go.py -x sensitivity`

### Multithread

We also provide infrastructure to evaluate multi-threaded applications, where all threads belong to the same process and each thread runs on a different core with individual per-core PCCs. In this case, the OS gathers promotion information from multiple PCCs and makes huge page promotion decisions for a single process, because all threads share the same address space. In our evaluation, we compare two different OS policies when selecting huge page candidates from multiple PCCs: 

1. **Highest PCC Frequency** selects promotion candidates with the globally highest PCC frequencies.
2. **Round Robin** selects candidates so that huge pages are equally distributed across the threads. Unless a thread runs out of candidates in its PCC, huge pages will always be distributed evenly amongst threads.

To perform evaluations of multi-threaded applications, execute `sudo bash multithread.sh`. This performs simulation via `sudo bash ../pin3.7/source/tools/run.sh pcc multithread` and real-system evaluation via `sudo python go.py -x multithread`.

## Results

If the experiment scripts were used, all results are stored in the `results/` folder. The folder organization can be summarized as follows:

	- single_thread
        - 30_sec
            - none (baseline)
            - pcc_N_P (N = PCC size [4, 8, 16, ..., 1024], P = percentage of memory footprint promoted [1, 2, 4, ..., 64, 100])
            - hawkeye_P (P = percentage of memory footprint promoted [1, 2, 4, ..., 64, 100])
            - thp (all data backed with huge pages)
    - frag50 (50% memory fragmentation)
        - 30_sec
            - none (baseline)
            - hawkeye (HawkEye, trying to promote as many huge pages as possible)
            - pcc_128_100 (128-entry PCC, trying to promote as many huge pages as possible)
            - pcc_128_100_demote (128-entry PCC, trying to promote as many huge pages as possible with demotion in place)
            - thp (Linux THP)
    - frag90 (90% memory fragmentation)
        - 30_sec
            - none (baseline)
            - hawkeye (HawkEye, trying to promote as many huge pages as possible)
            - pcc_128_100 (128-entry PCC, trying to promote as many huge pages as possible)
            - pcc_128_100_demote (128-entry PCC, trying to promote as many huge pages as possible with demotion in place)
            - thp (Linux THP)
    - multithread
        - 30_sec
            - T_threads (T = number of threads [2, 4, 8, 16])
                - none (baseline)
                - pcc_N_P_X (N = PCC size [128], P = percentage of memory footprint promoted [1, 2, 4, ..., 64, 100], X = huge page distribution policy [0, 1])
                - thp (all data backed with huge pages)

Within each folder, there are application/dataset experiment folders named as `application_dataset/`. When an experiment is in progress or not completed, the folder name will be `tmp_application_dataset/` until the experiment fully completes, i.e. all application executions complete and their results are parsed and aggregated. Within each complete application/dataset experiment folder, the following files are generated:

    - compiler_output.txt (compilation standard output)
    - compiler_err.txt (compilation standard error output)
    - access_output_x_i.txt (number of anonymous and huge pages over time)
    - app_output_x_i.txt (application standard output)
    - err_output_x_i.txt (application standard error output)
    - measurements_output_i.txt (metric values from perf)
    - perf_output_x_i.txt (perf output)
    - pf_output_x_i.txt (page faults over time)
    - results_output_i.txt (results output)
    - results.txt (average results output)     

`x` represents the huge page setting (e.g. 0 for baseline and THP, 21 for HawkEye and PCC) and `i` is the iteration number (each experiment is run 3 times, or 5 for fragmented memory evaluations). 

The runtimes for a given execution will be at the bottom of `app_output_x_i.txt` and appear as follows:

    total kernel computation time: [TIME_IN_SECONDS]
    user time: [USER_TIME_IN_SECONDS]
    kernel time: [KERNEL_TIME_IN_SECONDS]

The TLB miss rates for a given execution will be at the top of `results_i.txt` and appear as follows:

    TLB:
    TLB Miss Rate: [%]
    STLB Miss Rate: [%]
    Page Fault Rate: [%]
    Percent of TLB Accesses with PT Walks: [%]
    Percent of TLB Accesses with Completed PT Walks: [%]
    Percent of TLB Accesses with Page Faults: [%]

The average TLB statistics will be recorded in `results.txt`.

## Contact
Aninda Manocha: amanocha@princeton.edu
