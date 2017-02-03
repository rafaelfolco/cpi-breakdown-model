## PMU data files

CBM creates files in this dir to store data for the PMU events.
One file is created for each sample and for a group of events, as
shown in the following example:
`0.GRP1`:

```
Events were actively counted for 11.7 seconds.
Event counts (scaled) for the whole system:
    Event                       Count                    % time counted
    PM_1PLUS_PPC_CMPL           746,654,474              57.13
    PM_CMPLU_STALL              4,055,345,362            71.42
    PM_CMPLU_STALL_THRD         484,701,395              28.58
    PM_GCT_NOSLOT_CYC           110,832,972              14.29
    PM_NTCG_ALL_FIN             551,322,414              28.58
    PM_RUN_CYC                  5,854,287,084            42.87
    PM_RUN_INST_CMPL            2,960,605,927            57.13
```
