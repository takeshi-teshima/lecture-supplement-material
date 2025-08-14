#!/bin/bash

# Google TTS音声合成システム - 実行スクリプト

set -e  # エラー時に終了

echo "=== Google TTS音声合成システム ==="
echo ""

# 現在のディレクトリを確認
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "作業ディレクトリ: $SCRIPT_DIR"
echo ""

# 使用方法を表示
show_usage() {
    echo "使用方法:"
    echo "  $0                           # 全XMLファイルを音声合成"
    echo "  $0 [段落ID...]              # 特定の段落IDのみ音声合成"
    echo "  $0 --combine [XMLファイル]   # 音声を結合（XMLファイル指定）"
    echo "  $0 --combine-all            # 全XMLファイルの音声を結合"
    echo ""
    echo "例:"
    echo "  $0                                    # 全て処理"
    echo "  $0 00-01-001 00-01-002               # 特定段落のみ"
    echo "  $0 --combine 00-01_講義の全体像.xml  # 特定ファイルの結合"
    echo "  $0 --combine-all                     # 全ファイル結合"
    echo ""
}

# Python環境の確認
echo "Python環境の確認..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "エラー: Pythonが見つかりません。Python 3.8以上をインストールしてください。"
    exit 1
fi

echo "使用するPythonコマンド: $PYTHON_CMD"
$PYTHON_CMD --version
echo ""

# 設定ファイルの確認
if [ ! -f "config.yaml" ]; then
    echo "エラー: config.yaml が見つかりません。"
    echo "config.yaml を作成してGoogle TTS設定を行ってください。"
    exit 1
fi

echo "設定ファイル: config.yaml ✓"
echo ""

# Google Cloud認証の確認
echo "Google Cloud認証の確認..."
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "警告: GOOGLE_APPLICATION_CREDENTIALS 環境変数が設定されていません。"
    echo ""
    echo "Google Cloud Text-to-Speech APIを使用するには、以下の設定が必要です:"
    echo "1. Google Cloud Consoleでプロジェクトを作成"
    echo "2. Text-to-Speech APIを有効化"
    echo "3. サービスアカウントキーを作成してダウンロード"
    echo "4. 環境変数を設定: export GOOGLE_APPLICATION_CREDENTIALS=\"/path/to/your/key.json\""
    echo ""
    read -p "認証設定を完了しましたか？続行しますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "処理を中止しました。"
        exit 1
    fi
else
    echo "認証ファイル: $GOOGLE_APPLICATION_CREDENTIALS ✓"
    if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "警告: 指定された認証ファイルが見つかりません。"
    fi
fi
echo ""

# 依存関係の確認とインストール
echo "依存関係の確認..."
if [ -f "requirements.txt" ]; then
    echo "requirements.txt が見つかりました。依存関係をインストールします..."
    $PYTHON_CMD -m pip install -r requirements.txt
    echo ""
else
    echo "警告: requirements.txt が見つかりません。"
fi

# スクリプトディレクトリの確認
SCRIPTS_DIR="../1_Scripts"
if [ ! -d "$SCRIPTS_DIR" ]; then
    echo "エラー: スクリプトディレクトリが見つかりません: $SCRIPTS_DIR"
    echo "XMLスクリプトファイルが格納されているディレクトリを確認してください。"
    exit 1
fi

echo "スクリプトディレクトリ: $SCRIPTS_DIR ✓"

# XMLファイルの確認
XML_COUNT=$(find "$SCRIPTS_DIR" -name "*.xml" | wc -l)
if [ "$XML_COUNT" -eq 0 ]; then
    echo "警告: XMLスクリプトファイルが見つかりません。"
    echo "処理対象のファイルがない可能性があります。"
else
    echo "XMLファイル数: $XML_COUNT 個"
fi
echo ""

# 引数の処理
if [ $# -eq 0 ]; then
    echo "Google TTS音声合成処理を開始します..."
    echo "すべてのXMLファイルを処理します。"
    echo ""
    $PYTHON_CMD googletts_processor.py synthesize
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
    exit 0
elif [ "$1" = "--combine" ]; then
    if [ $# -lt 2 ]; then
        echo "エラー: --combine オプションにはXMLファイル名が必要です。"
        show_usage
        exit 1
    fi
    echo "音声結合処理を開始します: $2"
    echo ""
    $PYTHON_CMD googletts_processor.py combine "$2"
elif [ "$1" = "--combine-all" ]; then
    echo "全XMLファイルの音声結合処理を開始します..."
    echo ""
    $PYTHON_CMD googletts_processor.py combine-all
else
    echo "指定された段落IDで処理します: $@"
    echo ""
    $PYTHON_CMD googletts_processor.py synthesize --paragraph-ids "$@"
fi

echo ""
echo "=== 処理完了 ==="
echo ""
echo "生成されたファイルの確認:"

# 出力ディレクトリの確認
QUERIES_DIR="2_GoogleTTS_Queries"
AUDIO_DIR="3_GoogleTTS_Audio"
COMBINED_DIR="4_GoogleTTS_Combined"

if [ -d "$QUERIES_DIR" ]; then
    QUERY_COUNT=$(find "$QUERIES_DIR" -name "*.json" | wc -l)
    echo "クエリファイル: $QUERY_COUNT 個 ($QUERIES_DIR)"
fi

if [ -d "$AUDIO_DIR" ]; then
    AUDIO_COUNT=$(find "$AUDIO_DIR" -name "*.wav" | wc -l)
    echo "音声ファイル: $AUDIO_COUNT 個 ($AUDIO_DIR)"
fi

if [ -d "$COMBINED_DIR" ]; then
    COMBINED_COUNT=$(find "$COMBINED_DIR" -name "*.wav" | wc -l)
    echo "結合音声ファイル: $COMBINED_COUNT 個 ($COMBINED_DIR)"
fi

echo ""
echo "処理が完了しました。"
