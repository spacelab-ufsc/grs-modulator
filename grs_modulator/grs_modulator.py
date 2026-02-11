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
import numpy as np

from grs_modulator.gmsk import GMSK
from grs_modulator.usrp import USRP
from grs_modulator.pluto import Pluto 

class GRSModulator:
    """
    GRS Modulator
    """
    def __init__(self):
        """
        """
        self._args = self._parse_args()
        self._logger = self._setup_logging()
        self._config = self._create_config()


        self._init_zmq()
        self._sdr = self._init_sdr()
        self._modem = self._init_modem()

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
        parser.add_argument("--gain", type=int, default=-10,
                            help="Gain in dB (default: -10 dB). For Pluto range is 0 to -90.")
        parser.add_argument("--zmq-host", type=str, default="tcp://localhost:5555",
                            help="ZMQ Publisher address (default: tcp://localhost:5555)")
        parser.add_argument("--zmq-topic", type=str, default="tx_data",
                            help="ZMQ Topic to subscribe to (default: tx_data)")
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
        Initialize ZMQ Subscriber
        """
        self._zmq_ctx = zmq.Context()
        self._in_socket = self._zmq_ctx.socket(zmq.SUB)

        self._logger.info(f"Connecting to ZMQ Publisher at {self._args.zmq_host}")
        self._in_socket.connect(self._args.zmq_host)
        
        topic = self._args.zmq_topic
        self._logger.info(f"Subscribing to topic: '{topic}'")
        self._in_socket.setsockopt_string(zmq.SUBSCRIBE, topic)

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

    def _init_sdr(self):
        """
        Initialize the SDR
        """
        sdr_type = self._config["sdr"].lower()
        self._logger.info(f"Initializing SDR type: {sdr_type}")
        
        if sdr_type == "usrp":
            return USRP(
                sample_rate=self._config["sample_rate"], 
                gain=self._config["gain"]
            )
        elif sdr_type == "pluto":
            return Pluto(
                sample_rate=self._config["sample_rate"], 
                gain=self._config["gain"]
            )
        else:
            self._logger.error(f"Unknown SDR type: {sdr_type}")
            sys.exit(1)

    def _init_modem(self):
        """
        Initialize GMSK modem
        """
        L = 100 
        baud_rate = self._config["sample_rate"] / L
        bt = 0.5 
        
        self._logger.info(f"Initializing GMSK: Baud={baud_rate}, BT={bt}")
        return GMSK(bt=bt, baud=baud_rate)

    def run(self):
        """
        Modulates data and then transmits it through the SDR
        """
        self._logger.info("GRS Modulator is now running")
        self._logger.info("GRS Modulator loaded config " + json.dumps(self._config, indent=4, sort_keys=True, default=str))

        try:
            while True:
                topic_bytes, msg_bytes = self._in_socket.recv_multipart()
                
                data_integers = list(msg_bytes)
                
                # Modulate
                iq_samples, fs, dur = self._modem.modulate(data_integers)
                
                # Transmit
                self._sdr.transmit(
                    samples=iq_samples, 
                    dur=dur, 
                    rate=fs, 
                    freq=self._config["frequency"]
                )

        except KeyboardInterrupt:
            self._logger.warning("Interrupt signal was received! Exiting...")
        except Exception as e:
            self._logger.error(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._in_socket.close()
            self._zmq_ctx.term()

if __name__ == "__main__":
    app = GRSModulator()
    app.run()