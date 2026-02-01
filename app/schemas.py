from enum import Enum

from pydantic import BaseModel, Field


class Element(BaseModel):
    id: str = Field(...)
    selector: str = Field(...)

class ErrorType(str, Enum):
    """Enum for categorizing types of errors."""

    ELEMENT_NOT_FOUND = "element_not_found"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    JAVASCRIPT_ERROR = "javascript_error"
    UNKNOWN = "unknown"


class BrowserConfig(BaseModel):
    """Browser configuration from client"""

    use_proxy: bool = False
    block_images: bool = True
    block_css: bool = False
    headless: bool = False

    @classmethod
    def is_default(cls, conf) -> bool:
        """Check if this is default configuration"""
        if not isinstance(conf, cls):
            return False
        return conf.model_dump() == cls().model_dump()
