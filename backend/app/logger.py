import logging
import sys

def setup_logger(name: str = "stockpilot") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        
        fh = logging.FileHandler("stockpilot.log")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        logger.addHandler(sh)
    
    return logger

logger = setup_logger()
