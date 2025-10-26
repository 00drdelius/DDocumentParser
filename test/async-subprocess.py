import asyncio
from asyncio import subprocess as asubprocess

async def func():
    cmds=[
        "which",
        "nginx"
    ]
    process = await asubprocess.create_subprocess_exec(
        *cmds,
        stdin=asubprocess.PIPE, # 进程通信的管道
        stdout=asubprocess.PIPE, # 进程通信的管道
        stderr=asubprocess.PIPE, # 进程通信的管道
    )
    print(process.returncode)
    # await process.wait() #NOTE process.wait() raises an error if output to stdout is too huge to be saved in pipe buffer 
    stdout, stderr = await process.communicate()
    print(process.returncode) #NOTE 0 if process processed properly.
    print(stdout)
    print(stderr)


if __name__ == '__main__':
    asyncio.run(func())