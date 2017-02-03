#  Copyright 2017 IBM corp.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""Handle PMU events for CPI Breakdown Model (CBM)"""

import json
import logging
import math
import os
import re
import sys

from collections import defaultdict
from process import Command

log = logging.getLogger(__name__)
base_path = os.getcwd()


class PerformanceCounters:

    def __init__(self, runtime, rotation):
        # Raw PMU events
        self.raw_events = {}
        # Raw metrics
        self.raw_metrics = {}

        # CPI groups with collected data (dict of dicts)
        self.cpi_groups = {}
        # CPI metrics calculated
        self.cpi_metrics = {}

        self.rotation = rotation
        self.runtime = runtime

        self.data_path = os.path.join(base_path, 'dat')
        self.catalog_path = os.path.join(base_path, 'catalog')
        self.html_path = os.path.join(base_path, 'html')

        self.raw_events = self.load_json('pmu.json')
        self.raw_metrics = self.load_json('metrics.json')

    def sum_samples(self, counters):
        """Calculate average from samples for each counter."""
        sum_counters = {}
        for c in counters:
            sum_counters[c] = sum(counters[c])
        return sum_counters

    def parse_cpi_counters(self):
        """Parse PMU output file and return it as a dict."""
        for pmu_group in sorted(self.raw_events):
            if pmu_group == 'RUN':
                continue
            cpi_counters = defaultdict(list)
            for sample in range(self.rotation):
                cpi_file = os.path.join(self.data_path,
                                        "%d.%s" % (sample, pmu_group))
                log.debug('Parsing file %s...', cpi_file)
                with open(cpi_file, "r") as f:
                    try:
                        for line in f:
                            if line.lstrip().startswith("PM_"):
                                k, v, p = line.split()
                                # Get numbers from counter value 123,456,789
                                # oprofile's value is already scaled to 100%
                                # so percentage (time accounted) is ignored
                                value = int(v.replace(",", ""))

                                cpi_counters[k].append(value)
                                log.debug('%s[%d] = %d', k, sample, value)
                    except ValueError:
                        log.error("Error parsing PMU data: %s", ValueError)

            self.cpi_groups[pmu_group] = self.sum_samples(
                cpi_counters)

    def load_json(self, json_file):
        """Read PMU events or metrics from JSON file"""
        f = os.path.join(self.catalog_path, json_file)
        with open(f) as catalog:
            try:
                json_data = json.load(catalog)
            except Exception:
                log.error('Error loading %s: %s', json_file, Exception)
                sys.exit(0)
        return json_data

    def _print_catalog(self, catalog):
        """Print PMU events or CPI metrics from catalog"""
        log.debug('Loading catalog...')
        for pmu_group in catalog:
            log.debug("Loading PMU group %s", pmu_group)
            for item in catalog[pmu_group]:
                name = item.get("Name")
                description = item.get("Description")
                log.debug("Event: %s", name)
                log.debug("Description: %s", description)

    def calculate_cpi_metrics(self):
        """Calculate CPI metrics for the collected CPI counters"""
        self.parse_cpi_counters()
        self.calculate_run_cpi()
        for group in sorted(self.raw_metrics):
            if group == 'RUN':
                continue
            cpi_group = self.cpi_groups.get(group)
            for metric in self.raw_metrics[group]:
                # raw_formula contains the event names
                raw_formula = metric.get('Formula')
                metric_name = metric.get('Name')


                pattern = re.compile(
                    r'\b(' + '|'.join(cpi_group.keys()) + r')\b')
                # calc_formula contains math equation w/ numbers
                calc_formula = pattern.sub(
                    lambda x: "%d" % cpi_group[x.group()], raw_formula)

                # Load the math lib to eval formulas from catalog
                ns = vars(math).copy()
                # Clean namespace would prevent injection for normal users
                # No real effect for root users collecting system-wide events
                ns['__builtins__'] = None
                try:
                    log.debug("%s = [ %s ]", metric_name, calc_formula)
                    value = abs(int(eval(calc_formula, ns)))
                except:
                    log.error("%s couldn't be calculated.", metric_name)
                    value = 0
                    continue

                # PM_RUN_CYC is the base value for all metrics
                run_cpi = self.cpi_groups.get(group)['PM_RUN_CYC']
                percent = float(value) / float(run_cpi) * 100.0

                log.debug("\________| %d | %.2f |", value, percent)
                self.cpi_metrics[metric_name] = value, percent

    def calculate_run_cpi(self):
        """Calculate Run CPI: cycles per run instructions"""
        run_cyc = 0.0
        run_inst = 0.0
        for group in self.cpi_groups:
            # sum all run cycles and instructions from groups
            run_cyc += self.cpi_groups[group]['PM_RUN_CYC']
            run_inst += self.cpi_groups[group]['PM_RUN_INST_CMPL'] 
        self.cpi_metrics['RUN_CYC_CPI'] = (run_cyc, 100.0)
        cpi = float(run_cyc) / float(run_inst)
        self.cpi_metrics['RUN_CYC_INST_CPI'] = (0, cpi)

    def run_cpi(self):
        """Run profiler to collect CPI counters for PMU events"""
        cpi_groups = {}
        for pmu_group in self.raw_events:
            events = ','.join([x['Name'] for x in self.raw_events[pmu_group]])
            cpi_groups[pmu_group] = events

        # Group RUN is collected within all other groups, ignore it
        group_qty = len(cpi_groups) - 1
        group_interval = round((self.runtime / group_qty) / self.rotation)
        log.debug("Profile %d sample(s) of %d groups for %d seconds each.",
                  self.rotation, group_qty, group_interval)

        for sample in range(self.rotation):
            log.debug('Sample %d of %d: ', sample + 1, self.rotation)
            for pmu_group in sorted(cpi_groups):
                if pmu_group == 'RUN':
                    continue
                events = cpi_groups[pmu_group] + ',' + cpi_groups['RUN']
                pmu_file = os.path.join(self.data_path,
                                        "%d.%s" % (sample, pmu_group))
                log.debug("Profiling group %s", pmu_group)
                log.debug(events)
                Command(['ocount', '--system-wide', '-e', events, '-f',
                        pmu_file], group_interval)

    def breakdown_html(self):
        """Build CPI Breakdown Model into an HTML file"""
        ifn = os.path.join(self.html_path, 'cpi.html.template')
        ofn = os.path.join(self.html_path, 'cpi.html')
        pattern = re.compile(
            r'\b(' + '|'.join(self.cpi_metrics.keys()) + r')\b')
        with open(ifn, 'r') as ifile, open(ofn, 'w') as ofile:
            for line in ifile:
                rline = pattern.sub(
                    lambda x: "%.2f" % self.cpi_metrics[x.group()][1], line)
                ofile.write(rline)
