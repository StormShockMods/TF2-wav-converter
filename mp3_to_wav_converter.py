import os
import sys
import traceback
from tkinter import (
    filedialog, Tk, Toplevel, Listbox, END, Scrollbar, RIGHT, Y,
    Button, BOTTOM, BooleanVar, Checkbutton, Label, messagebox
)
from pydub import AudioSegment
from mutagen.wave import WAVE


# ----------------------------
# FFmpeg resolution
# ----------------------------
def get_ffmpeg_path():
    default_path = os.path.join(
        os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__),
        "ffmpeg.exe"
    )
    for arg in sys.argv:
        if arg.startswith("--ffmpeg-path="):
            custom_path = arg.split("=", 1)[1].strip('"')
            if os.path.isfile(custom_path):
                print(f"Using ffmpeg override at: {custom_path}", flush=True)
                return custom_path
            else:
                print(f"Warning: ffmpeg path override specified but file not found: {custom_path}", flush=True)
    print(f"Using bundled ffmpeg at: {default_path}", flush=True)
    return default_path


AudioSegment.converter = get_ffmpeg_path()


# ----------------------------
# Conversion helpers
# ----------------------------
def convert_mp3_to_wav_16bit_48k(input_path, output_path):
    print(f"Converting MP3: {input_path} -> {output_path}", flush=True)
    audio = AudioSegment.from_mp3(input_path)
    audio = audio.set_sample_width(2).set_frame_rate(48000)
    if audio.channels == 1:
        audio = AudioSegment.from_mono_audiosegments(audio, audio)
    audio.export(output_path, format="wav")
    print(f"Conversion complete: {output_path}", flush=True)


def convert_wav_to_stereo_16bit_48k(input_path, output_path):
    """
    Returns (did_convert, was_mono_source).

    did_convert -> True if we wrote a new file (format or channels changed).
    was_mono_source -> True if original WAV was mono (channels==1).
    """
    print(f"* Checking WAV: {input_path}", flush=True)
    audio = AudioSegment.from_wav(input_path)
    orig_channels = audio.channels
    orig_rate = audio.frame_rate
    orig_width = audio.sample_width

    # Normalize
    new_audio = audio.set_sample_width(2).set_frame_rate(48000)
    if new_audio.channels == 1:
        new_audio = AudioSegment.from_mono_audiosegments(new_audio, new_audio)

    changed = (
        new_audio.channels != orig_channels or
        new_audio.frame_rate != orig_rate or
        new_audio.sample_width != orig_width
    )

    if changed:
        print(f"* Converting WAV: {input_path} -> {output_path}", flush=True)
        new_audio.export(output_path, format="wav")
        print(f"* Updated WAV saved: {output_path}", flush=True)
        return True, (orig_channels == 1)
    else:
        print(f"* WAV already correct, no conversion needed: {input_path}", flush=True)
        return False, (orig_channels == 1)


# ----------------------------
# Metadata stripper
# ----------------------------
def remove_metadata_from_wav(file_path):
    try:
        audio = WAVE(file_path)
        audio.delete()
        audio.save()
        print(f"Metadata cleared for: {file_path}", flush=True)
    except Exception as e:
        print(f"Error clearing metadata from {file_path}: {e}", flush=True)


