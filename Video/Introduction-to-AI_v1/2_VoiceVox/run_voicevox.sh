#!/bin/bash

# VOICEVOX音声合成システム - 実行スクリプト

set -e  # エラー時に終了

echo "=== VOICEVOX音声合成システム ==="
echo ""

# 現在のディレクトリを確認
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "作業ディレクトリ: $SCRIPT_DIR"
echo ""

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

# 依存関係の確認
echo "依存関係の確認..."
if [ -f "requirements.txt" ]; then
    echo "必要なパッケージをインストール中..."
    $PYTHON_CMD -m pip install -r requirements.txt --quiet
    echo "依存関係のインストール完了"
else
    echo "警告: requirements.txt が見つかりません"
fi
echo ""

# VOICEVOXの接続確認
echo "VOICEVOX接続確認..."
if curl -s http://localhost:50021/version > /dev/null 2>&1; then
    echo "✓ VOICEVOXサーバーに接続できました"
    VOICEVOX_VERSION=$(curl -s http://localhost:50021/version | python3 -c "import sys, json; print(json.load(sys.stdin)['version'])" 2>/dev/null || echo "不明")
    echo "  バージョン: $VOICEVOX_VERSION"
else
    echo "✗ VOICEVOXサーバーに接続できません"
    echo ""
    echo "VOICEVOXを起動してください："
    echo "1. VOICEVOXアプリケーションを起動"
    echo "2. APIサーバーが http://localhost:50021 で起動するまで待機"
    echo "3. このスクリプトを再実行"
    echo ""
    exit 1
fi
echo ""

# 設定ファイルの確認
echo "設定ファイルの確認..."
if [ -f "config.yaml" ]; then
    echo "✓ config.yaml が見つかりました"
else
    echo "✗ config.yaml が見つかりません"
    echo "config.yaml ファイルを確認してください"
    exit 1
fi
echo ""

# スクリプトディレクトリの確認
echo "スクリプトディレクトリの確認..."
if [ -d "1_Scripts" ]; then
    XML_COUNT=$(find 1_Scripts -name "*.xml" | wc -l)
    echo "✓ 1_Scripts ディレクトリが見つかりました"
    echo "  XMLファイル数: $XML_COUNT"

    if [ $XML_COUNT -eq 0 ]; then
        echo "警告: XMLファイルが見つかりません"
        echo "1_Scripts/ ディレクトリにXMLファイルを配置してください"
    fi
else
    echo "✗ 1_Scripts ディレクトリが見つかりません"
    mkdir -p 1_Scripts
    echo "1_Scripts ディレクトリを作成しました"
    echo "XMLファイルを配置してから再実行してください"
    exit 1
fi
echo ""

# 出力ディレクトリの準備
echo "出力ディレクトリの準備..."
mkdir -p 2_VoiceVox_Queries
mkdir -p 3_VoiceVox_Audio
echo "✓ 出力ディレクトリを準備しました"
echo ""

# メイン処理の実行
echo "=== 音声合成処理開始 ==="
echo ""

if [ $XML_COUNT -gt 0 ]; then
    $PYTHON_CMD voicevox_processor.py
    echo ""
    echo "=== 処理完了 ==="
    echo ""
    echo "結果の確認:"
    echo "- クエリファイル: 2_VoiceVox_Queries/"
    echo "- 音声ファイル: 3_VoiceVox_Audio/"
else
    echo "処理対象のXMLファイルがありません"
    echo "1_Scripts/ ディレクトリにXMLファイルを配置してください"
fi
