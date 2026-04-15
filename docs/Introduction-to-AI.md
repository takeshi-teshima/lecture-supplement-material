---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: default
---

## 講義資料
[講義スライドはこちら](https://drive.google.com/drive/folders/14c9Yo92NUFiGhvebipgSILCKv8jpgBbe?usp=sharing)（閲覧のみ）

（過去の講義スライドはこちら：[2025年度](https://drive.google.com/drive/folders/1IINO87Q0_xwAfteCHvRdfK4wl-z4uCzt?usp=drive_link)）

{% if false %}
このページで公開するソースコードのライセンスは[こちら](https://github.com/takeshi-teshima/lecture-supplement-material/blob/features/initial-version/LICENSE)です．
{% endif %}

## ソースコード一覧

{% assign files = "../Introduction-to-AI/" | list_files: "*.ipynb" | newline_to_br | split: "<br>" | sort %}

|説明|ファイル|Colab|
|---|---|---|
{% for path in files -%}
{% if path | endswith: '.ipynb' -%}
{% assign filename = path | split: "/" | last -%}
{% assign stem = filename | remove: ".ipynb" -%}
{% capture file_url -%}https://github.com/takeshi-teshima/lecture-supplement-material/blob/features/initial-version/Introduction-to-AI/{{ filename }}{%- endcapture -%}
{% capture colab_url -%}https://colab.research.google.com/github/takeshi-teshima/lecture-supplement-material/blob/features/initial-version/Introduction-to-AI/{{ filename }}{%- endcapture -%}
||{{ filename }}|[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)]({{ colab_url }})|
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

{% if false %}
## Rubric

<table>
  {% for row in site.data.Introduction_to_AI_rubric %}
    {% if forloop.first %}
    <tr>
      {% for pair in row %}
        <th>{{ pair[0] }}</th>
      {% endfor %}
    </tr>
    {% endif %}

    {% tablerow pair in row %}
      {{ pair[1] }}
    {% endtablerow %}
  {% endfor %}
</table>
{% endif %}
