# jekyll-feed titles each feed with `site.title`, which al-folio sets to the
# literal string "blank" to mean "use the author's name". Substitute the name.
Jekyll::Hooks.register :pages, :post_render do |page|
  next unless page.output_ext == '.xml' && page.output&.include?('<title type="html">blank')

  config = page.site.config
  name = [config['first_name'], config['middle_name'], config['last_name']].compact.reject(&:empty?).join(' ')
  page.output = page.output.sub('<title type="html">blank', "<title type=\"html\">#{name}")
end
