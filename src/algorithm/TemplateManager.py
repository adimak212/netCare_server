import os
import json


class TemplateManager:
    _templates = None
    _filepath = ""

    @classmethod
    def init(cls, filepath: str):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Templates file not found: {filepath}")

        cls._filepath = filepath

        with open(filepath, "r") as f:
            data = json.load(f)

        cls._templates = data

    @classmethod
    def all(cls):
        if cls._templates is None:
            raise RuntimeError("TemplateManager not initialized.")
        return cls._templates

    @classmethod
    def get(cls, template_id: str):
        if cls._templates is None:
            raise RuntimeError("TemplateManager not initialized.")

        if template_id not in cls._templates:
            raise KeyError(f"Template '{template_id}' not found.")

        return cls._templates[template_id]
