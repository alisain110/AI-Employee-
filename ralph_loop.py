import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/ralph_loop.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RalphWiggumLoop:
    """
    Implements the Ralph Wiggum persistence loop pattern
    Keeps Claude working until a task is complete
    """

    def __init__(self, vault_path: str, max_iterations: int = 10):
        self.vault_path = Path(vault_path)
        self.max_iterations = max_iterations
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'

    def run_task(self, task_description: str, completion_condition=None):
        """
        Run a task with persistence until completion

        Args:
            task_description: Description of the task to be completed
            completion_condition: Function that returns True when task is complete
        """
        iteration = 0

        logger.info(f"Starting Ralph Wiggum loop for task: {task_description}")
        logger.info(f"Max iterations: {self.max_iterations}")

        while iteration < self.max_iterations:
            try:
                logger.info(f"Iteration {iteration + 1}")

                # Check if task is complete using the completion condition
                if completion_condition:
                    if completion_condition():
                        logger.info("Task completed successfully!")
                        return True
                else:
                    # Default completion check: no more files in Needs_Action
                    if not list(self.needs_action.glob('*.md')):
                        logger.info("No more files in Needs_Action - task considered complete")
                        return True

                # Process any available files
                needs_action_files = list(self.needs_action.glob('*.md'))
                if needs_action_files:
                    logger.info(f"Found {len(needs_action_files)} files to process")
                    for file_path in needs_action_files:
                        self.process_file(file_path)
                else:
                    logger.info("No files to process in this iteration")

                iteration += 1
                time.sleep(2)  # Brief pause between iterations

            except KeyboardInterrupt:
                logger.info("Ralph Wiggum loop interrupted by user")
                return False
            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {e}")
                iteration += 1
                time.sleep(5)  # Wait longer after error

        logger.warning(f"Max iterations ({self.max_iterations}) reached. Task may be incomplete.")
        return False

    def process_file(self, file_path: Path):
        """Process a file and potentially create follow-up tasks"""
        try:
            content = file_path.read_text()
            logger.info(f"Processing file: {file_path.name}")

            # Simple processing logic
            # In a real implementation, this would call Claude Code to process the file
            if "incomplete" in content.lower():
                # Simulate task not being complete yet
                logger.info(f"File {file_path.name} indicates task is incomplete")
            else:
                # Move file to Done as it's been processed
                done_path = self.done / file_path.name
                file_path.rename(done_path)
                logger.info(f"Moved {file_path.name} to Done")

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")

def main():
    """Example usage of the Ralph Wiggum loop"""
    vault_path = Path.cwd()

    def completion_check():
        """Example completion condition: check if all tasks are done"""
        needs_action = vault_path / 'Needs_Action'
        return len(list(needs_action.glob('*.md'))) == 0

    ralph_loop = RalphWiggumLoop(str(vault_path))

    success = ralph_loop.run_task(
        "Process all files in Needs_Action folder",
        completion_condition=completion_check
    )

    if success:
        print("Task completed successfully!")
    else:
        print("Task did not complete within the iteration limit.")

if __name__ == "__main__":
    main()