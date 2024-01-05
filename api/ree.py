import pandas as pd
from pywebio.input import file_upload
from pywebio.output import put_datatable, put_table, put_button, put_text, popup, put_loading
from pywebio.session import set_env
import csv 
import re
import chardet
from sklearn.metrics.pairwise import cosine_similarity
from pywebio.output import span
from pywebio.platform.flask import webio_view
from flask import Flask
import os

data_abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'REE_data.csv')

tmp_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp.csv')


def remove_bom(text):
    # Check if the text starts with the UTF-8 BOM character (\ufeff)
    if text.startswith('\ufeff'):
        # If it does, remove the BOM from the beginning of the string
        return text[1:]
    return text

#Convert the uploaded csv file to pandas dataframe
def content_to_pandas(content: list):
    
    with open(tmp_data_path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter = ',')
        
        for i in content:
            writer.writerow(re.split(',',i))
        
        

#To get the mineral names from REE_data.csv when the user clicks any row
def get_mineral(us_df,row,min):
    if min == 1:
        return us_df['Most similar'][row]
    elif min == 2:
        return us_df['2nd most similar'][row]
    elif min == 3:
        return us_df['3rd most similar'][row]


#To get the mineral compositions from REE_data.csv when the user clicks any row
def get_data(db_df,us_df,row,min):
                
    if min == 1:
        mineral1 = us_df['Most similar'][row]
        return db_df.loc[mineral1][db_df.loc[mineral1]!=0].to_string()
                
    elif min == 2:
        mineral2 = us_df['2nd most similar'][row]
        return db_df.loc[mineral2][db_df.loc[mineral2]!=0].to_string()
                
    elif min == 3:
        mineral3 = us_df['3rd most similar'][row]
        return db_df.loc[mineral3][db_df.loc[mineral3]!=0].to_string()

app = Flask(__name__)

def main():
    
    #Set the title of the web page
    set_env(title='REE mineral search')
    
    #Demo csv pop up window
    with popup('Make sure your csv is of the following format') as s:
        put_text('Enter 0 or leave blank where there is no data').style('color:red')
        put_table([
        ['1', 'value', 'value','value','0','value'],
        ['2', '', 'value','value','','value'],
        ['3', 'value', 'value','value','value',''],
        ], header=['Points', 'P2O5', 'La2O3','Ce2O3','Nd2O3','F'])

    
    #Open file dialog box
    file = file_upload(label='Upload your CSV file', accept='.csv', required=True)

    
          
    with put_loading():
        
        #Getting the contents of the csv file   
        raw_data = file['content']
            
        # Detect the encoding of the file content
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        put_text("Please wait few seconds")

        try:
            # Decode the file content using the detected encoding and remove BOM if present
            content = remove_bom(raw_data.decode(encoding))
            lines = content.splitlines()
            
            #Converted the uploaded file to pandas dataframe and reads the file
            content_to_pandas(lines)
            user_df = pd.read_csv(tmp_data_path)

            #Removes the tmp.csv file
            os.remove(tmp_data_path)
            
            #Get the point id's from the user data
            points = user_df.iloc[:,0]

            #Drop the point id column
            user_df = user_df.drop(user_df.columns[0], axis = 1)

            #Fill nan values with 0
            user_df.fillna(0, inplace=True)
            
            #Read the REE_data.csv and make a copy
            concatenated_df = pd.read_csv(data_abs_path)
            ree_df = concatenated_df.copy()
            concatenated_df = concatenated_df.drop(columns='Minerals')
            
            
            # Get the list of element columns
            element_columns = concatenated_df.columns


            # Create missing element columns in user_df if they don't exist
            for element in element_columns:
                if element not in user_df.columns:
                    user_df[element] = 0

            # Reorder the columns in user_df to match the order in REE_data.csv
            user_df = user_df[concatenated_df.columns]
            
                
            # Calculate cosine similarity between the numpy array and each row in the DataFrame
            sim_1, sim_2, sim_3 = [], [], []
            ree_array = concatenated_df.to_numpy()

            
            for i in range(user_df.shape[0]):

                #Convert each row into a vector
                array = user_df.iloc[i,:].values.ravel()
                
                sim_values = []
                for j in range(ree_array.shape[0]):
                    
                    #Calculate cosine similarities
                    similarities = cosine_similarity([ree_array[j]], [array])[0][0]
                    sim_values.append(similarities.item())
                

                series = pd.Series(sim_values)
                # Find the indices of the three most similar minerals
                most_similar_mineral_indices = series.nlargest(3).index

                # Get the names of the three most similar minerals
                most_similar_minerals = ree_df.loc[most_similar_mineral_indices, 'Minerals'].tolist()

                
                sim_1.append(most_similar_minerals[0])
                sim_2.append(most_similar_minerals[1])
                sim_3.append(most_similar_minerals[2])
                

            
            user_df['Most similar'] = sim_1
            user_df['2nd most similar'] = sim_2
            user_df['3rd most similar'] = sim_3

            #Delete columns that only contains zeros
            user_df = user_df.loc[:, (user_df != 0).any(axis=0)]

            #Add the point id column
            user_df.insert(0,'Points',points)
            #Covert user_df to dict to display the results as table
            user_dict = user_df.to_dict(orient='records')
            ree_df.set_index('Minerals', drop=True, inplace=True)
    
        except UnicodeDecodeError:
            # Handle the case when the file cannot be decoded with the detected encoding
            print("Error: Unable to decode the file with the detected encoding.")
            return []
    
       
    put_text('Click any row to display mineral compositions of similar minerals from webmineral database').style('color:blue; font-size: 20px')

    #Displaying the database from REE_data.csv when the user clicks any row
    put_datatable(user_dict, onselect=lambda row_id: put_table([[span('Compositions of similar minerals from webmineral database for point {}'.format(user_df.iloc[row_id,0]),col=3)],[get_mineral(user_df,row_id,1),get_mineral(user_df,row_id,2), get_mineral(user_df,row_id,3)],[get_data(ree_df,user_df,row_id,1),get_data(ree_df,user_df,row_id,2),get_data(ree_df,user_df,row_id,3)]]))

    #Download button. Results get saved in the working directory
    put_button('Download', onclick=lambda:user_df.to_csv("Result.csv", index=False))  
        

app.add_url_rule('/', 'webio_view', webio_view(main),
            methods=['GET', 'POST', 'OPTIONS'])  


if __name__ == "__main__":
    app.run(debug=False)
