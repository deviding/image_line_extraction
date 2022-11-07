#-*- coding:utf-8 -*-
from setting_data import SettingData
import cv2
import numpy as np
import copy

from PySide6.QtGui import *


class LineExtraction():
    """ 線抽出を行うクラス
    """

    def __init__(self):
        """ コンストラクタ
        """
        self.cv2_img      = None
        self.setting_data = None


    def set_image_setting(self, cv2_img, setting_data: SettingData):
        """ 変換する画像と設定値のオブジェクトを設定する関数

            Args:
                cv2_img (img): 変換画像
                setting_data (SettingData) : 設定値オブジェクト
        """
        self.cv2_img = cv2_img
        self.setting_data = setting_data


    def set_image(self, cv2_img):
        """ 変換する画像を設定する関数

            Args:
                cv2_img (img): 変換画像
        """
        self.cv2_img = cv2_img


    def set_setting_data(self, setting_data: SettingData):
        """ 設定値のオブジェクトを設定する関数

            Args:
                setting_data (SettingData) : 設定値オブジェクト
        """
        self.setting_data = setting_data


    def line_extraction(self):
        """ 画像を変換する関数

            Returns:
                result_img (img): 変換後画像
        """
        # 1:グレースケール化
        gray_img = cv2.cvtColor(self.cv2_img, cv2.COLOR_BGR2GRAY)
        # 2:ぼかす
        gray_img = self.img_blur(gray_img)
        # 3:輪郭線抽出
        outline_img = self.outine(gray_img)

        line_blur_size = self.setting_data.outline_rough
        if line_blur_size % 2 == 0:
            line_blur_size = line_blur_size + 1 # blurサイズは奇数じゃないとエラーになる

        # 4:輪郭線をぼかす
        outline_img = cv2.GaussianBlur(outline_img, (line_blur_size, line_blur_size), line_blur_size)
        outline_low  = self.setting_data.outline_low
        outline_high = self.setting_data.outline_high

        # 5:閾値で2値化
        _, outline_img = cv2.threshold(outline_img, outline_low, outline_high, cv2.THRESH_BINARY)

        line_state = self.setting_data.checkbox_line_flg
        shadow_state = self.setting_data.checkbox_shadow_flg

        # 6:影部分の処理(ぼかして閾値で2値化)
        gray_img = self.img_blur(gray_img) # ぼかす
        _, gray_img = cv2.threshold(gray_img, outline_low, outline_high, cv2.THRESH_BINARY)
        gray_img = self.low_contrast(gray_img)

        if line_state and shadow_state:
            # 両方にチェックがあった場合は7:輪郭線と影部分の画像を合成
            result_img = cv2.bitwise_and(outline_img, gray_img)
        elif line_state:
            # 線のみの場合は線だけ
            result_img = outline_img
        elif shadow_state:
            # 影のみの場合は影だけ
            result_img = gray_img
        else:
            # 両方チェックがなかったらそのまま
            result_img = self.cv2_img

        return result_img


    def img_blur(self, cv2_img):
        """ 設定値で画像をぼかす関数

            Args:
                cv2_img (img): 変換画像
    
            Returns:
                img (img): 処理後画像
        """
        blur_value = self.setting_data.img_blur_blur
        blur_size = blur_value
        if blur_value % 2 == 0:
            blur_size = blur_size + 1 # blurサイズは奇数じゃないとエラーになる

        return cv2.GaussianBlur(cv2_img, (blur_size, blur_size), blur_value) # ぼかす


    def outine(self, cv2_gray_img):
        """ 画像の輪郭線を抽出する関数

            Args:
                cv2_img (img): 変換二値化画像

            Returns:
                img (img): 処理後画像
        """
        # リサイズ
        fx = int(cv2_gray_img.shape[1] / self.setting_data.outline_rough)
        fy = int(cv2_gray_img.shape[0] / self.setting_data.outline_rough)
        gray_rezise_img = cv2.resize(cv2_gray_img, (fx, fy))

        # 輪郭線抽出
        outline_img = 255 - cv2.Canny(gray_rezise_img, self.setting_data.outline_high, self.setting_data.outline_low)
        return cv2.resize(outline_img, (cv2_gray_img.shape[1], cv2_gray_img.shape[0]))


    def low_contrast(self, cv2_img):
        """ コントラストを低減させる関数

            Args:
                cv2_img (img): 変換画像

            Returns:
                img (img): 処理後画像
        """
        # ルックアップテーブルの生成
        min_table = self.setting_data.contrast_low
        max_table = self.setting_data.contrast_high
        diff_table = max_table - min_table
        look_up_table = np.arange(256, dtype = 'uint8')
    
        for i in range(0, 255):
            look_up_table[i] = min_table + i * (diff_table) / 255
    
        # コントラストを低減させた結果を返す
        return cv2.LUT(cv2_img, look_up_table)


    def get_qpixmap(self, cv2_img, w, h):
        """ 画像をプレビューに表示する形式であるQPixmapに変換する関数

            Args:
                cv2_img (img): 変換画像
                w (int): width
                h (int): height

            Returns:
                img (img): 変換後画像
        """
        img = copy.deepcopy(cv2_img)

        # プレビュー画面に収まるように縮小
        w_ratio = img.shape[1] / w
        h_ratio = img.shape[0] / h

        if (w_ratio <= 1) and (h_ratio <= 1):
            ratio = 1
        elif w_ratio > h_ratio:
            ratio = w_ratio
        else:
            ratio = h_ratio

        fx = int(img.shape[1]/ratio)
        fy = int(img.shape[0]/ratio)
        img = cv2.resize(img, (fx, fy))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # QtはBGRなので順番を変更

        height, width, _ = img.shape
        bytePerLine = img.strides[0] # ⇒ 3*width相当

        qimg = QImage(img.data, width, height, bytePerLine, QImage.Format.Format_RGB888)       
        return QPixmap(QPixmap.fromImage(qimg))