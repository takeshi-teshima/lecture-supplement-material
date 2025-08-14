#!/bin/bash

# ---【引数のチェック】---
# スクリプトに渡された引数の数が2つでない場合は、使い方を表示して終了
if [ "$#" -ne 2 ]; then
  echo "❌ エラー: 引数の数が正しくありません。"
  echo ""
  echo "【使用方法】"
  echo "  $0 <入力PDFのパス> <タスクリストのパス>"
  echo ""
  echo "【例】"
  echo "  $0 my_document.pdf tasks.csv"
  exit 1
fi

# ---【設定】---
# 第1引数を入力PDFとして設定
INPUT_FILE="$1"
# 第2引数をタスクリストとして設定
TASK_LIST="$2"

# ファイルを出力するディレクトリ名（ここは固定）
OUTPUT_DIR="split_slides"
# ---【設定はここまで】---

# 出力ディレクトリがなければ作成
mkdir -p "$OUTPUT_DIR"

# 入力ファイルとタスクリストの存在をチェック
if [ ! -f "$INPUT_FILE" ]; then
  echo "❌ エラー: 入力ファイル '$INPUT_FILE' が見つかりません。"
  exit 1
fi
if [ ! -f "$TASK_LIST" ]; then
  echo "❌ エラー: タスクリスト '$TASK_LIST' が見つかりません。"
  exit 1
fi

echo "🚀 処理を開始します..."
echo "📄 入力PDF: $INPUT_FILE"
echo "📋 タスクリスト: $TASK_LIST"

# タスクリストを1行ずつ読み込んでループ処理
while IFS=',' read -r output_basename pages_to_extract; do
  # 空白行やコメント行(#で始まる行)をスキップ
  if [ -z "$output_basename" ] || [[ "$output_basename" =~ ^# ]]; then
    continue
  fi

  # 読み込んだベース名に拡張子「.pdf」を付けて、完全な出力パスを生成
  full_output_path="$OUTPUT_DIR/${output_basename}.pdf"

  echo "  [処理中] ページ '$pages_to_extract'  ->  $full_output_path"

    # pdftkコマンドで指定ページを抽出し、生成したファイル名で保存
    pdftk "$INPUT_FILE" cat $pages_to_extract output "$full_output_path"

done < "$TASK_LIST"

echo "✅ すべての処理が完了しました。"
