import tkinter as tk
from tkinter import font, messagebox
from DialogueAgent import DialogueAgent
from datastructures.dialoguestate import DialogueState
from datastructures.dialogueact import DialogueAct
from datastructures.defaults import get_greet_act, get_root_state

# 1. Initialize the agent, dialogue state, and dialogue act
agent = DialogueAgent()
state = get_root_state()
act = get_greet_act()


# 2. Function that gets called when the user clicks "Send" or presses the "Enter" key.
def chat_response():
    global state
    global act
    user_input = entry.get()
    if user_input.strip() == "":
        return

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

    chat_log.insert(tk.END, f"👤 You: {user_input}\n\n", "user")
    response, new_state, act = agent._dialoguePipeline(user_input, state, act)
    chat_log.insert(tk.END, f"🤖 Bot: {response}\n\n", "bot")

    if new_state and new_state.slots.get("goodbye", False):
        greet_act = DialogueAct("greet", {})
        greet_text = agent.nlg.generate(greet_act)
        chat_log.insert(tk.END, f"🤖 Bot: {greet_text}\n\n", "bot")
        state = get_root_state()
    else:
        state = new_state

    entry.delete(0, tk.END)
    chat_log.see(tk.END)


# Function to insert text into the entry box
def insert_text(text):
    entry.delete(0, tk.END)
    entry.insert(0, text)


# 3. Set up main GUI Window
root = tk.Tk()
root.title("Find Restaurant Assistant")
root.geometry("680x680")  # Increase the height to provide more space
root.configure(bg="#e9eef2")
root.resizable(False, False)

# 4. Set up text font style
text_font = font.Font(family="Helvetica", size=12)

# 5. Set up chat dialog window
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
chat_log.insert(
    tk.END, "────────────────────────────────────────────────────\n\n", "separator"
)

# 8. Show bot greeting as the first message
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
    bg="#75C93E",
    fg="white",
    activebackground="#3aaa2b",
    font=("Helvetica", 10, "bold"),
    relief=tk.FLAT,
    bd=0,
    padx=12,
    pady=6,
)
send_button.pack(side=tk.RIGHT, padx=(10, 0))

# 10. Create buttons for predefined texts
predefined_texts = [
    ("Hi", "#007ACC"),
    ("I don't know.", "#007ACC"),
    ("I want some good food.", "#007ACC"),
    ("I want to try italian food.", "#007ACC"),
    ("I don't care.", "#007ACC"),
    ("not expensivee please", "#007ACC"),
    ("I don't like this restaurant. Please recommend me another one.", "#007ACC"),
    ("I change my mind. I want to eat spanish food in the centre.", "#007ACC"),
    ("What's their phone number?", "#007ACC"),
    ("Do you have the description and signature dish of this restaurant?", "#007ACC"),
    ("Can you help me to reserve a place?", "#007ACC"),
    ("", "#B3B3B3"),
    ("cheap Italianan please.", "#EED91E"),
    ("Can you give me the description please?", "#EED91E"),
    ("Then i want to eat Pizza Hut.", "#EED91E"),
    ("surprise me!", "#AF1F7F"),
    ("i dont like this place", "#AF1F7F"),
    ("show me another one", "#AF1F7F"),
    ("Hi, i want to try german food.", "#09BE02"),
    ("north please.", "#09BE02"),
    ("cheap", "#09BE02"),
    ("Goodbye", "#CC0700"),
    ("Yes", "#CC0700"),
]


def open_predefined_buttons_window():
    button_window = tk.Toplevel(root)
    button_window.title("Predefined Messages")
    button_window.geometry("400x400")
    button_window.configure(bg="#e9eef2")

    # Create a frame for the buttons
    button_frame = tk.Frame(button_window, bg="#e9eef2")
    button_frame.pack(pady=10)

    # Add buttons for each predefined text in a grid layout
    for index, (text, color) in enumerate(predefined_texts):
        row = index // 3  # Determine the row index (0-based)
        column = index % 3  # Determine the column index (0-based)
        button = tk.Button(
            button_frame,
            text=text,
            command=lambda t=text: insert_text(t),
            bg=color,
            fg="white",
            font=("Helvetica", 10, "bold"),
            width=15,  # You can adjust the button width
        )
        button.grid(row=row, column=column, padx=5, pady=5)


open_predefined_buttons_window()

# 12. Start GUI loop
root.mainloop()
