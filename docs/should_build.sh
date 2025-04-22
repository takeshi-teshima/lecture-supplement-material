#!/bin/bash

echo "Checking for changes since last build ($CACHED_COMMIT_REF)..."

# --- 設定 ---
# Netlifyが監視するパス (必要に応じて調整)
# base, publish, functions ディレクトリや設定ファイルをリポジトリルートからの相対パスで指定
# 例: base = "site", publish = "site/dist", functions = "netlify/functions"
WATCH_PATHS="site site/dist netlify/functions netlify.toml ../Introduction-to-AI"
# -----------

# git diff を使って前回のビルド(CACHED_COMMIT_REF)から現在(HEAD)までの差分をチェック
# --quiet オプションは差分がなければ exit 0、あれば exit 1 を返す
# 指定したパスのいずれかに変更があれば git diff は exit 1 を返す
git diff --quiet $CACHED_COMMIT_REF HEAD -- $WATCH_PATHS

# git diff の終了コードを取得
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]
then
  # 差分がない場合 (git diff が exit 0)
  echo "No changes detected in monitored paths. Skipping build."
  exit 0 # Netlifyにビルドをスキップするよう指示 (exit 0)
else
  # 差分がある場合 (git diff が exit 1)
  echo "Changes detected in monitored paths. Proceeding with build."
  exit 1 # Netlifyにビルドを実行するよう指示 (exit 1)
fi
