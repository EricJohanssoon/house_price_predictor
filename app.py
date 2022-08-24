# -*- coding: utf-8 -*-
"""
Application that predicts heart disease percentage in the population of a town
based on the number of bikers and smokers. 

Trained on the data set of percentage of people biking 
to work each day, the percentage of people smoking, and the percentage of 
people with heart disease in an imaginary sample of 500 towns.

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

#Define the route to be home. 
#The decorator below links the relative route of the URL to the function it is decorating.
#Here, home function is with '/', our root directory. 
#Running the app sends us to index.html.
#Note that render_template means it looks for the file in the templates folder. 

#use the route() decorator to tell Flask what URL should trigger our function.
@app.route('/')
def home():
    return render_template('index.html')

def retrieve_data(url):
    
    print(type(str(url[0])))
    # retrieving relevant values from the url
    html_page = requests.get(str(url[0]))
    soup = BeautifulSoup(html_page.text, 'html.parser')
    select = soup.find('div', class_="_2IyrD _36W0F _16dH_")

    name = select.find('h1').text
    # price = select.find('h2').text
    size_and_area = select.findAll('h4')
    size = size_and_area[0].text
    area = size_and_area[1].text

    # split up size into size and #rooms
    size_and_rooms = size.replace('½', '.5').split(',')
    if len(size_and_rooms) > 1:
        size = float(size_and_rooms[0].split(' ')[0])
        rooms = float(size_and_rooms[1].split('rum')[0])
    else:
        size = int(size_and_rooms[0].split(' ')[0])
        rooms = 'N/A'

    # split up area into area and house type
    area_and_house_type = area.split(',')
    area = area_and_house_type[1]

    # load local json file
    with open('files_for_training_model/average_price_in_area.json') as f:
        average_price_in_area = json.load(f)


    df = pd.DataFrame(columns=['size', 'rooms','area'])
    df.loc[0] = [size, rooms, area]
    df
    # apply lambda function to df to get average price per m2 for each area
    df['area_price_per_m2'] = df.apply(lambda row: average_price_in_area[row['area']][0], axis=1)
    
    prediction = model.predict(df[['size', 'rooms', 'area_price_per_m2']])
    print(prediction)


    return name, int(prediction[0])

#You can use the methods argument of the route() decorator to handle different HTTP methods.
#GET: A GET message is send, and the server returns data
#POST: Used to send HTML form data to the server.
#Add Post method to the decorator to allow for form submission. 
#Redirect to /predict page with the output
@app.route('/predict',methods=['POST'])
def predict():

    int_features = [str(x) for x in request.form.values()] #Convert string inputs to float.
    url_array = [np.array(int_features)]  #Convert to the form [[a, b]] for input to the model
    url=url_array[0]
    name, output = retrieve_data(url)
    print(name)

    # output = url
    #print(output[0], type(output[0]))
    #output = round(prediction[0], 2)

    return render_template('index.html', apartment_info='The apartment is located in {}'.format(name), prediction_text='and the predicted selling price is {:,} kr'.format(output))


#When the Python interpreter reads a source file, it first defines a few special variables. 
#For now, we care about the __name__ variable.
#If we execute our code in the main program, like in our case here, it assigns
# __main__ as the name (__name__). 
#So if we want to run our code right here, we can check if __name__ == __main__
#if so, execute it here. 
#If we import this file (module) to another file then __name__ == app (which is the name of this python file).

if __name__ == "__main__":
    app.run()