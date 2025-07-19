import os
import sys
from tkinter import (
    filedialog, Tk, Toplevel, Listbox, END, Scrollbar, RIGHT, Y,
    Button, BOTTOM, BooleanVar, Checkbutton, Label
)
from pydub import AudioSegment
from mutagen.wave import WAVE

def get_ffmpeg_path():
    # Default bundled ffmpeg path (inside PyInstaller temp folder or script folder)
    default_path = os.path.join(
        os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__),
        "ffmpeg.exe"
    )

    # Check for --ffmpeg-path argument (e.g. --ffmpeg-path="C:/path/to/ffmpeg.exe")
    for arg in sys.argv:
        if arg.startswith("--ffmpeg-path="):
            custom_path = arg.split("=", 1)[1].strip('"')
            if os.path.isfile(custom_path):
                return custom_path
            else:
                print(f"Warning: ffmpeg path override specified but file not found: {custom_path}")

    # If no override, return default
    return default_path

# Set pydub's ffmpeg converter path
AudioSegment.converter = get_ffmpeg_path()

def convert_mp3_to_wav_16bit_48k(input_path, output_path):
    audio = AudioSegment.from_mp3(input_path)
    audio = audio.set_sample_width(2)  # 16-bit
    audio = audio.set_frame_rate(48000)
    audio.export(output_path, format="wav")

def remove_metadata_from_wav(file_path):
    try:
        audio = WAVE(file_path)
        audio.delete()
        audio.save()
    except Exception as e:
        print(f"Error clearing metadata from {file_path}: {e}")

def process_folder(folder_selected, include_subfolders):
    converted_files = set()
    all_files_to_show = []

    if include_subfolders:
        for root_dir, _, files in os.walk(folder_selected):
            for file in files:
                if file.lower().endswith(".mp3"):
                    mp3_path = os.path.join(root_dir, file)
                    wav_path = os.path.splitext(mp3_path)[0] + ".wav"
                    try:
                        convert_mp3_to_wav_16bit_48k(mp3_path, wav_path)
                        os.remove(mp3_path)
                        converted_files.add(os.path.abspath(wav_path))
                    except Exception as e:
                        print(f"Error converting {mp3_path}: {e}")
    else:
        for file in os.listdir(folder_selected):
            file_path = os.path.join(folder_selected, file)
            if file.lower().endswith(".mp3") and os.path.isfile(file_path):
                wav_path = os.path.splitext(file_path)[0] + ".wav"
                try:
                    convert_mp3_to_wav_16bit_48k(file_path, wav_path)
                    os.remove(file_path)
                    converted_files.add(os.path.abspath(wav_path))
                except Exception as e:
                    print(f"Error converting {file_path}: {e}")

    if include_subfolders:
        for root_dir, _, files in os.walk(folder_selected):
            for file in files:
                if file.lower().endswith(".wav"):
                    wav_path = os.path.abspath(os.path.join(root_dir, file))
                    remove_metadata_from_wav(wav_path)
                    if wav_path in converted_files:
                        all_files_to_show.append(wav_path)
                    else:
                        all_files_to_show.append(f"* {wav_path}")
    else:
        for file in os.listdir(folder_selected):
            file_path = os.path.join(folder_selected, file)
            if file.lower().endswith(".wav") and os.path.isfile(file_path):
                wav_path = os.path.abspath(file_path)
                remove_metadata_from_wav(wav_path)
                if wav_path in converted_files:
                    all_files_to_show.append(wav_path)
                else:
                    all_files_to_show.append(f"* {wav_path}")

    show_converted_list(all_files_to_show)

def show_converted_list(files):
    result_window = Toplevel()
    result_window.title("Conversion Complete - Files Processed")
    result_window.geometry("800x600")
    result_window.resizable(True, True)

    scrollbar = Scrollbar(result_window)
    scrollbar.pack(side=RIGHT, fill=Y)

    listbox = Listbox(result_window, width=120, yscrollcommand=scrollbar.set)
    for file in files:
        listbox.insert(END, file)
    listbox.pack(fill="both", expand=True)

    scrollbar.config(command=listbox.yview)

    exit_button = Button(result_window, text="Exit", command=lambda: (result_window.destroy(), sys.exit()))
    exit_button.pack(side=BOTTOM, pady=10)

    result_window.protocol("WM_DELETE_WINDOW", lambda: (result_window.destroy(), sys.exit()))
    result_window.mainloop()

def open_folder_selector_ui():
    root = Tk()
    root.title("MP3 to WAV Converter")

    check_var = BooleanVar()
    check_var.set(True)

    label = Label(root, text="Click to select folder and start conversion:")
    label.pack(pady=10)

    check = Checkbutton(root, text="Check subfolders", variable=check_var)
    check.pack(pady=5)

    def on_select_folder():
        folder = filedialog.askdirectory(title="Select Folder to Convert MP3s")
        if folder:
            root.withdraw()
            process_folder(folder, check_var.get())

    btn = Button(root, text="Select Folder", command=on_select_folder)
    btn.pack(pady=20)

    exit_button = Button(root, text="Exit", command=lambda: (root.destroy(), sys.exit()))
    exit_button.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    open_folder_selector_ui()
