from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from flask_wtf import FlaskForm
from wtforms import IntegerField,BooleanField
from wtforms.validators import DataRequired
import json
from RedisQueue import RedisQueue
app = Flask(__name__)

app.config.update(dict(
    SECRET_KEY="powerful secretkey",
    WTF_CSRF_SECRET_KEY="a csrf secret key"
))

class UpdateForm(FlaskForm):
	targetTemp = IntegerField('Target Temp', validators=[DataRequired()])
	manualControl = BooleanField('Manual Control', validators=[])
	manualBrightness = IntegerField('Manual Brightness', validators=[DataRequired()])
	maxBrightness = IntegerField('Maximum Brightness', validators=[DataRequired()])
	minBrightness = IntegerField('Minimum Brightness', validators=[DataRequired()])
	
brooderConfigFile = '../brooderConfig.txt'

@app.route("/")
def index():
	stats = {'currentTemp':0, 'currentHumidity':0, 'lastUpdateTime':"never", 'message':"Not initialized", 'targetTemp':0, 'brightness':0}
	form = UpdateForm()
	q = RedisQueue('brooder')
	dataPoints = []
	for item in q.getall():
		dataPoints.append(json.loads(str(item, 'utf-8')))
		
	if len(dataPoints) > 0:
		stats = dataPoints[-1]
	
	brooderConfig = json.load(open(brooderConfigFile))
	return render_template('main.html',**locals())

@app.route("/update", methods=["GET", "POST"])
def update():
	form = UpdateForm()
	if form.validate_on_submit():
		config = json.load(open(brooderConfigFile))
		config["targetTemp"] = form.targetTemp.data
		config["manualHeatIndex"] = form.manualBrightness.data
		config["pid"]["maxOutput"] = form.maxBrightness.data
		config["pid"]["minOutput"] = form.minBrightness.data
		print(str(form.manualControl.data))
		config["manualControl"] = form.manualControl.data
		with open(brooderConfigFile, 'w') as outfile:
			json.dump(config, outfile)
		
	
	return redirect(url_for('index'))

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5000, debug=False)
