#-*- coding:utf-8 -*-
from setting_data import SettingData
from line_extraction import LineExtraction
from batch import BatchGui

import os, sys, copy, json
import cv2
import numpy as np
from PIL import Image
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class ImageLineGui(QDialog):
    """ 大本のGUIクラス
    """
    VERSION = "1.0"
    TITLE = "Image Line Extraction v{}".format(VERSION)
    WINDOW_WIDTH  = 660
    WINDOW_HEIGHT = 580
    NO_IMG_PATH = "img/no_image.png"
    PREVIEW_WIDTH  = 640
    PREVIEW_HEIGHT = 360
    SAVE_FILE_DEFAULT = "./outline.png"
    SAVE_SETTING_FILE = "/setting.json"
    DEFAULT_SETTING_FILE = "json/default.json"
    CENTER = Qt.AlignmentFlag.AlignCenter


    def __init__(self, parent=None):
        """ コンストラクタ
        """
        super(ImageLineGui, self).__init__(parent)

        # アイコン画像を設定
        if sys.platform.startswith('win'):
            self.setWindowIcon(QPixmap(self.temp_path('img/icon.ico')))

        self.line_extraction = LineExtraction() # 画像変換用オブジェクト
        self.batch_form = BatchGui(self)
        self.batch_form.hide()

        # 実行ファイルパスと設定ファイルパス
        self.my_dir_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        self.json_path = self.my_dir_path + self.SAVE_SETTING_FILE
        self.default_json_path = self.temp_path(self.DEFAULT_SETTING_FILE)

        self.setting_data = {} # 設定ファイル内のデータ

        self.img_org = None # 加工元のオリジナルの画像
        self.img     = None # 加工後の画像

        # Widgetsの設定(タイトル、固定横幅、固定縦幅)
        self.setWindowTitle(self.TITLE)
        self.setFixedWidth(self.WINDOW_WIDTH)
        self.setFixedHeight(self.WINDOW_HEIGHT)

        # 画像ファイル選択部分
        file_layout = QHBoxLayout()
        self.img_path = QLineEdit("")
        self.img_path.setEnabled(False) # テキスト入力を禁止
        self.file_select_button = QPushButton("参照")
        self.file_select_button.clicked.connect(self.img_dialog)
        file_layout.addWidget(self.create_label("[変換画像ファイル]", True), 1)
        file_layout.addWidget(self.img_path, 5)
        file_layout.addWidget(self.file_select_button, 1)

        # 設定値選択部分
        setting_layout = QHBoxLayout()
        self.combobox = QComboBox(self)
        self.combobox.currentTextChanged.connect(self.set_setting_value)
        self.setting_save_button = QPushButton("保存")
        self.setting_save_button.clicked.connect(self.show_save_dialog)
        self.setting_delete_button = QPushButton("削除")
        self.setting_delete_button.clicked.connect(self.delete_setting)
        setting_layout.addWidget(self.create_label("[設定値選択]", True), 1)
        setting_layout.addSpacing(3)
        setting_layout.addWidget(self.combobox, 4)
        setting_layout.addWidget(self.setting_save_button, 1)
        setting_layout.addWidget(self.setting_delete_button, 1)

        # 輪郭線調節部分
        self.outline_low_sp = self.create_spinbox(0, 255, 70)
        self.outline_low_sp.valueChanged.connect(self.outline_low_change)
        self.outline_high_sp = self.create_spinbox(0, 255, 110)
        self.outline_high_sp.valueChanged.connect(self.outline_high_change)
        self.outline_rough_sp = self.create_spinbox(1, 10, 5)
        self.outline_blur_sp = self.create_spinbox(1, 10, 5)

        outline_layout = QVBoxLayout()
        outline_upper_layout = QHBoxLayout()
        outline_upper_layout.addWidget(QLabel("上限:"), 1)
        outline_upper_layout.addWidget(self.outline_high_sp, 2)
        outline_upper_layout.addWidget(QLabel("　　粗さ:"), 1.5)
        outline_upper_layout.addWidget(self.outline_rough_sp, 2)
        outline_layout.addLayout(outline_upper_layout, 1)
        outline_lower_layout = QHBoxLayout()
        outline_lower_layout.addWidget(QLabel("下限:"), 1)
        outline_lower_layout.addWidget(self.outline_low_sp, 2)
        outline_lower_layout.addWidget(QLabel(" 線ぼかし:"), 1.5)
        outline_lower_layout.addWidget(self.outline_blur_sp, 2)
        outline_layout.addLayout(outline_lower_layout, 1)

        # ぼかし部分
        blur_layout = QVBoxLayout()
        self.blur_sp = self.create_spinbox(0, 255, 10)
        blur_layout.addWidget(self.blur_sp, 1)

        # コントラスト調節部分
        contrast_layout = QVBoxLayout()
        self.contrast_low_sp = self.create_spinbox(0, 255, 50)
        self.contrast_low_sp.valueChanged.connect(self.contrast_low_change)
        self.contrast_high_sp = self.create_spinbox(0, 255, 230)
        self.contrast_high_sp.valueChanged.connect(self.contrast_high_change)
        contrast_upper_layout = QHBoxLayout()
        contrast_upper_layout.addWidget(QLabel("　上限:"), 1)
        contrast_upper_layout.addWidget(self.contrast_high_sp, 2)
        contrast_layout.addLayout(contrast_upper_layout, 1)
        contrast_lower_layout = QHBoxLayout()
        contrast_lower_layout.addWidget(QLabel("　下限:"), 1)
        contrast_lower_layout.addWidget(self.contrast_low_sp, 2)
        contrast_layout.addLayout(contrast_lower_layout, 1)

        # チェックボックス部分
        c_upper_layout = QHBoxLayout()
        self.line_checkbox   = QCheckBox()
        self.line_checkbox.setCheckState(Qt.CheckState.Checked)
        c_upper_layout.addWidget(QLabel("　　線出力:"), 1.8)
        c_upper_layout.addWidget(self.line_checkbox, 1)

        c_lower_layout = QHBoxLayout()
        self.shadow_checkbox = QCheckBox()
        self.shadow_checkbox.setCheckState(Qt.CheckState.Checked)
        c_lower_layout.addWidget(QLabel("　　影出力:"), 1.8)
        c_lower_layout.addWidget(self.shadow_checkbox, 1)

        checkbox_layout = QVBoxLayout()
        checkbox_layout.addLayout(c_upper_layout, 1)
        checkbox_layout.addLayout(c_lower_layout, 1)

        # 設定値部分をまとめる
        PADDING_SPACE = 32
        title_layout = QHBoxLayout()
        title_layout.addWidget(self.create_label("[アウトライン範囲]", True, self.CENTER), 2)
        title_layout.addSpacing(PADDING_SPACE)
        title_layout.addWidget(self.create_label("[画像のぼかし値]", True, self.CENTER), 1)
        title_layout.addSpacing(PADDING_SPACE)
        title_layout.addWidget(self.create_label(" [コントラスト範囲]", True, self.CENTER), 1)
        title_layout.addSpacing(PADDING_SPACE)
        title_layout.addWidget(self.create_label(" [変換内容]", True, self.CENTER), 1)

        setting_element_layout = QHBoxLayout()
        setting_element_layout.addLayout(outline_layout, 2)
        setting_element_layout.addSpacing(PADDING_SPACE)
        setting_element_layout.addLayout(blur_layout, 1)
        setting_element_layout.addSpacing(PADDING_SPACE)
        setting_element_layout.addLayout(contrast_layout, 1)
        setting_element_layout.addSpacing(PADDING_SPACE)
        setting_element_layout.addLayout(checkbox_layout, 1)

        # 画像プレビュー部分
        img_org = np.array(Image.open(self.temp_path(self.NO_IMG_PATH)))
        # RGBに変換する
        cv2_img = cv2.cvtColor(img_org, cv2.COLOR_BGR2RGB)
        # 読み込んだオリジナル画像をクラス変数に代入
        self.img_org = copy.deepcopy(cv2_img)
        img = self.line_extraction.get_qpixmap(cv2_img, self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT)
        img_layout = QHBoxLayout()
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # 画像を中央に表示
        self.img_label.setPixmap(img)
        self.img_label.setFrameStyle(QFrame.Box)
        img_layout.addWidget(self.img_label)

        # プレビュー/保存/一括処理ボタン部分
        btn_layout = QHBoxLayout()
        self.pre_btn = QPushButton("変換プレビュー")
        self.pre_btn.clicked.connect(self.img_preview)
        self.pre_btn.setEnabled(False)
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_img_dialog)
        self.save_btn.setEnabled(False)
        self.batch_btn = QPushButton("一括処理")
        self.batch_btn.clicked.connect(self.batch_dialog)
        self.batch_btn.setEnabled(True)
        btn_layout.addWidget(QLabel(""), 1)
        btn_layout.addWidget(self.pre_btn, 2)
        btn_layout.addWidget(QLabel(""), 1)
        btn_layout.addWidget(self.save_btn, 2)
        btn_layout.addWidget(QLabel(""), 1)
        btn_layout.addWidget(self.batch_btn, 2)
        btn_layout.addWidget(QLabel(""), 1)

        # レイアウトを作成して各要素を配置
        layout = QVBoxLayout()
        layout.addLayout(file_layout)
        layout.addSpacing(6)
        layout.addLayout(setting_layout)
        layout.addSpacing(6)
        layout.addLayout(title_layout)
        layout.addSpacing(6)
        layout.addLayout(setting_element_layout)
        layout.addLayout(img_layout)
        layout.addSpacing(6)
        layout.addLayout(btn_layout)

        # レイアウトを画面に設定
        self.setLayout(layout)

        # プルダウンの設定値を設定
        self.set_setting_list()


    def temp_path(self, relative_path):
        """ 実行時のパスを取得する関数

            Args:
                relative_path (str): 相対ファイルパス
            
            Returns:
                実行時のパス文字列
        """
        try:
            #Retrieve Temp Path
            base_path = sys._MEIPASS
        except Exception:
            #Retrieve Current Path Then Error 
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)


    def set_setting_list(self):
        """ 保存されている設定値をプルダウンに設定する関数
        """
        if os.path.exists(self.json_path):
            # 設定ファイルがあった場合はファイルを読み込む
            self.setting_data = self.load_json_file(self.json_path)
        else:
            # 設定ファイルがない場合はデフォルトのファイルを読み込む
            self.setting_data = self.load_json_file(self.default_json_path)

        setting_name_list = [*self.setting_data] # キーのみをリストとして取得
        setting_name_list.insert(0, "")     # 先頭に空文字を追加

        # 現在の選択値文字列を取得してプルダウンリストを更新
        current_str = self.combobox.currentText()
        self.combobox.clear()
        self.combobox.addItems(setting_name_list)

        if len(setting_name_list) > 2:
            # 何もない場合は空文字をセット
            self.combobox.setCurrentIndex(0)
        else:
            # 選択しているものを再セット
            self.combobox.setCurrentIndex(setting_name_list.index(current_str))


    def set_setting_value(self):
        """ 設定値を設定する関数
        """
        # 現在の選択値文字列を取得
        current_str = self.combobox.currentText()

        if current_str == "":
            return

        # 値を設定
        self.outline_low_sp.setValue(self.setting_data[current_str]['outline']['low'])
        self.outline_high_sp.setValue(self.setting_data[current_str]['outline']['high'])
        self.outline_rough_sp.setValue(self.setting_data[current_str]['outline']['rough'])
        self.outline_blur_sp.setValue(self.setting_data[current_str]['outline']['blur'])
        self.blur_sp.setValue(self.setting_data[current_str]['img_blur']['blur'])
        self.contrast_low_sp.setValue(self.setting_data[current_str]['contrast']['low'])
        self.contrast_high_sp.setValue(self.setting_data[current_str]['contrast']['high'])
        if self.setting_data[current_str]['checkbox']['line']:
            self.line_checkbox.setCheckState(Qt.CheckState.Checked)
        else:
            self.line_checkbox.setCheckState(Qt.CheckState.Unchecked)

        if self.setting_data[current_str]['checkbox']['shadow']:
            self.shadow_checkbox.setCheckState(Qt.CheckState.Checked)
        else:
            self.shadow_checkbox.setCheckState(Qt.CheckState.Unchecked)


    def show_save_dialog(self):
        """ 設定値保存のダイアログを表示する関数
        """
        # 設定値名を入力するダイアログを表示
        text, ok = QInputDialog.getText(self, "設定値保存", "設定名: ", QLineEdit.Normal, "")

        if ok and text:
            # OKかつ設定値名が入力されていた場合は保存を実行
            self.save_setting(text)
        elif ok and text == "":
            # OKかつ設定値が入力なしの場合は警告を出して再起呼び出し
            QMessageBox.warning(self, "注意", "設定名が入力されていません。")
            self.show_save_dialog()


    def save_setting(self, name):
        """ 設定値を保存する関数

            Args:
                name (str)  : 保存名
        """
        if name in self.setting_data:
            # 既に設定値が存在する場合は上書き確認
            ret = QMessageBox.warning(self, "注意", "対象の設定値「 " + name + "」 を上書きします。よろしいですか？", QMessageBox.Ok, QMessageBox.Cancel)
            # 上書きキャンセルの場合は何もしない
            if ret == QMessageBox.Cancel:
                return

        # デフォルトのjsonファイルを読み込んで追加データを作成
        add_data = self.load_json_file(self.default_json_path)
        add_data['default']['outline']['low']    = self.outline_low_sp.value()
        add_data['default']['outline']['high']   = self.outline_high_sp.value()
        add_data['default']['outline']['rough']  = self.outline_rough_sp.value()
        add_data['default']['outline']['blur']  = self.outline_blur_sp.value()
        add_data['default']['img_blur']['blur'] = self.blur_sp.value()
        add_data['default']['contrast']['low']   = self.contrast_low_sp.value()
        add_data['default']['contrast']['high']  = self.contrast_high_sp.value()
        # チェックボックスの設定
        if self.line_checkbox.checkState() == Qt.CheckState.Checked:
            add_data['default']['checkbox']['line'] = True
        else:
            add_data['default']['checkbox']['line'] = False

        if self.shadow_checkbox.checkState() == Qt.CheckState.Checked:
            add_data['default']['checkbox']['shadow'] = True
        else:
            add_data['default']['checkbox']['shadow'] = False

        add_data[name] = add_data.pop('default', add_data['default'])

        # データを追加して保存
        self.setting_data.update(add_data)
        self.save_json_file(self.json_path, self.setting_data)
        # プルダウンリストを更新
        self.combobox.setCurrentText(name)
        self.set_setting_list()
        # ダイアログを表示
        QMessageBox.information(self, "正常終了", "対象の設定値「 " + name + " 」を保存しました。プルダウンから選択してください。")


    def delete_setting(self):
        """ 設定値を削除する関数
        """
        current_str = self.combobox.currentText()

        setting_data = self.load_json_file(self.json_path)
        setting_name_list = [*setting_data] # キーのみをリストとして取得

        if current_str in setting_name_list:
            # キーが存在した場合はダイアログを表示
            ret = QMessageBox.warning(self, "注意", "対象の設定値「 " + current_str + "」 を削除します。よろしいですか？", QMessageBox.Ok, QMessageBox.Cancel)

            if ret == QMessageBox.Ok:
                # OKなら対象の設定値を削除して上書き保存
                setting_data.pop(current_str)
                self.save_json_file(self.json_path, setting_data)
                # リストを再取得
                self.combobox.setCurrentText("")
                self.set_setting_list()
                QMessageBox.information(self, "正常終了", "対象の設定値「 " + current_str + "」 を削除しました。")
        else:
            # キーが存在しない場合は警告
            QMessageBox.warning(self, "注意", "対象の設定値「 " + current_str + "」 が存在しないため削除できませんでした。")


    def create_spinbox(self, low, high, value):
        """ スピンボックスを作成する関数

            Args:
                low (int)  : 最小値
                high (int) : 最大値
                value (int): 値

            Returns:
                作成したQSpinBoxオブジェクト (QSpinBox): QSpinBox
        """
        sp = QSpinBox()
        sp.setRange(low, high)
        sp.setValue(value)
        return sp


    def create_label(self, name, bold_flg, alignment=None):
        """ ラベルを作成する関数

            Args:
                bold_flg (bool): 太文字にするかのフラグ
                alignment (AlignmentFlag): 文字位置の設定

            Returns:
                作成したQLabelオブジェクト (QLabel): QLabel
        """
        label = QLabel(name)

        if not alignment is None:
            label.setAlignment(alignment)

        if bold_flg:
            label.setStyleSheet("font-weight:bold;")

        return label


    def outline_low_change(self):
        """ 輪郭線の下限が変更された時の関数
        """
        low_value  = self.outline_low_sp.value()
        high_value = self.outline_high_sp.value()

        if low_value >= high_value:
            self.outline_low_sp.setValue(low_value - 1)


    def outline_high_change(self):
        """ 輪郭線の上限が変更された時の関数
        """
        low_value  = self.outline_low_sp.value()
        high_value = self.outline_high_sp.value()

        if high_value <= low_value:
            self.outline_high_sp.setValue(high_value + 1)


    def contrast_low_change(self):
        """ コントラストの下限が変更された時の関数
        """
        low_value  = self.contrast_low_sp.value()
        high_value = self.contrast_high_sp.value()

        if low_value >= high_value:
            self.contrast_low_sp.setValue(low_value - 1)


    def contrast_high_change(self):
        """ コントラストの上限が変更された時の関数
        """
        low_value  = self.contrast_low_sp.value()
        high_value = self.contrast_high_sp.value()

        if high_value <= low_value:
            self.contrast_high_sp.setValue(high_value + 1)


    def img_dialog(self):
        """ 画像選択ダイアログを表示する関数
        """
        file_open_flg = self.filedialog_clicked(self.img_path, "画像ファイル選択", "Images (*.png *.bmp *.jpg)")

        if (file_open_flg):
            # OpenCVだとパスに日本語が入っているとダメなのでnumpyで開く
            img_org = np.array(Image.open(self.img_path.text()))
            # RGBに変換する
            cv2_img = cv2.cvtColor(img_org, cv2.COLOR_BGR2RGB)
            # 読み込んだオリジナル画像をクラス変数に代入
            self.img_org = copy.deepcopy(cv2_img)
            # プレビューに表示できる形式にして表示
            img = self.line_extraction.get_qpixmap(cv2_img, self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT)
            self.img_label.setPixmap(img)


    def filedialog_clicked(self, line_edit, title, filter):
        """ ファイル選択ダイアログを表示させる関数

            Args:
                line_edit (QLineEdit): jsonファイルパス
                title (str) : ダイアログタイトル
                filter (str): jsonファイルパス

            Returns:
                True/False (bool): ファイルが選択されたかどうか
        """
        fileObj = QFileDialog.getOpenFileName(self, title, self.my_dir_path, filter)
        filepath = fileObj[0]

        if (filepath is not None) and (filepath != ""):
            # ファイルが選択されていればそのパスを設定
            line_edit.setText("")
            line_edit.setText(filepath)
            self.pre_btn.setEnabled(True)   # プレビューボタンは活性
            self.save_btn.setEnabled(False) # 保存ボタンは非活性
            return True
        else:
            return False


    def img_preview(self):
        """ プレビューを実行する関数
        """
        self.img = copy.deepcopy(self.img_org)
        # 画像を変換
        self.line_extraction.set_image_setting(self.img, self.create_setting_data())
        self.img = self.line_extraction.line_extraction()
        # プレビューに表示できる形式にして表示
        img = self.line_extraction.get_qpixmap(self.img, self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT)
        self.img_label.setPixmap(img)
        # プレビューを実行したら保存ボタンを活性化
        self.save_btn.setEnabled(True)


    def create_setting_data(self):
        """ 変換用設定値のオブジェクトを作成する関数

            Returns:
                setting_data (SettingData): 変換用設定値オブジェクト
        """
        setting_data = SettingData()
        setting_data.set_outline_range(self.outline_low_sp.value(), self.outline_high_sp.value())
        setting_data.set_outline_rough_blur(self.outline_rough_sp.value(), self.outline_blur_sp.value())
        setting_data.set_img_blur_blur(self.blur_sp.value())
        setting_data.set_contrast_range(self.contrast_low_sp.value(), self.contrast_high_sp.value())

        # チェックボックスの設定
        line_flg = False
        shadow_flg = False
        if self.line_checkbox.checkState() == Qt.CheckState.Checked:
            line_flg = True

        if self.shadow_checkbox.checkState() == Qt.CheckState.Checked:
            shadow_flg = True

        setting_data.set_checkbox_line_shadow(line_flg, shadow_flg)

        return setting_data


    def load_json_file(self, json_path):
        """ jsonファイルを辞書型で読み込む関数

            Args:
                json_path (str): jsonファイルパス

            Returns:
                json_data (dict): jsonファイルの辞書
        """
        json_data = None

        # ファイルのエンコードを設定
        encording_str = "utf-8"
        if sys.platform.startswith('win'):
            encording_str = "utf-8_sig"

        # jsonファイルを辞書として読み込み
        if os.path.exists(json_path):
            with open(json_path, "r", encoding=encording_str) as f:
                json_data = json.load(f)

        return json_data


    def save_json_file(self, json_path, json_data):
        """ jsonファイルに書き込む関数
    
            Args:
                json_path (str) : jsonファイルパス
                json_data (dict): jsonの辞書
        """
        # utf-8で書き込み
        with open(json_path, 'w', encoding='utf-8') as f:
            # インデントをつけてアスキー文字列ではない形で保存
            json.dump(json_data, f, indent=4, ensure_ascii=False)


    def save_img_dialog(self):
        """ 画像保存ダイアログを表示させて画像を保存する関数
        """
        file_path, _ = QFileDialog.getSaveFileName(self, "画像保存", self.my_dir_path + self.SAVE_FILE_DEFAULT, "PNG形式 (*.png)")

        if file_path != "":
            pil_img = Image.fromarray(cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB))
            pil_img.save(file_path)
            QMessageBox.information(self, "正常終了", file_path + " に画像を保存しました。")


    def batch_dialog(self):
        """ 一括処理ダイアログを表示させる関数
        """
        # フォームを表示
        self.batch_form.set_setting_data(self.create_setting_data())
        self.batch_form.set_close_fnc(self.set_gui_enabled, self.pre_btn.isEnabled(), self.save_btn.isEnabled())
        self.set_gui_enabled(False, False, False)
        self.batch_form.show()


    def set_gui_enabled(self, flg, pre_flg, save_flg):
        """ GUIの有効/無効を設定する関数

            Args:
                flg (bool): True/有効化、False/無効化
                pre_flg  (bool): プレビューボタンのTrue/有効化、False/無効化
                save_flg (bool): 保存ボタンのTrue/有効化、False/無効化
        """
        self.file_select_button.setEnabled(flg)
        self.combobox.setEnabled(flg)
        self.setting_save_button.setEnabled(flg)
        self.setting_delete_button.setEnabled(flg)

        self.outline_low_sp.setEnabled(flg)
        self.outline_high_sp.setEnabled(flg)
        self.outline_rough_sp.setEnabled(flg)
        self.outline_blur_sp.setEnabled(flg)
        self.blur_sp.setEnabled(flg)
        self.contrast_low_sp.setEnabled(flg)
        self.contrast_high_sp.setEnabled(flg)
        self.line_checkbox.setEnabled(flg)
        self.shadow_checkbox.setEnabled(flg)

        self.pre_btn.setEnabled(pre_flg)
        self.save_btn.setEnabled(save_flg)
        self.batch_btn.setEnabled(flg)
