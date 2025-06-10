from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home', 'pricing']

    def location(self, item):
        return reverse(item)

class TrackgramsSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['trackgrams:track']  # Adjust this based on your trackgrams URL name

    def location(self, item):
        return reverse(item)