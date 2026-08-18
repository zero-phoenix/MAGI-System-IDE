"""
Emulación de fragmentos con Unicorn (Plan MAGI 9.0 §5.3).

PARA QUÉ SIRVE DE VERDAD
=======================
Para verificación diferencial: ejecutas la misma secuencia de instrucciones en
tu implementación y en Unicorn, y comparas registro a registro. Cuando divergen,
sabes la instrucción EXACTA en la que tu emulador se equivoca.

Es la diferencia entre "el juego se cuelga en algún punto" y "en 0x08804a10 tu
`addu` no propaga el acarreo igual que el hardware". Sin esto, depurar un
dynarec es adivinar.
"""
from __future__ import annotations

import faulthandler
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_UC_ARCH = {"mips": "UC_ARCH_MIPS", "arm": "UC_ARCH_ARM",
            "arm64": "UC_ARCH_ARM64", "x86": "UC_ARCH_X86"}

# Las constantes de registro NO están en el paquete raíz de unicorn: viven en
# submódulos por arquitectura (unicorn.mips_const, unicorn.arm_const...).
# Buscarlas en `unicorn` devuelve None y el volcado de registros sale vacío
# sin que nada falle — un fallo silencioso, de los peores.
_CONST_MODULE = {"mips": "mips_const", "arm": "arm_const",
                 "arm64": "arm64_const", "x86": "x86_const"}


def _reg_const(arch: str, name: str):
    import importlib
    try:
        mod = importlib.import_module(f"unicorn.{_CONST_MODULE[arch]}")
    except (ImportError, KeyError):
        return None
    return getattr(mod, name, None)

# Registros que interesan por arquitectura. No hace falta volcar los 32.
_TRACKED = {
    "mips": ["UC_MIPS_REG_" + r for r in
             ("V0", "V1", "A0", "A1", "A2", "A3", "T0", "T1",
              "S0", "S1", "SP", "RA", "PC")],
    "arm": ["UC_ARM_REG_" + r for r in
            ("R0", "R1", "R2", "R3", "R4", "R5", "SP", "LR", "PC", "CPSR")],
    "arm64": ["UC_ARM64_REG_" + r for r in
              ("X0", "X1", "X2", "X3", "SP", "PC")],
}


@dataclass
class EmulationResult:
    ok: bool
    registers: dict[str, int] = field(default_factory=dict)
    memory: dict[int, str] = field(default_factory=dict)
    instructions_run: int = 0
    error: str | None = None
    stopped_at: int = 0

    def render(self) -> str:
        if not self.ok:
            return (f"ERROR tras {self.instructions_run} instrucciones "
                    f"en 0x{self.stopped_at:08x}: {self.error}")
        regs = "  ".join(f"{k}=0x{v:08x}" for k, v in self.registers.items())
        return (f"{self.instructions_run} instrucciones ejecutadas\n{regs}")

    def diff(self, other: EmulationResult) -> str:
        """Compara dos ejecuciones. La herramienta de depuración de dynarecs."""
        diffs = []
        for k, v in self.registers.items():
            w = other.registers.get(k)
            if w is not None and w != v:
                diffs.append(f"  {k}: 0x{v:08x} vs 0x{w:08x}  (delta {v - w:+d})")
        if not diffs:
            return "Sin divergencias en los registros seguidos."
        return "DIVERGENCIA:\n" + "\n".join(diffs)


