from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from pathlib import Path

@dataclass
class ReproducibleConfig:
    source_date_epoch: Optional[int] = None
    lock: Optional[str] = None

@dataclass
class OutputConfig:
    single_executable: List[str] = field(default_factory=lambda: ["windows", "linux"])
    max_size_mb: int = 180

@dataclass
class Recipe:
    name: str
    base: str
    arch: str
    kernel: str
    init: str
    packages: List[str]
    memory_mb: int
    disk_mb: int
    network: Literal["none", "host-only", "nat"] = "none"
    shared_folder: Literal["none", "ro", "rw"] = "none"
    persistence: Literal["none", "overlay", "full"] = "overlay"
    autostart: Optional[str] = None
    reproducible: ReproducibleConfig = field(default_factory=ReproducibleConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

@dataclass
class Component:
    name: str
    version: str
    license: str
    hash: str

@dataclass
class OsImage:
    path: Path
    recipe_name: str
    hash_sha256: str
    size_mb: int
    manifest: List[Component]

@dataclass
class ReproReport:
    is_reproducible: bool
    hash_run_1: str
    hash_run_2: str
    detail: str

@dataclass
class VmSession:
    session_id: str
    image: OsImage
    status: str
    engine: Literal["qemu", "wasm", "dosbox"]
    network_enabled: bool
    events: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class EraProfile:
    name: str
    compatible_formats: List[str]
    export_sequence: List[str]
    application: str
