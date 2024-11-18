---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: default
---

このページで公開する資料のライセンスは[こちら](https://github.com/takeshi-teshima/lecture-supplement-material/blob/features/initial-version/LICENSE)です．

## ソースコード一覧

{% assign files = "../Introduction-to-AI/" | list_files: "*.ipynb" | newline_to_br | split: "<br>" | sort %}

|講義回|説明|ファイル|Colab|
|---|---|---|---|
{% for path in files -%}
{% if path | endswith: '.ipynb' -%}
{% assign filename = path | split: "/" | last -%}
{% assign stem = filename | remove: ".ipynb" -%}
{% capture file_url -%}https://github.com/takeshi-teshima/lecture-supplement-material/blob/features/initial-version/Introduction-to-AI/{{ filename }}{%- endcapture -%}
{% capture colab_url -%}https://colab.research.google.com/github/takeshi-teshima/lecture-supplement-material/blob/features/initial-version/Introduction-to-AI/{{ filename }}{%- endcapture -%}
|||[{{ filename }}]({{ file_url }})|[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)]({{ colab_url }})|
{% endif -%}
{%- endfor %}

## 参考文献一覧

※全てを片っ端から読もうとすることはお勧めしません（教科書的な文献を除く）。知りたい事柄に応じて必要な箇所を読みましょう。

{% assign files = "_bibliography/Introduction-to-AI" | list_files: "*.bib" | newline_to_br | split: "<br>" | sort %}

{% for path in files -%}
{% if path | endswith: '.bib' -%}
{% assign filename = path | split: "/" | last -%}
{% assign stem = filename | remove: ".ipynb" -%}
### {{stem | replace: '提供参考文献-', '' | replace: '.bib', ''}} <small>([.bib](https://github.com/takeshi-teshima/lecture-supplement-material/blob/features/initial-version/docs/{{path}}))</small>
{% bibliography --file ../{{path}} %}
{% endif -%}
{%- endfor %}
