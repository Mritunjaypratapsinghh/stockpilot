import logging
import sys


def setup_logger(name: str = "stockpilot") -> logging.Logger:
    log = logging.getLogger(name)
    if not log.handlers:
        log.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        
        fh = logging.FileHandler("stockpilot.log")
        fh.setFormatter(fmt)
        log.addHandler(fh)
        
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        log.addHandler(sh)
    
    return log


logger = setup_logger()
