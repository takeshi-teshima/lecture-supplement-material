# lecture-supplement-material

[![Netlify Status](https://api.netlify.com/api/v1/badges/42b552d9-93bf-41c3-8761-149e7d653678/deploy-status)](https://app.netlify.com/sites/takeshi-teshima-lecture-supplement/deploys)

## Building docs

1. Install [asdf](https://asdf-vm.com/ja-jp/guide/getting-started.html).
1. [Add Ruby plugin](https://github.com/asdf-vm/asdf-ruby) (if not done already)
   `asdf plugin add ruby https://github.com/asdf-vm/asdf-ruby.git`
1. Install latest Ruby:
   `asdf install ruby latest`
1. Set local Ruby version:
   `asdf local ruby latest`
1. `bundle exec jekyll serve`
