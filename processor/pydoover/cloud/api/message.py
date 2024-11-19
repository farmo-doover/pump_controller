import json, time, csv
from datetime import datetime
from typing import Any


class Message:

    def __init__(self, client, data, channel_id=None, agent_id=None, channel_name=None):
        
        self.id = None
        self.timestamp = None

        self.client = client
        self.channel_id = channel_id
        self.agent_id = agent_id
        self.channel_name = channel_name
        self._payload = None

        if data is not None:
            self._from_data(data)

    def __repr__(self):
        if self._payload is not None:
            return f"<Message message_id={self.id}, payload={self._payload}>"
        return f"<Message message_id={self.id}>"

    def _from_data(self, data: dict[str, Any]):
        # {'agent': '9fb5d629-ce7f-4b08-b17a-c267cbcd0427', 'message': 'a7b493dd-4577-4f81-ac3d-f1b3be680b12', 'type': 'base', 'timestamp': 1715646840.250541}
        self.id = data.get("message", None)
        self.agent_id = data.get("agent", None)
        self.channel_name = data.get("channel_name", None)
        self.timestamp = data.get("timestamp", None)

        if not self.channel_id:
            self.channel_id = data.get("channel")

        self._payload = data.get("payload")

    def to_dict(self):
        return {
            "message": self.id,
            "agent": self.agent_id,
            "timestamp": self.timestamp,
            "channel": self.channel_id,
            "channel_name": self.channel_name,
            "payload": self._payload
        }

    def update(self):
        data = self.client._get_message_raw(self.channel_id, self.id)
        self._from_data(data)

    def delete(self):
        self.client._delete_message_raw(self.channel_id, self.id)

    def fetch_payload(self):
        if self._payload is not None:
            return self._payload

        data = self.client._get_message_raw(self.channel_id, self.id)
        self._payload = json.loads(data["payload"])
        return self._payload

    def get_age(self):
        return time.time() - self.timestamp

    def get_timestamp(self):
        return datetime.fromtimestamp(self.timestamp)

    @staticmethod
    def from_csv_export(client, csv_file_path):
        
        messages = []

        # Open and read the CSV file using the csv module
        with open(csv_file_path, 'r', newline='') as file:
            reader = csv.DictReader(file)  # Use DictReader to handle headers

            for row in reader:
                # Extract data from the row
                key = row['Key']
                timestamp = row['Timestamp (UTC)']
                channel_name = row['Channel']
                channel_id = row['Channel ID']
                agent_name = row['Agent']
                agent_id = row['Agent ID']
                payload = row['Payload']

                # Convert timestamp to UTC epoch timestamp
                timestamp = datetime.fromisoformat(timestamp).timestamp()

                # Create a Message instance
                message = Message(
                    client,
                    data=None,
                    channel_id=channel_id,
                    agent_id=agent_id,
                    channel_name=channel_name
                )

                message.id = key
                message.timestamp = timestamp
                message._payload = json.loads(payload)

                messages.append(message)

        # Sort the messages by timestamp
        messages.sort(key=lambda x: x.timestamp)

        return messages
