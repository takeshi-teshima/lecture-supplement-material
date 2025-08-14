# VOICEVOX音声合成システム

このシステムは、XMLスクリプトファイルからVOICEVOXを使用して音声合成を行うツールです。

## ディレクトリ構造

```
Video/Introduction-to-AI_v1/
├── 1_Scripts/                 # XMLスクリプトファイル
│   └── *.xml                 # 音声合成対象のスクリプト
├── 2_VoiceVox_Queries/       # 生成されたVOICEVOXクエリ
│   └── [XMLファイル名]/      # XMLファイルごとのディレクトリ
│       └── [段落ID].json     # 段落ごとのクエリファイル
├── 3_VoiceVox_Audio/         # 生成された音声ファイル
│   └── [XMLファイル名]/      # XMLファイルごとのディレクトリ
│       └── [段落ID].wav      # 段落ごとの音声ファイル
├── config.yaml               # システム設定ファイル
├── voicevox_processor.py     # メイン処理スクリプト
├── test_voicevox.py          # システムテストスクリプト
├── run_voicevox.sh           # 実行用シェルスクリプト
├── requirements.txt          # Python依存関係
└── README.md                 # このファイル
```

## 前提条件

### 1. VOICEVOXの準備

1. **VOICEVOXのダウンロードとインストール**
   - [VOICEVOX公式サイト](https://voicevox.hiroshiba.jp/)からダウンロード
   - お使いのOSに適したバージョンをインストール

2. **VOICEVOXの起動**
   ```bash
   # アプリケーションを起動するか、コマンドラインから：
   # Windowsの場合
   ./VOICEVOX.exe

   # macOSの場合
   open -a VOICEVOX

   # Linuxの場合
   ./VOICEVOX.AppImage
   ```

3. **APIサーバーの確認**
   - VOICEVOXが起動すると、デフォルトで `http://localhost:50021` でAPIサーバーが開始されます
   - ブラウザで `http://localhost:50021/docs` にアクセスしてAPIドキュメントを確認できます

### 2. Pythonの準備

**mise（旧rtx）によるPython環境管理を推奨**

1. miseのインストール（macOSの場合）
   ```bash
   brew install mise
   ```
   他OSは公式手順参照：[mise公式サイト](https://mise.jdx.dev/)

2. プロジェクトディレクトリでPython環境をセットアップ
   ```bash
   mise use python@3.11
   mise install
   # requirements.txtの内容が自動でインストールされます
   ```

3. mise仮想環境を有効化
   ```bash
   mise shell
   # 以降のコマンドは仮想環境内で実行されます
   ```

## 設定

### config.yamlの編集

システムの設定は `config.yaml` ファイルで管理されます。

#### サーバー接続設定
```yaml
voicevox:
  host: "localhost"      # VOICEVOXのホスト
  port: 50021            # VOICEVOXのポート
```

#### 音声生成パラメータ（生成結果に影響）
```yaml
voicevox_params:
  speaker_id: 3         # 話者ID（声の種類）
  speed_scale: 1.2      # 話速（0.5-2.0）
  pitch_scale: 0.15     # 音高（-0.15-0.15）
  intonation_scale: 1.33 # 抑揚（0.0-2.0）
  volume_scale: 1.0     # 音量（0.0-2.0）
```

`voicevox_params` の内容が同じであれば、同じテキストは同じハッシュ名で保存され、無駄な再生成を防ぎます。

---

### 話者IDについて

VOICEVOXでは異なる声質を話者IDで指定します。主な話者ID：

- `0`: 四国めたん（ノーマル）
- `1`: 四国めたん（あまあま）
- `2`: 四国めたん（ツンツン）
- `3`: ずんだもん（ノーマル）
- `4`: ずんだもん（あまあま）
- `5`: ずんだもん（ツンツン）
- `8`: 春日部つむぎ（ノーマル）
- `10`: 雨晴はう（ノーマル）

利用可能な話者の完全なリストは、VOICEVOXのAPIドキュメント（`http://localhost:50021/docs`）で確認できます。

## XMLスクリプトの形式

システムで処理可能なXMLスクリプトの形式：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manuscript>
  <paragraph id="段落ID">
    テキスト内容
    <pause duration="1"/>
    続きのテキスト
  </paragraph>

  <slide_transition slide_number="1" slide_title="スライドタイトル" />

  <paragraph id="次の段落ID">
    次の段落のテキスト
  </paragraph>
</manuscript>
```

### 対応要素

- `<paragraph id="ID">`: 音声合成対象の段落（ID属性必須）
- `<pause duration="秒数"/>`: ポーズ（間を指定）
- `<slide_transition>`: スライド切り替え（処理対象外）

### ポーズの処理

- `duration="2.0"` 以上: 「。」に変換
- `duration="1.0"` 以上: 「、」に変換
- それ以下: 「、」に変換

## 使用方法

### 0. 動作確認（推奨）

システムを初めて使用する前に、動作確認テストを実行することを強く推奨します：

```bash
# 動作確認テストの実行
python test_voicevox.py
```

このテストでは以下を確認します：
- VOICEVOX サーバーへの接続
- 話者リストの取得
- 設定ファイルの正常性
- XMLパース機能
- 音声合成機能

### 1. 基本的な使用手順

1. **VOICEVOXを起動**
   ```bash
   # VOICEVOXアプリケーションを起動
   ```

2. **XMLスクリプトを配置**
   ```bash
   # 1_Scripts/ ディレクトリにXMLファイルを配置
   cp your_script.xml 1_Scripts/
   ```

3. **設定の確認・調整**
   ```bash
   # config.yaml を確認・編集
   nano config.yaml
   ```

4. **mise仮想環境を有効化**
   ```bash
   mise shell
   ```

5. **音声合成の実行**
   ```bash
   # シェルスクリプトを使用（推奨）
   ./run_voicevox.sh

   # または直接Pythonスクリプトを実行
   python voicevox_processor.py
   ```

   # 特定の段落IDだけ再生成したい場合（複数指定可）
   python voicevox_processor.py --paragraph-ids 00-01-001 00-01-002
   # 既存ファイル（同じテキスト・パラメータのハッシュ）はスキップされます

### 2. 実行例

```bash
# VOICEVOXの起動確認
curl http://localhost:50021/version

# mise仮想環境を有効化
mise shell

# 動作確認テスト（推奨）
python test_voicevox.py

# システムの実行（シェルスクリプト使用）
./run_voicevox.sh

# または直接実行
python voicevox_processor.py
```

### 3. 出力の確認

実行が完了すると：

- `2_VoiceVox_Queries/[XMLファイル名]/` に各段落のクエリファイル（JSON）が生成されます。
- `3_VoiceVox_Audio/[XMLファイル名]/` に各段落の音声ファイル（WAV）が生成されます。
- ファイル名は `段落ID_ハッシュ値` 形式となり、テキストとパラメータが同じ場合は同じファイル名になります。

## トラブルシューティング

### 1. 接続エラー

**エラー**: "VOICEVOX接続エラー"

**解決方法**:
- VOICEVOXが起動しているか確認
- ポート50021が使用されているか確認
- ファイアウォール設定を確認

```bash
# VOICEVOXの状態確認
curl http://localhost:50021/version
```

### 2. 音声合成エラー

**エラー**: "音声合成失敗"

**解決方法**:
- 話者IDが正しいか確認
- テキストが長すぎないか確認（適切な長さに分割）
- 特殊文字や記号が問題ないか確認

### 3. ファイル保存エラー

**エラー**: "ファイル保存エラー"

**解決方法**:
- ディスク容量を確認
- 書き込み権限を確認
- ファイルパスの長さを確認

### 4. XMLパースエラー

**エラー**: "XMLパースエラー"

**解決方法**:
- XMLファイルの構文を確認
- 文字エンコーディング（UTF-8）を確認
- 必須属性（paragraph要素のid）を確認

## 高度な使用方法

### 1. バッチ処理の設定

```yaml
processing:
  max_concurrent_requests: 5  # 同時処理数
  retry_count: 3              # リトライ回数
  retry_delay: 1.0            # リトライ間隔
```

### 2. ログレベルの調整

```yaml
logging:
  level: "DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

### 3. カスタム音声パラメータ

```yaml
voicevox:
  speed_scale: 1.2      # 少し早口
  pitch_scale: 0.05     # 少し高い声
  intonation_scale: 1.2 # 抑揚強め
```

## 開発者向け情報

### スクリプトの主要クラス

- `VoiceVoxProcessor`: メイン処理クラス
  - `parse_xml_script()`: XMLパース
  - `create_audio_query()`: クエリ生成
  - `synthesize_speech()`: 音声合成
  - `process_paragraph()`: 段落処理
  - `process_xml_file()`: ファイル処理

### APIエンドポイント

- `GET /version`: バージョン情報
- `POST /audio_query`: 音声クエリ生成
- `POST /synthesis`: 音声合成
- `GET /speakers`: 話者情報取得

### 拡張例

```python
# カスタム話者設定
processor = VoiceVoxProcessor("custom_config.yaml")

# 単一ファイル処理
results = processor.process_xml_file("specific_script.xml")

# カスタムパラメータでの処理
query = processor.create_audio_query("テスト音声", speaker_id=8)
```

## ライセンス

このスクリプトはMITライセンスの下で提供されます。VOICEVOXの使用については、[VOICEVOX利用規約](https://voicevox.hiroshiba.jp/)を確認してください。

## サポート

問題が発生した場合：

1. このREADMEのトラブルシューティングを確認
2. ログファイルを確認（DEBUG レベルで詳細ログ出力）
3. VOICEVOX公式ドキュメントを参照
4. 設定ファイルの内容を再確認
