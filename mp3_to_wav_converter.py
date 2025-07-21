import os
import sys
import traceback
from tkinter import (
    filedialog, Tk, Toplevel, Listbox, END, Scrollbar, RIGHT, Y,
    Button, BOTTOM, BooleanVar, Checkbutton, Label, messagebox, Frame
)
from pydub import AudioSegment
from mutagen.wave import WAVE

# ----------------------------
# FFmpeg Configuration
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
# Conversion Functions
# ----------------------------
def convert_mp3_to_wav_16bit(input_path, output_path, sample_rate, dry_run=False):
    print(f"Converting MP3: {input_path} -> {output_path}", flush=True)
    if dry_run:
        print("Dry-run: Skipping actual conversion.")
        return False  # indicates file not actually converted
    audio = AudioSegment.from_mp3(input_path)
    audio = audio.set_sample_width(2).set_frame_rate(sample_rate)
    if audio.channels == 1:
        audio = AudioSegment.from_mono_audiosegments(audio, audio)
    audio.export(output_path, format="wav")
    print(f"Conversion complete: {output_path}", flush=True)
    return True  # indicates file converted

def convert_wav_to_stereo_16bit(input_path, output_path, sample_rate, dry_run=False):
    print(f"* Checking WAV: {input_path}", flush=True)
    audio = AudioSegment.from_wav(input_path)
    orig_channels = audio.channels
    orig_rate = audio.frame_rate
    orig_width = audio.sample_width

    # Already correct, skip conversion
    if orig_channels == 2 and orig_rate == sample_rate and orig_width == 2:
        print(f"* WAV already correct, skipping conversion: {input_path}", flush=True)
        return False, False, orig_rate  # no change, no mono source, original rate

    if dry_run:
        print(f"Dry-run: Would convert WAV: {input_path}")
        return True, (orig_channels == 1), orig_rate

    new_audio = audio.set_sample_width(2).set_frame_rate(sample_rate)
    if new_audio.channels == 1:
        new_audio = AudioSegment.from_mono_audiosegments(new_audio, new_audio)

    print(f"* Converting WAV: {input_path} -> {output_path}", flush=True)
    new_audio.export(output_path, format="wav")
    print(f"* Updated WAV saved: {output_path}", flush=True)
    return True, (orig_channels == 1), orig_rate

# ----------------------------
# Metadata Removal
# ----------------------------
def remove_metadata_from_wav(file_path, dry_run=False):
    if dry_run:
        print(f"Dry-run: Would clear metadata for: {file_path}")
        return
    try:
        audio = WAVE(file_path)
        audio.delete()
        audio.save()
        print(f"Metadata cleared for: {file_path}", flush=True)
    except Exception as e:
        print(f"Error clearing metadata from {file_path}: {e}", flush=True)

