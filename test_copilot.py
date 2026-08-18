import asyncio
import g4f

async def main():
    try:
        r = await g4f.ChatCompletion.create_async(
            model='gpt-4',
            provider=g4f.Provider.CopilotApp,
            messages=[{'role':'user', 'content':'hola'}]
        )
        print('Success:', r)
    except Exception as e:
        print('Error:', type(e).__name__, e)

asyncio.run(main())
