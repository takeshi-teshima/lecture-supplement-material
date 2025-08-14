# Google TTS音声合成システム

このシステムは、XMLスクリプトファイルからGoogle Cloud Text-to-Speech APIを使用して音声合成を行い、結合版音声ファイルも作成できるツールです。

## ディレクトリ構造

```
Video/Introduction-to-AI_v1/
├── 1_Scripts/                 # XMLスクリプトファイル
│   └── *.xml                 # 音声合成対象のスクリプト
├── 2_GoogleTTS_Queries/      # 生成されたGoogle TTSクエリ
│   └── [XMLファイル名]/      # XMLファイルごとのディレクトリ
│       └── [段落ID]_[ハッシュ].json   # 段落ごとのクエリファイル
├── 3_GoogleTTS_Audio/        # 生成された音声ファイル
│   └── [XMLファイル名]/      # XMLファイルごとのディレクトリ
│       └── [段落ID]_[ハッシュ].wav    # 段落ごとの音声ファイル
├── 4_GoogleTTS_Combined/     # 結合された音声ファイル
│   └── [XMLファイル名]_[ハッシュ].wav # ファイルごとの結合音声
├── config.yaml               # システム設定ファイル
├── googletts_processor.py    # メイン処理スクリプト
├── test_googletts.py         # システムテストスクリプト
├── run_googletts.sh          # 実行用シェルスクリプト
├── requirements.txt          # Python依存関係
└── README.md                 # このファイル
```

## 主な機能

### 1. 音声合成 (synthesize)
- XMLスクリプトファイルから段落ごとの音声を生成
- ファイル指定による部分処理
- 段落ID指定による再生成
- ハッシュベースの重複処理スキップ

### 2. 音声結合 (combine)
- 段落ごとの音声を一つのファイルに結合
- XMLのスライド遷移情報に基づくページめくりポーズ
- 設定可能なポーズ時間
- ハッシュベースの重複処理スキップ

## 前提条件

### 1. Google Cloud設定

