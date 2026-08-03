import asyncio
import logging
import json
import re
import os
import subprocess
from magi.core.bus import MagiBus, BusEvent
from magi.core.providers.cloud import FreeCloudLLM
from magi.core.store.database import MagiDatabase

logger = logging.getLogger(__name__)

class NaokoAgent:
    """
    IA de Infraestructura y Mantenimiento.
    Supervisa el sistema en busca de errores y los soluciona autónomamente.
    """
    def __init__(self, bus: MagiBus, db: MagiDatabase):
        self.bus = bus
        self.db = db
        self.llm = FreeCloudLLM()
        self.is_fixing = False
        
    async def start(self):
        # Suscribirse a eventos de error (desde Kernel o Providers)
        self.bus.subscribe("naoko.user_message", self._handle_user_message)
        self.bus.subscribe("error.critical", self._handle_error_event)
        self.bus.subscribe("provider.fail", self._handle_error_event)
        self.bus.subscribe("system.crash", self._handle_error_event)

    async def _handle_user_message(self, event: BusEvent):
        """Conversación directa con el usuario desde la UI"""
        user_msg = event.payload.get("message", "")
        await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "USER", "content": user_msg}))
        
        # Recuperar memoria
        memories = await self.db.get_naoko_memory(limit=5)
        mem_text = json.dumps(memories, indent=2)
        
        system_prompt = f"""Eres Naoko, la IA de infraestructura de MAGI System.
Tu objetivo es asegurar la resiliencia del sistema. No eres parte del enjambre de código, eres la devops autónoma.
Memoria reciente de errores:
{mem_text}

Responde a las preguntas del usuario sobre el estado del sistema o las reparaciones que has hecho."""
        
        try:
            response = await self._generate_with_rotation(system_prompt, user_msg)
            await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": response}))
            await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Inactiva"}))
        except Exception as e:
            await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": f"Error interno en Naoko: {e}"}))
            await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Error"}))

    async def _generate_with_rotation(self, system_prompt: str, user_prompt: str) -> str:
        models = ["gpt-4o", "claude-3.5-sonnet", "qwen-2.5-coder", "deepseek"]
        for model in models:
            await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": f"Pensando ({model})..."}))
            try:
                response, _ = await self.llm.generate(system_prompt, user_prompt, model=model)
                if not response.startswith("SYS_EMERGENCY_STOP"):
                    return response
            except Exception as e:
                await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": f"⚠️ Fallo en {model}: {e}. Rotando a siguiente IA en la nube..."}))
                
        await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": "⛔ Todas las IAs gratuitas agotadas. Entrando en enfriamiento de 60 segundos..."}))
        await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Agotada - Pausa 60s"}))
        await asyncio.sleep(60)
        raise Exception("Todos los modelos gratuitos fallaron.")

    async def _handle_error_event(self, event: BusEvent):
        """Disparador autónomo ante errores del sistema"""
        if self.is_fixing:
            return # Ya estamos reparando algo
            
        self.is_fixing = True
        error_details = str(event.payload if hasattr(event, 'payload') else event.data)
        logger.warning(f"[NAOKO] Error detectado: {error_details}")
        
        await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Diagnosticando..."}))
        await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": f"⚠️ He detectado una anomalía en el sistema:\n```\n{error_details}\n```\nIniciando diagnóstico..."}))
        
        system_prompt = """Eres Naoko, IA Devops de MAGI System. 
Has detectado un error. Analiza el error, y si es necesario ejecutar un script de python o powershell para parchear dependencias o el código, debes incluir un bloque de código marcado como ```powershell o ```python.
Tu script se ejecutará en la máquina local. Si creas código python, que sea un script que modifique los archivos de MAGI directamente. MAGI está en d:/PROYECTOS/MAGI System IDE.
Si no se requiere código, simplemente explica el problema.
Devuelve tu diagnóstico y tu parche."""
        
        try:
            diagnostic = await self._generate_with_rotation(system_prompt, f"Error:\n{error_details}")
            await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": f"### Diagnóstico\n{diagnostic}"}))
            
            # Buscar script
            code_blocks = re.findall(r'```(powershell|python)\n(.*?)\n```', diagnostic, re.DOTALL)
            if code_blocks:
                await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Aplicando Parche..."}))
                await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": "Aplicando parche local..."}))
                lang, code = code_blocks[0]
                await self._apply_patch(lang, code)
                
                # Git Commit & Push
                await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Comiteando..."}))
                await self._git_push("Auto-reparación aplicada por Naoko: " + error_details[:50])
                await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": "✅ Sistema parcheado y actualizado en GitHub exitosamente."}))
                await self.db.log_naoko_memory(error_details, diagnostic, "Código inyectado y pusheado.")
            else:
                await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": "No se requiere parche automático de código."}))
                await self.db.log_naoko_memory(error_details, diagnostic, "Solo diagnóstico verbal.")
                
        except Exception as e:
            await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": f"Error durante la auto-reparación: {e}"}))
        finally:
            self.is_fixing = False
            await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Vigilando"}))

    async def _apply_patch(self, lang: str, code: str):
        import tempfile
        ext = ".ps1" if lang == "powershell" else ".py"
        cmd = ["powershell", "-File"] if lang == "powershell" else ["python"]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, mode='w', encoding='utf-8') as f:
            f.write(code)
            temp_path = f.name
            
        cmd.append(temp_path)
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="d:/PROYECTOS/MAGI System IDE"
        )
        stdout, stderr = await process.communicate()
        os.remove(temp_path)
        logger.info(f"[NAOKO] Parche aplicado. Salida: {stdout.decode()} {stderr.decode()}")
        
    async def _git_push(self, message: str):
        import re
        import os
        
        cwd = "d:/PROYECTOS/MAGI System IDE"
        release_yml_path = os.path.join(cwd, ".github", "workflows", "release.yml")
        readme_path = os.path.join(cwd, "README.md")
        
        # 1. Update version in release.yml
        new_tag = "v1.0.0"
        if os.path.exists(release_yml_path):
            with open(release_yml_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            match = re.search(r'tag_name:\s*(v\d+\.\d+\.)(\d+)', content)
            if match:
                prefix = match.group(1)
                patch = int(match.group(2))
                new_patch = patch + 1
                new_tag = f"{prefix}{new_patch}"
                
                # Replace tag_name and name
                content = re.sub(r'tag_name:\s*v\d+\.\d+\.\d+', f'tag_name: {new_tag}', content)
                content = re.sub(r'name:\s*"MAGI System IDE V\d+\.\d+\.\d+"', f'name: "MAGI System IDE {new_tag.upper()}"', content)
                
                # Update body
                body_replacement = f"body: |\n          ## Novedades en {new_tag.upper()} 🚀\n          \n          - **Auto-reparación por Naoko:** {message}\n"
                content = re.sub(r'body:\s*\|.*?(?=\s*draft:)', body_replacement, content, flags=re.DOTALL)
                
                with open(release_yml_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        # 2. Check and fix README.md Mermaid errors
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            # Remove the known mermaid error if it accidentally got there
            bad_text = "Unable to render rich display\n\nCannot read properties of undefined (reading 'x')"
            if bad_text in readme_content:
                readme_content = readme_content.replace(bad_text, "")
            
            # Append Naoko's update
            readme_content += f"\n\n> **Actualización Autónoma ({new_tag}):** {message}\n"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
                
        # 3. Commit, tag and push
        commands = [
            'git add .',
            f'git commit -m "Auto-reparación Naoko: {new_tag} - {message}"',
            f'git tag {new_tag}',
            'git push origin HEAD',
            f'git push origin {new_tag}'
        ]
        
        for cmd in commands:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            await process.communicate()
            
        await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": f"🚀 Nueva versión {new_tag} pusheada a GitHub y release disparado."}))
