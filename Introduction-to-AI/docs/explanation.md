
# 初期セットアップ

```
$ poetry config virtualenvs.in-project true --local
```
により，ディレクトリ内の.venvに保存されるようにしてある．
これによって，ノートブック中の `!pip` によるライブラリインストールもローカルの仮想環境に入る．