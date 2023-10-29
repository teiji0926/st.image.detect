import os
from PIL import Image
from dotenv import load_dotenv
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import streamlit as st
from PIL import ImageDraw
from PIL import ImageFont
import requests
import io



#st内のシークレットから持ってくる環境変数
subscription_key = st.secrets["AZURE"]["VISION_KEY"]
endpoint = st.secrets["AZURE"]["VISION_ENDPOINT"]
connection_string = st.secrets["AZURE"]["AZURE_STORAGE_CONNECTION_STRING"]
container_name = st.secrets["AZURE"]["AZURE_STORAGE_CONTAINER_NAME"]


#Azure Blob Storageに接続するためのクライアントを作成
blob_service_client = BlobServiceClient.from_connection_string(connection_string)


# Computer Vision Clientの作成
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

def get_tags(image_url):
    tags_result = computervision_client.tag_image(image_url)
    tags = tags_result.tags
    tags_name = []
    for tag in tags:
        tags_name.append(tag.name)
    return tags_name

def detect_objects(image_url):
    detect_objects_results = computervision_client.detect_objects(image_url)
    objects = detect_objects_results.objects
    return objects

st.title('物体検出アプリ')

uploaded_file = st.file_uploader('Choose an image', type=['jpg','png'])

if uploaded_file is not None:
    # Blob名を設定
    blob_name = uploaded_file.name
    # Blobへのアップロード
    #特定のBlobと通信するためのクライアントを作成しています。具体的には、blob_service_clientのget_blob_clientメソッドを呼び出して、
    #特定のコンテナとBlobにアクセスするためのBlobClientインスタンスを取得しています。
    #BlobClientオブジェクトは、指定された名前のBlobに対する操作を行うためのクライアントを提供しますが、このクライアントを作成する時点でBlobが実際に存在する必要はありません。
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(uploaded_file, overwrite=True)
    # BlobのURLを取得
    #{blob_service_client.account_name} は、Azure Blob Storageのアカウント名を示します。
    #この部分はBlobServiceClientオブジェクトのaccount_nameプロパティから取得されます。
    blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}"

    # 物体検出とタグ取得
    objects = detect_objects(blob_url)
    tags_name = get_tags(blob_url)

    # 画像をダウンロードしてPILで開く
    response = requests.get(blob_url)
    #response.contentは、HTTPレスポンスのボディコンテンツをバイト形式で返します。このコンテンツは通常、バイナリデータ（この場合は画像データ）です。
    #io.BytesIO(response.content)は、ディスクに保存することなく、メモリ上で画像データを「ファイル」のように扱うための仮想的な「ファイル」を作成しています
    img = Image.open(io.BytesIO(response.content))

    # 描画
    #描画の準備！
    draw = ImageDraw.Draw(img)
    p_name = []
    for object in objects:
        x = object.rectangle.x
        y = object.rectangle.y
        w = object.rectangle.w
        h = object.rectangle.h
        
        #caption = object.object
        caption = object.object_property
        p_name.append(caption)
        draw.rectangle([(x, y), (x + w, y + h)], fill=None, outline='green', width=5)

        font = ImageFont.truetype(font='./arial.ttf', size=18)

        bbox = draw.textbbox((x, y), caption, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.rectangle([(x, y), (x + text_w, y + text_h)], fill='green')
        draw.text((x, y), caption, fill='white', font=font)

    tags_name = '/ '.join(tags_name)

    # Streamlit UIの表示
    st.image(img)

    st.markdown('**認識されたコンテンツタグ**')
    st.markdown(f'{tags_name}')
    st.markdown(f'{p_name}')

    # 処理が終わったらBlobからファイルを削除
    blob_client.delete_blob()
