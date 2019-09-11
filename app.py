# # Modules
from flask import Flask, render_template, request, redirect
import os
import requests
import numpy as np
import pandas as pd
import bokeh
from bokeh.plotting import figure
from bokeh.io import show
from bokeh.embed import components
bv = bokeh.__version__


# # Flask app

app = Flask(__name__)
app.vars={}
feat = ['Open','Adj_Open','Close','Adj_Close']


@app.route('/')
def main():
	return redirect('/index')


@app.route('/index',methods=['GET','POST'])
def index():
	if request.method == 'GET':
		return render_template('index.html')
	else:
		#request was a POST
		app.vars['ticker'] = request.form['ticker'].upper()
		app.vars['start_year'] = request.form['year']
		try: 
			int(app.vars['start_year'])
			app.vars['tag'] = 'Data specified for %s in %s' % (app.vars['ticker'],app.vars['start_year'])
		except ValueError: 
			app.vars['start_year'] = ''
			app.vars['tag'] = 'Start year not specified/recognized'
		app.vars['select'] = [feat[q] for q in range(4) if feat[q] in request.form.values()]
		return redirect('/graph')


@app.route('/graph',methods=['GET','POST'])
def graph():
	
	# Request data from Quandl and get into pandas collapsing data by week
	req = 'https://www.quandl.com/api/v3/datasets/WIKI/'
	req = '%s%s.json?api_key=HetuiyW7-21kwALz8S63&collapse=weekly' % (req,app.vars['ticker'])
	if not app.vars['start_year']=='':
		req = '%s&start_date=%s-01-01' % (req,app.vars['start_year'])
	r = requests.get(req)
	cols = r.json()['dataset']['column_names']
	df = pd.DataFrame(np.array(r.json()['dataset']['data']),columns=cols)
	df=df[['Date','Open','Adj. Open','Close','Adj. Close']]
	df.Date = pd.to_datetime(df.Date)
	df[['Open','Adj. Open','Close','Adj. Close']] = df[['Open','Adj. Open','Close','Adj. Close']].astype(float)
	df.columns =['Date','Open','Adj_Open','Close','Adj_Close']
	
	if not app.vars['start_year']=='':
		if df.Date.iloc[-1].year>int(app.vars['start_year']):
			app.vars['tag'] = '%s, but Quandl record begins in %s' % (app.vars['tag'],df.Date.iloc[-1].year)
	app.vars['desc'] = r.json()['dataset']['name'].split(',')[0]
	
	
	# Make Bokeh plot and insert using components
	# ------------------- ------------------------|
	TOOLS=['hover','crosshair','pan','wheel_zoom','box_zoom','reset','tap','save','box_select','poly_select','lasso_select']
	p = figure(plot_width=550, plot_height=550,tools=TOOLS, title=app.vars['ticker'], x_axis_type="datetime")
	if 'Open' in app.vars['select']:
		p.line(df.Date, df.Open, color="green",line_width=2,legend='Opening price')
	if 'Adj_Open' in app.vars['select']:
		p.line(df.Date, df.Adj_Open,color="blue", line_width=2,legend='Adjusted Opening price')
	if 'Close' in app.vars['select']:
		p.line(df.Date, df.Close,color="red", line_width=2,legend='Closing price')
	if 'Adj_Close' in app.vars['select']:
		p.line(df.Date, df.Adj_Close,color="darkcyan", line_width=2,legend='Adjusted Closing price')
	p.legend.orientation = "vertical"
	p.legend.location = "top_left"
		
	# axis labels
	p.xaxis.axis_label = "Time"
	p.xaxis.axis_label_text_font_style = 'bold'
	p.xaxis.axis_label_text_font_size = '12pt'
	p.xaxis.major_label_orientation = np.pi/4
	p.xaxis.major_label_text_font_size = '14pt'
	p.xaxis.bounds = (df.Date.iloc[-1],df.Date.iloc[0])
	p.yaxis.axis_label = "Price"
	p.yaxis.axis_label_text_font_style = 'bold'
	p.yaxis.axis_label_text_font_size = '12pt'
	p.yaxis.major_label_text_font_size = '12pt'
	
	# render graph template
	# ------------------- ------------------------|
	script, div = components(p)
	return render_template('graph.html', bv=bv, ticker=app.vars['ticker'],
							ttag=app.vars['desc'], yrtag=app.vars['tag'],
							script=script, div=div)
		
	
@app.errorhandler(500)
def error_handler(e):
	return render_template('error.html',ticker=app.vars['ticker'],year=app.vars['start_year'])

# # If main
#if __name__ == '__main__':
  #app.run(port=5000,debug=False)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
