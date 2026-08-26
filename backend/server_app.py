"""Coordinator: RFP decomposition, round orchestration, gap broadcast, SF330 assembly."""

from flwr.app import ConfigRecord, Context, Message, MessageType, RecordDict
from flwr.serverapp import Grid, ServerApp

app = ServerApp()


@app.main()
def main(grid: Grid, context: Context) -> None:
    """Run the three-round protocol: blind bidding, gap re-examination, disclosure."""
    num_rounds = int(context.run_config["num-rounds"])

    for server_round in range(1, num_rounds + 1):
        content = RecordDict({"round": ConfigRecord({"server_round": server_round})})
        messages = [
            Message(
                content=content,
                message_type=MessageType.QUERY,
                dst_node_id=node_id,
                group_id=str(server_round),
            )
            for node_id in grid.get_node_ids()
        ]
        replies = list(grid.send_and_receive(messages))
        print(f"[coordinator] round {server_round}: {len(replies)} replies")
