#
#  grs_modulator.py
#  
#  Copyright The GRS Modulator Contributors.
#  
#  This file is part of GRS Modulator.
#
#  GRS Modulator is free software; you can redistribute it
#  and/or modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  
#  GRS Modulator is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public
#  License along with GRS Modulator; if not, see <http://www.gnu.org/licenses/>.
#  
#

import argparse
import logging
import json
import sys
import zmq

from grs_modulator.gmsk import GMSK
from grs_modulator.usrp import USRP
from grs_modulator.pluto import Pluto 

class GRSModulator:
    """
    TODO
    """
    def __init__(self):
        """
        """
        # Parse command line arguments
        self._args = self._parse_args()

        # Setup logging
        self._logger = self._setup_logging()

        # Create config
        self._config = self._create_config()

        # Setup ZMQ
        self._init_zmq()

    def _parse_args(self):
        parser = argparse.ArgumentParser(description="GRS Modulator")
        parser.add_argument("--mod", type=str, default="gmsk", 
                            help="Modulation (default: gmsk) [options: gmsk]")
        parser.add_argument("--freq", type=float, default=145.9e6, 
                            help="Center frequency in Hz (default: 145.9e6)")
        parser.add_argument("--sample-rate", type=float, default=1e6,
                            help="Sample rate (default: 1 MHz)")
        parser.add_argument("--sdr", type=str, default="usrp",
                            help="SDR to transmit (default: usrp) [options: usrp, pluto]")
        parser.add_argument("--gain", type=int, default=-90,
                            help="Gain in dB (default: -90 dB)[Warning: This option is SDR dependent!]")
        parser.add_argument("--logging", action='store_true',
                            help="Enable logging (default: False)")

        args = parser.parse_args()

        return args

    def _setup_logging(self, level=logging.INFO):
        formatter = logging.Formatter(
            fmt='[%(asctime)s][%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%SZ'
        )
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        
        logger = logging.getLogger(__name__)
        logger.setLevel(level)
        logger.addHandler(handler)
        
        return logger
        
    def _init_zmq(self):
        """
        """
        self._zmq_ctx = zmq.Context()

        self._in_socket = self._zmq_ctx.socket(zmq.REP)

        self._in_socket.bind("tcp://*:5600")   # Bind to all interfaces on port 5600

    def _create_config(self):
        """
        """
        config = {
            "frequency": self._args.freq,
            "gain": self._args.gain,
            "sdr": self._args.sdr,
            "logging": self._args.logging,
            "sample_rate": self._args.sample_rate,
            "modulation": self._args.mod,
        }

        return config

    def run(self):
        """
        :return: None.

        """
        self._logger.info("GRS Modulator is now running")

        self._logger.info("GRS Modulator loaded config " + json.dumps(self._config, indent=4, sort_keys=True, default=str))

        try:
            while True:
                message = self._in_socket.recv_string()
                print(f"Received message: {message}")

        except KeyboardInterrupt:
            self._logger.warning("Interrupt signal was received! Exiting...")
        finally:
            self._in_socket.close()
            self._zmq_ctx.term()
