import os
import sys
import wave
import shutil
from tkinter import (
    filedialog, Tk, Toplevel, Listbox, END, Scrollbar, RIGHT, Y,
    Button, BOTTOM, BooleanVar, Checkbutton, Label, Frame, PhotoImage
)
from tkinter import font
from pydub import AudioSegment
from PIL import Image, ImageTk

# ----------------------------
# Audio Processing Functions
# ----------------------------
def convert_to_stereo(audio):
    if audio.channels == 1:
        return AudioSegment.from_mono_audiosegments(audio, audio)
    return audio

def convert_audio(file_path, output_path, sample_rate):
    audio = AudioSegment.from_file(file_path)
    audio = convert_to_stereo(audio)
    audio = audio.set_sample_width(2).set_frame_rate(sample_rate)
    audio.export(output_path, format="wav")

def get_wav_properties(file_path):
    with wave.open(file_path, 'rb') as wav_file:
        channels = wav_file.getnchannels()
        framerate = wav_file.getframerate()
    return channels, framerate

# ----------------------------
# UI Functions
# ----------------------------
def open_folder_selector_ui():
    bg_color = "#2e2e2e"  # dark grey background
    fg_color = "white"    # white text for contrast
    accent_green = "#4caf50"

    root = Tk()
    
    icon_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(__file__)), "icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    
    root.title("TF2-Wave-Converter")
    root.geometry("500x500")
    root.resizable(False, False)
    root.configure(bg=bg_color)

    # Load and place image if it exists
    image_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(__file__)), "icon-test.png")
    if os.path.exists(image_path):
        try:
            img = Image.open(image_path)
            img = img.resize((96, 96), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            img_label = Label(root, image=img_tk, bg=bg_color)
            img_label.image = img_tk  # keep reference
            img_label.pack(pady=(45, 15))
        except Exception as e:
            print(f"Could not load image: {e}")

    # Bold title label
    bold_font = font.Font(weight="bold", size=12)
    label = Label(root, text="- TF2 Wave Conversion Tool -", font=bold_font, bg=bg_color, fg=fg_color)
    label.pack(pady=0)
    
    # Bold title label
    bold_font = font.Font(weight="bold", size=10)
    label = Label(root, text="- Created by StormShockMods -", font=bold_font, bg=bg_color, fg=fg_color)
    label.pack(pady=(0, 5))
    
    # Bold title label
    bold_font = font.Font(weight="bold", size=10)
    label = Label(root, text="Options:", font=bold_font, bg=bg_color, fg=fg_color)
    label.pack(pady=(15, 0))

    # Checkboxes setup
    check_subfolders = BooleanVar()
    sample_rate_var = BooleanVar()
    dry_run_var = BooleanVar()

    options_frame = Frame(root, bg=bg_color)
    options_frame.pack(pady=10)

    check1 = Checkbutton(
        options_frame, text="Check subfolders", variable=check_subfolders,
        bg=bg_color, fg=fg_color, selectcolor=bg_color, activebackground=bg_color,
        activeforeground=fg_color
    )
    check1.grid(row=0, column=0, sticky="w", padx=5, pady=3)

    rate_check = Checkbutton(
        options_frame, text="Sample Rate: ", variable=sample_rate_var,
        command=lambda: update_sample_rate_label(),
        bg=bg_color, fg=fg_color, selectcolor=bg_color, activebackground=bg_color,
        activeforeground=fg_color
    )
    rate_check.grid(row=1, column=0, sticky="w", padx=5, pady=3)

    rate_label = Label(options_frame, text="", font=("TkDefaultFont", 10, "bold"),
                       bg=bg_color, fg=fg_color)
    rate_label.grid(row=1, column=1, sticky="w", padx=5)

    def update_sample_rate_label():
        if sample_rate_var.get():
            rate_label.config(text="48000 Hz", fg=accent_green)
        else:
            rate_label.config(text="44100 Hz", fg="red")

    update_sample_rate_label()

    checkonly_check = Checkbutton(
        options_frame, text="Check-only mode", variable=dry_run_var,
        command=lambda: update_checkonly_label(),
        bg=bg_color, fg=fg_color, selectcolor=bg_color, activebackground=bg_color,
        activeforeground=fg_color
    )
    checkonly_check.grid(row=2, column=0, sticky="w", padx=5, pady=3)

    checkonly_label = Label(options_frame, text="", font=("TkDefaultFont", 10, "bold"),
                            bg=bg_color, fg=fg_color)
    checkonly_label.grid(row=2, column=1, sticky="w", padx=5)

    def update_checkonly_label():
        if dry_run_var.get():
            checkonly_label.config(text="Enabled", fg=accent_green)
        else:
            checkonly_label.config(text="Disabled", fg="grey")

    update_checkonly_label()

    # Define this function before the button that uses it
    def on_select_folder():
        selected_folder = filedialog.askdirectory()
        if selected_folder:
            convert_files_in_folder(selected_folder, check_subfolders.get(), sample_rate_var.get(), dry_run_var.get())

    select_button = Button(
        root, text="Click to select folder and start conversion",
        command=on_select_folder, bg="#444444", fg=fg_color,
        activebackground="#555555", activeforeground=fg_color
    )
    select_button.pack(pady=20)

    exit_button = Button(
        root, text="Exit", command=root.destroy,
        bg="#444444", fg=fg_color,
        activebackground="#555555", activeforeground=fg_color
    )
    exit_button.pack(pady=5)

    root.mainloop()


# ----------------------------
# Conversion Function
# ----------------------------
def convert_files_in_folder(folder, check_subfolders, use_48000, dry_run):
    sample_rate = 48000 if use_48000 else 44100
    converted_files = []

    file_list = []
    for dirpath, dirnames, filenames in os.walk(folder):
        for file in filenames:
            if file.lower().endswith((".mp3", ".wav")):
                file_list.append(os.path.join(dirpath, file))
        if not check_subfolders:
            break

    for file_path in file_list:
        ext = os.path.splitext(file_path)[1].lower()
        base_name = os.path.splitext(file_path)[0]

        if ext == ".mp3":
            wav_path = base_name + ".wav"
            if dry_run:
                converted_files.append((file_path, f"Converted mp3, sample rate modification to {sample_rate} required, file not stereo, conversion required"))
                continue
            convert_audio(file_path, wav_path, sample_rate)
            os.remove(file_path)
            converted_files.append((file_path, f"Converted mp3, sample rate modified to {sample_rate}, converted to stereo"))

        elif ext == ".wav":
            try:
                channels, framerate = get_wav_properties(file_path)
                needs_update = (framerate != sample_rate or channels != 2)
                if not needs_update:
                    converted_files.append((file_path, f"Wave file already present and correct, sample rate {framerate}"))
                    continue

                if dry_run:
                    msg = "Wave file already present"
                    if framerate != sample_rate:
                        msg += f", sample rate modification to {sample_rate} required"
                    else:
                        msg += f", sample rate {framerate}"
                    if channels != 2:
                        msg += ", file not stereo, conversion required"
                    converted_files.append((file_path, msg))
                    continue

                temp_path = base_name + "_temp.wav"
                convert_audio(file_path, temp_path, sample_rate)
                os.remove(file_path)
                os.rename(temp_path, file_path)
                msg = "Wave file already present"
                if framerate != sample_rate:
                    msg += f", sample rate modified to {sample_rate}"
                else:
                    msg += f", sample rate {framerate}"
                if channels != 2:
                    msg += ", converted to stereo"
                converted_files.append((file_path, msg))

            except Exception as e:
                converted_files.append((file_path, f"Error reading wav file: {str(e)}"))

    show_result_window(converted_files)

# ----------------------------
# Result Display
# ----------------------------
def show_result_window(file_messages):
    bg_color = "#2e2e2e"
    fg_color = "white"
    accent_green = "#4caf50"

    result_win = Toplevel()
    result_win.title("Conversion Results")

    icon_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(__file__)), "icon.ico")
    if os.path.exists(icon_path):
        result_win.iconbitmap(icon_path)

    result_win.geometry("600x400")
    result_win.configure(bg=bg_color)

    # Frame for listbox + scrollbar
    list_frame = Frame(result_win, bg=bg_color)
    list_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))

    listbox = Listbox(
        list_frame, width=100, bg=bg_color, fg=fg_color,
        selectbackground=accent_green, selectforeground="black"
    )
    scrollbar = Scrollbar(list_frame, orient="vertical", command=listbox.yview)
    listbox.config(yscrollcommand=scrollbar.set)

    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)

    for path, msg in file_messages:
        listbox.insert(END, path)
        listbox.insert(END, msg)
        listbox.insert(END, "")

    # Frame for the close button at bottom
    button_frame = Frame(result_win, bg=bg_color)
    button_frame.pack(fill="x", pady=10)

    close_btn = Button(
        button_frame, text="Close", command=result_win.destroy,
        bg="#444444", fg=fg_color,
        activebackground="#555555", activeforeground=fg_color,
        width=12
    )
    close_btn.pack(pady=0)

# ----------------------------
# Entry
# ----------------------------
if __name__ == "__main__":
    open_folder_selector_ui()
