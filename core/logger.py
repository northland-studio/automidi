import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    _instance: Optional['Logger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is not None:
            return
        
        self._logger = logging.getLogger('AutoMidi')
        self._logger.setLevel(logging.DEBUG)
        
        self._logger.handlers.clear()
        
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        log_filename = datetime.now().strftime('automidi_%Y%m%d.log')
        log_path = log_dir / log_filename
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self._logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)
        
        self._log_path = str(log_path)
    
    @property
    def logger(self) -> logging.Logger:
        return self._logger
    
    @property
    def log_path(self) -> str:
        return self._log_path
    
    def debug(self, message: str):
        self._logger.debug(message)
    
    def info(self, message: str):
        self._logger.info(message)
    
    def warning(self, message: str):
        self._logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        self._logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = True):
        self._logger.critical(message, exc_info=exc_info)
    
    def exception(self, message: str):
        self._logger.exception(message)


logger = Logger()


def get_logger() -> Logger:
    return logger
