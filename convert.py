from moviepy import VideoFileClip
import os

# Folder containing videos
folder_path = r"uploads"

# Supported input formats
video_extensions = (".mp4", ".avi")

# Loop through all files
for file_name in os.listdir(folder_path):

    if file_name.lower().endswith(video_extensions):

        input_path = os.path.join(folder_path, file_name)

        # Output .mov file
        output_name = os.path.splitext(file_name)[0] + ".mov"
        output_path = os.path.join(folder_path, output_name)

        print(f"Converting: {file_name}")

        try:
            clip = VideoFileClip(input_path)

            clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac"
            )

            print(f"Saved: {output_name}")

        except Exception as e:
            print(f"Error converting {file_name}: {e}")

print("All conversions completed!")