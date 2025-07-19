# **TF2-wav-converter**

A simple exe file to mass-convert mp3 files to 48000 hz wav files and delete all metadata from converted files for Titanfall 2 Mods.

-------------------------------------------------------------------------------------------------------------------------------------

Welcome to the Readme for StormShock's TF2-Wav-Converter Program. 

You are free to use, redistribute and modify this program
as you see fit.

Be aware this program was created with assistance from ChatGPT for the explicit
purpose of mass-converting mp3 files to properly formatted wave files for Titanfall 2 mods and
removing metadata from converted files to minimize audio glitches inside the game.

With that said, this software is offered AS-IS. The code works but I am not a python programmer
(anymore) so I can offer some limited assistance with bugs, but that's about it.



***LICENSING***

This application includes FFmpeg, licensed under the LGPL v2.1 (or newer).
FFmpeg is copyright (c) the FFmpeg developers.
See https://ffmpeg.org/ for more information.

The included ffmpeg.exe is an unmodified binary from [https://www.gyan.dev/ffmpeg/builds/].
You may replace this binary with a compatible version as needed. To do so, run this program
from command prompt with:

mp3_to_wav_converter.exe --ffmpeg-path="PATH" 

and replace PATH with the full path your FFmpeg version.

A copy of the FFmpeg license is included in this package.



***INSTALLATION & USAGE***

- To use, download the .zip file and extract it somewhere on your computer.
- Then run "TF2-Wav-Converter.exe"
- It will take a moment (it's extracting everything including FFmpeg to a temporary directory on your computer)
- Then you will see a UI including an exit button, checkbox to convert files in subfolders or not, and a "Select Folder" button
- When you click the "Select Folder" button a windows dialog will open and you can select which folder you would like to comb for mp3 files.
- Once you find the correct folder, hit "Select Folder" at the bottom right of the dialog window and it will begin converting any mp3 files it finds inside that folder (and optionally subfolders) into .wav files.
- Once conversion is complete, it will then do a second comb through every file and delete any metadata attached to the wav files (this can cause loud static noises at the end of a sound effect in Titanfall 2).
- Once the metadata removal is completed for all files, a new window will pop up with a results list, showing the path of every file converted in that run (files present in a folder but not converted during that run will have a * before their path).
- From there, you can then exit the program and it will close.

  Vinson Dynamics thanks you for your service.
