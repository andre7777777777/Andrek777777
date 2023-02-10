import asyncio
import os
import copy

from dataclasses import dataclass

from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message
from aiogram import Bot, Dispatcher, executor, types
from icmplib import async_multiping, async_ping

API_TOKEN = '6055954803:AAH0tDtbUhGRX1eC3aWFU09_bbfzY13zScM'


bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)



@dataclass
class Server:
    host: str
    owner_id: int
    status: bool


    
class Watcher:
    
    def __init__(self) -> None:
        self.servers = []
        
    
    def add_server(self, server: Server):
        self.servers.append(server)
    
        
    async def check_online(self, server: Server) -> bool:
        response = await async_ping(server.host, timeout=1, count=1)
        return response.is_alive
    
    
    async def send_alert(self, server: Server):
        await bot.send_message(
            chat_id=server.owner_id,
            text=f"Сервер {server.host} теперь {'онлайн' if server.status else 'оффлайн'}"
        )        
        
        
    def server_by_host(self, host):
        for server in self.servers:
            if server.host == host:
                return server
            
            
    async def watch(self):
        while True:
            if len(self.servers) == 0:
                await asyncio.sleep(1)
                continue
            results = await async_multiping([server.host for server in self.servers], timeout=5)
            for server, result in zip(self.servers, results):
                # print(result)
                if result.is_alive == server.status:
                    continue
                new_server = copy.deepcopy(server)
                new_server.status = result.is_alive
                self.servers.remove(server)
                self.servers.append(new_server)
                try:
                    await self.send_alert(new_server)
                except Exception as e:
                    print(e)
            
            
watcher = Watcher()              
       
       
@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.answer("Добро пожаловать в бота. \nВведите /add {адресс} для добавления роутера")


@dp.message_handler(commands=['add'])
async def add_ip(message: Message):
    args = message.get_args()
    if not args:
        await message.answer("Не верно введена команда")
        return
    server_host = args
    server = Server(server_host, message.from_id, True)
    is_online = await watcher.check_online(server)
    if is_online:
        watcher.add_server(server)
        await message.answer("Сервер добавлен в мониторинг")
        await message.answer(f"Сервер {server.host} теперь {'онлайн' if server.status else 'оффлайн'}")
    else:
        await message.answer("Сервер офлайн")
        
    
    

async def startup(dp):
    print("Бот запустился")
    asyncio.create_task(watcher.watch())
    
    
if __name__ == "__main__":
    executor.start_polling(dp, on_startup=startup)