import tkinter as tk
from tkinter import font, messagebox
from DialogueAgent import DialogueAgent
from datastructures.dialoguestate import DialogueState
from datastructures.dialogueact import DialogueAct
from datastructures.defaults import get_greet_act, get_root_state

# 1. Initialize the agent, dialogue state and dialogue act
agent = DialogueAgent()

#  Will store DialogueState between turns and keep track of the current dialogue state
state = get_root_state()
act = get_greet_act()


# 2. Function that gets called when the user clicks "Send" oder presses the "enter" key.
def chat_response():
    global state
    global act
    user_input = entry.get()
    if user_input.strip() == "":
        return

    # Check if user wants to exit and close the conversation (key words: cancel, exit, abort)
    if agent._isAbort(user_input):
        msg = """⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠒⠒⠢⢄⡀⠀⠀⢠⡏⠉⠉⠉⠑⠒⠤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡞⠀⠀⠀⠀⠀⠙⢦⠀⡇⡇⠀⠀⠀⠀⠀⠀⠈⠱⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠊⠉⠉⠙⠒⢤⡀⠀⣼⠀⠀⢀⣶⣤⠀⠀⠀⢣⡇⡇⠀⠀⢴⣶⣦⠀⠀⠀⢳⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢀⣠⠤⢄⠀⠀⢰⡇⠀⠀⣠⣀⠀⠀⠈⢦⡿⡀⠀⠈⡟⣟⡇⠀⠀⢸⡇⡆⠀⠀⡼⢻⣠⠀⠀⠀⣸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢀⠖⠉⠀⠀⠀⣱⡀⡞⡇⠀⠀⣿⣿⢣⠀⠀⠈⣧⣣⠀⠀⠉⠋⠀⠀⠀⣸⡇⠇⠀⠀⠈⠉⠀⠀⠀⢀⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣠⠏⠀⠀⣴⢴⣿⣿⠗⢷⡹⡀⠀⠘⠾⠾⠀⠀⠀⣿⣿⣧⡀⠀⠀⠀⢀⣴⠇⣇⣆⣀⢀⣀⣀⣀⣀⣤⠟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣿⠀⠀⢸⢻⡞⠋⠀⠀⠀⢿⣷⣄⠀⠀⠀⠀⠀⣠⡇⠙⢿⣽⣷⣶⣶⣿⠋⢰⣿⣿⣿⣿⣿⣿⠿⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⡿⡄⠀⠈⢻⣝⣶⣶⠀⠀⠀⣿⣿⣱⣶⣶⣶⣾⡟⠀⠀⠀⢈⡉⠉⢩⡖⠒⠈⠉⡏⡴⡏⠉⠉⠉⠉⠉⠉⠉⠉⡇⠀⠀⢀⣴⠒⠢⠤⣀
⢣⣸⣆⡀⠀⠈⠉⠁⠀⠀⣠⣷⠈⠙⠛⠛⠛⠉⢀⣴⡊⠉⠁⠈⢢⣿⠀⠀⠀⢸⠡⠀⠁⠀⠀⠀⣠⣀⣀⣀⣀⡇⠀⢰⢁⡇⠀⠀⠀⢠
⠀⠻⣿⣟⢦⣤⡤⣤⣴⣾⡿⢃⡠⠔⠒⠉⠛⠢⣾⢿⣿⣦⡀⠀⠀⠉⠀⠀⢀⡇⢸⠀⠀⠀⠀⠀⠿⠿⠿⣿⡟⠀⢀⠇⢸⠀⠀⠀⠀⠘
⠀⠀⠈⠙⠛⠿⠿⠿⠛⠋⢰⡋⠀⠀⢠⣤⡄⠀⠈⡆⠙⢿⣿⣦⣀⠀⠀⠀⣜⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⢀⠃⠀⡸⠀⠇⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⢣⠀⠀⠈⠛⠁⠀⢴⠥⡀⠀⠙⢿⡿⡆⠀⠀⢸⠀⢸⢰⠀⠀⠀⢀⣿⣶⣶⡾⠀⢀⠇⣸⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⡀⢇⠀⠀⠀⢀⡀⠀⠀⠈⢢⠀⠀⢃⢱⠀⠀⠀⡇⢸⢸⠀⠀⠀⠈⠉⠉⠉⢱⠀⠼⣾⣿⣿⣷⣦⠴⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢱⠘⡄⠀⠀⢹⣿⡇⠀⠀⠈⡆⠀⢸⠈⡇⢀⣀⣵⢨⣸⣦⣤⣤⣄⣀⣀⣀⡞⠀⣠⡞⠉⠈⠉⢣⡀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢃⠘⡄⠀⠀⠉⠀⠀⣠⣾⠁⠀⠀⣧⣿⣿⡿⠃⠸⠿⣿⣿⣿⣿⣿⣿⠟⠁⣼⣾⠀⠀⠀⠀⢠⠇⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡄⠹⣀⣀⣤⣶⣿⡿⠃⠀⠀⠀⠈⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠀⠀⢻⣿⣷⣦⣤⣤⠎⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣤⣿⡿⠟⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠉⠀⠀⠀⠀⠀"""

        chat_log.insert(tk.END, msg + "\n\n", "bot")
        chat_log.see(tk.END)
        entry.delete(0, tk.END)
        send_button.config(state=tk.DISABLED)
        root.bind("<Return>", lambda x: x)
        return

    # Insert user's input as part of this round
    chat_log.insert(tk.END, f"👤 You: {user_input}\n\n", "user")

    # Normal dialogue response using the Dialogueagent pipeline
    response, new_state, act = agent._dialoguePipeline(user_input, state, act)
    chat_log.insert(tk.END, f"🤖 Bot: {response}\n\n", "bot")

    # If "goodbye intent" recognized by NLU (in the last step), the bot should say confirm and then say goodbye, but restart with greeting instead of close the conversation
    if new_state and new_state.slots.get("goodbye", False):
        greet_act = DialogueAct("greet", {})
        greet_text = agent.nlg.generate(greet_act)
        chat_log.insert(tk.END, f"🤖 Bot: {greet_text}\n\n", "bot")
        state = get_root_state()
    else:
        state = new_state

    # Clear input box
    entry.delete(0, tk.END)
    chat_log.see(tk.END)


