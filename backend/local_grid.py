"""In-process ``Grid``: drives real ``ClientApp`` handlers without Ray or a SuperLink.

The AgentApp process on SuperGrid has no ``Grid`` — ``@app.main()`` receives only
``(agent, context)`` — and the runtime strips every ``flwr`` requirement from the app's
dependencies, so ``flwr.simulation.run_simulation`` cannot be imported there either.

This shim closes that gap. It implements ``Grid`` by calling ``ClientApp`` instances
directly, one ``Context`` per firm, so the same round loop runs unchanged in the harness
(``backend.agent_app``) and in the federated surface (``backend.server_app``).
"""

from collections.abc import Iterable

from flwr.app import Context, Message, RecordDict
from flwr.clientapp import ClientApp
from flwr.serverapp import Grid
from flwr.supercore.run import Run


class LocalGrid(Grid):
    """Dispatch coordinator messages straight into per-node ``ClientApp`` instances.

    Node isolation is by ``Context``: each firm gets its own ``node_config`` and its own
    ``state``, and nothing but a ``Message`` crosses between them.
    """

    def __init__(self, client_app: ClientApp, contexts: dict[int, Context]) -> None:
        self._client_app = client_app
        self._contexts = contexts
        self._run: Run | None = None
        self._replies: dict[str, Message] = {}

    def set_run(self, run: Run) -> None:
        """Set the run this grid operates in."""
        self._run = run

    def run(self) -> Run:
        """Run information."""
        if self._run is None:
            raise RuntimeError("LocalGrid has no run set.")
        return self._run

    def create_message(  # noqa: D102
        self,
        content: RecordDict,
        message_type: str,
        dst_node_id: int,
        group_id: str,
    ) -> Message:
        return Message(
            content=content,
            message_type=message_type,
            dst_node_id=dst_node_id,
            group_id=group_id,
        )

    def get_node_ids(self) -> Iterable[int]:
        """Get node IDs."""
        return list(self._contexts)

    def push_messages(self, messages: Iterable[Message]) -> Iterable[str]:
        """Run each message through its destination node and hold the reply."""
        message_ids = []
        for message in messages:
            context = self._contexts[message.metadata.dst_node_id]
            self._replies[message.object_id] = self._client_app(message, context)
            message_ids.append(message.object_id)
        return message_ids

    def pull_messages(self, message_ids: Iterable[str]) -> Iterable[Message]:
        """Collect the replies held for the given message IDs."""
        return [self._replies.pop(mid) for mid in message_ids if mid in self._replies]

    def send_and_receive(self, messages: Iterable[Message], **kwargs: object) -> Iterable[Message]:
        """Push messages and pull their replies."""
        return self.pull_messages(self.push_messages(messages))
