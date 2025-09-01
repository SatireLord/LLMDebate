"""Simple Tkinter GUI wrapper around the LLMDebate demo.

This module exposes a tiny desktop interface so users can run the debate
application without touching the command line.  It is intentionally small and
well commented to remain approachable for beginners while leaving room for
future expansion.

The GUI allows you to:
* Enter a debate topic, number of turns and optional RNG seed.
* Display the transcript in a scrollable text box.
* Copy the transcript to the clipboard or save it to a ``.txt`` file.

The code is fully cross-platform but was written with macOS bundling in mind.
Use a tool like ``pyinstaller`` to generate a ``.app`` bundle.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from debate import run_debate


class DebateApp(tk.Tk):
    """Main application window for the debate GUI."""

    def __init__(self) -> None:
        super().__init__()
        self.title("LLM Debate")
        # Make the window a reasonable default size; users can resize freely.
        self.geometry("700x500")

        # Build all widgets (inputs, buttons, output box).
        self._build_widgets()

    # ------------------------------------------------------------------
    # UI Construction helpers
    # ------------------------------------------------------------------
    def _build_widgets(self) -> None:
        """Create and place all widgets in the window."""

        # Row 0: topic label + entry
        tk.Label(self, text="Topic:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.topic_var = tk.StringVar()
        tk.Entry(self, textvariable=self.topic_var).grid(
            row=0, column=1, columnspan=3, sticky="we", padx=5, pady=5
        )

        # Row 1: turns and seed inputs
        tk.Label(self, text="Turns:").grid(row=1, column=0, sticky="w", padx=5)
        self.turns_var = tk.IntVar(value=6)
        tk.Spinbox(self, from_=1, to=20, textvariable=self.turns_var, width=5).grid(
            row=1, column=1, sticky="w", padx=5
        )

        tk.Label(self, text="Seed (optional):").grid(row=1, column=2, sticky="e", padx=5)
        self.seed_var = tk.StringVar()
        tk.Entry(self, textvariable=self.seed_var, width=10).grid(
            row=1, column=3, sticky="w", padx=5
        )

        # Row 2: run button spanning all columns
        tk.Button(self, text="Run Debate", command=self._on_run).grid(
            row=2, column=0, columnspan=4, pady=5
        )

        # Row 3: text output area with a vertical scrollbar
        self.output = tk.Text(self, wrap="word")
        scroll = tk.Scrollbar(self, command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        self.output.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=(5, 0), pady=5)
        scroll.grid(row=3, column=3, sticky="ns", padx=(0, 5), pady=5)

        # Row 4: copy and save buttons
        tk.Button(self, text="Copy to Clipboard", command=self._copy_output).grid(
            row=4, column=0, sticky="w", padx=5, pady=5
        )
        tk.Button(self, text="Save Transcript", command=self._save_output).grid(
            row=4, column=1, sticky="w", padx=5, pady=5
        )

        # Make the text area expand with the window.
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_run(self) -> None:
        """Trigger a debate run in a background thread."""

        topic = self.topic_var.get().strip()
        if not topic:
            messagebox.showerror("Input Error", "Please enter a debate topic.")
            return

        try:
            seed = int(self.seed_var.get()) if self.seed_var.get() else None
        except ValueError:
            messagebox.showerror("Input Error", "Seed must be an integer.")
            return

        turns = self.turns_var.get()
        self.output.delete("1.0", tk.END)

        def worker() -> None:
            """Run the debate and display results once complete."""
            transcript = run_debate(topic, turns=turns, seed=seed)
            self.output.insert(tk.END, transcript)

        # Running in a thread keeps the UI responsive during generation.
        threading.Thread(target=worker, daemon=True).start()

    def _copy_output(self) -> None:
        """Copy the transcript to the clipboard for easy sharing."""

        text = self.output.get("1.0", tk.END)
        if not text.strip():
            messagebox.showinfo("Nothing to copy", "Run a debate first.")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", "Transcript copied to clipboard.")

    def _save_output(self) -> None:
        """Save the transcript to a ``.txt`` file chosen by the user."""

        text = self.output.get("1.0", tk.END)
        if not text.strip():
            messagebox.showinfo("Nothing to save", "Run a debate first.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text Files", "*.txt")]
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)


if __name__ == "__main__":
    # Creating an instance of the application and starting Tk's main loop
    # makes the window appear and handle user interaction.
    app = DebateApp()
    app.mainloop()
