import asyncio, g4f  
async def test():  
    try:  
        response = await g4f.client.AsyncClient().chat.completions.create(model='gpt-4o', provider=g4f.Provider.Blackbox, messages=[{'role': 'user', 'content': 'hola'}])  
        print('OK:', response.choices[0].message.content[:20])  
    except Exception as e:  
        print('FAIL:', type(e), e)  
asyncio.run(test())  
