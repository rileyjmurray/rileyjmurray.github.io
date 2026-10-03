# Notes (the `_notes` collection) are short posts without titles. Jekyll still
# needs a title for the browser tab, the Atom feed, and site search, so this
# generator derives a plain-text title and description from each note's body.
# A note can override either one by setting it in front matter.
module Jekyll
  class NoteMetadataGenerator < Generator
    safe true
    priority :highest

    TITLE_LENGTH = 60
    DESCRIPTION_LENGTH = 160

    def generate(site)
      notes = site.collections['notes']
      return unless notes

      notes.docs.each do |doc|
        text = plain_text(doc.content)
        fallback = "Note from #{doc.date.strftime('%B %-d, %Y')}"

        # Jekyll fills in a title from the filename slug ("143005") when the
        # front matter has none; treat that as "no title".
        if doc.data['title'].nil? || doc.data['title'] == Utils.titleize_slug(doc.data['slug'].to_s)
          doc.data['title'] = text.empty? ? fallback : truncate(text, TITLE_LENGTH)
        end
        doc.data['description'] ||= text.empty? ? fallback : truncate(text, DESCRIPTION_LENGTH)
      end
    end

    private

    # Strips Markdown syntax but leaves $$...$$ math untouched, since TeX
    # uses the same characters as emphasis markers.
    def plain_text(markdown)
      markdown.split(/(\$\$.+?\$\$)/m).map do |part|
        next part.gsub(/\s+/, ' ') if part.start_with?('$$')

        part
          .gsub(/!\[[^\]]*\]\([^)]*\)/, '')        # images
          .gsub(/\[([^\]]*)\]\([^)]*\)/, '\1')     # links -> link text
          .gsub(/<[^>]+>/, '')                     # inline HTML
          .gsub(/^\s{0,3}(?:#+|>+|[-*+]|\d+\.)\s+/, '') # headings, quotes, list markers
          .gsub(/[*_`~]/, '')                      # emphasis and code markers
      end.join.gsub(/\s+/, ' ').strip
    end

    def truncate(text, length)
      return text if text.length <= length

      cut = text[0, length]
      cut = cut[0, cut.rindex(' ')] if cut.rindex(' ')
      "#{cut.rstrip}…"
    end
  end
end