def emulate(code: bytes, *, arch: str = "mips", bits: int = 32,
            endian: str = "little", base: int = 0x1000,
            max_instructions: int = 10_000, timeout_us: int = 5_000_000,
            initial_regs: dict[str, int] | None = None,
            stack_size: int = 0x10000) -> EmulationResult:
    """
    Ejecuta un fragmento en un espacio de memoria aislado.

    No emula la consola entera: emula la CPU. Lo que hace falta para comprobar
    que una secuencia de instrucciones produce el estado que debe.
    """
    try:
        import unicorn
    except ImportError:
        return EmulationResult(False, error="unicorn no instalado: pip install unicorn")

    uc_arch = getattr(unicorn, _UC_ARCH.get(arch, ""), None)
    if uc_arch is None:
        return EmulationResult(False, error=f"arquitectura no soportada: {arch}")

    mode = 0
    if arch == "mips":
        mode |= (unicorn.UC_MODE_MIPS64 if bits == 64 else unicorn.UC_MODE_MIPS32)
    elif arch == "arm":
        mode |= unicorn.UC_MODE_ARM
    elif arch == "x86":
        mode |= unicorn.UC_MODE_64 if bits == 64 else unicorn.UC_MODE_32
    mode |= (unicorn.UC_MODE_BIG_ENDIAN if endian == "big"
             else unicorn.UC_MODE_LITTLE_ENDIAN)

    result = EmulationResult(ok=False)
    counter: dict[str, int] = {"n": 0}
    mu = None

    # EL VIGILANTE DE FALLOS SE APARTA MIENTRAS EMULA UNICORN.
    #
    # Unicorn es QEMU por dentro, y su MMU se apoya en excepciones del sistema
    # (páginas guarda) que él mismo captura y resuelve: son parte de su
    # funcionamiento normal, no un fallo. Pero `faulthandler` —que pytest
    # activa por defecto— las ve pasar y escribe «Windows fatal exception:
    # access violation» con un volcado de pila entero por cada una.
    #
    # No es solo ruido. En la suite en paralelo ese volcado va al mismo canal
    # por el que los workers de xdist se comunican, y el fichero que le tocaba
    # después al worker fallaba con errores imposibles —`tag=None` en un test
    # de hedge que pasa perfectamente solo—. Dos días de «cuelgue transitorio
    # de xdist» eran esto.
    #
    # Se aparta solo durante la emulación y se repone después, porque un
    # crash de verdad en el resto del programa sí hay que verlo.
    _vigilaba = faulthandler.is_enabled()
    if _vigilaba:
        faulthandler.disable()
    try:
        mu = unicorn.Uc(uc_arch, mode)

        code_size = max(0x1000, (len(code) + 0xFFF) & ~0xFFF)
        mu.mem_map(base, code_size)
        mu.mem_write(base, code)

        stack_base = base + code_size + 0x1000
        mu.mem_map(stack_base, stack_size)
        sp = stack_base + stack_size - 0x100

        sp_reg = {"mips": "UC_MIPS_REG_SP", "arm": "UC_ARM_REG_SP",
                  "arm64": "UC_ARM64_REG_SP", "x86": "UC_X86_REG_RSP"}.get(arch)
        sp_const = _reg_const(arch, sp_reg) if sp_reg else None
        if sp_const is not None:
            mu.reg_write(sp_const, sp)

        for name, value in (initial_regs or {}).items():
            const = _reg_const(arch, name if name.startswith("UC_")
                               else f"UC_{arch.upper()}_REG_{name.upper()}")
            if const is not None:
                mu.reg_write(const, value)

        def on_insn(uc, address, size, user_data):
            counter["n"] += 1
            if counter["n"] >= max_instructions:
                uc.emu_stop()

        mu.hook_add(unicorn.UC_HOOK_CODE, on_insn)
        mu.emu_start(base, base + len(code), timeout=timeout_us,
                     count=max_instructions)
        result.ok = True

    except Exception as e:
        result.error = f"{type(e).__name__}: {e}"
        pc_const = _reg_const(arch, {"mips": "UC_MIPS_REG_PC",
                                     "arm": "UC_ARM_REG_PC",
                                     "arm64": "UC_ARM64_REG_PC",
                                     "x86": "UC_X86_REG_RIP"}.get(arch, ""))
        if mu is not None and pc_const is not None:
            try:
                result.stopped_at = mu.reg_read(pc_const)
            except Exception:
                pass

    finally:
        if _vigilaba:
            faulthandler.enable()

    result.instructions_run = counter.get("n", 0) if isinstance(counter, dict) else 0
    if mu is None:
        return result
    for reg_name in _TRACKED.get(arch, []):
        const = _reg_const(arch, reg_name)
        if const is None:
            continue
        try:
            result.registers[reg_name.rsplit("_", 1)[-1]] = mu.reg_read(const)
        except Exception as e:
            logger.debug("[emulate] no se pudo leer %s: %s", reg_name, e)
    if result.ok and not result.registers:
        result.ok = False
        result.error = ("no se pudo leer ningún registro: revisa la versión de "
                        "unicorn")
    return result


def differential_test(code: bytes, reference_regs: dict[str, int], *,
                      arch: str = "mips", **kw) -> str:
    """
    Compara el resultado de Unicorn contra el estado que tu emulador produce.

    `reference_regs` es lo que tu implementación devolvió. Unicorn hace de
    oráculo: no es perfecto, pero es una segunda opinión independiente y
    reproducible.
    """
    got = emulate(code, arch=arch, **kw)
    if not got.ok:
        return f"la referencia no llegó a ejecutar: {got.error}"

    diffs = []
    for reg, expected in reference_regs.items():
        actual = got.registers.get(reg.upper())
        if actual is None:
            continue
        if actual != expected:
            diffs.append(f"  {reg}: tu emulador 0x{expected:08x}, "
                         f"referencia 0x{actual:08x}")
    if not diffs:
        return (f"Coincide en los {len(reference_regs)} registros comparados "
                f"tras {got.instructions_run} instrucciones.")
    return ("DIVERGENCIA respecto a la referencia:\n" + "\n".join(diffs)
            + "\n\nRevisa la última instrucción que escribe en esos registros.")
