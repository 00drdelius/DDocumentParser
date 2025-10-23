import asyncio
import aiohttp
from aiofiles import open as aopen

def embedding_format_instruction(task_description: str, query: str) -> str:
    """
    format instruction for Qwen3 embedding infer.
    Args:
        task_description(str): task description
        query(str): query
    """
    return f'Instruct: {task_description}\nQuery:{query}'


def reranker_format_instruction(instruction, query, doc):

    if instruction is None:
        instruction = 'Given a web search query, retrieve relevant passages that answer the query'
    output = "<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}".format(instruction=instruction,query=query, doc=doc)
    return output


async def get_embeddings(
    client:aiohttp.ClientSession,
    query: str=None,
    task_description:str=None,
    documents:list[str]|str=None
) -> list[dict]:
    """
    embedding query, returns vector.
    Returns:
        list[dict]: list of embedding item. Each contains key:
        [embedding:list[float], object:str, index:int, origin:str]
    """
    #NOTE boolean ^ boolean, 异或
    assert any(query) ^ any(documents), "You cannot send query and documents all at once."
    
    if query:
        query = embedding_format_instruction(task_description, query)

    payload=dict(
        model="Qwen3-Embedding-4B",
        input=query or documents,
        encoding_format="float",
    )
    async with client.post("embeddings",json=payload) as aresp:
        aresp.raise_for_status()
        try:
            data = await aresp.json()
            embeddings:list = data.get('data',dict())
            embeddings=sorted(embeddings, key=lambda e:e['index'])
        except Exception as e:
            print(f"[ERROR DURING EMBEDDINGS] {e}")
        else:
            for item in embeddings:
                item['origin']=documents[item['index']]

        return embeddings


async def get_reranker(
    client:aiohttp.ClientSession,
    query: str,
    instruction:str=None,
    documents:list[str]|str=None
) -> list[dict]:
    ...
    

async def main():
    with aiohttp.ClientSession(
        "http://172.29.1.239:9000/v1/",
        connector=aiohttp.TCPConnector(ssl=False,limit=80,),
        timeout=aiohttp.ClientTimeout(20.0),
    ) as client:
        ...
        
