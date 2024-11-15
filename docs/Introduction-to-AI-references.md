---
layout: default
---

{% assign files = "../Introduction-to-AI/Bibliography/" | list_files: "*.bib" | newline_to_br | split: "<br>" | sort %}

<table>
<tbody>
{% for path in files -%}
{% if path | endswith: '.bib' -%}
{% assign filename = path | split: "/" | last -%}
{% assign stem = filename | remove: ".ipynb" -%}
{% assign components = stem | split: "-" %}
{% assign last_index = components | size | minus: 1 %}
<tr>
{% for component in components %}{# comment #}
{% if forloop.index0 == last_index %}
{% if 2 - forloop.index0 > 0 %}
{% endif %}
<td>{{ component }}</td>
{% else %}
<td>{{ component }}</td>
{% endif %}
{% endfor %}
</tr>
{% endif -%}
{%- endfor %}
</tbody>
</table>
