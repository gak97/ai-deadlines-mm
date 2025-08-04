require 'jekyll'

# This plugin generates individual pages for each conference entry in the
# `_data/conferences.yml` file. It is adapted from the original
# `paperswithcode/ai-deadlines` project. Each page is rendered using the
# `conference.html` layout defined under `_pages`.

module Jekyll
  class DataPageGenerator < Generator
    safe true

    def generate(site)
      # Read the list of conferences from the YAML data file
      conferences = site.data['conferences'] || []
      conferences.each do |conference|
        # Construct a filename based on the conference ID
        # Each conference entry must define a unique `id` field
        id = conference['id']
        next unless id
        # Create a new page instance for the conference
        page = DataPage.new(site, site.source, File.join('conference', id), conference)
        site.pages << page
      end
    end
  end

  # A custom Jekyll page that takes arbitrary data and exposes it to the layout
  class DataPage < Page
    def initialize(site, base, dir, data)
      @site = site
      @base = base
      @dir  = dir
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(base, '_pages'), 'conference.html')
      self.data['title'] = data['title']
      self.data['conference'] = data
    end
  end
end