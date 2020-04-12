
import asyncio
import os
from time import time

import async_timeout
from nonebot import CommandSession, log, on_command, get_bot
from nonebot.permission import *

from .run_client import runScriptLang, runScriptLangAdmin

__plugin_name__ = '脚本'
__plugin_usage__ = f'''feature: 利用脚本来控制我
用法：启动脚本

以下程序赋值 "hello" 语句到变量 a 和 b 中并且打印，两句话间隔一秒：
setv a = "hello"
setv b = "world"
speak a
wait 1
speak b
'''


lastCall = time()
COOLDOWN = 15

@on_command('启动脚本', aliases=('脚本', 'script', 'script:'), permission=SUPERUSER | GROUP_MEMBER)
async def run_script(session: CommandSession):
    global lastCall
    if time() - lastCall <= COOLDOWN:
        await session.send(f'技能冷却中…… ({COOLDOWN}s)')
        return
    log.logger.debug(f'user {session.event["user_id"]} is trying to run a script')
    code: str = session.get('code')
    async with async_timeout.timeout(300):
        try:
            await runScriptLang(code, session)
        except asyncio.CancelledError:
            await session.send('任务超时，已经停止.', at_sender=True)
        finally:
            lastCall = time()


@run_script.args_parser
async def _(session: CommandSession):
    argsStripped: str = session.current_arg_text.strip()
    if not argsStripped:
        session.finish()
    else:
        session.state['code'] = argsStripped


@on_command('启动脚本到群', aliases=('scriptto', 'scriptto:'), permission=SUPERUSER)
async def run_script_A(session: CommandSession):
    bot = get_bot()
    groupId, code = session.get('group'), session.get('code')
    await session.send('脚本开始执行.')
    await runScriptLangAdmin(code, bot, session, groupId)
    await session.send('脚本执行完毕.')


@run_script_A.args_parser
async def arg_parser_x(session: CommandSession):
    argStripped = session.current_arg.strip()
    paramSplit = argStripped.split('\n', 1)
    if len(paramSplit) == 2:
        session.state['group'] = paramSplit[0]
        session.state['code'] = paramSplit[1]
    else:
        await session.send('用法：scriptto [群号] [这里空行] [code]')
        session.finish()
