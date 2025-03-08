import os
import google.auth
import requests
import io
import googleapiclient.discovery
import googleapiclient.errors
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload
import json

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PATH = "token.json"
CLIENT_SECRET_PATH = "client_secrets.json"



# **设置 OAuth 认证**
def authenticate_youtube():
    """ 优雅地进行 YouTube API 认证，自动复用已授权的 Token """

    credentials = None

    # **如果 `token.json` 存在，加载 Token**
    if os.path.exists(TOKEN_PATH):
        credentials = Credentials.from_authorized_user_file(TOKEN_PATH)

    # **如果没有 Token 或 Token 失效，重新认证**
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
        credentials = flow.run_local_server(port=0)  # ✅ 本地认证

        # **保存新的 Token**
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(credentials.to_json())

    return build("youtube", "v3", credentials=credentials)

def upload_video(youtube, file_path, title, description, tags, category_id="22",thumbnail_url=None):
    """自动上传视频到 YouTube"""
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": "private"  # 可以是 "public", "private", "unlisted"
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    response = request.execute()
    video_id = response["id"]
    print(f"✅ 视频上传成功！视频 ID: {video_id}")
    # **Step 2: 直接在内存中处理封面**
    if thumbnail_url:
        try:
            response = requests.get(thumbnail_url)
            response.raise_for_status()  # 确保请求成功

            # **使用 `BytesIO` 直接在内存中存储图片**
            thumbnail_bytes = io.BytesIO(response.content)
            thumbnail_upload = MediaIoBaseUpload(thumbnail_bytes, mimetype="image/jpeg")

            # **上传封面**
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=thumbnail_upload
            ).execute()

            print("✅ 封面图片上传成功（内存上传）！")

        except Exception as e:
            print(f"❌ 封面上传失败: {e}")

    return video_id



# **执行上传**
if __name__ == "__main__":
    youtube = authenticate_youtube()
    upload_video(
        youtube,
        "final_video.mp4",  # **你的视频文件**
        "自动上传的视频标题",
        "这个视频是由 Python 自动上传的！",
        [],
        category_id="25",  #YouTube 分类
        thumbnail_url="https://images.wsj.net/im-93292228?width=700&size=1&pixel_ratio=2",
    )


# category_id	类别名称
# 1	电影与动画
# 2	汽车与交通
# 10	音乐
# 15	宠物与动物
# 17	体育
# 19	旅游与活动
# 20	游戏
# 22	人物与博客
# 23	喜剧
# 24	娱乐
# 25	新闻与政治
# 26	如何与风格
# 27	教育
# 28	科学与技术
# 29	非营利组织与活动