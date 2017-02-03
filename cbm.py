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
"""CBM (CPI Breakdown Model)"""

import argparse
import logging

from pmu import PerformanceCounters

# Runtime
MIN_DURATION = 1

# Samples
MIN_ROTATION = 1


def main():
    parser = argparse.ArgumentParser(description='CBM (CPI Breakdown Model)')
    parser.add_argument('--duration', type=int,
                        help='Duration (in minutes) for collecting CPI PMU'
                             ' events. Minimum: 1 min.')
    parser.add_argument('--rotation', type=int,
                        help='Number of samples to rotate around PMU'
                             ' counters. Minimum: 1 sample.')
    parser.add_argument('--debug', action='store_true',
                        help='Enable DEBUG mode.')
    args = parser.parse_args()

    logformat = '%(asctime)s %(levelname)s %(name)s:  %(message)s'
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=logformat)
    else:
        logging.basicConfig(level=logging.INFO, format=logformat)
    log = logging.getLogger(__name__)

    _duration = max(args.duration, MIN_DURATION)
    duration = 60 * _duration

    _rotation = max(args.rotation, MIN_ROTATION)
    rotation = min(_duration, _rotation)

    if _duration != args.duration:
        log.debug("Enforcing duration = %d minute(s).", _duration)

    if rotation != args.rotation:
        log.debug("Enforcing rotation = %d sample(s).", rotation)

    pmu = PerformanceCounters(duration, rotation)

    pmu.run_cpi()
    pmu.calculate_cpi_metrics()
    pmu.breakdown_html()
    log.info("CPI = %f", pmu.cpi_metrics['RUN_CYC_INST_CPI'][1])

if __name__ == '__main__':
    main()
