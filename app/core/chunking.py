"""
Procesamiento inteligente de documentos mÃ©dicos: parsing y chunking semÃ¡ntico.

Respeta estructura de markdown (secciones, tablas, listas) para evitar fragmentar
conceptos mÃ©dicos.
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
        """Hash del contenido para deduplicaciÃ³n."""
        return hashlib.sha256(self.text.encode()).hexdigest()


class DocumentParser:
    """Parse markdown/txt respetando estructura mÃ©dica."""

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
            "neumonÃ­a", "embolia", "hemotorax", "neumotorax", "tension",
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
                # Ajustar profundidad de secciÃ³n
                current_section_path = current_section_path[:level] + [text]
                blocks.append({
                    "type": ContentType.SECTION_HEADER.value,
                    "content": line,
                    "section_path": " > ".join(current_section_path),
                    "start_line": i,
                })
                i += 1
                continue

            # Detectar bloque de cÃ³digo
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

            # PÃ¡rrafo normal (puede ser multi-lÃ­nea)
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
        """Extrae keywords mÃ©dicos del texto."""
        text_lower = text.lower()
        keywords = set()
        for keyword in self._medical_keywords:
            if keyword in text_lower:
                keywords.add(keyword)
        # Buscar tambiÃ©n tÃ©rminos con nÃºmeros (GRACE > 140, etc)
        numeric_terms = re.findall(r"\b[A-Z]+\s*(?:[><]=?|=)\s*\d+\b", text)
        keywords.update(numeric_terms)
        return sorted(list(keywords))

    def generate_hypothetical_questions(self, text: str, section_path: str) -> list[str]:
        """Genera preguntas hipoteticas de alta cobertura para retrieval QA."""
        text_lower = str(text or "").lower()
        section_parts = [
            part.strip()
            for part in str(section_path or "").split(">")
            if part and part.strip()
        ]
        topic = re.sub(
            r"\s+",
            " ",
            section_parts[-1] if section_parts else "este protocolo",
        ).strip()
        topic = topic[:96]

        stopwords = {
            "para",
            "como",
            "desde",
            "hasta",
            "entre",
            "sobre",
            "donde",
            "cuando",
            "porque",
            "ademas",
            "segun",
            "tras",
            "ante",
            "con",
            "sin",
            "del",
            "las",
            "los",
            "una",
            "uno",
            "unos",
            "unas",
            "este",
            "esta",
            "estos",
            "estas",
            "que",
        }
        content_terms = [
            token
            for token in re.findall(r"[a-zA-Z0-9\-]+", text_lower)
            if len(token) >= 5 and token not in stopwords
        ]
        top_terms = list(dict.fromkeys(content_terms))[:4]
        keywords = self.extract_keywords_from_text(text)[:4]

        questions: list[str] = [
            f"¿Cual es el manejo operativo de {topic}?",
            f"¿Cuales son los pasos iniciales para {topic}?",
        ]
        if "criterio" in text_lower or "criterios" in text_lower:
            questions.append(f"¿Que criterios de decision se describen en {topic}?")
        if "algoritmo" in text_lower or "protocolo" in text_lower:
            questions.append(f"¿Que algoritmo o protocolo se recomienda para {topic}?")
        if "tratamiento" in text_lower or "manejo" in text_lower:
            questions.append(f"¿Que tratamiento o manejo se propone en {topic}?")
        if "riesgo" in text_lower or "alerta" in text_lower or "red flag" in text_lower:
            questions.append(f"¿Que alertas o factores de riesgo aparecen en {topic}?")
        if "diagnostico" in text_lower:
            questions.append(f"¿Que enfoque diagnostico se indica en {topic}?")
        if keywords:
            questions.append(
                f"¿Que recomendaciones practicas se dan para {', '.join(keywords[:2])}?"
            )
        if top_terms:
            questions.append(
                f"¿Como se integran {', '.join(top_terms[:2])} dentro del plan operativo?"
            )

        deduped = [item.strip() for item in questions if item and item.strip()]
        deduped = list(dict.fromkeys(deduped))
        return deduped[:6]


class SemanticChunker:
    """Fragmenta documentos en chunks semÃ¡nticos respetando estructura."""

    def __init__(self, token_counter=None, chunk_size_tokens: int = 384, overlap_tokens: int = 64):
        """
        Args:
            token_counter: funciÃ³n que cuenta tokens (ej: tiktoken encoding)
            chunk_size_tokens: tamaÃ±o objetivo de chunks (256-512)
            overlap_tokens: solapamiento entre chunks (64 por defecto)
        """
        self.chunk_size = chunk_size_tokens
        self.overlap = overlap_tokens
        self.token_counter = token_counter or self._simple_token_count
        self._parser = DocumentParser()

    @staticmethod
    def _simple_token_count(text: str) -> int:
        """EstimaciÃ³n simple: ~1 token por 4 caracteres."""
        return max(1, len(text) // 4)

    def chunk(
        self,
        content: str,
        title: str = "documento",
        specialty: Optional[str] = None,
        source_file: Optional[str] = None,
        parsed_blocks: Optional[list[dict[str, str]]] = None,
    ) -> list[DocumentChunk]:
        """
        Fragmenta documento respetando estructura semÃ¡ntica.

        Args:
            content: texto del documento
            title: tÃ­tulo del documento
            specialty: especialidad mÃ©dica (ej: "cardiologÃ­a")
            source_file: archivo de origen

        Returns:
            Lista de DocumentChunk
        """
        blocks = parsed_blocks or self._parser.parse(content, title=title, specialty=specialty)
        chunks = []
        chunk_index = 0

        # Agrupar bloques en chunks respetando lÃ­mites semÃ¡nticos
        current_chunk_text = []
        current_section_path = "?"
        current_content_type = ContentType.PARAGRAPH
        current_token_count = 0

        for block in blocks:
            block_text = block.get("content", "").strip()
            section_path = block.get("section_path", current_section_path)
            block_content_type = self._normalize_content_type(block.get("type", "paragraph"))

            if not block_text:
                continue

            for piece in self._split_block_if_needed(block_text):
                block_token_count = self.token_counter(piece)

                # Si el bloque actual + nuevo excede tamaÃ±o, guarda chunk actual
                if current_chunk_text and current_token_count + block_token_count > self.chunk_size:
                    chunk_text = "\n".join(current_chunk_text).strip()
                    if chunk_text:
                        chunks.append(
                            self._create_chunk(
                                text=chunk_text,
                                chunk_index=chunk_index,
                                section_path=current_section_path,
                                content_type=current_content_type,
                                title=title,
                                specialty=specialty,
                                source_file=source_file,
                            )
                        )
                        chunk_index += 1

                    # Solapamiento real para mantener continuidad semantica entre chunks.
                    overlap_text = self._tail_with_token_budget(chunk_text, self.overlap)
                    current_chunk_text = [overlap_text] if overlap_text else []
                    current_token_count = (
                        self.token_counter(overlap_text) + 2 if overlap_text else 0
                    )

                # Agregar bloque/pieza al chunk actual
                current_chunk_text.append(piece)
                current_token_count += block_token_count + 2  # +2 por separadores
                current_section_path = section_path
                current_content_type = block_content_type

        # Ãšltimo chunk
        if current_chunk_text:
            chunk_text = "\n".join(current_chunk_text).strip()
            if chunk_text:
                chunks.append(
                    self._create_chunk(
                        text=chunk_text,
                        chunk_index=chunk_index,
                        section_path=current_section_path,
                        content_type=current_content_type,
                        title=title,
                        specialty=specialty,
                        source_file=source_file,
                    )
                )

        return chunks

    def _split_block_if_needed(self, block_text: str) -> list[str]:
        """
        Divide bloques sobredimensionados con estrategia recursiva:
        lineas -> frases -> corte duro por longitud.
        """
        max_tokens = max(32, int(self.chunk_size * 0.9))
        if self.token_counter(block_text) <= max_tokens:
            return [block_text]

        pieces = self._split_text_to_budget(block_text, max_tokens=max_tokens)
        cleaned = [piece.strip() for piece in pieces if piece and piece.strip()]
        return cleaned or [block_text]

    def _split_text_to_budget(self, text: str, *, max_tokens: int) -> list[str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) > 1:
            return self._pack_units(lines, max_tokens=max_tokens)

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[\.\!\?\:\;])\s+", text)
            if sentence.strip()
        ]
        if len(sentences) > 1:
            return self._pack_units(sentences, max_tokens=max_tokens)

        return self._hard_split(text, max_tokens=max_tokens)

    def _pack_units(self, units: list[str], *, max_tokens: int) -> list[str]:
        pieces: list[str] = []
        current: list[str] = []
        current_tokens = 0

        for unit in units:
            unit_tokens = self.token_counter(unit)
            if unit_tokens > max_tokens:
                if current:
                    pieces.append(" ".join(current).strip())
                    current = []
                    current_tokens = 0
                pieces.extend(self._hard_split(unit, max_tokens=max_tokens))
                continue

            if current and current_tokens + unit_tokens > max_tokens:
                pieces.append(" ".join(current).strip())
                current = [unit]
                current_tokens = unit_tokens
                continue

            current.append(unit)
            current_tokens += unit_tokens

        if current:
            pieces.append(" ".join(current).strip())
        return pieces

    def _hard_split(self, text: str, *, max_tokens: int) -> list[str]:
        words = [word for word in text.split() if word]
        if not words:
            return [text]

        pieces: list[str] = []
        current: list[str] = []
        current_tokens = 0
        for word in words:
            word_tokens = self.token_counter(word)
            if current and current_tokens + word_tokens > max_tokens:
                pieces.append(" ".join(current).strip())
                current = [word]
                current_tokens = word_tokens
                continue
            current.append(word)
            current_tokens += word_tokens
        if current:
            pieces.append(" ".join(current).strip())
        return pieces

    def _tail_with_token_budget(self, text: str, max_tokens: int) -> str:
        if not text or max_tokens <= 0:
            return ""
        words = [word for word in text.split() if word]
        if not words:
            return ""

        selected: list[str] = []
        total = 0
        for word in reversed(words):
            token_count = self.token_counter(word)
            if selected and total + token_count > max_tokens:
                break
            selected.append(word)
            total += token_count
        selected.reverse()
        return " ".join(selected).strip()

    def _create_chunk(
        self,
        text: str,
        chunk_index: int,
        section_path: str,
        content_type: ContentType,
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
            content_type=content_type,
            token_count=token_count,
            keywords=keywords,
            custom_questions=custom_questions,
            document_title=title,
            specialty=specialty,
            source_file=source_file,
        )

    @staticmethod
    def _normalize_content_type(raw_value: str) -> ContentType:
        normalized = str(raw_value or "").strip().lower()
        mapping = {
            "section_header": ContentType.SECTION_HEADER,
            "header": ContentType.SECTION_HEADER,
            "title": ContentType.SECTION_HEADER,
            "table": ContentType.TABLE,
            "otsl_table": ContentType.TABLE,
            "html_table": ContentType.TABLE,
            "formula": ContentType.CODE_BLOCK,
            "equation": ContentType.CODE_BLOCK,
            "latex": ContentType.CODE_BLOCK,
            "list": ContentType.LIST,
            "checklist": ContentType.CHECKLIST,
            "code_block": ContentType.CODE_BLOCK,
            "paragraph": ContentType.PARAGRAPH,
            "text": ContentType.PARAGRAPH,
        }
        return mapping.get(normalized, ContentType.PARAGRAPH)


def load_or_estimate_token_counter():
    """
    Intenta usar tiktoken si estÃ¡ disponible, sino usa estimaciÃ³n simple.
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")  # Encoding universal
        return lambda text: len(enc.encode(text))
    except ImportError:
        return SemanticChunker._simple_token_count

