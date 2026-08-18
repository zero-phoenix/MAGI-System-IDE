import asyncio
import g4f

async def main():
    try:
        r = await g4f.ChatCompletion.create_async(
            model='gpt-4',
            provider=g4f.Provider.Yqcloud,
            messages=[
                {"role": "user", "content": "Di: funciona"}
            ]
        )
        print('Success Yqcloud (no prompt):', r)
    except Exception as e:
        print('Error Yqcloud (no prompt):', type(e).__name__, e)

asyncio.run(main())
