import glob
import os
import requests
import asyncio
from io import BytesIO
import numpy as np
from PIL import Image
from moviepy import ImageClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, TextClip
import edge_tts  # ✅ 替换 gTTS
import spacy
import textwrap
from moviepy import ColorClip

from video.youtube_upload import authenticate_youtube, upload_video

import spacy.cli


def ensure_spacy_model():
    """ 确保 SpaCy 中文模型已安装 """
    model_name = "zh_core_web_sm"

    try:
        spacy.load(model_name)  # 尝试加载
    except OSError:
        spacy.cli.download(model_name)  # **调用 Spacy 官方的下载方法**


# **在 Coze Plugin 运行时确保 SpaCy 语言模型可用**
ensure_spacy_model()

# 加载 SpaCy 中文模型
nlp = spacy.load("zh_core_web_sm")

def split_text(text):
    """ 使用 SpaCy 进行智能分句 """
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents]

def load_image_from_url(url):
    """
    下载图片到内存，并返回一个 numpy 数组（RGB 格式）
    """
    response = requests.get(url)
    if response.status_code == 200:
        image_bytes = BytesIO(response.content)
        image = Image.open(image_bytes).convert("RGB")
        return np.array(image)
    else:
        raise Exception(f"图片下载失败：{url}")

# 输入的参数,这里的数据是示例
inputs={
    "title": "你的视频标题",
    "description": "你的视频描述",
    "tags": ["标签1", "标签2"],
    "category_id": "28",
    "privacy_status": "public",
    "contents": [
        {
            "paragraph": "这是第一段文案，其作用是用于描述漂亮的清晰图片内容和地道中国普通话配音使用。这是第二句话！这是第三句话？",
            "image": "https://images.wsj.net/im-93292228?width=700&size=1&pixel_ratio=2"},
    ],
    "thumbnail_url":"https://images.wsj.net/im-93292228?width=700&size=1&pixel_ratio=2"
}


clips = []

def wrap_text(text, max_width=20):
    """
    自动换行文本
    - `max_width`: 多少个字符后换行
    """
    return "\n".join(textwrap.wrap(text, width=max_width))

# 计算字幕的最佳宽度（稍微比文本宽一点，防止裁剪）
def get_text_width(text, font_size):
    return  max(250, int(len(text) * font_size ))  # ✅ 让黑底稍微宽一点

async def generate_audio(text, filename):
    """ 使用 Edge TTS 生成更自然的语音 """
    tts = edge_tts.Communicate(text, voice="zh-CN-YunyangNeural")  # ✅ 选择更自然的女声
    await tts.save(filename)

def create_image_clips(image_array, duration):
    """
    生成 1920x1080 视频片段，保持图片原始比例，多余部分用黑色填充
    """
    target_width,target_height = 1920,1080
    img_h, img_w = image_array.shape[:2]
    aspect_ratio = img_w / img_h
    target_ratio = target_width / target_height

    if aspect_ratio > target_ratio:
        # 图片比 16:9 更宽 → 调整宽度，按比例缩放高度
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
    else:
        # 图片比 16:9 更高 → 调整高度，按比例缩放宽度
        new_height = target_height
        new_width = int(target_height * aspect_ratio)

    # **调整图片尺寸**
    image_clip = ImageClip(image_array).resized((new_width, new_height)).with_duration(duration)

    # **创建黑色背景**
    bg_clip = ColorClip((target_width, target_height), color=(0, 0, 0)).with_duration(duration)

    # **将图片居中放入背景**
    return image_clip,bg_clip


# 遍历内容，生成视频片段
for contentID, item in enumerate(inputs["contents"]):

    paragraph = item["paragraph"]
    image_url = item["image"]

    texts = split_text(paragraph)  # ✅ 现在使用 SpaCy 进行智能分句
    for idx,text in enumerate(texts):
        # 加载图片到内存（返回 numpy 数组）
        image_array = load_image_from_url(image_url)

        # ✅ 使用 Edge TTS 生成音频（异步执行）
        audio_filename = f"audio_{contentID}_{idx}.mp3"
        asyncio.run(generate_audio(text, audio_filename))  # ✅ 替换 gTTS

        # 加载音频，并获取其时长
        audio_clip = AudioFileClip(audio_filename)
        duration = audio_clip.duration

        # 使用内存中的图片生成视频片段，时长与音频一致

        # image_clip = ImageClip(image_array).resized((1920, 1080)).with_duration(duration)
        image_clip,bg_clip = create_image_clips(image_array, duration)
        font_size = 50
        text_width = get_text_width(text, font_size)
        text_wrapped = wrap_text(text)

        num_lines = text_wrapped.count("\n") + 1  # 计算行数
        text_height = font_size * num_lines * 2  # ✅ 让多行文本有足够间距
        #y_offset = image_clip.h - text_height - font_size*2  # ✅ 调整 y_offset，避免被裁剪

        # **调整 y_offset（让字幕顶部对齐）**
        base_y = image_clip.h - 150  # ✅ 基准对齐高度
        y_offset = base_y - text_height // 2  # ✅ 让字幕居中，不会因行数不同而错位

        # 让字幕始终可见（白色字体 + 黑色描边）
        txt_clip = (
            TextClip(
                text=text_wrapped,
                font_size=font_size,
                color="white",  # ✅ 白色文本
                stroke_color="black",  # ✅ 黑色描边
                stroke_width=4,  # ✅ 描边宽度
                font="Songti",
                method="caption",
                size=(int(text_width), font_size * num_lines*3)  # ✅ 让字幕宽度合适
            )
            .with_duration(duration)
            .with_position(("center", "center"))
        )

        # 叠加字幕
        composite_clip = CompositeVideoClip([
            bg_clip,
            image_clip.with_position("center"),
            txt_clip.with_position(("center", y_offset))  # ✅ 让字幕不会贴底
        ]).with_audio(audio_clip)

        clips.append(composite_clip)

# 拼接所有视频片段生成最终视频
final_video = concatenate_videoclips(clips, method="compose")
final_video.write_videofile("final_video.mp4", fps=24)
youtube = authenticate_youtube()

upload_video(
    youtube,
    "final_video.mp4",  # **你的视频文件**
    inputs["title"],
    inputs["description"],
    inputs["tags"],
    category_id=inputs["category_id"],  # YouTube 分类 ID
    thumbnail_url=inputs["thumbnail_url"],
)

# 清理临时生成的音频文件
for file in glob.glob("audio_*.mp3"):
    os.remove(file)
