import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

# 로그 디렉토리 생성
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 로그 포맷 설정
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    log_level: str = "INFO",
    log_to_console: bool = True,
    log_to_file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
):
    """
    애플리케이션 로깅 설정
    
    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_console: 콘솔 출력 여부
        log_to_file: 파일 출력 여부
        max_bytes: 로그 파일 최대 크기 (바이트)
        backup_count: 백업 파일 개수
    """
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 기존 핸들러 제거
    root_logger.handlers.clear()
    
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # 콘솔 핸들러
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 파일 핸들러 (일반 로그)
    if log_to_file:
        # 일반 로그 파일 (크기 기반 로테이션)
        app_log_file = LOG_DIR / "app.log"
        file_handler = RotatingFileHandler(
            app_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 에러 로그 파일 (에러 레벨 이상만)
        error_log_file = LOG_DIR / "error.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        # 일별 로그 파일
        daily_log_file = LOG_DIR / "daily.log"
        daily_handler = TimedRotatingFileHandler(
            daily_log_file,
            when="midnight",
            interval=1,
            backupCount=30,  # 30일 보관
            encoding="utf-8",
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(formatter)
        daily_handler.suffix = "%Y-%m-%d"
        root_logger.addHandler(daily_handler)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거 가져오기
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
    
    Returns:
        Logger 인스턴스
    """
    return logging.getLogger(name)

