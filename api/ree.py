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

def content_to_pandas(content: list):
    # with open("/home/soorajgeo/myapp/data/tmp.csv", "w") as csv_file:
    with open(tmp_data_path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter = ',')
        # cleaned = clean(content)
        for i in content:
            writer.writerow(re.split(',',i))
        
        # return pd.read_csv(tmp_data_path)


def get_mineral(us_df,row,min):
    if min == 1:
        return us_df['Most similar'][row]
    elif min == 2:
        return us_df['2nd most similar'][row]
    elif min == 3:
        return us_df['3rd most similar'][row]


        
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
    
    set_env(title='REE mineral search')
    
    with popup('Make sure your csv is of the following format') as s:
        put_text('Enter 0 or leave blank where there is no data').style('color:red')
        put_table([
        ['1', 'value', 'value','value','0','value'],
        ['2', '', 'value','value','','value'],
        ['3', 'value', 'value','value','value',''],
        ], header=['Points', 'P2O5', 'La2O3','Ce2O3','Nd2O3','F'])

    
    
    file = file_upload(label='Upload your CSV file', accept='.csv')
    
    with put_loading():
        put_text("Please wait few seconds")

        raw_data = file['content']
            
        # Detect the encoding of the file content
        result = chardet.detect(raw_data)
        encoding = result['encoding']

        try:
            # Decode the file content using the detected encoding and remove BOM if present
            content = remove_bom(raw_data.decode(encoding))
            lines = content.splitlines()
            
            content_to_pandas(lines)
            user_df = pd.read_csv(tmp_data_path)
            
            
            points = user_df.iloc[:,0]
            user_df = user_df.drop(user_df.columns[0], axis = 1)
            user_df.fillna(0, inplace=True)
            
            concatenated_df = pd.read_csv(data_abs_path)
            # concatenated_df = pd.read_csv("static/REE_data.csv")
            ree_df = concatenated_df.copy()
            concatenated_df = concatenated_df.drop(columns='Minerals')
            
            
            # Get the list of element columns from df_minerals
            element_columns = concatenated_df.columns


            # Create missing element columns in df_user if they don't exist
            for element in element_columns:
                if element not in user_df.columns:
                    user_df[element] = 0

            # Reorder the columns in df_user to match the order in df_minerals
            user_df = user_df[concatenated_df.columns]
            
                
            # Calculate cosine similarity between the numpy array and each row in the DataFrame
            sim_1, sim_2, sim_3 = [], [], []
            ree_array = concatenated_df.to_numpy()

            
            for i in range(user_df.shape[0]):
                array = user_df.iloc[i,:].values.ravel()
                
                sim_values = []
                for j in range(ree_array.shape[0]):
                    
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
            user_df = user_df.loc[:, (user_df != 0).any(axis=0)]
            user_df.insert(0,'Points',points)
            user_dict = user_df.to_dict(orient='records')
            ree_df.set_index('Minerals', drop=True, inplace=True)
    
        except UnicodeDecodeError:
            # Handle the case when the file cannot be decoded with the detected encoding
            print("Error: Unable to decode the file with the detected encoding.")
            return []
    
       
    put_text('Click any row to display mineral compositions of similar minerals from webmineral database').style('color:blue; font-size: 20px')

    put_datatable(user_dict, onselect=lambda row_id: put_table([[span('Compositions of similar minerals from webmineral database for point {}'.format(user_df.iloc[row_id,0]),col=3)],[get_mineral(user_df,row_id,1),get_mineral(user_df,row_id,2), get_mineral(user_df,row_id,3)],[get_data(ree_df,user_df,row_id,1),get_data(ree_df,user_df,row_id,2),get_data(ree_df,user_df,row_id,3)]]))

    # put_button('Download', onclick=lambda:user_df.to_csv("/home/soorajgeo/myapp/data/Result.csv", index=False))
    put_button('Download', onclick=lambda:user_df.to_csv("Result.csv", index=False))  
        

app.add_url_rule('/', 'webio_view', webio_view(main),
            methods=['GET', 'POST', 'OPTIONS'])  # need GET,POST and OPTIONS methods

# app.run(host='localhost', port=8080)
if __name__ == "__main__":
    app.run(debug=False)
