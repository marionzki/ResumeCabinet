import uuid
from dataclasses import dataclass, field
from typing import List

@dataclass
class Module:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True

    def to_dict(self):
        return {
            "id": self.id,
            "is_active": self.is_active,
            "type": self.__class__.__name__
        }

    @classmethod
    def from_dict(cls, data):
        # Base implementation, overridden in subclasses or handled by factory
        pass

@dataclass
class TextModule(Module):
    title: str = ""
    text_extended: str = ""
    text_summary: str = ""
    use_summary: bool = False # True = Summary, False = Extended
    hyperlinks: List[dict] = field(default_factory=list) # List of {start, end, url}
    translations: dict = field(default_factory=dict) # {lang_code: {field: value}}

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "title": self.title,
            "text_extended": self.text_extended,
            "text_summary": self.text_summary,
            "use_summary": self.use_summary,
            "hyperlinks": self.hyperlinks,
            "translations": self.translations
        })
        return data

@dataclass
class ExperienceModule(TextModule):
    company: str = ""
    date_range: str = ""
    tags: List[str] = field(default_factory=list) # List of tag IDs or Names

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "company": self.company,
            "date_range": self.date_range,
            "tags": self.tags
        })
        return data

@dataclass
class EducationModule(TextModule):
    company: str = "" # Institution
    date_range: str = ""
    tags: List[str] = field(default_factory=list) # List of tag IDs or Names
    hide_text: bool = False # Option to hide extended/summary text

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "company": self.company,
            "date_range": self.date_range,
            "tags": self.tags,
            "hide_text": self.hide_text
        })
        return data

@dataclass
class ImageModule(Module):
    name: str = ""
    image_path: str = ""

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "name": self.name,
            "image_path": self.image_path
        })
        return data

@dataclass
class PersonalInfoModule(TextModule):
    # Specialized for Bio/Description
    pass

@dataclass
class AvatarModule(Module):
    image_path: str = ""

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "image_path": self.image_path
        })
        return data