# ----------------------------
# Folder Processing
# ----------------------------
def process_folder(folder_selected, include_subfolders, sample_rate, dry_run=False):
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

    # Track original WAVs for diagnostics
    preexisting_wavs = {os.path.abspath(p) for p in gathered if p.lower().endswith(".wav")}
    # To track mono->stereo converted wavs
    preexisting_wavs_mono_converted = set()
    # Track files converted this run (mp3 or wav)
    converted_files = set()

    # Dictionary file_path => dict of info for diagnostics
    file_diagnostics = {}

    print(f"Starting processing folder: {folder_selected}, include_subfolders={include_subfolders}, dry_run={dry_run}", flush=True)

    for full_path in gathered:
        lower = full_path.lower()
        root_dir = os.path.dirname(full_path)
        name, ext = os.path.splitext(os.path.basename(lower))
        try:
            if ext == ".mp3":
                wav_path = os.path.splitext(full_path)[0] + ".wav"
                converted = convert_mp3_to_wav_16bit(full_path, wav_path, sample_rate, dry_run=dry_run)
                if converted:
                    converted_files.add(os.path.abspath(wav_path))
                if not dry_run and converted:
                    os.remove(full_path)
                # Record diagnostics for the new wav file created from mp3
                file_diagnostics[os.path.abspath(wav_path)] = {
                    "converted_mp3": True,
                    "was_wav": False,
                    "sample_rate_modified": True,
                    "sample_rate_original": sample_rate,
                    "converted_to_stereo": True  # mp3 conversion always forces stereo here
                }

            elif ext == ".wav":
                converted_path = os.path.join(root_dir, f"{name}_converted.wav")
                did_convert, was_mono_source, orig_rate = convert_wav_to_stereo_16bit(full_path, converted_path, sample_rate, dry_run=dry_run)

                abs_path = os.path.abspath(full_path)

                if did_convert and not dry_run:
                    os.remove(full_path)
                    os.rename(converted_path, full_path)
                    converted_files.add(abs_path)
                    if was_mono_source:
                        preexisting_wavs_mono_converted.add(abs_path)

                else:
                    # Remove leftover temp if exists
                    if os.path.exists(converted_path):
                        os.remove(converted_path)

                # Fill diagnostic info
                file_diagnostics[abs_path] = {
                    "converted_mp3": False,
                    "was_wav": True,
                    "converted_to_stereo": was_mono_source,
                    "sample_rate_original": orig_rate,
                    "sample_rate_modified": did_convert,
                }
        except Exception as e:
            print(f"Error processing {full_path}: {e}", flush=True)
            traceback.print_exc()
            messagebox.showerror("Processing Error", f"Error processing file:\n{full_path}\n\n{e}")

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

    all_files_to_show = []

    for wav_path in final_wavs:
        remove_metadata_from_wav(wav_path, dry_run=dry_run)

        diag = file_diagnostics.get(wav_path, None)

        # Compose diagnostic line
        diag_line_parts = []
        if diag is None:
            # File that was already there but no conversion happened
            # Assume a preexisting wav that was never processed here
            diag_line_parts.append("Wave file already present")
            # Check if we can detect sample rate and channels info for extra accuracy
            try:
                audio = AudioSegment.from_wav(wav_path)
                is_correct = (audio.channels == 2 and audio.frame_rate == sample_rate and audio.sample_width == 2)
                if is_correct:
                    diag_line_parts.append("and correct")
                else:
                    diag_line_parts.append(f", sample rate {audio.frame_rate}")
                    if audio.channels == 1:
                        diag_line_parts.append(", mono")
            except Exception:
                pass
        else:
            if diag["was_wav"]:
                diag_line_parts.append("Wave file already present")
                if not diag["sample_rate_modified"]:
                    # Unmodified wav - report original sample rate
                    diag_line_parts.append(f", sample rate {diag['sample_rate_original']}")
                    if diag["converted_to_stereo"]:
                        if dry_run:
                            diag_line_parts.append(", file not stereo, conversion required")
                        else:
                            diag_line_parts.append(", converted to stereo")
                    else:
                        # check if correct or not
                        if diag['sample_rate_original'] == sample_rate:
                            diag_line_parts.append(" and correct")
                else:
                    # Was modified
                    if dry_run:
                        diag_line_parts.append(f", sample rate modification to {sample_rate} required")
                        if diag["converted_to_stereo"]:
                            diag_line_parts.append(", file not stereo, conversion required")
                    else:
                        diag_line_parts.append(f", sample rate modified to {sample_rate}")
                        if diag["converted_to_stereo"]:
                            diag_line_parts.append(", converted to stereo")

            if diag["converted_mp3"]:
                diag_line_parts.append("Converted mp3")
                # mp3 conversions always go stereo and sample rate set, so no need extra here

        all_files_to_show.append(wav_path)
        all_files_to_show.append("".join(diag_line_parts))

    print(f"Processing complete. Total files processed: {len(all_files_to_show)//2}", flush=True)
    show_converted_list(all_files_to_show)

# ----------------------------
# Result Display UI
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

# ----------------------------
# Entry UI
# ----------------------------
def open_folder_selector_ui():
    root = Tk()
    root.title("MP3/WAV Stereo Converter")

    check_subfolders = BooleanVar(value=True)
    sample_rate_var = BooleanVar(value=True)  # True = 48000, False = 44100
    dry_run_var = BooleanVar(value=False)    # False by default

    label = Label(root, text="Click to select folder and start conversion:")
    label.pack(pady=10)

    check1 = Checkbutton(root, text="Check subfolders", variable=check_subfolders)
    check1.pack(pady=5)

    # Sample rate section
    rate_frame = Frame(root)
    rate_frame.pack(pady=5)

    Label(rate_frame, text="Sample Rate").pack(side="left", padx=5)
    rate_label = Label(rate_frame, text="", font=("TkDefaultFont", 10, "bold"))
    rate_label.pack(side="right", padx=5)

    def update_sample_rate_label():
        if sample_rate_var.get():
            rate_label.config(text="48000 Hz", fg="green")
        else:
            rate_label.config(text="44100 Hz", fg="red")

    Checkbutton(rate_frame, variable=sample_rate_var, command=update_sample_rate_label).pack(side="left", padx=5)
    update_sample_rate_label()

    # Check-only mode section
    checkonly_frame = Frame(root)
    checkonly_frame.pack(pady=5)

    checkonly_label = Label(checkonly_frame, text="Check-only mode", font=("TkDefaultFont", 10, "bold"), fg="grey")
    checkonly_label.pack(side="left", padx=5)

    def update_checkonly_label():
        if dry_run_var.get():
            checkonly_label.config(fg="green")
        else:
            checkonly_label.config(fg="grey")

    Checkbutton(checkonly_frame, variable=dry_run_var, command=update_checkonly_label).pack(side="left", padx=5)
    update_checkonly_label()

    def on_select_folder():
        folder = filedialog.askdirectory(title="Select Folder to Convert Files")
        if folder:
            root.withdraw()
            selected_rate = 48000 if sample_rate_var.get() else 44100
            process_folder(folder, check_subfolders.get(), selected_rate, dry_run=dry_run_var.get())

    Button(root, text="Select Folder", command=on_select_folder).pack(pady=20)
    Button(root, text="Exit", command=lambda: (root.destroy(), sys.exit())).pack(pady=5)

    root.mainloop()

# ----------------------------
# Main Entry Point
# ----------------------------
if __name__ == "__main__":
    open_folder_selector_ui()
