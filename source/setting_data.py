#-*- coding:utf-8 -*-

class SettingData():
    """ 設定値を保持するクラス
    """

    def __init__(self):
        """ コンストラクタ
        """
        self.outline_low     = 0
        self.outline_high    = 0
        self.outline_rough   = 0 # 粗さ
        self.outline_blur    = 0 # 線ぼかし

        self.img_blur_blur   = 0

        self.contrast_low    = 0
        self.contrast_high   = 0

        self.checkbox_line_flg   = True
        self.checkbox_shadow_flg = True
 

    def set_outline_range(self, low, high):
        """ アウトラインの範囲の値を設定する関数

            Args:
                low (int) : 下限
                high (int): 上限
        """
        self.outline_low  = low
        self.outline_high = high


    def set_outline_rough_blur(self, rough, blur):
        """ アウトラインの粗さと線ぼかしの値を設定する関数

            Args:
                rough (int): 粗さ
                blur (int) : 線ぼかし
        """
        self.outline_rough = rough
        self.outline_blur  = blur


    def set_img_blur_blur(self, blur):
        """ 画像のぼかし値を設定する関数

            Args:
                blur (int) : 線ぼかし
        """
        self.img_blur_blur = blur


    def set_contrast_range(self, low, high):
        """ コントラストの範囲の値を設定する関数

            Args:
                low (int) : 下限
                high (int): 上限
        """
        self.contrast_low  = low
        self.contrast_high = high


    def set_checkbox_line_shadow(self, line_flg, shadow_flg):
        """ 変換内容のフラグを設定する関数

            Args:
                line_flg (bool)  : 線出力
                shadow_flg (bool): 影出力
        """
        self.checkbox_line_flg   = line_flg
        self.checkbox_shadow_flg = shadow_flg
