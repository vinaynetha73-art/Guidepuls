import json
from channels.generic.websocket import AsyncWebsocketConsumer

class EmergencyConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.room_group_name = "emergency_alerts"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def send_alert(self, event):

        await self.send(text_data=json.dumps({
            "alert": event["alert"]
        }))