module Jekyll
  module BibFileFilters
    require 'pathname'

    def list_bib_files(dir)
      base_dir = Jekyll.sites.first.source # Jekyllプロジェクトのルートディレクトリ
      target_dir = File.join(base_dir, dir)

      # 指定されたディレクトリ内の .bib ファイルを取得
      if Dir.exist?(target_dir)
        bib_files = Dir.glob(File.join(target_dir, "*.bib")).map { |f| Pathname.new(f).basename.to_s }
        bib_files.sort # ファイル名をソート
      else
        ["Error: Directory '#{dir}' not found."]
      end
    end
  end
end

Liquid::Template.register_filter(Jekyll::BibFileFilters)
