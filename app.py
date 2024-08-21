# imports
from flask import Flask, render_template, request, send_file, Response
from wtforms import Form, TextField, StringField, SubmitField
from jobscraper import extract_job, generate_url, extract_data, transform_data, get_next_page, save_to_xlsx, to_aws

app = Flask(__name__)
app.config['WTF_CSRF_ENABLED'] = False # Sensitive

# input form
class Form(Form):
	keyword = TextField('What')
	location = TextField('Where')

# home page
@app.route('/')
def index():

	form = Form(request.form)
	return render_template('index.html', form=form)

# results page
@app.route('/results', methods=('GET', 'POST'))
def search_resluts():

    if request.method == 'POST':
        keyword = request.form['keyword']
        location = request.form['location']
        number_of_jobs = extract_job(keyword, location)

    return render_template('job.html', length = number_of_jobs, keyword = keyword , location = location)

if __name__=='__main__':
	app.run(debug=True)
