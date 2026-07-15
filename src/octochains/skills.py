#==============================================================================
#
# Copyright (c) 2026 Ahmad Varasteh (octochains). All rights reserved.
# Licensed under the Business Source License 1.1 (the "License");
#
# you may not use this file except in compliance with the License.
#
#==============================================================================

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

@dataclass
class Skill:
    """
    Represents a granular, procedural knowledge directive used to govern 
    an agent's reasoning bounds without utilizing external code tools.
    """
    name: str
    description: str
    version: str
    content: str

    @classmethod
    def from_file(cls, file_path: Path) -> 'Skill':
        """
        Loads and parses a SKILL.md file from the file system.
        
        Args:
            file_path: The Path object pointing to the target markdown file.
            
        Returns:
            An instantiated Skill dataclass object.
            
        Raises:
            FileNotFoundError: If the file does not exist at the target path.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Skill configuration file not found at: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        return cls.from_string(raw_text)

    @classmethod
    def from_string(cls, raw_text: str) -> 'Skill':
        """
        Parses raw text content to isolate frontmatter metadata from the core markdown.
        Enforces zero-dependency by parsing basic key-value fields without PyYAML.
        
        Raises:
            ValueError: If frontmatter limits are missing or the mandatory name field is absent.
        """
        cleaned_text = raw_text.strip()
        
        if not cleaned_text.startswith("---"):
            raise ValueError(
                "Malformed skill format. A valid SKILL.md must begin with a '---' frontmatter boundary."
            )
            
        # Split into exactly 3 structural segments: leading split, frontmatter block, and markdown content
        segments = cleaned_text.split("---", 2)
        if len(segments) < 3:
            raise ValueError(
                "Malformed skill format. Missing closing '---' frontmatter boundary delimiter."
            )
            
        frontmatter_block = segments[1].strip()
        markdown_content = segments[2].strip()
        
        metadata: Dict[str, str] = {}
        for line in frontmatter_block.splitlines():
            line = line.strip()
            
            # Skip completely empty entries or document notes
            if not line or line.startswith("#"):
                continue
                
            if ":" in line:
                key, val = line.split(":", 1)
                metadata[key.strip().lower()] = val.strip()

        name = metadata.get("name")
        description = metadata.get("description", "")
        version = metadata.get("version", "1.0.0")

        if not name:
            raise ValueError(
                "Invalid frontmatter configuration. The 'name' attribute is mandatory inside SKILL.md metadata."
            )

        return cls(
            name=name,
            description=description,
            version=version,
            content=markdown_content
        )