import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Type

from .modules import (
    Module, TextModule, ExperienceModule, ImageModule, 
    PersonalInfoModule, AvatarModule, EducationModule
)

@dataclass
class Section:
    id: str
    title: str
    modules: List[Module] = field(default_factory=list)
    type: str = "generic" # generic, experience, education, software, language, personal

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "modules": [m.to_dict() for m in self.modules]
        }

    @classmethod
    def from_dict(cls, data):
        section = cls(id=data["id"], title=data["title"], type=data.get("type", "generic"))
        module_list = []
        for m_data in data["modules"]:
            # Factory logic
            m_type = m_data.get("type")
            
            # Migration/Correction for Education section
            if section.type == "education" and m_type != "EducationModule":
                 # Upgrade old TextModule to EducationModule
                 m_type = "EducationModule"

            if m_type == "ExperienceModule":
                mod = ExperienceModule(**{k: v for k, v in m_data.items() if k != "type"})
            elif m_type == "EducationModule":
                 # Ensure we don't pass unexpected keys if source was TextModule (it shouldn't have extras, but let's be safe)
                 # TextModule keys are subset.
                 # Filter to valid fields for EducationModule? Dataclass init doesn't like extra keys.
                 # Actually TextModule fields are subset.
                 valid_keys = {"id", "is_active", "title", "text_extended", "text_summary", "use_summary", "hyperlinks", "company", "date_range", "translations", "tags", "hide_text"}
                 filtered_data = {k: v for k, v in m_data.items() if k in valid_keys}
                 mod = EducationModule(**filtered_data)
            elif m_type == "ImageModule":
                mod = ImageModule(**{k: v for k, v in m_data.items() if k != "type"})
            elif m_type == "PersonalInfoModule":
                mod = PersonalInfoModule(**{k: v for k, v in m_data.items() if k != "type"})
            elif m_type == "AvatarModule":
                mod = AvatarModule(**{k: v for k, v in m_data.items() if k != "type"})
            else:
                mod = TextModule(**{k: v for k, v in m_data.items() if k != "type"})
            
            module_list.append(mod)
        section.modules = module_list
        return section

@dataclass
class HeaderInfo:
    name: str = ""
    job_position: str = ""
    certifications: str = ""
    city: str = ""
    country: str = ""
    email: str = ""
    phone: str = ""
    others: str = ""
    linkedin: str = ""
    translations: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

@dataclass
class Settings:
    language: str = "Español" # Español, Inglés, Gallego, Catalán

    def to_dict(self):
        return asdict(self)

