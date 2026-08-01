import time
import os
from agent_checkpoint.core import AgentCheckpoint

# Define a simple agent class whose state we want to persist
class MyAgent:
    def __init__(self, agent_id: str, initial_step: int = 0, initial_data: list = None):
        self.agent_id = agent_id
        self.current_step = initial_step
        self.processed_data = initial_data if initial_data is not None else []
        self.is_running = False

    def process_item(self, item: str):
        print(f"Agent {self.agent_id}: Processing item '{item}' at step {self.current_step}")
        self.processed_data.append(f"Processed: {item}")
        self.current_step += 1
        time.sleep(0.5) # Simulate work

    def get_state(self):
        return {
            "agent_id": self.agent_id,
            "current_step": self.current_step,
            "processed_data": self.processed_data
        }

    @classmethod
    def from_state(cls, state: dict):
        return cls(state["agent_id"], state["current_step"], state["processed_data"])

    def run(self, data_stream: list, checkpoint_interval: int = 2, checkpoint_manager: AgentCheckpoint = None):
        self.is_running = True
        print(f"\nAgent {self.agent_id} starting from step {self.current_step} with {len(self.processed_data)} items already processed.")
        
        for i, item in enumerate(data_stream[self.current_step:]):
            try:
                self.process_item(item)
                if (self.current_step % checkpoint_interval == 0) and checkpoint_manager:
                    checkpoint_manager.save_state(self.agent_id, self.get_state())
            except KeyboardInterrupt:
                print(f"\nAgent {self.agent_id} interrupted. Saving final state...")
                if checkpoint_manager:
                    checkpoint_manager.save_state(self.agent_id, self.get_state())
                print(f"Agent {self.agent_id} gracefully stopped at step {self.current_step}.")
                self.is_running = False
                break
        
        if self.is_running:
            print(f"\nAgent {self.agent_id} finished all items. Final step: {self.current_step}")
            if checkpoint_manager:
                checkpoint_manager.save_state(self.agent_id, self.get_state()) # Save final state
            self.is_running = False


# --- Main execution ---
if __name__ == "__main__":
    AGENT_ID = "my_streaming_agent_001"
    DB_FILE = "agent_state.db"

    # Clean up previous run's DB for a fresh start if desired
    # if os.path.exists(DB_FILE):
    #     os.remove(DB_FILE)
    #     print(f"Removed previous database: {DB_FILE}")

    checkpoint_manager = AgentCheckpoint(db_path=DB_FILE)

    # Try to load existing state
    loaded_state = checkpoint_manager.load_state(AGENT_ID)

    if loaded_state:
        agent = MyAgent.from_state(loaded_state)
        print(f"Resumed agent {agent.agent_id} from step {agent.current_step} with {len(agent.processed_data)} processed items.")
        print(f"Already processed: {agent.processed_data}")
    else:
        agent = MyAgent(AGENT_ID)
        print(f"Starting new agent {agent.agent_id}.")

    # Simulate a data stream
    data_stream = [f"item_{i}" for i in range(20)]

    print("\nStarting agent run. Press Ctrl+C to simulate an unexpected interruption.")
    agent.run(data_stream, checkpoint_interval=3, checkpoint_manager=checkpoint_manager)

    print(f"\nAgent {agent.agent_id} run completed or interrupted.")
    print(f"Final processed items count: {len(agent.processed_data)}")
    # print(f"Final processed items: {agent.processed_data}")

    # You can inspect agent_state.db using a SQLite browser to see the stored data.
    # To demonstrate resume, stop this script with Ctrl+C and run it again.
