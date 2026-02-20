import subprocess
import time
import os

# AAPKA EXACT PATH
CLAUDE_PATH = r"C:\Users\Admin\AppData\Roaming\npm\claude.cmd"
VAULT_PATH = r"C:\Users\Admin\Desktop\HACKATHON-0\AI_Employee_Vault"
ACTION_FOLDER = os.path.join(VAULT_PATH, "02_Needs_Action")

def run_claude_agent():
    # Pehle check karte hain ke kya file waqai wahan hai
    if not os.path.exists(CLAUDE_PATH):
        print(f"❌ ERROR: Claude file nahi mili! Path check karein: {CLAUDE_PATH}")
        return

    # Check tasks
    if not os.path.exists(ACTION_FOLDER):
        print(f"❌ Folder nahi mila: {ACTION_FOLDER}")
        return

    files = [f for f in os.listdir(ACTION_FOLDER) if f.endswith('.md') or f.endswith('.txt')]
    
    if not files:
        print("😴 Inbox khali hai... Task ka intezar hai.")
        return

    print(f"🎯 {len(files)} tasks mile! Claude kaam shuru kar raha hai...")

    master_prompt = "Read files in 02_Needs_Action, create a Plan.md, and process the tasks."

    try:
        # Pura path use karke run kar rahe hain
        subprocess.run([CLAUDE_PATH, "-p", master_prompt], shell=True, check=True)
        print("✅ Task complete!")
    except Exception as e:
        print(f"❌ Ab bhi koi masla hai: {e}")

if __name__ == "__main__":
    print("🚀 Silver Tier Loop Active!")
    print(f"📂 Monitoring: {ACTION_FOLDER}")
    while True:
        run_claude_agent()
        time.sleep(60)