@dataclass
class CVData:
    settings: Settings = field(default_factory=Settings)
    header_info: HeaderInfo = field(default_factory=lambda: HeaderInfo(
        name="Mario Noriega Zamora",
        job_position="Procedural 3D Artist",
        certifications="",
        city="Madrid",
        country="España",
        email="mnoriegazamora@gmail.com",
        phone="699651797",
        others="",
        linkedin="https://www.linkedin.com/in/mario-noriega-zamora/"
    ))
    # Individual sections
    personal_info: Section = field(default_factory=lambda: Section(id="personal", title="Información Personal", type="personal", modules=[
        PersonalInfoModule(title="Bio", text_extended="Soy una persona curiosa y orientada a la resolución de problemas, con gran capacidad de adaptación y trabajo en equipo. Me apasiona el desarrollo de soluciones creativas a través de la programación, combinando mi experiencia en entornos 3D y simulación con el uso de lenguajes como Python, C++ y programación orientada a objetos. Mi objetivo es seguir creciendo en el ámbito del desarrollo de software y la programación, adquiriendo nuevas competencias que me permitan afrontar proyectos cada vez más complejos en simulación, automatización y generación procedural.")
    ]))
    experience: Section = field(default_factory=lambda: Section(id="experience", title="Experiencia Profesional", type="experience", modules=[
        ExperienceModule(
            title="Operador de cámara", 
            company="Plateros producciones - Salamanca, España", 
            date_range="05/2008 – 06/2008",
            text_extended='Grabación de piezas audiovisuales para los documentales: "De la dehesa a la mesa" y "Cinco pueblos patrimonio vivo". http://platerosmultimedia.com/documentales/',
            tags=["Grabación de vídeo"]
        ),
        ExperienceModule(
            title="Redactor de noticias", 
            company="Región digital - Mérida, España", 
            date_range="08/2008 – 09/2008",
            text_extended="Redactor en prácticas cubriendo las noticias locales con redacción de noticias, reportajes y crónicas.",
            tags=["Prensa escrita"]
        ),
        ExperienceModule(
            title="Redactor de deportes", 
            company="La Gaceta de Salamanca - Salamanca, España", 
            date_range="10/2008 – 05/2009",
            text_extended="Redactor en prácticas. Redacción de crónicas, noticias y entrevistas para el periódico, así como la cobertura de los resultados de las categorías inferiores.",
            tags=["Prensa escrita"]
        ),
        ExperienceModule(
            title="Becario en Departamento de televisión", 
            company="Universidad Pontificia de Salamanca - Salamanca, España", 
            date_range="10/2007 – 06/2009",
            text_extended="Grabación de eventos y edición de piezas con Avid Liquid y Sony Vegas",
            tags=["Diseño gráfico", "Edición"]
        ),
        ExperienceModule(
            title="Redactor de deportes", 
            company="El Periódico Extremadura - Cáceres, España", 
            date_range="07/2009 – 08/2009",
            text_extended="Redactor de deportes en prácticas cubriendo el periodo de fichajes y el ascenso de los equipos extremeños a 2ªB. Redacción de crónicas y entrevistas de diversos deportes.",
            tags=["Prensa escrita"]
        ),
        ExperienceModule(
            title="Becario de Diseño Gráfico", 
            company="Ochoimedio Estudio - Cáceres, España", 
            date_range="07/2010 – 08/2010",
            text_extended="Especialización en diseño de imagen corporativa y creación de imagen y papelería para campañas publicitarias de la Consejería de Extremadura para los Jóvenes y el Deporte. Edición web y gestión de contenidos con Wordpress y Joomla.",
            tags=["Branding", "Adobe Photoshop", "Photoshop", "Diseño gráfico"]
        ),
        ExperienceModule(
            title="Atención al cliente en Redes Sociales", 
            company="Atento Comunicaciones - Cáceres, España", 
            date_range="01/2012 – 09/2017",
            text_extended="Atención en Twitter y Facebook de clientes a través de gestores de redes sociales. Recopilación y análisis de datos de tráfico y feedback para la elaboración de la estrategia Social Media.",
            tags=["Medios sociales"]
        ),
        ExperienceModule(
            title="Gestor de recepción de alarmas", 
            company="Securitas Seguridad España - Madrid, España", 
            date_range="05/2018 - 08/2018",
            text_extended="Recepción de saltos de alarma en turno de noche y toma de decisiones inmediata en función de la situación específica.",
            tags=[]
        ),
        ExperienceModule(
            title="Teleoperador", 
            company="Quirón Salud - Madrid, España", 
            date_range="05/2020 - 03/2021",
            text_extended="Cierre de citas en los centros de Quirón Salud de toda España.",
            tags=["Gestión de agendas médicas"]
        ),
        ExperienceModule(
            title="Procedural 3D artist", 
            company="Computer Visión Center - Madrid, España", 
            date_range="10/2020 - 03/2024",
            text_extended='Generación procedural de entornos urbanos y naturales para proyectos de conducción autónoma basada en IA. Desarrollo propio de widgets y blueprints en Unreal y assets en Houdini FX. Co-autor en el dataset: "All for One, and One for All: UrbanSyn Dataset, the third Musketeer of Synthetic Driving Scenes" https://www.urbansyn.org.',
            tags=["Posproducción de vídeo", "Adobe Premiere Pro", "3D", "Unreal Engine 4.27", "Houdini FX", "C++", "Diseño gráfico", "Python", "Edición de vídeo"]
        ),
        ExperienceModule(
            title="Procedural 3D artist", 
            company="Universidade da Coruña (CITIC) - A Coruña, España", 
            date_range="04/2025 - 05/2025",
            text_extended="",
            tags=["Houdini FX", "Diseño gráfico", "Python", "Rendering for autonomous driving"]
        )
    ]))
    education: Section = field(default_factory=lambda: Section(id="education", title="Formación", type="education", modules=[
        EducationModule(title="Licenciado en Comunicación Audiovisual", company="Universidad Pontificia de Salamanca - Salamanca, España", date_range="2003 – 2009", text_extended=""),
        EducationModule(title="Posgrado de Experto en Locución Audiovisual", company="Universidad Pontificia de Salamanca - Salamanca, España", date_range="2009 – 2009", text_extended=""),
        EducationModule(title="Curso de Diseño Gráfico (500h)", company="Academia Innovartex - Cáceres, España", date_range="2009 - 2010", text_extended=""),
        EducationModule(title="Curso Superior en Community Manager", company="Escuela de Negocios Europea de Barcelona - Barcelona, España", date_range="10/2017 - 12/2017", text_extended=""),
        EducationModule(title="Curso Superior en Posicionamiento Web", company="Escuela de Negocios Europea de Barcelona - Barcelona, España", date_range="12/2017 - 02/2018", text_extended=""),
        EducationModule(title="Curso Superior en e-Commerce y Marketing", company="Escuela de Negocios Europea de Barcelona - Barcelona, España", date_range="02/2018 - 04/2018", text_extended=""),
        EducationModule(title="Máster en Composición y VFX (600h)", company="Escuela Trazos - Madrid, España", date_range="10/2018 - 08/2019", text_extended=""),
        EducationModule(title="Creación de Videojuegos con Unreal Engine (350h)", company="CIFP José Luis Garci - Alcobendas, Madrid", date_range="10/2024 - 03/2025", text_extended=""),
        EducationModule(title="Programación con lenguajes orientados a objetos y bases de datos relacionales (710h)", company="Merinero - Madrid, España", date_range="07/2025 - 12/2025", text_extended=""),
        EducationModule(title="Inteligencia Artificial Generativa (22h)", company="Mantia - Madrid, España", date_range="09/2025 - 10/2025", text_extended="")
    ]))
    knowledge: Section = field(default_factory=lambda: Section(id="knowledge", title="Competencias", type="generic", modules=[
        TextModule(title="Grabación de vídeo"),
        TextModule(title="Prensa escrita"),
        TextModule(title="Diseño gráfico"),
        TextModule(title="Edición de vídeo"),
        TextModule(title="Branding"),
        TextModule(title="Medios sociales"),
        TextModule(title="Gestión de agendas médicas"),
        TextModule(title="Posproducción de vídeo"),
        TextModule(title="3D"),
        TextModule(title="Rendering for autonomous driving")
    ]))
    software: Section = field(default_factory=lambda: Section(id="software", title="Software", type="software", modules=[
        ImageModule(name="Adobe Photoshop"),
        ImageModule(name="Adobe Premiere Pro"),
        ImageModule(name="Unreal Engine 4.27"),
        ImageModule(name="Houdini FX"),
        ImageModule(name="Sony Vegas"),
        ImageModule(name="Avid Liquid")
    ]))
    languages: Section = field(default_factory=lambda: Section(id="languages", title="Lenguajes de Programación", type="language", modules=[
        ImageModule(name="Python"),
        ImageModule(name="C++")
    ]))
    
    # Custom sections could be added here in a list if needed, but for now fixed structure as per request
    
    def to_json(self):
        return json.dumps({
            "settings": self.settings.to_dict(),
            "header_info": self.header_info.to_dict(),
            "sections": {
                "personal_info": self.personal_info.to_dict(),
                "experience": self.experience.to_dict(),
                "education": self.education.to_dict(),
                "knowledge": self.knowledge.to_dict(),
                "software": self.software.to_dict(),
                "languages": self.languages.to_dict()
            }
        }, indent=4)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        cv = cls()
        cv.settings = Settings(**data.get("settings", {}))
        cv.header_info = HeaderInfo(**data.get("header_info", {}))
        
        sections = data.get("sections", {})
        if "personal_info" in sections:
            cv.personal_info = Section.from_dict(sections["personal_info"])
        if "experience" in sections:
            cv.experience = Section.from_dict(sections["experience"])
        if "education" in sections:
            cv.education = Section.from_dict(sections["education"])
        if "knowledge" in sections:
            cv.knowledge = Section.from_dict(sections["knowledge"])
        if "software" in sections:
            cv.software = Section.from_dict(sections["software"])
        if "languages" in sections:
            cv.languages = Section.from_dict(sections["languages"])
            
        return cv
