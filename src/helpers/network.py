"""
Network Utilities - Global Helpers
Handles port management and process termination.
"""

import os
import signal
import subprocess
import shlex
import time
import logging
from typing import List

logger = logging.getLogger(__name__)

def get_pids_on_port(port: int) -> List[int]:
    """Get all PIDs listening on a specific port"""
    try:
        # lsof -t -i:<port> returns only the PIDs
        cmd = f"lsof -t -i:{port}"
        output = subprocess.check_output(shlex.split(cmd), text=True)
        return [int(pid) for pid in output.strip().split('\n') if pid.strip()]
    except subprocess.CalledProcessError:
        # No process found on this port (returns exit code 1)
        return []
    except Exception as e:
        logger.error(f"Error finding PIDs on port {port}: {e}")
        return []

def kill_process_on_port(port: int) -> bool:
    """Find and kill processes running on a specific port"""
    pids = get_pids_on_port(port)
    if not pids:
        return False

    logger.info(f"Cleaning up {len(pids)} process(es) on port {port} (PIDs: {pids})")
    
    success = True
    for pid in pids:
        try:
            logger.warning(f"Killing process {pid} on port {port}...")
            # Try SIGTERM first
            os.kill(pid, signal.SIGTERM)
            
            # Wait a bit and check
            time.sleep(0.1)
            try:
                os.kill(pid, 0) # Still alive?
                os.kill(pid, signal.SIGKILL) # Force it
            except OSError:
                pass # Already dead
                
        except ProcessLookupError:
            pass # Already gone
        except Exception as e:
            logger.error(f"Failed to kill process {pid}: {e}")
            success = False
            
    # CRITICAL: Wait for OS to release the port
    if pids:
        logger.info(f"Waiting for OS to release port {port}...")
        for _ in range(5): # Max 1 second
            time.sleep(0.2)
            if not get_pids_on_port(port):
                logger.info(f"Port {port} is now free.")
                return True
        
        logger.warning(f"Port {port} still appears to be in use.")
            
    return success
