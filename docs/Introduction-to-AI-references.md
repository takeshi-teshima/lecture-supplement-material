---
layout: default
---

{{"../Introduction-to-AI/Bibliography/" | list_bib_files}}
"../Introduction-to-AI/Bibliography/"

{% assign files = "../Introduction-to-AI/Bibliography/" | list_files: "*.bib" | newline_to_br | split: "<br>" | sort %}

{% for path in files -%}
{% if path | endswith: '.bib' -%}
{% assign filename = path | split: "/" | last -%}
{% assign stem = filename | remove: ".ipynb" -%}
## {{stem | replace: '提供参考文献-', '' | replace: '.bib', ''}}
{% bibliography --file ../{{path}} %}
{% endif -%}
{%- endfor %}
