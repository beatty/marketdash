#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#

import logging
import wsgiref.handlers
from decimal import Decimal
import ystockquote

from google.appengine.ext import webapp
from google.appengine.api import memcache

name_info = {
	"SPY":{'name':"S&P 500 SPDR", "asset_class":"domestic large-cap balanced"},
	"PFN":{'name':"Pimco Income Strategy Fund II", "asset_class":"fixed income"},
	"VTV":{'name':"Vanguard Value", "asset_class":"domestic value"},
	"VBR":{'name':"Vanguard Small-Cap Value", "asset_class":"domestic small-cap value"},
	"IWC":{'name':"iShares Russell Microcap", "asset_class":"domestic microcap"},
	"SCZ":{'name':"iShares MSCI EAFE Small Cap", "asset_class":"international small-cap"},
	"EFA":{'name':"iShares MSCI EAFE", "asset_class":"international"},
	"EFV":{'name':"iShares MSCI EAFE Value", "asset_class":"international value"},
	"DLS":{'name':"WisdomTree International SmallCap Div", "asset_class":"international small-cap"},
	"VWO":{'name':"Vanguard Emerging Markets", "asset_class":"emerging markets"},
	"FXI":{'name':"iShares FTSE/Xinhua China 25", "asset_class":"large-cap china"},
	"VNQ":{'name':"Vanguard REIT", "asset_class":"REIT"}
}

class MainHandler(webapp.RequestHandler):
	def get_cached_quote(self, symbol):
		key = "quote_" + symbol
		valstr = memcache.get(key)

		if valstr is None:
			fullquote = None
			try:
				fullquote = ystockquote.get_all(symbol)
				valstr = "%s,%s,%s,%s,%s,%s" % (fullquote['price'], fullquote['52_week_high'], fullquote['52_week_low'], fullquote['50day_moving_avg'], fullquote['200day_moving_avg'], fullquote['change'])
				memcache.add(key, valstr, 60*10)
			except Exception, e:
				logging.error('error retrieving quote for %s (%s)', symbol, e)
		  
		val = {}
		if valstr is not None:
			values = valstr.split(",")
			val['price'] = Decimal(values[0])
			val['52_week_high'] = Decimal(values[1])
			val['52_week_low'] = Decimal(values[2])
			val['50day_moving_avg'] = Decimal(values[3])
			val['200day_moving_avg'] = Decimal(values[4])
			if len(values) > 5:
				val['change'] = Decimal(values[5])
		
		return val
		
	def get(self):
		memcache.flush_all()
		symbols = ["SPY", "PFN", "VTV", "VBR", "VDE", "IWC", "SCZ", "EFA", "EFV", "DLS", "VWO", "FXI", "VNQ", "WPS", "DBC", "IEF", "TIP", "SHY", "BRK-A", "SDS", "SKF"]

		results = {}
		for symbol in symbols:
		    val = self.get_cached_quote(symbol)
		    if val is not None:
		        results[symbol] = val
	
		out = "<html><title>John's Market Dashboard</title><body style='margin-left:50px; font-family:sans-serif'><h2>John's Market Dashboard</h2>"
		out += "<div>WARNING: there's a bug -- look at the chart, not the CASH/OPEN indicator</div>"
		out += "<h3>200-day moving averages</h3>"
		out += "<div style='font-size:small'>These are the ETFs I care about and their 200-day simple moving averages. See <a href='http://papers.ssrn.com/sol3/papers.cfm?abstract_id=962461'>A Quantitative Approach to Tactical Asset Allocation</a> and <a href='http://dshort.com/articles/SP500-monthly-moving-averages.html'>dshort</a> for a backgrounder on technical trading signals for long-term timing.</div>"
		out += "<table style='padding:10px' cellpadding='5'>"
		out += "<th><td width='50px'>indicator</td><td width='50px'>price</td><td width='50px'>150 day sma</td><td width='50px'>pct below sma</td></th>"

		for symbol in symbols:
			k = symbol
			v = results[k]
			
			if v is None:
			    logging.error('no value for ' + k)
			    continue
			
			if not v.has_key('price'):
			    logging.error('no attrs for ' + k)
			    continue
			
			if k in name_info:
				metadata = name_info[k]
			else:
				metadata = {}
			price = v["price"]
			sma200 = v["200day_moving_avg"]

			if 'change' in v:
				change = int(v['change'])
			else:
				change = 0
			
			if price < sma200:
				indicator = "<span style='color:red'>CASH</span>"
			else:
				indicator = "<span style='color:green'>OPEN</span>"

			if change < 0:
				changecol = "<span style='color:red'>%s</span>" % change
			else:
				changecol = "<span style='color:green'>%s</span>" % change

			if metadata is not None and "name" in metadata:
				name = metadata['name']
			else:
				name = ""

			if metadata is not None and "asset_class" in metadata:
				asset_class = metadata['asset_class']
			else:
				asset_class = ""
				
			out += "<tr>"
			out += "<td><a href='http://finance.yahoo.com/q?s=%s'>%s</a> <br><span style='font-size:small'>%s<br>%s</span></td>" % (k, k, name, asset_class)
			out += "<td>%s</td>" % indicator
			out += "<td>%s</td>" % price
			#out += "<td>%s</td>" % changecol
			out += "<td>%s</td>" % sma200
			out += "<td>%s</td>" % ( round(100 * ((sma200 - price) / sma200), 2), )
			out += "<td><img src='http://ichart.finance.yahoo.com/z?s=%s&t=1y&q=l&l=on&z=s&p=m200&a='/></td>" % k
			out += "</tr>"
			
		out += "</table>"
		
		out += "<h3>Market Data</h3>"
		out += "<div>S&P 500 P/E10: 14.34</div>"
		out += "<div>The following courtesy of <a href='http://dshort.com'>dshort</a>"
		out += "<div><img src='http://dshort.com/charts/SP-Composite-PE10-ratio-by-quintile.gif'/></div>"
		out += "<div><img src='http://dshort.com/charts/bears/four-bears.gif'/></div>"
		out += """<style type='text/css'>@import url('http://s3.amazonaws.com/getsatisfaction.com/feedback/feedback.css');</style>
		<script src='http://s3.amazonaws.com/getsatisfaction.com/feedback/feedback.js' type='text/javascript'></script>
		<script type="text/javascript" charset="utf-8">
		  var tab_options = {}
		  tab_options.placement = "left";  // left, right, bottom, hidden
		  tab_options.color = "#222"; // hex (#FF0000) or color (red)
		  GSFN.feedback('http://getsatisfaction.com/johnsmarketdashboard/feedback/topics/new?display=overlay&style=idea', tab_options);
		</script>"""
		out += "</body></html>"

		#spy200 = ystockquote.get_200day_moving_avg('SPY')
		self.response.out.write(out) #'SPY: %s' % (spy,)) #, (spy, spy200))

