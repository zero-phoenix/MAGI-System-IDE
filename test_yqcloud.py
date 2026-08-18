import asyncio
import g4f

async def main():
    try:
        r = await g4f.ChatCompletion.create_async(
            model='gpt-4',
            provider=g4f.Provider.Yqcloud,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. You must always answer in Spanish language. Do NOT use Chinese language."},
                {"role": "user", "content": "Di: funciona"}
            ]
        )
        print('Success Yqcloud:', r)
    except Exception as e:
        print('Error Yqcloud:', type(e).__name__, e)

asyncio.run(main())