1. **Google Cloudプロジェクトの作成**
   - [Google Cloud Console](https://console.cloud.google.com/)にアクセス
   - 新しいプロジェクトを作成するか、既存のプロジェクトを選択

2. **Text-to-Speech APIの有効化**
   ```bash
   # Google Cloud CLIを使用する場合
   gcloud services enable texttospeech.googleapis.com
   ```
   または、Google Cloud Consoleの「APIとサービス」→「ライブラリ」から「Cloud Text-to-Speech API」を検索して有効化

3. **サービスアカウントキーの作成**
   - Google Cloud Console → 「IAMと管理」→「サービスアカウント」
   - 新しいサービスアカウントを作成
   - 「Text-to-Speech API User」ロールを付与
   - キーを作成してJSONファイルをダウンロード

4. **認証情報の設定**
   ```bash
   # 環境変数でキーファイルのパスを指定
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   ```

### 2. Pythonの準備

- **Python 3.8以上**が必要です
- 依存関係のインストール:
  ```bash
  pip install -r requirements.txt
  ```

### 3. 必要な依存関係

```txt
google-cloud-texttospeech>=2.14.0
click>=8.0.0
pydub>=0.25.0
requests>=2.28.0
PyYAML>=6.0
```

## 設定ファイル (config.yaml)

システムの動作を制御する設定ファイルです：

```yaml
# Google Cloud Text-to-Speech設定
google_tts:
  language_code: "ja-JP"                    # 言語コード
  voice_name: "ja-JP-Standard-D"           # 音声名
  speaking_rate: 1.2                       # 話速 (0.25-4.0)
  pitch: 0.0                               # 音高 (-20.0-20.0)
  volume_gain_db: 0.0                      # 音量 (-96.0-16.0)
  audio_encoding: "LINEAR16"               # 音声エンコーディング

# 処理設定
processing:
  scripts_dir: "../1_Scripts"              # XMLスクリプトディレクトリ
  queries_dir: "2_GoogleTTS_Queries"      # クエリ出力ディレクトリ
  audio_dir: "3_GoogleTTS_Audio"          # 音声出力ディレクトリ
  combined_dir: "4_GoogleTTS_Combined"    # 結合音声出力ディレクトリ
  audio_format: "wav"                      # 音声ファイル形式
  pause_duration_multiplier: 1.0          # ポーズ時間倍率
  page_turn_pause: 1.5                    # ページめくりポーズ（秒）
  paragraph_pause: 0.5                    # パラグラフ間ポーズ（秒）
  max_concurrent_requests: 3              # 同時リクエスト数
  retry_count: 3                           # リトライ回数
  retry_delay: 1.0                         # リトライ間隔（秒）

# ログ設定
logging:
  level: "INFO"                            # ログレベル
  format: "%(asctime)s - %(levelname)s - %(message)s"
```

### 利用可能な音声

Google TTS では多くの音声が利用できます：

#### 標準音声 (Standard)
- `ja-JP-Standard-A`: 女性の声
- `ja-JP-Standard-B`: 男性の声
- `ja-JP-Standard-C`: 男性の声
- `ja-JP-Standard-D`: 女性の声

#### ニューラル音声 (Neural2) - より自然な音声
- `ja-JP-Neural2-B`: 女性の声
- `ja-JP-Neural2-C`: 男性の声
- `ja-JP-Neural2-D`: 男性の声

## 使用方法

このツールは複数のコマンドを提供します。`python googletts_processor.py [コマンド] [オプション]` の形式で実行します。

### 1. 音声合成 (synthesize)

XMLスクリプトから段落ごとの音声ファイルを生成します。

```bash
# 全XMLファイルを処理
python googletts_processor.py synthesize

# 特定のXMLファイルのみ処理（部分一致）
python googletts_processor.py synthesize --files "00-01" --files "01-02"

# 特定の段落IDのみ処理
python googletts_processor.py synthesize --paragraph-ids "00-01-001" --paragraph-ids "00-01-002"

# ファイル指定と段落指定の組み合わせ
python googletts_processor.py synthesize --files "00-01" --paragraph-ids "00-01-001"

# 詳細ログ付きで実行
python googletts_processor.py --verbose synthesize
```

### 2. 音声結合 (combine)

段落ごとの音声ファイルを一つの結合音声ファイルにまとめます。

```bash
# 特定のXMLファイルの音声を結合
python googletts_processor.py combine "00-01_講義の全体像.xml"

# ページめくりポーズをカスタマイズ
python googletts_processor.py combine "00-01_講義の全体像.xml" --page-turn-pause 2.0

# パラグラフ間ポーズもカスタマイズ
python googletts_processor.py combine "00-01_講義の全体像.xml" --page-turn-pause 2.0 --paragraph-pause 0.3

# 全XMLファイルの音声を結合
python googletts_processor.py combine-all

# 全結合をカスタムポーズで実行
python googletts_processor.py combine-all --page-turn-pause 2.0 --paragraph-pause 0.3
```

### 3. 共通オプション

```bash
# カスタム設定ファイルを使用
python googletts_processor.py --config custom_config.yaml synthesize

# 詳細ログを出力
python googletts_processor.py --verbose combine "00-01_講義の全体像.xml"

# ヘルプを表示
python googletts_processor.py --help
python googletts_processor.py synthesize --help
python googletts_processor.py combine --help
```

### 4. 従来のシェルスクリプトとの互換性

既存のrun_googletts.shスクリプトも引き続き使用できます：

```bash
# シェルスクリプトを使用（音声合成のみ）
./run_googletts.sh

# 特定の段落を再生成
./run_googletts.sh 00-01-001 00-01-002
```

### XMLスクリプトファイルの形式

XMLファイルは以下の形式で記述します：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manuscript>
  <paragraph id="00-01-001">
    これは最初の段落です。
    <pause duration="1"/>
    1秒のポーズが入ります。
  </paragraph>

  <slide_transition slide_number="1" slide_title="スライドタイトル" />

  <paragraph id="00-01-002">
    これは2番目の段落です。
    <pause duration="2"/>
    2秒のポーズが入ります。
  </paragraph>
</manuscript>
```

### 出力ファイル

実行すると以下のファイルが生成されます：

1. **クエリファイル** (`2_GoogleTTS_Queries/[XMLファイル名]/[段落ID]_[ハッシュ].json`)
   ```json
   {
     "id": "00-01-001",
     "text": "これは最初の段落です。、1秒のポーズが入ります。",
     "params": {
       "language_code": "ja-JP",
       "voice_name": "ja-JP-Standard-D",
       "speaking_rate": 1.2,
       "pitch": 0.0
     },
     "hash": "a1b2c3d4e5f67890"
   }
   ```

2. **音声ファイル** (`3_GoogleTTS_Audio/[XMLファイル名]/[段落ID]_[ハッシュ].wav`)
   - WAV形式の音声ファイル
   - 段落ごとに個別のファイルとして生成

## テスト

システムの動作確認には以下のテストスクリプトを使用します：

```bash
# テストの実行
python test_googletts.py
```

テストでは以下の項目を確認します：
- Google TTS API接続テスト
- XMLパース機能テスト
- テキスト抽出機能テスト
- 音声合成リクエスト生成テスト
- ハッシュ生成テスト

## トラブルシューティング

### よくある問題と解決方法

1. **認証エラー**
   ```
   エラー: Google TTS APIに接続できません
   ```
   - `GOOGLE_APPLICATION_CREDENTIALS` 環境変数が正しく設定されているか確認
   - サービスアカウントキーファイルが存在するか確認
   - APIが有効化されているか確認

2. **API制限エラー**
   ```
   エラー: Quota exceeded
   ```
   - `config.yaml` の `max_concurrent_requests` を小さくする
   - しばらく時間を置いてから再実行

3. **音声ファイルが生成されない**
   - 出力ディレクトリの書き込み権限を確認
   - XMLファイルの形式が正しいか確認
   - ログを確認してエラーメッセージを調べる

4. **XMLパースエラー**
   ```
   エラー: XMLパースエラー
   ```
   - XMLファイルが正しい形式で記述されているか確認
   - 文字エンコーディングがUTF-8になっているか確認

### ログレベルの変更

詳細なデバッグ情報が必要な場合：

```yaml
logging:
  level: "DEBUG"  # INFOからDEBUGに変更
```

### パフォーマンス調整

- **同時リクエスト数の調整**: `max_concurrent_requests` を調整
- **リトライ設定**: `retry_count` と `retry_delay` を調整
- **音声パラメータ**: `speaking_rate` や `pitch` で生成速度を調整

## 費用について

Google Cloud Text-to-Speech APIは使用量に応じて課金されます：

- **標準音声**: 100万文字あたり $4.00
- **ニューラル音声**: 100万文字あたり $16.00
- **月間100万文字まで無料**（初回利用時）

詳細は[Google Cloud価格表](https://cloud.google.com/text-to-speech/pricing)を参照してください。

## ライセンス

このツールはMITライセンスの下で公開されています。
Google Cloud Text-to-Speech APIの利用規約に従って使用してください。
