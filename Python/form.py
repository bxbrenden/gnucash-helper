from flask import Flask, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import FloatField,\
                    SelectField,\
                    StringField,\
                    SubmitField,\
                    TextAreaField
from wtforms.validators import DataRequired


class TransactionForm(FlaskForm):
    debit = SelectField('Source Account (Debit)',
                        validators=[DataRequired()],
                        choices=[
                            'Assets:Personal Checking',
                            'Assets:Personal Savings',
                            'Assets:Personal Checking:Budget:Food',
                            'Assets:Personal Checking:Budget:Entertainment'
                        ],
                        validate_choice=True)
    credit = SelectField('Destination Account (Credit)',
                         validators=[DataRequired()],
                         choices=[
                             'Expenses',
                             'Expenses:Food',
                             'Expenses:Charity',
                             'Expenses:OnlyFans'
                         ],
                         validate_choice=True)
    amount = FloatField('Amount ($)',
                        validators=[DataRequired('Do not include a dollar sign $')],
                        render_kw={'placeholder': 'Ex: 4.20'})
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'bleepbloop'
bootstrap = Bootstrap(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    form = TransactionForm()
    if form.validate_on_submit():
        flash(f'Transaction for ${float(form.amount.data):.2f} saved!')
        return redirect(url_for('index'))
    return render_template('index.html', form=form)


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


@app.errorhandler(404)
def page_nout_found(e):
    return render_template('404.html')
