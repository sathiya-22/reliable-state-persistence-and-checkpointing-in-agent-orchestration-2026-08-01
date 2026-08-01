import pickle
import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel
from agent_checkpoint.db import SQLiteManager

class Checkpoint(BaseModel):
    id: str
    timestamp: datetime.datetime
    state: bytes

class AgentCheckpoint:
    """
    Manages the persistence and retrieval of agent states using SQLite.
    """

    def __init__(self, db_path: str = "agent_state.db"):
        self.db_manager = SQLiteManager(db_path)

    def save_state(self, agent_id: str, state: Any) -> None:
        """
        Saves the current state of an agent to the database.
        The state object is serialized using pickle.
        """
        serialized_state = pickle.dumps(state)
        timestamp = datetime.datetime.now()
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO checkpoints (id, timestamp, state) VALUES (?, ?, ?)",
                (agent_id, timestamp, serialized_state)
            )
            conn.commit()
        print(f"[{timestamp}] Checkpoint saved for agent '{agent_id}'.")

    def load_state(self, agent_id: str) -> Optional[Any]:
        """
        Loads the last saved state for a given agent ID.
        Returns None if no state is found.
        """
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, timestamp, state FROM checkpoints WHERE id = ? ORDER BY timestamp DESC LIMIT 1",
                (agent_id,)
            )
            row = cursor.fetchone()

        if row:
            checkpoint_data = Checkpoint(
                id=row[0],
                timestamp=datetime.datetime.fromisoformat(row[1]),
                state=row[2]
            )
            deserialized_state = pickle.loads(checkpoint_data.state)
            print(f"[{checkpoint_data.timestamp}] Checkpoint loaded for agent '{agent_id}'.")
            return deserialized_state
        print(f"No checkpoint found for agent '{agent_id}'.")
        return None

    def delete_state(self, agent_id: str) -> None:
        """Deletes all saved states for a given agent ID."""
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM checkpoints WHERE id = ?", (agent_id,))
            conn.commit()
        print(f"All checkpoints deleted for agent '{agent_id}'.")
