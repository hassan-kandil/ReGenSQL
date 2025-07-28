from typing import Dict, List

import time
import openai

from src.config import logger

from llama_index.core.llms import LLM
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core import Settings


def chat(messages: List[Dict]) -> str:
    chat_messages = [ChatMessage(**m) for m in messages]
    start = time.time()
    response = Settings.llm.chat(chat_messages)
    logger.debug({"messages": messages, "response": response.message.content, "time": time.time() - start})
    print(f"Response for messages: {messages} is {response.message.content[:100]} in {time.time() - start:.2f} seconds")
    return response.message.content


async def achat(messages: List[Dict], model: LLM = None) -> str:
    if model is None:
        model = Settings.llm
    chat_messages = [ChatMessage(**m) for m in messages]
    start = time.time()
    try:
        response = await model.achat(chat_messages)
    except (ConnectionResetError, openai.APIConnectionError):
        time.sleep(5)
        response = await model.achat(chat_messages)
    logger.debug({"messages": messages, "response": response.message.content, "time": time.time() - start})
    print(f"Response for messages: {messages} is {response.message.content[:100]} in {time.time() - start:.2f} seconds")
    return response.message.content
