# cpi-breakdown-model
## CBM

CBM is a performance analysis tool for **system-wide** profiling based
on CPI - Cycles per Instruction - *Breakdown Model*.
It runs Oprofile Linux tool to collect PMU counters and calcutates CPI
metrics on Power Platform.
The tool helps profiling complex workloads and evaluating performance.

                              ,,                          
                             *MM                          
                              MM                          
                     ,p6"bo   MM,dMMb.  `7MMpMMMb.pMMMb.  
                    6M'  OO   MM    `Mb   MM    MM    MM  
                    8M        MM     M8   MM    MM    MM  
                    YM.    ,  MM.   ,M9   MM    MM    MM  
                     YMbmd'   P^YbmdP'  .JMML  JMML  JMML.

                   CPI Breakdown Model, a performance tool
              https://github.com/rafaelfolco/cpi-breakdown-model

### Requirements

 - oprofile (system-wide profiler for Linux systems)
 - python (2.7)

### Run

Run CBM *(as root)* for a given amount of time:
```sh
    # python cbm.py --duration=60 --rotation=5
```

This will run `CBM` for *60 minutes*  collecting *5 samples* of each
performance counter. Then open the HTML report  `html/cpi.html` in
a browser. You can start a simple HTTP server by running:

```sh
    # python -m SimpleHTTPServer
```

CBM HTML report will be available at:
`http://<hostname>:8000/html/cpi.html`

### Debug

Run CBM with `--debug`:
```sh
    # python cbm.py --duration=60 --rotation=5 --debug
```

### Methodology

Performance Monitoring Units (PMU)  are counted during the specified
duration time. These counters are collected by groups, divided into
time slices within the overall runtime.

```
  |-g1-g2-g3-g4-g5-|
  |--- runtime ----|
```

For long runs, its is possible to collect multiple samples in order
to get a more precise performance analysis of the running workload
over time.

```
  |-g1-g2-g3-g4-g5-|-g1-g2-g3-g4-g5-|...|-g1-g2-g3-g4-g5-|
  |     sample 1   |     sample 2   |...|    sample N    |
  |---------------------- runtime -----------------------|
```

CBM sums all samples from each group for every counter. CPI metrics
are finally calculated for each group of counters.

### TODOs

 - Write unit tests
 - Fix `RUN_CYCLES`: sum of Breakdown 1 metrics is not actually 100%
 - Show description for metrics and counters from breakdown table
