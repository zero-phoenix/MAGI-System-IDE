import asyncio
import time
import g4f
import sys

async def medir_proveedor(provider_name):
    cls = getattr(g4f.Provider, provider_name, None)
    if cls is None:
        return provider_name, None, False, "No class"
    
    if getattr(cls, 'use_nodriver', False) or getattr(cls, 'webdriver', False):
        return provider_name, None, False, "Browser"
        
    try:
        t0 = time.monotonic()
        response = await asyncio.wait_for(
            g4f.ChatCompletion.create_async(
                model="gpt-4",
                provider=cls,
                messages=[{"role": "user", "content": "Hola. Di exactamente: funciona"}]
            ), timeout=10.0)
        latency_ms = (time.monotonic() - t0) * 1000
        response = str(response)
        idioma_ok = "funciona" in response.lower()
        return provider_name, latency_ms, idioma_ok, response[:60].replace("\n", " ")
    except Exception as e:
        latency_ms = (time.monotonic() - t0) * 1000
        return provider_name, latency_ms, False, type(e).__name__

async def main():
    providers = [p.__name__ for p in g4f.Provider.__providers__ if p.working and not p.needs_auth]
    print(f"Probando {len(providers)} proveedores trabajando sin auth...")
    sys.stdout.flush()
    
    sem = asyncio.Semaphore(15)
    
    async def worker(p):
        async with sem:
            res = await medir_proveedor(p)
            print(f"Completado {p}: {res[3][:30]}")
            sys.stdout.flush()
            return res
            
    results = await asyncio.gather(*(worker(p) for p in providers))
    
    print("\n--- RESULTADOS ---")
    sys.stdout.flush()
    exitos = [r for r in results if r[1] is not None and r[2]]
    exitos.sort(key=lambda x: x[1])
    for r in exitos:
        print(f"EXITO: {r[0]} ({int(r[1])}ms) -> {r[3]}")
    sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())
