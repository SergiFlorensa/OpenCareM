"""
Procesamiento inteligente de documentos médicos: parsing y chunking semántico.

Respeta estructura de markdown (secciones, tablas, listas) para evitar fragmentar
conceptos médicos.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Optional


class ContentType(str, Enum):
    """Tipo de contenido detectado en el documento."""

    SECTION_HEADER = "section_header"
    TABLE = "table"
    LIST = "list"
    PARAGRAPH = "paragraph"
    CODE_BLOCK = "code_block"
    CHECKLIST = "checklist"


@dataclass
class DocumentChunk:
    """Fragmento de documento con metadatos enriquecidos."""

    text: str
    chunk_index: int
    section_path: str  # "H1 > H2 > H3"
    content_type: ContentType
    token_count: int
    keywords: list[str]
    custom_questions: list[str]  # preguntas que responde este chunk
    document_title: str
    specialty: Optional[str] = None
    source_file: Optional[str] = None

    def to_dict(self) -> dict:
        """Convierte a diccionario para persistencia."""
        return {
            k: v.value if isinstance(v, Enum) else v
            for k, v in asdict(self).items()
        }

    def content_hash(self) -> str:
        """Hash del contenido para deduplicación."""
        return hashlib.sha256(self.text.encode()).hexdigest()


class DocumentParser:
    """Parse markdown/txt respetando estructura médica."""

    def __init__(self):
        self._heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        self._table_pattern = re.compile(r"^\|.+\|$", re.MULTILINE)
        self._list_pattern = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
        self._code_block_pattern = re.compile(r"```[\s\S]*?```", re.MULTILINE)
        self._checklist_pattern = re.compile(r"^\s*[-*+]\s+\[[-xX]\]\s+", re.MULTILINE)
        self._medical_keywords = {
            "sepsis", "lactato", "qsofa", "scasest", "troponina", "grace",
            "ecg", "rcp", "acls", "shock", "reanimacion", "hipotermia",
            "ictus", "hsa", "aspects", "trauma", "abcde", "consentimiento",
            "bioetica", "anticoagulacion", "antiagregantes", "heparina",
            "warfarina", "fibrinolisis", "intervension", "cateterismos",
            "paro cardiaco", "asistolia", "fibrilacion", "torsades",
            "bradicardia", "taquicardia", "arritmia", "sop", "sinusitis",
            "neumonía", "embolia", "hemotorax", "neumotorax", "tension",
            "taponamiento", "tamponade", "quilotorax", "efusion",
            "hematoma", "edema", "gangrena", "necrosis", "apoptosis"
        }

    def parse(
        self,
        content: str,
        title: str = "sin_titulo",
        specialty: Optional[str] = None,
    ) -> list[dict]:
        """
        Parse de documento en bloques respetando secciones y tablas.
        Retorna lista de bloques estructurados.
        """
        blocks = []
        current_section_path = ["Documento"]
        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Detectar encabezado
            heading_match = self._heading_pattern.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2)
                # Ajustar profundidad de sección
                current_section_path = current_section_path[:level] + [text]
                blocks.append({
                    "type": ContentType.SECTION_HEADER.value,
                    "content": line,
                    "section_path": " > ".join(current_section_path),
                    "start_line": i,
                })
                i += 1
                continue

            # Detectar bloque de código
            if line.strip().startswith("```"):
                code_block = [line]
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_block.append(lines[i])
                    i += 1
                if i < len(lines):
                    code_block.append(lines[i])
                    i += 1
                blocks.append({
                    "type": ContentType.CODE_BLOCK.value,
                    "content": "\n".join(code_block),
                    "section_path": " > ".join(current_section_path),
                })
                continue

            # Detectar tabla
            if self._table_pattern.match(line):
                table_lines = [line]
                i += 1
                while i < len(lines) and self._table_pattern.match(lines[i]):
                    table_lines.append(lines[i])
                    i += 1
                blocks.append({
                    "type": ContentType.TABLE.value,
                    "content": "\n".join(table_lines),
                    "section_path": " > ".join(current_section_path),
                })
                continue

            # Detectar lista de chequeo
            if self._checklist_pattern.match(line):
                checklist_lines = [line]
                i += 1
                while i < len(lines) and (
                    self._checklist_pattern.match(lines[i]) or
                    (lines[i].startswith("    ") or lines[i].startswith("\t"))
                ):
                    checklist_lines.append(lines[i])
                    i += 1
                blocks.append({
                    "type": ContentType.CHECKLIST.value,
                    "content": "\n".join(checklist_lines),
                    "section_path": " > ".join(current_section_path),
                })
                continue

            # Detectar lista
            if self._list_pattern.match(line):
                list_lines = [line]
                i += 1
                while i < len(lines) and (
                    self._list_pattern.match(lines[i]) or
                    (lines[i].startswith("    ") or lines[i].startswith("\t"))
                ):
                    list_lines.append(lines[i])
                    i += 1
                blocks.append({
                    "type": ContentType.LIST.value,
                    "content": "\n".join(list_lines),
                    "section_path": " > ".join(current_section_path),
                })
                continue

            # Párrafo normal (puede ser multi-línea)
            if line.strip():
                paragraph_lines = [line]
                i += 1
                while (
                    i < len(lines) and
                    lines[i].strip() and
                    not self._heading_pattern.match(lines[i]) and
                    not self._table_pattern.match(lines[i]) and
                    not self._list_pattern.match(lines[i]) and
                    not lines[i].strip().startswith("```")
                ):
                    paragraph_lines.append(lines[i])
                    i += 1
                blocks.append({
                    "type": ContentType.PARAGRAPH.value,
                    "content": "\n".join(paragraph_lines),
                    "section_path": " > ".join(current_section_path),
                })
                continue

            i += 1

        return blocks

    def extract_keywords_from_text(self, text: str) -> list[str]:
        """Extrae keywords médicos del texto."""
        text_lower = text.lower()
        keywords = set()
        for keyword in self._medical_keywords:
            if keyword in text_lower:
                keywords.add(keyword)
        # Buscar también términos con números (GRACE > 140, etc)
        numeric_terms = re.findall(r"\b[A-Z]+\s*(?:[><]=?|=)\s*\d+\b", text)
        keywords.update(numeric_terms)
        return sorted(list(keywords))

    def generate_hypothetical_questions(self, text: str, section_path: str) -> list[str]:
        """Genera preguntas hipotéticas que responde este fragmento."""
        questions = []
        text_lower = text.lower()

        # Heurísticas para generar preguntas
        if "protocolo" in text_lower or "algoritmo" in text_lower:
            if "scasest" in section_path.lower() or "troponina" in text_lower:
                questions.append("¿Cuál es el protocolo de SCASEST?")
                questions.append("¿Cómo evalúo el riesgo en sospecha coronario?")
            if "reanimacion" in section_path.lower() or "rcp" in text_lower:
                questions.append("¿Cómo procedo en un paro cardíaco?")

        if "shock" in text_lower:
            questions.append("¿Cómo clasifico y trato el shock?")
            questions.append("¿Qué vasopresor uso?")

        if "sepsis" in text_lower:
            questions.append("¿Cuál es el bundle de sepsis?")
            questions.append("¿Cómo calculo qSOFA?")

        if "trauma" in text_lower:
            questions.append("¿Cuál es el enfoque ABCDE en trauma?")
            questions.append("¿Cómo manajo traumatismo múltiple?")

        return questions if questions else ["¿Qué dice este fragmento?"]


class SemanticChunker:
    """Fragmenta documentos en chunks semánticos respetando estructura."""

    def __init__(self, token_counter=None, chunk_size_tokens: int = 384, overlap_tokens: int = 64):
        """
        Args:
            token_counter: función que cuenta tokens (ej: tiktoken encoding)
            chunk_size_tokens: tamaño objetivo de chunks (256-512)
            overlap_tokens: solapamiento entre chunks (64 por defecto)
        """
        self.chunk_size = chunk_size_tokens
        self.overlap = overlap_tokens
        self.token_counter = token_counter or self._simple_token_count
        self._parser = DocumentParser()

    @staticmethod
    def _simple_token_count(text: str) -> int:
        """Estimación simple: ~1 token por 4 caracteres."""
        return max(1, len(text) // 4)

    def chunk(
        self,
        content: str,
        title: str = "documento",
        specialty: Optional[str] = None,
        source_file: Optional[str] = None,
    ) -> list[DocumentChunk]:
        """
        Fragmenta documento respetando estructura semántica.

        Args:
            content: texto del documento
            title: título del documento
            specialty: especialidad médica (ej: "cardiología")
            source_file: archivo de origen

        Returns:
            Lista de DocumentChunk
        """
        blocks = self._parser.parse(content, title=title, specialty=specialty)
        chunks = []
        chunk_index = 0

        # Agrupar bloques en chunks respetando límites semánticos
        current_chunk_text = []
        current_section_path = "?"
        current_token_count = 0

        for block in blocks:
            block_text = block.get("content", "").strip()
            block_type = block.get("type", ContentType.PARAGRAPH.value)
            section_path = block.get("section_path", current_section_path)

            if not block_text:
                continue

            block_token_count = self.token_counter(block_text)

            # Tablas y listas nunca se fragmentan
            should_protect_block = block_type in [
                ContentType.TABLE.value,
                ContentType.LIST.value,
                ContentType.CHECKLIST.value,
                ContentType.CODE_BLOCK.value,
            ]

            # Si el bloque actual + nuevo excede tamaño, guarda chunk actual
            if (
                current_chunk_text and
                current_token_count + block_token_count > self.chunk_size and
                not should_protect_block
            ):
                chunk_text = "\n".join(current_chunk_text).strip()
                if chunk_text:
                    chunks.append(
                        self._create_chunk(
                            text=chunk_text,
                            chunk_index=chunk_index,
                            section_path=current_section_path,
                            title=title,
                            specialty=specialty,
                            source_file=source_file,
                        )
                    )
                    chunk_index += 1
                current_chunk_text = []
                current_token_count = 0

            # Agregar bloque al chunk actual
            current_chunk_text.append(block_text)
            current_token_count += block_token_count + 2  # +2 por separadores
            current_section_path = section_path

        # Último chunk
        if current_chunk_text:
            chunk_text = "\n".join(current_chunk_text).strip()
            if chunk_text:
                chunks.append(
                    self._create_chunk(
                        text=chunk_text,
                        chunk_index=chunk_index,
                        section_path=current_section_path,
                        title=title,
                        specialty=specialty,
                        source_file=source_file,
                    )
                )

        return chunks

    def _create_chunk(
        self,
        text: str,
        chunk_index: int,
        section_path: str,
        title: str,
        specialty: Optional[str],
        source_file: Optional[str],
    ) -> DocumentChunk:
        """Crea DocumentChunk con metadatos enriquecidos."""
        token_count = self.token_counter(text)
        keywords = self._parser.extract_keywords_from_text(text)
        custom_questions = self._parser.generate_hypothetical_questions(text, section_path)

        return DocumentChunk(
            text=text,
            chunk_index=chunk_index,
            section_path=section_path,
            content_type=ContentType.PARAGRAPH,
            token_count=token_count,
            keywords=keywords,
            custom_questions=custom_questions,
            document_title=title,
            specialty=specialty,
            source_file=source_file,
        )


def load_or_estimate_token_counter():
    """
    Intenta usar tiktoken si está disponible, sino usa estimación simple.
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")  # Encoding universal
        return lambda text: len(enc.encode(text))
    except ImportError:
        return SemanticChunker._simple_token_count