class FeedbackHandler(webapp.RequestHandler):
	def get(self):
		self.response.out.write("""<html><body>
		<h2>John's Market Dashboard</h2>
		
		<div id="gsfn_list_widget">
		  <a href="http://getsatisfaction.com/johnsmarketdashboard" class="widget_title">Active customer service discussions in John's Market Dashboard</a>
		  <div id="gsfn_content">Loading...</div>
		  <div class="powered_by"><a href="http://getsatisfaction.com/"><img alt="Favicon" src="http://www.getsatisfaction.com/favicon.gif" style="vertical-align: middle;" /></a> <a href="http://getsatisfaction.com/">Get Satisfaction support network</a></div>
		</div>
		<script src="http://getsatisfaction.com/johnsmarketdashboard/widgets/javascripts/c3750bd8c4/widgets.js" type="text/javascript"></script><script src="http://getsatisfaction.com/johnsmarketdashboard/topics.widget?callback=gsfnTopicsCallback&amp;limit=5&amp;sort=last_active_at&amp;style=topics" type="text/javascript"></script>

		<iframe id="fdbk_iframe_inline" allowTransparency="true" width="100%" height="500" scrolling="no" frameborder="0" src="http://getsatisfaction.com/johnsmarketdashboard/feedback/topics/new?display=inline&amp;style=idea"></iframe>

		</body></html>""")

class QuoteHandler(webapp.RequestHandler):
	def get(self):
		symbol = self.request.get('s')


class CalNewsHandler(webapp.RequestHandler):
	def get(self):
		self.response.out.write("""<html><body><script type='text/javascript' charset='utf-8' src='http://scripts.hashemian.com/jss/feed.js?print=yes&numlinks=25&summarylen=50&seedate=yes&url=http:%2F%2Fpipes.yahoo.com%2Fpipes%2Fpipe.run%3F_id%3DANWYaYML3hG9JMopbrsjiw%26_render%3Drss'></script></html></body>""")

def main():
	application = webapp.WSGIApplication([('/', MainHandler), ('/calnews', CalNewsHandler), ('/feedback', FeedbackHandler)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()