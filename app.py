# -*- coding: utf-8 -*-
"""
Application that predict the selling price of an apartment in stockholm. 

Trained on the data set ~8000 sold apartments and houses in the Stockolm area.
Uses, a random forrest model to predict the selling price based on the size, 
rooms, area and monthly fee.

"""


import numpy as np
import pickle
import requests
from flask import Flask, request, render_template
from bs4 import BeautifulSoup
import pandas as pd
import json

#Create an app object using the Flask class. 
app = Flask(__name__)

#Load the trained model. (Pickle file)
model = pickle.load(open('models/rf_regressor.pkl', 'rb'))

#use the route() decorator to tell Flask what URL should trigger our function.
@app.route('/')
def home():
    return render_template('index.html')

def retrieve_data(url):
    
    # retrieving relevant values from the url
    html_page = requests.get(str(url[0]))
    soup = BeautifulSoup(html_page.text, 'html.parser')
    select_left = soup.find('div', class_="_2IyrD _36W0F _16dH_")
    select_right = soup.find('div', class_="_36W0F mz1O4")

    name = select_left.find('h1').text
    size_and_area = select_left.findAll('h4')
    size = size_and_area[0].text
    area = size_and_area[1].text
    monthly_fee = select_right.findAll('div', text='Avgift')[0].next_sibling.text

    # split up size into size and #rooms
    size_and_rooms = size.replace('½', '.5').split(',')
    if len(size_and_rooms) > 1:
        size = float(size_and_rooms[0].split(' ')[0])
        rooms = float(size_and_rooms[1].split('rum')[0])
    else:
        size = int(size_and_rooms[0].split(' ')[0])
        rooms = 'N/A'

    # convert monthly fee to int and delete ' kr'
    if str(monthly_fee)=='nan':
        monthly_fee = 'N/A'
    elif str(monthly_fee).find('m²')==-1:
        monthly_fee = int(str(monthly_fee).split('kr')[0].replace(' ', ''))
    else:
        monthly_fee = 'N/A'

    # split up area into area and house type
    area_and_house_type = area.split(',')
    area = area_and_house_type[1]

    # load local json file
    with open('files_for_training_model/average_price_in_area.json') as f:
        average_price_in_area = json.load(f)

    df = pd.DataFrame(columns=['size', 'rooms','area', 'monthly_fee'])
    df.loc[0] = [size, rooms, area, monthly_fee]
    df

    # apply lambda function to df to get average price per m2 for each area
    df['area_price_per_m2'] = df.apply(lambda row: average_price_in_area[row['area']][0], axis=1)

    prediction = model.predict(df[['size', 'rooms', 'area_price_per_m2', 'monthly_fee']])
    return name, int(prediction[0])

@app.route('/predict',methods=['POST'])
def predict():

    int_features = [str(x) for x in request.form.values()] #Convert string inputs to float.
    url_array = [np.array(int_features)]  #Convert to the form [[a, b]] for input to the model
    url=url_array[0]
    name, output = retrieve_data(url)

    # output = url
    #print(output[0], type(output[0]))
    #output = round(prediction[0], 2)

    return render_template('index.html', apartment_info='The apartment is located in {} and the predicted selling price is:'.format(name), prediction_text=' {:,} kr'.format(output))


if __name__ == "__main__":
    app.run(
    host='0.0.0.0', port=8080
)
