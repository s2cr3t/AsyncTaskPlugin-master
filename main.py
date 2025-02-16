from baidusearch import search  # Import baidusearch library
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost
from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *  # 导入事件类
from datetime import datetime, timedelta
import dateparser
from typing import List, Tuple
import logging
import re
import os
import shutil
import yaml
import time
import asyncio
import pkg.platform.types as platform_types
from . import mux, webpilot
import json
backend_mapping = {
    "webpilot": webpilot.process,
    "native": mux.process,
}


process: callable = None
config: dict = None
selfs = None
ctxs: EventContext = None;
# Register plugin
# 异步初始化

@register(name="Async_Task_runner", description="基于GPT的函数调用能力，为QChatGPT提供定时任务功能", version="0.1.0", author="s2cr3t")
class AsyncTask(Plugin):
    async def initialize(self):
        pass
    def __init__(self, host: APIHost):
        pass

    @llm_func("Async_Task_runner")
    async def _(self, query, messages: str, end_time: str, interval_minutes: int):
        """Call this function to create a async task when asking to do something in some time
        - Explain clearly the things you need to do 
        - This function will return the things you need to do 

        Args:
            messages(str): The message content that you want to send periodically. It can be any string (e.g., "Reminder", "Notification").
            end_time(str): The end time of the range when the message generation stops. Should be in a flexible time format like '1 minute later', '1 hour later', 'today at 5 pm', etc.
            interval_minutes(int): The interval in minutes between each generated message. For example, if set to 15, the message will be generated every 15 minutes within the time range.

        Returns:
            list of tuples: Each tuple contains a timestamp (in string format "YYYY-MM-DD HH:MM:SS") and the corresponding message. If the input range is valid and the intervals are calculated correctly, the list will include all the messages with their respective timestamps within the time range.
        """
        try:
            # 将 query 存入一个 JSON 文件
            with open('query_data.txt', 'w') as f:
                f.write(str(query))

            target_info = {
            "target_id": str(query.launcher_id), 
            "target_type": str(query.launcher_type).split(".")[-1].lower(),  # 获取枚举值的小写形式
            }
            self.target_id = target_info["target_id"]
            self.target_type = target_info["target_type"]
            asyncio.create_task(self.runTask(messages, end_time, interval_minutes))
            return "定时任务设置完成"  # Immediate response
        except Exception as e:
            logging.error("[Async_Task_runner] error: {}".format(e))
            return f"Error occurred: {e}"

    async def runTask(self, messages: str, end_time: str, interval_minutes: int):
        start_time = datetime.now()
        
        end_time_parsed = dateparser.parse(end_time)
        if end_time_parsed is None:
            raise ValueError(f"Unable to parse the end time: {end_time}")
        end_time = end_time_parsed
        current_time = start_time
        result_messages = []  

        # 启动后台任务
        await self.replytask(messages, end_time, interval_minutes, current_time, result_messages)


    async def replytask(self, messages: str, end_time: str, interval_minutes: int, current_time: datetime, result_messages: list):
        # 每次检查时间，确保不超出end_time
        while current_time <= end_time:
            #print(f"Current time: {current_time}, End time: {end_time}")
            result_messages.append((current_time.strftime("%Y-%m-%d %H:%M:%S"), messages))
            #print(f"Scheduled message at {current_time.strftime('%Y-%m-%d %H:%M:%S')}: {messages}")
            
            await asyncio.sleep(interval_minutes * 60)

            current_time = datetime.now()

            if current_time > end_time:
                break

        await self.host.send_active_message(
                    adapter=self.host.get_platform_adapters()[0],
                    target_type=self.target_type,
                    target_id=self.target_id,
                    message=platform_types.MessageChain([
                        platform_types.Plain("@" + str(self.target_id) + " " + messages)
                    ])
                )


    # Triggered when plugin is uninstalled
    def __del__(self):
        pass