# 3. Set up main GUI Window
root = tk.Tk()
root.title("Find Restaurant Assistant")
root.geometry("680x680")
root.configure(bg="#e9eef2")  # Soft blue-gray for background color
root.resizable(False, False)

# 4. Set up text font style
text_font = font.Font(family="Helvetica", size=12)

# 5. Set up chat dialay window
chat_log = tk.Text(
    root,
    height=30,
    width=70,
    font=text_font,
    bg="white",
    fg="#2b2b2b",
    wrap=tk.WORD,
    padx=12,
    pady=12,
    bd=0,
    relief=tk.FLAT,
)
chat_log.pack(padx=15, pady=15)

# 6. Message tag styles
chat_log.tag_config("user", foreground="#007ACC", font=("Helvetica", 11, "bold"))
chat_log.tag_config("bot", foreground="#228B22", font=("Helvetica", 11, "bold"))
chat_log.tag_config("ascii", foreground="#228B22", font=("Courier", 9))
chat_log.tag_config("welcome", foreground="#666666", font=("Helvetica", 13))
chat_log.tag_config("separator", foreground="#cccccc")


# 7. Display static introduction message (not part of conversation)
welcome_text = (
    "💡 Welcome!\n"
    "\n"
    "I can help you find restaurants in Cambridge. Tell me your food, area, and price range preferences.\n"
    'If you do not have any preference yet, try typing: "Surprise me".\n'
)
chat_log.insert(tk.END, welcome_text, "welcome")

# Add a horizontal separator (visual line)
chat_log.insert(
    tk.END, "────────────────────────────────────────────────────\n\n", "separator"
)

# 8. Then immediately show bot greeting as first message (Show Bot greeting as Round 0 start)
greet_act = DialogueAct("greet", {})
greet_text = agent.nlg.generate(greet_act)
chat_log.insert(tk.END, f"🤖 Bot: {greet_text}\n\n", "bot")

# 9. User input field and send button container
input_frame = tk.Frame(root, bg="#e9eef2")
input_frame.pack(padx=15, pady=(0, 15), fill=tk.X)

entry = tk.Entry(
    input_frame,
    font=text_font,
    bg="white",
    fg="#000",
    relief=tk.FLAT,
    highlightthickness=1,
    highlightbackground="#ccc",
)
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)

# Send button
send_button = tk.Button(
    input_frame,
    text="Send",
    command=chat_response,
    bg="#4CAF50",
    fg="white",
    activebackground="#45a049",
    font=("Helvetica", 10, "bold"),
    relief=tk.FLAT,
    bd=0,
    padx=12,
    pady=6,
)
send_button.pack(side=tk.RIGHT, padx=(10, 0))

# 10. Allow "Enter" key to send message
root.bind("<Return>", lambda event: chat_response())

# 11. Start GUI loop
root.mainloop()
