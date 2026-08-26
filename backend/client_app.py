"""Firm node: local search, matcher agent, bander, and the BD approval gate."""

from flwr.app import ConfigRecord, Context, Message, RecordDict
from flwr.clientapp import ClientApp

app = ClientApp()


@app.query()
def query(msg: Message, context: Context) -> Message:
    """Answer a coordinator round with this firm's attestations."""
    server_round = int(msg.content["round"]["server_round"])
    reply = RecordDict({"ack": ConfigRecord({"server_round": server_round})})
    return Message(content=reply, reply_to=msg)