# ----------------------------
# Main processing
# ----------------------------
def process_folder(folder_selected, include_subfolders):
    # Collect all file paths up front (so we don't consume os.walk twice)
    if include_subfolders:
        gathered = []
        for root_dir, _, files in os.walk(folder_selected):
            for f in files:
                gathered.append(os.path.join(root_dir, f))
    else:
        gathered = [
            os.path.join(folder_selected, f)
            for f in os.listdir(folder_selected)
            if os.path.isfile(os.path.join(folder_selected, f))
        ]

    # Track what existed before we touched anything (so we can mark *)
    preexisting_wavs = {os.path.abspath(p) for p in gathered if p.lower().endswith(".wav")}
    preexisting_wavs_mono_converted = set()  # subset for ** marking

    converted_files = set()  # all files we actually converted (mp3->wav or wav->updated)
    all_files_to_show = []

    print(f"Starting processing folder: {folder_selected}, include_subfolders={include_subfolders}", flush=True)

    # First pass: convert MP3s and normalize/convert WAVs
    for full_path in gathered:
        lower = full_path.lower()
        root_dir = os.path.dirname(full_path)
        name, ext = os.path.splitext(os.path.basename(lower))
        try:
            if ext == ".mp3":
                wav_path = os.path.splitext(full_path)[0] + ".wav"
                convert_mp3_to_wav_16bit_48k(full_path, wav_path)
                os.remove(full_path)
                converted_files.add(os.path.abspath(wav_path))

            elif ext == ".wav":
                # We'll create a temp converted file in same folder
                converted_path = os.path.join(root_dir, f"{name}_converted.wav")
                did_convert, was_mono_source = convert_wav_to_stereo_16bit_48k(full_path, converted_path)
                if did_convert:
                    os.remove(full_path)
                    os.rename(converted_path, full_path)
                    converted_files.add(os.path.abspath(full_path))
                    if was_mono_source:
                        preexisting_wavs_mono_converted.add(os.path.abspath(full_path))
                else:
                    # cleanup temp if created
                    if os.path.exists(converted_path):
                        os.remove(converted_path)
                    # even if no conversion, we still want to know if it was mono source
                    if was_mono_source:
                        # Means original file *was* mono but "no conversion" is contradictory;
                        # this can happen if upstream libs reported 2 channels after load.
                        # We'll be conservative and not mark ** in this branch.
                        pass

        except Exception as e:
            print(f"Error processing {full_path}: {e}", flush=True)
            traceback.print_exc()
            messagebox.showerror("Processing Error", f"Error processing file:\n{full_path}\n\n{e}")

    # Second pass: strip metadata & build display list
    # Re-list WAVs after conversions (state may have changed)
    if include_subfolders:
        final_wavs = []
        for root_dir, _, files in os.walk(folder_selected):
            for f in files:
                if f.lower().endswith(".wav"):
                    final_wavs.append(os.path.abspath(os.path.join(root_dir, f)))
    else:
        final_wavs = [
            os.path.abspath(os.path.join(folder_selected, f))
            for f in os.listdir(folder_selected)
            if f.lower().endswith(".wav") and os.path.isfile(os.path.join(folder_selected, f))
        ]

    for wav_path in final_wavs:
        remove_metadata_from_wav(wav_path)

        if wav_path in converted_files:
            # Newly created (from MP3) OR updated preexisting WAV
            if wav_path in preexisting_wavs:
                # It existed before; decide between * and **.
                if wav_path in preexisting_wavs_mono_converted:
                    all_files_to_show.append(f"** {wav_path}")
                else:
                    all_files_to_show.append(f"* {wav_path}")
            else:
                # This is a brand-new WAV from MP3 conversion -> no prefix
                all_files_to_show.append(wav_path)
        else:
            # Not converted this run (just metadata cleared)
            # If it was preexisting, mark *; never ** because no conversion occurred.
            if wav_path in preexisting_wavs:
                all_files_to_show.append(f"* {wav_path}")
            else:
                all_files_to_show.append(wav_path)

    print(f"Processing complete. Total files processed: {len(all_files_to_show)}", flush=True)
    show_converted_list(all_files_to_show)


# ----------------------------
# UI
# ----------------------------
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
    root.title("MP3/WAV Stereo Converter")

    check_var = BooleanVar()
    check_var.set(True)

    label = Label(root, text="Click to select folder and start conversion:")
    label.pack(pady=10)

    check = Checkbutton(root, text="Check subfolders", variable=check_var)
    check.pack(pady=5)

    def on_select_folder():
        folder = filedialog.askdirectory(title="Select Folder to Convert Files")
        if folder:
            root.withdraw()
            process_folder(folder, check_var.get())

    btn = Button(root, text="Select Folder", command=on_select_folder)
    btn.pack(pady=20)

    exit_button = Button(root, text="Exit", command=lambda: (root.destroy(), sys.exit()))
    exit_button.pack(pady=5)

    root.mainloop()


# ----------------------------
# Entry
# ----------------------------
if __name__ == "__main__":
    open_folder_selector_ui()
