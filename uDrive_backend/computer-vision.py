import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import torch
import torchvision.transforms as T
from torchvision.models.detection import fasterrcnn_resnet50_fpn
import os
import shutil
import subprocess
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
import moviepy.editor as mp
import mysql.connector
from mysql.connector import Error
import uuid

class OtonomSurus:
    def __init__(self):
        # Onceden egitilmis modelin yuklenmesi
        self.model = fasterrcnn_resnet50_fpn(pretrained=True)
        self.model.eval()
        self.yolo_model = "yolov8m.pt"
        self.ortalama_hiz_kmsaat = 0
        self.total_distance = 0

    #TRAFIK ISIGI TESPITI
    # Goruntunun pytorch icin uygun hale getirilmesi
    def transform_image(self, image):
        transform = T.Compose([T.ToTensor()])
        transformed_image = transform(image).unsqueeze(0)
        return transformed_image

    # Goruntunun renk analizinin yapilmasi
    def renk_dagilim_analizi(self, image):
        hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        return hist

    # Goruntulerin renk analizlerinin karsilastirilmasi
    def renk_analiz_karsilastirma(self, hist1, hist2, hist3):
        diff1 = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CHISQR)
        diff2 = cv2.compareHist(hist2, hist3, cv2.HISTCMP_CHISQR)
        diff3 = cv2.compareHist(hist1, hist3, cv2.HISTCMP_CHISQR)
        return diff1, diff2, diff3

    def trafik_isigi_tespit(self, video,output_path):
        # Video dosyasinin okunmasi
        cap = cv2.VideoCapture(video)

        # Video ozelliklerinin alinmasi
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        # Video yazicilarinin tanimlanmasi

        out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))

        while cap.isOpened():
            # Bir sonraki frame'in alinmasi
            ret, frame = cap.read()
            if not ret:
                break

            # Frame'in PIL icin uygun hale donusturulmesi
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # Goruntunun pytorch icin yazilan fonksiyonla islenmesi
            image_tensor = self.transform_image(image)

            # resnet ile nesne tespitinin yapilmasi
            with torch.no_grad():
                prediction = self.model(image_tensor)

            # Tespit edilen trafik isiklarinin ve doğruluk degerlerinin kaydedilmesi
            traffic_lights = [(box, score) for box, label, score in
                              zip(prediction[0]['boxes'], prediction[0]['labels'], prediction[0]['scores']) if
                              label == 10]

            image_np = np.array(frame)

            if traffic_lights:
                # Frame'in renk uzayinin tekrar RGB'ye donusturulmesi
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                text_content = ""

                for box, score in traffic_lights:
                    if score > 0.90:
                        # Trafik isiginin 3 parcaya bolunmesi
                        x1 = int(box[0])
                        y1 = int(box[1])
                        x2 = int(box[2])
                        y2 = int(box[3])
                        third_height = (y2 - y1) // 3

                        part1 = frame_rgb[y1:y1 + third_height, x1:x2, :]
                        part2 = frame_rgb[y1 + third_height:y1 + 2 * third_height, x1:x2, :]
                        part3 = frame_rgb[y1 + 2 * third_height:y2, x1:x2, :]

                        # Parcaların renk analizinin yapilmasi
                        hist1 = self.renk_dagilim_analizi(part1)
                        hist2 = self.renk_dagilim_analizi(part2)
                        hist3 = self.renk_dagilim_analizi(part3)

                        # Parcaların renk analizlerinin karsilastirilmasi
                        diff1, diff2, diff3 = self.renk_analiz_karsilastirma(hist1, hist2, hist3)

                        # Trafik isiginin renginin tespit edilmesi
                        listee = [diff1, diff2, diff3]
                        sorted_listee = sorted(listee, reverse=True)

                        # Trafik isigi bilgilerinin kutunun yanina yazdirilmasi
                        font_scale = 1.5
                        if (sorted_listee[0] == diff1 and sorted_listee[1] == diff3) or (
                                sorted_listee[0] == diff3 and sorted_listee[1] == diff1):
                            color_light = "Kirmizi"
                            text = f"{score:.2f} {color_light}"
                            cv2.rectangle(image_np, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 0, 255),
                                          2)
                            cv2.putText(image_np, text, (int(box[0]), int(box[1] - 5)), cv2.FONT_HERSHEY_SIMPLEX,
                                        font_scale,
                                        (0, 0, 255), 2)

                        elif (sorted_listee[0] == diff2 and sorted_listee[1] == diff1) or (
                                sorted_listee[0] == diff1 and sorted_listee[1] == diff2):
                            color_light = "Sari"
                            text = f"{score:.2f} {color_light}"
                            cv2.rectangle(image_np, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])),
                                          (0, 255, 255), 2)
                            cv2.putText(image_np, text, (int(box[0]), int(box[1] - 5)), cv2.FONT_HERSHEY_SIMPLEX,
                                        font_scale,
                                        (0, 255, 255), 2)

                        elif (sorted_listee[0] == diff2 and sorted_listee[1] == diff3) or (
                                sorted_listee[0] == diff3 and sorted_listee[1] == diff2):
                            color_light = "Yesil"
                            text = f"{score:.2f} {color_light}"
                            cv2.rectangle(image_np, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 0),
                                          2)
                            cv2.putText(image_np, text, (int(box[0]), int(box[1] - 5)), cv2.FONT_HERSHEY_SIMPLEX,
                                        font_scale,
                                        (0, 255, 0), 2)

                        else:
                            color_light = "Belirlenemedi"
                            text = f"{score:.2f} {color_light}"
                            cv2.rectangle(image_np, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 0, 0),
                                          2)
                            cv2.putText(image_np, text, (int(box[0]), int(box[1] - 5)), cv2.FONT_HERSHEY_SIMPLEX,
                                        font_scale,
                                        (0, 0, 0), 2)

            # Videoya frame'in yazilmasi
            out.write(image_np)


        # Videolarin serbest birakilmasi
        cap.release()
        out.release()
        cv2.destroyAllWindows()


    # NESNE TESPIT
    def nesne_tespit(self, input_video,output_path):
        # YOLO ile nesne tespit yapilmasi
        yolo_process = subprocess.run(
            f"yolo detect predict model={self.yolo_model} source={input_video}",
            shell=True,
            capture_output=True
        )

        # Output videosunun konumunun bulunmasi
        output_directory = "runs/detect/predict"
        output_video = None
        for root, dirs, files in os.walk(output_directory):
            for file in files:
                output_video = os.path.join(root, file)

        # Videonun bulunulan dizine tasinmasi ve runs klasorunun silinmesi
        if output_video:
            new_output_video_path = os.path.join(os.getcwd(), output_path)
            shutil.move(output_video, new_output_video_path)
            shutil.rmtree("runs")

    #SERIT TESPIT
    # Şeritlerin sadece yolda tespit edilmesini sağlayacak bir bolge kisitlamasi
    def bolge_kisitlamasi(self, frame):
        height = frame.shape[0]
        width = frame.shape[1]
        koseler = np.array([[(0, height), (width*0.1, 0.90*height), (width/5*4, 0.90*height), (width, height)]], dtype=np.int32)
        kisitlama = np.zeros_like(frame)
        cv2.fillPoly(kisitlama, koseler, 255)
        kisitlanmis_frame = cv2.bitwise_and(frame, kisitlama)
        return kisitlanmis_frame

    def serit_tespit(self, video_path,output_path):
        # Video dosyasinin okunmasi
        cap = cv2.VideoCapture(video_path)

        # Video boyutunun ve fps bilgisinin alinmasi
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        # Video yazicisinin tanimlanmasi
        out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

        while True:
            # Bir sonraki frame'in alinmasi
            ret, frame = cap.read()
            if not ret:
                break

            # Frame'in gri tonlamaya donusturulmesi
            gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Frame'e threshold uygulanmasi - pixel degeri 200'den buyukse beyaz, kucukse siyah olur
            (thresh, filtrelenmis_frame) = cv2.threshold(gray_image, 200, 255, cv2.THRESH_BINARY)

            # Frame'e gurultu azaltmak icin Gauss filtresi ve kenar tespiti icin Canny algoritmasinin uygulanmasi
            filtrelenmis_frame = cv2.GaussianBlur(filtrelenmis_frame, (5, 5), 3)
            filtrelenmis_frame = cv2.Canny(filtrelenmis_frame, 180, 255)

            # Bolge kisitlamsinin frame'e uygulanmasi
            kisitlanmis_frame = self.bolge_kisitlamasi(filtrelenmis_frame)

            # Cizgi tespiti yapilir
            cizgiler, _ = cv2.findContours(kisitlanmis_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Belirlenen seritler cizilir
            for cizgi in cizgiler:
                cv2.drawContours(frame, [cizgi], -1, (0, 255, 0), 3)

            # Videoya frame'in yazilmasi
            out.write(frame)


        # Videolarin serbest birakilmasi
        cap.release()
        out.release()
        cv2.destroyAllWindows()


    #HIZ TESPIT
    def hiz_tespit(self, video,output_path):
        # Video dosyasinin okunmasi
        cap = cv2.VideoCapture(video)

        # Video ozelliklerinin alinmasi
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Video yazicilarinin tanimlanmasi
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Hiz ve konum bilgileri
        self.total_distance = 0
        frame_count = 0
        prev_position = None

        # Piksel basina mesafe (1 piksel yaklasik 0.002 metre)
        meters_per_pixel = 0.002

        while True:
            # Bir sonraki frame'in alinmasi
            ret, frame = cap.read()
            if not ret:
                break

            # Frame'in gri tonlamaya donusturulmesi
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Frame'e kenar tespiti yapilmasi
            edges = cv2.Canny(gray_frame, 50, 150)

            # Kenarlarin belirlenmesi
            cizgiler, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Cizgi bulunmussa
            if cizgiler:
                # En buyuk alana sahip cizginin alinmasi
                c = max(cizgiler, key=cv2.contourArea)
                area = cv2.contourArea(c)

                # Cizgilerin alani yeterince buyukse (ornegin, bir araba penceresi gibi)
                if area > 10:
                    # Cizgilerin merkezinin bulunmasi
                    merkez = cv2.moments(c)
                    cx = int(merkez['m10'] / merkez['m00'])
                    cy = int(merkez['m01'] / merkez['m00'])

                    # Onceki konum varsa, hizin hesaplanmasi
                    if prev_position is not None:
                        # Onceki konum ile mevcut konum karsilastirarak hizin hesaplanmasi
                        distance_pixels = np.sqrt((cx - prev_position[0]) ** 2 + (cy - prev_position[1]) ** 2)
                        distance_meters = distance_pixels * meters_per_pixel
                        hiz_metresaniye = distance_meters * fps  # metre/saniye cinsinden hiz
                        hiz_kmsaat = hiz_metresaniye * 3.6  # km/saat cinsine donusturulmesi

                        self.total_distance += distance_meters

                        # Hizin frame'e yazilmasi
                        cv2.putText(frame, "Hiz: {:.2f} km/s".format(hiz_kmsaat), (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                    # Mevcut konumun onceki konum olarak guncellenmesi
                    prev_position = (cx, cy)

                    frame_count += 1

            # Videoya frame'in yazilmasi
            output_video.write(frame)

        # Videolarin serbest birakilmasi
        cap.release()
        output_video.release()
        cv2.destroyAllWindows()

        # Ortalama hizin hesaplanmasi
        total_time_seconds = frame_count / fps
        ortalama_hiz_metresaniye = self.total_distance / total_time_seconds if total_time_seconds > 0 else 0
        self.ortalama_hiz_kmsaat = ortalama_hiz_metresaniye * 3.6

        print("Bu videodaki ortalama hiz: {:.2f} km/s".format(self.ortalama_hiz_kmsaat))
        print("Bu videoda gidilen mesafe yaklaşık: {:.2f} metre".format(self.total_distance))

    def create_connection(self):
            try:
                connection = mysql.connector.connect(
                    host='localhost',  # Veritabanı sunucusu adresi
                    database='uDrives',  # Veritabanı adı
                    user='root',  # Veritabanı kullanıcı adı
                    password='Kubra3460'  # Veritabanı kullanıcı şifresi
                )
                if connection.is_connected():
                    print("MySQL veritabanına başarıyla bağlanıldı")
                    return connection
            except Error as e:
                print("MySQL bağlantı hatası:", e)
                return None

    def insert_user(self,userID, userName, userPassword):
        connection = self.create_connection()
        if connection:
            cursor = connection.cursor()
            try:
                sql_insert_query = """INSERT INTO users (userID, userName,userPassword) VALUES (%s, %s, %s)"""
                cursor.execute(sql_insert_query, (userID, userName, userPassword))
                connection.commit()
                print("Kayıt başarılı bir şekilde eklendi")
            except Error as e:
                print("Veri eklenirken hata oluştu:", e)
            finally:
                cursor.close()
                connection.close()
                print("MySQL bağlantısı kapatıldı")

    def insert_user_record(self,tarih,ortHizBilgisi,mesafe, hiz, trafikIsigi, nesneTespit, seritTakip, analysis):
        connection = self.create_connection()
        if connection:
            cursor = connection.cursor()
            try:
                sql_insert_query = """INSERT INTO user (tarih,ortHizBilgisi,mesafe, hiz, trafikIsigi, nesneTespit, seritTakip,analysis) 
                                      VALUES (%s, %s,%s,%s, %s, %s, %s, %s)"""
                cursor.execute(sql_insert_query, (tarih, ortHizBilgisi,mesafe,hiz, trafikIsigi, nesneTespit, seritTakip, analysis))
                connection.commit()
                print("Kayıt başarılı bir şekilde eklendi")
            except Error as e:
                print("Veri eklenirken hata oluştu:", e)
            finally:
                cursor.close()
                connection.close()
                print("MySQL bağlantısı kapatıldı")
    def find_videos_in_current_directory_recursively_by_name(self,video_name):
        current_directory = os.getcwd()
        video_paths = []
        for root, dirs, files in os.walk(current_directory):
            for file in files:
                if video_name.lower() in file.lower() and file.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.flv')):
                    video_paths.append(os.path.join(root, file))
        return video_paths



if __name__ == "__main__":
    surus_analiz = OtonomSurus()
    
    # Fonksiyonlarin calistirilmasi
    surus_analiz.serit_tespit(video_path,"serit_tespit.mp4")
    surus_analiz.hiz_tespit("serit_tespit.mp4","hiz_tespit.mp4")
    surus_analiz.trafik_isigi_tespit("hiz_tespit.mp4","trafik_isigi_tespit.mp4")
    surus_analiz.nesne_tespit("trafik_isigi_tespit.mp4","otonom_surus.mp4")

    surus_analiz.serit_tespit(video_path,"serit.mp4")
    surus_analiz.hiz_tespit(video_path,"hiz.mp4")
    surus_analiz.trafik_isigi_tespit(video_path,"trafik_isigi.mp4")
    surus_analiz.nesne_tespit(video_path,"nesne.mp4")

    original_value = surus_analiz.ortalama_hiz_kmsaat
    ort_hiz = float(round(original_value, 2))
    original = surus_analiz.total_distance
    mesafe = float(round(original, 2))

    # Kullanım
    hiz = 'hiz.mp4' 

    videos = surus_analiz.find_videos_in_current_directory_recursively_by_name(hiz)
    for video in videos:
        hiz_path = video

    # Kullanım
    serit = 'serit.mp4'  

    videos = surus_analiz.find_videos_in_current_directory_recursively_by_name(serit)
    for video in videos:
        serit_takip_path = video

    # Kullanım
    trafik_isigi = 'trafik_isigi.mp4' 

    videos = surus_analiz.find_videos_in_current_directory_recursively_by_name(trafik_isigi)
    for video in videos:
        trafik_isigi_path = video

    # Kullanım
    nesne= 'nesne.mp4' 

    videos = surus_analiz.find_videos_in_current_directory_recursively_by_name(nesne)
    for video in videos:
        nesne_tespit_path = video

    # Kullanım
    otonom_surus = 'otonom_surus.mp4'  
    
    videos = surus_analiz.find_videos_in_current_directory_recursively_by_name(otonom_surus)
    for video in videos:
        genel_surus_path = video
    surus_analiz.create_connection()
    surus_analiz.insert_user(3, 'Kubra', 'password123')

    # Video dosyalarının yolunu kaydet
    serit_takip_path = "/Users/kubra/Desktop/PycharmProjects/pythonProject5/serit.mp4"
    hiz_path = "/Users/kubra/Desktop/PycharmProjects/pythonProject5/hiz.mp4"
    trafik_isigi_path = "/Users/kubra/Desktop/PycharmProjects/pythonProject5/trafik_isigi.mp4"
    nesne_tespit_path = surus_analiz.nesne_tespit_data(b"nesne.mp4", "nesne.mp4")
    genel_surus_path = surus_analiz.genel_surus_data(b"otonom_surus.mp4","otonom_surus.mp4")

    print(f"serit: {serit_takip_path}")
    print(f"hiz: {hiz_path}")
    print(f"trafik_isigi: {trafik_isigi_path}")
    print(f"nesne_tespit: {nesne_tespit_path}")
    print(f"genel_surus: {genel_surus_path}")




