# 🚩 タスク
Google ColabもしくはJupyter notebookで実行可能なコードを生成してください．

## ✅ コードの形式と環境

- **コード形式：**
  - Google ColabまたはJupyter Notebookで直接実行可能な形式であること。
  - 改善依頼時は、特に指示がない限り、常に **self-containedなコード全体** を示す。

- **インストールコマンドの扱い：**
  - pip install コマンドは、コード中には含めずに、別途明記する。
  - コマンドは、標準的なGoogle Colab等の環境に対して追加で必要なもののみを示すこと。

## ✅ コードの挙動・再現性に関する指定

- **乱数制御：**
  - randomnessは完全に固定し（例：np.random.seed(0)、torch.manual_seed(0)等）、コードを冪等にすること。

- **プロット表示方法：**
  - 結果のファイルへの保存は不要。`plt.show()`などで出力を表示するだけにする。
  - 各プロットはすべて個別のfigureとして生成し、subfigure化（subplot）を行わない。

## ✅ クラス分類問題におけるプロット指定

- **クラス記号指定 (2クラスの場合)：**
  - クラス0: crosses（×）
  - クラス1: circles（○）

- **クラス色指定 (2クラスの場合)：**
  - クラス0: blue
  - クラス1: dark orange

- **背景色：**
  - データのみのプロット時は背景を白に設定する。

- **軸範囲（xlim, ylim）：**
  - 同一パターンの異なるパラメータ比較時には、軸の範囲を共通化する。

## ✅ 損失曲線とDecision Boundaryに関する色・スタイル指定

- **曲線の色と線幅：**
  - training loss curve：blue
  - validation loss curve：purple
  - test loss curve：green
  - decision boundary：orange
  - これらの線幅は原則として3以上、必要に応じて5に設定する。データ点の線幅は原則として1で設定する．

## ✅ PyTorch利用時のフレームワーク指定

- PyTorchを利用する場合は、必ず **torch lightning** を利用すること。

## ✅ コードの構造と抽象化に関する指示

- コードは、抽象的に理解しやすい綺麗なコードに仕上げる。
- 必要に応じて、抽象化のためにクラスを定義して構造化することを推奨する。

## ✅ 色のパレット利用に関する指示

- **コード冒頭に以下のパレットを定義して、コード中ではこのパレットを名前で呼び出すこと。**

```python
# -----------------------------------------
# Original Color Palette
# -----------------------------------------
color_palette = {
    "white": "#FFFFFF",
    "light_gray": "#D3D3D3",
    "gray": "#808080",
    "black": "#000000",
    "green": "#008000",
    "blue": "#0000FF",
    "light_blue": "#ADD8E6",
    "light_light_blue": "#E0FFFF",
    "yellow": "#FFFF00",
    "orange": "#FFA500",
    "dark_orange": "#FF8C00",
    "purple": "#800080",
}

# -----------------------------------------
# Class Colors (5 Classes)
# -----------------------------------------
# We will use these both for data points AND region coloring
class_colors = [
    color_palette["dark_orange"],  # Class 0
    color_palette["blue"],         # Class 1
    color_palette["green"],        # Class 2
    color_palette["purple"],       # Class 3
    color_palette["yellow"]        # Class 4
]
```

## ✅ 提供した可視化コードを参考とする際の注意点

- 元の可視化コード（Logistic回帰・Polynomial Featuresを用いたデモ）は、上記の指定に沿った色指定やスタイルに従って書き換えて利用すること。
- Logistic回帰や決定境界のプロットは示したコードをベースに適宜カスタマイズして使ってよい。
