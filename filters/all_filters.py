from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message

from languages.lang_controller import get_string


class TextEquals(BoundFilter):
    def __init__(self, string_code):
        self.string_code = string_code

    async def check(self, message: Message):
        if message.text == get_string(self.string_code):
            return True
        return False
