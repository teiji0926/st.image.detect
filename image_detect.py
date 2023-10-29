from array import array
import os
from PIL import Image
import sys
import time
import json
from dotenv import load_dotenv


import azure.ai.vision as sdk
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

# .env ファイルのパスを指定（必要に応じて）
env_path = 'C:/Users/teiji/OneDrive/Desktop/streamlit/Image_Recognition/.env'
load_dotenv(dotenv_path=env_path, override=True)

print("DEBUG: VISION_ENDPOINT =", os.getenv("VISION_ENDPOINT"))


print("Endpoint:", os.getenv("VISION_ENDPOINT"))
print("Key:", os.getenv("VISION_KEY"))


subscription_key = os.getenv("VISION_KEY")
endpoint = os.getenv("VISION_ENDPOINT")




#認証
#コード内でos.environ["VISION_KEY"]という行を見つけると、subscription_keyは環境変数VISION_KEYから取得する
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))


#タグ取得関数
def get_tags(file_path):
    local_image = open(file_path, "rb")
    tags_result = computervision_client.tag_image_in_stream(local_image)
    tags = tags_result.tags
    tags_name = []
    #辞書型に見えるけどオブジェクトなので、name属性でとってくる
    for tag in tags:
        tags_name.append(tag.name)
    return tags_name


def detect_objects(file_path): 
    # Call API with local image
    #公式ドキュメントは
    image_stream = open(file_path, "rb")
    detect_objects_results = computervision_client.detect_objects_in_stream(image_stream)
    objects = detect_objects_results.objects
    return objects

import streamlit as st
from PIL import ImageDraw
from PIL import ImageFont

st.title('物体検出アプリ')

uploaded_file = st.file_uploader('Choose an image', type=['jpg','png'])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    img_path = f'img/{uploaded_file.name}'

    img.save(img_path)
    objects = detect_objects(img_path)

    #描画
    #どの画像に書き込むかを指定。書き込む準備
    draw = ImageDraw.Draw(img)
    for object in objects:
       x = object.rectangle.x
       y = object.rectangle.y
       w = object.rectangle.w
       h = object.rectangle.h

       #公式のjsonはobjectだけど変わってるから要注意

       caption = object.object_property
       draw.rectangle([(x,y),(x+w,y+h)],fill=None,outline='green',width=5)

       #文字を描いたときのサイズを指定
       font = ImageFont.truetype(font='./arial.ttf',size=500)

       # テキストのバウンディングボックスを取得
       bbox = draw.textbbox((x, y), caption, font=font)
       # バウンディングボックスの幅と高さを計
       text_w = bbox[2] - bbox[0]
       text_h = bbox[3] - bbox[1]
       draw.rectangle([(x,y),(x+text_w,y+text_h)],fill='green')
       draw.text((x,y),caption,fill='white',font=font)
       
       #タグ取得
       tags_name = get_tags(img_path)
       tags_name = '/ '.join(tags_name)

       #フォント情報を作る


    st.image(img)

    st.markdown('**認識されたコンテンツタグ**')
    st.markdown(f'{tags_name}')
    os.remove(img_path)