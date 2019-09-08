import asyncio
import functools

from nonebot import CommandSession

from .a import EvalGrammar



## interacts with none bot

def botSpeaksMsg(s: str, session: CommandSession, tasks: list):
    if len(s) > 400:
        s = s[:400] + '\n文本过长已截断.'
    tasks.append(session.send(
        s.replace(r'\n', '\n').replace(r'\t', '\t')
    ))


def botSendsMsgToAGroup(s: str, bot, group_id, tasks: list):
    tasks.append(
        bot.send_group_msg(group_id=group_id, message=s)
    )


def botWaits(t: int, session: CommandSession, tasks: list):
    if t < 0 or t > 180:
        raise ValueError('"wait" expects sleeping time less than 180s.')
    tasks.append(asyncio.sleep(t))


## run


async def runScriptLang(code: str, session: CommandSession):
    'group member calls the bot to run script'

    tasks = []

    addd = functools.partial(botSpeaksMsg, session=session, tasks=tasks)

    try:
        x = EvalGrammar(code, externalFunctions={
            'speak': addd,
            'wait': functools.partial(botWaits, session=session, tasks=tasks)
        })
        x.exec_in_global()
    except Exception as exc:
        addd('ERROR: ' + str(exc) + ' --TERMINAING')
    
    if len(tasks) > 20:
        await session.send('过多的命令不会被处理.正在退出.')
        return
    for co in tasks:
        await co


async def runScriptLangAdmin(code: str, bot, session, group_id):
    'admin, in private chat, lets the bot to run script and redirects output to a group'
    tasks = []
    try:
        x = EvalGrammar(code, externalFunctions={
            'speak': functools.partial(botSendsMsgToAGroup, bot=bot, group_id=group_id, tasks=tasks),
            'wait': functools.partial(botWaits, session=None, tasks=tasks)
        })
    except Exception as exc:
        botSpeaksMsg('ERROR: ' + str(exc) + ' --TERMINAING', session, tasks)
    x.exec_in_global()
    for co in tasks:
        await co