from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from .models import Symbol

class BaseParser(ABC):
    @property
    @abstractmethod
    def language_name(self) -> str:
        """The language name this parser handles, e.g. 'Python', 'JavaScript', 'TypeScript'."""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of file extensions, e.g. ['.js', '.jsx']."""
        pass

    @abstractmethod
    def parse(self, file_path: Path, relative_path: str) -> List[Symbol]:
        """Parse source file into structured symbols."""
        pass
