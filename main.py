from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    CompositeVideoClip,
    concatenate_audioclips,
)
from moviepy.video.tools.subtitles import SubtitlesClip
from PIL import Image, ImageDraw, ImageFont
from frame import generate_frame
from tts import generate_tts
import numpy as np
import whisper
import os
import random
import json
import torch

# Override with WHISPER_MODEL=medium.en for higher quality (slower on CPU).
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium.en")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading Whisper model {WHISPER_MODEL!r} on {DEVICE}...")
model = whisper.load_model(WHISPER_MODEL, device=DEVICE)

def get_video_number():
    filename = "utils/counter.txt"

    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("0")

    with open(filename, "r") as f:
        count = int(f.read().strip())

    count += 1

    with open(filename, "w") as f:
        f.write(str(count))

    return count

def add_text_glow(text, font, size, color, glow_radius=5):
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    bbox = draw.textbbox((0, 0), text, font=font)
    x_center = (size[0] - (bbox[2] - bbox[0])) // 2
    y_center = (size[1] - (bbox[3] - bbox[1])) // 2

    for dx in range(-glow_radius, glow_radius + 1, 2):
        for dy in range(-glow_radius, glow_radius + 1, 2):
            draw.text(
                (x_center + dx, y_center + dy), text, font=font, fill=(0, 0, 0, 150)
            )
    draw.text((x_center, y_center), text, font=font, fill=color)
    return img

def create_text_with_glow(
    text, fontsize, color, font_path, size=(900, 200), glow_radius=5
):
    font = ImageFont.truetype(font_path, fontsize)
    pil_image = add_text_glow(text, font, size, color, glow_radius)
    return (
        ImageClip(np.array(pil_image))
        .set_duration(5)
        .set_fps(24)
        .resize(height=size[1])
    )


def generate_video(file_path, cropped=True):
    print("Starting video generation...")

    title_audio = AudioFileClip("title_audio.wav")
    story_audio = AudioFileClip("story_audio.wav")

    background_video = VideoFileClip("utils/gameplay.mp4")

    title_duration = title_audio.duration
    story_start_time = title_duration

    total_duration = title_audio.duration + story_audio.duration
    max_seed = max(0, background_video.duration - total_duration)
    seed = random.uniform(0, max_seed) if max_seed > 0 else 0
    if background_video.duration < total_duration:
        raise ValueError(
            f"Gameplay video is too short ({background_video.duration:.1f}s) for "
            f"this story ({total_duration:.1f}s). Use a longer utils/gameplay.mp4."
        )
    background_video = background_video.subclip(seed, seed + total_duration)

    if cropped:
        if background_video.h < 1920:
            background_video = background_video.resize(height=1920)

        background_video = background_video.crop(
            width=1080,
            height=1920,
            x_center=background_video.w // 2,
            y_center=background_video.h // 2,
        )

    print("Creating image clip for title...")

    fixed_width = 850

    image_clip = (
        ImageClip("utils/output_image.png")
        .resize(width=fixed_width)  
        .set_position("center")
        .set_duration(title_duration)
    )
    image_clip = image_clip.set_position("center").set_duration(title_duration)

    print("Generating subtitles using Whisper...")

    result = model.transcribe("story_audio.wav", word_timestamps=True)

    subtitles = []
    story_end_time = title_duration + story_audio.duration

    for segment in result["segments"]:
        for word in segment["words"]:
            start_time = word["start"] + title_duration
            end_time = word["end"] + title_duration
            text = word["word"]

            solid_caption = (
                create_text_with_glow(
                    text,
                    fontsize=100,
                    color="white",
                    font_path="utils/Montserrat-ExtraBold.ttf",
                    glow_radius=5,
                )
                .set_position(("center", "center"))
                .set_start(start_time)
                .set_duration(end_time - start_time)
            )

            subtitles.append(solid_caption)

    print("Merging audio...")
    combined_audio = concatenate_audioclips(
        [title_audio, story_audio.set_start(story_start_time)]
    )

    background_video = background_video.set_audio(combined_audio)

    print("Composing final video...")
    final_video = CompositeVideoClip([background_video, image_clip] + subtitles)

    final_video = final_video.set_duration(total_duration)

    print("Saving final video as 'Final_video_with_captions.mp4'...")

    final_video.write_videofile(
        file_path,
        codec="libx264",
        audio_codec="aac",
        bitrate="20M",
        audio_bitrate="320k",
        preset="veryfast",
        ffmpeg_params=[
        "-crf", "16",     
        "-pix_fmt", "yuv420p",  
        ],
        threads=max(1, min(4, os.cpu_count() or 2)),
    )

    print("Final Video Completed!")

def cleanup():
    for filename in ("story_audio.wav", "title_audio.wav", "utils/output_image.png"):
        if os.path.exists(filename):
            os.remove(filename)

def load_story(count):
    with open("utils/stories.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    stories = data.get("stories", [])
    if not stories:
        raise ValueError("utils/stories.json contains no stories.")
    # Cycle through the available stories when the counter exceeds the list.
    story = stories[(count - 1) % len(stories)]
    title = story["title"]
    gender = story["main_character_gender"]
    num_parts = story["num_parts"]
    description = story.get("description", "")
    tags = story.get("tags", [])
    parts = story["parts"]

    return title, gender, num_parts, description, tags, parts


def make_story():
    count = get_video_number()
    title, gender, num_parts, description, tags, parts = load_story(count)
    os.makedirs(f"Stories/Story_{count}", exist_ok=True)
    print("Story Retrieved")

    if num_parts == 1:
        title, gender, num_parts, description, tags, parts = load_story(count)
        story_path = f"Stories/Story_{count}/Reddit_Story_1.mp4"
        generate_tts(title, parts[0]["content"], gender)
        generate_frame(title)
        generate_video(story_path)
        if os.path.exists(story_path):
            cleanup()
    else:
        i = 1
        for part in parts:
            title, gender, num_parts, description, tags, parts = load_story(count)
            story_path = f"Stories/Story_{count}/Reddit_Story_{i}.mp4"
            if num_parts == i:
                title = f"{title} (Final Part)"
                generate_frame(title)
                generate_tts(title, parts[i - 1]["content"], gender)
                generate_video(story_path)
                if os.path.exists(story_path):
                    cleanup()
                break
            else:
                title = f"{title} (Part {i})"
                generate_frame(title)
                generate_tts(title, parts[i - 1]["content"], gender)
                generate_video(story_path)
                if os.path.exists(story_path):
                    cleanup()
                i += 1

    print("Stories Generated.")
  
if __name__ == "__main__":
    make_story()