import socketio
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")

def register_socket_events(sio):
    @sio.event
    async def connect(sid, environ):
        print(f"✅ Cliente conectado: {sid}")

    @sio.event
    async def disconnect(sid):
        print(f"❌ Cliente desconectado: {sid}")

    @sio.event
    async def join_user_room(sid, user_id):
        await sio.enter_room(sid, f"user_{user_id}")
        print(f"🎯 Cliente {sid} entrou na sala user_{user_id}")




    # Codigo de mandar mensagem notificacao com socket

    # await sio.emit(
    #         'trophy_unlocked',
    #         {
    #             "title": "Completou 20 tarefas!",
    #             "description": "Você completou 20 tarefas. Continue assim! 💪"
    #         },
    #         room=f"user_{user_id}"
    #     )