import asyncio
import aiohttp
import uuid

async def main():
    headers = {
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Host": "copilot.microsoft.com",
        "User-Agent": "CopilotNative/30.0.440505001-prod (Android 14; Google; Pixel 8 Pro)",
        "X-Search-UILang": "en-US",
        "Origin": "https://copilot.microsoft.com"
    }
    
    start_payload = {
        "timeZone": "Europe/Kiev",
        "startNewConversation": True,
        "teenSupportEnabled": True,
        "correctPersonalizationSetting": True,
        "deferredDataUseCapable": True
    }
    
    async with aiohttp.ClientSession() as session:
        print("Starting conversation...")
        async with session.post(
            "https://copilot.microsoft.com/c/api/start", 
            headers=headers, 
            json=start_payload
        ) as resp:
            print("Start status:", resp.status)
            if resp.status != 200:
                print("Failed to start:", await resp.text())
                return
            
            start_data = await resp.json()
            conversation_id = start_data.get("currentConversationId")
            print("Conv ID:", conversation_id)

        client_session_id = str(uuid.uuid4())
        ws_url = f"wss://copilot.microsoft.com/c/api/chat?api-version=2&clientSessionId={client_session_id}"
        
        print("Connecting to WS...")
        try:
            async with session.ws_connect(ws_url, headers=headers) as ws:
                print("Connected!")
        except Exception as e:
            print("Error connecting WS:", type(e).__name__, e)

asyncio.run(main())
